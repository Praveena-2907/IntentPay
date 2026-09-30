import React, { useState, useEffect } from 'react';
import { 
  Sliders, ArrowRight, DollarSign, TrendingDown, AlertTriangle, 
  CheckCircle, ShieldAlert, RefreshCw, Calculator
} from 'lucide-react';
import { api } from '../services/api';
import { StatusChip } from '../components/StatusChip';
import { formatRupees } from '../utils/format';

export function WhatIf() {
  const [paymentAmount, setPaymentAmount] = useState(25000);
  const [monthlyIncome, setMonthlyIncome] = useState(50000);
  const [monthlyExpense, setMonthlyExpense] = useState(15500);
  const [loanEmi, setLoanEmi] = useState(5000);
  const [recurringDelta, setRecurringDelta] = useState(0);

  const [loading, setLoading] = useState(false);
  const [scenarioResult, setScenarioResult] = useState(null);

  useEffect(() => {
    runScenario();
  }, [paymentAmount, monthlyIncome, monthlyExpense, loanEmi, recurringDelta]);

  const runScenario = async () => {
    try {
      setLoading(true);
      const res = await api.simulateWhatIf({
        payment_amount: Number(paymentAmount) || 0,
        monthly_income: Number(monthlyIncome) || 50000,
        monthly_expense: Number(monthlyExpense) || 15500,
        loan_amount: Number(loanEmi) || 0,
        recurring_expense_delta: Number(recurringDelta) || 0
      });
      setScenarioResult(res);
    } catch (err) {
      console.error('What-if calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const before = scenarioResult?.before || {};
  const after = scenarioResult?.after || {};
  const delta = scenarioResult?.delta || {};

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-console-border gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white tracking-wide flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            <span>WHAT-IF CASH-FLOW SCENARIO SIMULATOR</span>
          </h1>
          <p className="text-xs text-console-muted font-mono mt-1">
            Simulate the compound impact of large discretionary payments, EMIs, and recurring budget adjustments.
          </p>
        </div>

        <button
          onClick={() => {
            setPaymentAmount(25000);
            setLoanEmi(5000);
            setRecurringDelta(0);
          }}
          className="self-start md:self-auto px-3 py-1.5 bg-console-surface hover:bg-console-border border border-console-border rounded text-xs font-mono text-console-muted hover:text-white flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>RESET DEFAULTS</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left: Interactive Sliders & Inputs (5 cols) */}
        <div className="lg:col-span-5 bg-console-card border border-console-border rounded p-4 space-y-5">
          <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2 border-b border-console-border pb-2">
            <Calculator className="w-4 h-4 text-blue-400" />
            <span>SCENARIO PARAMETERS</span>
          </h2>

          <div className="space-y-4 font-mono text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-console-muted uppercase text-[11px]">Hypothetical Payment Outlay:</label>
                <span className="text-white font-bold">{formatRupees(paymentAmount)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="100000"
                step="1000"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(Number(e.target.value))}
                className="w-full accent-blue-500 bg-console-dark cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="text-console-muted uppercase text-[11px]">Monthly Loan / EMI Outflow:</label>
                <span className="text-white font-bold">{formatRupees(loanEmi)}/mo</span>
              </div>
              <input
                type="range"
                min="0"
                max="30000"
                step="500"
                value={loanEmi}
                onChange={(e) => setLoanEmi(Number(e.target.value))}
                className="w-full accent-blue-500 bg-console-dark cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="text-console-muted uppercase text-[11px]">Recurring Expense Shift (Δ):</label>
                <span className={`font-bold ${recurringDelta > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {recurringDelta > 0 ? `+${formatRupees(recurringDelta)}` : formatRupees(recurringDelta)}/mo
                </span>
              </div>
              <input
                type="range"
                min="-10000"
                max="10000"
                step="500"
                value={recurringDelta}
                onChange={(e) => setRecurringDelta(Number(e.target.value))}
                className="w-full accent-blue-500 bg-console-dark cursor-pointer"
              />
            </div>

            <div className="pt-2 border-t border-console-border space-y-3">
              <div>
                <label className="block text-console-muted mb-1 text-[11px] uppercase">Monthly Income Baseline:</label>
                <input
                  type="number"
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                  className="w-full bg-console-dark border border-console-border rounded px-3 py-1.5 text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-console-muted mb-1 text-[11px] uppercase">Monthly Obligations Baseline:</label>
                <input
                  type="number"
                  value={monthlyExpense}
                  onChange={(e) => setMonthlyExpense(Number(e.target.value))}
                  className="w-full bg-console-dark border border-console-border rounded px-3 py-1.5 text-white font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Comparative Analysis & Runway (7 cols) */}
        <div className="lg:col-span-7 space-y-6">

          {/* Scenario Outcome Banner */}
          {after.impact_level && (
            <div className={`p-4 rounded border font-mono ${
              after.impact_level === 'NEGATIVE_BALANCE' || after.impact_level === 'CRITICAL_LOW'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                : after.impact_level === 'DEFICIT' || after.impact_level === 'SIGNIFICANT'
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {after.impact_level === 'NEGATIVE_BALANCE' ? (
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                  ) : after.impact_level === 'SIGNIFICANT' || after.impact_level === 'DEFICIT' ? (
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                  )}
                  <span className="font-bold text-xs uppercase tracking-wide">
                    SCENARIO RISK CLASSIFICATION: {after.impact_level}
                  </span>
                </div>
                <StatusChip status={after.impact_level} size="sm" />
              </div>
            </div>
          )}

          {/* Before vs After Comparison Table */}
          <div className="bg-console-card border border-console-border rounded overflow-hidden">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="bg-console-dark border-b border-console-border text-console-muted text-[11px] uppercase">
                  <th className="p-3">Financial Metric</th>
                  <th className="p-3 text-right">Baseline (Before)</th>
                  <th className="p-3 text-right">Scenario (After)</th>
                  <th className="p-3 text-right">Net Shift (Δ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-border">
                <tr>
                  <td className="p-3 text-white font-medium">Monthly Inflow</td>
                  <td className="p-3 text-right text-console-muted">{formatRupees(before.monthly_income)}</td>
                  <td className="p-3 text-right text-white font-bold">{formatRupees(after.monthly_income)}</td>
                  <td className="p-3 text-right text-console-muted">₹0</td>
                </tr>
                <tr>
                  <td className="p-3 text-white font-medium">Monthly Obligations</td>
                  <td className="p-3 text-right text-console-muted">{formatRupees(before.monthly_expenses)}</td>
                  <td className="p-3 text-right text-amber-400 font-bold">{formatRupees(after.monthly_expenses)}</td>
                  <td className="p-3 text-right text-amber-400 font-bold">
                    +{(after.monthly_expenses - before.monthly_expenses) > 0 ? formatRupees(after.monthly_expenses - before.monthly_expenses) : '₹0'}
                  </td>
                </tr>
                <tr>
                  <td className="p-3 text-white font-medium">Net Monthly Cash Flow</td>
                  <td className="p-3 text-right text-console-muted">{formatRupees(before.net_monthly_cash_flow)}</td>
                  <td className={`p-3 text-right font-bold ${after.net_monthly_cash_flow < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {formatRupees(after.net_monthly_cash_flow)}
                  </td>
                  <td className={`p-3 text-right font-bold ${delta.net_monthly_cash_flow < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {delta.net_monthly_cash_flow > 0 ? `+${formatRupees(delta.net_monthly_cash_flow)}` : formatRupees(delta.net_monthly_cash_flow)}
                  </td>
                </tr>
                <tr className="bg-console-dark/40">
                  <td className="p-3 text-white font-bold">Projected Month-End Balance</td>
                  <td className="p-3 text-right text-console-muted font-bold">{formatRupees(before.projected_month_end_balance)}</td>
                  <td className={`p-3 text-right font-bold ${after.projected_month_end_balance < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {formatRupees(after.projected_month_end_balance)}
                  </td>
                  <td className={`p-3 text-right font-bold ${delta.projected_month_end_balance < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {formatRupees(delta.projected_month_end_balance)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Contextual Insights */}
          <div className="bg-console-card border border-console-border rounded p-4 font-mono text-xs space-y-2">
            <span className="text-[11px] text-console-muted uppercase block font-semibold">
              AUTOMATED FINANCIAL ADVISORY NOTES:
            </span>
            <ul className="space-y-1.5 list-disc list-inside text-console-muted">
              <li>One-time simulated outlay of {formatRupees(paymentAmount)} immediately impacts available liquid reserves.</li>
              {loanEmi > 0 && <li>Recurring EMI of {formatRupees(loanEmi)}/mo reduces monthly disposable income by {((loanEmi / monthlyIncome) * 100).toFixed(1)}%.</li>}
              {after.projected_month_end_balance < 0 ? (
                <li className="text-rose-400 font-bold">WARNING: Scenario pushes account balance into negative liquidity territory.</li>
              ) : (
                <li className="text-emerald-400">Account maintains positive cushion following simulated payment execution.</li>
              )}
            </ul>
          </div>

        </div>

      </div>

    </div>
  );
}
