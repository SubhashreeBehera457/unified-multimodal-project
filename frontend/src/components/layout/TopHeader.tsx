import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, Radio, ShieldAlert } from 'lucide-react';
import { ConnectionState } from '../../hooks/useLiveData';

interface TopHeaderProps {
  lastSync: string;
  connectionStatus: ConnectionState;
  systemStatus: string;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  lastSync,
  connectionStatus,
  systemStatus,
  onRefresh,
  isRefreshing = false,
}) => {
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toTimeString().split(' ')[0]);
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  const isLive = connectionStatus === 'LIVE CONNECTION';
  const isReconnecting = connectionStatus === 'RECONNECTING';

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between px-6 py-3 bg-[#0B0F17]/95 backdrop-blur border-b border-[#1F2937]">
      {/* Title & Platform Tagline */}
      <div className="flex items-center gap-4">
        <div className="flex items-center justify-center w-8 h-8 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold tracking-wider text-slate-100 uppercase">
              Disaster Response Intelligence
            </h1>
            <span className="px-1.5 py-0.2 text-[10px] font-mono tracking-widest text-sky-400 bg-sky-950/60 border border-sky-800/60 rounded">
              OPS-CENTRAL
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            REAL-TIME EMERGENCY OPERATIONS PLATFORM
          </p>
        </div>
      </div>

      {/* Real-time Telemetry Indicators */}
      <div className="flex items-center gap-6">
        {/* System Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded bg-[#111827] border border-[#1F2937] text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-400">STATUS:</span>
          <span className="font-semibold text-emerald-400 uppercase">{systemStatus || 'OPERATIONAL'}</span>
        </div>

        {/* Live Clock */}
        <div className="flex flex-col text-right font-mono">
          <span className="text-[11px] text-slate-400 leading-none">LOCAL TIME</span>
          <span className="text-sm font-semibold text-slate-200">{currentTime || '--:--:--'}</span>
        </div>

        {/* Last Sync */}
        <div className="flex flex-col text-right font-mono">
          <span className="text-[11px] text-slate-400 leading-none">LAST SYNC</span>
          <span className="text-sm font-medium text-slate-300">{lastSync || '--:--:--'}</span>
        </div>

        {/* Connection Indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded font-mono text-xs border ${
              isLive
                ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400'
                : isReconnecting
                ? 'bg-amber-950/30 border-amber-500/30 text-amber-300 animate-pulse'
                : 'bg-rose-950/30 border-rose-500/30 text-rose-400'
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${isLive ? 'animate-pulse' : ''}`} />
            <span className="font-semibold tracking-wide">{connectionStatus}</span>
          </div>

          {/* Refresh Action */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh operations telemetry"
            className="p-1.5 rounded bg-[#111827] border border-[#1F2937] hover:border-sky-500/40 text-slate-300 hover:text-sky-400 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
