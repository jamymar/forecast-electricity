import React from 'react';

export default function MetricCard({ title, value, subtitle, icon }) {
  return (
    <div className="relative overflow-hidden p-5 rounded-xl border transition-all duration-300 bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 hover:border-slate-350 dark:hover:border-slate-600/50 backdrop-blur-sm shadow-sm hover:shadow-md group">
      <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/15 transition-all"></div>
      
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <h3 className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">{title}</h3>
          <p className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">{value}</p>
          <span className="text-xs text-slate-555 dark:text-slate-400 font-medium">{subtitle}</span>
        </div>
        {icon && <div className="text-slate-400 dark:text-slate-400 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors">{icon}</div>}
      </div>
    </div>
  );
}
