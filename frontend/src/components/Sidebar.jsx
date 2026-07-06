import React from 'react';
import { LayoutDashboard, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar({ isCollapsed, setIsCollapsed }) {
  return (
    <aside 
      className={`fixed top-0 left-0 h-screen z-30 flex flex-col justify-between border-r transition-all duration-300 
        bg-slate-900 border-slate-800 text-slate-100
        ${isCollapsed ? 'w-16' : 'w-64'}`}
    >
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/20 shrink-0">
            <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-ping absolute"></span>
            <span className="w-2.5 h-2.5 bg-blue-500 rounded-full relative"></span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-lg tracking-wide text-white">éCO2mix</span>
              <span className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">Régulateur</span>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        <a 
          href="#" 
          onClick={(e) => e.preventDefault()}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors border bg-blue-600/10 text-blue-400 border-blue-500/20"
        >
          <LayoutDashboard className="w-5 h-5" />
          {!isCollapsed && <span>Consommation</span>}
        </a>
      </nav>

      <div className="p-3 border-t flex flex-col gap-2 border-slate-800">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg transition-colors text-slate-400 hover:text-slate-200 hover:bg-slate-850"
        >
          {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          {!isCollapsed && <span className="ml-3 text-sm">Replier le menu</span>}
        </button>
      </div>
    </aside>
  );
}
