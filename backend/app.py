import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import plotly.express as px
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Electricity Forecasting & Energy Mix", layout="wide")

load_dotenv()

def get_connection():
    try:
        # Tenter d'utiliser les secrets de production de Streamlit Cloud
        return psycopg2.connect(
            host=st.secrets["SUPABASE_HOST"],
            database=st.secrets["SUPABASE_DB"],
            user=st.secrets["SUPABASE_USER"],
            password=st.secrets["SUPABASE_PASSWORD"],
            port=st.secrets["SUPABASE_PORT"]
        )
    except Exception:
        # Fallback local via le fichier .env
        return psycopg2.connect(
            host=os.getenv("SUPABASE_HOST"),
            database=os.getenv("SUPABASE_DB"),
            user=os.getenv("SUPABASE_USER"),
            password=os.getenv("SUPABASE_PASSWORD"),
            port=os.getenv("SUPABASE_PORT")
        )

@st.cache_data(ttl=900)
def load_historical():
    conn = get_connection()
    # Récupération de toutes les colonnes enrichies
    query = """
        SELECT 
            timestamp, consumption, nuclear, gas, coal, oil, 
            wind, solar, hydro, bioenergy, pumped_storage, 
            net_imports, co2_intensity 
        FROM historical_data 
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    return df

# Chargement des données historiques uniquement
df_historical = load_historical()

# --- HEADER ---
st.title("⚡ French Electricity Grid Dashboard")
st.markdown("Suivi en temps réel de la consommation, du mix de production énergétique et de l'intensité carbone (Données API ODRE).")
st.markdown("---")

# --- MÉTRIQUES CLÉS ---
if not df_historical.empty:
    latest_row = df_historical.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Consommation Actuelle", f"{int(latest_row['consumption']):,} MW" if pd.notna(latest_row['consumption']) else "N/A")
    with col2:
        # Part des énergies décarbonées (Nucléaire + Renouvelables)
        re_cols = ['nuclear', 'wind', 'solar', 'hydro', 'bioenergy']
        total_prod = sum(latest_row[c] for c in re_cols if pd.notna(latest_row[c]))
        share_decarbonated = (total_prod / latest_row['consumption'] * 100) if latest_row['consumption'] > 0 else 0
        st.metric("Part Décarbonée", f"{round(share_decarbonated, 1)} %")
    with col3:
        st.metric("Intensité Carbone", f"{int(latest_row['co2_intensity'])} g CO₂/kWh" if pd.notna(latest_row['co2_intensity']) else "N/A")
    with col4:
        st.metric("Dernière mise à jour (Local)", df_historical['timestamp'].max().tz_convert('Europe/Paris').strftime("%d %b %Y, %H:%M"))

st.markdown("---")

# --- SÉLECTION DE LA PÉRIODE POUR L'HISTORIQUE ---
st.subheader("📊 Données Historiques du Réseau")
period = st.selectbox("Période d'affichage", ["24 heures", "7 jours", "30 jours", "90 jours"], index=1)
days_mapping = {"24 heures": 1, "7 jours": 7, "30 jours": 30, "90 jours": 90}
days = days_mapping[period]

# Filtrage de l'historique pour la période choisie
df_period = df_historical.tail(24 * days).copy()

# Création des onglets
tab1, tab2, tab3 = st.tabs(["🔌 Consommation", "☘️ Mix Énergétique", "🛢️ Émissions CO₂ & Échanges"])

with tab1:
    st.markdown("#### Historique de la Consommation Globale (MW)")
    fig_cons = px.line(df_period, x='timestamp', y='consumption', labels={'consumption': 'Consommation (MW)', 'timestamp': 'Date'}, color_discrete_sequence=['#1f77b4'])
    fig_cons.update_layout(hovermode='x unified', margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_cons, use_container_width=True)

with tab2:
    st.markdown("#### Mix de Production Électrique Français (MW)")
    # Préparation des données pour le Stacked Area Chart
    production_sources = {
        'Nucléaire': 'nuclear',
        'Gaz': 'gas',
        'Solaire': 'solar',
        'Éolien': 'wind',
        'Hydraulique': 'hydro',
        'Bioénergies': 'bioenergy',
        'Charbon': 'coal',
        'Fioul': 'oil'
    }
    
    # Création du graphique d'aires empilées avec Plotly
    fig_mix = go.Figure()
    
    # Couleurs harmonieuses pour chaque source d'énergie
    colors = {
        'Nucléaire': '#fcd34d',
        'Gaz': '#f87171',
        'Solaire': '#fbbf24',
        'Éolien': '#60a5fa',
        'Hydraulique': '#3b82f6',
        'Bioénergies': '#34d399',
        'Charbon': '#4b5563',
        'Fioul': '#9ca3af'
    }
    
    for label, col_name in production_sources.items():
        if col_name in df_period.columns:
            fig_mix.add_trace(go.Scatter(
                x=df_period['timestamp'],
                y=df_period[col_name],
                name=label,
                mode='lines',
                line=dict(width=0.5),
                stackgroup='one', # Empilage
                fillcolor=colors[label]
            ))
            
    fig_mix.update_layout(
        yaxis_title="Production (MW)",
        xaxis_title="Date",
        hovermode='x unified',
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_mix, use_container_width=True)

with tab3:
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Intensité Carbone de la Production (g CO₂ / kWh)")
        fig_co2 = px.line(df_period, x='timestamp', y='co2_intensity', labels={'co2_intensity': 'Taux de CO₂ (g/kWh)', 'timestamp': 'Date'}, color_discrete_sequence=['#ef4444'])
        fig_co2.update_layout(hovermode='x unified', margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_co2, use_container_width=True)
        
    with col_right:
        st.markdown("#### Échanges Physiques aux Frontières (MW)")
        st.caption("Une valeur positive indique une importation, une valeur négative indique une exportation.")
        fig_imports = px.area(df_period, x='timestamp', y='net_imports', labels={'net_imports': 'Solde import/export (MW)', 'timestamp': 'Date'}, color_discrete_sequence=['#8b5cf6'])
        fig_imports.update_layout(hovermode='x unified', margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_imports, use_container_width=True)

st.markdown("---")

if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()