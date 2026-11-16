import React from 'react';

interface SourceBadgeProps {
  source: string;
  className?: string;
  short?: boolean;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, className = '', short = false }) => {
  const s = (source || '').toUpperCase();

  if (s === 'LIVE' || s.includes('LIVE') || s === 'GDACS' || s.includes('OPEN-METEO') || s.includes('GDELT')) {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono font-medium rounded border border-emerald-500/30 bg-emerald-950/40 text-emerald-400 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        {short ? 'LIVE' : `[ LIVE ] ${source}`}
      </span>
    );
  }

  if (s.includes('MODEL') || s.includes('XGBOOST') || s.includes('DISTILBERT') || s.includes('RESNET') || s.includes('SHAP')) {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono font-medium rounded border border-sky-500/30 bg-sky-950/40 text-sky-300 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
        {short ? 'MODEL' : `[ MODEL GENERATED ] ${source.replace('MODEL GENERATED', '').trim() || source}`}
      </span>
    );
  }

  if (s.includes('SIMULATION') || s.includes('DEMO')) {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono font-medium rounded border border-amber-500/30 bg-amber-950/40 text-amber-300 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        {short ? 'SIM' : `[ SIMULATION ] ${source.replace('SIMULATION', '').trim() || 'Demo'}`}
      </span>
    );
  }

  if (s.includes('NOT CONFIGURED') || s.includes('UNAVAILABLE') || s.includes('ERROR')) {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono font-medium rounded border border-slate-700 bg-slate-900/60 text-slate-400 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
        {short ? 'UNAVAIL' : `[ UNAVAILABLE ] ${source}`}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-mono rounded border border-slate-700 bg-slate-800 text-slate-300 ${className}`}>
      {source}
    </span>
  );
};
