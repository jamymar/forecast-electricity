import React, { useEffect, useRef } from 'react';
import ApexCharts from 'apexcharts';

export default function MixChart({ dates, series, averages, startMs, historyEndMs, theme, isLoading }) {
  const areaChartRef = useRef(null);
  const donutChartRef = useRef(null);
  const areaChartInstance = useRef(null);
  const donutChartInstance = useRef(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    if (areaChartRef.current && series.nuclear && series.nuclear.length > 0) {
      const gridStyle = {
        borderColor: isDark ? 'rgba(51, 65, 85, 0.3)' : 'rgba(226, 232, 240, 0.6)',
        strokeDashArray: 4
      };

      const areaOptions = {
        chart: {
          type: 'area',
          height: 450,
          stacked: true,
          toolbar: { show: false },
          zoom: { enabled: false },
          fontFamily: 'Inter, sans-serif',
          background: 'transparent'
        },
        theme: { mode: theme },
        colors: ['#fbbf24', '#f87171', '#fcd34d', '#60a5fa', '#3b82f6', '#34d399', '#4b5563', '#9ca3af'],
        stroke: { curve: 'smooth', width: 0.5 },
        dataLabels: { enabled: false },
        fill: { type: 'solid', opacity: 0.8 },
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
        legend: {
          position: 'top',
          horizontalAlign: 'left',
          itemMargin: { horizontal: 15, vertical: 5 },
          markers: { offsetX: -6 }
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
          { name: 'Nucléaire', data: series.nuclear || [] },
          { name: 'Gaz', data: series.gas || [] },
          { name: 'Solaire', data: series.solar || [] },
          { name: 'Éolien', data: series.wind || [] },
          { name: 'Hydraulique', data: series.hydro || [] },
          { name: 'Bioénergies', data: series.bioenergy || [] },
          { name: 'Charbon', data: series.coal || [] },
          { name: 'Fioul', data: series.oil || [] }
        ]
      };

      if (areaChartInstance.current) areaChartInstance.current.destroy();
      areaChartInstance.current = new ApexCharts(areaChartRef.current, areaOptions);
      areaChartInstance.current.render();
    }

    if (donutChartRef.current && averages.nuclear !== undefined) {
      const donutOptions = {
        chart: {
          type: 'donut',
          height: 380,
          fontFamily: 'Inter, sans-serif',
          background: 'transparent',
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            animateGradually: { enabled: true, delay: 150 },
            dynamicAnimation: { enabled: true, speed: 350 }
          },
          dropShadow: {
            enabled: true,
            blur: 3,
            left: 0,
            top: 2,
            opacity: isDark ? 0.15 : 0.04
          }
        },
        theme: { mode: theme },
        colors: ['#fbbf24', '#f87171', '#fcd34d', '#60a5fa', '#3b82f6', '#34d399', '#4b5563', '#9ca3af'],
        labels: ['Nucléaire', 'Gaz', 'Solaire', 'Éolien', 'Hydraulique', 'Bioénergies', 'Charbon', 'Fioul'],
        stroke: { show: false, width: 0 },
        dataLabels: { enabled: false },
        fill: {
          type: 'gradient',
          gradient: {
            shade: 'dark',
            type: 'vertical',
            shadeIntensity: 0.2,
            inverseColors: false,
            opacityFrom: 0.9,
            opacityTo: 1,
            stops: [0, 100]
          }
        },
        states: {
          hover: { filter: { type: 'darken', value: 0.88 } }
        },
        tooltip: {
          enabled: true,
          theme: theme,
          y: {
            formatter: (value, { globals }) => {
              const series = globals.series;
              const total = series.reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${Number(value).toLocaleString()} MW (${percentage}%)`;
            }
          }
        },
        legend: {
          position: 'bottom',
          markers: { offsetX: -6 }
        },
        plotOptions: {
          pie: {
            donut: {
              size: '72%',
              labels: {
                show: true,
                name: { 
                  show: true,
                  fontSize: '13px',
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 600,
                  color: isDark ? '#94a3b8' : '#64748b',
                  offsetY: -8
                },
                value: { 
                  show: true,
                  fontSize: '22px',
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 800,
                  color: isDark ? '#ffffff' : '#0f172a',
                  offsetY: 6,
                  formatter: (v) => `${Number(v).toLocaleString()} MW`
                },
                total: {
                  show: true,
                  label: 'Production Moyenne',
                  fontSize: '11px',
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 700,
                  color: isDark ? '#64748b' : '#94a3b8',
                  formatter: (w) => {
                    const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                    return `${total.toLocaleString()} MW`;
                  }
                }
              }
            }
          }
        },
        series: [
          averages.nuclear || 0,
          averages.gas || 0,
          averages.solar || 0,
          averages.wind || 0,
          averages.hydro || 0,
          averages.bioenergy || 0,
          averages.coal || 0,
          averages.oil || 0
        ]
      };

      if (donutChartInstance.current) donutChartInstance.current.destroy();
      donutChartInstance.current = new ApexCharts(donutChartRef.current, donutOptions);
      donutChartInstance.current.render();
    }

    return () => {
      if (areaChartInstance.current) areaChartInstance.current.destroy();
      if (donutChartInstance.current) donutChartInstance.current.destroy();
    };
  }, [series, averages, dates, startMs, historyEndMs, theme]);

  const hasAreaData = series.nuclear && series.nuclear.length > 0;
  const hasDonutData = averages.nuclear !== undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 p-6 rounded-xl border bg-white dark:bg-slate-800/40 border-slate-200 dark:border-slate-800/50 backdrop-blur-sm shadow-md flex flex-col gap-4 relative overflow-hidden">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Chronologie de la production par filière</h2>
          <p className="text-xs text-slate-550 dark:text-slate-400">Cumul de puissance injectée sur le réseau par type d'énergie (MW)</p>
        </div>
        <div className="relative w-full min-h-[450px] flex items-center justify-center">
          {hasAreaData && (
            <div className={`w-full transition-all duration-300 ${isLoading ? 'blur-[1.5px] opacity-40 pointer-events-none' : ''}`}>
              <div ref={areaChartRef} className="w-full" />
            </div>
          )}
          {!hasAreaData && (
            <div className="text-slate-500 dark:text-slate-400 text-sm font-semibold animate-pulse">
              Chargement du graphique...
            </div>
          )}
          {hasAreaData && isLoading && (
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
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Part moyenne sur la période</h2>
          <p className="text-xs text-slate-555 dark:text-slate-400">Répartition moyenne de la production électrique</p>
        </div>
        <div className="relative w-full flex items-center justify-center flex-1 min-h-[380px]">
          {hasDonutData && (
            <div className={`w-full transition-all duration-300 ${isLoading ? 'blur-[1.5px] opacity-40 pointer-events-none' : ''}`}>
              <div ref={donutChartRef} className="w-full" />
            </div>
          )}
          {!hasDonutData && (
            <div className="text-slate-555 dark:text-slate-400 text-sm font-semibold animate-pulse">
              Chargement...
            </div>
          )}
          {hasDonutData && isLoading && (
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
