import React from 'react';

export default function PeriodSummary({ enrShare, co2Avg, tradeBalance }) {
  return (
    <div className="p-4 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-sm space-y-3">
      <div>
        <h2 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">Bilan de la Période</h2>
      </div>
      
      <div className="space-y-2 text-xs font-medium">
        <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700/40">
          <span className="text-slate-555 dark:text-slate-400">Part EnR prod.</span>
          <span className="text-slate-850 dark:text-slate-200 font-bold">{enrShare ? `${enrShare} %` : '-- %'}</span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700/40">
          <span className="text-slate-555 dark:text-slate-400">Intensité CO₂ moy.</span>
          <span className="text-slate-850 dark:text-slate-200 font-bold">{co2Avg ? `${co2Avg} g/kWh` : '-- g/kWh'}</span>
        </div>
        <div className="flex justify-between items-center py-2">
          <span className="text-slate-555 dark:text-slate-400">Solde commercial</span>
          <span className="text-slate-850 dark:text-slate-200 font-bold">{tradeBalance || '--'}</span>
        </div>
      </div>
    </div>
  );
}
