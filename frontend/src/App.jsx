import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';

import TelemetryDashboard from './components/TelemetryDashboard';
import HistoryVaultTab from './components/HistoryVaultTab';
import Overview from './components/Overview';
import TechnicalDocsTab from './components/TechnicalDocsTab';
import IPsecSecurityPage from './components/IPsecSecurityPage';
import LiveSecurityLabPage from './components/LiveSecurityLabPage';

import { ThemeProvider } from './ThemeContext';
const VALID_TABS = ['dashboard', 'ipsec-security', 'live-security', 'vault', 'overview', 'docs'];

function getInitialTab() {
  if (typeof window !== 'undefined') {
    const hash = window.location.hash.replace('#', '').trim().toLowerCase();
    if (hash === 'documentation' || hash === 'technical-documentation') return 'docs';
    // Legacy hash redirects for old bookmarks
    if (hash === 'analyzer' || hash === 'ipsec') return 'ipsec-security';
    if (hash === 'live' || hash === 'testbed') return 'live-security';
    if (hash === 'telemetry') return 'dashboard';
    if (hash === 'compliance') return 'ipsec-security';
    if (VALID_TABS.includes(hash)) return hash;
  }
  return 'overview';
}

export default function App() {
  const [activeTab, setActiveTabRaw] = useState(getInitialTab);
  const [inspectedAnalysis, setInspectedAnalysis] = useState(null);
  const [liveJobId, setLiveJobId] = useState(null);
  const [liveDashboardEnabled, setLiveDashboardEnabled] = useState(false);
  const [showLiveBlockedDialog, setShowLiveBlockedDialog] = useState(false);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '').trim().toLowerCase();
      let resolved = hash;
      if (hash === 'documentation' || hash === 'technical-documentation') resolved = 'docs';
      else if (hash === 'analyzer' || hash === 'ipsec') resolved = 'ipsec-security';
      else if (hash === 'live' || hash === 'testbed') resolved = 'live-security';
      else if (hash === 'telemetry') resolved = 'dashboard';
      else if (hash === 'compliance') resolved = 'ipsec-security';
      if (VALID_TABS.includes(resolved)) {
        setActiveTabRaw(resolved);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const setActiveTab = (tab) => {
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', `/#${tab}`);
    }
    setActiveTabRaw(tab);
  };

  const handleNavigateToAnalysis = (analysisData) => {
    setInspectedAnalysis(analysisData);
    setActiveTab('ipsec-security');
  };

  return (
    <ThemeProvider>
      <div className="app-container">
        {/* Ambient background glows */}
        <div className="ambient-grid" aria-hidden="true" />
        <div className="ambient-glow-orb orb-top" aria-hidden="true" />
        <div className="ambient-glow-orb orb-bottom" aria-hidden="true" />

        {/* Sticky Glass Navbar */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          liveDashboardEnabled={liveDashboardEnabled}
        />

        {/* Main Tab Content */}
        <main className="main-content">
          {activeTab === 'dashboard' && (
            <TelemetryDashboard
              externalAnalysis={inspectedAnalysis}
              onNavigateToTestbed={() => setActiveTab('live-security')}
              onNavigateToAnalyzer={() => setActiveTab('ipsec-security')}
              onNavigateToOverview={() => setActiveTab('overview')}
            />
          )}
          {activeTab === 'ipsec-security' && (
            <IPsecSecurityPage externalAnalysis={inspectedAnalysis} />
          )}
          {activeTab === 'live-security' && (
            <LiveSecurityLabPage
              externalAnalysis={inspectedAnalysis}
              onNavigateToAnalyzer={() => setActiveTab('ipsec-security')}
              onNavigateToOverview={() => setActiveTab('overview')}
              onNavigateToAnalysis={handleNavigateToAnalysis}
            />
          )}
          {activeTab === 'vault' && <HistoryVaultTab onSelectAnalysis={handleNavigateToAnalysis} />}
          {activeTab === 'overview' && (
            <Overview
              onStartAnalysis={() => setActiveTab('ipsec-security')}
              onViewTelemetry={() => setActiveTab('dashboard')}
            />
          )}
          {activeTab === 'docs' && <TechnicalDocsTab />}
        </main>

        {/* Footer */}
        <footer className="site-footer">
          <div className="footer-inner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.9rem' }}>Privcomm</span>
              <span style={{ color: 'var(--text-muted)' }}>&mdash;</span>
              <span style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>AI-Assisted IPsec VPN Security Intelligence</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              FIPS 140-3 &bull; NIST SP 800-77 &bull; NSA CSfC &bull; Zero External Data Exfiltration
            </div>
          </div>
        </footer>
        {/* Live-blocked dialog */}
        {showLiveBlockedDialog && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="live-blocked-title"
            onClick={() => setShowLiveBlockedDialog(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: 9999,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
              animation: 'fade-in 0.18s ease',
            }}
          >
            <div
              onClick={e => e.stopPropagation()}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: '14px',
                padding: '32px 36px',
                maxWidth: '380px',
                width: '90%',
                boxShadow: '0 24px 64px rgba(0,0,0,0.45)',
                textAlign: 'center',
                animation: 'slide-in-up 0.22s var(--ease-spring)',
              }}
            >
              {/* Icon */}
              <div style={{
                width: 52, height: 52, borderRadius: '50%',
                background: 'rgba(234,179,8,0.12)',
                border: '1px solid rgba(234,179,8,0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 18px',
                fontSize: '1.6rem',
              }}>
                {'!'}
              </div>
              <div id="live-blocked-title" style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                fontSize: '1rem',
                color: 'var(--text-primary)',
                marginBottom: '10px',
                letterSpacing: '0.02em',
              }}>
                No Active Session
              </div>
              <p style={{
                fontSize: '0.84rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
                marginBottom: '24px',
              }}>
                Run the testbed first to start a live IPsec session before opening the Live Dashboard.
              </p>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <button
                  id="live-blocked-go-testbed"
                  onClick={() => { setShowLiveBlockedDialog(false); setActiveTabRaw('live-security'); }}
                  style={{
                    padding: '9px 20px',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'var(--accent-blue)',
                    color: '#fff',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    letterSpacing: '0.03em',
                  }}
                >
                  Go to Testbed
                </button>
                <button
                  id="live-blocked-dismiss"
                  onClick={() => setShowLiveBlockedDialog(false)}
                  style={{
                    padding: '9px 20px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 500,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ThemeProvider>
  );
}
