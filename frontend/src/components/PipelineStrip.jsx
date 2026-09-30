import React from 'react';
import { Check, AlertTriangle, X, ChevronRight, Clock } from 'lucide-react';

export function PipelineStrip({ stages = {} }) {
  // stages format: { intent: "PASS"|"FAIL"|"NO_MATCH", paydna: "PASS"|"FAIL", behavior: "PASS"|"WARN"|"FAIL", decision: "ALLOW"|"VERIFY"|"HOLD" }

  const stageDefs = [
    { key: 'intent', label: '1. INTENT' },
    { key: 'paydna', label: '2. PAYDNA POLICY' },
    { key: 'behavior', label: '3. BEHAVIOR' },
    { key: 'decision', label: '4. DECISION' },
  ];

  return (
    <div className="w-full bg-console-surface border border-console-border rounded-sm p-3">
      <div className="text-[10px] font-mono uppercase tracking-widest text-console-muted mb-2 font-semibold">
        EVALUATION PIPELINE
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {stageDefs.map((def, idx) => {
          const state = (stages[def.key] || 'PENDING').toUpperCase();

          let badgeBg = 'bg-[#161F29] border-console-border text-console-muted';
          let icon = <Clock className="w-3.5 h-3.5" />;
          let stateLabel = state;

          if (state === 'PASS' || state === 'ALLOW') {
            badgeBg = 'bg-[#22C55E]/10 border-[#22C55E]/40 text-console-allow';
            icon = <Check className="w-3.5 h-3.5 stroke-[2.5]" />;
          } else if (state === 'WARN') {
            badgeBg = 'bg-[#F59E0B]/10 border-[#F59E0B]/40 text-console-verify';
            icon = <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5]" />;
          } else if (state === 'FAIL' || state === 'HOLD') {
            badgeBg = 'bg-[#EF4444]/10 border-[#EF4444]/40 text-console-hold';
            icon = <X className="w-3.5 h-3.5 stroke-[2.5]" />;
          } else if (state === 'VERIFY') {
            badgeBg = 'bg-[#F59E0B]/10 border-[#F59E0B]/40 text-console-verify';
            icon = <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5]" />;
          } else if (state === 'NO_MATCH') {
            badgeBg = 'bg-[#161F29] border-console-border text-console-muted';
            icon = <span className="text-[11px] font-mono">—</span>;
            stateLabel = 'NO MATCH';
          }

          return (
            <div
              key={def.key}
              className={`flex items-center justify-between p-2 rounded-sm border ${badgeBg} transition-colors`}
            >
              <div>
                <div className="text-[10px] font-sans font-medium text-console-muted tracking-wider">
                  {def.label}
                </div>
                <div className="text-xs font-mono font-bold mt-0.5 tracking-wide">
                  {stateLabel}
                </div>
              </div>
              <div>{icon}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
