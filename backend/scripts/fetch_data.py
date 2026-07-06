import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from datetime import datetime, timedelta
import pandas as pd
from psycopg2.extras import execute_values

from src.db.client import get_connection
from src.ingestion.rte_client import fetch_realised
from src.processing.features import compute_hourly_avg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fetch_data.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("--- Début du pipeline ---")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM historical_data ORDER BY timestamp DESC LIMIT 1")
    res = cursor.fetchone()
    if res:
        last_timestamp = res[0]
        logging.info(f"Dernier timestamp en base : {last_timestamp}")
        # Commencer à partir de la veille du dernier point en base
        start_date = last_timestamp.replace(tzinfo=None).replace(hour=0, minute=0, second=0) - timedelta(days=1)
    else:
        # Si la base est vide, on commence à J-7
        logging.info("Base vide. Récupération à partir de J-7...")
        start_date = datetime.now() - timedelta(days=7)

    end_date = datetime.now().replace(microsecond=0)

    logging.info("Récupération des données temps réel depuis l'API ODRE...")

    df_raw = fetch_realised(start_date, end_date)
    if df_raw.empty:
        logging.warning("Aucune donnée renvoyée par l'API.")
        cursor.close()
        conn.close()
        return

    df_final = compute_hourly_avg(df_raw)
    logging.info(f"{len(df_final)} lignes après traitement")

    rows = []
    for _, row in df_final.iterrows():
        rows.append((
            row['start_date'].isoformat(),
            float(row['consumption']) if pd.notna(row['consumption']) else None,
            float(row['nuclear']) if pd.notna(row['nuclear']) else None,
            float(row['gas']) if pd.notna(row['gas']) else None,
            float(row['coal']) if pd.notna(row['coal']) else None,
            float(row['oil']) if pd.notna(row['oil']) else None,
            float(row['wind']) if pd.notna(row['wind']) else None,
            float(row['solar']) if pd.notna(row['solar']) else None,
            float(row['hydro']) if pd.notna(row['hydro']) else None,
            float(row['bioenergy']) if pd.notna(row['bioenergy']) else None,
            float(row['pumped_storage']) if pd.notna(row['pumped_storage']) else None,
            float(row['net_imports']) if pd.notna(row['net_imports']) else None,
            float(row['co2_intensity']) if pd.notna(row['co2_intensity']) else None,
            'ODRE'
        ))

    logging.info("Insertion dans Supabase...")
    execute_values(cursor, """
        INSERT INTO historical_data (
            timestamp, consumption, nuclear, gas, coal, oil, wind, solar, 
            hydro, bioenergy, pumped_storage, net_imports, co2_intensity, source
        )
        VALUES %s
        ON CONFLICT (timestamp) DO UPDATE SET
            consumption = EXCLUDED.consumption,
            nuclear = EXCLUDED.nuclear,
            gas = EXCLUDED.gas,
            coal = EXCLUDED.coal,
            oil = EXCLUDED.oil,
            wind = EXCLUDED.wind,
            solar = EXCLUDED.solar,
            hydro = EXCLUDED.hydro,
            bioenergy = EXCLUDED.bioenergy,
            pumped_storage = EXCLUDED.pumped_storage,
            net_imports = EXCLUDED.net_imports,
            co2_intensity = EXCLUDED.co2_intensity,
            source = EXCLUDED.source
    """, rows)

    conn.commit()
    logging.info(f"{len(rows)} lignes insérées/mises à jour.")
    logging.info("--- Fin du pipeline ---")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()