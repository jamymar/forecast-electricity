import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import xgboost as xgb
import holidays
from vacances_scolaires_france import SchoolHolidayDates
from psycopg2.extras import execute_values

# Résolution des chemins pour importer 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.db.client import get_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

fr_holidays = holidays.France()
school_holidays = SchoolHolidayDates()

def is_bridge(dt):
    """Calcule si un jour (lundi ou vendredi) fait le pont avec un jour férié français."""
    if dt.weekday() == 4:  # Vendredi
        if (dt - timedelta(days=1)).date() in fr_holidays:
            return 1
    if dt.weekday() == 0:  # Lundi
        if (dt + timedelta(days=1)).date() in fr_holidays:
            return 1
    return 0

def prepare_features(df):
    """Génère toutes les variables explicatives avancées (météo, calendrier FR, lags et tendances)."""
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['timestamp'])
    
    # Calendrier de base
    df['hour'] = df['datetime'].dt.hour
    df['dayofweek'] = df['datetime'].dt.dayofweek
    df['month'] = df['datetime'].dt.month
    df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)
    
    # 1. Caractéristiques cycliques
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12.0)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12.0)
    
    # 2. Variable croisée Calendrier (Heure x Week-end)
    df['hour_weekend'] = df['hour'] + (df['is_weekend'] * 24)
    
    # 3. Vacances Scolaires et Ponts français
    df['date_only'] = df['datetime'].dt.date
    df['is_school_holiday'] = df['date_only'].apply(lambda d: 1 if school_holidays.is_holiday_for_zone(d, 'C') else 0)
    df['is_holiday'] = df['date_only'].apply(lambda d: 1 if d in fr_holidays else 0)
    df['is_bridge_day'] = df['datetime'].apply(is_bridge)
    
    # 4. Lags de consommation historiques (par rapport à l'instant T)
    df['lag_1'] = df['consumption'].shift(1)
    df['lag_2'] = df['consumption'].shift(2)
    df['lag_24'] = df['consumption'].shift(24)
    df['lag_48'] = df['consumption'].shift(48)
    df['lag_168'] = df['consumption'].shift(168)
    
    # 5. Tendances de consommation (Diff)
    df['diff_1'] = df['consumption'] - df['lag_1']
    df['diff_24'] = df['consumption'] - df['lag_24']
    
    # 6. Statistiques glissantes de consommation
    df['rolling_mean_24'] = df['consumption'].rolling(window=24).mean()
    df['rolling_std_24'] = df['consumption'].rolling(window=24).std()
    df['rolling_mean_168'] = df['consumption'].rolling(window=168).mean()
    
    # 7. Météo - Température brute
    df['temp_now'] = df['temperature']
    df['temp_lag_24'] = df['temperature'].shift(24)
    
    return df

def get_live_weather_forecast():
    """Récupère les prévisions de température météo à 48h depuis l'API Open-Meteo."""
    logging.info("Appel de l'API de prévisions météo Open-Meteo pour Paris...")
    url = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&hourly=temperature_2m&timezone=UTC"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            times = data.get("hourly", {}).get("time", [])
            temps = data.get("hourly", {}).get("temperature_2m", [])
            
            # Structurer sous forme de dictionnaire timestamp -> température
            forecast_map = {}
            for t, temp in zip(times, temps):
                ts = pd.to_datetime(t).tz_localize('UTC')
                forecast_map[ts] = float(temp)
            return forecast_map
    except Exception as e:
        logging.error(f"Impossible de récupérer les prévisions météo : {e}")
    return {}

def main():
    logging.info("--- Début du pipeline XGBoost Météo & Calendrier FR ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Charger l'historique complet (incluant la nouvelle colonne temperature)
    logging.info("Chargement des données historiques depuis Supabase...")
    cursor.execute("SELECT timestamp, consumption, temperature FROM historical_data ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    
    if len(rows) < 1000:
        logging.error("Données historiques insuffisantes.")
        return
        
    df_raw = pd.DataFrame(rows, columns=['timestamp', 'consumption', 'temperature'])
    df_raw['consumption'] = df_raw['consumption'].astype(float)
    df_raw['temperature'] = df_raw['temperature'].astype(float)
    
    # 2. Préparer toutes les caractéristiques
    df = prepare_features(df_raw)
    
    # Définition des colonnes de base à l'instant T (sans nuages, HDD/CDD ni inertie)
    base_feature_cols = [
        'hour', 'dayofweek', 'month', 'is_weekend',
        'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
        'hour_weekend',
        'is_school_holiday', 'is_holiday', 'is_bridge_day',
        'lag_1', 'lag_2', 'lag_24', 'lag_48', 'lag_168',
        'diff_1', 'diff_24',
        'rolling_mean_24', 'rolling_std_24', 'rolling_mean_168',
        'temp_now', 'temp_lag_24'
    ]
    
    # Supprimer les lignes contenant des NaNs
    df_clean = df.dropna(subset=base_feature_cols + ['temperature']).reset_index(drop=True)
    
    # 3. Séparation Train / Backtest (J-35)
    split_date = datetime.now() - timedelta(days=35)
    train_mask = pd.to_datetime(df_clean['timestamp']).dt.tz_localize(None) < split_date
    df_train = df_clean[train_mask].reset_index(drop=True)
    
    logging.info(f"Taille du jeu d'entraînement : {len(df_train)} lignes.")
    
    # 4. Entraînement des 48 modèles directs
    models = {}
    logging.info("Entraînement des 48 modèles XGBoost avec calendrier et météo brute...")
    
    for h in range(1, 49):
        df_train_h = df_train.copy()
        # Variables cibles futures
        df_train_h['temp_target'] = df_train_h['temperature'].shift(-h)
        
        # Liste de features étendue pour l'horizon H
        features_h = base_feature_cols + ['temp_target']
        
        X_train_h = df_train_h[features_h]
        y_train_h = df_train_h['consumption'].shift(-h)
        
        # Aligner et nettoyer les NaNs générés par le shift
        valid_idx = y_train_h.notna() & X_train_h['temp_target'].notna()
        X_train_h = X_train_h[valid_idx]
        y_train_h = y_train_h[valid_idx]
        
        # Modèle
        model = xgb.XGBRegressor(
            n_estimators=95,
            max_depth=5,
            learning_rate=0.07,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_h, y_train_h)
        models[h] = model
        
    logging.info("Entraînement terminé.")

    # 5. Simulation du Backtest (sur les 35 derniers jours)
    logging.info("Génération du backtesting glissant...")
    df_backtest = df_clean[~train_mask].reset_index(drop=True)
    
    prediction_date = datetime.now()
    all_predictions = []
    
    # Boucle de simulation (glissement quotidien)
    for idx in range(0, len(df_backtest) - 48, 24):
        row_t = df_backtest.iloc[idx]
        last_timestamp = pd.to_datetime(row_t['timestamp'])
        
        for h in range(1, 49):
            future_row = df_backtest.iloc[idx + h]
            temp_target_val = float(future_row['temperature'])
            
            # Reconstruire les features à l'instant T
            x_data = {col: row_t[col] for col in base_feature_cols}
            x_data['temp_target'] = temp_target_val
            
            X_t = pd.DataFrame([x_data])
            pred_val = float(models[h].predict(X_t)[0])
            pred_timestamp = last_timestamp + timedelta(hours=h)
            
            all_predictions.append((
                pred_timestamp,
                pred_val,
                "XGBoost Thermosensible",
                "48h",
                prediction_date
            ))

    # 6. Prévisions du Futur Réel (48 prochaines heures)
    weather_forecast_map = get_live_weather_forecast()
    
    logging.info("Génération des prévisions futures réelles...")
    last_known_row = df_clean.iloc[-1]
    last_known_time = pd.to_datetime(last_known_row['timestamp'])
    
    for h in range(1, 49):
        pred_timestamp = last_known_time + timedelta(hours=h)
        
        # Météo future cible (ou fallback)
        temp_target_val = weather_forecast_map.get(
            pred_timestamp, 
            float(last_known_row['temperature'])
        )
        
        x_data = {col: last_known_row[col] for col in base_feature_cols}
        x_data['temp_target'] = temp_target_val
        
        X_last = pd.DataFrame([x_data])
        pred_val = float(models[h].predict(X_last)[0])
        
        all_predictions.append((
            pred_timestamp,
            pred_val,
            "XGBoost Thermosensible",
            "48h",
            prediction_date
        ))

    # 7. Évaluation de la MAPE de validation en direct (Python)
    mape_errors = []
    actual_map = {str(row['timestamp']): float(row['consumption']) for _, row in df_clean.iterrows()}
    
    for pred_timestamp, pred_val, _, _, _ in all_predictions:
        actual_val = actual_map.get(str(pred_timestamp))
        if actual_val and actual_val > 0:
            mape_errors.append(abs((actual_val - pred_val) / actual_val))
            
    val_mape = np.mean(mape_errors) * 100 if mape_errors else None
    if val_mape is not None:
        logging.info(f"==> SCORE MAPE DE VALIDATION (Avancé + Nuages + HDD/CDD + Vacances FR) : {val_mape:.4f} %")
        
        log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../experiments_log.md'))
        log_exists = os.path.exists(log_path)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            if not log_exists:
                f.write("# Historique des Expérimentations XGBoost\n\n")
                f.write("| Date | MAPE (%) | Description des Features | Estimators | Depth | LR |\n")
                f.write("|---|---|---|---|---|---|\n")
            
            features_desc = "XGBoost Super-Feature (Weather 4 + HDD/CDD + Inertia + holidays/bridges)"
            f.write(f"| {datetime.now().strftime('%Y-%m-%d %H:%M')} | **{val_mape:.3f} %** | {features_desc} | 95 | 5 | 0.07 |\n")
        logging.info(f"Expérimentation enregistrée dans : {log_path}")

    # 8. Élimination des doublons de timestamps
    unique_predictions = {}
    for row in all_predictions:
        unique_predictions[row[0]] = row
    unique_insert_rows = list(unique_predictions.values())

    # 9. Insertion dans Supabase
    logging.info(f"Insertion de {len(unique_insert_rows)} prédictions XGBoost en base...")
    execute_values(cursor, """
        INSERT INTO predictions_xgboost (timestamp, predicted_value, model_name, horizon, prediction_date)
        VALUES %s
        ON CONFLICT (timestamp) 
        DO UPDATE SET 
            predicted_value = EXCLUDED.predicted_value,
            prediction_date = EXCLUDED.prediction_date,
            model_name = EXCLUDED.model_name
    """, unique_insert_rows)
    
    conn.commit()
    logging.info("Prévisions XGBoost insérées avec succès dans Supabase !")
    
    cursor.close()
    conn.close()
    logging.info("--- Fin du pipeline XGBoost ---")

if __name__ == "__main__":
    main()
