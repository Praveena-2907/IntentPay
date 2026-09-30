import React from 'react';
import { Check, AlertTriangle, Square, Clock, X } from 'lucide-react';

export function StatusChip({ status, size = 'sm' }) {
  const norm = (status || '').toUpperCase();

  let label = norm;
  let icon = null;
  let styleClass = 'bg-[#161F29] text-console-muted border-console-border';

  if (norm === 'ALLOW' || norm === 'EXECUTED_SIMULATED') {
    label = norm === 'EXECUTED_SIMULATED' ? 'EXECUTED (SIMULATED)' : 'ALLOW';
    icon = <Check className="w-3.5 h-3.5 stroke-[2.5]" />;
    styleClass = 'bg-[#22C55E]/10 text-console-allow border-[#22C55E]/30';
  } else if (norm === 'VERIFY' || norm === 'PENDING_VERIFICATION') {
    label = norm === 'PENDING_VERIFICATION' ? 'PENDING VERIFICATION' : 'VERIFY';
    icon = <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5]" />;
    styleClass = 'bg-[#F59E0B]/10 text-console-verify border-[#F59E0B]/30';
  } else if (norm === 'HOLD' || norm === 'HELD') {
    label = norm === 'HELD' ? 'HELD (BLOCKED)' : 'HOLD';
    icon = <Square className="w-3 h-3 fill-current" />;
    styleClass = 'bg-[#EF4444]/10 text-console-hold border-[#EF4444]/30';
  } else if (norm === 'REJECTED') {
    label = 'REJECTED';
    icon = <X className="w-3.5 h-3.5 stroke-[2.5]" />;
    styleClass = 'bg-[#EF4444]/10 text-console-hold border-[#EF4444]/30';
  } else if (norm === 'ACTIVE') {
    label = 'ACTIVE';
    icon = <span className="w-1.5 h-1.5 rounded-full bg-console-allow inline-block" />;
    styleClass = 'bg-[#22C55E]/10 text-console-allow border-[#22C55E]/30';
  } else if (norm === 'PAUSED') {
    label = 'PAUSED';
    icon = <Clock className="w-3 h-3" />;
    styleClass = 'bg-[#F59E0B]/10 text-console-verify border-[#F59E0B]/30';
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-medium rounded-sm border ${padding} ${styleClass} tracking-wide select-none`}>
      {icon}
      <span>{label}</span>
    </span>
  );
}
