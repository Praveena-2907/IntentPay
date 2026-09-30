import React, { useState } from 'react';
import { 
  X, CheckCircle, AlertTriangle, ShieldAlert, ChevronDown, ChevronRight, 
  Copy, Check, Clock, User, ArrowRight, Shield, Activity, DollarSign, 
  HelpCircle, Code, AlertOctagon
} from 'lucide-react';
import { StatusChip } from './StatusChip';
import { formatRupees, formatDateTime } from '../utils/format';

export function DecisionTraceDrawer({ trace, isOpen, onClose }) {
  const [copied, setCopied] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    s1: true, s2: true, s3: true, s4: true, s5: true, s6: true, s7: true, s8: true, s9: true
  });

  if (!isOpen || !trace) return null;

  const toggleSection = (key) => {
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(trace, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const decision = trace.decision || 'ALLOW';
  const rawInput = trace.raw_input || {};
  const intentEval = trace.intent_evaluation || {};
  const polEval = trace.policy_evaluation || {};
  const behSignals = trace.behavior_signals || [];
  const impact = trace.cash_flow_impact || {};
  const rules = trace.rules_evaluated || [];
  const reasons = trace.reasons || [];
  const tx = trace.transaction || {};

  const getDecisionIcon = (dec) => {
    switch (dec) {
      case 'ALLOW': return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case 'VERIFY': return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'HOLD': return <ShieldAlert className="w-5 h-5 text-rose-400" />;
      default: return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-sm flex justify-end animate-fade-in">
      {/* Drawer Container */}
      <div className="w-full max-w-3xl bg-console-card border-l border-console-border h-full flex flex-col shadow-2xl">
        
        {/* Drawer Header */}
        <div className="p-4 border-b border-console-border bg-console-dark flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getDecisionIcon(decision)}
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-sm font-bold text-white tracking-wider">
                  DECISION TRACE: {trace.id || trace.transaction_id || 'LIVE_TRACE'}
                </span>
                <StatusChip status={decision} size="sm" />
                {tx.status && <StatusChip status={tx.status} size="sm" />}
              </div>
              <p className="text-xs text-console-muted font-mono mt-0.5">
                Evaluated: {formatDateTime(trace.created_at || tx.timestamp || new Date().toISOString())}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={copyJson}
              className="p-1.5 text-console-muted hover:text-white bg-console-surface hover:bg-console-border rounded transition-colors text-xs font-mono flex items-center space-x-1"
              title="Copy Trace JSON"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'COPIED' : 'JSON'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-console-muted hover:text-white rounded hover:bg-console-border transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Drawer Body: 9 Ordered Stages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">

          {/* STAGE 1: INPUT NORMALIZATION */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s1')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">1</span>
                <span>INPUT NORMALIZATION</span>
              </div>
              {expandedSections.s1 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
            </button>
            {expandedSections.s1 && (
              <div className="p-3 grid grid-cols-2 gap-3 font-mono text-console-muted">
                <div>
                  <span className="block text-[10px] uppercase text-console-muted">Raw Recipient:</span>
                  <span className="text-white font-medium">{rawInput.recipient || tx.recipient || 'N/A'}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase text-console-muted">Normalized Recipient:</span>
                  <span className="text-white font-medium">{String(rawInput.recipient || tx.recipient || '').trim().toLowerCase() || 'N/A'}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase text-console-muted">Amount:</span>
                  <span className="text-white font-bold">{formatRupees(rawInput.amount || tx.amount || 0)}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase text-console-muted">Category:</span>
                  <span className="text-white font-medium">{rawInput.category || tx.category || 'N/A'}</span>
                </div>
              </div>
            )}
          </div>

          {/* STAGE 2: INTENT MATCH & EVALUATION */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s2')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">2</span>
                <span>INTENT MATCH & EVALUATION</span>
              </div>
              <div className="flex items-center space-x-2">
                <StatusChip status={intentEval.result || 'NO_MATCH'} size="sm" />
                {expandedSections.s2 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
              </div>
            </button>
            {expandedSections.s2 && (
              <div className="p-3 space-y-2 font-mono">
                <div className="flex justify-between items-center pb-2 border-b border-console-border/30">
                  <span className="text-console-muted">Matched Intent:</span>
                  <span className="text-white font-semibold">
                    {intentEval.matched_intent ? `${intentEval.matched_intent.purpose} (${intentEval.matched_intent.id})` : 'NO_MATCH (No active matching rule)'}
                  </span>
                </div>
                {intentEval.matched_intent && (
                  <>
                    <div className="flex justify-between text-console-muted">
                      <span>Configured Action:</span>
                      <StatusChip status={intentEval.matched_intent.action} size="sm" />
                    </div>
                    {intentEval.conditions_evaluated && intentEval.conditions_evaluated.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-console-border/20">
                        <span className="text-[10px] text-console-muted uppercase block mb-1">Conditions Evaluated:</span>
                        <div className="space-y-1">
                          {intentEval.conditions_evaluated.map((c, i) => (
                            <div key={i} className="flex justify-between items-center text-[11px] bg-console-dark/60 p-1.5 rounded">
                              <span className="text-console-muted">{c.field} {c.operator} {c.value}</span>
                              <span className={c.passed ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                                {c.passed ? 'PASS' : 'FAIL'} ({c.actual})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {intentEval.reason && (
                  <p className="text-console-muted text-[11px] italic mt-1">Reason: {intentEval.reason}</p>
                )}
              </div>
            )}
          </div>

          {/* STAGE 3: POLICY CHECKS */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s3')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">3</span>
                <span>PAYDNA POLICY EVALUATION</span>
              </div>
              <div className="flex items-center space-x-2">
                <StatusChip status={polEval.violations && polEval.violations.length > 0 ? 'FAIL' : 'PASS'} size="sm" />
                {expandedSections.s3 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
              </div>
            </button>
            {expandedSections.s3 && (
              <div className="p-3 space-y-2 font-mono">
                {polEval.evaluated_policies && polEval.evaluated_policies.length > 0 ? (
                  <div className="space-y-2">
                    {polEval.evaluated_policies.map((p, idx) => (
                      <div key={idx} className="p-2 rounded bg-console-dark/60 border border-console-border/30 flex justify-between items-center">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-white font-bold">{p.id}</span>
                            <span className="text-xs text-console-muted">[{p.policy_type}]</span>
                          </div>
                          <p className="text-[11px] text-console-muted mt-0.5">{p.description || p.detail}</p>
                        </div>
                        <StatusChip status={p.violated ? 'FAIL' : 'PASS'} size="sm" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-console-muted text-xs">No active policies configured.</p>
                )}
              </div>
            )}
          </div>

          {/* STAGE 4: BEHAVIORAL SIGNALS */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s4')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">4</span>
                <span>BEHAVIORAL ANOMALY SIGNALS</span>
              </div>
              <div className="flex items-center space-x-2">
                <StatusChip status={behSignals.length > 0 ? 'WARN' : 'PASS'} size="sm" />
                {expandedSections.s4 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
              </div>
            </button>
            {expandedSections.s4 && (
              <div className="p-3 space-y-3 font-mono">
                {behSignals.length === 0 ? (
                  <p className="text-emerald-400 text-xs flex items-center space-x-1.5">
                    <CheckCircle className="w-4 h-4" />
                    <span>All behavioral dimensions match established historical baseline.</span>
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {behSignals.map((sig, i) => (
                      <div key={i} className="flex justify-between items-center p-2 rounded bg-amber-500/10 border border-amber-500/30">
                        <div>
                          <span className="text-amber-400 font-bold block">{sig.signal || sig.type}</span>
                          <span className="text-[11px] text-console-muted">{sig.detail || sig.message}</span>
                        </div>
                        <StatusChip status={sig.level || 'MEDIUM'} size="sm" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* STAGE 5: FINAL SYNTHESIS & PRIORITY HIERARCHY */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s5')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">5</span>
                <span>DECISION SYNTHESIS & RULES EVALUATED</span>
              </div>
              <div className="flex items-center space-x-2">
                <StatusChip status={decision} size="sm" />
                {expandedSections.s5 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
              </div>
            </button>
            {expandedSections.s5 && (
              <div className="p-3 space-y-2 font-mono">
                <div className="space-y-1">
                  {rules.map((rule, idx) => (
                    <div key={idx} className="flex justify-between items-center p-1.5 bg-console-dark/60 rounded text-[11px]">
                      <div>
                        <span className="text-white font-semibold">{rule.label || rule.id}</span>
                        {rule.detail && <span className="text-console-muted ml-2">({rule.detail})</span>}
                      </div>
                      <StatusChip status={rule.result} size="sm" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* STAGE 6: ACTION EXECUTED */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s6')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">6</span>
                <span>ACTION EXECUTED & LIFECYCLE</span>
              </div>
              {expandedSections.s6 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
            </button>
            {expandedSections.s6 && (
              <div className="p-3 font-mono text-xs space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-console-muted">Status:</span>
                  <StatusChip status={tx.status || (decision === 'ALLOW' ? 'EXECUTED_SIMULATED' : decision === 'VERIFY' ? 'PENDING_VERIFICATION' : 'HELD')} size="sm" />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-console-muted">Payment Mode:</span>
                  <span className="text-white font-semibold">Simulated Execution (Zero Real Money)</span>
                </div>
              </div>
            )}
          </div>

          {/* STAGE 7: CASH-FLOW IMPACT */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s7')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">7</span>
                <span>CASH-FLOW LIQUIDITY IMPACT</span>
              </div>
              <div className="flex items-center space-x-2">
                <StatusChip status={impact.risk_level || 'LOW'} size="sm" />
                {expandedSections.s7 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
              </div>
            </button>
            {expandedSections.s7 && (
              <div className="p-3 grid grid-cols-2 gap-2 font-mono text-xs">
                <div className="bg-console-dark/60 p-2 rounded">
                  <span className="text-[10px] text-console-muted uppercase block">Available Liquidity:</span>
                  <span className="text-white font-bold">{formatRupees(impact.available_liquidity || 0)}</span>
                </div>
                <div className="bg-console-dark/60 p-2 rounded">
                  <span className="text-[10px] text-console-muted uppercase block">Projected Balance:</span>
                  <span className={`font-bold ${(impact.projected_balance || 0) < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {formatRupees(impact.projected_balance || 0)}
                  </span>
                </div>
                <div className="bg-console-dark/60 p-2 rounded">
                  <span className="text-[10px] text-console-muted uppercase block">Monthly Income Impact:</span>
                  <span className="text-white font-bold">{((impact.monthly_impact_pct || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-console-dark/60 p-2 rounded">
                  <span className="text-[10px] text-console-muted uppercase block">Risk Level:</span>
                  <span className="text-white font-bold">{impact.risk_level || 'LOW'}</span>
                </div>
              </div>
            )}
          </div>

          {/* STAGE 8: DETERMINISTIC HUMAN EXPLANATION */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s8')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">8</span>
                <span>DETERMINISTIC EXPLANATION (NO LLM)</span>
              </div>
              {expandedSections.s8 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
            </button>
            {expandedSections.s8 && (
              <div className="p-3 space-y-2 font-mono text-xs">
                {reasons.length > 0 ? (
                  <ul className="space-y-1 list-disc list-inside text-white">
                    {reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-emerald-400">Payment satisfies all active intent requirements and conforms with security policies.</p>
                )}
              </div>
            )}
          </div>

          {/* STAGE 9: CONFLICT & SAFETY ANALYSIS */}
          <div className="border border-console-border rounded bg-console-surface/50 overflow-hidden">
            <button
              onClick={() => toggleSection('s9')}
              className="w-full p-2.5 bg-console-surface/80 flex items-center justify-between text-left font-mono font-semibold text-white border-b border-console-border/40"
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px]">9</span>
                <span>CONFLICT & SAFETY ANALYSIS</span>
              </div>
              {expandedSections.s9 ? <ChevronDown className="w-4 h-4 text-console-muted" /> : <ChevronRight className="w-4 h-4 text-console-muted" />}
            </button>
            {expandedSections.s9 && (
              <div className="p-3 font-mono text-xs space-y-1">
                <p className="text-console-muted">Cross-checked against all configured security policies and intents.</p>
                <p className="text-emerald-400 font-semibold">Zero blocking race-conditions or intent conflicts detected.</p>
              </div>
            )}
          </div>

          {/* RAW JSON TOGGLE */}
          <div className="pt-2 border-t border-console-border">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="flex items-center space-x-1.5 text-console-muted hover:text-white font-mono text-xs transition-colors"
            >
              <Code className="w-4 h-4" />
              <span>{showRawJson ? 'HIDE RAW JSON PAYLOAD' : 'INSPECT RAW JSON PAYLOAD'}</span>
            </button>
            {showRawJson && (
              <pre className="mt-2 p-3 bg-console-dark rounded border border-console-border text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-60">
                {JSON.stringify(trace, null, 2)}
              </pre>
            )}
          </div>

        </div>

        {/* Drawer Footer */}
        <div className="p-3 border-t border-console-border bg-console-dark flex justify-between items-center text-xs font-mono text-console-muted">
          <span>INTENTPAY ENGINE V2.0</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 bg-console-surface hover:bg-console-border text-white rounded transition-colors"
          >
            CLOSE TRACE
          </button>
        </div>

      </div>
    </div>
  );
}
