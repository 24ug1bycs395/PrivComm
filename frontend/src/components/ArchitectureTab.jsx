import React, { useState, useEffect } from 'react';
import {
  Layers,
  Cpu,
  Database,
  Code2,
  ChevronRight,
  BookOpen,
  ArrowRight,
  FileCode2,
  Sparkles,
  Zap,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Scale,
  ShoppingBag,
  Eye,
  Mail,
  Workflow,
  Table,
  Binary,
  ShieldCheck,
  Search,
  HardDrive,
  Activity,
  Server,
  Lock,
  Radio,
  FileText,
  Terminal,
  Key,
  ShieldAlert,
  GitBranch,
  Network,
  Check
} from 'lucide-react';

const FlowConnector = ({ label }) => (
  <div className="architecture-flow-connector" role="img" aria-label={`${label} workflow connector`}>
    <div className="architecture-flow-line" aria-hidden="true">
      <span className="architecture-flow-packet" />
      <span className="architecture-flow-arrow">⌄</span>
    </div>
    <span className="architecture-flow-label">{label} <span aria-hidden="true">↓</span></span>
  </div>
);

export default function ArchitectureTab() {
  const [activeSection, setActiveSection] = useState('hla');

  const sections = [
    {
      id: 'hla',
      num: '01',
      title: 'High-Level Architecture (HLA)',
      subtitle: '7-Tier Live Blueprint & End-to-End Dataflow',
      icon: Layers,
    },
    {
      id: 'lla',
      num: '02',
      title: 'Low-Level Architecture (LLA)',
      subtitle: 'Internal Functions, Math Models & Call Graphs',
      icon: Code2,
    },
    {
      id: 'schemas',
      num: '03',
      title: 'Database Schemas & Data Layer',
      subtitle: 'Supabase PostgreSQL, SQLite & CBOM Models',
      icon: Database,
    },
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 220;
      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const top = element.offsetTop;
          const height = element.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '60px' }}>
      
      {/* Hero Header */}
      <header
        style={{
          position: 'relative',
          padding: '40px 0 36px 0',
          borderBottom: '1px solid var(--border-default)',
          background: 'linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%)',
          overflow: 'hidden',
          marginBottom: '32px'
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '-60px',
            right: '15%',
            width: '380px',
            height: '380px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%)',
            filter: 'blur(50px)',
            pointerEvents: 'none'
          }}
        />

        <div style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: '0 24px', position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>PrivComm Platform</span>
            <span style={{ color: 'var(--text-muted)' }}>/</span>
            <span style={{ color: 'var(--text-secondary)' }}>System Architecture Specification</span>
          </div>

          <div style={{ maxWidth: '900px' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 12px',
                borderRadius: '9999px',
                background: 'var(--accent-cyan-dim)',
                border: '1px solid var(--border-blueprint)',
                color: 'var(--accent-cyan)',
                fontSize: '0.72rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '16px'
              }}
            >
              <Layers size={13} />
              <span>Technical Blueprint &amp; System Architecture v3.2</span>
            </div>

            <h1
              style={{
                fontSize: '2.4rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
                marginBottom: '14px',
                fontFamily: 'var(--font-sans)'
              }}
            >
              PrivComm <span style={{ background: 'linear-gradient(90deg, var(--accent-cyan), #60a5fa, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Software Architecture &amp; Intelligence Framework</span>
            </h1>

            <p style={{ fontSize: '0.96rem', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '820px' }}>
              Comprehensive technical specification describing the dual-layer architecture of <strong>PrivComm</strong> — featuring the <strong>High-Level Architecture (HLA)</strong> with live multi-tier dataflow orchestration, the <strong>Low-Level Architecture (LLA)</strong> covering zero-payload packet dissection, RFC 4303 arithmetic cipher elimination, 28-feature XGBoost/IsolationForest models, multi-vendor AST parsing, and RFC 8032 Ed25519 Merkle audit seals.
            </p>
          </div>
        </div>
      </header>

      {/* Main Two-Column Layout with Sticky Sidebar */}
      <div style={{ maxWidth: 'var(--max-width)', margin: '0 auto', padding: '0 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(260px, 300px) 1fr', gap: '32px', alignItems: 'start' }}>
          
          {/* Sticky Left Table of Contents */}
          <aside style={{ position: 'sticky', top: '88px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: '16px',
                padding: '20px',
                backdropFilter: 'blur(16px)',
                boxShadow: 'var(--shadow-md)'
              }}
            >
              <h3
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--text-muted)',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <BookOpen size={14} style={{ color: 'var(--accent-cyan)' }} />
                <span>Table of Contents</span>
              </h3>
              
              <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {sections.map((sec) => {
                  const Icon = sec.icon;
                  const isActive = activeSection === sec.id;
                  return (
                    <button
                      key={sec.id}
                      onClick={() => scrollToSection(sec.id)}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '12px 14px',
                        borderRadius: '12px',
                        border: isActive ? '1px solid var(--border-blueprint)' : '1px solid transparent',
                        background: isActive ? 'var(--accent-cyan-dim)' : 'transparent',
                        color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s var(--ease-spring)'
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) e.currentTarget.style.background = 'var(--bg-secondary)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <div
                        style={{
                          padding: '8px',
                          borderRadius: '8px',
                          background: isActive ? 'var(--accent-cyan)' : 'var(--bg-tertiary)',
                          color: isActive ? '#030712' : 'var(--text-secondary)',
                          flexShrink: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <Icon size={16} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)' }}>
                            {sec.num}
                          </span>
                          {isActive && <ChevronRight size={13} style={{ color: 'var(--accent-cyan)' }} />}
                        </div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {sec.title}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {sec.subtitle}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Quick Tech Architecture Card */}
            <div
              style={{
                background: 'linear-gradient(135deg, var(--bg-card) 0%, var(--bg-tertiary) 100%)',
                border: '1px solid var(--border-default)',
                borderRadius: '16px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
                boxShadow: 'var(--shadow-sm)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                <Cpu size={14} />
                <span>PrivComm Technology Stack</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>FRONTEND</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>React 19 + Vite</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>BACKEND</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>FastAPI ASGI</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>ML ENGINE</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>XGBoost + IForest</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>TESTBED</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>strongSwan 4-Node</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>PERSISTENCE</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Supabase / SQLite</div>
                </div>
                <div style={{ padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '2px' }}>ATTESTATION</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Ed25519 + Merkle</div>
                </div>
              </div>
            </div>
          </aside>

          {/* Right Main Content */}
          <main style={{ display: 'flex', flexDirection: 'column', gap: '56px' }}>

            {/* ========================================================================= */}
            {/* SECTION 1: HIGH-LEVEL ARCHITECTURE (HLA) */}
            {/* ========================================================================= */}
            <section id="hla" style={{ scrollMarginTop: '100px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '14px', borderBottom: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      padding: '10px 14px',
                      borderRadius: '12px',
                      background: 'var(--accent-cyan-dim)',
                      color: 'var(--accent-cyan)',
                      border: '1px solid var(--border-blueprint)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      fontSize: '1rem'
                    }}
                  >
                    01
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
                      High-Level Architecture (HLA)
                    </h2>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
                      7-Tier Live Platform Blueprint • Real-Time Pipeline Orchestration
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                  <span style={{ display: 'inline-flex', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-success)', boxShadow: 'var(--status-success-shadow)' }} />
                  <span style={{ color: 'var(--status-success)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Active Data Pipeline
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                PrivComm follows an <strong>AI-assisted, privacy-preserving zero-payload intelligence architecture</strong>. Raw packet captures and vendor configs are ingested locally without decrypting sensitive payloads. The system extracts 28 statistical flow features, identifies protocol negotiation drift, computes NIST SP 800-77 &amp; FIPS 140-3 compliance violations, performs Post-Quantum readiness auditing, and cryptographically signs findings via RFC 8032 Ed25519 Merkle tree audit proofs.
              </p>

              {/* 7-Tier Live Architecture Diagram Blueprint */}
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-blueprint)',
                  borderRadius: '20px',
                  padding: '28px',
                  backdropFilter: 'blur(20px)',
                  boxShadow: 'var(--shadow-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '20px',
                  position: 'relative'
                }}
              >
                {/* Visual Blueprint Title */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                    <Network size={16} style={{ color: 'var(--accent-cyan)' }} />
                    <span>PrivComm System Topology &amp; Microservice Conduit Flow</span>
                  </div>
                  <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    FIPS 140-3 / NIST SP 800-77 Compliant
                  </span>
                </div>

                {/* TIER 1: USERS & APPLICATION ACCESS */}
                <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Tier 1: Users &amp; Application Access
                    </span>
                    <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>Role-Based Access</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🛡️ Security Analyst
                    </div>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      ⚙️ Security Engineer
                    </div>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      📋 SOC / Compliance Reviewer
                    </div>
                  </div>
                </div>

                <FlowConnector label="HTTPS / WebSocket Client Handshake" />

                {/* TIER 2: FRONTEND / PRESENTATION LAYER */}
                <div style={{ border: '1px solid var(--border-blueprint)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Tier 2: Frontend / Presentation Layer (React 19 + Vite + Glassmorphic UI)
                    </span>
                    <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>Single Page App</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      📊 Telemetry
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🔍 PCAP Analyzer
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🖥️ 4-Node Testbed
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🗄️ History Vault
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      ⚖️ Compliance Matrix
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🏛️ Architecture
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🤖 AI Sentinel
                    </div>
                  </div>
                </div>

                <FlowConnector label="REST API JSON Payloads + Multipart Uploads" />

                {/* TIER 3: BACKEND / APPLICATION LAYER */}
                <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Tier 3: Modular Backend &amp; Application API Layer (FastAPI ASGI Service)
                    </span>
                    <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>Uvicorn Worker Pool</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px' }}>
                    <div style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Protocol API</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>/analyze/protocol</div>
                    </div>
                    <div style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Vendor Config API</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>/analyze/vendor-config</div>
                    </div>
                    <div style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Anomaly &amp; ML API</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>/api/anomaly/*</div>
                    </div>
                    <div style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Testbed &amp; Attack API</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>/api/testbed/*</div>
                    </div>
                    <div style={{ padding: '8px 12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Attestation Seal API</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>/api/seal/*</div>
                    </div>
                  </div>
                </div>

                <FlowConnector label="Validated service events + telemetry" />

                {/* TWO-COLUMN SPLIT: TESTBED (LEFT) & PERSISTENCE (RIGHT) */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  
                  {/* TIER 4: STRONGSWAN TESTBED */}
                  <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Tier 4: strongSwan Virtual Testbed
                      </span>
                      <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>Isolated Emulation</span>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Testbed Orchestrator</div>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Automated scenario generation &amp; PCAP retrieval</div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', fontSize: '0.7rem', textAlign: 'center' }}>
                        VM 1 (Initiator)
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', fontSize: '0.7rem', textAlign: 'center' }}>
                        VM 2 (Responder)
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', fontSize: '0.7rem', textAlign: 'center' }}>
                        VM 3 (Observer)
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', fontSize: '0.7rem', textAlign: 'center' }}>
                        VM 4 (Attacker)
                      </div>
                    </div>
                    <div style={{ padding: '6px 10px', background: 'var(--bg-card)', border: '1px dashed var(--border-blueprint)', borderRadius: '6px', fontSize: '0.7rem', color: 'var(--accent-cyan)', textAlign: 'center' }}>
                      Live Attack Injection: PSK Harvest • IKE Flood • Replay • SNDL
                    </div>
                  </div>

                  {/* TIER 5: DATA / PERSISTENCE */}
                  <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Tier 5: Data &amp; Persistence Layer
                      </span>
                      <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>Dual Storage</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.72rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Repository Layer</div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>AnalysisJobRepository</div>
                      </div>
                      <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.72rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Storage Service</div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>PCAP &amp; Report Blob</div>
                      </div>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', fontSize: '0.72rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Supabase PostgreSQL (Cloud)</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Row-Level Security (RLS) &amp; Relational Queries</div>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'var(--bg-card)', border: '1px dashed var(--border-subtle)', borderRadius: '8px', fontSize: '0.72rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Local File &amp; SQLite Fallback</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Offline Air-Gapped Operation</div>
                    </div>
                  </div>

                </div>

                {/* TIER 6: IPSEC SECURITY INTELLIGENCE PIPELINE */}
                <div style={{ border: '1px solid var(--border-blueprint)', borderRadius: '14px', padding: '20px', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <ShieldCheck size={16} style={{ color: 'var(--accent-cyan)' }} />
                      <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        Tier 6: IPsec Security Intelligence &amp; Analysis Core
                      </span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', padding: '2px 10px', borderRadius: '9999px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                      Zero-Payload Decryption
                    </span>
                  </div>

                  {/* Flow Stages */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px' }}>
                    <div style={{ padding: '10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>01. INGESTION</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>PCAP / Config Input</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>TShark / Scapy + Multi-Vendor Lexer</div>
                    </div>
                    <div style={{ padding: '10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>02. PROTOCOL ENGINE</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>IKE / ESP Dissection</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>RFC 4303 Arithmetic Elimination</div>
                    </div>
                    <div style={{ padding: '10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>03. ML &amp; ANOMALY</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>28-Feature XGBoost</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>IsolationForest Anomaly Detector</div>
                    </div>
                    <div style={{ padding: '10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>04. PROVENANCE &amp; POLICY</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>Context Policy Engine</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>4-Tier Provenance Tagging</div>
                    </div>
                  </div>

                  {/* Backend Security Assessment Submodules */}
                  <div style={{ padding: '12px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '10px' }}>
                    <div style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px' }}>
                      SECURITY ASSESSMENT SUBMODULES
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', fontSize: '0.72rem' }}>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        📈 Risk Calculator
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        💡 Recommendation Engine
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        📉 Drift &amp; Downgrade
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        ⚛️ Post-Quantum (PQC)
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        👁️ Metadata Exposure
                      </div>
                      <div style={{ padding: '6px 8px', background: 'var(--bg-tertiary)', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                        🔏 Ed25519 Merkle Seal
                      </div>
                    </div>
                  </div>
                </div>

                {/* TIER 7: SECURITY OUTPUTS & DECISION SUPPORT */}
                <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', background: 'var(--bg-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Tier 7: Security Outputs &amp; Decision Support
                    </span>
                    <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>Returned to Frontend</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      📑 Analysis Results &amp; Findings
                    </div>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🎯 100-Point Security Scorecard
                    </div>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      🔧 Hardened Remediation Diffs
                    </div>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '8px', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      📄 Executive PDF &amp; HTML Reports
                    </div>
                  </div>
                </div>

              </div>
            </section>

            {/* ========================================================================= */}
            {/* SECTION 2: LOW-LEVEL ARCHITECTURE (LLA) */}
            {/* ========================================================================= */}
            <section id="lla" style={{ scrollMarginTop: '100px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '14px', borderBottom: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      padding: '10px 14px',
                      borderRadius: '12px',
                      background: 'var(--accent-blue-dim)',
                      color: 'var(--accent-blue)',
                      border: '1px solid var(--border-blueprint)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      fontSize: '1rem'
                    }}
                  >
                    02
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
                      Low-Level Architecture (LLA)
                    </h2>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
                      Internal Functions, Algorithms, Code Modules &amp; Mathematical Models
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                  <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    12 Core Codebase Modules
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                The Low-Level Architecture (LLA) documents the concrete source modules, key exported functions, mathematical formulations, computational complexities, and the sequential function call graph executing across the PrivComm repository.
              </p>

              {/* Grid of LLA Module Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
                
                {/* 1. pcap_decoder.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <Sliders size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>pcap_decoder.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>analyzer/pcap_decoder.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>decode_pcap_in_memory(pcap_bytes)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Zero-dependency Big-Endian binary parser parsing PCAP/PCAPNG headers, Ethernet frames, IPv4/IPv6, UDP ports 500/4500, IKE ISAKMP SPIs, and ESP Next Header indices.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Time Complexity: <span style={{ color: 'var(--text-primary)' }}>O(N) single-pass streaming</span></div>
                      <div>• Memory Footprint: <span style={{ color: 'var(--text-primary)' }}>Bounded generator with buffer recycling</span></div>
                    </div>
                  </div>
                </div>

                {/* 2. rfc4303.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <Binary size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>rfc4303.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>analyzer/rfc4303.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>eliminate_ciphers_by_padding()</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Arithmetic block alignment cipher candidate elimination without decryption by computing ESP payload modulo alignments against known block sizes.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Modulo Rule: <span style={{ color: 'var(--text-primary)' }}>L_rem = (L_payload - 8 - L_icv) mod BlockSize</span></div>
                      <div>• Output: <span style={{ color: 'var(--text-primary)' }}>Pruned cipher compatibility candidate matrix</span></div>
                    </div>
                  </div>
                </div>

                {/* 3. vendor_config_parser.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <Terminal size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>vendor_config_parser.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>analyzer/vendor_config_parser.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>parse_vendor_config(text, vendor)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Deterministic AST &amp; regex lexer for Cisco ASA/IOS, Fortinet FortiOS, pfSense/OPNsense XML, Libreswan, and strongSwan + automated hardened diff generator.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Vendors: <span style={{ color: 'var(--text-primary)' }}>Cisco, Fortinet, pfSense XML, Libreswan, strongSwan</span></div>
                      <div>• Synthesis: <span style={{ color: 'var(--text-primary)' }}>Generates 1-click hardened compliant diff playbooks</span></div>
                    </div>
                  </div>
                </div>

                {/* 4. flow_extractor.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <Activity size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>flow_extractor.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>analyzer/flow_extractor.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>extract_flow_features(packets)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Extracts 28 non-payload bidirectional statistical flow features across forward/backward packet size distributions, inter-arrival times (FIAT/BIAT), duration, and cadence.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Features: <span style={{ color: 'var(--text-primary)' }}>FIAT_mean, BIAT_std, byte_rate, flow_duration, etc.</span></div>
                      <div>• Normalization: <span style={{ color: 'var(--text-primary)' }}>Zero-payload privacy preserving computation</span></div>
                    </div>
                  </div>
                </div>

                {/* 5. xgboost_adapter.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <Sparkles size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>xgboost_adapter.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>ml/xgboost_adapter.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>predict_traffic_class(feature_vector)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Ensemble of 400 gradient boosted trees executing softmax multiclass probability prediction across 14 application traffic categories (Chat, VoIP, P2P, Streaming, Transfer).
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Hyperparameters: <span style={{ color: 'var(--text-primary)' }}>n_estimators=400, max_depth=8, lr=0.08</span></div>
                      <div>• Output: <span style={{ color: 'var(--text-primary)' }}>Predicted class, confidence &amp; softmax vector</span></div>
                    </div>
                  </div>
                </div>

                {/* 6. anomaly/service.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <AlertTriangle size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>service.py (Anomaly)</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>anomaly/service.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>detect_anomalies(features, baseline)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Unsupervised IsolationForest isolation trees combined with rolling Z-score detectors to identify packet replay attacks, high-entropy exfiltration, and tunnel jitter.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Formulation: <span style={{ color: 'var(--text-primary)' }}>s(x,n) = 2^(-E(h(x)) / c(n))</span></div>
                      <div>• Output: <span style={{ color: 'var(--text-primary)' }}>Anomaly score [-1.0 to 1.0] + severity rating</span></div>
                    </div>
                  </div>
                </div>

                {/* 7. metadata_exposure.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <Eye size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>metadata_exposure.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>analyzer/metadata_exposure.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>assess_metadata_exposure(flow_data)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Quantifies passive cryptographic exposure across outer IP header disclosure, unencrypted IKEv1 Aggressive IDi/IDr payloads, SPI correlation index, and transport mode penalties.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Penalty Scale: <span style={{ color: 'var(--text-primary)' }}>Transport Mode (-20), Plain IDi/IDr (-35)</span></div>
                      <div>• Score Output: <span style={{ color: 'var(--text-primary)' }}>Exposure Index (0-100) + privacy leakage report</span></div>
                    </div>
                  </div>
                </div>

                {/* 8. policy_engine.py & pqc_assessor.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <Scale size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>policy_engine.py &amp; pqc_assessor.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>security/policy_engine.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>evaluate_compliance_and_pqc()</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Deterministic rule engine evaluating NIST SP 800-77 Rev 1, FIPS 140-3, and Mosca theorem inequality (X + Y &gt; Z) against Harvest Now Decrypt Later (HNDL) quantum threats.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Mosca Model: <span style={{ color: 'var(--text-primary)' }}>X (Shelf-life) + Y (Migration) &gt; Z (Collapse)</span></div>
                      <div>• Hybrid Checks: <span style={{ color: 'var(--text-primary)' }}>RFC 9370 Multiple KE &amp; RFC 8784 PPK support</span></div>
                    </div>
                  </div>
                </div>

                {/* 9. seal/signer.py & seal/merkle.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <Lock size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>signer.py &amp; merkle.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>seal/signer.py &amp; seal/merkle.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>generate_merkle_audit_seal()</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Pure-Python RFC 8032 Ed25519 digital signature engine over twisted Edwards curve -x^2 + y^2 = 1 - (121665/121666)x^2y^2 (mod 2^255 - 19) coupled with a binary Merkle audit tree.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Merkle Root: <span style={{ color: 'var(--text-primary)' }}>H(H(Left) || H(Right)) SHA-256 tree</span></div>
                      <div>• Verification: <span style={{ color: 'var(--text-primary)' }}>O(log N) membership proof generation</span></div>
                    </div>
                  </div>
                </div>

                {/* 10. testbed/orchestrator.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <Server size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>orchestrator.py &amp; attack_simulator.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>services/testbed/orchestrator.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>run_testbed_scenario(scenario_id)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Controls 4 isolated network namespaces executing real strongSwan swanctl tunnels, live tcpdump packet capture, and controlled vulnerability injections.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Topology: <span style={{ color: 'var(--text-primary)' }}>Initiator (.10), Responder (.20), Observer (.30), Attacker (.40)</span></div>
                      <div>• Scenarios: <span style={{ color: 'var(--text-primary)' }}>NIST Compliant, Aggressive PSK, Weak 3DES, IKE Flooding</span></div>
                    </div>
                  </div>
                </div>

                {/* 11. crypto_bom.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                        <FileText size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>crypto_bom.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>reports/crypto_bom.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)' }}>generate_cbom(analysis_result)</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Synthesizes a CycloneDX-compatible Cryptographic Bill of Materials (<code style={{ fontFamily: 'var(--font-mono)' }}>privcomm.cbom.v1</code>) detailing cryptographic primitives, key lengths, and CNSA 2.0 status.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Schema: <span style={{ color: 'var(--text-primary)' }}>CycloneDX CBOM v1.6 specification</span></div>
                      <div>• Output: <span style={{ color: 'var(--text-primary)' }}>Cryptographic asset inventory JSON &amp; verification hash</span></div>
                    </div>
                  </div>
                </div>

                {/* 12. db/repository.py & supabase_client.py */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ padding: '6px', borderRadius: '8px', background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>
                        <Database size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>repository.py &amp; supabase_client.py</div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>db/repository.py</div>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}>Python 3.11</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Main Function: </span>
                      <code style={{ padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-blue)' }}>AnalysisJobRepository.save_job()</code>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', lineHeight: 1.5 }}>
                      Abstraction layer orchestrating dual-mode persistence with Supabase PostgreSQL cloud syncing, SQLite local transactions, and signed audit history.
                    </p>
                    <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div>• Resilience: <span style={{ color: 'var(--text-primary)' }}>Auto-fallback to local SQLite when offline</span></div>
                      <div>• Security: <span style={{ color: 'var(--text-primary)' }}>Postgres Row-Level Security (RLS) policies</span></div>
                    </div>
                  </div>
                </div>

              </div>

              {/* Step-by-Step Runtime Function Call Graph */}
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '16px',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)' }}>
                    <Workflow size={18} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                      Runtime Execution Pipeline &amp; Function Call Graph
                    </h3>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
                      Sequential control flow: Client Upload ➔ Feature Extraction ➔ Cryptographic Verification ➔ Signed Output
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
                  
                  {/* Step 1 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: 'var(--accent-cyan)', color: '#030712', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      1
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>Ingestion &amp; Binary Frame Decoding</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>pcap_decoder.py / vendor_config_parser.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>decode_pcap_in_memory()</code> streams Ethernet frames, decodes IPv4/IPv6 packet headers, and isolates UDP ports 500/4500 and ESP packets.
                      </div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: 'var(--accent-blue)', color: '#ffffff', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      2
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>IKE/ESP Protocol Dissection &amp; RFC 4303 Alignment</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>ike_parser.py + rfc4303.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>parse_ike_payloads()</code> parses Security Association transforms; <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>eliminate_ciphers_by_padding()</code> eliminates cipher candidates via block alignment math.
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: 'var(--status-success)', color: '#030712', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      3
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>Statistical Feature Extraction (28 Dimensions)</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--status-success)' }}>flow_extractor.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-success)' }}>extract_flow_features()</code> calculates forward/backward inter-arrival times, burst rates, packet lengths, and flow durations without decrypting data.
                      </div>
                    </div>
                  </div>

                  {/* Step 4 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: 'var(--status-warning)', color: '#030712', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      4
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>ML Classification &amp; Behavioral Anomaly Detection</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--status-warning)' }}>xgboost_adapter.py + service.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-warning)' }}>XGBoostAdapter.predict()</code> outputs 14-class probability distribution; <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-warning)' }}>AnomalyService.predict()</code> detects behavioral outliers.
                      </div>
                    </div>
                  </div>

                  {/* Step 5 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: '#818cf8', color: '#ffffff', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      5
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>Security Policy, Drift &amp; Post-Quantum Assessment</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#818cf8' }}>policy_engine.py + pqc_assessor.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: '#818cf8' }}>SecurityPolicyEngine.evaluate()</code> audits NIST SP 800-77 rules, configuration drift, and Mosca theorem quantum shelf-life risks.
                      </div>
                    </div>
                  </div>

                  {/* Step 6 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: '#f43f5e', color: '#ffffff', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      6
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>RFC 8032 Ed25519 Signature &amp; Merkle Seal</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#f43f5e' }}>signer.py + merkle.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: '#f43f5e' }}>generate_merkle_audit_seal()</code> generates a SHA-256 Merkle root over analysis claims and signs it with an Ed25519 private key.
                      </div>
                    </div>
                  </div>

                  {/* Step 7 */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: 'var(--accent-cyan)', color: '#030712', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      7
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)' }}>Persistence, Remediation Diff &amp; Report Synthesis</span>
                        <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>repository.py + report_generator.py</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>AnalysisJobRepository.save_job()</code> writes records to PostgreSQL/SQLite; outputs executive HTML/PDF reports and CBOM inventory.
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </section>

            {/* ========================================================================= */}
            {/* SECTION 3: DATABASE SCHEMAS & DATA LAYER */}
            {/* ========================================================================= */}
            <section id="schemas" style={{ scrollMarginTop: '100px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '14px', borderBottom: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      padding: '10px 14px',
                      borderRadius: '12px',
                      background: 'var(--status-success-dim)',
                      color: 'var(--status-success)',
                      border: '1px solid var(--status-success-border)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      fontSize: '1rem'
                    }}
                  >
                    03
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
                      Database Schemas &amp; Data Layer
                    </h2>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
                      Supabase PostgreSQL 16 &amp; SQLite Dual Persistence Model
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                  <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'var(--status-success-dim)', border: '1px solid var(--status-success-border)', color: 'var(--status-success)', fontWeight: 600 }}>
                    PostgreSQL 16 / SQLite Hybrid
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                PrivComm persistence is designed with <strong>defense-in-depth isolation</strong>. All analysis records, flow features, security assessments, audit seals, and CBOM inventories are stored with strict UUID primary keys, cryptographic verification hashes, and Row-Level Security (RLS) policies.
              </p>

              {/* Grid of Database Tables */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                
                {/* 1. analysis_jobs table */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Table size={16} style={{ color: 'var(--accent-cyan)' }} />
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>analysis_jobs</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>AnalysisJobModel</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>[PK]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>file_hash_sha256</span>
                      <span style={{ color: 'var(--text-muted)' }}>VARCHAR(64) <span style={{ color: 'var(--status-success)', fontWeight: 700 }}>[INDEX]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>capture_source</span>
                      <span style={{ color: 'var(--text-muted)' }}>VARCHAR(32) (PCAP/Config)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>security_score</span>
                      <span style={{ color: 'var(--text-muted)' }}>INTEGER (0-100)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                      <span style={{ color: 'var(--text-primary)' }}>created_at</span>
                      <span style={{ color: 'var(--text-muted)' }}>TIMESTAMPTZ</span>
                    </div>
                  </div>
                </div>

                {/* 2. security_assessments table */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Table size={16} style={{ color: 'var(--accent-blue)' }} />
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>security_assessments</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>SecurityAssessmentModel</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>[PK]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>job_id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--status-warning)', fontWeight: 700 }}>[FK -&gt; jobs]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>nist_compliance_status</span>
                      <span style={{ color: 'var(--text-muted)' }}>VARCHAR(32)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>pqc_readiness_score</span>
                      <span style={{ color: 'var(--text-muted)' }}>FLOAT (0.0-1.0)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                      <span style={{ color: 'var(--text-primary)' }}>findings_payload</span>
                      <span style={{ color: 'var(--text-muted)' }}>JSONB</span>
                    </div>
                  </div>
                </div>

                {/* 3. audit_seals table */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Table size={16} style={{ color: '#f43f5e' }} />
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>audit_seals</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>AuditSealModel</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>[PK]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>job_id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--status-warning)', fontWeight: 700 }}>[FK -&gt; jobs]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>merkle_root_sha256</span>
                      <span style={{ color: 'var(--text-muted)' }}>CHAR(64)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>ed25519_signature</span>
                      <span style={{ color: 'var(--text-muted)' }}>CHAR(128)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                      <span style={{ color: 'var(--text-primary)' }}>signer_public_key</span>
                      <span style={{ color: 'var(--text-muted)' }}>CHAR(64)</span>
                    </div>
                  </div>
                </div>

                {/* 4. cbom_inventory table */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: '14px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Table size={16} style={{ color: 'var(--status-success)' }} />
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>cbom_inventory</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>CBOMRecordModel</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>id</span>
                      <span style={{ color: 'var(--text-muted)' }}>UUID <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>[PK]</span></span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>algorithm_name</span>
                      <span style={{ color: 'var(--text-muted)' }}>VARCHAR(64)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>primitive_type</span>
                      <span style={{ color: 'var(--text-muted)' }}>VARCHAR(32) (AEAD/DH/KEM)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span style={{ color: 'var(--text-primary)' }}>cnsa_2_0_compliant</span>
                      <span style={{ color: 'var(--text-muted)' }}>BOOLEAN</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                      <span style={{ color: 'var(--text-primary)' }}>quantum_safe</span>
                      <span style={{ color: 'var(--text-muted)' }}>BOOLEAN</span>
                    </div>
                  </div>
                </div>

              </div>
            </section>

          </main>
        </div>
      </div>
    </div>
  );
}
