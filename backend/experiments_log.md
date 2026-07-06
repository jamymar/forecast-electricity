# Historique des Expérimentations XGBoost

| Date | MAPE (%) | Description des Features | Estimators | Depth | LR |
|---|---|---|---|---|---|
| 2026-07-06 00:19 | **3.669 %** | 19 features (Lags, Rolling stats, Sin/Cos calendar) | 85 | 5 | 0.08 |
| 2026-07-06 00:20 | **3.919 %** | 16 features (Lags, Rolling stats, Sin/Cos calendar) | 85 | 5 | 0.08 |
| 2026-07-06 00:21 | **3.909 %** | Dynamic features: 19 for h<=12, 16 for h>12 (No short lag) | 85 | 5 | 0.08 |
| 2026-07-06 00:25 | **2.981 %** | Thermosensitive XGBoost (Full lags + target temperature) | 90 | 5 | 0.08 |
| 2026-07-06 00:30 | **3.015 %** | XGBoost Super-Feature (Weather 4 + HDD/CDD + Inertia + holidays/bridges) | 95 | 5 | 0.07 |
| 2026-07-06 00:31 | **3.018 %** | XGBoost Super-Feature (Weather 4 + HDD/CDD + Inertia + holidays/bridges) | 95 | 5 | 0.07 |
| 2026-07-06 00:33 | **2.999 %** | XGBoost Super-Feature (Weather 4 + HDD/CDD + Inertia + holidays/bridges) | 95 | 5 | 0.07 |
| 2026-07-06 00:42 | **LightGBM** | **2.978 %** | LightGBM with native categorical handling (Weather + Calendar FR) | 110 | 31 | 0.06 |
