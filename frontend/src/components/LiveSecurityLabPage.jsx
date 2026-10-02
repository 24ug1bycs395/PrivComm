import React, { useState } from 'react';
import {
  Activity,
  Server,
  Zap,
  ShieldAlert,
  ChevronRight,
  Radio
} from 'lucide-react';
import TelemetryDashboard from './TelemetryDashboard';
import TestbedTab from './TestbedTab';
import AttackSimulator from './AttackSimulator';

const SUB_TABS = [
  { id: 'dashboard', label: 'Live Dashboard',      icon: Activity },
  { id: 'attack',    label: 'Attack Simulation',   icon: ShieldAlert },
  { id: 'testbed',   label: 'strongSwan Testbed',  icon: Server },
];

export default function LiveSecurityLabPage({
  externalAnalysis,
  onNavigateToAnalyzer,
  onNavigateToOverview,
  onNavigateToAnalysis,
}) {
  const [activeSection, setActiveSection] = useState('dashboard');

  return (
    <div style={{ animation: 'fade-in 0.35s ease' }}>
      {/* ── Page Header ─── */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '5px 14px', borderRadius: '9999px',
          background: 'var(--accent-blue-dim)', border: '1px solid var(--border-default)',
          color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)',
          fontSize: '0.74rem', fontWeight: 600, marginBottom: '12px'
        }}>
          <Radio size={14} />
          <span>LIVE SECURITY LAB</span>
        </div>
        <h1 style={{
          fontSize: '1.85rem', fontWeight: 800,
          color: 'var(--text-primary)', letterSpacing: '-0.02em',
          marginBottom: '6px'
        }}>
          Live Security &amp; Testbed
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '680px' }}>
          Real-time telemetry monitoring, live tunnel analysis, and strongSwan IPsec testbed orchestration in a unified workspace.
        </p>
      </div>

      {/* ── Internal Section Tabs ─── */}
      <div className="live-section-tabs" style={{
        display: 'flex',
        gap: '4px',
        marginBottom: '24px',
        padding: '4px',
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md, 10px)',
        border: '1px solid var(--border-subtle)',
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        scrollbarWidth: 'none',
      }}>
        {SUB_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '7px',
                padding: '10px 18px',
                borderRadius: 'var(--radius-sm, 8px)',
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.82rem',
                fontWeight: isActive ? 700 : 500,
                whiteSpace: 'nowrap',
                transition: 'all 0.22s ease',
                background: isActive ? 'var(--accent-blue-dim)' : 'transparent',
                color: isActive ? 'var(--accent-blue)' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 0 12px rgba(59,130,246,0.08)' : 'none',
                flexShrink: 0,
              }}
            >
              <Icon size={15} strokeWidth={isActive ? 2.2 : 1.7} />
              <span>{tab.label}</span>
              {isActive && (
                <span style={{
                  display: 'inline-flex', alignItems: 'center', gap: '3px',
                  fontSize: '0.68rem', opacity: 0.7,
                }}>
                  <ChevronRight size={13} />
                </span>
              )}
            </button>
          );
        })}

        {/* Live indicator */}
        <div style={{
          marginLeft: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '0 14px',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--status-success)',
          fontWeight: 600,
          flexShrink: 0,
        }}>
          <span style={{
            width: '7px', height: '7px', borderRadius: '50%',
            background: 'var(--status-success-dot)',
            boxShadow: 'var(--status-success-shadow)',
            animation: 'pulse-glow 2s ease-in-out infinite',
          }} />
          <span>ACTIVE</span>
        </div>
      </div>

      {/* ── Section Content (display:none preserves state across tab switches) ─── */}
      <div style={{ display: activeSection === 'dashboard' ? 'block' : 'none' }}>
        <TelemetryDashboard
          externalAnalysis={externalAnalysis}
          onNavigateToTestbed={() => setActiveSection('testbed')}
          onNavigateToAnalyzer={onNavigateToAnalyzer}
          onNavigateToOverview={onNavigateToOverview}
        />
      </div>
      <div style={{ display: activeSection === 'attack' ? 'block' : 'none' }}>
        <AttackSimulator />
      </div>
      <div style={{ display: activeSection === 'testbed' ? 'block' : 'none' }}>
        <TestbedTab onNavigateToAnalysis={onNavigateToAnalysis} />
      </div>
    </div>
  );
}
