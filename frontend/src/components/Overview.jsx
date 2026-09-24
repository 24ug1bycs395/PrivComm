import React from 'react';
import { Shield, CheckCircle, ArrowRight, Eye, Search, Lock, HelpCircle, Activity, CheckSquare } from 'lucide-react';
import TopologyCanvas from './TopologyCanvas';

export default function Overview({ onStartAnalysis }) {
  const steps = [
    { num: '01', title: 'Observe', desc: 'Ingest and dissect live interface taps, raw PCAP/PCAPNG streams, and gateway session telemetry.', tag: 'Data Ingestion', icon: Eye },
    { num: '02', title: 'Identify', desc: 'Demultiplex IKEv1/IKEv2 handshakes, ESP/AH payload types, SPI indices, and negotiation transforms.', tag: 'Protocol Parsing', icon: Search },
    { num: '03', title: 'Assess', desc: 'Validate cipher resilience, PRF/hash integrity, key lengths, and Diffie-Hellman group parameters.', tag: 'Crypto Evaluation', icon: Lock },
    { num: '04', title: 'Explain', desc: 'Generate transparent, deterministic security rationale without black-box ML obfuscation.', tag: 'Explainable AI', icon: HelpCircle },
    { num: '05', title: 'Simulate', desc: 'Model hypothetical cipher downgrades, rekey exhaustion events, and replay vulnerability postures.', tag: 'Digital Twin', icon: Activity },
    { num: '06', title: 'Secure', desc: 'Synthesize actionable remediation playbooks, cryptographic hardening scripts, and audit reports.', tag: 'Hardening', icon: CheckSquare },
  ];

  return (
    <div>
      {/* Hero Section */}
      <div style={{ textAlign: 'center', maxWidth: '840px', margin: '0 auto 48px auto' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '9999px', background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.25)', color: '#38bdf8', fontFamily: 'JetBrains Mono', fontSize: '0.74rem', fontWeight: 600, marginBottom: '18px' }}>
          <span>FEDERAL & ENTERPRISE SECURITY FRAMEWORK</span>
          <span>/</span>
          <span>NIST SP 800-77 &bull; NSA CSfC</span>
        </div>

        <h1 style={{ fontSize: '2.8rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em', lineHeight: 1.15, marginBottom: '18px' }}>
          Cyber Sentinel Intelligence
        </h1>

        <p style={{ fontSize: '1.1rem', color: '#94a3b8', lineHeight: 1.7, marginBottom: '28px' }}>
          Transform VPN packet captures, logs, configurations, and encrypted traffic into actionable security intelligence, risk assessments, and explainable recommendations.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '14px' }}>
          <button type="button" className="btn btn-primary" onClick={onStartAnalysis}>
            <span>Launch Live Analyzer</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Network Topology Visualizer */}
      <div style={{ marginBottom: '56px' }}>
        <TopologyCanvas />
      </div>

      {/* Seven-Stage Execution Pipeline */}
      <div style={{ marginBottom: '40px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.74rem', color: '#38bdf8', letterSpacing: '0.1em', fontWeight: 700 }}>
            DETERMINISTIC METHODOLOGY
          </span>
          <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', marginTop: '6px' }}>
            Six-Stage Intelligence Pipeline
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.num} className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'JetBrains Mono', fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8' }}>
                    {step.num}
                  </span>
                  <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={18} />
                  </div>
                </div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{step.title}</h4>
                <p style={{ fontSize: '0.86rem', color: '#94a3b8', lineHeight: 1.6 }}>{step.desc}</p>
                <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.7rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.08)', padding: '3px 8px', borderRadius: '4px', alignSelf: 'flex-start' }}>
                  {step.tag}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
