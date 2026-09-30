import React from 'react';

export function KpiTile({ label, value, delta, status = 'default' }) {
  let valueColor = 'text-console-text';
  if (status === 'allow') valueColor = 'text-console-allow';
  if (status === 'verify') valueColor = 'text-console-verify';
  if (status === 'hold') valueColor = 'text-console-hold';
  if (status === 'accent') valueColor = 'text-console-accent';

  return (
    <div className="bg-console-surface border border-console-border p-4 rounded-sm hover:border-console-border/80 transition-colors">
      <div className="text-[11px] font-sans uppercase tracking-wider text-console-muted font-semibold">
        {label}
      </div>
      <div className={`text-2xl font-mono font-bold mt-1.5 tabular-nums ${valueColor}`}>
        {value}
      </div>
      {delta && (
        <div className="text-[11px] font-mono text-console-muted/80 mt-1 truncate">
          {delta}
        </div>
      )}
    </div>
  );
}
