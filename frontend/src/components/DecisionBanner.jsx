import React from 'react';
import { formatINR } from '../utils/format';
import { CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

export function DecisionBanner({ decision, amount, recipient, category, reasons = [], explanation }) {
  const norm = (decision || '').toUpperCase();

  let borderStyle = 'border-l-[3px] border-l-console-muted';
  let badgeStyle = 'bg-[#161F29] text-console-muted border-console-border';
  let icon = null;

  if (norm === 'ALLOW') {
    borderStyle = 'border-l-[3px] border-l-console-allow';
    badgeStyle = 'bg-[#22C55E]/15 text-console-allow border-[#22C55E]/40';
    icon = <CheckCircle2 className="w-5 h-5 text-console-allow" />;
  } else if (norm === 'VERIFY') {
    borderStyle = 'border-l-[3px] border-l-console-verify';
    badgeStyle = 'bg-[#F59E0B]/15 text-console-verify border-[#F59E0B]/40';
    icon = <AlertTriangle className="w-5 h-5 text-console-verify" />;
  } else if (norm === 'HOLD') {
    borderStyle = 'border-l-[3px] border-l-console-hold';
    badgeStyle = 'bg-[#EF4444]/15 text-console-hold border-[#EF4444]/40';
    icon = <ShieldAlert className="w-5 h-5 text-console-hold" />;
  }

  return (
    <div className={`w-full bg-console-surface border border-console-border ${borderStyle} p-4 rounded-sm`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-console-border/60">
        <div className="flex items-center gap-3">
          {icon}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-console-muted">
              DECISION OUTCOME
            </div>
            <div className="text-lg font-mono font-bold text-console-text">
              {norm}
            </div>
          </div>
        </div>

        {amount !== undefined && recipient && (
          <div className="text-right">
            <div className="text-[10px] font-mono uppercase tracking-widest text-console-muted">
              TRANSACTION TARGET
            </div>
            <div className="font-mono text-sm font-semibold text-console-text">
              <span className="text-console-accent">{formatINR(amount)}</span>
              <span className="text-console-muted mx-1.5">→</span>
              <span className="text-console-text">{recipient}</span>
              {category && <span className="text-xs text-console-muted ml-2">[{category}]</span>}
            </div>
          </div>
        )}
      </div>

      {explanation && (
        <div className="mt-3 text-sm text-console-text leading-relaxed font-sans">
          {explanation}
        </div>
      )}

      {reasons && reasons.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-console-border/40">
          <div className="text-[10px] font-mono uppercase tracking-wider text-console-muted mb-1.5">
            EVALUATION FACTORS & TRIGGERS ({reasons.length})
          </div>
          <ul className="space-y-1">
            {reasons.map((reason, idx) => (
              <li key={idx} className="text-xs text-console-muted flex items-start gap-2">
                <span className="font-mono text-console-border select-none mt-0.5">•</span>
                <span className="font-mono text-console-text/90">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
