import React from 'react';

export function PlaceholderPage({ title, description }) {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="border-b border-console-border pb-3">
        <h1 className="text-lg font-mono font-bold text-console-text">{title}</h1>
        <p className="text-xs font-sans text-console-muted mt-1">{description}</p>
      </div>
      <div className="bg-console-surface border border-console-border p-8 text-center text-xs font-mono text-console-muted rounded-sm">
        MODULE READY · TELEMETRY ACTIVE
      </div>
    </div>
  );
}
