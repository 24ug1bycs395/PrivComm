import React from 'react';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';

export default function ThreatMatrixTab() {
  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', animation: 'fade-in 0.35s ease' }}>
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '5px 14px', borderRadius: '9999px',
          background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)',
          color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)',
          fontSize: '0.74rem', fontWeight: 600, marginBottom: '12px'
        }}>
          <Shield size={14} />
          <span>SECURITY RISK MODELING</span>
        </div>
        <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
          3x3 Threat &amp; Likelihood Matrix
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Deterministic severity-by-likelihood scoring matrix based on empirical IPsec vulnerability vectors and cryptanalytic margins.
        </p>
      </div>

      <div className="card-glass" style={{ marginBottom: '28px' }}>
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
          Threat Matrix Grid
        </h4>
        <div className="matrix-grid-3x3" style={{ maxWidth: '640px', margin: '0 auto' }}>
          <div></div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 600 }}>Low Impact</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 600 }}>Med Impact</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 600 }}>High Impact</div>

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>High L-hood</div>
          <div className="matrix-cell matrix-med">Medium (50)</div>
          <div className="matrix-cell matrix-high">High (75)</div>
          <div className="matrix-cell matrix-crit">Critical (100)</div>

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>Med L-hood</div>
          <div className="matrix-cell matrix-low">Low (25)</div>
          <div className="matrix-cell matrix-med">Medium (50)</div>
          <div className="matrix-cell matrix-high">High (75)</div>

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>Low L-hood</div>
          <div className="matrix-cell matrix-low">Low (10)</div>
          <div className="matrix-cell matrix-low">Low (25)</div>
          <div className="matrix-cell matrix-med">Medium (50)</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        <div className="card-glass">
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <AlertTriangle size={18} />
            <span>High / Critical Severity Triggers</span>
          </h4>
          <ul style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', paddingLeft: '20px', lineHeight: 1.8 }}>
            <li>Single DES / 3DES-CBC ciphers (Sweet32 vulnerability)</li>
            <li>MD5 or SHA-1 integrity hashing (RFC 8221 Deprecated)</li>
            <li>Diffie-Hellman Group 1, 2, or 5 (&lt;2048-bit MODP)</li>
            <li>IKEv1 Aggressive Mode with plaintext PSK hash</li>
          </ul>
        </div>

        <div className="card-glass">
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <CheckCircle size={18} />
            <span>Secure / Compliant Baselines</span>
          </h4>
          <ul style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', paddingLeft: '20px', lineHeight: 1.8 }}>
            <li>AES-256-GCM / ChaCha20-Poly1305 AEAD suites</li>
            <li>HMAC-SHA2-256 / SHA2-384 / SHA2-512 PRF algorithms</li>
            <li>DH Group 14 (2048-bit), Group 19 (ECP-256), Group 20</li>
            <li>IKEv2 with Perfect Forward Secrecy (PFS) enforced</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
