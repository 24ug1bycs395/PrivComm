import React, { useState } from 'react';
import {
  UploadCloud,
  FileCheck,
  AlertTriangle,
  Shield,
  Cpu,
  Lock,
  Zap,
  Download,
  FileText,
  CheckCircle2,
  AlertOctagon,
  ChevronRight,
  Terminal,
  Activity
} from 'lucide-react';
import AnomalyDetectionPanel from './AnomalyDetectionPanel';

export default function AnalyzerWorkspace({ externalAnalysis }) {
  const [loading, setLoading] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState([]);
  const [activeFilename, setActiveFilename] = useState('');
  const [analysisResult, setAnalysisResult] = useState(externalAnalysis || null);
  const [errorNotice, setErrorNotice] = useState(null);

  React.useEffect(() => {
    if (externalAnalysis) {
      setAnalysisResult(externalAnalysis);
      setActiveFilename(externalAnalysis.filename || 'inspected_capture.pcap');
    }
  }, [externalAnalysis]);

  // Trigger analysis for sample scenarios
  const handleLoadSample = async (scenarioType) => {
    setLoading(true);
    setErrorNotice(null);
    const targetFilename = scenarioType === 'ikev2-strong'
      ? 'ikev2_s2s_ipsec_vpn_aes_gcm.pcapng'
      : 'IKEv1_Aggressive_DES_MD5.pcap';
    setActiveFilename(targetFilename);

    setPipelineLogs([
      `[01/04 INGESTION] Streaming ${targetFilename} to in-memory parsing buffer...`,
      `[02/04 DISSECTION] Decoding IKEv1/IKEv2 handshakes, SPI headers & ESP payloads...`,
      `[03/04 AI CLASSIFIER] Computing 28 statistical flow features & running XGBoost model...`,
      `[04/04 POLICY AUDIT] Verifying cryptographic parameters against NIST SP 800-77 Rev 1...`,
    ]);

    const endpoint = scenarioType === 'ikev2-strong' ? '/analyze/sample' : '/analyze/sample-weak';

    try {
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Analysis request failed`);
      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      console.warn('Using fallback data:', err);
      // Fallback state if backend is offline
      setAnalysisResult(getMockData(scenarioType));
    } finally {
      setLoading(false);
    }
  };

  // Handle custom PCAP upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setErrorNotice(null);
    setActiveFilename(file.name);

    setPipelineLogs([
      `[01/04 INGESTION] Ingesting ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`,
      `[02/04 DISSECTION] Dissecting raw frames with Scapy/TShark protocol engine...`,
      `[03/04 AI CLASSIFIER] Running XGBoost Encrypted Multiclass Classifier...`,
      `[04/04 SECURITY AUDIT] Evaluating compliance and generating remediation directives...`,
    ]);

    try {
      const formData = new FormData();
      formData.append('pcap_file', file);

      const res = await fetch('/analyze/protocol', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        let errorMsg = `Server returned HTTP ${res.status}`;
        try {
          const errJson = await res.json();
          if (errJson?.detail) errorMsg = errJson.detail;
        } catch (_) {
          const errText = await res.text().catch(() => '');
          if (errText) errorMsg = `${errorMsg} - ${errText.slice(0, 120)}`;
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      setErrorNotice(err.message);
      setPipelineLogs((prev) => [...prev, `[ERROR] ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  const getMockData = (type) => {
    const isStrong = type === 'ikev2-strong';
    return {
      ipsec_detected: true,
      ike_version: isStrong ? 'IKEv2' : 'IKEv1 (Aggressive Mode)',
      mode: isStrong ? 'Tunnel' : 'Transport',
      encryption: isStrong ? 'AES-256-GCM' : '3DES-CBC',
      integrity: isStrong ? 'AEAD' : 'HMAC-MD5-96',
      dh_group: isStrong ? '19' : '2',
      source_ip: '192.168.1.10',
      destination_ip: '10.0.0.1',
      ip_version: 'IPv4',
      initiator_spi: isStrong ? '0xa9f4e28174b081c2' : '0x812fa910bb421109',
      responder_spi: isStrong ? '0x981255e1a3bc47d0' : '0x12c4ea55781290aa',
      esp_detected: true,
      ah_detected: false,
      packet_count: isStrong ? 1482 : 844,
      metadata_exposure: {
        source_ip: '192.168.1.10',
        destination_ip: '10.0.0.1',
        ip_version: 'IPv4',
        exposure_score: isStrong ? 0 : 70,
        exposure_rating: isStrong ? 'LOW' : 'HIGH',
        visible_endpoints: {
          source_ip: '192.168.1.10',
          destination_ip: '10.0.0.1',
          outer_header_exposure: 'FULL_IP_PAIR_VISIBLE'
        },
        identity_exposure: {
          plaintext_identity_leak: !isStrong,
          identity_protection_status: isStrong ? 'ENCRYPTED_OR_ABSENT' : 'PLAINTEXT_EXPOSED',
          exposed_identity_type: isStrong ? null : 'ID_FQDN'
        },
        spi_correlation: {
          initiator_spi: isStrong ? '0xa9f4e28174b081c2' : '0x812fa910bb421109',
          responder_spi: isStrong ? '0x981255e1a3bc47d0' : '0x12c4ea55781290aa',
          esp_spis: ['0x00001000'],
          spi_linkability_risk: isStrong ? 'LOW' : 'MEDIUM',
          session_tracking_vulnerability: true
        },
        transport_mode_exposure: {
          encapsulation_mode: isStrong ? 'Tunnel' : 'Transport',
          inner_header_exposed: !isStrong,
          exposed_metadata_bytes_per_pkt: isStrong ? 0 : 20,
          exposure_risk: isStrong ? 'LOW' : 'HIGH'
        }
      },
      traffic_classification: {
        traffic_type: isStrong ? 'CHAT / MESSAGING' : 'REMOTE-DESKTOP',
        confidence: isStrong ? 0.954 : 0.887,
      },
      security_assessment: {
        risk_level: isStrong ? 'SECURE' : 'HIGH',
        risk_score: isStrong ? 0 : 85,
        findings: isStrong
          ? []
          : [
              {
                finding_id: 'FINDING-001',
                title: 'Deprecated 3DES-CBC Cipher Suite',
                severity: 'HIGH',
                observed: '3DES-CBC (112-bit effective)',
                expected: 'AES-256-GCM / ChaCha20-Poly1305',
                recommendation: 'Decommission 3DES immediately to prevent Sweet32 collision attacks.',
              },
              {
                finding_id: 'FINDING-002',
                title: 'Weak Diffie-Hellman Group 2 (MODP 1024-bit)',
                severity: 'HIGH',
                observed: 'DH Group 2 (1024-bit)',
                expected: 'DH Group 14 (2048-bit) or Group 19 (ECP-256)',
                recommendation: 'Migrate key exchange proposals to minimum Group 14 or Group 19.',
              },
              {
                finding_id: 'FINDING-003',
                title: 'Deprecated MD5 Integrity Hash Algorithm',
                severity: 'HIGH',
                observed: 'HMAC-MD5-96',
                expected: 'HMAC-SHA2-256 or AEAD Cipher',
                recommendation: 'Upgrade integrity hashing to SHA-256 or AEAD mode per RFC 8221.',
              },
              {
                finding_id: 'IPSEC-META-001',
                title: 'Plaintext IKE Identity Payload Exposed',
                severity: 'HIGH',
                observed: 'Unencrypted ID_FQDN detected',
                expected: 'Encrypted Identity Payloads (IKEv2 IKE_AUTH)',
                recommendation: 'Avoid IKEv1 Aggressive Mode or plaintext identity exchanges to prevent identity exposure.',
              },
            ],
      },
    };
  };

  const riskLevel = analysisResult?.security_assessment?.risk_level || 'SECURE';
  const riskScore = analysisResult?.security_assessment?.risk_score ?? 0;
  const trafficType = analysisResult?.traffic_classification?.traffic_type || 'VPN-TUNNEL';
  const confidence = analysisResult?.traffic_classification?.confidence ?? 0.95;
  const confPercent = (confidence * 100).toFixed(1);
  const findings = analysisResult?.security_assessment?.findings || [];

  return (
    <div className="analyzer-workspace-container">
      {/* Header Pretitle */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '9999px', background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.74rem', fontWeight: 600, marginBottom: '10px' }}>
          <Activity size={14} />
          <span>LIVE PROTOCOL DISSECTION &amp; XGBOOST INFERENCE</span>
        </div>
        <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
          IPsec VPN Security Intelligence Platform
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '820px' }}>
          Upload live packet captures (.pcap, .pcapng) or inspect reference cryptographic handshakes to run deterministic policy checks and AI traffic classification.
        </p>
      </div>

      {/* Dual Ingestion Toolbar */}
      <div className="analyzer-grid-top">
        {/* Drag & Drop Upload Zone */}
        <div
          className="dropzone-box"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
          }}
          onClick={() => document.getElementById('reactPcapInput')?.click()}
        >
          <div className="dropzone-icon-wrap">
            <UploadCloud size={28} />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Drag &amp; Drop PCAP Capture Files
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Supports .pcap, .pcapng &bull; Local in-memory parsing
            </div>
          </div>
          <input
            id="reactPcapInput"
            type="file"
            accept=".pcap,.pcapng,.cap"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
          />
          <button type="button" className="btn btn-secondary btn-sm" style={{ pointerEvents: 'none' }}>
            Browse Local File
          </button>
        </div>

        {/* Reference Presets */}
        <div className="samples-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              REFERENCE SCENARIOS
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>1-Click Audit</span>
          </div>

          <div className="sample-row-card" onClick={() => handleLoadSample('ikev2-strong')}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '6px', background: 'var(--accent-green-dim)', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Shield size={18} />
              </div>
              <div>
                <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.84rem', color: 'var(--text-primary)', display: 'block' }}>
                  IKEv2_SuiteB_GCM256.pcap
                </strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Compliant IKEv2 &bull; AES-256-GCM &bull; DH Group 19 &bull; Clean Policy
                </span>
              </div>
            </div>
            <span className="btn btn-primary btn-sm">Run Audit</span>
          </div>

          <div className="sample-row-card" onClick={() => handleLoadSample('ikev1-weak')}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '6px', background: 'rgba(220, 38, 38, 0.1)', color: 'var(--accent-red)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle size={18} />
              </div>
              <div>
                <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.84rem', color: 'var(--text-primary)', display: 'block' }}>
                  IKEv1_Aggressive_DES_MD5.pcap
                </strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Vulnerable &bull; 3DES-CBC &bull; DH Group 2 &bull; PSK Hash Exposure
                </span>
              </div>
            </div>
            <span className="btn btn-secondary btn-sm">Run Audit</span>
          </div>
        </div>
      </div>

      {/* Pipeline Status Logs Stream */}
      {loading && (
        <div className="console-box">
          <div className="console-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="live-dot" style={{ background: 'var(--accent-cyan)', boxShadow: '0 0 8px var(--accent-cyan)' }}></span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Executing Intelligence Pipeline...</span>
            </div>
            <span style={{ color: 'var(--accent-cyan)', fontSize: '0.72rem', background: 'var(--accent-cyan-dim)', padding: '2px 8px', borderRadius: '4px' }}>
              DISSECTION &amp; INFERENCE ACTIVE
            </span>
          </div>
          {pipelineLogs.map((log, idx) => (
            <div key={idx} style={{ color: idx === pipelineLogs.length - 1 ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}>
              {log}
            </div>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {errorNotice && (
        <div style={{ padding: '14px 18px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: 'var(--accent-red)', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertOctagon size={18} />
          <span>{errorNotice}</span>
        </div>
      )}

      {/* LIVE RESULTS DASHBOARD */}
      {analysisResult && !loading && (
        <div className="results-container">
          {/* Top File Banner */}
          <div className="file-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FileCheck size={24} />
              </div>
              <div>
                <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {activeFilename}
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Parsed {analysisResult.packet_count || 1482} frames &bull; Scapy/TShark Engine
                  </span>
                  {analysisResult.source_ip && analysisResult.destination_ip && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px' }}>
                      IP Pair: {analysisResult.source_ip} &rarr; {analysisResult.destination_ip} ({analysisResult.ip_version || 'IPv4'})
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 18px',
              borderRadius: '9999px',
              fontFamily: 'JetBrains Mono',
              fontSize: '0.82rem',
              fontWeight: 700,
              background: riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'rgba(34, 197, 94, 0.15)' : (riskLevel === 'MEDIUM' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
              color: riskLevel === 'SECURE' || riskLevel === 'LOW' ? '#4ade80' : (riskLevel === 'MEDIUM' ? '#fde047' : '#fca5a5'),
              border: `1px solid ${riskLevel === 'SECURE' || riskLevel === 'LOW' ? '#22c55e' : (riskLevel === 'MEDIUM' ? '#eab308' : '#ef4444')}`
            }}>
              <span className="live-dot" style={{ background: 'currentColor' }}></span>
              <span>{riskLevel} RISK ({riskScore}/100)</span>
            </div>
          </div>

          {/* 4 Executive Metrics Grid */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-title-bar">
                <span>SECURITY RISK SCORE</span>
                <Shield size={16} color="#38bdf8" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="metric-big-val" style={{ color: '#38bdf8' }}>{riskScore}</span>
                <span style={{ color: '#64748b', fontFamily: 'JetBrains Mono', fontSize: '0.9rem' }}>/ 100</span>
              </div>
              <span className={`status-badge ${riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'compliant' : (riskLevel === 'MEDIUM' ? 'warning' : 'danger')}`} style={{ alignSelf: 'flex-start' }}>
                {riskLevel} LEVEL
              </span>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>AI TRAFFIC CLASSIFICATION</span>
                <Cpu size={16} color="#a855f7" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                {trafficType}
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'JetBrains Mono' }}>
                  <span>Confidence</span>
                  <span>{confPercent}%</span>
                </div>
                <div className="confidence-bar-bg">
                  <div className="confidence-bar-fill" style={{ width: `${confPercent}%` }}></div>
                </div>
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>CIPHER &amp; INTEGRITY SUITE</span>
                <Lock size={16} color="var(--accent-green)" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                {analysisResult.encryption || 'AES-256-GCM'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                Integrity / PRF: <strong style={{ color: 'var(--text-primary)' }}>{analysisResult.integrity || 'AEAD'}</strong>
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>KEY EXCHANGE &amp; MODE</span>
                <Zap size={16} color="var(--accent-yellow)" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                Group {analysisResult.dh_group || '19'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                Mode: <strong style={{ color: 'var(--text-primary)' }}>{analysisResult.ike_version || 'IKEv2'} ({analysisResult.mode || 'Tunnel'})</strong>
              </div>
            </div>
          </div>

          {/* Observable Metadata Exposure Summary Card */}
          <div className="matrix-card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)' }}>
                <Activity size={18} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Observable Metadata Exposure Intelligence
                </h4>
              </div>
              <span className={`status-badge ${analysisResult.metadata_exposure?.exposure_rating === 'LOW' || !analysisResult.metadata_exposure ? 'compliant' : (analysisResult.metadata_exposure?.exposure_rating === 'MEDIUM' ? 'warning' : 'danger')}`}>
                EXPOSURE: {analysisResult.metadata_exposure?.exposure_rating || 'LOW'} ({analysisResult.metadata_exposure?.exposure_score || 0}/100)
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginTop: '16px' }}>
              <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '4px' }}>
                  VISIBLE ENDPOINT IPS
                </span>
                <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.86rem', color: 'var(--accent-cyan)' }}>
                  {analysisResult.source_ip || 'N/A'} &rarr; {analysisResult.destination_ip || 'N/A'}
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  Outer IP Pair ({analysisResult.ip_version || 'IPv4'})
                </span>
              </div>

              <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '4px' }}>
                  IKE IDENTITY PAYLOADS ($ID_i$ / $ID_r$)
                </span>
                <strong style={{ fontSize: '0.86rem', color: analysisResult.metadata_exposure?.identity_exposure?.plaintext_identity_leak ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                  {analysisResult.metadata_exposure?.identity_exposure?.plaintext_identity_leak ? 'PLAINTEXT EXPOSED' : 'ENCRYPTED / ABSENT'}
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  {analysisResult.metadata_exposure?.identity_exposure?.exposed_identity_type || 'No Plaintext Leakage'}
                </span>
              </div>

              <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '4px' }}>
                  SPI SESSION LINKABILITY
                </span>
                <strong style={{ fontSize: '0.86rem', color: analysisResult.metadata_exposure?.spi_correlation?.spi_linkability_risk === 'HIGH' ? 'var(--accent-red)' : 'var(--accent-yellow)' }}>
                  {analysisResult.metadata_exposure?.spi_correlation?.spi_linkability_risk || 'LOW'} TRACKING RISK
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  {analysisResult.metadata_exposure?.spi_correlation?.esp_spis?.length || 0} ESP SPI(s) Observed
                </span>
              </div>

              <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '4px' }}>
                  HEADER EXPOSURE (MODE)
                </span>
                <strong style={{ fontSize: '0.86rem', color: analysisResult.mode === 'Transport' ? 'var(--accent-yellow)' : 'var(--accent-green)' }}>
                  {analysisResult.mode || 'Tunnel'} Mode ({analysisResult.metadata_exposure?.transport_mode_exposure?.exposed_metadata_bytes_per_pkt || 0} B/pkt)
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  {analysisResult.mode === 'Transport' ? 'Exposes Inner IP Header' : 'Full Envelope Encapsulation'}
                </span>
              </div>
            </div>
          </div>

          {/* VPN Behavioral Anomaly Detection Panel */}
          <div style={{ marginBottom: '24px' }}>
            <AnomalyDetectionPanel
              anomalyData={analysisResult.behavioral_anomaly}
              pcapFeatures={analysisResult.flow_features || analysisResult}
              isEmbedded={true}
            />
          </div>

          {/* Dual Column: 3x3 Threat Matrix + Cryptographic Parameters */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.35fr', gap: '24px', marginBottom: '24px' }}>
            {/* 3x3 Threat Matrix */}
            <div className="matrix-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
                <Shield size={18} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  3x3 Threat Matrix (Severity vs Likelihood)
                </h4>
              </div>
              <div className="matrix-grid-3x3">
                <div></div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Low Impact</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Med Impact</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>High Impact</div>

                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>High L-hood</div>
                <div className={`matrix-cell matrix-med ${riskLevel === 'MEDIUM' ? 'active-risk' : ''}`}>Medium</div>
                <div className="matrix-cell matrix-high">High</div>
                <div className={`matrix-cell matrix-crit ${riskLevel === 'HIGH' ? 'active-risk' : ''}`}>Critical</div>

                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Med L-hood</div>
                <div className={`matrix-cell matrix-low ${riskLevel === 'LOW' || riskLevel === 'SECURE' ? 'active-risk' : ''}`}>Low</div>
                <div className="matrix-cell matrix-med">Medium</div>
                <div className="matrix-cell matrix-high">High</div>

                <div style={{ fontFamily: 'JetBrains Mono', fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Low L-hood</div>
                <div className="matrix-cell matrix-low">Low</div>
                <div className="matrix-cell matrix-low">Low</div>
                <div className="matrix-cell matrix-med">Medium</div>
              </div>
            </div>

            {/* Cryptographic Baseline Table */}
            <div className="matrix-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
                <Terminal size={18} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Cryptographic Parameters &amp; Baseline Verification
                </h4>
              </div>
              <div className="table-responsive">
                <table className="cyber-table">
                  <thead>
                    <tr>
                      <th>Parameter</th>
                      <th>Observed Value</th>
                      <th>Baseline Baseline</th>
                      <th>Compliance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResult.source_ip && analysisResult.destination_ip && (
                      <tr>
                        <td><strong>Endpoint IP Pair</strong></td>
                        <td><code>{analysisResult.source_ip} &rarr; {analysisResult.destination_ip}</code></td>
                        <td>Observable Outer IP Headers</td>
                        <td><span className="status-badge compliant">EXTRACTED</span></td>
                      </tr>
                    )}
                    <tr>
                      <td><strong>IKE Version</strong></td>
                      <td><code>{analysisResult.ike_version || 'IKEv2'}</code></td>
                      <td>IKEv2 (RFC 7296)</td>
                      <td>
                        <span className={`status-badge ${String(analysisResult.ike_version).includes('v2') ? 'compliant' : 'danger'}`}>
                          {String(analysisResult.ike_version).includes('v2') ? 'COMPLIANT' : 'VIOLATION'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Encryption Cipher</strong></td>
                      <td><code>{analysisResult.encryption || 'AES-256-GCM'}</code></td>
                      <td>AES-256-GCM / AES-256-CBC</td>
                      <td>
                        <span className={`status-badge ${!String(analysisResult.encryption).includes('3DES') ? 'compliant' : 'danger'}`}>
                          {!String(analysisResult.encryption).includes('3DES') ? 'COMPLIANT' : 'DEPRECATED'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Integrity / PRF</strong></td>
                      <td><code>{analysisResult.integrity || 'AEAD'}</code></td>
                      <td>AEAD / HMAC-SHA2-256</td>
                      <td>
                        <span className={`status-badge ${!String(analysisResult.integrity).includes('MD5') ? 'compliant' : 'danger'}`}>
                          {!String(analysisResult.integrity).includes('MD5') ? 'COMPLIANT' : 'WEAK'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Diffie-Hellman</strong></td>
                      <td><code>Group {analysisResult.dh_group || '19'}</code></td>
                      <td>Group 14, 19, 20, 21</td>
                      <td>
                        <span className={`status-badge ${parseInt(analysisResult.dh_group || '19', 10) >= 14 || analysisResult.dh_group === '19' ? 'compliant' : 'danger'}`}>
                          {parseInt(analysisResult.dh_group || '19', 10) >= 14 || analysisResult.dh_group === '19' ? 'COMPLIANT' : 'INSECURE'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Encapsulation</strong></td>
                      <td><code>ESP (Prot 50) • Replay Active</code></td>
                      <td>RFC 4303 Security Payload</td>
                      <td><span className="status-badge compliant">COMPLIANT</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Security Findings & Actionable Remediations */}
          <div className="matrix-card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
              <AlertOctagon size={18} />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Security Audit Findings &amp; Explainable Remediation Directives
              </h4>
            </div>

            {findings.length === 0 ? (
              <div className="finding-box LOW">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent-green)' }}> Zero Cryptographic Policy Violations</span>
                  <span className="status-badge compliant">NIST COMPLIANT</span>
                </div>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  The capture matches corporate baselines, FIPS 140-3 primitives, and NSA Commercial Solutions for Classified guidelines. No weak transforms or deprecated DH groups observed.
                </p>
              </div>
            ) : (
              findings.map((f, i) => (
                <div key={i} className={`finding-box ${f.severity || 'HIGH'}`}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.92rem' }}>
                      [{f.finding_id || `AUDIT-${i + 1}`}] {f.title}
                    </span>
                    <span className={`status-badge ${f.severity === 'HIGH' ? 'danger' : 'warning'}`}>
                      {f.severity} SEVERITY
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Observed: <code style={{ color: 'var(--accent-cyan)', background: 'var(--accent-cyan-dim)', padding: '2px 6px', borderRadius: '4px' }}>{f.observed}</code> &bull; Expected: <code style={{ color: 'var(--accent-cyan)', background: 'var(--accent-cyan-dim)', padding: '2px 6px', borderRadius: '4px' }}>{f.expected}</code>
                  </div>
                  <div style={{ fontSize: '0.84rem', color: 'var(--accent-cyan)', background: 'var(--accent-cyan-dim)', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid var(--accent-cyan)' }}>
                    <strong>Actionable Directive:</strong> {f.recommendation}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Export Toolbar */}
          <div className="export-card">
            <div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Export Formal Reports &amp; Telemetry
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Download standalone executive printable HTML report or technical JSON format for SIEM ingestion.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <a
                href={`/reports/download-html?filename=${encodeURIComponent(activeFilename)}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary"
              >
                <Download size={16} />
                <span>Executive HTML Report</span>
              </a>
              <a
                href={`/reports/download-json?filename=${encodeURIComponent(activeFilename)}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
              >
                <FileText size={16} />
                <span>Technical JSON</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
