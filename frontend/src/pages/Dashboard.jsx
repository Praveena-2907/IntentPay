import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { formatINR, formatTimestamp } from '../utils/format';
import { KpiTile } from '../components/KpiTile';
import { StatusChip } from '../components/StatusChip';
import { ToastAlert } from '../components/ToastAlert';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { ArrowUpRight, Shield, Brain, ArrowRight, RefreshCw, AlertCircle } from 'lucide-react';

export function Dashboard({ onSelectTrace }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="text-xs font-mono text-console-muted">LOADING SYSTEM TELEMETRY...</div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-console-surface border border-console-border animate-pulse rounded-sm" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ToastAlert
          type="error"
          title="Telemetry Error"
          message={error}
          actionButton={
            <button
              onClick={fetchDashboardData}
              className="px-2.5 py-1 text-xs font-mono bg-console-hold text-white rounded-sm hover:opacity-90"
            >
              RETRY
            </button>
          }
        />
      </div>
    );
  }

  const { kpis, spending_by_category, decision_distribution, recent_decisions, active_intents, active_policies, pending_suggestions } = data || {};

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Title & Scope */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-console-border">
        <div>
          <h1 className="text-lg font-mono font-bold text-console-text tracking-wide">
            DECISION & POLICY TELEMETRY
          </h1>
          <p className="text-xs font-sans text-console-muted mt-0.5">
            Operational overview of digital payment intents, PayDNA rules, and simulated execution outcomes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/simulator"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-semibold bg-console-accent text-white rounded-sm hover:bg-blue-600 transition-colors"
          >
            <span>LAUNCH SIMULATOR</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Pending Suggestion Alert */}
      {pending_suggestions && pending_suggestions.length > 0 && (
        <div className="space-y-2">
          {pending_suggestions.map((sug) => (
            <ToastAlert
              key={sug.id}
              type="warning"
              title="RECURRING PAYMENT PATTERN DETECTED"
              message={`${sug.reason} Would you like to create an automated intent for ${sug.recipient}?`}
              actionButton={
                <Link
                  to="/intents"
                  className="px-2.5 py-1 text-xs font-mono font-semibold bg-console-verify text-black rounded-sm hover:opacity-90"
                >
                  CREATE INTENT
                </Link>
              }
            />
          ))}
        </div>
      )}

      {/* 6 KPI Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiTile
          label="ACTIVE INTENTS"
          value={kpis?.intents ?? 4}
          delta="Automated rules"
          status="accent"
        />
        <KpiTile
          label="PAYDNA POLICIES"
          value={kpis?.policies ?? 5}
          delta="Active security controls"
          status="default"
        />
        <KpiTile
          label="EVALUATED"
          value={kpis?.evaluated ?? 27}
          delta={`Vol: ${formatINR(kpis?.simulated_volume || 0)}`}
          status="default"
        />
        <KpiTile
          label="APPROVED"
          value={kpis?.approved ?? 21}
          delta="Passed intent & policy"
          status="allow"
        />
        <KpiTile
          label="VERIFY TRIGGERS"
          value={kpis?.verify ?? 5}
          delta="Manual review required"
          status="verify"
        />
        <KpiTile
          label="HELD / BLOCKED"
          value={kpis?.held ?? 1}
          delta="Policy / ceiling violation"
          status="hold"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Category Spending Bar Chart (2 cols) */}
        <div className="lg:col-span-2 bg-console-surface border border-console-border p-4 rounded-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
              SIMULATED SPENDING BY CATEGORY (INR)
            </span>
            <span className="text-[10px] font-mono text-console-muted">EXECUTED_SIMULATED</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={spending_by_category || []} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis
                  dataKey="category"
                  stroke="#8B98A5"
                  fontSize={11}
                  tickLine={false}
                  fontFamily="Inter"
                />
                <YAxis
                  stroke="#8B98A5"
                  fontSize={10}
                  tickLine={false}
                  fontFamily="JetBrains Mono"
                  tickFormatter={(val) => `₹${val / 1000}k`}
                />
                <Tooltip
                  cursor={{ fill: '#161F29' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-console-surface border border-console-border p-2 rounded-sm shadow-md font-mono text-xs">
                          <div className="text-console-muted">{d.category}</div>
                          <div className="text-console-text font-bold mt-0.5">{formatINR(d.amount)}</div>
                          <div className="text-[10px] text-console-muted">{d.count} transactions</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="amount" fill="#3B82F6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Decision Distribution Donut (1 col) */}
        <div className="bg-console-surface border border-console-border p-4 rounded-sm flex flex-col">
          <div className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold mb-2">
            DECISION DISTRIBUTION
          </div>

          <div className="h-44 w-full relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={decision_distribution || []}
                  innerRadius={45}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="count"
                >
                  {(decision_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#111820" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-console-surface border border-console-border p-2 rounded-sm font-mono text-xs">
                          <span className="font-bold" style={{ color: d.color }}>{d.decision}</span>: {d.count} ({Math.round(d.count / (kpis?.evaluated || 1) * 100)}%)
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute text-center pointer-events-none">
              <div className="text-lg font-mono font-bold text-console-text">{kpis?.evaluated ?? 27}</div>
              <div className="text-[9px] font-mono uppercase text-console-muted">TOTAL</div>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-auto space-y-1.5 pt-2 border-t border-console-border/60">
            {(decision_distribution || []).map((d) => (
              <div key={d.decision} className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-console-text font-medium">{d.decision}</span>
                </div>
                <div className="text-console-muted">
                  {d.count} <span className="text-[10px]">({Math.round((d.count / (kpis?.evaluated || 1)) * 100)}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Decisions Table */}
      <div className="bg-console-surface border border-console-border rounded-sm">
        <div className="p-3.5 border-b border-console-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
              RECENT DECISIONS LEDGER
            </span>
          </div>
          <Link
            to="/history"
            className="text-xs font-mono text-console-accent hover:underline flex items-center gap-1"
          >
            <span>FULL HISTORY</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-console-surface-2 text-console-muted uppercase text-[10px] tracking-wider border-b border-console-border">
              <tr>
                <th className="py-2.5 px-3">TX ID</th>
                <th className="py-2.5 px-3">RECIPIENT</th>
                <th className="py-2.5 px-3">CATEGORY</th>
                <th className="py-2.5 px-3">AMOUNT</th>
                <th className="py-2.5 px-3">DECISION</th>
                <th className="py-2.5 px-3 hidden md:table-cell">PRIMARY REASON</th>
                <th className="py-2.5 px-3">TIMESTAMP</th>
                <th className="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-console-border/60">
              {(recent_decisions || []).map((tx) => (
                <tr
                  key={tx.id}
                  className="hover:bg-console-surface-2/60 transition-colors h-9"
                >
                  <td className="py-2 px-3 font-semibold text-console-accent">{tx.id}</td>
                  <td className="py-2 px-3 text-console-text font-medium">{tx.recipient}</td>
                  <td className="py-2 px-3 text-console-muted">{tx.category}</td>
                  <td className="py-2 px-3 font-bold text-console-text">{formatINR(tx.amount)}</td>
                  <td className="py-2 px-3">
                    <StatusChip status={tx.decision} size="sm" />
                  </td>
                  <td className="py-2 px-3 text-console-muted text-[11px] truncate max-w-xs hidden md:table-cell">
                    {tx.reason}
                  </td>
                  <td className="py-2 px-3 text-console-muted text-[11px]">
                    {formatTimestamp(tx.timestamp)}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <button
                      onClick={() => onSelectTrace && onSelectTrace(tx.id)}
                      className="px-2 py-0.5 text-[10px] font-mono text-console-muted hover:text-console-text bg-console-surface-2 border border-console-border hover:border-console-border/80 rounded-sm"
                    >
                      TRACE
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Rules Grid (Intents & Policies Summary) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Active Intents */}
        <div className="bg-console-surface border border-console-border p-4 rounded-sm">
          <div className="flex items-center justify-between pb-3 border-b border-console-border mb-3">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-console-accent" />
              <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
                ACTIVE PAYMENT INTENTS ({active_intents?.length || 0})
              </span>
            </div>
            <Link to="/intents" className="text-xs font-mono text-console-accent hover:underline">
              MANAGE
            </Link>
          </div>

          <div className="space-y-2">
            {(active_intents || []).map((intent) => (
              <div
                key={intent.id}
                className="flex items-center justify-between p-2.5 bg-console-surface-2 border border-console-border rounded-sm text-xs font-mono"
              >
                <div>
                  <div className="font-semibold text-console-text">
                    <span className="text-console-muted mr-1.5">{intent.id}</span>
                    {intent.purpose}
                  </div>
                  <div className="text-[11px] text-console-muted mt-0.5">
                    Target: {intent.recipient || 'Any'} [{intent.category}] · {intent.frequency}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-console-accent">
                    {intent.amount ? formatINR(intent.amount) : 'Dynamic'}
                  </div>
                  <span className="text-[10px] text-console-allow">AUTO-PAY</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Active Policies */}
        <div className="bg-console-surface border border-console-border p-4 rounded-sm">
          <div className="flex items-center justify-between pb-3 border-b border-console-border mb-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-console-verify" />
              <span className="text-[11px] font-mono uppercase tracking-wider text-console-muted font-semibold">
                ACTIVE PAYDNA POLICIES ({active_policies?.length || 0})
              </span>
            </div>
            <Link to="/policies" className="text-xs font-mono text-console-accent hover:underline">
              MANAGE
            </Link>
          </div>

          <div className="space-y-2">
            {(active_policies || []).map((pol) => (
              <div
                key={pol.id}
                className="flex items-center justify-between p-2.5 bg-console-surface-2 border border-console-border rounded-sm text-xs font-mono"
              >
                <div>
                  <div className="font-semibold text-console-text">
                    <span className="text-console-muted mr-1.5">{pol.id}</span>
                    {pol.description}
                  </div>
                  <div className="text-[11px] text-console-muted mt-0.5">
                    Type: {pol.policy_type}
                  </div>
                </div>
                <div className="text-right">
                  <StatusChip status={pol.action} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
