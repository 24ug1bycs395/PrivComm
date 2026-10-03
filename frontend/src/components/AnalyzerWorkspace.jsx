import React, { useState } from 'react';
import {
  UploadCloud,
  FileCheck,
  AlertTriangle,
  Info,
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
  Activity,
  Copy,
  Check,
  Server,
  Code2,
  Sliders,
  Sparkles
} from 'lucide-react';
import AnomalyDetectionPanel from './AnomalyDetectionPanel';

const createDemoAnalysis = (scenarioType, filename) => {
  const isStrong = scenarioType === 'ikev2-strong';
  return {
    analysis_source: 'demo_simulation',
    data_provenance: 'Synthetic UI demonstration data; no capture was parsed and no classifier inference was run.',
    filename,
    packet_count: null,
    packet_evidence: [],
    capture_sha256: null,
    ike_version: isStrong ? 'IKEv2' : 'IKEv1 (Aggressive Mode)',
    encryption: isStrong ? 'AES-256-GCM' : 'DES-CBC',
    integrity: isStrong ? 'AEAD' : 'MD5',
    dh_group: isStrong ? '19' : '2',
    pfs: null,
    mode: 'Tunnel',
    traffic_classification: {
      traffic_type: 'HTTP_GET',
      confidence: null,
      status: 'demo_simulation',
    },
    security_assessment: {
      risk_level: isStrong ? 'LOW' : 'HIGH',
      risk_score: isStrong ? 12 : 88,
      findings: isStrong ? [] : [{
        finding_id: 'DEMO-WEAK-PROPOSAL',
        title: 'Illustrative weak cryptographic proposal',
        severity: 'HIGH',
        observed: 'IKEv1 Aggressive Mode, DES-CBC, MD5, DH Group 2 (synthetic example)',
        expected: 'IKEv2 with approved modern algorithms',
        recommendation: 'Use this example to demonstrate the interface only; validate a real configuration or capture before making changes.',
      }],
    },
  };
};

export default function AnalyzerWorkspace({ externalAnalysis }) {
  const [ingestionMode, setIngestionMode] = useState('pcap'); // 'pcap' or 'vendor-config'
  const [loading, setLoading] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState([]);
  const [activeFilename, setActiveFilename] = useState('');
  const [analysisResult, setAnalysisResult] = useState(externalAnalysis || null);
  const [errorNotice, setErrorNotice] = useState(null);

  // Vendor Config State
  const [selectedVendor, setSelectedVendor] = useState('auto');
  const [vendorConfigText, setVendorConfigText] = useState('');
  const [copiedRemediation, setCopiedRemediation] = useState(false);

  React.useEffect(() => {
    if (externalAnalysis) {
      setAnalysisResult(externalAnalysis);
      setActiveFilename(externalAnalysis.filename || 'inspected_capture.pcap');
    }
  }, [externalAnalysis]);

  const handleDownloadPDF = async (e) => {
    e.preventDefault();
    const fallbackPath = '/reports/ikev2_s2s_ipsec_vpn_aes_gcm_executive_report.pdf';
    try {
      const res = await fetch(`/reports/download-pdf?filename=${encodeURIComponent(activeFilename)}`);
      const contentType = res.headers.get('content-type') || '';
      if (res.ok && (contentType.includes('pdf') || contentType.includes('octet-stream'))) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${(activeFilename || 'ipsec_report').replace(/\.[^/.]+$/, '')}_executive_report.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        return;
      }
    } catch (err) {
      console.warn('PDF endpoint unavailable, downloading static report fallback:', err);
    }
    const a = document.createElement('a');
    a.href = fallbackPath;
    a.download = `${(activeFilename || 'ipsec_report').replace(/\.[^/.]+$/, '')}_executive_report.pdf`;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const handleDownloadCBOM = () => {
    if (!analysisResult?.crypto_bom) return;
    const blob = new Blob([JSON.stringify(analysisResult.crypto_bom, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(activeFilename || 'capture').replace(/\.[^/.]+$/, '')}_cbom.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = async (e) => {
    e.preventDefault();
    if (analysisResult) {
      const blob = new Blob([JSON.stringify(analysisResult, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(activeFilename || 'analysis').replace(/\.[^/.]+$/, '')}_technical_report.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      return;
    }
    const a = document.createElement('a');
    a.href = '/reports/ikev2_s2s_ipsec_vpn_aes_gcm.json';
    a.download = `${(activeFilename || 'analysis').replace(/\.[^/.]+$/, '')}_technical_report.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  // Trigger analysis for PCAP sample scenarios
  const handleLoadSample = async (scenarioType) => {
    setLoading(true);
    setErrorNotice(null);
    setAnalysisResult(null);
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
      const demoResult = createDemoAnalysis(scenarioType, targetFilename);
      setAnalysisResult(demoResult);
      setErrorNotice(`Backend sample analysis unavailable (${err.message}). Showing a synthetic UI demo only; no PCAP was parsed.`);
      setPipelineLogs([
        '[DEMO ONLY] Backend unavailable; displaying synthetic sample values.',
        '[DEMO ONLY] No capture was read, no packet evidence or offsets were created.',
        '[DEMO ONLY] No classifier inference or policy evaluation was run.',
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Handle custom PCAP upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setErrorNotice(null);
    setAnalysisResult(null);
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

  // Handle Multi-Vendor Config Analysis
  const handleAnalyzeVendorConfig = async () => {
    if (!vendorConfigText.trim()) {
      setErrorNotice('Please paste or upload a router/firewall configuration to analyze.');
      return;
    }
    setLoading(true);
    setErrorNotice(null);
    setAnalysisResult(null);
    const fn = `${selectedVendor === 'auto' ? 'vendor' : selectedVendor}_config.cfg`;
    setActiveFilename(fn);

    setPipelineLogs([
      `[01/04 VENDOR DETECT] Identifying firewall / router syntax (${selectedVendor})...`,
      `[02/04 LEXER PARSE] Extracting crypto maps, phase1/phase2 proposals & transform sets...`,
      `[03/04 POLICY AUDIT] Running NIST SP 800-77, FIPS 140-3 & PQC evaluations...`,
      `[04/04 REMEDIATION] Generating production-hardened vendor configuration diff...`,
    ]);

    try {
      const res = await fetch('/analyze/vendor-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_text: vendorConfigText,
          vendor: selectedVendor,
          filename: fn
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}: Vendor config analysis failed`);
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      setErrorNotice(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Vendor Config File Upload
  const handleVendorFileUpload = async (file) => {
    if (!file) return;
    const text = await file.text();
    setVendorConfigText(text);
    setActiveFilename(file.name);
    setLoading(true);
    setErrorNotice(null);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('config_file', file);

      const res = await fetch(`/analyze/vendor-config/upload?vendor=${selectedVendor}`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}: Upload failed`);
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      setErrorNotice(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Pre-load Vendor Sample Templates
  const handleSelectVendorSample = (sampleKey) => {
    const samples = {
      cisco_asa_weak: {
        vendor: 'cisco',
        text: `! Cisco ASA Legacy IKEv1 VPN Configuration (Vulnerable)
crypto isakmp policy 10
 encr 3des
 hash md5
 authentication pre-share
 group 2
 lifetime 86400
!
crypto ipsec transform-set LEGACY_TRANSFORM esp-3des esp-md5-hmac
 mode transport
!
crypto map OUTSIDE_MAP 10 ipsec-isakmp
 set peer 203.0.113.15
 set transform-set LEGACY_TRANSFORM
 match address VPN_TRAFFIC
!`
      },
      cisco_ios_modern: {
        vendor: 'cisco',
        text: `! Cisco IOS-XE Modern Compliant IKEv2 Configuration
crypto ikev2 proposal IKEV2_GCM_PROP
 encryption aes-gcm-256
 prf sha256
 group 19
!
crypto ikev2 policy IKEV2_GCM_POLICY
 proposal IKEV2_GCM_PROP
!
crypto ipsec transform-set GCM_TRANSFORM esp-gcm 256
 mode tunnel
!
crypto ipsec profile HARDENED_IPSEC_PROFILE
 set transform-set GCM_TRANSFORM
 set pfs group19
 set security-association lifetime seconds 28800
!
crypto map SECURE_MAP 10 ipsec-isakmp
 set peer 198.51.100.25
 set transform-set GCM_TRANSFORM
 set pfs group19
!`
      },
      fortinet_fortios: {
        vendor: 'fortinet',
        text: `# FortiGate IPsec VPN Phase 1 & 2 Config
config vpn ipsec phase1-interface
    edit "HQ_BRANCH_TUNNEL"
        set interface "wan1"
        set ike-version 2
        set proposal aes256gcm-prfsha256 aes256-sha256
        set dhgrp 19 14
        set remote-gw 198.51.100.50
        set psksecret ENC mySecretKey123
        set keylife 28800
    next
end

config vpn ipsec phase2-interface
    edit "HQ_BRANCH_P2"
        set phase1name "HQ_BRANCH_TUNNEL"
        set proposal aes256gcm
        set dhgrp 19
        set pfs enable
        set encapsulation tunnel
        set auto-negotiate enable
    next
end`
      },
      pfsense_xml: {
        vendor: 'pfsense',
        text: `<ipsec>
    <phase1>
        <ikeid>1</ikeid>
        <iketype>ikev2</iketype>
        <interface>wan</interface>
        <remote-gateway>198.51.100.80</remote-gateway>
        <protocol>inet</protocol>
        <myid_type>myaddress</myid_type>
        <peerid_type>peeraddress</peerid_type>
        <encryption-algorithm>
            <name>aes256gcm</name>
            <keylen>256</keylen>
        </encryption-algorithm>
        <hash-algorithm>sha256</hash-algorithm>
        <dhgroup>19</dhgroup>
        <prf-algorithm>sha256</prf-algorithm>
        <lifetime>28800</lifetime>
    </phase1>
    <phase2>
        <ikeid>1</ikeid>
        <mode>tunnel</mode>
        <pfsgroup>19</pfsgroup>
        <lifetime>3600</lifetime>
        <encryption-algorithm-option>
            <name>aes256gcm</name>
            <keylen>256</keylen>
        </encryption-algorithm-option>
    </phase2>
</ipsec>`
      },
      libreswan_conf: {
        vendor: 'libreswan',
        text: `# Libreswan IPsec Site-to-Site Connection
conn Cloud-to-Datacenter
    authby=secret
    type=tunnel
    left=192.168.1.1
    leftsubnet=192.168.1.0/24
    right=198.51.100.99
    rightsubnet=10.0.0.0/16
    ikev2=insist
    ike=aes_gcm256-sha2_512;dh19
    esp=aes_gcm256;dh19
    pfs=yes
    salifetime=8h
    auto=start`
      }
    };

    const s = samples[sampleKey];
    if (s) {
      setVendorConfigText(s.text);
      setSelectedVendor(s.vendor);
    }
  };

  const handleCopyRemediation = () => {
    if (analysisResult?.remediation_config) {
      navigator.clipboard.writeText(analysisResult.remediation_config);
      setCopiedRemediation(true);
      setTimeout(() => setCopiedRemediation(false), 2000);
    }
  };

  const riskLevel = analysisResult?.security_assessment?.risk_level || 'UNVERIFIED';
  const riskScore = analysisResult?.security_assessment?.risk_score ?? null;
  const trafficType = analysisResult?.traffic_classification?.traffic_type || 'UNVERIFIED';
  const confidence = analysisResult?.traffic_classification?.confidence ?? null;
  const confPercent = confidence === null ? null : (confidence * 100).toFixed(1);
  const findings = analysisResult?.security_assessment?.findings || [];
  const packetEvidence = analysisResult?.packet_evidence || [];
  const isObserved = (value) => value !== null && value !== undefined
    && String(value).trim() !== '' && String(value).toLowerCase() !== 'unknown';
  const ikeKnown = isObserved(analysisResult?.ike_version);
  const encryption = String(analysisResult?.encryption || '').toUpperCase();
  const encryptionKnown = isObserved(analysisResult?.encryption);
  const encryptionCompliant = encryptionKnown
    && !['DES', '3DES', 'NULL', 'RC4'].some((algorithm) => encryption.includes(algorithm))
    && ['AES-256-GCM', 'AES-128-GCM', 'AES-256-CBC'].some((algorithm) => encryption.includes(algorithm));
  const integrity = String(analysisResult?.integrity || '').toUpperCase();
  const integrityKnown = isObserved(analysisResult?.integrity);
  const integrityCompliant = integrityKnown
    && !['MD5', 'SHA1'].some((algorithm) => integrity.includes(algorithm))
    && ['AEAD', 'HMAC-SHA2-256', 'HMAC-SHA2-384', 'HMAC-SHA2-512'].some((algorithm) => integrity.includes(algorithm));
  const modeKnown = isObserved(analysisResult?.mode);
  const pfsKnown = analysisResult?.pfs === true || analysisResult?.pfs === false;
  const dhKnown = isObserved(analysisResult?.dh_group);
  const dhCompliant = dhKnown && ['14', '19', '20', '21', '28'].includes(String(analysisResult.dh_group));

  return (
    <div className="analyzer-workspace-container">
      {/* Header Pretitle */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '9999px', background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.74rem', fontWeight: 600, marginBottom: '10px' }}>
          <Activity size={14} />
          <span>DUAL INGESTION: PCAP WIRE DISSECTION &bull; MULTI-VENDOR CONFIG PARSING</span>
        </div>
        <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '8px' }}>
          IPsec Security Assessment &amp; Configuration Intelligence
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '880px' }}>
          Audit live network packet captures or upload multi-vendor firewall configs (Cisco, Fortinet, pfSense, Libreswan, strongSwan) for automated risk scoring, compliance checks, and copy-paste hardening playbooks.
        </p>
      </div>

      {/* Ingestion Mode Toggle Selector */}
      <div style={{
        display: 'inline-flex',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '12px',
        padding: '4px',
        marginBottom: '20px',
        gap: '6px'
      }}>
        <button
          type="button"
          onClick={() => setIngestionMode('pcap')}
          style={{
            background: ingestionMode === 'pcap' ? 'var(--accent-cyan-dim)' : 'transparent',
            color: ingestionMode === 'pcap' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            border: ingestionMode === 'pcap' ? '1px solid var(--accent-cyan)' : '1px solid transparent',
            borderRadius: '8px',
            padding: '8px 18px',
            fontSize: '0.82rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease'
          }}
        >
          <UploadCloud size={16} />
          <span>📁 PCAP Network Capture (.pcap / .pcapng)</span>
        </button>

        <button
          type="button"
          onClick={() => setIngestionMode('vendor-config')}
          style={{
            background: ingestionMode === 'vendor-config' ? 'var(--accent-cyan-dim)' : 'transparent',
            color: ingestionMode === 'vendor-config' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            border: ingestionMode === 'vendor-config' ? '1px solid var(--accent-cyan)' : '1px solid transparent',
            borderRadius: '8px',
            padding: '8px 18px',
            fontSize: '0.82rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease'
          }}
        >
          <Code2 size={16} />
          <span>⚙️ Multi-Vendor Firewall Config (Cisco, Fortinet, pfSense)</span>
        </button>
      </div>

      {/* ----------------- MODE 1: PCAP CAPTURE INGESTION ----------------- */}
      {ingestionMode === 'pcap' && (
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
                Supports .pcap, .pcapng &bull; Scapy + TShark In-Memory Parsing
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
              Browse Local PCAP
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
                <div style={{ width: '36px', height: '36px', borderRadius: '6px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
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
              <span className="btn btn-primary btn-sm">
                {loading && activeFilename.includes('ikev2') ? 'Auditing...' : 'Run Audit'}
              </span>
            </div>

            <div className="sample-row-card" onClick={() => !loading && handleLoadSample('ikev1-weak')}>
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
              <span className="btn btn-secondary btn-sm">
                {loading && activeFilename.includes('IKEv1') ? 'Auditing...' : 'Run Audit'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ----------------- MODE 2: MULTI-VENDOR CONFIG INGESTION ----------------- */}
      {ingestionMode === 'vendor-config' && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-default)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px'
        }}>
          {/* Vendor selection & Preset Samples bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>Target Vendor Syntax:</span>
              <select
                value={selectedVendor}
                onChange={(e) => setSelectedVendor(e.target.value)}
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '0.8rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="auto">✨ Auto-Detect Vendor</option>
                <option value="cisco">Cisco ASA / IOS-XE</option>
                <option value="fortinet">Fortinet FortiOS</option>
                <option value="pfsense">pfSense / OPNsense (XML)</option>
                <option value="libreswan">Libreswan / Openswan</option>
                <option value="strongswan">strongSwan (swanctl.conf)</option>
              </select>
            </div>

            {/* Quick Sample Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>Load Template:</span>
              <button
                type="button"
                onClick={() => handleSelectVendorSample('cisco_asa_weak')}
                style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444', borderRadius: '4px', padding: '3px 8px', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                🔴 Cisco ASA (3DES Weak)
              </button>
              <button
                type="button"
                onClick={() => handleSelectVendorSample('cisco_ios_modern')}
                style={{ background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', borderRadius: '4px', padding: '3px 8px', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                🟢 Cisco IOS-XE (Compliant)
              </button>
              <button
                type="button"
                onClick={() => handleSelectVendorSample('fortinet_fortios')}
                style={{ background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', borderRadius: '4px', padding: '3px 8px', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                🟢 Fortinet FortiOS
              </button>
              <button
                type="button"
                onClick={() => handleSelectVendorSample('pfsense_xml')}
                style={{ background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', borderRadius: '4px', padding: '3px 8px', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                🟢 pfSense XML
              </button>
              <button
                type="button"
                onClick={() => handleSelectVendorSample('libreswan_conf')}
                style={{ background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', borderRadius: '4px', padding: '3px 8px', fontSize: '0.72rem', cursor: 'pointer', fontWeight: 600 }}
              >
                🟢 Libreswan
              </button>
            </div>
          </div>

          {/* Config Editor Textarea */}
          <div style={{ position: 'relative', marginBottom: '14px' }}>
            <textarea
              rows={8}
              value={vendorConfigText}
              onChange={(e) => setVendorConfigText(e.target.value)}
              placeholder="Paste raw configuration snippet here (e.g. crypto ikev2 proposal, config vpn ipsec phase1-interface, <ipsec><phase1>... or conn Cloud-VPN)..."
              style={{
                width: '100%',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '12px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                lineHeight: '1.5',
                resize: 'vertical',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Upload Button + Run Audit Button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                id="vendorFileInput"
                type="file"
                accept=".cfg,.conf,.txt,.xml,.json"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files?.[0] && handleVendorFileUpload(e.target.files[0])}
              />
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => document.getElementById('vendorFileInput')?.click()}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <UploadCloud size={15} />
                <span>Upload .cfg / .conf / .xml File</span>
              </button>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                Supports Cisco ASA/IOS, Fortinet, pfSense XML, Libreswan &amp; strongSwan
              </span>
            </div>

            <button
              type="button"
              className="btn btn-primary"
              onClick={handleAnalyzeVendorConfig}
              disabled={loading || !vendorConfigText.trim()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 20px', cursor: 'pointer' }}
            >
              <Sliders size={16} />
              <span>{loading ? 'Analyzing Configuration...' : 'Audit & Generate Remediation'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorNotice && (
        <div style={{
          padding: '14px 18px',
          background: analysisResult?.analysis_source === 'demo_simulation' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 68, 68, 0.12)',
          border: `1px solid ${analysisResult?.analysis_source === 'demo_simulation' ? 'rgba(245, 158, 11, 0.55)' : 'rgba(239, 68, 68, 0.3)'}`,
          borderRadius: '8px',
          color: analysisResult?.analysis_source === 'demo_simulation' ? 'var(--text-primary)' : 'var(--accent-red)',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {analysisResult?.analysis_source === 'demo_simulation' ? <Info size={18} /> : <AlertOctagon size={18} />}
          <span>{errorNotice}</span>
        </div>
      )}

      {/* LIVE RESULTS DASHBOARD */}
      {analysisResult && (
        <div className="results-container">
          {/* Top File Banner */}
          <div className="file-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '8px', background: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {analysisResult.vendor ? <Server size={24} /> : <FileCheck size={24} />}
              </div>
              <div>
                <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {activeFilename}
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
                  {analysisResult.vendor && (
                    <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>
                      VENDOR: {analysisResult.vendor}
                    </span>
                  )}
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {analysisResult.analysis_source === 'demo_simulation'
                      ? 'Synthetic demo values · no capture parsed'
                      : analysisResult.raw_config_lines
                        ? `Parsed ${analysisResult.raw_config_lines} configuration lines`
                        : `Parsed ${analysisResult.packet_count ?? 'Unknown'} frames`} &bull; {analysisResult.analysis_source === 'demo_simulation' ? 'Browser demo' : analysisResult.vendor ? 'Vendor Lexer Engine' : 'Scapy/TShark Engine'}
                  </span>
                  {analysisResult.source_ip && analysisResult.destination_ip && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', background: 'var(--accent-cyan-dim)', border: '1px solid var(--border-default)', color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px' }}>
                      IP Pair: {analysisResult.source_ip} &rarr; {analysisResult.destination_ip}
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
              background: riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'var(--status-success-dim)' : (riskLevel === 'MEDIUM' ? 'var(--status-warning-dim)' : 'var(--status-danger-dim)'),
              color: riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'var(--status-success)' : (riskLevel === 'MEDIUM' ? 'var(--status-warning)' : 'var(--status-danger)'),
              border: `1px solid ${riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'var(--status-success-border)' : (riskLevel === 'MEDIUM' ? 'var(--status-warning-border)' : 'var(--status-danger-border)')}`
            }}>
              <span className="live-dot" style={{ background: 'currentColor' }}></span>
              <span>{riskLevel} RISK ({riskScore}/100)</span>
            </div>
          </div>

          {analysisResult.analysis_source === 'demo_simulation' && (
            <div role="status" style={{
              margin: '0 0 24px',
              padding: '14px 16px',
              border: '1px solid rgba(245, 158, 11, 0.55)',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.1)',
              color: 'var(--text-primary)',
              lineHeight: 1.5,
            }}>
              <strong style={{ color: '#f59e0b' }}>SIMULATED DEMO RESULT — NOT CAPTURE ANALYSIS</strong>
              <div>{analysisResult.data_provenance} Do not use these illustrative values as security evidence or operational guidance.</div>
            </div>
          )}

          {/* 4 Executive Metrics Grid */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-title-bar">
                <span>SECURITY RISK SCORE</span>
                <Shield size={16} color="#38bdf8" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="metric-big-val" style={{ color: '#38bdf8' }}>{riskScore ?? 'N/A'}</span>
                {riskScore !== null && <span style={{ color: '#64748b', fontFamily: 'JetBrains Mono', fontSize: '0.9rem' }}>/ 100</span>}
              </div>
              <span className={`status-badge ${riskLevel === 'SECURE' || riskLevel === 'LOW' ? 'compliant' : (riskLevel === 'MEDIUM' ? 'warning' : 'danger')}`} style={{ alignSelf: 'flex-start' }}>
                {riskLevel} LEVEL
              </span>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>AI TRAFFIC / POLICY CLASS</span>
                <Cpu size={16} color="#a855f7" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                {trafficType}
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'JetBrains Mono' }}>
                  <span>Raw top-class score (uncalibrated)</span>
                  <span>{confPercent === null ? 'N/A' : `${confPercent}%`}</span>
                </div>
                {confPercent !== null && <div className="confidence-bar-bg">
                  <div className="confidence-bar-fill" style={{ width: `${confPercent}%` }}></div>
                </div>}
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>CIPHER &amp; INTEGRITY SUITE</span>
                <Lock size={16} color="var(--accent-cyan)" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                {analysisResult.encryption || 'Unverified'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                Integrity / PRF: <strong style={{ color: 'var(--text-primary)' }}>{analysisResult.integrity || 'Unverified'}</strong>
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-title-bar">
                <span>KEY EXCHANGE &amp; MODE</span>
                <Zap size={16} color="var(--accent-yellow)" />
              </div>
              <div className="metric-big-val" style={{ fontSize: '1.25rem' }}>
                {analysisResult.dh_group ? `Group ${analysisResult.dh_group}` : 'DH group unverified'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                Mode: <strong style={{ color: 'var(--text-primary)' }}>{analysisResult.ike_version || 'Unverified'} ({analysisResult.mode || 'mode unverified'})</strong>
              </div>
            </div>
          </div>

          {/* VENDOR-HARDENED PRODUCTION REMEDIATION PLAYBOOK (When Available) */}
          {analysisResult.remediation_config && (
            <div className="matrix-card" style={{
              marginBottom: '24px',
              border: '1px solid var(--accent-cyan)',
              background: 'rgba(56, 189, 248, 0.04)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)' }}>
                  <Sparkles size={18} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Hardened Configuration Template — Review Before Use ({analysisResult.vendor || 'Custom'})
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={handleCopyRemediation}
                  style={{
                    background: copiedRemediation ? 'var(--status-success-dim)' : 'var(--accent-cyan-dim)',
                    border: '1px solid var(--border-default)',
                    color: copiedRemediation ? 'var(--status-success)' : 'var(--accent-cyan)',
                    borderRadius: '6px',
                    padding: '4px 12px',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  {copiedRemediation ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copiedRemediation ? 'Copied to Clipboard!' : 'Copy Remediated Config'}</span>
                </button>
              </div>

              <div style={{ marginTop: '14px' }}>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                  This is a suggested template, not a configuration diff. It has not been applied or validated on <strong>{analysisResult.vendor || 'a target router'}</strong>; review it against your complete device configuration before use.
                </p>
                <pre style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '14px',
                  color: 'var(--accent-cyan)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  lineHeight: '1.5',
                  overflowX: 'auto',
                  margin: 0
                }}>
                  {analysisResult.remediation_config}
                </pre>
              </div>
            </div>
          )}

          {/* Observable Metadata Exposure Summary Card */}
          {analysisResult.analysis_source === 'demo_simulation' ? (
            <div className="matrix-card" style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
                <Activity size={18} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>Capture Metadata</h4>
              </div>
              <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>Not available in this browser-only demonstration. No packet capture or endpoint metadata was inspected.</p>
            </div>
          ) : <div className="matrix-card" style={{ marginBottom: '24px' }}>
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
                  {analysisResult.source_ip || 'Unverified'} &rarr; {analysisResult.destination_ip || 'Unverified'}
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  Outer IP Pair ({analysisResult.ip_version || 'IP version unverified'})
                </span>
              </div>

              <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '4px' }}>
                  IKE IDENTITY PAYLOADS ($ID_i$ / $ID_r$)
                </span>
                <strong style={{ fontSize: '0.86rem', color: analysisResult.metadata_exposure?.identity_exposure?.plaintext_identity_leak ? 'var(--text-secondary)' : 'var(--accent-cyan)' }}>
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
                <strong style={{ fontSize: '0.86rem', color: analysisResult.mode === 'Transport' ? 'var(--accent-blue)' : 'var(--accent-cyan)' }}>
                  {analysisResult.mode || 'Mode unverified'} ({analysisResult.metadata_exposure?.transport_mode_exposure?.exposed_metadata_bytes_per_pkt ?? 'unverified'} B/pkt)
                </strong>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', display: 'block', marginTop: '4px' }}>
                  {analysisResult.mode === 'Transport' ? 'Exposes Inner IP Header' : 'Full Envelope Encapsulation'}
                </span>
              </div>
            </div>
          </div>}

          {/* VPN Behavioral Anomaly Detection Panel (If packet features available) */}
          {analysisResult.behavioral_anomaly && (
            <div style={{ marginBottom: '24px' }}>
              <AnomalyDetectionPanel
                anomalyData={analysisResult.behavioral_anomaly}
                pcapFeatures={analysisResult.flow_features || analysisResult}
                isEmbedded={true}
              />
            </div>
          )}

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
                      <th>Baseline Requirement</th>
                      <th>Compliance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResult.source_ip && analysisResult.destination_ip && (
                      <tr>
                        <td><strong>Endpoint IP Pair</strong></td>
                        <td><code>{analysisResult.source_ip} &rarr; {analysisResult.destination_ip}</code></td>
                        <td>Configured Gateway Endpoints</td>
                        <td><span className="status-badge compliant">EXTRACTED</span></td>
                      </tr>
                    )}
                    <tr>
                      <td><strong>IKE Version</strong></td>
                      <td><code>{ikeKnown ? analysisResult.ike_version : 'Unknown'}</code></td>
                      <td>IKEv2 (RFC 7296)</td>
                      <td>
                        <span className={`status-badge ${!ikeKnown ? 'warning' : String(analysisResult.ike_version).toUpperCase().includes('V2') ? 'compliant' : 'danger'}`}>
                          {!ikeKnown ? 'UNVERIFIED' : String(analysisResult.ike_version).toUpperCase().includes('V2') ? 'COMPLIANT' : 'VIOLATION'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Encryption Cipher</strong></td>
                      <td><code>{encryptionKnown ? analysisResult.encryption : 'Unknown'}</code></td>
                      <td>AES-256-GCM / AES-256-CBC</td>
                      <td>
                        <span className={`status-badge ${!encryptionKnown ? 'warning' : encryptionCompliant ? 'compliant' : 'danger'}`}>
                          {!encryptionKnown ? 'UNVERIFIED' : encryptionCompliant ? 'COMPLIANT' : 'DEPRECATED / UNAPPROVED'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Integrity / PRF</strong></td>
                      <td><code>{integrityKnown ? analysisResult.integrity : 'Unknown'}</code></td>
                      <td>AEAD / HMAC-SHA2-256</td>
                      <td>
                        <span className={`status-badge ${!integrityKnown ? 'warning' : integrityCompliant ? 'compliant' : 'danger'}`}>
                          {!integrityKnown ? 'UNVERIFIED' : integrityCompliant ? 'COMPLIANT' : 'WEAK / UNAPPROVED'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Operating Mode</strong></td>
                      <td><code>{modeKnown ? `${analysisResult.mode} Mode` : 'Unknown'}</code></td>
                      <td>Tunnel Mode (RFC 4301)</td>
                      <td>
                        <span className={`status-badge ${!modeKnown ? 'warning' : analysisResult.mode === 'Tunnel' ? 'compliant' : 'warning'}`}>
                          {!modeKnown ? 'UNVERIFIED' : analysisResult.mode === 'Tunnel' ? 'COMPLIANT' : 'HOST-TO-HOST'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Perfect Forward Secrecy</strong></td>
                      <td><code>{!pfsKnown ? 'Unknown / not observable' : analysisResult.pfs ? 'Enforced' : 'Disabled'}</code></td>
                      <td>PFS Enabled (Child SA DH)</td>
                      <td>
                        <span className={`status-badge ${!pfsKnown ? 'warning' : analysisResult.pfs ? 'compliant' : 'danger'}`}>
                          {!pfsKnown ? 'UNVERIFIED' : analysisResult.pfs ? 'ENFORCED' : 'DISABLED'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Diffie-Hellman</strong></td>
                      <td><code>{dhKnown ? `Group ${analysisResult.dh_group}` : 'Unknown'}</code></td>
                      <td>Group 14, 19, 20, 21</td>
                      <td>
                        <span className={`status-badge ${!dhKnown ? 'warning' : dhCompliant ? 'compliant' : 'danger'}`}>
                          {!dhKnown ? 'UNVERIFIED' : dhCompliant ? 'COMPLIANT' : 'INSECURE / UNAPPROVED'}
                        </span>
                      </td>
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
                Security Audit Findings &amp; Explainable Directives
              </h4>
            </div>

            {findings.length === 0 ? (
              <div className="finding-box LOW">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={15} />
                    No Policy Findings
                  </span>
                  <span className="status-badge compliant">NO FINDINGS</span>
                </div>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  No policy findings were reported for values that could be evaluated. Parameters marked unknown or unverified are not evidence of compliance.
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

          {/* Capture-linked observations */}
          <div className="matrix-card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-cyan)', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
              <FileText size={18} />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>Packet Evidence</h4>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', overflowWrap: 'anywhere' }}>
              Capture SHA-256: <code>{analysisResult.capture_sha256 || 'Unavailable'}</code>
              <br />Byte ranges are zero-based and half-open; observations do not reveal encrypted payload contents.
            </p>
            {packetEvidence.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem' }}>No packet-level offsets are available for this result.</p>
            ) : packetEvidence.slice(0, 12).map((packet, packetIndex) => (
              <div key={`${packet.frame_number}-${packetIndex}`} className="finding-box LOW">
                <strong>{packet.protocol || 'Packet'} · frame {packet.frame_number ?? 'unavailable'}</strong>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {packet.source_ip || 'unknown'} → {packet.destination_ip || 'unknown'} · timestamp {packet.timestamp ?? 'unavailable'} ·
                  {' '}bytes [{packet.capture_byte_offset ?? 'unavailable'}, {Number.isInteger(packet.capture_byte_offset) && Number.isInteger(packet.capture_byte_length)
                    ? packet.capture_byte_offset + packet.capture_byte_length
                    : 'unavailable'})
                </div>
                {Object.entries(packet.fields || {}).map(([field, value]) => (
                  Array.isArray(value) ? value.map((item, index) => (
                    <div key={`${field}-${index}`} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {field} #{index + 1}: {item.transform_type ? `transform ${item.transform_type} / ${item.transform_id}` : JSON.stringify(item)}
                      {' '}· bytes [{item.capture_byte_offset ?? 'unavailable'}, {Number.isInteger(item.capture_byte_offset) && Number.isInteger(item.capture_byte_length)
                        ? item.capture_byte_offset + item.capture_byte_length
                        : 'unavailable'})
                    </div>
                  )) : value && typeof value === 'object' ? (
                    <div key={field} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {field}: {value.value ?? 'observed'} · bytes [{value.capture_byte_offset ?? 'unavailable'}, {Number.isInteger(value.capture_byte_offset) && Number.isInteger(value.capture_byte_length)
                        ? value.capture_byte_offset + value.capture_byte_length
                        : 'unavailable'})
                    </div>
                  ) : null
                ))}
              </div>
            ))}
          </div>

          {/* Export Toolbar */}
          <div className="export-card">
            <div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Export Formal Reports &amp; Telemetry
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Download formal executive PDF report or technical JSON format for SIEM ingestion.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                type="button"
                onClick={handleDownloadPDF}
                className="btn btn-primary"
                style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                title="Download Executive PDF Report"
              >
                <Download size={16} />
                <span>Executive PDF Report</span>
              </button>
              <button
                type="button"
                onClick={handleDownloadJSON}
                className="btn btn-secondary"
                style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                title="Download Technical JSON"
              >
                <FileText size={16} />
                <span>Technical JSON</span>
              </button>
              <button
                type="button"
                onClick={handleDownloadCBOM}
                className="btn btn-secondary"
                disabled={!analysisResult.crypto_bom}
                style={{ cursor: analysisResult.crypto_bom ? 'pointer' : 'not-allowed', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                title="Download capture-backed cryptographic inventory"
              >
                <Download size={16} />
                <span>Crypto BOM</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
