import sys
import os
import logging
import requests
import pandas as pd
from psycopg2.extras import execute_values

# Résolution des chemins pour importer 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db.client import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("--- Début du script d'importation météo (Température & Couverture Nuageuse) ---")
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Récupérer la plage de dates de notre historique en base
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM historical_data")
    min_date, max_date = cursor.fetchone()
    
    if not min_date or not max_date:
        logging.error("La table historical_data est vide. Impossible de lier des données météo.")
        return
        
    start_str = min_date.strftime("%Y-%m-%d")
    end_str = max_date.strftime("%Y-%m-%d")
    logging.info(f"Plage historique détectée : de {start_str} à {end_str}")

    # 2. Appeler l'API Historique Open-Meteo pour Paris (Lat 48.8566, Lon 2.3522)
    # Récupère la température à 2m et la couverture nuageuse (cloud_cover)
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude=48.8566&longitude=2.3522&start_date={start_str}&end_date={end_str}&hourly=temperature_2m,cloud_cover&timezone=UTC"
    
    logging.info("Téléchargement des données météo depuis l'API Open-Meteo...")
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"Erreur API Open-Meteo: {response.text}")
        return
        
    data = response.json()
    hourly_data = data.get("hourly", {})
    times = hourly_data.get("time", [])
    temps = hourly_data.get("temperature_2m", [])
    clouds = hourly_data.get("cloud_cover", [])
    
    logging.info(f"Téléchargement réussi : {len(times)} points météo reçus.")

    # 3. Préparer les données pour la mise à jour
    logging.info("Création de la table temporaire de mise à jour...")
    cursor.execute("""
        CREATE TEMP TABLE temp_weather_updates (
            timestamp TIMESTAMPTZ PRIMARY KEY,
            temperature NUMERIC,
            cloud_cover NUMERIC
        ) ON COMMIT DROP;
    """)
    
    update_rows = []
    for t, temp, cloud in zip(times, temps, clouds):
        if temp is None or cloud is None:
            continue
        timestamp_utc = pd.to_datetime(t).tz_localize('UTC')
        update_rows.append((timestamp_utc, float(temp), float(cloud)))

    # Insérer dans la table temporaire
    execute_values(cursor, """
        INSERT INTO temp_weather_updates (timestamp, temperature, cloud_cover)
        VALUES %s
    """, update_rows)

    # Faire l'UPDATE en masse vers historical_data
    logging.info("Mise à jour des colonnes temperature et cloud_cover dans historical_data...")
    cursor.execute("""
        UPDATE historical_data h
        SET temperature = t.temperature,
            cloud_cover = t.cloud_cover
        FROM temp_weather_updates t
        WHERE h.timestamp = t.timestamp;
    """)
    
    conn.commit()
    logging.info("Météo historique (Température + Nuages) mise à jour avec succès dans Supabase !")
    
    cursor.close()
    conn.close()
    logging.info("--- Fin du script météo ---")

if __name__ == "__main__":
    main()
