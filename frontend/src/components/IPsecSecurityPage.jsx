import React, { useState } from 'react';
import {
  Activity,
  Shield,
  FileCheck,
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import AnalyzerWorkspace from './AnalyzerWorkspace';
import ThreatMatrixTab from './ThreatMatrixTab';
import ComplianceTab from './ComplianceTab';

const SUB_TABS = [
  { id: 'analyzer',   label: 'PCAP / Packet Analysis',   icon: Activity },
  { id: 'threats',    label: 'Threat & Risk Matrix',      icon: AlertTriangle },
  { id: 'compliance', label: 'Security & Compliance',     icon: FileCheck },
];

export default function IPsecSecurityPage({ externalAnalysis }) {
  const [activeSection, setActiveSection] = useState('analyzer');

  return (
    <div style={{ animation: 'fade-in 0.35s ease' }}>
      {/* ── Page Header ─── */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '5px 14px', borderRadius: '9999px',
          background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)',
          color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)',
          fontSize: '0.74rem', fontWeight: 600, marginBottom: '12px'
        }}>
          <Shield size={14} />
          <span>IPSEC SECURITY CENTER</span>
        </div>
        <h1 style={{
          fontSize: '1.85rem', fontWeight: 800,
          color: 'var(--text-primary)', letterSpacing: '-0.02em',
          marginBottom: '6px'
        }}>
          IPsec Security
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '680px' }}>
          Unified PCAP analysis, protocol assessment, threat modeling, and compliance verification for IPsec VPN infrastructure.
        </p>
      </div>

      {/* ── Internal Section Tabs ─── */}
      <div className="ipsec-section-tabs" style={{
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
                background: isActive ? 'var(--accent-cyan-dim)' : 'transparent',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 0 12px rgba(56,189,248,0.08)' : 'none',
                flexShrink: 0,
              }}
            >
              <Icon size={15} strokeWidth={isActive ? 2.2 : 1.7} />
              <span>{tab.label}</span>
              {isActive && <ChevronRight size={13} style={{ opacity: 0.5 }} />}
            </button>
          );
        })}
      </div>

      {/* ── Section Content (conditionally rendered to preserve state) ─── */}
      <div style={{ display: activeSection === 'analyzer' ? 'block' : 'none' }}>
        <AnalyzerWorkspace externalAnalysis={externalAnalysis} />
      </div>
      <div style={{ display: activeSection === 'threats' ? 'block' : 'none' }}>
        <ThreatMatrixTab />
      </div>
      <div style={{ display: activeSection === 'compliance' ? 'block' : 'none' }}>
        <ComplianceTab />
      </div>
    </div>
  );
}
