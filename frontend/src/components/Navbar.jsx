import React, { useEffect, useState } from 'react';
import { Activity, Layers, FileCheck, Server, Database, LayoutDashboard, Sun, Moon, Menu, X, Shield, Radio, BookOpen } from 'lucide-react';
import { useTheme } from '../ThemeContext';

const tabs = [
  { id: 'dashboard', label: 'Telemetry', icon: LayoutDashboard },
  { id: 'live', label: 'Live Dashboard', icon: Radio },
  { id: 'analyzer', label: 'PCAP Analyzer', icon: Activity },
  { id: 'testbed', label: 'Testbed', icon: Server },
  { id: 'vault', label: 'Vault', icon: Database },
  { id: 'overview', label: 'Architecture', icon: Layers },
  { id: 'compliance', label: 'Compliance', icon: FileCheck },
];

export default function Navbar({ activeTab, setActiveTab, liveDashboardEnabled = false }) {
  const { theme, toggle } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isDark = theme === 'dark';

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <>
      <header className={`site-header${scrolled ? ' scrolled' : ''}`} role="banner">
        <div className="header-inner">
          <button
            type="button"
            className="brand-wrapper"
            onClick={() => setActiveTab('overview')}
            aria-label="Privcomm home"
          >
            <span className="brand-mark" aria-hidden="true"><Shield size={18} strokeWidth={2.1} /></span>
            <span className="brand-lockup">
              <span className="brand-name">Privcomm</span>
              <span className="brand-subtitle">IPSEC SECURITY INTELLIGENCE</span>
            </span>
          </button>
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '9px',
            cursor: 'pointer',
            textDecoration: 'none',
            userSelect: 'none',
            flexShrink: 0
          }}
          >
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            background: 'var(--accent-blue)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(37,99,235,0.3)'
          }}>
            <Shield size={16} strokeWidth={2.5} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              fontSize: '0.92rem',
              letterSpacing: '-0.01em',
              color: 'var(--text-primary)'
            }}>
              PRIVCOMM
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.62rem',
              fontWeight: 700,
              color: 'var(--accent-blue)',
              padding: '1px 5px',
              border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
              borderRadius: '3px',
              background: 'var(--accent-blue-dim)'
            }}>
              v2.4
            </span>
          </div>
        </div>

        {/* Desktop Nav */}
        <nav className="nav-tabs" aria-label="Main Navigation">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const isLiveLocked = tab.id === 'live' && !liveDashboardEnabled;
            return (
              <button
                key={tab.id}
                type="button"
                id={`nav-${tab.id}`}
                className={`nav-tab-btn${isActive ? ' active' : ''}`}
                onClick={() => !isLiveLocked && setActiveTab(tab.id)}
                disabled={isLiveLocked}
                title={isLiveLocked ? 'Run the testbed and establish the tunnel first' : undefined}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={15} strokeWidth={isActive ? 2.2 : 1.8} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>

          {/* Live badge */}
          <div className="header-status-badge" aria-label="System Status: Operational">
            <span className="live-dot" aria-hidden="true" />
            <span>LIVE</span>
          </div>

          {/* Theme toggle */}
          <button
            type="button"
            id="theme-toggle-btn"
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            onClick={toggle}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: '1px solid var(--border-default)',
              background: 'var(--bg-card)',
              color: isDark ? '#38bdf8' : '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
              backdropFilter: 'blur(12px)',
              transition: 'all 0.22s var(--ease-spring)',
              boxShadow: isDark
                ? '0 0 12px rgba(56,189,248,0.15)'
                : '0 0 12px rgba(37,99,235,0.15)',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1) rotate(15deg)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1) rotate(0deg)'; }}
          >
            {isDark
              ? <Sun size={16} strokeWidth={2} />
              : <Moon size={16} strokeWidth={2} />
            }
          </button>

          {/* Mobile menu toggle — hidden via CSS on wide screens */}
          <button
            type="button"
            className="mobile-menu-toggle"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{
              display: 'none', /* shown via @media in CSS */
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              border: '1px solid var(--border-default)',
              background: 'var(--bg-card)',
              color: 'var(--text-secondary)',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>
    </header >

      {/* Mobile Drawer */ }
  {
    mobileOpen && (
      <nav
        className="mobile-nav-drawer"
        aria-label="Mobile Navigation"
        style={{
          position: 'fixed',
          top: 'var(--header-height)',
          left: 0,
          right: 0,
          background: 'var(--bg-primary)',
          backdropFilter: 'blur(24px)',
          borderBottom: '1px solid var(--border-default)',
          padding: '12px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          zIndex: 99,
          animation: 'slide-in-up 0.2s ease',
        }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          const isLiveLocked = tab.id === 'live' && !liveDashboardEnabled;
          return (
            <button
              key={tab.id}
              type="button"
              className={`nav-tab-btn${isActive ? ' active' : ''}`}
              onClick={() => { if (!isLiveLocked) { setActiveTab(tab.id); setMobileOpen(false); } }}
              disabled={isLiveLocked}
              title={isLiveLocked ? 'Run the testbed and establish the tunnel first' : undefined}
              style={{ justifyContent: 'flex-start', padding: '10px 14px', width: '100%' }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    )
  }
    </>
  );
}
