import React, { useState } from 'react';
import {
  Shield, CheckCircle, ArrowRight, Eye, Search, Lock,
  HelpCircle, Activity, CheckSquare, Cpu, Zap, Database,
  TrendingUp, GitBranch, Globe, Award, ChevronRight, Terminal,
  ExternalLink, Layers, Check
} from 'lucide-react';
import PrivCommTunnelVisualizer from './PrivCommTunnelVisualizer';

/* ── Pipeline Steps (makingsoftware.com Chapter Breakdown) ──────────── */
const steps = [
  {
    num: '01',
    chapter: 'CH_01: OBSERVE',
    title: 'Traffic & Ingestion Tap',
    desc: 'Passively ingest live interface taps, raw PCAP/PCAPNG packet streams, and gateway session telemetry without inline latency.',
    tag: 'DATA_INGESTION',
    icon: Eye,
    words: 'eBPF / AF_PACKET'
  },
  {
    num: '02',
    chapter: 'CH_02: IDENTIFY',
    title: 'Protocol Demultiplexing',
    desc: 'Dissect IKEv1/IKEv2 handshakes, ESP/AH payload types, SPI indices, and negotiation transform proposals down to byte level.',
    tag: 'PROTOCOL_PARSING',
    icon: Search,
    words: 'IKEv1 / IKEv2 / ESP'
  },
  {
    num: '03',
    chapter: 'CH_03: ASSESS',
    title: 'Cryptographic Evaluation',
    desc: 'Verify cipher strength, PRF/hash integrity, key lengths, and Diffie-Hellman groups against NIST SP 800-77 and NSA CSfC baselines.',
    tag: 'CRYPTO_AUDIT',
    icon: Lock,
    words: 'NIST SP 800-77'
  },
  {
    num: '04',
    chapter: 'CH_04: EXPLAIN',
    title: 'Deterministic Rationale',
    desc: 'Synthesize explainable security justifications and CVSS-calibrated threat ratings with zero black-box inference.',
    tag: 'EXPLAINABLE_AI',
    icon: HelpCircle,
    words: 'CVSS v3.1 SCORING'
  },
  {
    num: '05',
    chapter: 'CH_05: SIMULATE',
    title: 'Digital Twin Modeling',
    desc: 'Simulate hypothetical cipher downgrades, rekey exhaustion windows, and sequence replay attacks in an isolated environment.',
    tag: 'DIGITAL_TWIN',
    icon: Activity,
    words: 'WHAT-IF ENGINE'
  },
  {
    num: '06',
    chapter: 'CH_06: SECURE',
    title: 'Vendor Hardening Playbooks',
    desc: 'Generate tailored Cisco, Fortinet, Juniper, and strongSwan remediation scripts, hardening playbooks, and compliance attestations.',
    tag: 'HARDENING_EXPORT',
    icon: CheckSquare,
    words: 'MULTI-VENDOR CLI'
  },
];

/* ── Capability Highlights ──────────────────────────────────────────── */
const capabilities = [
  { icon: Cpu,        label: 'XGBoost Traffic Classification',  sub: 'ML-driven IKE/ESP classification · 92.14% accuracy' },
  { icon: Zap,        label: 'Real-Time PCAP Dissection',       sub: 'Zero-latency protocol stream parser (<80ms)' },
  { icon: Database,   label: 'Analysis Persistence Vault',      sub: 'Tamper-evident SQLite/Supabase session ledger' },
  { icon: TrendingUp, label: 'CVSS Risk Score Engine',          sub: 'Automated cryptographic debt quantification' },
  { icon: GitBranch,  label: 'strongSwan 3-Node Testbed',       sub: 'Multi-VM tunnel orchestration & packet replay' },
  { icon: Globe,      label: 'Sovereign Air-Gapped Mode',       sub: 'Zero external cloud egress · 100% on-premise' },
  { icon: Shield,     label: 'NIST SP 800-77 Rev 1 Audit',      sub: 'Federal cryptographic policy enforcement' },
  { icon: Award,      label: 'FIPS 140-3 & NSA CSfC 4.1',       sub: 'Compliant cipher suite validation' },
];

/* ── Interactive Architecture FAQ Console Data ──────────────────────── */
const faqItems = [
  {
    id: 'airgap',
    question: 'How is zero-exfiltration air-gapped security guaranteed?',
    inLabel: 'GET /api/v2/audit/privacy-mode',
    answer: `PRIVCOMM is engineered for sovereign defence and critical infrastructure networks:
- Zero telemetry, packet bytes, or cryptographic parameters leave the local host or VPC.
- Dissection occurs entirely in-memory using localized TShark/libpcap and Scapy routines.
- Machine learning traffic classification runs offline on local XGBoost models without external API calls.
- Complies with NSA Commercial Solutions for Classified (CSfC) air-gapped deployment criteria.`
  },
  {
    id: 'weak-crypto',
    question: 'Why are 3DES and Diffie-Hellman Group 2 flagged as high risk?',
    inLabel: 'EVAL /crypto/primitive-deprecation',
    answer: `NIST SP 800-77 Rev 1 and NIST SP 800-131A explicitly deprecate legacy primitives:
- 3DES suffers from 64-bit block size vulnerability (Sweet32 attack, CVE-2016-2183), allowing birthday-bound plaintext recovery.
- DH Group 2 (1024-bit MODP) has estimated cracking costs within reach of state-tier actors (Logjam vulnerability).
- PRIVCOMM automatically recommends upgrading to AES-256-GCM and Curve25519 (DH Group 31) or ECP-384 (DH Group 20).`
  },
  {
    id: 'testbed',
    question: 'How does the strongSwan testbed orchestrate simulations?',
    inLabel: 'INIT /testbed/orchestration',
    answer: `The multi-node testbed executes realistic physical and virtualized VPN topologies:
- Initiator (192.168.56.10): Configured with swanctl, initiates IKE_SA_INIT and IKE_AUTH.
- Responder (192.168.56.20): Validates proposal transforms and creates CHILD_SA.
- Observer (192.168.56.30): Promiscuous interface tap capturing all ESP and IKE negotiation packets.
- Generates live PCAP captures fed directly into the analysis workspace for forensic inspection.`
  },
  {
    id: 'standards',
    question: 'What federal and enterprise standards are verified?',
    inLabel: 'SPEC /standards/compliance-matrix',
    answer: `PRIVCOMM continuously checks configurations against authoritative cryptographic baselines:
- NIST SP 800-77 Rev 1: Guide to IPsec VPNs.
- NSA CSfC 4.1: IPsec VPN Capability Package requirements.
- FIPS 140-3: Approved security algorithms and key generation rules.
- RFC 7296 (IKEv2), RFC 4303 (ESP), and RFC 8221 (Cryptographic Algorithm Implementation Requirements).`
  }
];

export default function Overview({ onStartAnalysis, onViewTelemetry }) {
  const [selectedFaq, setSelectedFaq] = useState(faqItems[0]);

  return (
    <div style={{ animation: 'fade-in 0.35s ease' }}>

      {/* ─── Hero: Two-Column Technical Manual Layout (makingsoftware.com style) ─── */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '40px',
        alignItems: 'start',
        marginBottom: '48px',
      }}>

        {/* LEFT COLUMN: Editorial Narrative & Specifications */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>

          {/* Large Retro Blueprint Header */}
          <h1 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'clamp(2.6rem, 5.5vw, 4.4rem)',
            fontWeight: 800,
            color: 'var(--accent-blue)',
            letterSpacing: '-0.03em',
            lineHeight: 1.02,
            marginBottom: '10px',
            textShadow: '2px 2px 0 rgba(37, 99, 235, 0.12)',
          }}>
            PRIVCOMM
          </h1>

          {/* Subtitle */}
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.86rem',
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
            marginBottom: '22px',
          }}>
            AUTONOMOUS IPSEC CRYPTOGRAPHIC INTELLIGENCE PLATFORM
          </div>

          {/* Editorial Serif Narrative with Drop-Cap */}
          <p className="drop-cap" style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '1.08rem',
            lineHeight: 1.82,
            color: 'var(--text-secondary)',
            marginBottom: '28px',
          }}>
            Transforming VPN packet captures, strongSwan runtime telemetry, and encrypted ESP payloads into
            deterministic compliance audits, CVSS risk scores, and vendor remediation playbooks — without a
            single byte of telemetry leaving your sovereign perimeter.
          </p>

          {/* Action Button Row */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '32px' }}>
            <button
              type="button"
              id="hero-launch-analyzer"
              className="btn btn-primary"
              onClick={onStartAnalysis}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                padding: '11px 22px',
                borderRadius: '4px',
              }}
            >
              <Zap size={15} />
              <span>Launch Live Analyzer</span>
              <ArrowRight size={15} />
            </button>
            <button
              type="button"
              id="hero-view-dashboard"
              className="btn btn-secondary"
              onClick={onViewTelemetry}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                padding: '11px 22px',
                borderRadius: '4px',
              }}
            >
              <span>Telemetry Dashboard</span>
              <ChevronRight size={15} />
            </button>
          </div>

          {/* Quick Technical Specs Table (makingsoftware.com style) */}
          <div style={{
            border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
            borderRadius: '4px',
            background: 'var(--bg-card)',
            padding: '16px 20px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.74rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            boxShadow: '0 2px 10px rgba(37,99,235,0.04)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-tertiary)' }}>CLASSIFICATION ACCURACY</span>
              <span className="leader-dots" />
              <strong style={{ color: 'var(--accent-blue)' }}>92.14% (XGBoost)</strong>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Interactive Architecture Blueprint Chassis */}
        <div className="blueprint-frame" style={{ position: 'static', alignSelf: 'center', padding: 0, overflow: 'hidden' }}>
          <PrivCommTunnelVisualizer showHeader={false} showTelemetry={false} />
        </div>
      </section>

      {/* ─── Dithered Pixel Divider (makingsoftware.com style) ──────── */}
      <div className="pixel-divider" />

      {/* ─── Six-Stage Pipeline: Table of Contents Style (makingsoftware.com style) ─── */}
      <section style={{ marginBottom: '64px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'clamp(1.5rem, 3vw, 2.2rem)',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: 0,
          }}>
            Platform Execution Pipeline
          </h2>
          <p style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '1rem',
            color: 'var(--text-secondary)',
            marginTop: '8px',
            maxWidth: '640px',
          }}>
            A deterministic and explainable seven-stage methodology engineered to systematically inspect, evaluate, and fortify enterprise IPsec architectures.
          </p>
        </div>

        {/* 2-Column Responsive Chapter Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '16px',
        }}>
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                id={`pipeline-step-${step.num}`}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '6px',
                  padding: '20px 22px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  transition: 'all 0.18s ease',
                  boxShadow: 'var(--shadow-sm)',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--accent-blue)';
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(37,99,235,0.08)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-default)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {/* Top header row with chapter and tag */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    color: 'var(--accent-blue)',
                    letterSpacing: '0.06em',
                  }}>
                    {step.chapter}
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.64rem',
                    padding: '2px 8px',
                    borderRadius: '3px',
                    border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
                    background: 'var(--accent-blue-dim)',
                    color: 'var(--accent-blue)',
                    fontWeight: 600,
                  }}>
                    {step.tag}
                  </span>
                </div>

                {/* Title + Dotted Leader Line */}
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <h3 style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1.05rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    margin: 0,
                  }}>
                    {step.title}
                  </h3>
                  <span className="leader-dots" />
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.68rem',
                    color: 'var(--text-tertiary)',
                    flexShrink: 0,
                  }}>
                    {step.words}
                  </span>
                </div>

                {/* Description */}
                <p style={{
                  fontFamily: 'var(--font-serif)',
                  fontSize: '0.92rem',
                  lineHeight: 1.68,
                  color: 'var(--text-secondary)',
                  margin: 0,
                }}>
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── Dithered Pixel Divider ─────────────────────────────────── */}
      <div className="pixel-divider" />

      {/* ─── Capabilities Matrix (Hardware Manual Style) ────────────── */}
      <section style={{ marginBottom: '64px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'clamp(1.5rem, 3vw, 2.2rem)',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: 0,
          }}>
            Cryptographic Assurance &amp; Engine Matrix
          </h2>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '14px',
        }}>
          {capabilities.map((cap, i) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.label}
                id={`capability-${i}`}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '14px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '4px',
                  padding: '16px 18px',
                  transition: 'all 0.16s ease',
                  boxShadow: 'var(--shadow-sm)',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--accent-blue)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-default)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '4px',
                  background: 'var(--accent-blue-dim)',
                  border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-blue)',
                  flexShrink: 0,
                  marginTop: '2px',
                }}>
                  <Icon size={16} strokeWidth={2} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '4px',
                    letterSpacing: '-0.01em',
                  }}>
                    {cap.label}
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.78rem',
                    color: 'var(--text-tertiary)',
                    lineHeight: 1.5,
                  }}>
                    {cap.sub}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── Dithered Pixel Divider ─────────────────────────────────── */}
      <div className="pixel-divider" />

      {/* ─── Interactive Architecture FAQ Console (makingsoftware.com style) ─── */}
      <section style={{ marginBottom: '64px' }}>
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'clamp(1.5rem, 3vw, 2.2rem)',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: 0,
          }}>
            Architecture Inquiries &amp; System Telemetry
          </h2>
          <p style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '1rem',
            color: 'var(--text-secondary)',
            marginTop: '8px',
          }}>
            Select an operational query on the left to inspect deterministic platform responses in the technical console.
          </p>
        </div>

        {/* Split FAQ: Question List on Left, Terminal I/O Card on Right */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          alignItems: 'stretch',
        }}>

          {/* Left: Selectable Question List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {faqItems.map((item) => {
              const isSelected = selectedFaq.id === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedFaq(item)}
                  style={{
                    textAlign: 'left',
                    padding: '16px 20px',
                    borderRadius: '4px',
                    border: isSelected
                      ? '1px solid var(--accent-blue)'
                      : '1px solid var(--border-default)',
                    background: isSelected
                      ? 'rgba(37, 99, 235, 0.06)'
                      : 'var(--bg-card)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    transition: 'all 0.16s ease',
                    boxShadow: isSelected
                      ? '0 2px 8px rgba(37,99,235,0.12)'
                      : 'var(--shadow-sm)'
                  }}
                >
                  <span style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.9rem',
                    fontWeight: isSelected ? 700 : 500,
                    color: isSelected ? 'var(--accent-blue)' : 'var(--text-primary)',
                  }}>
                    {item.question}
                  </span>
                  <ChevronRight
                    size={16}
                    style={{
                      color: isSelected ? 'var(--accent-blue)' : 'var(--text-tertiary)',
                      flexShrink: 0,
                      transform: isSelected ? 'translateX(2px)' : 'none',
                      transition: 'transform 0.15s ease',
                    }}
                  />
                </button>
              );
            })}
          </div>

          {/* Right: Terminal Console I/O Card (makingsoftware.com style) */}
          <div style={{
            background: '#0a0f1d',
            border: '1px solid #1e293b',
            borderRadius: '6px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 8px 30px rgba(0,0,0,0.25)',
          }}>
            {/* Terminal Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 16px',
              background: '#060a14',
              borderBottom: '1px solid #1e293b',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.72rem',
              color: '#94a3b8',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                <span style={{ color: '#38bdf8', marginLeft: '6px' }}>IN: [{selectedFaq.inLabel}]</span>
              </div>
              <span style={{ color: '#64748b' }}>TTY_01</span>
            </div>

            {/* Terminal Body */}
            <div style={{
              padding: '20px',
              flex: 1,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              lineHeight: 1.7,
              color: '#cbd5e1',
              whiteSpace: 'pre-line',
            }}>
              <div style={{ color: '#38bdf8', marginBottom: '12px' }}>
                OUT: RESPONSE [{selectedFaq.id.toUpperCase()}]
              </div>
              {selectedFaq.answer}
            </div>

            {/* Terminal Footer Bar */}
            <div style={{
              padding: '8px 16px',
              background: '#060a14',
              borderTop: '1px solid #1e293b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.68rem',
              fontFamily: 'var(--font-mono)',
              color: '#64748b',
            }}>
              <span>STATUS: 200 OK · ZERO_EXFILTRATION: VERIFIED</span>
              <span style={{ color: '#10b981' }}>● READY</span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Dithered Pixel Divider ─────────────────────────────────── */}
      <div className="pixel-divider" />

      {/* ─── Bottom CTA Box (makingsoftware.com style) ──────────────── */}
      <section
        id="overview-cta-banner"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-blueprint, rgba(37,99,235,0.3))',
          borderRadius: '6px',
          padding: '40px 32px',
          textAlign: 'center',
          boxShadow: '0 4px 20px rgba(37,99,235,0.06)',
          marginBottom: '32px',
        }}
      >
        <h2 style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'clamp(1.6rem, 3.2vw, 2.2rem)',
          fontWeight: 800,
          color: 'var(--text-primary)',
          letterSpacing: '-0.02em',
          marginBottom: '12px',
        }}>
          Begin Your IPsec Cryptographic Audit
        </h2>
        <p style={{
          fontFamily: 'var(--font-serif)',
          color: 'var(--text-secondary)',
          fontSize: '1rem',
          lineHeight: 1.7,
          maxWidth: '540px',
          margin: '0 auto 28px',
        }}>
          Upload a raw packet capture (.pcap, .pcapng) or connect to the strongSwan multi-node testbed to start real-time protocol dissection.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button
            type="button"
            id="cta-launch-analyzer"
            className="btn btn-primary"
            onClick={onStartAnalysis}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              padding: '11px 26px',
              borderRadius: '4px',
            }}
          >
            <Zap size={16} />
            <span>Launch Live Analyzer</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </section>
    </div>
  );
}
