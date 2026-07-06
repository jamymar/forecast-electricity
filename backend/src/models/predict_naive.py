import sys
import os
import logging
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

# Imports internes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.db.client import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("--- Début du script Modèle Naïf Saisonnier (J-7) ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Récupérer tout l'historique récent (par exemple les 40 derniers jours)
    # afin de pouvoir remplir les prédictions naïves des 33 derniers jours et des 48h futures
    logging.info("Extraction de l'historique réel récent...")
    limit_date = datetime.now() - timedelta(days=40)
    cursor.execute("""
        SELECT timestamp, consumption 
        FROM historical_data 
        WHERE timestamp >= %s
        ORDER BY timestamp ASC
    """, (limit_date,))
    rows = cursor.fetchall()
    
    if not rows:
        logging.error("Aucune donnée historique trouvée.")
        return

    logging.info(f"Données de base récupérées : {len(rows)} points.")
    prediction_date = datetime.now()
    
    # 2. Générer les prévisions Naïves J-7
    # La prévision pour l'instant T est égale à la valeur réelle à l'instant T - 7 jours
    insert_rows = []
    for timestamp, consumption in rows:
        if consumption is None:
            continue
        # Décaler la date de +7 jours pour projeter cette valeur dans le futur
        predicted_timestamp = timestamp + timedelta(days=7)
        
        insert_rows.append((
            predicted_timestamp,
            float(consumption),
            "Naïf Saisonnier (J-7)",
            "48h",
            prediction_date
        ))

    # 3. Insertion en masse dans Supabase
    logging.info(f"Insertion de {len(insert_rows)} prédictions naïves uniques...")
    execute_values(cursor, """
        INSERT INTO predictions_naive (timestamp, predicted_value, model_name, horizon, prediction_date)
        VALUES %s
        ON CONFLICT (timestamp) 
        DO UPDATE SET 
            predicted_value = EXCLUDED.predicted_value,
            prediction_date = EXCLUDED.prediction_date,
            model_name = EXCLUDED.model_name
    """, insert_rows)
    
    conn.commit()
    logging.info("Modèle Naïf Saisonnier J-7 importé avec succès !")
    
    cursor.close()
    conn.close()
    logging.info("--- Fin du script ---")

if __name__ == "__main__":
    main()
