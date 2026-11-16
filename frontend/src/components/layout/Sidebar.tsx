import React from 'react';
import {
  LayoutDashboard,
  CloudLightning,
  AlertTriangle,
  Layers,
  Navigation,
  Cpu,
  Database,
  CloudSun,
  Globe,
  Newspaper,
  Compass,
} from 'lucide-react';
import { SystemHealthData } from '../../types';
import { HealthBadge } from '../status/HealthBadge';

export type PageId =
  | 'command-center'
  | 'pre-disaster-risk'
  | 'misinformation'
  | 'multimodal'
  | 'rescue-routing';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  health: SystemHealthData | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  health,
}) => {
  const navItems: Array<{ id: PageId; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'command-center', label: 'COMMAND CENTER', icon: LayoutDashboard },
    { id: 'pre-disaster-risk', label: 'PRE-DISASTER RISK', icon: CloudLightning },
    { id: 'misinformation', label: 'MISINFORMATION', icon: AlertTriangle },
    { id: 'multimodal', label: 'MULTIMODAL ANALYSIS', icon: Layers },
    { id: 'rescue-routing', label: 'RESCUE ROUTING', icon: Navigation },
  ];

  const services = health?.services;

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col justify-between bg-[#0B0F17] border-r border-[#1F2937] min-h-[calc(100vh-53px)] select-none">
      {/* Navigation Links */}
      <div className="p-4 space-y-6">
        <div className="px-2 py-1">
          <p className="text-[11px] font-mono tracking-widest text-slate-500 uppercase">
            Operations Console
          </p>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded text-xs font-mono font-medium tracking-wide transition-colors ${
                  isActive
                    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#111827] border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom: System Health Telemetry */}
      <div className="p-4 border-t border-[#1F2937] bg-[#0E131F]/50">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase font-semibold">
            SYSTEM HEALTH
          </span>
          <HealthBadge
            status={health?.overall_status || 'UNKNOWN'}
            label={health?.overall_status || 'CHECKING'}
          />
        </div>

        <div className="space-y-2 font-mono text-[11px]">
          {/* AI Engine */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-slate-500" />
              <span>AI ENGINE</span>
            </div>
            <HealthBadge status={services?.ai_engine.status || 'OFFLINE'} />
          </div>

          {/* Data Pipeline */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <Database className="w-3.5 h-3.5 text-slate-500" />
              <span>DATA PIPELINE</span>
            </div>
            <HealthBadge status={services?.data_pipeline.status || 'ONLINE'} />
          </div>

          {/* Weather */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <CloudSun className="w-3.5 h-3.5 text-slate-500" />
              <span>WEATHER</span>
            </div>
            <HealthBadge status={services?.weather.status || 'UNAVAILABLE'} />
          </div>

          {/* GDACS */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              <span>GDACS</span>
            </div>
            <HealthBadge status={services?.gdacs.status || 'UNAVAILABLE'} />
          </div>

          {/* GDELT News */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <Newspaper className="w-3.5 h-3.5 text-slate-500" />
              <span>NEWS (GDELT)</span>
            </div>
            <HealthBadge status={services?.gdelt.status || 'UNAVAILABLE'} />
          </div>

          {/* Routing (OSRM) */}
          <div className="flex items-center justify-between px-2 py-1 rounded bg-[#111827] border border-[#1F2937]/60">
            <div className="flex items-center gap-2 text-slate-400">
              <Compass className="w-3.5 h-3.5 text-slate-500" />
              <span>ROUTING</span>
            </div>
            <HealthBadge status={services?.osrm.status || 'UNAVAILABLE'} />
          </div>
        </div>
      </div>
    </aside>
  );
};
