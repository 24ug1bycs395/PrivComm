import React from 'react';
import { Shield, Activity, Layers, FileCheck, Server, Database, LayoutDashboard } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Telemetry Dashboard', icon: LayoutDashboard },
    { id: 'analyzer', label: 'Live PCAP Analyzer', icon: Activity },
    { id: 'testbed', label: 'strongSwan Testbed', icon: Server },
    { id: 'vault', label: 'Analysis Vault', icon: Database },
    { id: 'overview', label: 'Architecture', icon: Layers },
    { id: 'threat-matrix', label: 'Threat Matrix', icon: Shield },
    { id: 'compliance', label: 'Compliance Specs', icon: FileCheck },
  ];

  return (
    <header className="site-header">
      <div className="header-inner">
        <div className="brand-wrapper" onClick={() => setActiveTab('analyzer')}>
          <div className="brand-icon">
            <Shield size={22} />
          </div>
          <div className="brand-title-group">
            <span className="brand-title">Privcomm</span>
            <span className="brand-subtitle">AI-ASSISTED IPSEC INTELLIGENCE</span>
          </div>
        </div>

        <nav className="nav-tabs" aria-label="Main Navigation">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="header-status-badge">
          <span className="live-dot"></span>
          <span>NIST SP 800-77 AUDIT ENGINE</span>
        </div>
      </div>
    </header>
  );
}
