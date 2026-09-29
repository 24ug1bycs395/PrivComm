import React, { useState } from 'react';
import {
  BookOpen,
  FileCode,
  Layers,
  Cpu,
  Shield,
  Server,
  Activity,
  Zap,
  Lock,
  Download,
  ExternalLink,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Database,
  Search
} from 'lucide-react';

export default function TechnicalDocsTab() {
  const [activeSection, setActiveSection] = useState('architecture');
  const [searchQuery, setSearchQuery] = useState('');

  const sections = [
    { id: 'overview', title: '1. Executive Overview & Architecture', icon: BookOpen },
    { id: 'architecture', title: '2. System Architecture & Pipeline', icon: Layers },
    { id: 'dissection', title: '3. Ingestion & TShark Dissection Engine', icon: Activity },
    { id: 'ml-engine', title: '4. XGBoost Flow Classifier (28 Features)', icon: Cpu },
    { id: 'security-policy', title: '5. NIST SP 800-77 Policy Audit Engine', icon: Shield },
    { id: 'anomaly-engine', title: '6. Behavioral Anomaly & Drift Engine', icon: Zap },
    { id: 'pqc-engine', title: '7. Post-Quantum Cryptography Readiness', icon: Lock },
    { id: 'testbed-arch', title: '8. Testbed Orchestration & K8s Roadmap', icon: Server },
    { id: 'api-reference', title: '9. Complete REST API Reference', icon: FileCode },
  ];

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px', minHeight: 'calc(100vh - 120px)' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(56, 189, 248, 0.05) 100%)',
        border: '1px solid var(--border-default)',
        borderRadius: '16px',
        padding: '24px 28px',
        marginBottom: '24px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        <div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Technical Documentation & System Specification
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: '6px 0 0 0', maxWidth: '750px' }}>
            Comprehensive architectural specifications, machine learning schemas, cryptographic compliance rules, and API reference for the Privcomm IPsec VPN Intelligence Platform.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href="/docs/TECHNICAL_DOCUMENTATION.md"
            download="TECHNICAL_DOCUMENTATION.md"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              padding: '8px 14px',
              borderRadius: '8px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textDecoration: 'none',
              cursor: 'pointer'
            }}
          >
            <Download size={14} /> Download Raw Markdown
          </a>
        </div>
      </div>

      {/* Main Grid: Sidebar + Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px' }} className="docs-grid-layout">
        
        {/* Navigation Sidebar */}
        <aside style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '16px',
          height: 'fit-content',
          position: 'sticky',
          top: '90px'
        }}>
          <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
            Documentation Index
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {sections.map((sec) => {
              const Icon = sec.icon;
              const isActive = activeSection === sec.id;
              return (
                <button
                  key={sec.id}
                  type="button"
                  onClick={() => setActiveSection(sec.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                    color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 400,
                    fontSize: '0.78rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Icon size={14} style={{ flexShrink: 0 }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{sec.title}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Content Viewer */}
        <main style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '28px 32px',
          color: 'var(--text-primary)',
          fontSize: '0.88rem',
          lineHeight: '1.7'
        }}>

          {/* Section 1: Overview */}
          {activeSection === 'overview' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                1. Executive Overview & System Architecture
              </h2>
              <p>
                <strong>Privcomm</strong> is a production-grade, zero-trust IPsec VPN Intelligence and Traffic Classification platform engineered to dissect, audit, classify, and secure encrypted site-to-site and remote-access VPN infrastructure in real time.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', margin: '20px 0' }}>
                <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <strong style={{ color: 'var(--accent-cyan)', display: 'block', marginBottom: '4px' }}>Deep Packet Dissection</strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Extracts unencrypted IKEv1/IKEv2 handshake proposals, ESP security associations, SPI parameters, and tunnel modes without breaching encrypted boundaries.</span>
                </div>
                <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <strong style={{ color: 'var(--accent-cyan)', display: 'block', marginBottom: '4px' }}>AI Traffic Classification</strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Trained XGBoost multi-class classifier using 28 statistical flow features to identify 14 tunneled traffic types (Chat, VoIP, P2P, Streaming, etc.).</span>
                </div>
                <div style={{ padding: '14px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <strong style={{ color: 'var(--accent-cyan)', display: 'block', marginBottom: '4px' }}>NIST Compliance Audit</strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Automated compliance evaluation against NIST SP 800-77 Rev 1, FIPS 140-3, and Post-Quantum hybrid transition frameworks.</span>
                </div>
              </div>
            </div>
          )}

          {/* Section 2: Architecture */}
          {activeSection === 'architecture' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                2. System Architecture & End-to-End Pipeline
              </h2>
              <p>
                The architecture decouples packet ingestion, deep protocol dissection, machine learning classification, and compliance auditing into deterministic, asynchronous pipelines.
              </p>

              <pre style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '16px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem',
                overflowX: 'auto',
                color: '#38bdf8'
              }}>
{`PCAP / Live VM Stream (UDP 500 / 4500 / ESP)
      │
      ▼
[ Ingestion & Packet Dissection Engine ]
  ├── TShark / Scapy Structured Dissection
  ├── IKEv1/IKEv2 Handshake Parsing (SPI, Ciphers, DH Groups, PFS)
  └── Flow Statistical Feature Extraction (28 features)
      │
      ├───────────────────────────────────────────┐
      ▼                                           ▼
[ XGBoost Classifier (ML Engine) ]     [ Security Policy Audit Engine ]
  ├── 28-dimensional Feature Matrix        ├── NIST SP 800-77 Rulebook (POL-01..06)
  ├── 14 Encrypted Traffic Classes         ├── Risk Scoring & Penalty Model (0-100)
  └── Multiclass Confidence Softmax        └── Post-Quantum Readiness Matrix
      │                                           │
      └─────────────────────┬─────────────────────┘
                            ▼
               [ Report & Telemetry Core ]
                 ├── Unified JSON Assessment
                 ├── Executive PDF/HTML Reports
                 └── React Web Visualization Engine`}
              </pre>
            </div>
          )}

          {/* Section 3: Dissection */}
          {activeSection === 'dissection' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                3. Ingestion & TShark Dissection Engine
              </h2>
              <p>
                <code>analyzer/pcap_ingestion.py</code> and <code>analyzer/tshark.py</code> ingest PCAP/PCAPNG capture files. TShark is utilized for high-throughput structured dissection with automatic Scapy fallback.
              </p>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                <li><strong>Observable Parameters:</strong> IKE version, Initiator/Responder SPIs, Transform proposals (Encryption, Integrity, PRF, DH Groups), Exchange types (IKE_SA_INIT, IKE_AUTH), and Encapsulation Mode (Tunnel vs Transport).</li>
                <li><strong>Zero-Exfiltration Guarantee:</strong> Payload content within ESP segments remains strictly encrypted. Inspection relies exclusively on observable cryptographic negotiation headers and flow timing statistics.</li>
              </ul>
            </div>
          )}

          {/* Section 4: ML Engine */}
          {activeSection === 'ml-engine' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                4. XGBoost Flow Classifier (28 Statistical Features)
              </h2>
              <p>
                The ML subsystem classifies encrypted flows into 14 distinct application classes without decrypting packets.
              </p>
              <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.74rem', marginBottom: '14px' }}>
                <code>duration, total_fiat, total_biat, min_fiat, min_biat, max_fiat, max_biat, mean_fiat, mean_biat, flowPktsPerSecond, flowBytesPerSecond, min_flowiat, max_flowiat, mean_flowiat, std_flowiat, min_active, mean_active, max_active, std_active, min_idle, mean_idle, max_idle, std_idle, bytes_per_pkt, fiat_biat_ratio, log_duration, log_bytes_sec, log_pkts_sec</code>
              </div>
              <p><strong>Training Details:</strong> Stratified 70/15/15 split on consolidated VPN flow dataset. Model parameters: <code>n_estimators=400</code>, <code>max_depth=8</code>, <code>learning_rate=0.08</code>, <code>objective=multi:softprob</code>.</p>
            </div>
          )}

          {/* Section 5: Security Policy */}
          {activeSection === 'security-policy' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                5. NIST SP 800-77 Policy Audit Engine
              </h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', marginTop: '12px' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Policy ID</th>
                    <th style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Requirement</th>
                    <th style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Standard Benchmark</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-01</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Protocol Modernity</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Mandates IKEv2 (RFC 7296); flags legacy IKEv1.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-02</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Encryption Strength</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Enforces AES-GCM AEAD; flags 3DES/DES.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-03</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Diffie-Hellman Group</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Rejects DH Groups &lt; 14; prefers Group 19 (ECDH P-256).</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-04</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Perfect Forward Secrecy</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Mandates ephemeral Phase 2 re-keying.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-05</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Integrity Verification</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Rejects broken MD5 and SHA-1 hashing.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}><code>POL-06</code></td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Encapsulation Mode</td>
                    <td style={{ padding: '8px 12px', border: '1px solid var(--border-subtle)' }}>Prefers Tunnel Mode over Transport Mode for inner IP protection.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Section 6: Anomaly Engine */}
          {activeSection === 'anomaly-engine' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                6. Behavioral Anomaly & Drift Engine
              </h2>
              <p>
                Monitors live VPN telemetry for statistical drift against historical baselines. Detects replay attacks, abnormal packet burst anomalies, high entropy exfiltration, and out-of-sequence sequence numbers (ESN).
              </p>
            </div>
          )}

          {/* Section 7: Post-Quantum */}
          {activeSection === 'pqc-engine' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                7. Post-Quantum Cryptography Readiness
              </h2>
              <p>
                Evaluates transition readiness toward Post-Quantum hybrid key exchange schemes (IETF RFC 9370 & NIST ML-KEM/Kyber). Identifies tunnels vulnerable to "Harvest Now, Decrypt Later" (HNDL) adversaries.
              </p>
            </div>
          )}

          {/* Section 8: Testbed & Roadmap */}
          {activeSection === 'testbed-arch' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                8. Multi-Node Docker Testbed & Orchestration Roadmap
              </h2>
              <p>
                The Privcomm Testbed provisions automated IPsec scenarios between isolated nodes (<strong>Initiator: 192.168.56.10</strong>, <strong>Responder: 192.168.56.20</strong>, <strong>Observer/Sentinel: 192.168.56.30</strong>).
              </p>
              <div style={{ padding: '14px', background: 'rgba(56, 189, 248, 0.08)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.22)', margin: '14px 0' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>Enterprise Deployment Roadmap:</strong> Production scaling encapsulates node images in Kubernetes (K8s) pods, managing automated capture pipelines with eBPF/tshark sidecars across AWS, GCP, and Azure.
              </div>
            </div>
          )}

          {/* Section 9: API Reference */}
          {activeSection === 'api-reference' && (
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', marginTop: 0 }}>
                9. Complete REST API Reference
              </h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', marginTop: '12px' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: '8px 10px', border: '1px solid var(--border-subtle)' }}>Method</th>
                    <th style={{ padding: '8px 10px', border: '1px solid var(--border-subtle)' }}>Endpoint</th>
                    <th style={{ padding: '8px 10px', border: '1px solid var(--border-subtle)' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)', color: '#38bdf8', fontWeight: 700 }}>POST</td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}><code>/analyze/protocol</code></td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}>Upload and inspect raw PCAP/PCAPNG binary file.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)', color: '#34d399', fontWeight: 700 }}>GET</td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}><code>/analyze/sample</code></td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}>Retrieve compliant IKEv2 AES-GCM assessment.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)', color: '#34d399', fontWeight: 700 }}>GET</td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}><code>/analyze/sample-weak</code></td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}>Retrieve non-compliant legacy IKEv1 3DES sample.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)', color: '#34d399', fontWeight: 700 }}>GET</td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}><code>/api/history</code></td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}>Query list of historical PCAP audits.</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)', color: '#34d399', fontWeight: 700 }}>GET</td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}><code>/reports/download-html</code></td>
                    <td style={{ padding: '6px 10px', border: '1px solid var(--border-subtle)' }}>Download standalone executive audit report.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
