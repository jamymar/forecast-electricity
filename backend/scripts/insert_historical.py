import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from psycopg2.extras import execute_values
from src.db.client import get_connection

conn = get_connection()
cursor = conn.cursor()

print("Lecture du fichier CSV...")
df = pd.read_csv("data/consumption_data_cleaned.csv")
df['start_date'] = pd.to_datetime(df['start_date'], utc=True)

print("Préparation des lignes...")
rows = []
for _, row in df.iterrows():
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

print("Insertion dans Supabase...")
execute_values(cursor, """
    INSERT INTO historical_data (
        timestamp, consumption, nuclear, gas, coal, oil, wind, solar, 
        hydro, bioenergy, pumped_storage, net_imports, co2_intensity, source
    )
    VALUES %s
    ON CONFLICT (timestamp) DO NOTHING
""", rows)

conn.commit()
print(f"{len(rows)} lignes insérées avec succès dans la table enrichie.")

cursor.close()
conn.close()