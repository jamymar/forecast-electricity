import sys
import os
import logging
from datetime import datetime, timedelta
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

def clean(val):
    return int(round(float(val))) if val is not None else 0

def main():
    logging.info("--- Début du script de prédiction avec Amazon Chronos ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # Récupérer les 1024 dernières valeurs de consommation
    logging.info("Récupération de l'historique récent de consommation...")
    cursor.execute("""
        SELECT timestamp, consumption 
        FROM historical_data 
        ORDER BY timestamp DESC 
        LIMIT 1024
    """)
    rows = cursor.fetchall()
    
    if len(rows) < 128:
        logging.error(f"Historique insuffisant pour Chronos (trouvé {len(rows)}). Abandon.")
        return
        
    # Inverser pour avoir l'ordre chronologique
    rows.reverse()
    
    # Extraire les valeurs et timestamps
    context_timestamps = [r[0] for r in rows]
    context_values = [float(r[1]) for r in rows]
    last_timestamp = context_timestamps[-1]
    
    logging.info(f"Contexte récupéré : {len(context_values)} points (de {context_timestamps[0]} à {last_timestamp})")

    # Charger le modèle Amazon Chronos-T5-Base en zéro-shot
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

    # Lancement de la prédiction zéro-shot
    horizon = 48
    logging.info(f"Lancement de la prédiction sur un horizon de {horizon} heures...")
    
    # Convertir en tenseur PyTorch pour le modèle
    context_tensor = torch.tensor(context_values, dtype=torch.float32)
    
    # Inférence Chronos
    forecast = pipeline.predict(
        context_tensor.unsqueeze(0),
        prediction_length=horizon,
        num_samples=20
    )
    
    # Calculer la médiane
    predictions = torch.median(forecast[0], dim=0).values.numpy()
    
    logging.info(f"Prédictions générées avec succès (amplitude moyenne: {np.mean(predictions):.0f} MW)")

    # Insertion des prédictions dans Supabase
    logging.info("Préparation de l'écriture des prédictions dans Supabase...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions_chronos (
            timestamp TIMESTAMPTZ PRIMARY KEY,
            predicted_value DOUBLE PRECISION,
            model_name VARCHAR,
            horizon VARCHAR,
            prediction_date TIMESTAMPTZ
        );
    """)

    prediction_date = datetime.now()
    
    insert_rows = []
    for i in range(horizon):
        pred_timestamp = last_timestamp + timedelta(hours=i+1)
        insert_rows.append((
            pred_timestamp,
            float(predictions[i]),
            "chronos-2",
            f"{horizon}h",
            prediction_date
        ))
        
    from psycopg2.extras import execute_values
    execute_values(cursor, """
        INSERT INTO predictions_chronos (timestamp, predicted_value, model_name, horizon, prediction_date)
        VALUES %s
        ON CONFLICT (timestamp) 
        DO UPDATE SET 
            predicted_value = EXCLUDED.predicted_value,
            prediction_date = EXCLUDED.prediction_date,
            model_name = EXCLUDED.model_name
    """, insert_rows)
    
    conn.commit()
    logging.info(f"{len(insert_rows)} prédictions insérées/mises à jour dans predictions_chronos.")
    
    cursor.close()
    conn.close()
    logging.info("--- Fin du script de prédiction ---")

if __name__ == "__main__":
    main()
