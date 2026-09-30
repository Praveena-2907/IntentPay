import React from 'react';
import { formatINR } from '../utils/format';
import { ShieldCheck, Sparkles, AlertTriangle, Check, X } from 'lucide-react';

export function ParseReview({ draft, type = 'intent', source, warnings = [], onConfirm, onDiscard, isSubmitting }) {
  if (!draft) return null;

  const isFallback = source === 'fallback';

  return (
    <div className="bg-console-surface border border-console-border rounded-sm p-4 space-y-4">
      {/* Header with Source Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-console-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-console-muted font-semibold">
            {type === 'intent' ? 'STRUCTURED INTENT DRAFT' : 'STRUCTURED POLICY DRAFT'}
          </span>
          <div className="text-sm font-mono font-bold text-console-text mt-0.5">
            {draft.purpose || draft.description}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isFallback ? (
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-sm bg-console-verify/15 text-console-verify border border-console-verify/30 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>AI UNAVAILABLE — USING SECURE FALLBACK PARSER</span>
            </span>
          ) : (
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-sm bg-console-accent/15 text-console-accent border border-console-accent/30 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>PARSED BY GEMINI AI</span>
            </span>
          )}
        </div>
      </div>

      {/* Warnings Banner if any */}
      {warnings && warnings.length > 0 && (
        <div className="p-2.5 bg-console-verify/10 border border-console-verify/30 rounded-sm text-xs font-mono text-console-verify flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>{warnings.join("; ")}</div>
        </div>
      )}

      {/* Field Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-console-surface-2 p-3 rounded-sm border border-console-border text-xs font-mono">
        {type === 'intent' ? (
          <>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Recipient</span>
              <div className="text-console-text font-semibold">{draft.recipient || 'Any (Category-wide)'}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Category</span>
              <div className="text-console-text font-semibold">{draft.category}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Amount / Ceiling</span>
              <div className="text-console-accent font-bold">
                {draft.amount ? formatINR(draft.amount) : (draft.max_amount ? `Max ${formatINR(draft.max_amount)}` : 'Dynamic')}
              </div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Action</span>
              <div className="text-console-allow font-bold">{draft.action}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Frequency</span>
              <div className="text-console-text">{draft.frequency}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Day of Month</span>
              <div className="text-console-text">{draft.day_of_month ? `Day ${draft.day_of_month}` : 'Any day'}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Trigger</span>
              <div className="text-console-text">{draft.trigger}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Conditions</span>
              <div className="text-console-text">{draft.conditions?.length || 0} active rule(s)</div>
            </div>
          </>
        ) : (
          <>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Policy Type</span>
              <div className="text-console-text font-semibold">{draft.policy_type}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Scope / Target</span>
              <div className="text-console-text font-semibold">{draft.scope ? `${draft.scope}: ${draft.scope_value}` : 'Global'}</div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Threshold / Limit</span>
              <div className="text-console-verify font-bold">
                {formatINR(draft.threshold || draft.limit || 0)}
                {draft.period && ` / ${draft.period}`}
              </div>
            </div>
            <div>
              <span className="text-console-muted text-[10px] uppercase">Action</span>
              <div className="text-console-verify font-bold">{draft.action}</div>
            </div>
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-2 pt-2 border-t border-console-border/60">
        <button
          onClick={onDiscard}
          disabled={isSubmitting}
          className="px-3 py-1.5 text-xs font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm hover:border-console-border/80 transition-colors"
        >
          DISCARD DRAFT
        </button>

        <button
          onClick={onConfirm}
          disabled={isSubmitting}
          className="px-4 py-1.5 text-xs font-mono font-bold bg-console-accent text-white rounded-sm hover:bg-blue-600 transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          <Check className="w-3.5 h-3.5" />
          <span>{isSubmitting ? 'PERSISTING...' : 'CONFIRM & PERSIST TO DB'}</span>
        </button>
      </div>
    </div>
  );
}
