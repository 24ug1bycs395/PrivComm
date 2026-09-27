import React, { useState } from 'react';
import Navbar from './components/Navbar';
import TelemetryDashboard from './components/TelemetryDashboard';
import LiveDashboardTab from './components/LiveDashboardTab';
import AnalyzerWorkspace from './components/AnalyzerWorkspace';
import TestbedTab from './components/TestbedTab';
import HistoryVaultTab from './components/HistoryVaultTab';
import Overview from './components/Overview';
import ThreatMatrixTab from './components/ThreatMatrixTab';
import ComplianceTab from './components/ComplianceTab';
import { ThemeProvider } from './ThemeContext';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [inspectedAnalysis, setInspectedAnalysis] = useState(null);

  const handleNavigateToAnalysis = (analysisData) => {
    setInspectedAnalysis(analysisData);
    setActiveTab('dashboard');
  };

  return (
    <ThemeProvider>
      <div className="app-container">
        {/* Ambient background glows */}
        <div className="ambient-grid" aria-hidden="true" />
        <div className="ambient-glow-orb orb-top" aria-hidden="true" />
        <div className="ambient-glow-orb orb-bottom" aria-hidden="true" />

        {/* Sticky Glass Navbar */}
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main Tab Content */}
        <main className="main-content">
          {activeTab === 'dashboard' && (
            <TelemetryDashboard
              externalAnalysis={inspectedAnalysis}
              onNavigateToTestbed={() => setActiveTab('testbed')}
              onNavigateToAnalyzer={() => setActiveTab('analyzer')}
              onNavigateToOverview={() => setActiveTab('overview')}
            />
          )}
          {activeTab === 'live' && (
            <LiveDashboardTab
              onNavigateToTestbed={() => setActiveTab('testbed')}
              onNavigateToAnalyzer={() => setActiveTab('analyzer')}
            />
          )}
          {activeTab === 'analyzer' && <AnalyzerWorkspace externalAnalysis={inspectedAnalysis} />}
          {activeTab === 'testbed' && <TestbedTab onNavigateToAnalysis={handleNavigateToAnalysis} />}
          {activeTab === 'vault' && <HistoryVaultTab onSelectAnalysis={handleNavigateToAnalysis} />}
          {activeTab === 'overview' && (
            <Overview
              onStartAnalysis={() => setActiveTab('analyzer')}
              onViewTelemetry={() => setActiveTab('dashboard')}
            />
          )}
          {activeTab === 'threat-matrix' && <ThreatMatrixTab />}
          {activeTab === 'compliance' && <ComplianceTab />}
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
      </div>
    </ThemeProvider>
  );
}
