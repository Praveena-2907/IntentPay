import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatINR } from '../utils/format';
import { StatusChip } from '../components/StatusChip';
import { ToastAlert } from '../components/ToastAlert';
import { BookOpen, Shield, Brain, Power } from 'lucide-react';

export function Constitution() {
  const [policies, setPolicies] = useState([]);
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [polData, intData] = await Promise.all([
        api.getPolicies(),
        api.getIntents()
      ]);
      setPolicies(polData);
      setIntents(intData);
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTogglePolicy = async (pol) => {
    try {
      const newStatus = pol.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
      await api.updatePolicy(pol.id, { status: newStatus });
      await fetchData();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  // Group policies
  const limitPolicies = policies.filter((p) => p.policy_type === 'MAX_TRANSACTION_AMOUNT');
  const recipientPolicies = policies.filter((p) => p.policy_type === 'NEW_RECIPIENT_LIMIT' || p.scope === 'RECIPIENT');
  const periodPolicies = policies.filter((p) => p.policy_type === 'PERIOD_LIMIT' && p.scope !== 'RECIPIENT');
  const autoPayIntents = intents.filter((i) => i.action === 'AUTO_PAY');

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-console-border pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-console-accent" />
          <h1 className="text-lg font-mono font-bold text-console-text">
            PAYMENT CONSTITUTION & DERIVED POLICY SET
          </h1>
        </div>
        <p className="text-xs font-mono text-console-muted mt-1 uppercase tracking-wider">
          User-defined policy set. Not a legal document.
        </p>
      </div>

      {feedback && (
        <ToastAlert
          type={feedback.type}
          message={feedback.message}
          onDismiss={() => setFeedback(null)}
        />
      )}

      {loading ? (
        <div className="p-8 text-center text-xs font-mono text-console-muted">
          COMPILING CONSTITUTIONAL ARTICLES...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Article Group 1: General Limits */}
          <div className="bg-console-surface border border-console-border rounded-sm">
            <div className="p-3 bg-console-surface-2 border-b border-console-border flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-console-text uppercase tracking-wider">
                ARTICLE I — GENERAL TRANSACTION CEILINGS & CAPS
              </span>
              <span className="text-[10px] font-mono text-console-muted">{limitPolicies.length} POLICIES</span>
            </div>

            <div className="divide-y divide-console-border/60">
              {limitPolicies.length === 0 ? (
                <div className="p-4 text-xs font-mono text-console-muted text-center">No limit policies registered.</div>
              ) : (
                limitPolicies.map((p) => (
                  <div key={p.id} className="p-3.5 flex items-center justify-between gap-4 text-xs font-mono hover:bg-console-surface-2/40 transition-colors">
                    <div>
                      <div className="font-semibold text-console-text">
                        <span className="text-console-accent mr-2">{p.id}</span>
                        {p.description}
                      </div>
                      <div className="text-[11px] text-console-muted mt-0.5">
                        Cap: {formatINR(p.threshold || 0)} · Action: {p.action}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusChip status={p.status} size="sm" />
                      <button
                        onClick={() => handleTogglePolicy(p)}
                        className="px-2 py-0.5 text-[10px] font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm"
                      >
                        {p.status === 'ACTIVE' ? 'PAUSE' : 'ACTIVATE'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Article Group 2: Recipient Rules */}
          <div className="bg-console-surface border border-console-border rounded-sm">
            <div className="p-3 bg-console-surface-2 border-b border-console-border flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-console-text uppercase tracking-wider">
                ARTICLE II — RECIPIENT TRUST & IDENTITY GUARDRAILS
              </span>
              <span className="text-[10px] font-mono text-console-muted">{recipientPolicies.length} POLICIES</span>
            </div>

            <div className="divide-y divide-console-border/60">
              {recipientPolicies.map((p) => (
                <div key={p.id} className="p-3.5 flex items-center justify-between gap-4 text-xs font-mono hover:bg-console-surface-2/40 transition-colors">
                  <div>
                    <div className="font-semibold text-console-text">
                      <span className="text-console-accent mr-2">{p.id}</span>
                      {p.description}
                    </div>
                    <div className="text-[11px] text-console-muted mt-0.5">
                      Scope: {p.scope ? `${p.scope} (${p.scope_value})` : 'New Recipient'} · Action: {p.action}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusChip status={p.status} size="sm" />
                    <button
                      onClick={() => handleTogglePolicy(p)}
                      className="px-2 py-0.5 text-[10px] font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm"
                    >
                      {p.status === 'ACTIVE' ? 'PAUSE' : 'ACTIVATE'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Article Group 3: Period Limits */}
          <div className="bg-console-surface border border-console-border rounded-sm">
            <div className="p-3 bg-console-surface-2 border-b border-console-border flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-console-text uppercase tracking-wider">
                ARTICLE III — CATEGORY VELOCITY & PERIODIC EXPENDITURE CAPS
              </span>
              <span className="text-[10px] font-mono text-console-muted">{periodPolicies.length} POLICIES</span>
            </div>

            <div className="divide-y divide-console-border/60">
              {periodPolicies.map((p) => (
                <div key={p.id} className="p-3.5 flex items-center justify-between gap-4 text-xs font-mono hover:bg-console-surface-2/40 transition-colors">
                  <div>
                    <div className="font-semibold text-console-text">
                      <span className="text-console-accent mr-2">{p.id}</span>
                      {p.description}
                    </div>
                    <div className="text-[11px] text-console-muted mt-0.5">
                      Limit: {formatINR(p.limit || 0)} / {p.period?.toLowerCase()} window (rolling {p.period === 'WEEK' ? '7' : '30'} days)
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusChip status={p.status} size="sm" />
                    <button
                      onClick={() => handleTogglePolicy(p)}
                      className="px-2 py-0.5 text-[10px] font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border rounded-sm"
                    >
                      {p.status === 'ACTIVE' ? 'PAUSE' : 'ACTIVATE'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Article Group 4: Derived Auto-Pay Articles from Intents */}
          <div className="bg-console-surface border border-console-border rounded-sm">
            <div className="p-3 bg-console-surface-2 border-b border-console-border flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-console-text uppercase tracking-wider">
                ARTICLE IV — DERIVED AUTO-PAY DISCRETIONS (DERIVED FROM INTENTS)
              </span>
              <span className="text-[10px] font-mono text-console-muted">{autoPayIntents.length} ACTIVE RULES</span>
            </div>

            <div className="divide-y divide-console-border/60">
              {autoPayIntents.map((i) => (
                <div key={i.id} className="p-3.5 flex items-center justify-between gap-4 text-xs font-mono hover:bg-console-surface-2/40 transition-colors">
                  <div>
                    <div className="font-semibold text-console-text">
                      <span className="text-console-accent mr-2">{i.id}</span>
                      Automated clearance for {i.purpose} ({i.category})
                    </div>
                    <div className="text-[11px] text-console-muted mt-0.5">
                      Target: {i.recipient || 'Category-wide'} · Amount: {i.amount ? formatINR(i.amount) : (i.max_amount ? `Max ${formatINR(i.max_amount)}` : 'Condition-based')} · {i.frequency}
                    </div>
                  </div>
                  <div>
                    <StatusChip status="ALLOW" size="sm" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
