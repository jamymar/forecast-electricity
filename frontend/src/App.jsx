import React, { useState, useEffect, useRef } from 'react';
import { createClient } from '@supabase/supabase-js';
import Sidebar from './components/Sidebar';
import MetricCard from './components/MetricCard';
import ConsumptionChart from './components/ConsumptionChart';
import MixChart from './components/MixChart';
import CO2ImportsChart from './components/CO2ImportsChart';
import ComparisonTable from './components/ComparisonTable';
import ExtremePoints from './components/ExtremePoints';
import PeriodSummary from './components/PeriodSummary';
import { Activity, Flame, Leaf, Globe } from 'lucide-react';

import flatpickr from 'flatpickr';
import 'flatpickr/dist/flatpickr.min.css';

const French = {
  firstDayOfWeek: 1,
  weekdays: {
    shorthand: ["dim", "lun", "mar", "mer", "jeu", "ven", "sam"],
    longhand: ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
  },
  months: {
    shorthand: ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"],
    longhand: ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
  },
  ordinal: (nth) => nth > 1 ? "" : "er",
  rangeSeparator: " au ",
  weekAbbreviation: "Sem",
  scrollTitle: "Défiler pour augmenter la valeur",
  toggleTitle: "Cliquer pour basculer",
  time_24hr: true
};

const SUPABASE_URL = "https://crnhghkopqputqekbmid.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_uqYjWYc7tDT7w56tMiwisQ_hedNFgW5";
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export default function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [activeTab, setActiveTab] = useState('consumption');
  
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [activeRange, setActiveRange] = useState(7);

  const startInputRef = useRef(null);
  const endInputRef = useRef(null);
  const fpStartInstance = useRef(null);
  const fpEndInstance = useRef(null);

  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState({ type: 'info', message: 'Système prêt' });
  const [lastUpdate, setLastUpdate] = useState('--');

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.add('dark');
    document.body.style.backgroundColor = '#090d16';
    document.body.style.color = '#f8fafc';
  }, []);

  useEffect(() => {
    if (startInputRef.current && endInputRef.current) {
      const today = new Date();
      const config = {
        locale: French,
        dateFormat: "Y-m-d",
        maxDate: today,
        disableMobile: true
      };

      fpStartInstance.current = flatpickr(startInputRef.current, {
        ...config,
        defaultDate: startDate,
        onChange: (selectedDates, dateStr) => {
          if (dateStr && typeof dateStr === 'string' && !dateStr.includes('[object')) {
            setStartDate(dateStr);
            setActiveRange(null);
          }
        }
      });

      fpEndInstance.current = flatpickr(endInputRef.current, {
        ...config,
        defaultDate: endDate,
        onChange: (selectedDates, dateStr) => {
          if (dateStr && typeof dateStr === 'string' && !dateStr.includes('[object')) {
            setEndDate(dateStr);
            setActiveRange(null);
          }
        }
      });
    }

    return () => {
      if (fpStartInstance.current) fpStartInstance.current.destroy();
      if (fpEndInstance.current) fpEndInstance.current.destroy();
    };
  }, []);

  useEffect(() => {
    if (fpStartInstance.current) {
      fpStartInstance.current.setDate(startDate, false);
      if (endDate) fpStartInstance.current.set("maxDate", endDate);
    }
    if (fpEndInstance.current) {
      fpEndInstance.current.setDate(endDate, false);
      if (startDate) fpEndInstance.current.set("minDate", startDate);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, []);

  const [liveMetrics, setLiveMetrics] = useState({
    consumption: 0,
    decarbonatedShare: 0,
    co2Intensity: 0,
    imports: 0,
    importsLabel: 'Flux commercial instantané'
  });

  const [periodSummary, setPeriodSummary] = useState({
    enrShare: 0,
    co2Avg: 0,
    tradeBalance: '--'
  });

  const [extremePoints, setExtremePoints] = useState({
    peak: { value: 0, date: '--' },
    valley: { value: 0, date: '--' }
  });

  const [mapes, setMapes] = useState({
    rte: null,
    timesfm: null,
    chronos: null,
    lightgbm: null,
    naive: null
  });

  const [chartData, setChartData] = useState({
    dates: [],
    series: {
      consumption: [],
      forecast: [],
      timesfm: [],
      chronos: [],
      lightgbm: [],
      naive: [],
      nuclear: [],
      gas: [],
      coal: [],
      oil: [],
      wind: [],
      solar: [],
      hydro: [],
      bioenergy: [],
      net_imports: [],
      co2_intensity: []
    },
    averages: {
      nuclear: 0,
      gas: 0,
      solar: 0,
      wind: 0,
      hydro: 0,
      bioenergy: 0,
      coal: 0,
      oil: 0
    },
    startMs: 0,
    forecastEndMs: 0,
    historyEndMs: 0
  });

  const clean = (val) => (val !== null && val !== undefined) ? Math.round(Number(val)) : 0;

  const handleQuickRange = (days) => {
    setActiveRange(days);
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days);
    const newStart = start.toISOString().split('T')[0];
    const newEnd = end.toISOString().split('T')[0];
    setStartDate(newStart);
    setEndDate(newEnd);
    fetchData(newStart, newEnd);
  };

  const fetchData = async (start, end) => {
    const finalStart = (start && typeof start === 'string') ? start : startDate;
    const finalEnd = (end && typeof end === 'string') ? end : endDate;

    setIsLoading(true);
    setSystemStatus({ type: 'info', message: 'Chargement des données...' });
    
    try {
      const startIso = finalStart + "T00:00:00Z";
      const endIso = finalEnd + "T23:59:59Z";
      
      const endObj = new Date(finalEnd);
      endObj.setDate(endObj.getDate() + 2);
      const forecastEndIso = endObj.toISOString();

      const { data: historicalData, error: historicalError } = await supabase
        .from('historical_data')
        .select('*')
        .gte('timestamp', startIso)
        .lte('timestamp', endIso)
        .order('timestamp', { ascending: true });

      if (historicalError) throw historicalError;

      if (!historicalData || historicalData.length === 0) {
        setSystemStatus({ type: 'warning', message: 'Aucune donnée trouvée.' });
        setIsLoading(false);
        return;
      }

      const [
        { data: forecastData },
        { data: timesfmData },
        { data: chronosData },
        { data: naiveData },
        { data: lightgbmData }
      ] = await Promise.all([
        supabase.from('predictions_rte').select('*').gte('timestamp', startIso).lte('timestamp', forecastEndIso).order('timestamp', { ascending: true }),
        supabase.from('predictions_timesfm').select('*').gte('timestamp', startIso).lte('timestamp', forecastEndIso).order('timestamp', { ascending: true }),
        supabase.from('predictions_chronos').select('*').gte('timestamp', startIso).lte('timestamp', forecastEndIso).order('timestamp', { ascending: true }),
        supabase.from('predictions_naive').select('*').gte('timestamp', startIso).lte('timestamp', forecastEndIso).order('timestamp', { ascending: true }),
        supabase.from('predictions_lightgbm').select('*').gte('timestamp', startIso).lte('timestamp', forecastEndIso).order('timestamp', { ascending: true })
      ]);

      setSystemStatus({ type: 'success', message: `${historicalData.length} points chargés` });
      processData(historicalData, forecastData || [], timesfmData || [], chronosData || [], naiveData || [], lightgbmData || [], startIso, forecastEndIso);
    } catch (err) {
      console.error(err);
      setSystemStatus({ type: 'error', message: 'Erreur de chargement' });
    } finally {
      setIsLoading(false);
    }
  };

  const processData = (historicalData, forecastData, timesfmData, chronosData, naiveData, lightgbmData, startIso, forecastEndIso) => {
    const startMs = new Date(startIso).getTime();
    const forecastEndMs = new Date(forecastEndIso).getTime();
    const historyEndMs = historicalData.length > 0 ? new Date(historicalData[historicalData.length - 1].timestamp).getTime() : new Date().getTime();

    const dates = [];
    const consumption_series = [];
    
    const nuclear = [];
    const gas = [];
    const coal = [];
    const oil = [];
    const wind = [];
    const solar = [];
    const hydro = [];
    const bioenergy = [];
    const net_imports = [];
    const co2_intensity = [];

    const realMap = {};
    let peakVal = 0;
    let peakDate = '--';
    let valleyVal = Infinity;
    let valleyDate = '--';

    let totalCons = 0;
    let totalDecarb = 0;
    let totalWindSolarHydroBio = 0;
    let totalProd = 0;
    let totalCo2Intensity = 0;
    let totalNetImports = 0;

    historicalData.forEach(row => {
      const t = new Date(row.timestamp).getTime();
      dates.push(t);

      const consVal = clean(row.consumption);
      consumption_series.push([t, consVal]);
      realMap[t] = consVal;

      if (consVal > peakVal) {
        peakVal = consVal;
        peakDate = row.timestamp;
      }
      if (consVal < valleyVal && consVal > 0) {
        valleyVal = consVal;
        valleyDate = row.timestamp;
      }

      nuclear.push(clean(row.nuclear));
      gas.push(clean(row.gas));
      coal.push(clean(row.coal));
      oil.push(clean(row.oil));
      wind.push(clean(row.wind));
      solar.push(clean(row.solar));
      hydro.push(clean(row.hydro));
      bioenergy.push(clean(row.bioenergy));
      net_imports.push(clean(row.net_imports));
      co2_intensity.push(clean(row.co2_intensity));

      const decarb = clean(row.nuclear) + clean(row.wind) + clean(row.solar) + clean(row.hydro) + clean(row.bioenergy);
      const enr = clean(row.wind) + clean(row.solar) + clean(row.hydro) + clean(row.bioenergy);
      const prod = decarb + clean(row.gas) + clean(row.coal) + clean(row.oil);

      totalCons += consVal;
      totalDecarb += decarb;
      totalWindSolarHydroBio += enr;
      totalProd += prod;
      totalCo2Intensity += clean(row.co2_intensity);
      totalNetImports += clean(row.net_imports);
    });

    const calcMape = (data) => {
      let sum = 0;
      let count = 0;
      data.forEach(row => {
        const t = new Date(row.timestamp).getTime();
        const predVal = clean(row.predicted_value);
        const actual = realMap[t];
        if (actual && actual > 0) {
          sum += Math.abs((actual - predVal) / actual);
          count++;
        }
      });
      return count > 0 ? (sum / count) * 100 : null;
    };

    const mapeRte = calcMape(forecastData);
    const mapeTimesfm = calcMape(timesfmData);
    const mapeChronos = calcMape(chronosData);
    const mapeNaive = calcMape(naiveData);
    const mapeLightgbm = calcMape(lightgbmData);

    setMapes({
      rte: mapeRte,
      timesfm: mapeTimesfm,
      chronos: mapeChronos,
      naive: mapeNaive,
      lightgbm: mapeLightgbm
    });

    const mapSeries = (data) => data.map(row => [new Date(row.timestamp).getTime(), clean(row.predicted_value)]);
    
    const latest = historicalData[historicalData.length - 1];
    setLiveMetrics({
      consumption: clean(latest.consumption),
      decarbonatedShare: totalCons > 0 ? Math.round((totalDecarb / totalCons) * 100) : 0,
      co2Intensity: clean(latest.co2_intensity),
      imports: clean(latest.net_imports),
      importsLabel: clean(latest.net_imports) >= 0 ? "Flux commercial instantané (entrant)" : "Flux commercial instantané (sortant)"
    });

    setExtremePoints({
      peak: { value: peakVal, date: peakDate },
      valley: { value: valleyVal === Infinity ? 0 : valleyVal, date: valleyDate }
    });

    const periodEnrShare = totalProd > 0 ? Math.round((totalWindSolarHydroBio / totalProd) * 100) : 0;
    const periodCo2Avg = historicalData.length > 0 ? Math.round(totalCo2Intensity / historicalData.length) : 0;
    const tradeBalanceGWh = Math.round((totalNetImports / 1000) * 10) / 10;
    
    let tradeText = "Équilibré";
    if (tradeBalanceGWh > 0) tradeText = `Imp. ${tradeBalanceGWh} GWh`;
    else if (tradeBalanceGWh < 0) tradeText = `Exp. ${Math.abs(tradeBalanceGWh)} GWh`;

    setPeriodSummary({
      enrShare: periodEnrShare,
      co2Avg: periodCo2Avg,
      tradeBalance: tradeText
    });

    const getAvg = (arr) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;

    setChartData({
      dates,
      series: {
        consumption: consumption_series,
        forecast: mapSeries(forecastData),
        timesfm: mapSeries(timesfmData),
        chronos: mapSeries(chronosData),
        naive: mapSeries(naiveData),
        lightgbm: mapSeries(lightgbmData),
        nuclear, gas, coal, oil, wind, solar, hydro, bioenergy,
        net_imports: net_imports.map((val, idx) => [dates[idx], val]),
        co2_intensity: co2_intensity.map((val, idx) => [dates[idx], val])
      },
      averages: {
        nuclear: getAvg(nuclear),
        gas: getAvg(gas),
        solar: getAvg(solar),
        wind: getAvg(wind),
        hydro: getAvg(hydro),
        bioenergy: getAvg(bioenergy),
        coal: getAvg(coal),
        oil: getAvg(oil)
      },
      startMs,
      forecastEndMs,
      historyEndMs
    });

    setLastUpdate(new Date(latest.timestamp).toLocaleString('fr-FR', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
      timeZone: 'Europe/Paris'
    }) + " (Paris)");
  };

  return (
    <div className="min-h-screen font-sans pb-16 dark bg-slate-955 text-slate-100">
      <Sidebar 
        isCollapsed={isSidebarCollapsed} 
        setIsCollapsed={setIsSidebarCollapsed} 
      />

      <div className={`transition-all duration-300 ${isSidebarCollapsed ? 'pl-16' : 'pl-64'}`}>
        <div className="flex items-center justify-between px-8 py-3 border-b backdrop-blur-md sticky top-0 z-20 bg-slate-900/60 border-slate-800 text-slate-300">
          <div className="flex items-center gap-2.5 text-xs font-semibold">
            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`}></span>
            <span className="text-slate-400 uppercase tracking-wider">Statut :</span>
            <span>{systemStatus.message}</span>
          </div>
        </div>

        <main className="p-8 max-w-7xl mx-auto space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b pb-6 border-slate-800/80">
            <div className="space-y-1">
              <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r bg-clip-text text-transparent from-white via-slate-200 to-slate-400">
                Consommation Électrique
              </h1>
              <p className="text-sm text-slate-400 font-medium">Tableau de bord de l'électricité française en temps réel</p>
            </div>
            
            <div className="flex p-1 border rounded-lg shrink-0 bg-slate-900/80 border-slate-800">
              <button 
                onClick={() => setActiveTab('consumption')}
                className={`px-4 py-2 text-xs font-bold rounded-md transition-all
                  ${activeTab === 'consumption' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                Chronologie & Modèles
              </button>
              <button 
                onClick={() => setActiveTab('mix')}
                className={`px-4 py-2 text-xs font-bold rounded-md transition-all
                  ${activeTab === 'mix' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                Mix Énergétique
              </button>
              <button 
                onClick={() => setActiveTab('co2-imports')}
                className={`px-4 py-2 text-xs font-bold rounded-md transition-all
                  ${activeTab === 'co2-imports' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                CO₂ & Échanges
              </button>
            </div>
          </div>

          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard 
              title="Consommation en direct" 
              value={liveMetrics.consumption ? `${liveMetrics.consumption.toLocaleString()} MW` : '-- MW'}
              subtitle="Puissance appelée"
              icon={<Activity className="w-5 h-5" />}
            />
            <MetricCard 
              title="Production décarbonée" 
              value={`${liveMetrics.decarbonatedShare} %`}
              subtitle="Nucléaire + EnR"
              icon={<Leaf className="w-5 h-5" />}
            />
            <MetricCard 
              title="Intensité carbone" 
              value={liveMetrics.co2Intensity ? `${liveMetrics.co2Intensity} g/kWh` : '-- g/kWh'}
              subtitle="Émissions du mix"
              icon={<Flame className="w-5 h-5" />}
            />
            <MetricCard 
              title="Solde aux frontières" 
              value={liveMetrics.imports ? `${Math.abs(liveMetrics.imports).toLocaleString()} MW` : '-- MW'}
              subtitle={liveMetrics.importsLabel}
              icon={<Globe className="w-5 h-5" />}
            />
          </section>

          <section className="p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/50 border-slate-800/80">
            <div className="flex flex-wrap gap-2">
              <button 
                onClick={() => handleQuickRange(7)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200
                  ${activeRange === 7 
                    ? 'border-blue-500 bg-blue-600 text-white shadow-md font-bold' 
                    : 'border-slate-700/60 bg-slate-800/40 hover:bg-slate-800 text-slate-300 hover:text-white'}`}
              >
                7 derniers jours
              </button>
              <button 
                onClick={() => handleQuickRange(14)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200
                  ${activeRange === 14 
                    ? 'border-blue-500 bg-blue-600 text-white shadow-md font-bold' 
                    : 'border-slate-700/60 bg-slate-800/40 hover:bg-slate-800 text-slate-300 hover:text-white'}`}
              >
                14 jours
              </button>
              <button 
                onClick={() => handleQuickRange(30)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200
                  ${activeRange === 30 
                    ? 'border-blue-500 bg-blue-600 text-white shadow-md font-bold' 
                    : 'border-slate-700/60 bg-slate-800/40 hover:bg-slate-800 text-slate-300 hover:text-white'}`}
              >
                30 derniers jours
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-semibold">
              <div className="flex items-center gap-2">
                <label className="text-slate-400 font-sans">Du</label>
                <input 
                  type="text" 
                  ref={startInputRef}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 !bg-slate-800 !text-white outline-none focus:border-blue-500 transition-colors w-28 text-center cursor-pointer"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-slate-400 font-sans">Au</label>
                <input 
                  type="text" 
                  ref={endInputRef}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 !bg-slate-800 !text-white outline-none focus:border-blue-500 transition-colors w-28 text-center cursor-pointer"
                />
              </div>
              <button 
                onClick={fetchData}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 font-bold transition-colors shadow-md text-white"
              >
                Valider
              </button>
            </div>
          </section>

          <div key={activeTab} className="tab-fade-in">
            {activeTab === 'consumption' && (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
                <div className="lg:col-span-3 space-y-6">
                  <ConsumptionChart 
                    dates={chartData.dates}
                    series={chartData.series}
                    startMs={chartData.startMs}
                    forecastEndMs={chartData.forecastEndMs}
                    theme="dark"
                    isLoading={isLoading}
                  />
                  <ComparisonTable mapes={mapes} />
                </div>
                
                <div className="space-y-6">
                  <ExtremePoints 
                    peak={extremePoints.peak}
                    valley={extremePoints.valley}
                  />
                  <PeriodSummary 
                    enrShare={periodSummary.enrShare}
                    co2Avg={periodSummary.co2Avg}
                    tradeBalance={periodSummary.tradeBalance}
                  />
                </div>
              </div>
            )}

            {activeTab === 'mix' && (
              <MixChart 
                dates={chartData.dates}
                series={chartData.series}
                averages={chartData.averages}
                startMs={chartData.startMs}
                historyEndMs={chartData.historyEndMs}
                theme="dark"
                isLoading={isLoading}
              />
            )}

            {activeTab === 'co2-imports' && (
              <CO2ImportsChart 
                dates={chartData.dates}
                series={chartData.series}
                startMs={chartData.startMs}
                historyEndMs={chartData.historyEndMs}
                theme="dark"
                isLoading={isLoading}
              />
            )}
          </div>

          <footer className="border-t pt-6 text-xs text-slate-550 flex flex-col sm:flex-row justify-between gap-4 border-slate-800/80">
            <p>© 2026 éCO2mix • Données RTE / ODRE</p>
            <p>Dernière mise à jour : <span className="text-slate-400 font-semibold">{lastUpdate}</span></p>
          </footer>
        </main>
      </div>
    </div>
  );
}
