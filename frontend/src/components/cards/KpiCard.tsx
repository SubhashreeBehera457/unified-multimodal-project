import React from 'react';

interface KpiCardProps {
  label: string;
  value: number | string;
  subtext?: string;
  accent?: 'critical' | 'warning' | 'safe' | 'accent' | 'default';
  icon?: React.ComponentType<{ className?: string }>;
  tag?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  subtext,
  accent = 'default',
  icon: Icon,
  tag,
}) => {
  let borderColor = 'border-[#1F2937]';
  let valueColor = 'text-slate-100';
  let iconBg = 'bg-slate-800/40 text-slate-400';

  if (accent === 'critical') {
    borderColor = 'border-rose-500/30 hover:border-rose-500/50';
    valueColor = 'text-rose-400';
    iconBg = 'bg-rose-950/40 text-rose-400 border border-rose-500/30';
  } else if (accent === 'warning') {
    borderColor = 'border-amber-500/30 hover:border-amber-500/50';
    valueColor = 'text-amber-400';
    iconBg = 'bg-amber-950/40 text-amber-400 border border-amber-500/30';
  } else if (accent === 'safe') {
    borderColor = 'border-emerald-500/30 hover:border-emerald-500/50';
    valueColor = 'text-emerald-400';
    iconBg = 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30';
  } else if (accent === 'accent') {
    borderColor = 'border-sky-500/30 hover:border-sky-500/50';
    valueColor = 'text-sky-300';
    iconBg = 'bg-sky-950/40 text-sky-400 border border-sky-500/30';
  }

  return (
    <div className={`p-3.5 rounded bg-[#111827] border ${borderColor} transition-colors flex flex-col justify-between`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-mono font-medium tracking-wider text-slate-400 uppercase truncate">
          {label}
        </span>
        {Icon && (
          <div className={`p-1.5 rounded ${iconBg}`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className={`text-2xl font-bold font-mono tracking-tight ${valueColor}`}>
          {value !== undefined && value !== null ? value : '--'}
        </div>
        {tag && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#161E2E] text-slate-400 border border-[#1F2937]">
            {tag}
          </span>
        )}
      </div>

      {subtext && (
        <div className="mt-1 text-[11px] font-mono text-slate-500 truncate">
          {subtext}
        </div>
      )}
    </div>
  );
};
