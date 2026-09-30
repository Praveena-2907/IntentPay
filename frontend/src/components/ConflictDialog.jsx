import React from 'react';
import { formatINR } from '../utils/format';
import { AlertTriangle, ShieldAlert, ArrowRight, X } from 'lucide-react';

export function ConflictDialog({ conflict, onKeepPolicy, onUpdateIntent, onCancel }) {
  if (!conflict) return null;

  const { intent, policy, reason } = conflict;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="bg-console-surface border border-console-verify/60 rounded-sm w-full max-w-2xl shadow-2xl p-5 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-console-border">
          <div className="flex items-center gap-2 text-console-verify">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-console-muted">
                POLICY CONFLICT DETECTED
              </span>
              <h2 className="text-sm font-mono font-bold text-console-text">
                Autonomous Rule Contradiction
              </h2>
            </div>
          </div>
          <button onClick={onCancel} className="text-console-muted hover:text-console-text p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Reason summary */}
        <div className="p-3 bg-console-verify/10 border border-console-verify/30 rounded-sm text-xs font-mono text-console-text leading-relaxed">
          {reason}
        </div>

        {/* Side by side comparison */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          {/* Intent Card */}
          <div className="bg-console-surface-2 p-3.5 border border-console-border rounded-sm space-y-1.5">
            <div className="text-[10px] uppercase text-console-accent font-semibold flex items-center gap-1">
              <span>AUTO-PAY INTENT</span>
            </div>
            <div className="font-bold text-console-text">{intent?.purpose}</div>
            <div className="text-console-muted">
              Target: <span className="text-console-text">{intent?.recipient || 'Any'} [{intent?.category}]</span>
            </div>
            <div className="text-console-muted">
              Auto-pay: <span className="text-console-accent font-bold">{formatINR(intent?.amount || 0)}</span>
            </div>
          </div>

          {/* Policy Card */}
          <div className="bg-console-surface-2 p-3.5 border border-console-border rounded-sm space-y-1.5">
            <div className="text-[10px] uppercase text-console-verify font-semibold flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>SECURITY POLICY ({policy?.id})</span>
            </div>
            <div className="font-bold text-console-text">{policy?.description}</div>
            <div className="text-console-muted">
              Type: <span className="text-console-text">{policy?.policy_type}</span>
            </div>
            <div className="text-console-muted">
              Threshold: <span className="text-console-verify font-bold">{formatINR(policy?.threshold || 0)}</span> ({policy?.action})
            </div>
          </div>
        </div>

        {/* 3 Resolution Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-2 pt-3 border-t border-console-border">
          <button
            onClick={onCancel}
            className="w-full sm:w-auto px-3 py-1.5 text-xs font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm transition-colors"
          >
            CANCEL
          </button>
          <button
            onClick={onUpdateIntent}
            className="w-full sm:w-auto px-3.5 py-1.5 text-xs font-mono font-bold bg-console-surface-2 hover:bg-console-surface text-console-accent border border-console-accent/40 rounded-sm transition-colors"
          >
            UPDATE INTENT
          </button>
          <button
            onClick={onKeepPolicy}
            className="w-full sm:w-auto px-4 py-1.5 text-xs font-mono font-bold bg-console-verify hover:bg-amber-600 text-black rounded-sm transition-colors"
          >
            KEEP SECURITY POLICY
          </button>
        </div>
      </div>
    </div>
  );
}
