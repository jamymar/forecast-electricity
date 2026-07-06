import React from 'react';
import { Award } from 'lucide-react';

export default function ComparisonTable({ mapes }) {
  const models = [
    { id: 'rte', name: 'Prévision RTE', source: "Réseau de Transport d'Électricité", mape: mapes.rte },
    { id: 'timesfm', name: 'Google TimesFM 2.5', source: 'Zero-Shot IA (1024 points de contexte)', mape: mapes.timesfm },
    { id: 'lightgbm', name: 'LightGBM Direct', source: "Boosting d'arbres (variables qualitatives natives + météo)", mape: mapes.lightgbm },
    { id: 'naive', name: 'Modèle Naïf Saisonnier (J-7)', source: 'Baseline (Copie de la semaine précédente)', mape: mapes.naive }
  ];

  const validMapes = models.filter(m => m.mape !== null && m.mape !== undefined).map(m => m.mape);
  const minMape = validMapes.length > 0 ? Math.min(...validMapes) : null;

  return (
    <div className="p-6 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Comparatif de Performance des Modèles</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">Erreur moyenne absolue en pourcentage (MAPE) sur la période sélectionnée</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700/60 text-slate-500 dark:text-slate-400 font-semibold">
              <th className="py-3 px-4">Modèle</th>
              <th className="py-3 px-4">Description / Source</th>
              <th className="py-3 px-4 text-right">MAPE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {models.map((model) => {
              const isBest = minMape !== null && model.mape === minMape;
              const mapeText = model.mape !== null && model.mape !== undefined ? `${model.mape.toFixed(2)} %` : 'N/A';

              return (
                <tr 
                  key={model.id} 
                  className={`transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/20 
                    ${isBest 
                      ? 'bg-emerald-500/5 text-emerald-600 dark:text-emerald-300 font-semibold' 
                      : 'text-slate-700 dark:text-slate-300'
                    }`}
                >
                  <td className="py-3.5 px-4 flex items-center gap-2">
                    {isBest && <Award className="w-4 h-4 text-emerald-500 dark:text-emerald-400 shrink-0" />}
                    <span>{model.name}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-555 dark:text-slate-400 text-xs">{model.source}</td>
                  <td className="py-3.5 px-4 text-right font-bold">
                    {mapeText}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
