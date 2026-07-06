import sys
import os
import logging
from datetime import datetime, timedelta
import numpy as np

# Résolution des chemins pour importer 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.db.client import get_connection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean(val):
    return int(round(float(val))) if val is not None else 0

def main():
    logging.info("--- Début du script de Backtesting avec Google TimesFM ---")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Charger le modèle Google TimesFM
    logging.info("Chargement du modèle Google TimesFM...")
    try:
        import timesfm
        model = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
        model.compile(
            timesfm.ForecastConfig(
                max_context=1024,
                max_horizon=256,
                normalize_inputs=True,
                use_continuous_quantile_head=True,
            )
        )
    except Exception as e:
        logging.error(f"Impossible d'initialiser TimesFM : {e}")
        return

    # 2. Récupérer l'historique complet pour extraire des tranches de contexte
    # On récupère les données des 50 derniers jours pour pouvoir faire des prévisions glissantes sur les 30 derniers jours
    logging.info("Récupération de l'historique de consommation pour le backtesting...")
    cursor.execute("""
        SELECT timestamp, consumption 
        FROM historical_data 
        ORDER BY timestamp ASC
    """)
    all_rows = cursor.fetchall()
    
    if len(all_rows) < 1024:
        logging.error("Historique insuffisant en base pour faire un backtesting 1024 context.")
        return

    # Convertir en liste exploitable
    timestamps = [r[0] for r in all_rows]
    values = np.array([float(r[1]) for r in all_rows], dtype=np.float32)
    
    logging.info(f"Nombre total de points réels chargés : {len(values)}")

    # 3. Effectuer des prévisions glissantes toutes les 24 heures (1 fois par jour) sur les 30 derniers jours
    # Pour chaque jour J dans les 30 derniers jours, on prend les 1024 heures de contexte précédentes et on prédit les 96 heures suivantes.
    forecast_horizon = 96
    step_hours = 24  # Pas de glissement (faire une prévision par jour)
    
    # On commence à l'indice qui correspond à environ 35 jours avant la fin
    end_idx = len(values)
    start_idx = end_idx - (35 * 24) # Commencer à J-35
    
    if start_idx < 1024:
        start_idx = 1024  # Sécurité : avoir au moins 1024 points de contexte
        
    logging.info(f"Début du backtesting glissant de l'indice {start_idx} à {end_idx}...")
    
    prediction_date = datetime.now()
    all_predictions = []
    
    # Boucle glissante
    for idx in range(start_idx, end_idx, step_hours):
        # Contexte de 1024 points
        context_values = values[idx-1024:idx]
        last_timestamp = timestamps[idx-1]
        
        logging.info(f"Inférence au point temporel : {last_timestamp}...")
        
        # Inférence TimesFM
        try:
            point_forecast, _ = model.forecast(
                horizon=forecast_horizon,
                inputs=[context_values]
            )
            predictions = point_forecast[0]
            
            # Structurer les lignes pour insertion
            for i, val in enumerate(predictions):
                pred_timestamp = last_timestamp + timedelta(hours=i+1)
                all_predictions.append((
                    pred_timestamp,
                    float(val),
                    "Google-TimesFM-2.5",
                    f"{forecast_horizon}h",
                    prediction_date
                ))
        except Exception as ex:
            logging.error(f"Erreur d'inférence à {last_timestamp} : {ex}")
            continue

    # 4. Insertion en masse des prévisions de backtest (sans doublon de clé primaire)
    if all_predictions:
        # Éliminer les doublons de timestamps en gardant la prévision la plus récente pour chaque heure
        unique_predictions = {}
        for row in all_predictions:
            # Clé: le timestamp (row[0])
            unique_predictions[row[0]] = row
            
        unique_insert_rows = list(unique_predictions.values())
        
        logging.info(f"Insertion de {len(unique_insert_rows)} points de prévisions uniques générés par le backtesting...")
        from psycopg2.extras import execute_values
        execute_values(cursor, """
            INSERT INTO predictions_timesfm (timestamp, predicted_value, model_name, horizon, prediction_date)
            VALUES %s
            ON CONFLICT (timestamp) 
            DO UPDATE SET 
                predicted_value = EXCLUDED.predicted_value,
                prediction_date = EXCLUDED.prediction_date,
                model_name = EXCLUDED.model_name
        """, unique_insert_rows)
        conn.commit()
        logging.info("Backtesting inséré avec succès dans la base Supabase !")
    else:
        logging.warning("Aucune prédiction générée.")
        
    cursor.close()
    conn.close()
    logging.info("--- Fin du script de Backtesting ---")

if __name__ == "__main__":
    main()
