import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { api } from './services/api';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Simulator } from './pages/Simulator';
import { Intents } from './pages/Intents';
import { Policies } from './pages/Policies';
import { Constitution } from './pages/Constitution';
import { History } from './pages/History';
import { WhatIf } from './pages/WhatIf';
import { Analytics } from './pages/Analytics';
import { DecisionTraceDrawer } from './components/DecisionTraceDrawer';

export default function App() {
  const [user, setUser] = useState(null);
  const [isFallback, setIsFallback] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [traceDrawerOpen, setTraceDrawerOpen] = useState(false);

  const initData = async () => {
    try {
      const health = await api.getHealth();
      setIsFallback(!health.ai_configured);

      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch (e) {
      console.warn('System initialization warning:', e);
      setIsFallback(true);
    }
  };

  useEffect(() => {
    initData();
  }, []);

  const handleResetData = async () => {
    if (!window.confirm('Reset database back to initial seed data?')) return;
    try {
      setIsResetting(true);
      await api.resetDemoData();
      await initData();
      window.location.reload();
    } catch (err) {
      alert('Reset failed: ' + err.message);
    } finally {
      setIsResetting(false);
    }
  };

  const handleSelectTrace = async (traceOrTxId) => {
    try {
      if (typeof traceOrTxId === 'object' && traceOrTxId !== null) {
        setSelectedTrace(traceOrTxId);
        setTraceDrawerOpen(true);
      } else {
        // Assume it is transaction_id or trace_id
        const txId = String(traceOrTxId).startsWith('TR-') ? `TX-${traceOrTxId.substring(3)}` : traceOrTxId;
        const traceData = await api.getPaymentTrace(txId);
        setSelectedTrace(traceData);
        setTraceDrawerOpen(true);
      }
    } catch (err) {
      console.error('Failed to load trace:', err);
    }
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-console-bg text-console-text flex flex-col font-sans selection:bg-console-accent/25">
        {/* Persistent Operational Top Bar */}
        <TopBar
          user={user}
          isFallback={isFallback}
          onResetData={handleResetData}
          isResetting={isResetting}
        />

        {/* Main Console Workspace */}
        <div className="flex-1 flex overflow-hidden">
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
          />

          <main className="flex-1 overflow-y-auto bg-console-bg">
            <Routes>
              <Route path="/" element={<Dashboard onSelectTrace={handleSelectTrace} />} />
              <Route path="/simulator" element={<Simulator />} />
              <Route path="/intents" element={<Intents />} />
              <Route path="/policies" element={<Policies />} />
              <Route path="/constitution" element={<Constitution />} />
              <Route path="/history" element={<History />} />
              <Route path="/what-if" element={<WhatIf />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </main>
        </div>

        {/* Global Trace Drawer */}
        <DecisionTraceDrawer
          trace={selectedTrace}
          isOpen={traceDrawerOpen}
          onClose={() => setTraceDrawerOpen(false)}
        />
      </div>
    </BrowserRouter>
  );
}
