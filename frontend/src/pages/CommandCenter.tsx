import React, { useState } from 'react';
import {
  AlertTriangle,
  Users,
  ShieldCheck,
  Globe,
  Radio,
  Flame,
  Plus,
  RefreshCw,
  Cpu,
  Layers,
} from 'lucide-react';
import { DashboardData, Incident, SystemHealthData, WeatherData } from '../types';
import { KpiCard } from '../components/cards/KpiCard';
import { WeatherCard } from '../components/cards/WeatherCard';
import { IncidentMap } from '../components/maps/IncidentMap';
import { IncidentFeed } from '../components/incidents/IncidentFeed';
import { IncidentModal } from '../components/incidents/IncidentModal';
import { SourceBadge } from '../components/status/SourceBadge';
import { HealthBadge } from '../components/status/HealthBadge';
import { api } from '../services/api';

interface CommandCenterProps {
  dashboard: DashboardData | null;
  health: SystemHealthData | null;
  loading: boolean;
  onRefresh: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  dashboard,
  health,
  loading,
  onRefresh,
}) => {
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [modalIncident, setModalIncident] = useState<Incident | null>(null);
  const [syncingGdacs, setSyncingGdacs] = useState(false);
  const [syncGdacsNotice, setSyncGdacsNotice] = useState<string | null>(null);

  const kpis = dashboard?.kpis || {
    active_incidents: 0,
    critical_alerts: 0,
    verified_reports: 0,
    dispatched_teams: 0,
    people_at_risk: 0,
    gdacs_incidents: 0,
  };

  const incidents = dashboard?.recent_incidents || [];
  const weather = dashboard?.weather || null;
  const teams = dashboard?.active_teams || [];

  const handleSyncGdacs = async () => {
    setSyncingGdacs(true);
    setSyncGdacsNotice(null);
    try {
      const res = await api.getGDACS(250, true);
      if (res.source === 'LIVE') {
        setSyncGdacsNotice(`Synchronized ${res.total_events} live global alerts (Wildfires, Floods, Earthquakes, etc.).`);
        onRefresh();
      } else {
        setSyncGdacsNotice(res.error || 'GDACS feed unavailable');
      }
    } catch (e: any) {
      setSyncGdacsNotice(`GDACS sync error: ${e.message}`);
    } finally {
      setSyncingGdacs(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner / Operational Notice */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3 rounded bg-[#111827] border border-[#1F2937]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-100">
                ACTIVE MONITORING SECTOR: ODISHA / BAY OF BENGAL
              </span>
              <SourceBadge source="LIVE Open-Meteo" short={true} />
            </div>
            <p className="text-[11px] font-mono text-slate-400">
              Multimodal ML inference active: XGBoost Hazard Index, DistilBERT Social NLP, ResNet-50 Vision
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {syncGdacsNotice && (
            <span className="text-[11px] font-mono text-sky-400 mr-2">
              {syncGdacsNotice}
            </span>
          )}
          <button
            onClick={handleSyncGdacs}
            disabled={syncingGdacs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] text-xs font-mono text-slate-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncingGdacs ? 'animate-spin' : ''}`} />
            <span>{syncingGdacs ? 'SYNCING GDACS...' : 'SYNC GDACS RSS'}</span>
          </button>
        </div>
      </div>

      {/* KPI / Telemetry Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          label="Active Incidents"
          value={kpis.active_incidents}
          accent={kpis.active_incidents > 0 ? 'accent' : 'default'}
          icon={Flame}
          subtext="Requiring response"
        />
        <KpiCard
          label="Critical Alerts"
          value={kpis.critical_alerts}
          accent={kpis.critical_alerts > 0 ? 'critical' : 'safe'}
          icon={AlertTriangle}
          subtext="Immediate action"
        />
        <KpiCard
          label="People At Risk"
          value={kpis.people_at_risk?.toLocaleString()}
          accent="warning"
          icon={Users}
          subtext="Estimated impact"
        />
        <KpiCard
          label="Rescue Dispatched"
          value={kpis.dispatched_teams}
          accent="safe"
          icon={ShieldCheck}
          subtext="Teams en route"
        />
        <KpiCard
          label="Verified Reports"
          value={kpis.verified_reports}
          accent="accent"
          icon={Radio}
          subtext="DistilBERT verified"
        />
        <KpiCard
          label="GDACS Events"
          value={kpis.gdacs_incidents}
          accent="default"
          icon={Globe}
          tag="LIVE"
          subtext="Global alerts merged"
        />
      </div>

      {/* Main Section: Interactive Tactical Map + Live Incident Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[560px]">
        {/* Map on Left (7 cols on lg) */}
        <div className="lg:col-span-8 h-full">
          <IncidentMap
            incidents={incidents}
            teams={teams}
            selectedIncident={selectedIncident}
            onSelectIncident={(inc) => {
              setSelectedIncident(inc);
              setModalIncident(inc);
            }}
          />
        </div>

        {/* Live Incident Feed on Right (4 cols on lg) */}
        <div className="lg:col-span-4 h-full">
          <IncidentFeed
            incidents={incidents}
            selectedId={selectedIncident?.incident_id}
            onSelectIncident={(inc) => {
              setSelectedIncident(inc);
              setModalIncident(inc);
            }}
            loading={loading}
          />
        </div>
      </div>

      {/* Bottom Telemetry Row: Weather + Risk Summary + Health Telemetry */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Weather Telemetry */}
        <WeatherCard weather={weather} loading={loading} />

        {/* AI Risk Model Telemetry Summary */}
        <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              <span className="text-xs font-mono font-bold text-slate-200 uppercase">
                AI Risk Intelligence
              </span>
            </div>
            <SourceBadge source="MODEL GENERATED XGBoost" />
          </div>

          <div className="p-3 rounded bg-[#161E2E] border border-[#1F2937] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">MODEL ARCHITECTURE:</span>
              <span className="font-semibold text-slate-200">XGBoost Regressor</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">DATASET:</span>
              <span className="text-slate-300">Odisha Daily Rain + IBTrACS</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">EXPLAINABILITY:</span>
              <span className="text-emerald-400 font-semibold">SHAP TreeExplainer</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">OPERATIONAL THRESHOLD:</span>
              <span className="text-amber-400 font-semibold">70.0 Score Trigger</span>
            </div>
          </div>

          <div className="mt-3 text-[11px] font-mono text-slate-400">
            Open the <strong>Pre-Disaster Risk</strong> tab to run simulations or explain predictions via SHAP.
          </div>
        </div>

        {/* Operations Activity Timeline */}
        <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span className="text-xs font-mono font-bold text-slate-200 uppercase">
                Operations Timeline
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">LIVE LOG</span>
          </div>

          <div className="space-y-2 max-h-[140px] overflow-y-auto custom-scrollbar font-mono text-[11px] pr-1">
            {dashboard?.timeline && dashboard.timeline.length > 0 ? (
              dashboard.timeline.map((evt, idx) => (
                <div key={idx} className="p-1.5 rounded bg-[#161E2E] border border-[#1F2937]/50 flex items-start gap-2">
                  <span className="text-sky-400 flex-shrink-0">{evt.time}</span>
                  <span className="text-slate-300 line-clamp-2">{evt.description}</span>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-center py-4">No events logged yet.</div>
            )}
          </div>

          <div className="mt-2 text-[10px] font-mono text-slate-500 text-right">
            Disaster Operations Hub v2.0
          </div>
        </div>
      </div>

      {/* Incident Details & Dispatch Modal */}
      {modalIncident && (
        <IncidentModal
          incident={modalIncident}
          teams={teams}
          onClose={() => setModalIncident(null)}
          onDispatched={() => {
            onRefresh();
          }}
        />
      )}
    </div>
  );
};
