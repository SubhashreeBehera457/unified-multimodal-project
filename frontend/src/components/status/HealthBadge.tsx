import React from 'react';

interface HealthBadgeProps {
  status: 'ONLINE' | 'DEGRADED' | 'NOT CONFIGURED' | 'UNAVAILABLE' | string;
  label?: string;
  showDot?: boolean;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({ status, label, showDot = true }) => {
  const s = (status || '').toUpperCase();

  let colorClasses = 'border-slate-700 bg-slate-800/60 text-slate-400';
  let dotColor = 'bg-slate-500';

  if (s.startsWith('ONLINE') || s === 'OPERATIONAL') {
    colorClasses = 'border-emerald-500/20 bg-emerald-950/30 text-emerald-400';
    dotColor = 'bg-emerald-400';
  } else if (s === 'DEGRADED') {
    colorClasses = 'border-amber-500/20 bg-amber-950/30 text-amber-300';
    dotColor = 'bg-amber-400';
  } else if (s === 'NOT CONFIGURED') {
    colorClasses = 'border-slate-800 bg-slate-900/40 text-slate-500';
    dotColor = 'bg-slate-600';
  } else if (s === 'UNAVAILABLE' || s === 'OFFLINE') {
    colorClasses = 'border-rose-500/20 bg-rose-950/30 text-rose-400';
    dotColor = 'bg-rose-500';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono rounded border ${colorClasses}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />}
      {label || s}
    </span>
  );
};
