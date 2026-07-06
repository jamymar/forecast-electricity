import pandas as pd

def compute_hourly_avg(df : pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la moyenne horaire pour toutes les colonnes numériques présentes.
    Prend en charge à la fois le format simple (pour les prévisions : 'value')
    et le format enrichi (pour la consommation réelle : mix énergétique).
    """
    if df.empty:
        return df

    # Cas des prévisions simples (ancienne API ou fetch_forecast)
    if 'value' in df.columns:
        df['date_column'] = df['start_date'].dt.date.astype(str)
        df['hour_column'] = df['start_date'].dt.hour
        df['min_column'] = df['start_date'].dt.minute
        
        avg_hourly = df.groupby(['date_column', 'hour_column'])['value'].mean().reset_index().rename(columns={'value': 'avg_value_hourly'})
        df_ = pd.merge(avg_hourly, df, on=['date_column', 'hour_column'], how='inner')
        df_ = df_[df_['min_column'] == 0]
        
        df_final = df_[['start_date', 'avg_value_hourly']].copy()
        df_final = df_final.drop_duplicates(subset='start_date', keep='first')
        df_final = df_final.sort_values('start_date').reset_index(drop=True)
        return df_final

    # Cas du mix énergétique enrichi
    columns_to_average = [
        'consumption', 'nuclear', 'gas', 'coal', 'oil', 'wind', 'solar', 
        'hydro', 'bioenergy', 'pumped_storage', 'net_imports', 'co2_intensity'
    ]
    
    # Ne conserver que les colonnes réellement présentes
    cols = [c for c in columns_to_average if c in df.columns]
    
    df['date_column'] = df['start_date'].dt.date.astype(str)
    df['hour_column'] = df['start_date'].dt.hour
    df['min_column'] = df['start_date'].dt.minute
    
    # Calcul de la moyenne sur les groupes (Date, Heure)
    avg_hourly = df.groupby(['date_column', 'hour_column'])[cols].mean().reset_index()
    
    # Jointure pour récupérer la date exacte du début de l'heure (minute 0)
    df_ = pd.merge(
        avg_hourly, 
        df[['date_column', 'hour_column', 'min_column', 'start_date']], 
        on=['date_column', 'hour_column'], 
        how='inner'
    )
    df_ = df_[df_['min_column'] == 0]
    
    # Sélection des colonnes finales
    df_final = df_[['start_date'] + cols].copy()
    df_final = df_final.drop_duplicates(subset='start_date', keep='first')
    df_final = df_final.sort_values('start_date').reset_index(drop=True)
    
    return df_final