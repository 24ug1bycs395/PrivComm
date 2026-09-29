import React from 'react';
import { FileCheck, Award, Check } from 'lucide-react';

export default function ComplianceTab() {
  const standards = [
    {
      title: 'NIST Special Publication 800-77 Rev 1',
      sub: 'Guide to IPsec VPNs',
      desc: 'Mandates minimum 128-bit security margin, AES-GCM AEAD transforms, Diffie-Hellman Group 14+ or Curve25519, and SHA-256 integrity algorithms.',
      status: 'FULLY VALIDATED'
    },
    {
      title: 'NSA Commercial Solutions for Classified (CSfC)',
      sub: 'VPN Capability Package v4.1',
      desc: 'Requires dual-tunnel architecture with Outer/Inner encryption, Suite-B cryptography (AES-256, ECDSA P-384, SHA-384), and non-reusable ephemeral keys.',
      status: 'AUDIT COMPLIANT'
    },
    {
      title: 'RFC 7296 & RFC 8221 Cryptographic Baselines',
      sub: 'IETF IPsec Standards Baseline',
      desc: 'Formally deprecates single DES, 3DES-CBC, MD5, and SHA-1 transforms for all modern security associations.',
      status: 'ENFORCED'
    }
  ];

  return (
    <div className="record-page" style={{ maxWidth: '1000px', margin: '0 auto', animation: 'fade-in 0.35s ease' }}>
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '5px 14px', borderRadius: '9999px',
          background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)',
          color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)',
          fontSize: '0.74rem', fontWeight: 600, marginBottom: '12px'
        }}>
          <FileCheck size={14} />
          <span>GOVERNMENT &amp; ENTERPRISE COMPLIANCE</span>
        </div>
        <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
          Cryptographic Standards &amp; Frameworks
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Deterministic baseline evaluation rules evaluated during raw PCAP stream ingestion.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {standards.map((std, i) => (
          <div key={i} className="card-glass" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '20px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                <Award size={20} color="var(--accent-blue)" />
                <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>{std.title}</h4>
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.76rem', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '8px' }}>
                {std.sub}
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {std.desc}
              </p>
            </div>
            <span className="status-badge compliant" style={{ flexShrink: 0 }}>
              <Check size={12} style={{ display: 'inline', marginRight: '4px' }} />
              {std.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
