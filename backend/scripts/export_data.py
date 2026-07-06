import sys
import os
import json
from datetime import datetime, timedelta

# Ajouter le chemin parent (dossier backend/) pour résoudre les imports de src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.client import get_connection

def export_grid_data():
    print("Connexion à Supabase...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Déterminer la date limite (les 7 derniers jours par rapport au point le plus récent)
    cursor.execute("SELECT max(timestamp) FROM historical_data")
    max_time = cursor.fetchone()[0]
    
    if not max_time:
        print("Erreur : Aucune donnée historique trouvée dans la base.")
        cursor.close()
        conn.close()
        return
        
    start_time = max_time - timedelta(days=7)
    print(f"Extraction des données de {start_time} à {max_time}...")
    
    # 2. Récupérer toutes les données sur 7 jours
    query = """
        SELECT 
            timestamp, consumption, nuclear, gas, coal, oil, 
            wind, solar, hydro, bioenergy, pumped_storage, 
            net_imports, co2_intensity 
        FROM historical_data 
        WHERE timestamp >= %s 
        ORDER BY timestamp ASC
    """
    cursor.execute(query, (start_time,))
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not rows:
        print("Aucune donnée récupérée pour cette période.")
        return
        
    # 3. Structurer les données sous forme de séries pour ApexCharts
    timestamps = []
    consumption = []
    nuclear = []
    gas = []
    coal = []
    oil = []
    wind = []
    solar = []
    hydro = []
    bioenergy = []
    pumped_storage = []
    net_imports = []
    co2_intensity = []
    
    # Helper pour convertir float ou None
    def clean_val(val):
        return round(float(val), 1) if val is not None else 0.0

    for r in rows:
        timestamps.append(r[0].isoformat() + "Z" if hasattr(r[0], "isoformat") else r[0])
        consumption.append(clean_val(r[1]))
        nuclear.append(clean_val(r[2]))
        gas.append(clean_val(r[3]))
        coal.append(clean_val(r[4]))
        oil.append(clean_val(r[5]))
        wind.append(clean_val(r[6]))
        solar.append(clean_val(r[7]))
        hydro.append(clean_val(r[8]))
        bioenergy.append(clean_val(r[9]))
        pumped_storage.append(clean_val(r[10]))
        net_imports.append(clean_val(r[11]))
        co2_intensity.append(clean_val(r[12]))

    # Calcul des métriques pour les cartes du Dashboard (sur le point le plus récent)
    latest_index = -1
    latest_consumption = consumption[latest_index]
    latest_co2 = co2_intensity[latest_index]
    
    # Part décarbonée = (Nucléaire + Vent + Solaire + Hydro + Bio) / Consommation
    latest_decarb_total = (
        nuclear[latest_index] + wind[latest_index] + 
        solar[latest_index] + hydro[latest_index] + bioenergy[latest_index]
    )
    latest_decarb_share = round((latest_decarb_total / latest_consumption * 100), 1) if latest_consumption > 0 else 0.0
    
    # Dernière mise à jour au format lisible
    last_update_str = max_time.strftime("%Y-%m-%d %H:%M")
    
    payload = {
        "metrics": {
            "latest_consumption": latest_consumption,
            "latest_co2_intensity": latest_co2,
            "latest_decarbonated_share": latest_decarb_share,
            "last_update": last_update_str
        },
        "series": {
            "timestamps": timestamps,
            "consumption": consumption,
            "nuclear": nuclear,
            "gas": gas,
            "coal": coal,
            "oil": oil,
            "wind": wind,
            "solar": solar,
            "hydro": hydro,
            "bioenergy": bioenergy,
            "pumped_storage": pumped_storage,
            "net_imports": net_imports,
            "co2_intensity": co2_intensity
        }
    }
    
    # Déterminer le chemin cible dans le dossier frontend
    # Note : Le chemin relatif part de backend/scripts/ vers frontend/data/
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "data"))
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "grid_data.json")
    
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"Exportation réussie ! {len(timestamps)} points sauvegardés dans {target_path}")

if __name__ == "__main__":
    export_grid_data()
