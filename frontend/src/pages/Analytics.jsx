import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Activity, Shield, TrendingUp, Sparkles, Check, 
  RefreshCw, DollarSign, Calendar, Clock, AlertTriangle, ArrowRight
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, AreaChart, Area } from 'recharts';
import { api } from '../services/api';
import { StatusChip } from '../components/StatusChip';
import { formatRupees } from '../utils/format';

export function Analytics() {
  const [spending, setSpending] = useState(null);
  const [behavior, setBehavior] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creatingIntentId, setCreatingIntentId] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [spendData, behData, suggData] = await Promise.all([
        api.getSpendingAnalytics(),
        api.getBehaviorAnalytics(),
        api.getSuggestions()
      ]);
      setSpending(spendData);
      setBehavior(behData);
      setSuggestions(suggData || []);
    } catch (err) {
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertSuggestion = async (sugg) => {
    try {
      setCreatingIntentId(sugg.id);
      await api.createIntent({
        purpose: `${sugg.recipient} Membership`,
        recipient: sugg.recipient,
        category: sugg.category,
        amount: sugg.suggested_amount,
        max_amount: null,
        frequency: sugg.frequency,
        day_of_month: sugg.day_of_month || 5,
        action: 'AUTO_PAY',
        conditions: [{ field: 'amount', operator: '==', value: sugg.suggested_amount }]
      });
      await api.dismissSuggestion(sugg.id);
      setSuccessMsg(`Intent created for ${sugg.recipient}!`);
      setTimeout(() => setSuccessMsg(null), 3000);
      await loadData();
    } catch (err) {
      alert('Failed to convert suggestion: ' + err.message);
    } finally {
      setCreatingIntentId(null);
    }
  };

  const stats = behavior?.stats || {};
  const catBreakdown = spending?.category_breakdown || [];
  const monthlyTrend = spending?.monthly_trend || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-console-border gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white tracking-wide flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <span>ANALYTICS & BEHAVIORAL HEURISTICS</span>
          </h1>
          <p className="text-xs text-console-muted font-mono mt-1">
            Aggregated historical spending telemetry and empirical anomaly baseline metrics.
          </p>
        </div>

        <button
          onClick={loadData}
          className="self-start md:self-auto px-3 py-1.5 bg-console-surface hover:bg-console-border border border-console-border rounded text-xs font-mono text-console-muted hover:text-white flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs rounded flex items-center space-x-2 animate-fade-in">
          <Check className="w-4 h-4" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Recurring Suggestions (F16) */}
      {suggestions.length > 0 && (
        <div className="bg-blue-950/20 border border-blue-500/40 rounded p-4 space-y-3">
          <div className="flex items-center space-x-2 text-blue-400 font-mono text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>RECURRING PATTERN DETECTED (F16 SMART SUGGESTION)</span>
          </div>
          
          <div className="space-y-2">
            {suggestions.map((s) => (
              <div key={s.id} className="p-3 bg-console-dark rounded border border-console-border flex flex-col md:flex-row justify-between md:items-center gap-3">
                <div className="font-mono text-xs space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-bold">{s.recipient}</span>
                    <span className="text-console-muted">({s.category})</span>
                    <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-bold">
                      {s.frequency}
                    </span>
                  </div>
                  <p className="text-console-muted text-[11px]">{s.reason}</p>
                </div>

                <button
                  onClick={() => handleConvertSuggestion(s)}
                  disabled={creatingIntentId === s.id}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold rounded transition-colors flex items-center space-x-1.5 self-start md:self-auto"
                >
                  {creatingIntentId === s.id ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>CREATING INTENT...</span>
                    </>
                  ) : (
                    <>
                      <span>CREATE INTENT FROM THIS</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Behavioral Baseline KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-console-card border border-console-border rounded p-4 font-mono">
          <span className="block text-[11px] text-console-muted uppercase">Average Outlay</span>
          <span className="text-lg font-bold text-white mt-1 block">
            {formatRupees(spending?.average_transaction || 0)}
          </span>
          <span className="text-[10px] text-console-muted mt-1 block">Per simulated transaction</span>
        </div>

        <div className="bg-console-card border border-console-border rounded p-4 font-mono">
          <span className="block text-[11px] text-console-muted uppercase">Max Executed Spend</span>
          <span className="text-lg font-bold text-white mt-1 block">
            {formatRupees(stats.max_amount || 0)}
          </span>
          <span className="text-[10px] text-console-muted mt-1 block">Upper baseline ceiling</span>
        </div>

        <div className="bg-console-card border border-console-border rounded p-4 font-mono">
          <span className="block text-[11px] text-console-muted uppercase">Active Hour Band</span>
          <span className="text-lg font-bold text-emerald-400 mt-1 block">
            {behavior?.typical_hour_band || '08:00 – 22:00'}
          </span>
          <span className="text-[10px] text-console-muted mt-1 block">Standard operating window</span>
        </div>

        <div className="bg-console-card border border-console-border rounded p-4 font-mono">
          <span className="block text-[11px] text-console-muted uppercase">Total Executed Volume</span>
          <span className="text-lg font-bold text-white mt-1 block">
            {formatRupees(spending?.total_spend || 0)}
          </span>
          <span className="text-[10px] text-console-muted mt-1 block">{spending?.transaction_count || 0} transactions</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Category Breakdown Bar Chart */}
        <div className="bg-console-card border border-console-border rounded p-4 space-y-3">
          <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2 border-b border-console-border pb-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>CATEGORY SPEND BREAKDOWN</span>
          </h2>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={catBreakdown} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <XAxis type="number" stroke="#6B7280" tickFormatter={(v) => `₹${v/1000}k`} />
                <YAxis dataKey="category" type="category" stroke="#9CA3AF" width={80} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [formatRupees(val), 'Total Spend']}
                  contentStyle={{ backgroundColor: '#111820', border: '1px solid #1F2A37', borderRadius: '4px' }}
                />
                <Bar dataKey="amount" fill="#3B82F6" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Behavioral Anomaly Rules & Thresholds */}
        <div className="bg-console-card border border-console-border rounded p-4 space-y-3">
          <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2 border-b border-console-border pb-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>BEHAVIORAL ANOMALY HEURISTIC THRESHOLDS</span>
          </h2>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-2.5 bg-console-dark rounded border border-console-border/40 flex justify-between items-center">
              <div>
                <span className="text-white font-bold block">HIGH_AMOUNT Trigger</span>
                <span className="text-console-muted text-[11px]">MEDIUM at ≥ 2.5× baseline; HIGH at ≥ 5.0× baseline</span>
              </div>
              <StatusChip status="MEDIUM" size="sm" />
            </div>

            <div className="p-2.5 bg-console-dark rounded border border-console-border/40 flex justify-between items-center">
              <div>
                <span className="text-white font-bold block">NEW_RECIPIENT Trigger</span>
                <span className="text-console-muted text-[11px]">Recipient not present in verified directory</span>
              </div>
              <StatusChip status="MEDIUM" size="sm" />
            </div>

            <div className="p-2.5 bg-console-dark rounded border border-console-border/40 flex justify-between items-center">
              <div>
                <span className="text-white font-bold block">UNUSUAL_TIME Trigger</span>
                <span className="text-console-muted text-[11px]">Execution outside 08:00–22:00 typical band</span>
              </div>
              <StatusChip status="MEDIUM" size="sm" />
            </div>

            <div className="p-2.5 bg-console-dark rounded border border-console-border/40 flex justify-between items-center">
              <div>
                <span className="text-white font-bold block">FREQUENCY_SPIKE Trigger</span>
                <span className="text-console-muted text-[11px]">≥ 4 payments executed in trailing 24h</span>
              </div>
              <StatusChip status="MEDIUM" size="sm" />
            </div>

            <div className="p-2.5 bg-console-dark rounded border border-console-border/40 flex justify-between items-center">
              <div>
                <span className="text-white font-bold block">CATEGORY_SPIKE Trigger</span>
                <span className="text-console-muted text-[11px]">Trailing 7d category total + amount ≥ 2× weekly avg</span>
              </div>
              <StatusChip status="MEDIUM" size="sm" />
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
