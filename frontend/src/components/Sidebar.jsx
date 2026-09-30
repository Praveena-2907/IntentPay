import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PlayCircle,
  Brain,
  Shield,
  BookOpen,
  History,
  Calculator,
  BarChart3,
  Menu,
  X
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'DASHBOARD', icon: LayoutDashboard },
  { path: '/simulator', label: 'SIMULATOR', icon: PlayCircle },
  { path: '/intents', label: 'PAYMENT INTENTS', icon: Brain },
  { path: '/policies', label: 'PAYDNA POLICIES', icon: Shield },
  { path: '/constitution', label: 'CONSTITUTION', icon: BookOpen },
  { path: '/history', label: 'TRANSACTION HISTORY', icon: History },
  { path: '/what-if', label: 'WHAT-IF SIMULATOR', icon: Calculator },
  { path: '/analytics', label: 'ANALYTICS', icon: BarChart3 },
];

export function Sidebar({ isOpen, onToggle }) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onToggle}
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 w-64 bg-console-surface border-r border-console-border flex flex-col z-40 transform transition-transform duration-150 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Mobile Header in Drawer */}
        <div className="flex md:hidden items-center justify-between p-4 border-b border-console-border">
          <span className="font-mono text-xs font-bold text-console-text">NAVIGATION</span>
          <button onClick={onToggle} className="text-console-muted p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Console Nav Label */}
        <div className="hidden md:block px-4 pt-4 pb-2">
          <span className="text-[10px] font-mono uppercase tracking-widest text-console-muted font-semibold">
            CONTROL CONSOLE
          </span>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth < 768) onToggle();
                }}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 text-xs font-mono rounded-sm transition-colors ${
                    isActive
                      ? 'bg-console-surface-2 text-console-text border-l-2 border-console-accent font-semibold'
                      : 'text-console-muted hover:text-console-text hover:bg-console-surface-2/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer Meta */}
        <div className="p-3 border-t border-console-border text-[10px] font-mono text-console-muted/70">
          <div>INTENTPAY CONSOLE v2.0</div>
          <div>STATUS: OPERATIONAL</div>
        </div>
      </aside>
    </>
  );
}
