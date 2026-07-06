import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';

export default function ExtremePoints({ peak, valley }) {
  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === '--') return '--';
    const dateObj = new Date(dateStr);
    return dateObj.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Paris'
    }) + ' (Paris)';
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Points Extrêmes</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
        {/* Pic */}
        <div className="flex items-center gap-4 p-4 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 hover:border-red-500/20 transition-all shadow-sm">
          <div className="p-3 rounded-lg bg-red-500/10 text-red-555 dark:text-red-400 shrink-0">
            <ArrowUp className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pic de consommation</span>
            <p className="text-xl font-black text-slate-900 dark:text-white">{peak.value ? `${peak.value.toLocaleString()} MW` : '-- MW'}</p>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block truncate">{formatDate(peak.date)}</span>
          </div>
        </div>

        {/* Creux */}
        <div className="flex items-center gap-4 p-4 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 hover:border-blue-500/20 transition-all shadow-sm">
          <div className="p-3 rounded-lg bg-blue-500/10 text-blue-555 dark:text-blue-400 shrink-0">
            <ArrowDown className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Creux de consommation</span>
            <p className="text-xl font-black text-slate-900 dark:text-white">{valley.value ? `${valley.value.toLocaleString()} MW` : '-- MW'}</p>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block truncate">{formatDate(valley.date)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
