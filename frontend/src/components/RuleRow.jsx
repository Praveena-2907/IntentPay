import React from 'react';
import { Check, AlertTriangle, X } from 'lucide-react';

export function RuleRow({ id, label, result, detail }) {
  const norm = (result || '').toUpperCase();

  let icon = <Check className="w-3.5 h-3.5 text-console-allow stroke-[2.5]" />;
  let badgeStyle = 'text-console-allow bg-console-allow/10 border-console-allow/30';

  if (norm === 'FAIL' || norm === 'HOLD') {
    icon = <X className="w-3.5 h-3.5 text-console-hold stroke-[2.5]" />;
    badgeStyle = 'text-console-hold bg-console-hold/10 border-console-hold/30';
  } else if (norm === 'WARN' || norm === 'VERIFY') {
    icon = <AlertTriangle className="w-3.5 h-3.5 text-console-verify stroke-[2.5]" />;
    badgeStyle = 'text-console-verify bg-console-verify/10 border-console-verify/30';
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 bg-console-surface-2 border border-console-border rounded-sm hover:border-console-border/80 transition-colors">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="shrink-0">{icon}</div>
        <div className="min-w-0">
          <div className="font-mono text-xs font-semibold text-console-text truncate">
            {id && <span className="text-console-muted mr-1.5">{id} ·</span>}
            {label}
          </div>
          {detail && (
            <div className="text-[11px] font-sans text-console-muted mt-0.5 truncate">
              {detail}
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0 self-start sm:self-center">
        <span className={`px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded-sm border ${badgeStyle}`}>
          {norm}
        </span>
      </div>
    </div>
  );
}
