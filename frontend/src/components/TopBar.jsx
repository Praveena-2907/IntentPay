import React from 'react';
import { formatINR } from '../utils/format';
import { ShieldCheck, Cpu, RefreshCw, AlertCircle } from 'lucide-react';

export function TopBar({ user, isFallback, onResetData, isResetting }) {
  const available = user ? (user.current_balance - user.upcoming_expenses) : 20500;

  return (
    <header className="h-14 bg-console-surface border-b border-console-border px-4 flex items-center justify-between z-20 sticky top-0">
      {/* Brand & Simulation Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-console-accent animate-pulse" />
          <span className="font-mono text-sm font-bold tracking-wider text-console-text">
            INTENT<span className="text-console-accent">PAY</span>
          </span>
        </div>

        <span className="hidden sm:inline-flex items-center px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded-sm bg-[#EF4444]/15 text-console-hold border border-[#EF4444]/30">
          SIMULATED — NO REAL FUNDS
        </span>
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-sm bg-console-surface-2 border border-console-border text-[11px] font-mono text-console-muted">
          <Cpu className="w-3.5 h-3.5 text-console-allow" />
          <span>ENGINE:</span>
          <span className="text-console-allow font-semibold">ONLINE</span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-1 rounded-sm bg-console-surface-2 border border-console-border text-[11px] font-mono">
          <span className="text-console-muted">PARSER:</span>
          {isFallback ? (
            <span className="text-console-verify font-semibold" title="AI Unavailable — Secure Fallback Active">
              FALLBACK
            </span>
          ) : (
            <span className="text-console-accent font-semibold">
              GEMINI AI
            </span>
          )}
        </div>

        {/* Demo User Info */}
        <div className="hidden lg:flex items-center gap-3 border-l border-console-border pl-3 text-xs font-mono">
          <div>
            <span className="text-console-muted mr-1">USER:</span>
            <span className="text-console-text font-semibold">{user?.name || 'Demo User'}</span>
          </div>
          <div>
            <span className="text-console-muted mr-1">AVAILABLE:</span>
            <span className="text-console-allow font-bold">{formatINR(available)}</span>
          </div>
        </div>

        {/* Reset Demo Data button */}
        <button
          onClick={onResetData}
          disabled={isResetting}
          title="Reset database to seed state"
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border hover:border-console-border/80 rounded-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isResetting ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">RESET SEED</span>
        </button>
      </div>
    </header>
  );
}
