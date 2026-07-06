import sys
import os
import logging
from datetime import datetime
import numpy as np
import torch

# Résolution des chemins pour importer 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.db.client import get_connection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("--- Début du script de Backtesting avec Amazon Chronos ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Charger le modèle Amazon Chronos-T5-Base
    logging.info("Chargement du modèle Amazon Chronos-T5-Base...")
    try:
        from chronos import ChronosPipeline
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipeline = ChronosPipeline.from_pretrained(
            "amazon/chronos-t5-base",
            device_map=device,
            torch_dtype=torch.float32
        )
    except Exception as e:
        logging.error(f"Impossible d'initialiser Chronos : {e}")
        return

    # 2. Récupérer l'historique complet pour extraire des tranches de contexte
    logging.info("Récupération de l'historique de consommation pour le backtesting...")
    cursor.execute("""
        SELECT timestamp, consumption 
        FROM historical_data 
        ORDER BY timestamp ASC
    """)
    all_rows = cursor.fetchall()
    
    if len(all_rows) < 1024:
        logging.error("Historique insuffisant en base pour faire un backtesting (besoin d'au moins 1024 points).")
        return

    timestamps = [r[0] for r in all_rows]
    values = np.array([float(r[1]) for r in all_rows], dtype=np.float32)
    
    logging.info(f"Nombre total de points réels chargés : {len(values)}")

    # 3. Effectuer des prévisions glissantes toutes les 24 heures (1 fois par jour) sur les 30 derniers jours
    forecast_horizon = 96
    step_hours = 24
    
    end_idx = len(values)
    start_idx = end_idx - (35 * 24) # Commencer à J-35
    
    if start_idx < 1024:
        start_idx = 1024
        
    logging.info(f"Début du backtesting glissant de l'indice {start_idx} à {end_idx}...")
    
    prediction_date = datetime.now()
    all_predictions = []
    
    # Boucle glissante
    for idx in range(start_idx, end_idx, step_hours):
        context_values = values[idx-1024:idx]
        last_timestamp = timestamps[idx-1]
        
        logging.info(f"Inférence au point temporel : {last_timestamp}...")
        
        # Inférence Chronos
        try:
            context_tensor = torch.tensor(context_values, dtype=torch.float32)
            
            # Predict
            forecast = pipeline.predict(
                context_tensor.unsqueeze(0),
                prediction_length=forecast_horizon,
                num_samples=20
            )
            
            # Extraire la médiane
            predictions = torch.median(forecast[0], dim=0).values.numpy()
            
            # Stocker les lignes de prédiction
            from datetime import timedelta
            for i, val in enumerate(predictions):
                pred_timestamp = last_timestamp + timedelta(hours=i+1)
                all_predictions.append((
                    pred_timestamp,
                    float(val),
                    "chronos-2",
                    f"{forecast_horizon}h",
                    prediction_date
                ))
        except Exception as e:
            logging.error(f"Erreur d'inférence à l'indice {idx} : {e}")
            continue

    # 4. Écrire le lot de prédictions du backtest dans la table predictions_chronos
    if all_predictions:
        logging.info(f"Création de la table de prédictions si nécessaire...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions_chronos (
                timestamp TIMESTAMPTZ PRIMARY KEY,
                predicted_value DOUBLE PRECISION,
                model_name VARCHAR,
                horizon VARCHAR,
                prediction_date TIMESTAMPTZ
            );
        """)
        
        # Dédoublonner par timestamp (les prédictions les plus récentes écrasent les anciennes)
        clean_predictions = {}
        for row in all_predictions:
            clean_predictions[row[0]] = row
        clean_list = list(clean_predictions.values())
        
        logging.info(f"Insertion par lot de {len(clean_list)} prédictions de backtest (dédoublonnées)...")
        from psycopg2.extras import execute_values
        execute_values(cursor, """
            INSERT INTO predictions_chronos (timestamp, predicted_value, model_name, horizon, prediction_date)
            VALUES %s
            ON CONFLICT (timestamp) 
            DO UPDATE SET 
                predicted_value = EXCLUDED.predicted_value,
                prediction_date = EXCLUDED.prediction_date,
                model_name = EXCLUDED.model_name
        """, clean_list)
        
        conn.commit()
        logging.info("Backtesting de Chronos terminé et enregistré avec succès !")
    else:
        logging.warning("Aucune prédiction à insérer.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
