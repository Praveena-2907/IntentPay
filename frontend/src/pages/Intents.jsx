import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatINR, formatTimestamp } from '../utils/format';
import { ParseReview } from '../components/ParseReview';
import { ConflictDialog } from '../components/ConflictDialog';
import { ToastAlert } from '../components/ToastAlert';
import { StatusChip } from '../components/StatusChip';
import { Brain, Sparkles, Plus, Play, Pause, Trash2, AlertCircle } from 'lucide-react';

const SUGGESTED_EXAMPLES = [
  "Pay my electricity bill automatically if it is below ₹3000.",
  "Send my mother ₹10000 every month.",
  "Pay rent of ₹15000 automatically on the 5th after salary.",
  "Pay water bill automatically if bill amount is under ₹600."
];

export function Intents() {
  const [nlText, setNlText] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [activeConflict, setActiveConflict] = useState(null);

  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchIntents = async () => {
    try {
      setLoading(true);
      const data = await api.getIntents();
      setIntents(data);
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntents();
  }, []);

  const handleParse = async (e) => {
    e.preventDefault();
    if (!nlText.trim()) return;

    try {
      setIsParsing(true);
      setFeedback(null);
      const res = await api.parseIntent(nlText);
      setParseResult(res);

      if (res.conflicts && res.conflicts.length > 0) {
        setActiveConflict(res.conflicts[0]);
      }
    } catch (err) {
      setFeedback({ type: 'error', message: 'Parsing failed: ' + err.message });
    } finally {
      setIsParsing(false);
    }
  };

  const handleConfirmPersist = async () => {
    if (!parseResult?.draft) return;
    try {
      setIsSubmitting(true);
      const created = await api.createIntent(parseResult.draft);
      setFeedback({
        type: 'success',
        message: `Intent ${created.id} ('${created.purpose}') successfully confirmed and active.`
      });
      setParseResult(null);
      setNlText('');
      await fetchIntents();
    } catch (err) {
      setFeedback({ type: 'error', message: 'Failed to persist intent: ' + err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePauseToggle = async (intent) => {
    try {
      if (intent.status === 'ACTIVE') {
        await api.pauseIntent(intent.id);
      } else {
        await api.resumeIntent(intent.id);
      }
      await fetchIntents();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete intent ${id}?`)) return;
    try {
      await api.deleteIntent(id);
      setFeedback({ type: 'info', message: `Intent ${id} deleted.` });
      await fetchIntents();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-6xl mx-auto">
      {/* Title */}
      <div className="border-b border-console-border pb-3">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-console-accent" />
          <h1 className="text-lg font-mono font-bold text-console-text">
            PAYMENT INTENT MANAGER
          </h1>
        </div>
        <p className="text-xs font-sans text-console-muted mt-0.5">
          Program natural-language intents into structured automated payment rules. LLMs parse proposals; rules only activate upon explicit user confirmation.
        </p>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <ToastAlert
          type={feedback.type}
          message={feedback.message}
          onDismiss={() => setFeedback(null)}
        />
      )}

      {/* Conflict Dialog */}
      {activeConflict && (
        <ConflictDialog
          conflict={activeConflict}
          onKeepPolicy={() => setActiveConflict(null)}
          onUpdateIntent={() => {
            setActiveConflict(null);
            setParseResult(null);
          }}
          onCancel={() => {
            setActiveConflict(null);
            setParseResult(null);
          }}
        />
      )}

      {/* Natural Language Creation Box */}
      <div className="bg-console-surface border border-console-border rounded-sm p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
            PROGRAM NEW PAYMENT INTENT (NATURAL LANGUAGE)
          </span>
          <span className="text-[10px] font-mono text-console-muted">CONFIRMATION REQUIRED</span>
        </div>

        <form onSubmit={handleParse} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={nlText}
              onChange={(e) => setNlText(e.target.value)}
              placeholder="e.g. Pay my electricity bill automatically if it is below ₹3000."
              className="flex-1 bg-console-bg border border-console-border px-3 py-2 text-xs font-mono text-console-text rounded-sm focus:outline-none focus:border-console-accent"
            />
            <button
              type="submit"
              disabled={isParsing || !nlText.trim()}
              className="px-4 py-2 text-xs font-mono font-bold bg-console-accent text-white rounded-sm hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shrink-0"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isParsing ? 'PARSING...' : 'PARSE INTENT'}</span>
            </button>
          </div>

          {/* Preset Prompts Pills */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[10px] font-mono text-console-muted uppercase mr-1">PRESETS:</span>
            {SUGGESTED_EXAMPLES.map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setNlText(ex)}
                className="px-2 py-0.5 text-[10px] font-mono bg-console-surface-2 hover:bg-console-border border border-console-border rounded-sm text-console-muted hover:text-console-text transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Parse Review Card (if draft available) */}
      {parseResult && (
        <ParseReview
          draft={parseResult.draft}
          source={parseResult.source}
          warnings={parseResult.warnings}
          onConfirm={handleConfirmPersist}
          onDiscard={() => setParseResult(null)}
          isSubmitting={isSubmitting}
        />
      )}

      {/* Active Intents Table */}
      <div className="bg-console-surface border border-console-border rounded-sm">
        <div className="p-3.5 border-b border-console-border flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
            CONFIGURED INTENTS ({intents.length})
          </span>
          <span className="text-[10px] font-mono text-console-muted">EVALUATED AT PAYMENT RUNTIME</span>
        </div>

        {loading ? (
          <div className="p-6 text-center text-xs font-mono text-console-muted">
            LOADING CONFIGURED INTENTS...
          </div>
        ) : intents.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-console-muted">
            NO ACTIVE INTENTS CONFIGURED. PROGRAM AN INTENT ABOVE.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-console-surface-2 text-console-muted uppercase text-[10px] tracking-wider border-b border-console-border">
                <tr>
                  <th className="py-2.5 px-3">ID</th>
                  <th className="py-2.5 px-3">PURPOSE</th>
                  <th className="py-2.5 px-3">TARGET</th>
                  <th className="py-2.5 px-3">AMOUNT / CEILING</th>
                  <th className="py-2.5 px-3">ACTION</th>
                  <th className="py-2.5 px-3">FREQUENCY</th>
                  <th className="py-2.5 px-3">STATUS</th>
                  <th className="py-2.5 px-3 text-right">MANAGE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-border/60">
                {intents.map((intent) => (
                  <tr key={intent.id} className="hover:bg-console-surface-2/60 transition-colors h-10">
                    <td className="py-2 px-3 font-semibold text-console-accent">{intent.id}</td>
                    <td className="py-2 px-3 text-console-text font-medium">{intent.purpose}</td>
                    <td className="py-2 px-3 text-console-muted">
                      {intent.recipient || 'Any'} [{intent.category}]
                    </td>
                    <td className="py-2 px-3 font-bold text-console-text">
                      {intent.amount ? formatINR(intent.amount) : (intent.max_amount ? `Max ${formatINR(intent.max_amount)}` : 'Dynamic')}
                    </td>
                    <td className="py-2 px-3 font-bold text-console-allow">{intent.action}</td>
                    <td className="py-2 px-3 text-console-muted">
                      {intent.frequency} {intent.day_of_month ? `(Day ${intent.day_of_month})` : ''}
                    </td>
                    <td className="py-2 px-3">
                      <StatusChip status={intent.status} size="sm" />
                    </td>
                    <td className="py-2 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handlePauseToggle(intent)}
                          title={intent.status === 'ACTIVE' ? 'Pause Intent' : 'Resume Intent'}
                          className="p-1 text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm hover:border-console-border/80"
                        >
                          {intent.status === 'ACTIVE' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                        <button
                          onClick={() => handleDelete(intent.id)}
                          title="Delete Intent"
                          className="p-1 text-console-muted hover:text-console-hold bg-console-surface-2 border border-console-border rounded-sm hover:border-console-hold/40"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
