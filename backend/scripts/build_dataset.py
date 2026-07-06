import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime, timedelta
from src.ingestion.rte_client import fetch_realised
from src.processing.features import compute_hourly_avg

start_date = datetime(2020, 1, 1)
end_date = datetime.now().replace(microsecond=0)

all_df = []

current = start_date
while current < end_date:
    next_date = min(current + timedelta(days=180), end_date)
    print(f"Récupération {current.date()} -> {next_date.date()}")
    df_raw = fetch_realised(current, next_date)
    if not df_raw.empty:
        all_df.append(df_raw)
    current = next_date

if not all_df:
    print("Aucune donnée récupérée.")
    sys.exit(1)

df_concat = pd.concat(all_df, ignore_index=True)
df_final = compute_hourly_avg(df_concat)

# Remplissage des trous
full_range = pd.date_range(start=df_final['start_date'].min(),
                           end=df_final['start_date'].max(),
                           freq='h', tz='UTC')
df_full = pd.DataFrame({'start_date': full_range})
df_final = pd.merge(df_full, df_final, on='start_date', how='left')

# Appliquer le remplissage (par décalage de 7 jours (168h) puis interpolation) à toutes les colonnes numériques
columns_to_fill = [
    'consumption', 'nuclear', 'gas', 'coal', 'oil', 'wind', 'solar', 
    'hydro', 'bioenergy', 'pumped_storage', 'net_imports', 'co2_intensity'
]
cols = [c for c in columns_to_fill if c in df_final.columns]

for col in cols:
    # On remplace par la valeur de la semaine précédente si c'est nul
    df_final[col] = df_final[col].fillna(df_final[col].shift(168))
    # Interpolation linéaire pour boucher le reste des trous
    df_final[col] = df_final[col].interpolate(method='linear')

df_final.to_csv("data/consumption_data_cleaned.csv", index=False)
print(f"Terminé — {len(df_final)} lignes sauvegardées")