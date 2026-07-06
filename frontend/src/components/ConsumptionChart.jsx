import React, { useEffect, useRef } from 'react';
import ApexCharts from 'apexcharts';
import { Maximize2 } from 'lucide-react';

export default function ConsumptionChart({ series, startMs, forecastEndMs, theme, isLoading }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    if (!chartRef.current) return;
    if (!series.consumption || series.consumption.length === 0) return;

    const gridStyle = {
      borderColor: isDark ? 'rgba(51, 65, 85, 0.3)' : 'rgba(226, 232, 240, 0.6)',
      strokeDashArray: 4
    };

    const options = {
      chart: {
        type: 'line',
        height: 450,
        toolbar: { show: false },
        zoom: { enabled: true, type: 'x', autoScaleYaxis: true },
        fontFamily: 'Inter, sans-serif',
        background: 'transparent'
      },
      theme: { mode: theme },
      colors: ['#0056a4', '#7c3aed', '#10b981', '#f58220', '#94a3b8'],
      stroke: { curve: 'smooth', width: [3, 2.5, 2.5, 2.5, 2.5] },
      dataLabels: { enabled: false },
      markers: { size: 0, hover: { size: 5 } },
      grid: gridStyle,
      xaxis: {
        type: 'datetime',
        min: startMs,
        max: forecastEndMs
      },
      yaxis: {
        labels: { formatter: (v) => v ? v.toLocaleString() : v }
      },
      tooltip: {
        shared: true,
        intersect: false,
        theme: theme,
        x: {
          formatter: (val) => new Date(val).toLocaleString('fr-FR', {
            day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris'
          })
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'left',
        itemMargin: { horizontal: 15, vertical: 5 },
        markers: { offsetX: -6 }
      },
      series: [
        { name: 'Consommation réelle', data: series.consumption || [] },
        { name: 'Prévision RTE', data: series.forecast || [] },
        { name: 'Google TimesFM', data: series.timesfm || [] },
        { name: 'LightGBM Direct', data: series.lightgbm || [] },
        { name: 'Modèle Naïf (J-7)', data: series.naive || [] }
      ]
    };

    chartInstance.current = new ApexCharts(chartRef.current, options);
    chartInstance.current.render();

    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, [series, startMs, forecastEndMs, theme]);

  const handleResetZoom = () => {
    if (chartInstance.current) {
      chartInstance.current.updateOptions({
        xaxis: { min: undefined, max: undefined }
      });
    }
  };

  const hasData = series.consumption && series.consumption.length > 0;

  return (
    <div className="p-6 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-md flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white font-sans">Suivi & Prévisions de Consommation</h2>
          <p className="text-xs text-slate-550 dark:text-slate-400">Consommation réelle vs prévisions (MW)</p>
        </div>
        <button 
          onClick={handleResetZoom}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-600/50 transition-colors shadow-sm"
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span>Reset Zoom</span>
        </button>
      </div>
      
      <div className="relative w-full min-h-[450px] flex items-center justify-center">
        {hasData && (
          <div className={`w-full transition-all duration-300 ${isLoading ? 'blur-[1.5px] opacity-40 pointer-events-none' : ''}`}>
            <div ref={chartRef} className="w-full" />
          </div>
        )}
        
        {!hasData && (
          <div className="text-slate-555 dark:text-slate-400 text-sm font-semibold animate-pulse">
            Chargement du graphique...
          </div>
        )}

        {hasData && isLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-slate-950/5 rounded-lg">
            <div className="flex flex-col items-center gap-2 bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
              <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">Mise à jour...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
