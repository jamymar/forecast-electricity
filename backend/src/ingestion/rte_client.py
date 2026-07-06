import requests
import pandas as pd
from datetime import datetime

# Colonnes d'intérêt issues d'ODRE et leur renommage pour la base de données
COLUMNS_MAPPING = {
    'date_heure': 'start_date',
    'consommation': 'consumption',
    'nucleaire': 'nuclear',
    'gaz': 'gas',
    'charbon': 'coal',
    'fioul': 'oil',
    'eolien': 'wind',
    'solaire': 'solar',
    'hydraulique': 'hydro',
    'bioenergies': 'bioenergy',
    'pompage': 'pumped_storage',
    'ech_physiques': 'net_imports',
    'taux_co2': 'co2_intensity'
}

def fetch_realised(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Récupère la consommation et le mix de production d'électricité en temps réel 
    depuis l'API ODRE (Opendatasoft).
    Cette API s'actualise toutes les 15 minutes sans nécessiter de clé API.
    """
    # 1. Formater les dates en chaînes ISO
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 2. Nous interrogeons les deux tables (temps réel et consolidée/historique) pour couvrir toute la période
    datasets = ["eco2mix-national-tr", "eco2mix-national-cons-def"]
    dfs = []
    
    select_fields = ",".join(COLUMNS_MAPPING.keys())

    for ds in datasets:
        url = f"https://opendata.reseaux-energies.fr/api/explore/v2.1/catalog/datasets/{ds}/exports/json"
        params = {
            "where": f'date_heure >= "{start_str}" and date_heure < "{end_str}"',
            "select": select_fields
        }
        try:
            res = requests.get(url, params=params, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns=COLUMNS_MAPPING)
                    dfs.append(df)
        except Exception as e:
            print(f"Erreur d'accès au dataset {ds} : {e}")

    if not dfs:
        # Retourne un DataFrame vide avec les bonnes colonnes
        return pd.DataFrame(columns=COLUMNS_MAPPING.values())

    # 3. Concaténer, trier et supprimer les doublons (dans la zone de recouvrement des deux tables)
    df_concat = pd.concat(dfs, ignore_index=True)
    df_concat['start_date'] = pd.to_datetime(df_concat['start_date'], utc=True)
    
    # On supprime les lignes où la consommation (consumption) est nulle
    df_concat = df_concat.dropna(subset=['consumption'])
    df_concat = df_concat.drop_duplicates(subset='start_date')
    df_concat = df_concat.sort_values('start_date').reset_index(drop=True)
    
    return df_concat


def fetch_forecast(start_date: datetime, end_date: datetime, forecast_type: str = "D-2") -> pd.DataFrame:
    """
    Récupère les prévisions de consommation officielles de la RTE depuis l'API publique ODRE.
    Utilise 'prevision_j1' (prévision de la veille) pour simuler la prévision D-2/D-1 sans authentification.
    """
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    datasets = ["eco2mix-national-tr", "eco2mix-national-cons-def"]
    dfs = []
    
    # On utilise la prévision J-1 (prevision_j1) comme proxy pour la prévision RTE
    for ds in datasets:
        url = f"https://opendata.reseaux-energies.fr/api/explore/v2.1/catalog/datasets/{ds}/exports/json"
        params = {
            "where": f'date_heure >= "{start_str}" and date_heure < "{end_str}"',
            "select": "date_heure,prevision_j1"
        }
        try:
            res = requests.get(url, params=params, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={'date_heure': 'start_date', 'prevision_j1': 'value'})
                    dfs.append(df)
        except Exception:
            pass

    if not dfs:
        return pd.DataFrame(columns=['start_date', 'value'])

    df_concat = pd.concat(dfs, ignore_index=True)
    df_concat['start_date'] = pd.to_datetime(df_concat['start_date'], utc=True)
    df_concat = df_concat.dropna(subset=['value'])
    df_concat = df_concat.drop_duplicates(subset='start_date')
    df_concat = df_concat.sort_values('start_date').reset_index(drop=True)
    
    return df_concat