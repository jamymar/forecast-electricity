import React, { useEffect, useRef } from 'react';
import ApexCharts from 'apexcharts';

export default function CO2ImportsChart({ dates, series, startMs, historyEndMs, theme, isLoading }) {
  const co2ChartRef = useRef(null);
  const importsChartRef = useRef(null);
  const co2ChartInstance = useRef(null);
  const importsChartInstance = useRef(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    if (co2ChartRef.current && series.co2_intensity && series.co2_intensity.length > 0) {
      const gridStyle = {
        borderColor: isDark ? 'rgba(51, 65, 85, 0.3)' : 'rgba(226, 232, 240, 0.6)',
        strokeDashArray: 4
      };

      const co2Options = {
        chart: {
          type: 'line',
          height: 350,
          toolbar: { show: false },
          fontFamily: 'Inter, sans-serif',
          background: 'transparent'
        },
        theme: { mode: theme },
        colors: ['#d32f2f'],
        stroke: { curve: 'smooth', width: 3 },
        dataLabels: { enabled: false },
        grid: gridStyle,
        xaxis: {
          type: 'datetime',
          categories: dates,
          min: startMs,
          max: historyEndMs
        },
        yaxis: {
          title: { text: 'g CO₂ / kWh' }
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
        series: [
          { name: 'Intensité Carbone', data: series.co2_intensity || [] }
        ]
      };

      if (co2ChartInstance.current) co2ChartInstance.current.destroy();
      co2ChartInstance.current = new ApexCharts(co2ChartRef.current, co2Options);
      co2ChartInstance.current.render();
    }

    if (importsChartRef.current && series.net_imports && series.net_imports.length > 0) {
      const gridStyle = {
        borderColor: isDark ? 'rgba(51, 65, 85, 0.3)' : 'rgba(226, 232, 240, 0.6)',
        strokeDashArray: 4
      };

      const importsOptions = {
        chart: {
          type: 'area',
          height: 350,
          toolbar: { show: false },
          fontFamily: 'Inter, sans-serif',
          background: 'transparent'
        },
        theme: { mode: theme },
        colors: ['#7c3aed'],
        stroke: { curve: 'smooth', width: 2 },
        dataLabels: { enabled: false },
        fill: { type: 'gradient', gradient: { opacityFrom: 0.3, opacityTo: 0.02 } },
        grid: gridStyle,
        xaxis: {
          type: 'datetime',
          categories: dates,
          min: startMs,
          max: historyEndMs
        },
        yaxis: {
          labels: { formatter: (v) => v.toLocaleString() }
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
        series: [
          { name: 'Solde Net Import', data: series.net_imports || [] }
        ]
      };

      if (importsChartInstance.current) importsChartInstance.current.destroy();
      importsChartInstance.current = new ApexCharts(importsChartRef.current, importsOptions);
      importsChartInstance.current.render();
    }

    return () => {
      if (co2ChartInstance.current) co2ChartInstance.current.destroy();
      if (importsChartInstance.current) importsChartInstance.current.destroy();
    };
  }, [series, dates, startMs, historyEndMs, theme]);

  const hasCo2Data = series.co2_intensity && series.co2_intensity.length > 0;
  const hasImportsData = series.net_imports && series.net_imports.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="p-6 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-md flex flex-col gap-4 relative overflow-hidden">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Taux d'émissions de CO₂</h2>
          <p className="text-xs text-slate-550 dark:text-slate-400">Intensité carbone de la production d'électricité (g CO₂ / kWh)</p>
        </div>
        <div className="relative w-full min-h-[300px] flex items-center justify-center">
          {hasCo2Data ? (
            <div ref={co2ChartRef} className="w-full" />
          ) : (
            <div className="text-slate-500 dark:text-slate-400 text-sm font-semibold animate-pulse">
              Chargement du graphique...
            </div>
          )}
          {hasCo2Data && isLoading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-slate-950/5 rounded-lg">
              <div className="flex flex-col items-center gap-2 bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">Mise à jour...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-md flex flex-col gap-4 relative overflow-hidden">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Solde commercial d'échanges physiques</h2>
          <p className="text-xs text-slate-555 dark:text-slate-400">Puissance échangée (Exportation &lt; 0 | Importation &gt; 0)</p>
        </div>
        <div className="relative w-full min-h-[300px] flex items-center justify-center">
          {hasImportsData ? (
            <div ref={importsChartRef} className="w-full" />
          ) : (
            <div className="text-slate-500 dark:text-slate-400 text-sm font-semibold animate-pulse">
              Chargement du graphique...
            </div>
          )}
          {hasImportsData && isLoading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-slate-950/5 rounded-lg">
              <div className="flex flex-col items-center gap-2 bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">Mise à jour...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
