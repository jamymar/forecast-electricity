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

def main():
    logging.info("--- Début du script de prédiction avec Google TimesFM ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # Étape 2 : Récupérer les 1024 dernières valeurs de consommation (Contexte)
    logging.info("Récupération de l'historique récent de consommation...")
    cursor.execute("""
        SELECT timestamp, consumption 
        FROM historical_data 
        ORDER BY timestamp DESC 
        LIMIT 1024
    """)
    rows = cursor.fetchall()
    
    if len(rows) < 128:
        logging.error(f"Historique insuffisant pour TimesFM (il faut au moins 128 points, trouvé {len(rows)}). Abandon.")
        return
        
    # Inverser pour avoir l'ordre chronologique
    rows.reverse()
    
    # Extraire les valeurs et timestamps
    context_timestamps = [r[0] for r in rows]
    context_values = np.array([float(r[1]) for r in rows], dtype=np.float32)
    last_timestamp = context_timestamps[-1]
    
    logging.info(f"Contexte récupéré : {len(context_values)} points (de {context_timestamps[0]} à {last_timestamp})")

    # Étape 3 : Charger et compiler le modèle Google TimesFM
    # (Les poids du modèle ~800 Mo seront téléchargés automatiquement depuis Hugging Face au premier lancement)
    logging.info("Chargement du modèle Google TimesFM depuis Hugging Face...")
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

    # Étape 4 : Lancement de la prédiction (Inférence)
    # Horizon de 48 heures (2 jours dans le futur)
    horizon = 48
    logging.info(f"Lancement de la prédiction sur un horizon de {horizon} heures...")
    
    # TimesFM attend une liste de séries temporelles 1D
    point_forecast, _ = model.forecast(
        horizon=horizon,
        inputs=[context_values]
    )
    
    # Extraire le premier (et unique) résultat de la liste
    predictions = point_forecast[0]
    logging.info(f"Prédictions générées avec succès (amplitude moyenne: {np.mean(predictions):.0f} MW)")

    # Étape 5 : Insertion des prédictions dans Supabase
    logging.info("Préparation de l'écriture des prédictions dans Supabase...")
    prediction_date = datetime.now()
    
    insert_rows = []
    for i, val in enumerate(predictions):
        # Calculer le timestamp futur (+1h pour chaque pas)
        pred_timestamp = last_timestamp + timedelta(hours=i+1)
        insert_rows.append((
            pred_timestamp,
            float(val),
            "Google-TimesFM-2.5",
            f"{horizon}h",
            prediction_date
        ))
        
    # Insertion par lot (ON CONFLICT DO UPDATE permet de mettre à jour la valeur si le timestamp existe déjà)
    from psycopg2.extras import execute_values
    execute_values(cursor, """
        INSERT INTO predictions_timesfm (timestamp, predicted_value, model_name, horizon, prediction_date)
        VALUES %s
        ON CONFLICT (timestamp) 
        DO UPDATE SET 
            predicted_value = EXCLUDED.predicted_value,
            prediction_date = EXCLUDED.prediction_date,
            model_name = EXCLUDED.model_name
    """, insert_rows)
    
    conn.commit()
    logging.info(f"{len(insert_rows)} prédictions insérées/mises à jour dans predictions_timesfm.")
    
    cursor.close()
    conn.close()
    logging.info("--- Fin du script de prédiction ---")

if __name__ == "__main__":
    main()
