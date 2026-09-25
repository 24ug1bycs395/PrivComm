import React, { useState } from 'react';
import Navbar from './components/Navbar';
import TelemetryDashboard from './components/TelemetryDashboard';
import AnalyzerWorkspace from './components/AnalyzerWorkspace';
import TestbedTab from './components/TestbedTab';
import HistoryVaultTab from './components/HistoryVaultTab';
import Overview from './components/Overview';
import ThreatMatrixTab from './components/ThreatMatrixTab';
import ComplianceTab from './components/ComplianceTab';
import { Shield } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [inspectedAnalysis, setInspectedAnalysis] = useState(null);

  const handleNavigateToAnalysis = (analysisData) => {
    setInspectedAnalysis(analysisData);
    setActiveTab('dashboard');
  };

  return (
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
          />
        )}
        {activeTab === 'analyzer' && <AnalyzerWorkspace externalAnalysis={inspectedAnalysis} />}
        {activeTab === 'testbed' && <TestbedTab onNavigateToAnalysis={handleNavigateToAnalysis} />}
        {activeTab === 'vault' && <HistoryVaultTab onSelectAnalysis={handleNavigateToAnalysis} />}
        {activeTab === 'overview' && <Overview onStartAnalysis={() => setActiveTab('analyzer')} />}
        {activeTab === 'threat-matrix' && <ThreatMatrixTab />}
        {activeTab === 'compliance' && <ComplianceTab />}
      </main>

      {/* Footer */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={18} color="#38bdf8" />
            <span style={{ fontWeight: 700, color: '#fff' }}>Privcomm</span>
            <span style={{ color: '#64748b' }}>&bull; AI-Assisted IPsec VPN Security Intelligence</span>
          </div>
          <div style={{ fontFamily: 'JetBrains Mono', fontSize: '0.72rem', color: '#94a3b8' }}>
            FIPS 140-3 &bull; NIST SP 800-77 &bull; Zero External Data Exfiltration
          </div>
        </div>
      </footer>
    </div>
  );
}
