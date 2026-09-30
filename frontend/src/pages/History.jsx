import React, { useState, useEffect } from 'react';
import { 
  History as HistoryIcon, Search, Filter, RefreshCw, ArrowRight,
  CheckCircle, AlertTriangle, ShieldAlert, ArrowUpDown, Download
} from 'lucide-react';
import { api } from '../services/api';
import { StatusChip } from '../components/StatusChip';
import { DecisionTraceDrawer } from '../components/DecisionTraceDrawer';
import { formatRupees, formatDateTime } from '../utils/format';

export function History() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & search
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Trace drawer
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loadingTrace, setLoadingTrace] = useState(false);

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPayments();
      setPayments(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTrace = async (paymentId) => {
    try {
      setLoadingTrace(true);
      const trace = await api.getPaymentTrace(paymentId);
      setSelectedTrace(trace);
      setDrawerOpen(true);
    } catch (err) {
      alert('Unable to load trace: ' + err.message);
    } finally {
      setLoadingTrace(false);
    }
  };

  // Filtered payments list
  const filtered = payments.filter((tx) => {
    const matchesDecision = filterDecision === 'ALL' || tx.decision === filterDecision;
    const query = searchTerm.toLowerCase();
    const matchesSearch = 
      !searchTerm ||
      tx.recipient.toLowerCase().includes(query) ||
      tx.id.toLowerCase().includes(query) ||
      tx.category.toLowerCase().includes(query) ||
      (tx.purpose && tx.purpose.toLowerCase().includes(query));

    return matchesDecision && matchesSearch;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-console-border gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-white tracking-wide flex items-center space-x-2">
            <HistoryIcon className="w-5 h-5 text-blue-400" />
            <span>TRANSACTION HISTORY & DECISION LEDGER</span>
          </h1>
          <p className="text-xs text-console-muted font-mono mt-1">
            Immutable audit trail of all simulated payment executions and policy decisions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadPayments}
            className="px-3 py-1.5 bg-console-surface hover:bg-console-border border border-console-border rounded text-xs font-mono text-console-muted hover:text-white flex items-center space-x-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-console-card border border-console-border rounded p-4 flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Decision Filter Chips */}
        <div className="flex items-center space-x-2 overflow-x-auto w-full md:w-auto font-mono text-xs">
          <span className="text-console-muted text-[11px] uppercase mr-1">Filter:</span>
          {['ALL', 'ALLOW', 'VERIFY', 'HOLD'].map((dec) => (
            <button
              key={dec}
              onClick={() => setFilterDecision(dec)}
              className={`px-3 py-1.5 rounded transition-colors ${
                filterDecision === dec
                  ? 'bg-blue-600 text-white font-bold'
                  : 'bg-console-dark hover:bg-console-surface text-console-muted hover:text-white border border-console-border/60'
              }`}
            >
              {dec}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-console-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search recipient, ID, category..."
            className="w-full bg-console-dark border border-console-border rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-console-muted focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>
      </div>

      {/* 9-Column Transaction Ledger Table */}
      <div className="bg-console-card border border-console-border rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="bg-console-dark border-b border-console-border text-console-muted text-[11px] uppercase">
                <th className="p-3">Time</th>
                <th className="p-3">ID</th>
                <th className="p-3">Recipient</th>
                <th className="p-3">Category</th>
                <th className="p-3 text-right">Amount</th>
                <th className="p-3 text-center">Decision</th>
                <th className="p-3">Action / Lifecycle</th>
                <th className="p-3">Purpose / Notes</th>
                <th className="p-3 text-right">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-console-border">
              {loading && payments.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-8 text-center text-console-muted">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-400" />
                    <span>Loading transaction ledger...</span>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-8 text-center text-console-muted">
                    No transactions match current filters.
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => (
                  <tr 
                    key={tx.id}
                    onClick={() => handleOpenTrace(tx.id)}
                    className="hover:bg-console-surface/60 transition-colors cursor-pointer group"
                  >
                    <td className="p-3 text-console-muted whitespace-nowrap text-[11px]">
                      {formatDateTime(tx.timestamp || tx.created_at)}
                    </td>
                    <td className="p-3 font-bold text-white whitespace-nowrap">
                      {tx.id}
                    </td>
                    <td className="p-3 font-semibold text-white whitespace-nowrap">
                      {tx.recipient}
                    </td>
                    <td className="p-3 text-console-muted whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded bg-console-dark border border-console-border/40 text-[10px]">
                        {tx.category}
                      </span>
                    </td>
                    <td className="p-3 text-right font-bold text-white whitespace-nowrap">
                      {formatRupees(tx.amount)}
                    </td>
                    <td className="p-3 text-center whitespace-nowrap">
                      <StatusChip status={tx.decision} size="sm" />
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      <StatusChip status={tx.status} size="sm" />
                    </td>
                    <td className="p-3 text-console-muted text-[11px] max-w-xs truncate">
                      {tx.purpose || 'Direct payment'}
                    </td>
                    <td className="p-3 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenTrace(tx.id);
                        }}
                        className="px-2 py-1 bg-console-surface group-hover:bg-blue-600 text-console-muted group-hover:text-white rounded border border-console-border text-[10px] flex items-center space-x-1 ml-auto transition-colors"
                      >
                        <span>VIEW TRACE</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Ledger Summary Footer */}
        <div className="p-3 bg-console-dark border-t border-console-border flex justify-between items-center text-xs font-mono text-console-muted">
          <span>Showing {filtered.length} of {payments.length} simulated transactions</span>
          <span>Zero real money processed • Simulated ledger</span>
        </div>
      </div>

      {/* Decision Trace Drawer */}
      <DecisionTraceDrawer
        trace={selectedTrace}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

    </div>
  );
}
