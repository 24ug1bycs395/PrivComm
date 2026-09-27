import React from 'react';
import {
  Shield, CheckCircle, ArrowRight, Eye, Search, Lock,
  HelpCircle, Activity, CheckSquare, Cpu, Zap, Database,
  TrendingUp, GitBranch, Globe, Award, ChevronRight
} from 'lucide-react';
import TopologyCanvas from './TopologyCanvas';

/* ── Pipeline Steps (Unified 3-4 Color Palette: Blue, Green, Amber) ─── */
const steps = [
  {
    num: '01', title: 'Observe',
    desc: 'Ingest live interface taps, raw PCAP/PCAPNG streams, and gateway session telemetry in real-time.',
    tag: 'Data Ingestion', icon: Eye,
    color: 'var(--accent-blue)', glow: 'var(--accent-blue-dim)',
  },
  {
    num: '02', title: 'Identify',
    desc: 'Demultiplex IKEv1/IKEv2 handshakes, ESP/AH payload types, SPI indices, and negotiation transforms.',
    tag: 'Protocol Parsing', icon: Search,
    color: 'var(--accent-cyan)', glow: 'var(--accent-cyan-dim)',
  },
  {
    num: '03', title: 'Assess',
    desc: 'Validate cipher resilience, PRF/hash integrity, key lengths, and Diffie-Hellman group parameters.',
    tag: 'Crypto Evaluation', icon: Lock,
    color: 'var(--accent-cyan)', glow: 'var(--accent-cyan-dim)',
  },
  {
    num: '04', title: 'Explain',
    desc: 'Generate transparent, deterministic security rationale without black-box ML obfuscation.',
    tag: 'Explainable AI', icon: HelpCircle,
    color: 'var(--accent-blue)', glow: 'var(--accent-blue-dim)',
  },
  {
    num: '05', title: 'Simulate',
    desc: 'Model hypothetical cipher downgrades, rekey exhaustion events, and replay vulnerability postures.',
    tag: 'Digital Twin', icon: Activity,
    color: 'var(--accent-blue)', glow: 'var(--accent-blue-dim)',
  },
  {
    num: '06', title: 'Secure',
    desc: 'Synthesize actionable remediation playbooks, cryptographic hardening scripts, and audit reports.',
    tag: 'Hardening', icon: CheckSquare,
    color: 'var(--accent-cyan)', glow: 'var(--accent-cyan-dim)',
  },
];

/* ── Capability Highlights ──────────────────────────────────────────── */
const capabilities = [
  { icon: Cpu,        label: 'XGBoost Traffic Classification',  sub: 'ML-driven IKE/ESP classification' },
  { icon: Zap,        label: 'Real-Time PCAP Dissection',       sub: 'Zero-latency protocol parsing' },
  { icon: Database,   label: 'Analysis Vault',                  sub: 'Persistent session storage' },
  { icon: TrendingUp, label: 'Risk Score Engine',               sub: 'CVSS-aligned threat scoring' },
  { icon: GitBranch,  label: 'strongSwan Testbed',              sub: 'Full IPsec tunnel simulation' },
  { icon: Globe,      label: 'Geo-IP Correlation',              sub: 'Endpoint geolocation mapping' },
  { icon: Shield,     label: 'NIST SP 800-77 Compliance',       sub: 'Automated policy auditing' },
  { icon: Award,      label: 'FIPS 140-3 Validation',           sub: 'Federal crypto standard checks' },
];

/* ── Trust Metrics ──────────────────────────────────────────────────── */
const metrics = [
  { value: '99.4%', label: 'Detection Accuracy' },
  { value: '<80ms', label: 'Analysis Latency' },
  { value: '200+',  label: 'Cipher Profiles' },
  { value: '0',     label: 'External Data Exfil' },
];

/* ── Component ──────────────────────────────────────────────────────── */
export default function Overview({ onStartAnalysis, onViewTelemetry }) {
  return (
    <div className="overview-page" style={{ animation: 'fade-in 0.4s ease' }}>

      {/* ─── Hero ─────────────────────────────────────────────────── */}
      <section style={{ textAlign: 'center', maxWidth: '860px', margin: '0 auto 72px auto' }}>

        {/* Top pill label */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '10px',
          padding: '7px 18px', borderRadius: '9999px',
          background: 'var(--accent-cyan-dim)',
          border: '1px solid var(--border-default)',
          color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)',
          fontSize: '0.72rem', fontWeight: 600,
          letterSpacing: '0.08em', marginBottom: '28px',
          textTransform: 'uppercase',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <Shield size={14} strokeWidth={2.5} />
          <span>NIST SP 800-77 · NSA CSfC · FIPS 140-3</span>
          <span style={{ opacity: 0.35 }}>|</span>
          <span>Federal &amp; Enterprise Security</span>
        </div>

        {/* Headline */}
        <h1 style={{
          fontSize: 'clamp(2.2rem, 5vw, 3.4rem)',
          fontWeight: 900,
          color: 'var(--text-primary)',
          letterSpacing: '-0.035em',
          lineHeight: 1.12,
          marginBottom: '22px',
        }}>
          AI-Assisted{' '}
          <span style={{ color: 'var(--accent-blue)' }}>
            IPsec Security
          </span>
          <br />Intelligence Platform
        </h1>

        {/* Sub */}
        <p style={{
          fontSize: '1.08rem', color: 'var(--text-secondary)',
          lineHeight: 1.75, marginBottom: '36px',
          maxWidth: '660px', margin: '0 auto 36px auto',
        }}>
          Transform VPN packet captures, gateway logs, and encrypted traffic into
          actionable risk assessments, explainable recommendations, and compliance reports —
          without a single byte leaving your perimeter.
        </p>

        {/* CTA Row */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button
            type="button"
            id="hero-launch-analyzer"
            className="btn btn-primary btn-lg"
            onClick={onStartAnalysis}
          >
            <Zap size={17} />
            Launch Live Analyzer
            <ArrowRight size={17} />
          </button>
          <button
            type="button"
            id="hero-view-dashboard"
            className="btn btn-secondary btn-lg"
            onClick={onViewTelemetry}
          >
            View Telemetry Dashboard
            <ChevronRight size={17} />
          </button>
        </div>
      </section>

      {/* ─── Trust Metrics Strip ──────────────────────────────────── */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1px',
          background: 'var(--border-subtle)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          marginBottom: '72px',
          boxShadow: 'var(--shadow-sm)'
        }}
        aria-label="Platform Statistics"
      >
        {metrics.map((m) => (
          <div
            key={m.label}
            style={{
              background: 'var(--bg-card)',
              padding: '28px 20px',
              textAlign: 'center',
            }}
          >
            <div style={{
              fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)',
              letterSpacing: '-0.03em', lineHeight: 1,
              marginBottom: '6px',
            }}>
              {m.value}
            </div>
            <div style={{
              fontSize: '0.78rem', color: 'var(--text-tertiary)',
              fontFamily: 'var(--font-mono)', letterSpacing: '0.04em',
              fontWeight: 500,
            }}>
              {m.label}
            </div>
          </div>
        ))}
      </section>

      {/* ─── Network Topology ─────────────────────────────────────── */}
      <section style={{ marginBottom: '80px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div className="section-label">Live Network Topology</div>
          <h2 style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            End-to-End VPN Architecture Visualization
          </h2>
        </div>
        <TopologyCanvas />
      </section>

      {/* ─── Six-Stage Pipeline ───────────────────────────────────── */}
      <section style={{ marginBottom: '80px' }}>
        <div style={{ textAlign: 'center', marginBottom: '44px' }}>
          <div className="section-label">Deterministic Methodology</div>
          <h2 style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Six-Stage Intelligence Pipeline
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '10px', maxWidth: '520px', margin: '10px auto 0' }}>
            A transparent, auditable analysis chain — no black boxes, no hidden inference.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
        }}>
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <article
                key={step.num}
                className="card-glass"
                id={`pipeline-step-${step.num}`}
                style={{
                  display: 'flex', flexDirection: 'column', gap: '16px',
                  borderTop: `3px solid ${step.color}`,
                  position: 'relative', overflow: 'hidden',
                  animationDelay: `${i * 60}ms`,
                }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontSize: '1.4rem',
                    fontWeight: 800, color: step.color, lineHeight: 1,
                  }}>
                    {step.num}
                  </span>
                  <div style={{
                    width: '38px', height: '38px', borderRadius: '10px',
                    background: step.glow,
                    border: '1px solid var(--border-default)',
                    color: step.color,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <Icon size={18} strokeWidth={2} />
                  </div>
                </div>

                {/* Content */}
                <div>
                  <h3 style={{
                    fontSize: '1.08rem', fontWeight: 700, color: 'var(--text-primary)',
                    marginBottom: '8px', letterSpacing: '-0.01em',
                  }}>
                    {step.title}
                  </h3>
                  <p style={{
                    fontSize: '0.86rem', color: 'var(--text-secondary)',
                    lineHeight: 1.65,
                  }}>
                    {step.desc}
                  </p>
                </div>

                {/* Tag */}
                <span className="tag-mono" style={{ alignSelf: 'flex-start', color: step.color, borderColor: 'var(--border-default)' }}>
                  {step.tag}
                </span>
              </article>
            );
          })}
        </div>
      </section>

      {/* ─── Capabilities Grid ────────────────────────────────────── */}
      <section style={{ marginBottom: '80px' }}>
        <div style={{ textAlign: 'center', marginBottom: '44px' }}>
          <div className="section-label">Platform Capabilities</div>
          <h2 style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Built for High-Assurance Environments
          </h2>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px',
        }}>
          {capabilities.map((cap, i) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.label}
                id={`capability-${i}`}
                style={{
                  display: 'flex', alignItems: 'center', gap: '16px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '18px 20px',
                  cursor: 'default',
                  transition: 'all 0.22s var(--ease-smooth)',
                  boxShadow: 'var(--shadow-sm)'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--accent-blue)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                }}
              >
                <div style={{
                  width: '40px', height: '40px', borderRadius: '10px', flexShrink: 0,
                  background: 'var(--accent-cyan-dim)',
                  border: '1px solid var(--border-default)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--accent-cyan)',
                }}>
                  <Icon size={18} strokeWidth={1.8} />
                </div>
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                    {cap.label}
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    {cap.sub}
                  </div>
                </div>
                <CheckCircle size={15} style={{ marginLeft: 'auto', color: 'var(--accent-cyan)', flexShrink: 0, opacity: 0.85 }} />
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── CTA Banner ───────────────────────────────────────────── */}
      <section
        id="overview-cta-banner"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-xl)',
          padding: '48px 40px',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-md)'
        }}
      >
        <div className="section-label" style={{ marginBottom: '14px' }}>Ready to Analyze</div>
        <h2 style={{
          fontSize: '1.9rem', fontWeight: 800, color: 'var(--text-primary)',
          letterSpacing: '-0.025em', marginBottom: '14px',
        }}>
          Start Your First IPsec Analysis
        </h2>
        <p style={{
          color: 'var(--text-secondary)', fontSize: '0.98rem', lineHeight: 1.7,
          maxWidth: '500px', margin: '0 auto 30px',
        }}>
          Upload a PCAP file or connect to a live interface to begin real-time
          protocol dissection and security assessment.
        </p>
        <button
          type="button"
          id="cta-launch-analyzer"
          className="btn btn-primary btn-lg"
          onClick={onStartAnalysis}
          style={{ margin: '0 auto' }}
        >
          <Zap size={17} />
          Launch Analyzer
          <ArrowRight size={17} />
        </button>
      </section>
    </div>
  );
}
