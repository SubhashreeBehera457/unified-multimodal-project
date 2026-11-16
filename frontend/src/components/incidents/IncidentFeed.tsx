import React, { useState, useMemo } from 'react';
import { Incident } from '../../types';
import { SourceBadge } from '../status/SourceBadge';
import { Users, MapPin, ChevronRight, AlertOctagon, Flame, Waves, Zap, Wind, Search, SunMedium } from 'lucide-react';

interface IncidentFeedProps {
  incidents: Incident[];
  onSelectIncident: (inc: Incident) => void;
  selectedId?: string;
  loading?: boolean;
}

export const IncidentFeed: React.FC<IncidentFeedProps> = ({
  incidents,
  onSelectIncident,
  selectedId,
  loading = false,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Calculate disaster counts for quick filters
  const counts = useMemo(() => {
    let wildfire = 0;
    let flood = 0;
    let earthquake = 0;
    let cyclone = 0;
    let drought = 0;

    incidents.forEach((inc) => {
      const t = (inc.disaster_type || '').toUpperCase();
      if (t.includes('FIRE') || t.includes('WILDFIRE')) wildfire++;
      else if (t.includes('FLOOD')) flood++;
      else if (t.includes('EARTHQUAKE')) earthquake++;
      else if (t.includes('CYCLONE') || t.includes('STORM') || t.includes('TYPHOON')) cyclone++;
      else if (t.includes('DROUGHT')) drought++;
    });

    return { wildfire, flood, earthquake, cyclone, drought };
  }, [incidents]);

  const filtered = useMemo(() => {
    return incidents.filter((inc) => {
      // 1. Severity filter
      if (severityFilter !== 'ALL' && inc.severity !== severityFilter) return false;

      // 2. Disaster Type filter
      if (typeFilter !== 'ALL') {
        const t = (inc.disaster_type || '').toUpperCase();
        if (typeFilter === 'WILDFIRE' && !t.includes('FIRE') && !t.includes('WILDFIRE')) return false;
        if (typeFilter === 'FLOOD' && !t.includes('FLOOD')) return false;
        if (typeFilter === 'EARTHQUAKE' && !t.includes('EARTHQUAKE')) return false;
        if (typeFilter === 'CYCLONE' && !t.includes('CYCLONE') && !t.includes('STORM') && !t.includes('TYPHOON')) return false;
        if (typeFilter === 'DROUGHT' && !t.includes('DROUGHT')) return false;
      }

      // 3. Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesLocation = (inc.location || '').toLowerCase().includes(q);
        const matchesType = (inc.disaster_type || '').toLowerCase().includes(q);
        const matchesId = (inc.incident_id || '').toLowerCase().includes(q);
        const matchesDesc = (inc.description || '').toLowerCase().includes(q);
        if (!matchesLocation && !matchesType && !matchesId && !matchesDesc) return false;
      }

      return true;
    });
  }, [incidents, severityFilter, typeFilter, searchQuery]);

  const getDisasterBadge = (type: string) => {
    const t = (type || '').toUpperCase();
    if (t.includes('FIRE') || t.includes('WILDFIRE')) {
      return {
        icon: <Flame className="w-3 h-3 text-orange-400" />,
        text: 'WILDFIRE',
        badgeClass: 'bg-orange-950/80 text-orange-300 border-orange-800/80',
      };
    }
    if (t.includes('FLOOD')) {
      return {
        icon: <Waves className="w-3 h-3 text-cyan-400" />,
        text: 'FLOOD',
        badgeClass: 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80',
      };
    }
    if (t.includes('EARTHQUAKE')) {
      return {
        icon: <Zap className="w-3 h-3 text-amber-400" />,
        text: 'EARTHQUAKE',
        badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-800/80',
      };
    }
    if (t.includes('CYCLONE') || t.includes('STORM') || t.includes('TYPHOON')) {
      return {
        icon: <Wind className="w-3 h-3 text-purple-400" />,
        text: 'CYCLONE',
        badgeClass: 'bg-purple-950/80 text-purple-300 border-purple-800/80',
      };
    }
    if (t.includes('DROUGHT')) {
      return {
        icon: <SunMedium className="w-3 h-3 text-yellow-400" />,
        text: 'DROUGHT',
        badgeClass: 'bg-yellow-950/80 text-yellow-300 border-yellow-800/80',
      };
    }
    return {
      icon: <AlertOctagon className="w-3 h-3 text-sky-400" />,
      text: type,
      badgeClass: 'bg-sky-950/80 text-sky-300 border-sky-800/80',
    };
  };

  return (
    <div className="flex flex-col h-full rounded bg-[#111827] border border-[#1F2937] overflow-hidden">
      {/* Feed Header */}
      <div className="p-3 border-b border-[#1F2937] bg-[#0E131F]/90 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase">
              Live Incident Stream
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 font-bold">
              {filtered.length} / {incidents.length}
            </span>
          </div>

          {/* Severity quick filters */}
          <div className="flex items-center gap-1">
            {['ALL', 'CRITICAL', 'HIGH'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${
                  severityFilter === sev
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 font-bold'
                    : 'bg-[#161E2E] text-slate-400 border-[#1F2937] hover:border-slate-600'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Disaster Type Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 custom-scrollbar text-[10px] font-mono">
          <button
            onClick={() => setTypeFilter('ALL')}
            className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors border ${
              typeFilter === 'ALL'
                ? 'bg-slate-700 text-white border-slate-500 font-bold'
                : 'bg-[#161E2E] text-slate-400 border-[#1F2937] hover:text-slate-200'
            }`}
          >
            ALL ({incidents.length})
          </button>
          {counts.wildfire > 0 && (
            <button
              onClick={() => setTypeFilter('WILDFIRE')}
              className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors flex items-center gap-1 border ${
                typeFilter === 'WILDFIRE'
                  ? 'bg-orange-600/30 text-orange-200 border-orange-500 font-bold'
                  : 'bg-[#161E2E] text-orange-400/80 border-[#1F2937] hover:text-orange-300'
              }`}
            >
              <span>🔥 WILDFIRE</span>
              <span className="px-1 rounded bg-orange-950 text-orange-400 text-[9px]">{counts.wildfire}</span>
            </button>
          )}
          {counts.flood > 0 && (
            <button
              onClick={() => setTypeFilter('FLOOD')}
              className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors flex items-center gap-1 border ${
                typeFilter === 'FLOOD'
                  ? 'bg-cyan-600/30 text-cyan-200 border-cyan-500 font-bold'
                  : 'bg-[#161E2E] text-cyan-400/80 border-[#1F2937] hover:text-cyan-300'
              }`}
            >
              <span>🌊 FLOOD</span>
              <span className="px-1 rounded bg-cyan-950 text-cyan-400 text-[9px]">{counts.flood}</span>
            </button>
          )}
          {counts.earthquake > 0 && (
            <button
              onClick={() => setTypeFilter('EARTHQUAKE')}
              className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors flex items-center gap-1 border ${
                typeFilter === 'EARTHQUAKE'
                  ? 'bg-amber-600/30 text-amber-200 border-amber-500 font-bold'
                  : 'bg-[#161E2E] text-amber-400/80 border-[#1F2937] hover:text-amber-300'
              }`}
            >
              <span>⚡ EARTHQUAKE</span>
              <span className="px-1 rounded bg-amber-950 text-amber-400 text-[9px]">{counts.earthquake}</span>
            </button>
          )}
          {counts.cyclone > 0 && (
            <button
              onClick={() => setTypeFilter('CYCLONE')}
              className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors flex items-center gap-1 border ${
                typeFilter === 'CYCLONE'
                  ? 'bg-purple-600/30 text-purple-200 border-purple-500 font-bold'
                  : 'bg-[#161E2E] text-purple-400/80 border-[#1F2937] hover:text-purple-300'
              }`}
            >
              <span>🌀 CYCLONE</span>
              <span className="px-1 rounded bg-purple-950 text-purple-400 text-[9px]">{counts.cyclone}</span>
            </button>
          )}
          {counts.drought > 0 && (
            <button
              onClick={() => setTypeFilter('DROUGHT')}
              className={`px-2 py-0.5 rounded whitespace-nowrap transition-colors flex items-center gap-1 border ${
                typeFilter === 'DROUGHT'
                  ? 'bg-yellow-600/30 text-yellow-200 border-yellow-500 font-bold'
                  : 'bg-[#161E2E] text-yellow-400/80 border-[#1F2937] hover:text-yellow-300'
              }`}
            >
              <span>🏜️ DROUGHT</span>
              <span className="px-1 rounded bg-yellow-950 text-yellow-400 text-[9px]">{counts.drought}</span>
            </button>
          )}
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by country, city, disaster type..."
            className="w-full pl-8 pr-3 py-1 rounded bg-[#0B0F17] border border-[#1F2937] text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>
      </div>

      {/* Incident List */}
      <div className="flex-1 overflow-y-auto divide-y divide-[#1F2937]/60 custom-scrollbar">
        {loading && incidents.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-slate-500">
            LOADING INCIDENT TELEMETRY...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-slate-500">
            NO INCIDENTS MATCHING CRITERIA
          </div>
        ) : (
          filtered.map((inc) => {
            const isSelected = selectedId === inc.incident_id;
            const isCritical = inc.severity === 'CRITICAL';
            const isHigh = inc.severity === 'HIGH';
            const badge = getDisasterBadge(inc.disaster_type);

            return (
              <div
                key={inc.incident_id}
                onClick={() => onSelectIncident(inc)}
                className={`p-3 cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-sky-500/10 border-l-2 border-sky-400'
                    : 'hover:bg-[#161E2E]/80 border-l-2 border-transparent'
                }`}
              >
                {/* Row 1: Badges & Time */}
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {/* Disaster Type Badge */}
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold flex items-center gap-1 border ${badge.badgeClass}`}
                    >
                      {badge.icon}
                      <span>{badge.text}</span>
                    </span>

                    {/* Severity Badge */}
                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold tracking-wider ${
                        isCritical
                          ? 'bg-rose-950/80 text-rose-400 border border-rose-800'
                          : isHigh
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {inc.severity}
                    </span>

                    {/* Source Badge */}
                    <SourceBadge source={inc.source} short={true} />
                  </div>

                  <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">
                    {inc.created_at || 'LIVE'}
                  </span>
                </div>

                {/* Row 2: Location & Arrow */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1 text-xs font-mono font-bold text-slate-100">
                    <MapPin className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                    <span className="truncate">{inc.location}</span>
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 text-slate-500 ${isSelected ? 'text-sky-400 translate-x-0.5' : ''}`} />
                </div>

                {/* Row 3: Description snippet if available */}
                {inc.description && (
                  <p className="text-[11px] font-mono text-slate-400 mt-1 line-clamp-1">
                    {inc.description}
                  </p>
                )}

                {/* Row 4: People at risk & Assigned team */}
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mt-2 pt-1 border-t border-[#1F2937]/40">
                  <div className="flex items-center gap-1">
                    <Users className="w-3 h-3 text-slate-500" />
                    <span>{inc.people_at_risk?.toLocaleString() || 0} at risk</span>
                  </div>
                  <span className="truncate max-w-[130px]">
                    {inc.assigned_team || 'Unassigned'}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
