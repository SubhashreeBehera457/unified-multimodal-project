import React, { useState } from 'react';
import { Incident, RescueTeam } from '../../types';
import { SourceBadge } from '../status/SourceBadge';
import { X, Send, ShieldAlert, MapPin, Users, Clock, AlertTriangle, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';

interface IncidentModalProps {
  incident: Incident | null;
  teams: RescueTeam[];
  onClose: () => void;
  onDispatched: () => void;
}

export const IncidentModal: React.FC<IncidentModalProps> = ({
  incident,
  teams,
  onClose,
  onDispatched,
}) => {
  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [dispatching, setDispatching] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ text: string; error?: boolean } | null>(null);

  if (!incident) return null;

  const availableTeams = teams.filter((t) => t.status === 'AVAILABLE');

  const handleDispatch = async () => {
    if (!selectedTeamId) return;
    setDispatching(true);
    setStatusMsg(null);
    try {
      await api.dispatchTeam(selectedTeamId, incident.incident_id);
      setStatusMsg({ text: 'Team dispatch orders broadcast successfully.' });
      onDispatched();
    } catch (err: any) {
      setStatusMsg({ text: err.message, error: true });
    } finally {
      setDispatching(false);
    }
  };

  const isCritical = incident.severity === 'CRITICAL';
  const isHigh = incident.severity === 'HIGH';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded bg-[#111827] border border-[#1F2937] shadow-2xl overflow-hidden font-mono">
        {/* Header */}
        <div className="p-4 border-b border-[#1F2937] flex items-center justify-between bg-[#0E131F]">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-bold ${
                isCritical
                  ? 'bg-rose-950 text-rose-400 border border-rose-800'
                  : isHigh
                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                  : 'bg-sky-950 text-sky-400 border border-sky-800'
              }`}
            >
              {incident.severity}
            </span>
            <span className="text-sm font-bold text-slate-100 uppercase">
              {incident.incident_id}
            </span>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-[#161E2E] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Disaster Type & Source */}
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 uppercase tracking-tight">
              {incident.disaster_type}
            </h3>
            <SourceBadge source={incident.source} />
          </div>

          {/* Location */}
          <div className="p-3 rounded bg-[#161E2E] border border-[#1F2937] text-xs">
            <div className="flex items-center gap-1.5 text-slate-300 font-semibold mb-1">
              <MapPin className="w-4 h-4 text-sky-400" />
              <span>{incident.location}</span>
            </div>
            <div className="text-[11px] text-slate-400">
              Coordinates: {incident.latitude?.toFixed(4)}°N, {incident.longitude?.toFixed(4)}°E
            </div>
          </div>

          {/* Key Incident Stats */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]">
              <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>POPULATION AT RISK</span>
              </div>
              <div className="text-base font-bold text-slate-100">
                {incident.people_at_risk?.toLocaleString() || 0}
              </div>
            </div>

            <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]">
              <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>ASSIGNED UNIT</span>
              </div>
              <div className="text-sm font-bold text-sky-300 truncate">
                {incident.assigned_team || 'Unassigned'}
              </div>
            </div>
          </div>

          {/* Description */}
          {incident.description && (
            <div className="p-3 rounded bg-[#0B0F17] border border-[#1F2937] text-xs text-slate-300 leading-relaxed">
              <span className="text-[10px] text-slate-500 block mb-1 uppercase font-bold tracking-wider">
                SITUATION REPORT
              </span>
              {incident.description}
            </div>
          )}

          {/* External GDACS link if available */}
          {incident.gdacs_url && (
            <div className="text-right">
              <a
                href={incident.gdacs_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[11px] text-sky-400 hover:underline"
              >
                <span>View Official GDACS Bulletin</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}

          {/* Dispatch Section */}
          <div className="p-4 rounded bg-[#0E131F] border border-[#1F2937] space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Send className="w-4 h-4 text-sky-400" />
              <span>DISPATCH EMERGENCY RESCUE UNIT</span>
            </div>

            {availableTeams.length === 0 ? (
              <p className="text-xs text-amber-400/80">
                All units are currently deployed or unavailable.
              </p>
            ) : (
              <div className="flex gap-2">
                <select
                  value={selectedTeamId}
                  onChange={(e) => setSelectedTeamId(e.target.value)}
                  className="flex-1 px-3 py-2 rounded bg-[#161E2E] border border-[#1F2937] text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="">Select Response Team...</option>
                  {availableTeams.map((team) => (
                    <option key={team.team_id} value={team.team_id}>
                      {team.name} (Cap: {team.capacity})
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleDispatch}
                  disabled={!selectedTeamId || dispatching}
                  className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                >
                  {dispatching ? 'ORDERING...' : 'DISPATCH'}
                </button>
              </div>
            )}

            {statusMsg && (
              <div
                className={`p-2 rounded text-xs ${
                  statusMsg.error
                    ? 'bg-rose-950/40 text-rose-400 border border-rose-800'
                    : 'bg-emerald-950/40 text-emerald-400 border border-emerald-800'
                }`}
              >
                {statusMsg.text}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
