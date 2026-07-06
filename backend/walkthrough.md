# Walkthrough - Dashboard Électrique Connecté Directement à Supabase

Ce guide explique comment faire fonctionner le site web de manière autonome en le connectant **directement** à votre base de données Supabase, vous permettant de sélectionner n'importe quelle plage de dates en direct.

---

## 1. Autoriser l'accès public en lecture dans Supabase (Sécurité RLS)

Par défaut, Supabase bloque l'accès anonyme aux tables. Pour que votre navigateur web puisse lire la table `historical_data` directement, vous devez ajouter une règle d'accès public en lecture seule (*SELECT*).

Exécutez ce script SQL dans le **SQL Editor** de votre projet Supabase :

```sql
-- 1. Activer la sécurité au niveau des lignes (Row Level Security)
ALTER TABLE historical_data ENABLE ROW LEVEL SECURITY;

-- 2. Créer une règle publique permettant la lecture seule pour tout le monde (anonyme)
CREATE POLICY "Permettre la lecture publique" 
ON historical_data 
FOR SELECT 
USING (true);
```

---

## 2. Configurer la clé d'accès dans le Frontend

Ouvrez le fichier [app.js](file:///Users/jamy/Desktop/electricity_forecasting_new/frontend/app.js) :

1. Votre URL de projet a été configurée automatiquement : `https://crnhghkopqputqekbmid.supabase.co`.
2. Remplacez la valeur de la variable **`SUPABASE_ANON_KEY`** (ligne 6) par votre clé publique **`anon public`**.
   *   *Où la trouver ?* Dans Supabase > **Project Settings** (engrenage en bas à gauche) > **API** > copiez la clé indiquée sous **`anon public`**.

---

## 3. Lancer le site web et tester

1. Ouvrez le fichier [index.html](file:///Users/jamy/Desktop/electricity_forecasting_new/frontend/index.html) dans votre navigateur (double-cliquez dessus).
2. Utilisez le sélecteur de date (Du / Au) ou cliquez sur les boutons rapides ("7 derniers jours", "30 derniers jours").
3. Le site va interroger Supabase directement en tâche de fond et actualiser instantanément les graphiques interactifs ApexCharts.

---

## 4. Avantages de cette solution
*   **Plus besoin de script Python d'exportation** : Pas de génération de fichier JSON à faire tourner sur un serveur. Le site est 100 % autonome.
*   **Plages de dates infinies** : L'utilisateur du site peut charger les données de 2020, d'un mois précis ou de la veille directement en changeant le calendrier, la requête se fait en temps réel.
*   **Respect de la charte graphique (DA)** : Le design du site (polices, couleurs claires et sombres, bordures, boutons) a été calqué sur le fichier `style.css` de votre Portfolio.
