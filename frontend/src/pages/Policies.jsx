import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatINR } from '../utils/format';
import { ParseReview } from '../components/ParseReview';
import { ToastAlert } from '../components/ToastAlert';
import { StatusChip } from '../components/StatusChip';
import { Shield, Sparkles, Trash2, AlertCircle } from 'lucide-react';

const SUGGESTED_EXAMPLES = [
  "Any new recipient above ₹5000 requires confirmation.",
  "Payments above ₹25,000 require verification.",
  "Weekly shopping limit ₹10,000.",
  "Food payments above ₹2000 require confirmation."
];

export function Policies() {
  const [nlText, setNlText] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [parseResult, setParseResult] = useState(null);

  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const data = await api.getPolicies();
      setPolicies(data);
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleParse = async (e) => {
    e.preventDefault();
    if (!nlText.trim()) return;

    try {
      setIsParsing(true);
      setFeedback(null);
      const res = await api.parsePolicy(nlText);
      setParseResult(res);
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
      const created = await api.createPolicy(parseResult.draft);
      setFeedback({
        type: 'success',
        message: `Policy ${created.id} ('${created.description}') confirmed and activated.`
      });
      setParseResult(null);
      setNlText('');
      await fetchPolicies();
    } catch (err) {
      if (err.status === 409) {
        setFeedback({
          type: 'warning',
          message: err.message || 'Duplicate policy detected with identical parameters.'
        });
      } else {
        setFeedback({ type: 'error', message: 'Failed to persist policy: ' + err.message });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete policy ${id}?`)) return;
    try {
      await api.deletePolicy(id);
      setFeedback({ type: 'info', message: `Policy ${id} deleted.` });
      await fetchPolicies();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-6xl mx-auto">
      {/* Title */}
      <div className="border-b border-console-border pb-3">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-console-verify" />
          <h1 className="text-lg font-mono font-bold text-console-text">
            PAYDNA SECURITY POLICY RULES
          </h1>
        </div>
        <p className="text-xs font-sans text-console-muted mt-0.5">
          Program deterministic financial guardrails (caps, velocity limits, and verification thresholds). Duplicate parameters are blocked with HTTP 409.
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

      {/* Natural Language Creation Box */}
      <div className="bg-console-surface border border-console-border rounded-sm p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
            PROGRAM NEW PAYDNA POLICY (NATURAL LANGUAGE)
          </span>
          <span className="text-[10px] font-mono text-console-muted">CONFIRMATION REQUIRED</span>
        </div>

        <form onSubmit={handleParse} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={nlText}
              onChange={(e) => setNlText(e.target.value)}
              placeholder="e.g. Any new recipient above ₹5000 requires confirmation."
              className="flex-1 bg-console-bg border border-console-border px-3 py-2 text-xs font-mono text-console-text rounded-sm focus:outline-none focus:border-console-accent"
            />
            <button
              type="submit"
              disabled={isParsing || !nlText.trim()}
              className="px-4 py-2 text-xs font-mono font-bold bg-console-verify text-black rounded-sm hover:bg-amber-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 shrink-0"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isParsing ? 'PARSING...' : 'PARSE POLICY'}</span>
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
          type="policy"
          source={parseResult.source}
          warnings={parseResult.warnings}
          onConfirm={handleConfirmPersist}
          onDiscard={() => setParseResult(null)}
          isSubmitting={isSubmitting}
        />
      )}

      {/* Active Policies Table */}
      <div className="bg-console-surface border border-console-border rounded-sm">
        <div className="p-3.5 border-b border-console-border flex items-center justify-between">
          <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
            CONFIGURED PAYDNA POLICIES ({policies.length})
          </span>
          <span className="text-[10px] font-mono text-console-muted">STRICT EVALUATION AT RUNTIME</span>
        </div>

        {loading ? (
          <div className="p-6 text-center text-xs font-mono text-console-muted">
            LOADING POLICIES...
          </div>
        ) : policies.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-console-muted">
            NO POLICIES CONFIGURED.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-console-surface-2 text-console-muted uppercase text-[10px] tracking-wider border-b border-console-border">
                <tr>
                  <th className="py-2.5 px-3">ID</th>
                  <th className="py-2.5 px-3">POLICY TYPE</th>
                  <th className="py-2.5 px-3">SCOPE / TARGET</th>
                  <th className="py-2.5 px-3">THRESHOLD / LIMIT</th>
                  <th className="py-2.5 px-3">ACTION</th>
                  <th className="py-2.5 px-3">DESCRIPTION</th>
                  <th className="py-2.5 px-3">STATUS</th>
                  <th className="py-2.5 px-3 text-right">MANAGE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-border/60">
                {policies.map((pol) => (
                  <tr key={pol.id} className="hover:bg-console-surface-2/60 transition-colors h-10">
                    <td className="py-2 px-3 font-semibold text-console-verify">{pol.id}</td>
                    <td className="py-2 px-3 text-console-text font-medium">{pol.policy_type}</td>
                    <td className="py-2 px-3 text-console-muted">
                      {pol.scope ? `${pol.scope}: ${pol.scope_value}` : 'Global'}
                    </td>
                    <td className="py-2 px-3 font-bold text-console-text">
                      {formatINR(pol.threshold || pol.limit || 0)}
                      {pol.period && ` / ${pol.period.toLowerCase()}`}
                    </td>
                    <td className="py-2 px-3">
                      <StatusChip status={pol.action} size="sm" />
                    </td>
                    <td className="py-2 px-3 text-console-muted max-w-xs truncate">{pol.description}</td>
                    <td className="py-2 px-3">
                      <StatusChip status={pol.status} size="sm" />
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={() => handleDelete(pol.id)}
                        title="Delete Policy"
                        className="p-1 text-console-muted hover:text-console-hold bg-console-surface-2 border border-console-border rounded-sm hover:border-console-hold/40"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
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
