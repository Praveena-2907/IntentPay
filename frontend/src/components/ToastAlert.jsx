import React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, X } from 'lucide-react';

export function ToastAlert({ type = 'info', title, message, onDismiss, actionButton }) {
  let border = 'border-console-border';
  let bg = 'bg-console-surface-2';
  let icon = <Info className="w-4 h-4 text-console-accent" />;

  if (type === 'error' || type === 'violation' || type === 'hold') {
    border = 'border-console-hold/40';
    bg = 'bg-console-hold/10';
    icon = <AlertCircle className="w-4 h-4 text-console-hold" />;
  } else if (type === 'warning' || type === 'conflict' || type === 'anomaly') {
    border = 'border-console-verify/40';
    bg = 'bg-console-verify/10';
    icon = <AlertTriangle className="w-4 h-4 text-console-verify" />;
  } else if (type === 'success') {
    border = 'border-console-allow/40';
    bg = 'bg-console-allow/10';
    icon = <CheckCircle2 className="w-4 h-4 text-console-allow" />;
  }

  return (
    <div className={`flex items-start justify-between gap-3 p-3 rounded-sm border ${border} ${bg} transition-all`}>
      <div className="flex items-start gap-2.5 min-w-0">
        <div className="mt-0.5 shrink-0">{icon}</div>
        <div className="min-w-0">
          {title && (
            <div className="text-xs font-mono font-bold text-console-text uppercase tracking-wide">
              {title}
            </div>
          )}
          <div className="text-xs text-console-text/90 mt-0.5 leading-relaxed font-sans">
            {message}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {actionButton}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-console-muted hover:text-console-text p-1 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
