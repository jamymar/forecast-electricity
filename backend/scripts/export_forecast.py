import json
import os
from datetime import datetime, timedelta
import psycopg2
from src.db.client import get_connection

def export_to_json(output_path="../PORTFOLIO FINAL/assets/data/latest_forecast.json"):
    """
    Queries Supabase for the last 7 days of historical consumption and the 48h forecasts,
    aligns the timelines, and exports a unified JSON file for native portfolio charting.
    """
    print("Connecting to Supabase...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Get the last timestamp from history to define the split between past and future
    cursor.execute("SELECT max(timestamp) FROM historical_data")
    max_hist_time = cursor.fetchone()[0]
    print(f"Latest historical data point: {max_hist_time}")
    
    # Calculate boundaries
    start_history = max_hist_time - timedelta(days=7)
    end_forecast = max_hist_time + timedelta(hours=48)
    
    # 2. Query 7 days of history
    print("Fetching historical data...")
    cursor.execute(
        "SELECT timestamp, value FROM historical_data WHERE timestamp >= %s ORDER BY timestamp ASC",
        (start_history,)
    )
    history_rows = cursor.fetchall()
    
    # 3. Query 48h forecasts for Chronos-2 Zero Shot
    print("Fetching Chronos-2 Zero-Shot forecasts...")
    cursor.execute(
        "SELECT timestamp, predicted_value FROM predictions WHERE timestamp > %s AND timestamp <= %s ORDER BY timestamp ASC",
        (max_hist_time, end_forecast)
    )
    zeroshot_rows = cursor.fetchall()
    
    # 4. Query 48h forecasts for Chronos-2 LoRA
    print("Fetching Chronos-2 LoRA forecasts...")
    cursor.execute(
        "SELECT timestamp, predicted_value FROM predictions_lora WHERE timestamp > %s AND timestamp <= %s ORDER BY timestamp ASC",
        (max_hist_time, end_forecast)
    )
    lora_rows = cursor.fetchall()
    
    # 5. Query 48h forecasts for RTE Benchmark
    print("Fetching RTE Benchmark forecasts...")
    cursor.execute(
        "SELECT timestamp, predicted_value FROM predictions_rte WHERE horizon = 'H+48' AND timestamp > %s AND timestamp <= %s ORDER BY timestamp ASC",
        (max_hist_time, end_forecast)
    )
    rte_rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 6. Parse SQL rows into dictionaries keyed by ISO-string timestamp
    history_dict = {t.isoformat() + "Z" if hasattr(t, "isoformat") else t: float(v) for t, v in history_rows}
    zeroshot_dict = {t.isoformat() + "Z" if hasattr(t, "isoformat") else t: float(v) for t, v in zeroshot_rows}
    lora_dict = {t.isoformat() + "Z" if hasattr(t, "isoformat") else t: float(v) for t, v in lora_rows}
    rte_dict = {t.isoformat() + "Z" if hasattr(t, "isoformat") else t: float(v) for t, v in rte_rows}
    
    # Create the unified list of timestamps (168h past + 48h future)
    timestamps = sorted(list(history_dict.keys()) + list(lora_dict.keys()))
    
    historical_value = []
    chronos_zero_shot = []
    chronos_lora = []
    rte_benchmark = []
    
    # Scale values to Gigawatts (GW) to make numbers clean (e.g. 55000 MW -> 55.0 GW)
    def to_gw(val):
        return round(val / 1000.0, 2) if val is not None else None

    for ts in timestamps:
        historical_value.append(to_gw(history_dict.get(ts)))
        chronos_zero_shot.append(to_gw(zeroshot_dict.get(ts)))
        chronos_lora.append(to_gw(lora_dict.get(ts)))
        rte_benchmark.append(to_gw(rte_dict.get(ts)))
        
    payload = {
        "timestamps": timestamps,
        "historical_value": historical_value,
        "chronos_zero_shot": chronos_zero_shot,
        "chronos_lora": chronos_lora,
        "rte_benchmark": rte_benchmark
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully baked forecast data ({len(timestamps)} hours) to {output_path}!")

if __name__ == "__main__":
    export_to_json()
