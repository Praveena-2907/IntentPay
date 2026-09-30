import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, RefreshCw, CheckCircle, AlertTriangle, ShieldAlert, ArrowRight,
  TrendingDown, DollarSign, Calendar, Tag, User, Info, Check, X
} from 'lucide-react';
import { api } from '../services/api';
import { PipelineStrip } from '../components/PipelineStrip';
import { DecisionBanner } from '../components/DecisionBanner';
import { RuleRow } from '../components/RuleRow';
import { StatusChip } from '../components/StatusChip';
import { DecisionTraceDrawer } from '../components/DecisionTraceDrawer';
import { formatRupees } from '../utils/format';

const PRESETS = [
  {
    label: 'Test 1: Happy Path (Bescom ₹2.5k)',
    recipient: 'Bescom',
    amount: 2500,
    category: 'Utilities',
    purpose: 'Monthly electricity bill',
    time: '14:00'
  },
  {
    label: 'Test 2: Exceeds Limit (Bescom ₹4.2k)',
    recipient: 'Bescom',
    amount: 4200,
    category: 'Utilities',
    purpose: 'Spike electricity bill',
    time: '14:00'
  },
  {
    label: 'Test 3: New Recipient (Sneha ₹8k)',
    recipient: 'Sneha Rao',
    amount: 8000,
    category: 'Transfer',
    purpose: 'Peer transfer to new contact',
    time: '15:30'
  },
  {
    label: 'Test 4: Anomaly Cascade (Crypto ₹85k @ 03:15)',
    recipient: 'Crypto Global',
    amount: 85000,
    category: 'Investment',
    purpose: 'High value night-time transfer',
    time: '03:15'
  },
  {
    label: 'Test 5: Exceeds Balance (Tanishq ₹30k)',
    recipient: 'Tanishq',
    amount: 30000,
    category: 'Shopping',
    purpose: 'Jewellery purchase',
    time: '16:00'
  },
  {
    label: 'Test 6: Blocked Intent (Stake Casino ₹2k)',
    recipient: 'Stake Casino',
    amount: 2000,
    category: 'Entertainment',
    purpose: 'Online betting',
    time: '21:00'
  }
];

const KNOWN_RECIPIENTS = [
  'Bescom', 'ACT Fibernet', 'Swiggy', 'Uber', 'Cult.fit', 'Airtel', 
  'Amazon', 'Zomato', 'Urban Company', 'Flipkart'
];

const CATEGORIES = [
  'Utilities', 'Internet', 'Food & Dining', 'Travel', 'Transfer', 
  'Investment', 'Shopping', 'Entertainment', 'Rent', 'General'
];

export function Simulator() {
  const [recipient, setRecipient] = useState('Bescom');
  const [amount, setAmount] = useState(2500);
  const [category, setCategory] = useState('Utilities');
  const [purpose, setPurpose] = useState('Monthly electricity bill');
  const [timeStr, setTimeStr] = useState('14:00');
  const [clientRequestId, setClientRequestId] = useState(() => crypto.randomUUID());

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Execution state
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  // Trace drawer
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Rule rows expand state
  const [rulesExpanded, setRulesExpanded] = useState(true);

  // Trigger analysis on form changes
  useEffect(() => {
    runAnalysis();
  }, [recipient, amount, category, timeStr]);

  const runAnalysis = async () => {
    if (!amount || amount < 1 || !recipient.trim()) return;
    try {
      setAnalyzing(true);
      setErrorMsg(null);
      
      const [hours, minutes] = (timeStr || '12:00').split(':').map(Number);
      const now = new Date();
      now.setHours(hours || 12, minutes || 0, 0, 0);

      const payload = {
        recipient: recipient.trim(),
        amount: Number(amount),
        category,
        purpose: purpose || undefined,
        timestamp: now.toISOString(),
        client_request_id: clientRequestId
      };

      const res = await api.analyzePayment(payload);
      setAnalysisResult(res);
      // Clear prior execution if inputs change
      setExecutionResult(null);
    } catch (err) {
      console.error('Analysis error:', err);
      setErrorMsg(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplyPreset = (p) => {
    setRecipient(p.recipient);
    setAmount(p.amount);
    setCategory(p.category);
    setPurpose(p.purpose);
    setTimeStr(p.time);
    setClientRequestId(crypto.randomUUID());
    setExecutionResult(null);
  };

  const handleSimulateExecution = async () => {
    if (!amount || amount < 1 || !recipient.trim()) return;
    try {
      setExecuting(true);
      setErrorMsg(null);

      const [hours, minutes] = (timeStr || '12:00').split(':').map(Number);
      const now = new Date();
      now.setHours(hours || 12, minutes || 0, 0, 0);

      const payload = {
        recipient: recipient.trim(),
        amount: Number(amount),
        category,
        purpose: purpose || undefined,
        timestamp: now.toISOString(),
        client_request_id: clientRequestId
      };

      const res = await api.simulatePayment(payload);
      setExecutionResult(res);
    } catch (err) {
      console.error('Execution error:', err);
      setErrorMsg(err.message);
    } finally {
      setExecuting(false);
    }
  };

  const handleConfirmPayment = async () => {
    if (!executionResult?.transaction?.id) return;
    try {
      setExecuting(true);
      const res = await api.confirmPayment(executionResult.transaction.id);
      setExecutionResult(prev => ({
        ...prev,
        transaction: {
          ...prev.transaction,
          status: 'EXECUTED_SIMULATED'
        },
        verified: true
      }));
    } catch (err) {
      alert('Confirmation failed: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  const handleRejectPayment = async () => {
    if (!executionResult?.transaction?.id) return;
    try {
      setExecuting(true);
      const res = await api.rejectPayment(executionResult.transaction.id);
      setExecutionResult(prev => ({
        ...prev,
        transaction: {
          ...prev.transaction,
          status: 'REJECTED'
        }
      }));
    } catch (err) {
      alert('Rejection failed: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  const handleOpenTrace = async () => {
    try {
      if (executionResult?.transaction?.id) {
        const trace = await api.getPaymentTrace(executionResult.transaction.id);
        setSelectedTrace(trace);
        setDrawerOpen(true);
      } else if (analysisResult) {
        // Construct live analysis trace
        const liveTrace = {
          id: 'TRACE_PREVIEW',
          transaction_id: 'SIMULATED_PREVIEW',
          decision: analysisResult.decision,
          reasons: analysisResult.reasons,
          rules_evaluated: analysisResult.rules_evaluated,
          intent_evaluation: analysisResult.intent_evaluation,
          policy_evaluation: analysisResult.policy_evaluation,
          behavior_signals: analysisResult.behavior_signals,
          cash_flow_impact: analysisResult.cash_flow_impact,
          raw_input: { recipient, amount, category, purpose },
          created_at: new Date().toISOString()
        };
        setSelectedTrace(liveTrace);
        setDrawerOpen(true);
      }
    } catch (err) {
      alert('Unable to load decision trace: ' + err.message);
    }
  };

  const impact = analysisResult?.cash_flow_impact || {};

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-console-border gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white tracking-wide flex items-center space-x-2">
            <span className="w-2.5 h-2.5 bg-blue-500 rounded-sm inline-block"></span>
            <span>PAYMENT SIMULATOR & DECISION SANDBOX</span>
          </h1>
          <p className="text-xs text-console-muted font-mono mt-1">
            Simulate payment requests through live Intent matching, PayDNA policies, and behavioral anomaly heuristics.
          </p>
        </div>

        <button
          onClick={() => {
            setClientRequestId(crypto.randomUUID());
            setExecutionResult(null);
            runAnalysis();
          }}
          className="self-start md:self-auto px-3 py-1.5 bg-console-surface hover:bg-console-border border border-console-border rounded text-xs font-mono text-console-muted hover:text-white flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>NEW SESSION</span>
        </button>
      </div>

      {/* Preset Scenarios (Section 9 Demo Scripts) */}
      <div className="bg-console-card border border-console-border rounded p-3">
        <span className="text-[11px] font-mono text-console-muted uppercase tracking-wider block mb-2 font-semibold">
          LOAD VERIFICATION PRESETS (SECTION 9 TEST MATRIX):
        </span>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleApplyPreset(p)}
              className="p-2 bg-console-dark hover:bg-console-surface border border-console-border/60 hover:border-blue-500/50 rounded text-left transition-colors"
            >
              <span className="block text-[11px] font-mono text-white font-semibold truncate">{p.label}</span>
              <span className="block text-[10px] font-mono text-console-muted mt-0.5">{p.recipient} • {formatRupees(p.amount)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Two-Column Simulator Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: Form & Cash Impact (5 cols) */}
        <div className="lg:col-span-5 space-y-6">

          {/* Payment Form */}
          <div className="bg-console-card border border-console-border rounded p-4 space-y-4">
            <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2 border-b border-console-border pb-2">
              <DollarSign className="w-4 h-4 text-blue-400" />
              <span>PAYMENT PARAMETERS</span>
            </h2>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-console-muted mb-1 text-[11px] uppercase">
                  Recipient Name:
                </label>
                <input
                  type="text"
                  list="known-recipients"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  placeholder="e.g. Bescom, Sneha Rao"
                  className="w-full bg-console-dark border border-console-border rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                />
                <datalist id="known-recipients">
                  {KNOWN_RECIPIENTS.map((r, i) => (
                    <option key={i} value={r} />
                  ))}
                </datalist>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-console-muted mb-1 text-[11px] uppercase">
                    Amount (INR):
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={amount}
                    onChange={(e) => setAmount(Math.max(1, parseInt(e.target.value) || 0))}
                    className="w-full bg-console-dark border border-console-border rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-console-muted mb-1 text-[11px] uppercase">
                    Time (HH:MM):
                  </label>
                  <input
                    type="time"
                    value={timeStr}
                    onChange={(e) => setTimeStr(e.target.value)}
                    className="w-full bg-console-dark border border-console-border rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-console-muted mb-1 text-[11px] uppercase">
                  Category:
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-console-dark border border-console-border rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                >
                  {CATEGORIES.map((cat, i) => (
                    <option key={i} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-console-muted mb-1 text-[11px] uppercase">
                  Payment Purpose / Memo:
                </label>
                <input
                  type="text"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  placeholder="e.g. Utility settlement"
                  className="w-full bg-console-dark border border-console-border rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>

            {/* Simulate Execution Button */}
            <div className="pt-2">
              <button
                onClick={handleSimulateExecution}
                disabled={executing || analyzing || !amount}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-mono font-bold text-xs rounded transition-colors flex items-center justify-center space-x-2 shadow-lg disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>SIMULATING PAYMENT EXECUTION...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>SIMULATE EXECUTION</span>
                  </>
                )}
              </button>
              <div className="flex justify-between items-center text-[10px] font-mono text-console-muted mt-2">
                <span>IDEMPOTENCY: {clientRequestId.substring(0, 13)}...</span>
                <span>SIMULATED ONLY</span>
              </div>
            </div>
          </div>

          {/* Cash-Flow Impact Preview Panel */}
          <div className="bg-console-card border border-console-border rounded p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-console-border pb-2">
              <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <TrendingDown className="w-4 h-4 text-emerald-400" />
                <span>CASH-FLOW IMPACT PREVIEW</span>
              </h2>
              {(impact.impact_level || impact.risk_level) && (
                <StatusChip status={impact.impact_level || impact.risk_level} size="sm" />
              )}
            </div>

            {((impact.impact_level || impact.risk_level) === 'EXCEEDS_AVAILABLE' || impact.warning) && (
              <div className={`p-2 rounded text-xs font-mono flex items-center space-x-2 ${
                (impact.impact_level || impact.risk_level) === 'EXCEEDS_AVAILABLE' 
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30 font-bold' 
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
              }`}>
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>
                  {(impact.impact_level || impact.risk_level) === 'EXCEEDS_AVAILABLE'
                    ? 'EXCEEDS AVAILABLE LIQUIDITY: Projected balance is negative'
                    : impact.warning}
                </span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <div className="bg-console-dark p-2.5 rounded border border-console-border/40">
                <span className="block text-[10px] text-console-muted uppercase">Available Liquidity:</span>
                <span className="text-white font-bold text-sm">{formatRupees(impact.available_liquidity || 0)}</span>
              </div>

              <div className="bg-console-dark p-2.5 rounded border border-console-border/40">
                <span className="block text-[10px] text-console-muted uppercase">Projected Balance:</span>
                <span className={`font-bold text-sm ${(impact.projected_balance || 0) < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {formatRupees(impact.projected_balance || 0)}
                </span>
              </div>

              <div className="bg-console-dark p-2.5 rounded border border-console-border/40">
                <span className="block text-[10px] text-console-muted uppercase">Runway (Before / After):</span>
                <span className="text-white font-bold">
                  {impact.runway_days_before ?? '—'}d <span className="text-console-muted">→</span> {impact.runway_days_after ?? '—'}d
                </span>
              </div>

              <div className="bg-console-dark p-2.5 rounded border border-console-border/40">
                <span className="block text-[10px] text-console-muted uppercase">Monthly Income Impact:</span>
                <span className="text-white font-bold">{((impact.monthly_impact_pct || 0) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Live Pipeline, Decision & Execution Receipts (7 cols) */}
        <div className="lg:col-span-7 space-y-6">

          {/* Live Pipeline Strip */}
          <div className="bg-console-card border border-console-border rounded p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-console-border pb-2">
              <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                EVALUATION PIPELINE STAGES
              </h2>
              {analyzing && (
                <span className="text-[10px] font-mono text-blue-400 animate-pulse flex items-center space-x-1">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>ANALYZING...</span>
                </span>
              )}
            </div>

            <PipelineStrip pipelineStatus={analysisResult?.pipeline_status} />
          </div>

          {/* Decision Banner */}
          {analysisResult && (
            <DecisionBanner
              decision={analysisResult.decision}
              reasons={analysisResult.reasons}
              explanation={analysisResult.explanation}
              rulesEvaluated={analysisResult.rules_evaluated}
            />
          )}

          {/* Execution Result Card (ALLOW receipt, VERIFY prompt, HOLD notice) */}
          {executionResult && (
            <div className="bg-console-card border-2 border-console-border rounded p-5 space-y-4 animate-fade-in shadow-xl">
              <div className="flex items-center justify-between border-b border-console-border pb-3">
                <div className="flex items-center space-x-3">
                  {executionResult.decision === 'ALLOW' && <CheckCircle className="w-6 h-6 text-emerald-400" />}
                  {executionResult.decision === 'VERIFY' && <AlertTriangle className="w-6 h-6 text-amber-400" />}
                  {executionResult.decision === 'HOLD' && <ShieldAlert className="w-6 h-6 text-rose-400" />}
                  <div>
                    <h3 className="font-mono font-bold text-sm text-white">
                      SIMULATION OUTCOME: {executionResult.transaction?.id}
                    </h3>
                    <p className="text-xs text-console-muted font-mono">
                      Status: <span className="text-white font-semibold">{executionResult.transaction?.status}</span>
                    </p>
                  </div>
                </div>
                <StatusChip status={executionResult.transaction?.status || executionResult.decision} />
              </div>

              {/* Verified Badge */}
              {executionResult.verified && (
                <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-400 text-xs font-mono flex items-center space-x-2">
                  <Check className="w-4 h-4" />
                  <span>PAYMENT MANUALLY VERIFIED & EXECUTED IN SIMULATION</span>
                </div>
              )}

              {/* Conditional Action Buttons based on Decision */}
              {executionResult.transaction?.status === 'PENDING_VERIFICATION' && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded space-y-3">
                  <p className="text-xs font-mono text-amber-300">
                    Policy threshold or behavioral anomaly requires explicit user verification before execution.
                  </p>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={handleConfirmPayment}
                      disabled={executing}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-mono font-bold text-xs rounded transition-colors flex items-center space-x-1.5"
                    >
                      <Check className="w-4 h-4" />
                      <span>CONFIRM PAYMENT</span>
                    </button>
                    <button
                      onClick={handleRejectPayment}
                      disabled={executing}
                      className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-mono font-bold text-xs rounded transition-colors flex items-center space-x-1.5"
                    >
                      <X className="w-4 h-4" />
                      <span>REJECT</span>
                    </button>
                  </div>
                </div>
              )}

              {executionResult.decision === 'HOLD' && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded">
                  <p className="text-xs font-mono text-rose-300">
                    Execution BLOCKED. Payment violates non-negotiable security policy or matched an explicit BLOCK intent rule.
                  </p>
                </div>
              )}

              {/* Trace Action */}
              <div className="flex justify-between items-center pt-2">
                <span className="text-[11px] font-mono text-console-muted">
                  Recorded in immutable audit trace ledger
                </span>
                <button
                  onClick={handleOpenTrace}
                  className="px-3 py-1.5 bg-console-surface hover:bg-console-border border border-console-border rounded text-xs font-mono text-white flex items-center space-x-1.5 transition-colors"
                >
                  <span>VIEW FULL DECISION TRACE</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* Evaluated Rules Table */}
          {analysisResult?.rules_evaluated && (
            <div className="bg-console-card border border-console-border rounded overflow-hidden">
              <div 
                onClick={() => setRulesExpanded(!rulesExpanded)}
                className="p-3 bg-console-dark flex items-center justify-between cursor-pointer border-b border-console-border"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                    EVALUATED RULES & ENGINE CHECKS ({analysisResult.rules_evaluated.length})
                  </span>
                </div>
                <span className="text-xs font-mono text-console-muted">
                  {rulesExpanded ? 'COLLAPSE' : 'EXPAND'}
                </span>
              </div>

              {rulesExpanded && (
                <div className="divide-y divide-console-border">
                  {analysisResult.rules_evaluated.map((rule, idx) => (
                    <RuleRow
                      key={idx}
                      id={rule.id}
                      label={rule.label}
                      result={rule.result}
                      detail={rule.detail}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

        </div>

      </div>

      {/* Decision Trace Drawer Modal */}
      <DecisionTraceDrawer
        trace={selectedTrace}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

    </div>
  );
}
