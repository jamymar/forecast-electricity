# Suivi et Prévision de la Consommation Électrique Française

Ce projet est une application complète de suivi en temps réel et de prévision de la consommation électrique en France. Il compare les données réelles issues de l'API RTE avec les prévisions générées par différents modèles (prévisions réseau RTE, Google TimesFM 2.5, LightGBM Direct et modèle naïf saisonnier).

## Architecture

Le projet est divisé en deux parties principales :
1. **Frontend (React)** : Un tableau de bord interactif moderne développé avec Vite, Tailwind CSS v4 et ApexCharts.
2. **Backend (Python)** : Les scripts d'ingestion quotidienne des données RTE et les pipelines d'exécution des modèles de prévision.

Toutes les données historiques et de prévisions sont stockées sur une base de données PostgreSQL gérée via Supabase.

```
RTE API ---> Scripts d'ingestion (Python) ---> Supabase (PostgreSQL)
                                                    |
                                                    v
Application Web (React + ApexCharts) <---------------
```

## Structure du Projet

```
├── backend/
│   ├── src/
│   │   ├── db/          # Connexion à la base Supabase
│   │   ├── ingestion/   # Client pour récupérer les données de l'API RTE
│   │   └── models/      # Modèles de prédiction (TimesFM, LightGBM, Naïve)
│   ├── scripts/         # Scripts d'exécution de la collecte et des prédictions
│   └── app.py           # Ancienne maquette Streamlit (obsolète)
│
└── frontend/
    ├── src/
    │   ├── components/  # Composants graphiques (ApexCharts) et tableaux
    │   ├── App.jsx      # Point d'entrée de l'application
    │   └── main.jsx
    ├── tailwind.config.js
    └── package.json
```

## Configuration et Installation Locale

### 1. Ingestion et Modèles (Backend)

Pour installer et exécuter les scripts Python du backend :

Préparez l'environnement virtuel et installez les dépendances nécessaires :
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Créez un fichier `.env` à la racine du dossier `backend` avec vos accès à l'API RTE et à Supabase :
```env
SUPABASE_HOST=votre_host
SUPABASE_DB=postgres
SUPABASE_USER=votre_utilisateur
SUPABASE_PASSWORD=votre_mot_de_passe
SUPABASE_PORT=5432
RTE_CLIENT_ID=votre_client_id
RTE_CLIENT_SECRET=votre_client_secret
```

Exécutez le script d'ingestion pour mettre à jour les données :
```bash
python scripts/fetch_data.py
```

### 2. Interface Utilisateur (Frontend)

Pour faire tourner le tableau de bord React en local :

Installez les dépendances du projet :
```bash
cd frontend
npm install
```

Compilez et lancez le serveur de développement :
```bash
npm run dev
```

Pour compiler la version de production et la servir localement :
```bash
npm run build
python -m http.server 8000 --directory dist
```
L'application sera alors accessible à l'adresse `http://localhost:8000`.
