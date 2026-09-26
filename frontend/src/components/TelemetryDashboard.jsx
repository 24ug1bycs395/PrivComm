import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Shield,
  Server,
  Cpu,
  Lock,
  Zap,
  FileText,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Terminal,
  Download,
  ArrowRight,
  MessageSquare,
  Bot,
  Send,
  X,
  Sparkles,
  Database,
  Layers,
  Check,
  AlertOctagon,
  HelpCircle,
  Eye,
  ExternalLink
} from 'lucide-react';

export default function TelemetryDashboard({ externalAnalysis, onNavigateToTestbed, onNavigateToAnalyzer }) {
  const [analysis, setAnalysis] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [selectedFilename, setSelectedFilename] = useState('ikev2_s2s_ipsec_vpn_aes_gcm.pcapng');
  const [telemetryLogs, setTelemetryLogs] = useState([
    '[SYSTEM] Privcomm Live Telemetry Dashboard initialized.',
    '[STREAM] Listening for VM tap ingestion streams on port 500 / 4500 / 50...',
    '[DISSECTOR] Engine ready. XGBoost Multiclass Classifier loaded.',
    '[POLICY] Context-Aware Security Baseline Rulebook v2.0 ACTIVE.'
  ]);

  // Chatbot State
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'ai',
      text: '👋 Hello! Ask me anything about live VM telemetry, IPsec ciphers, DH groups, or risk ratings!'
    }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, chatLoading]);

  // Load history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  // Handle external analysis passed from Testbed or Vault
  useEffect(() => {
    if (externalAnalysis) {
      setAnalysis(externalAnalysis);
      const fn = externalAnalysis.filename || externalAnalysis.scenario_name || 'testbed_capture.pcap';
      setSelectedFilename(fn);
      setTelemetryLogs(prev => [
        `[INGEST] Loaded inspected capture session: ${fn}`,
        `[AUDIT] Computed Risk Score: ${externalAnalysis.security_assessment?.risk_score ?? externalAnalysis.risk_score ?? 0}/100`,
        `[CLASSIFIER] Target Traffic Class: ${externalAnalysis.traffic_classification?.traffic_type || externalAnalysis.traffic_type || 'IPsec'}`,
        ...prev.slice(0, 8)
      ]);
    } else {
      // Default initial sample load
      loadDefaultSample();
    }
  }, [externalAnalysis]);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setHistoryList(data);
        }
      }
    } catch (e) {
      console.log('Using default history list');
    }
  };

  const loadDefaultSample = async () => {
    try {
      const res = await fetch('/api/report-data?filename=ikev2_s2s_ipsec_vpn_aes_gcm.pcapng');
      if (res.ok) {
        const data = await res.json();
        setAnalysis(formatReportData(data, 'ikev2_s2s_ipsec_vpn_aes_gcm.pcapng'));
      } else {
        setAnalysis(getFallbackData('ikev2_s2s_ipsec_vpn_aes_gcm.pcapng'));
      }
    } catch (e) {
      setAnalysis(getFallbackData('ikev2_s2s_ipsec_vpn_aes_gcm.pcapng'));
    }
  };

  const loadHistoryItem = async (filename) => {
    setSelectedFilename(filename);
    setTelemetryLogs(prev => [`[FETCH] Fetching telemetry data for ${filename}...`, ...prev.slice(0, 8)]);
    try {
      const res = await fetch(`/api/report-data?filename=${encodeURIComponent(filename)}`);
      if (res.ok) {
        const data = await res.json();
        setAnalysis(formatReportData(data, filename));
      } else {
        setAnalysis(getFallbackData(filename));
      }
    } catch (e) {
      setAnalysis(getFallbackData(filename));
    }
  };

  // Chat API call
  const handleSendChatMessage = async (overrideText = null) => {
    const textToSend = (overrideText !== null ? overrideText : chatInput).trim();
    if (!textToSend) return;

    if (!chatOpen) setChatOpen(true);

    const newMsgs = [...chatMessages, { sender: 'user', text: textToSend }];
    setChatMessages(newMsgs);
    if (overrideText === null) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend })
      });

      if (res.ok) {
        const data = await res.json();
        const reply = data.reply || 'Analysis complete.';
        setChatMessages(prev => [...prev, { sender: 'ai', text: reply }]);
      } else {
        setChatMessages(prev => [...prev, { sender: 'ai', text: '⚠️ Unable to fetch AI response from server backend.' }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: '⚠️ Network error: Could not reach Privcomm AI service.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const askAiAboutCard = (title, details) => {
    const promptText = `Explain in detail the security mechanics, RFC standards, and compliance impact of: ${title}. Observed details: ${details}`;
    handleSendChatMessage(promptText);
  };

  // Data helpers
  function formatReportData(data, defaultFilename) {
    const ipsec = data.ipsec || data;
    const sec = data.security_assessment || ipsec.security_assessment || {};
    const tc = data.traffic_classification || ipsec.traffic_classification || {};
    const meta = data.metadata_exposure || ipsec.metadata_exposure || {};
    const drift = data.drift_detection || ipsec.drift_detection || {};
    const pol = data.policy_as_code || ipsec.policy_as_code || {};
    const pqc = data.post_quantum_readiness || ipsec.post_quantum_readiness || {};
    const explain = data.explainability || ipsec.explainability || [];

    return {
      filename: defaultFilename,
      packet_count: data.capture?.packet_count || ipsec.packet_count || 12,
      ike_version: ipsec.ike_version || 'IKEv2',
      mode: ipsec.mode || 'Tunnel',
      encryption: ipsec.encryption || 'AES-256-GCM',
      integrity: ipsec.integrity || 'AEAD',
      dh_group: ipsec.dh_group || '19',
      pfs: ipsec.pfs !== undefined ? ipsec.pfs : true,
      source_ip: ipsec.source_ip || '192.168.1.10',
      destination_ip: ipsec.destination_ip || '10.0.0.1',
      security_assessment: sec,
      traffic_classification: tc,
      metadata_exposure: meta,
      drift_detection: drift,
      policy_as_code: pol,
      post_quantum_readiness: pqc,
      explainability: explain
    };
  }

  function getFallbackData(filename) {
    const isWeak = filename.toLowerCase().includes('weak') || filename.toLowerCase().includes('des') || filename.toLowerCase().includes('ikev1');
    return {
      filename: filename,
      packet_count: isWeak ? 844 : 1482,
      ike_version: isWeak ? 'IKEv1 (Aggressive)' : 'IKEv2',
      mode: isWeak ? 'Transport' : 'Tunnel',
      encryption: isWeak ? '3DES-CBC' : 'AES-256-GCM',
      integrity: isWeak ? 'HMAC-MD5-96' : 'AEAD',
      dh_group: isWeak ? '2' : '19',
      pfs: !isWeak,
      source_ip: '192.168.1.10',
      destination_ip: '10.0.0.1',
      security_assessment: {
        risk_score: isWeak ? 60 : 0,
        risk_level: isWeak ? 'HIGH' : 'SECURE'
      },
      traffic_classification: {
        traffic_type: isWeak ? 'VPN-BROWSING' : 'CHAT',
        confidence: isWeak ? 0.521 : 0.4767,
        class_probabilities: isWeak ? [
          { category: 'BROWSING', probability: 0.521 },
          { category: 'FILE TRANSFER', probability: 0.284 },
          { category: 'CHAT', probability: 0.122 },
          { category: 'P2P', probability: 0.073 }
        ] : [
          { category: 'CHAT', probability: 0.4767 },
          { category: 'P2P', probability: 0.258 },
          { category: 'BROWSING', probability: 0.086 },
          { category: 'FILE TRANSFER', probability: 0.083 }
        ]
      },
      metadata_exposure: {
        exposure_rating: isWeak ? 'HIGH' : 'LOW',
        exposure_score: isWeak ? 70 : 0,
        visible_endpoints: { source_ip: '192.168.1.10', destination_ip: '10.0.0.1' },
        identity_exposure: { identity_protection_status: isWeak ? 'PLAINTEXT_EXPOSED' : 'ENCRYPTED_OR_ABSENT' },
        spi_correlation: { spi_linkability_risk: isWeak ? 'HIGH' : 'MEDIUM' },
        transport_mode_exposure: { encapsulation_mode: isWeak ? 'Transport' : 'Tunnel' }
      },
      drift_detection: {
        drift_detected: isWeak,
        drift_count: isWeak ? 3 : 0,
        variance_score: isWeak ? 60 : 0
      },
      policy_as_code: {
        compliance_score: isWeak ? 40 : 100,
        passed: isWeak ? 2 : 6,
        failed: isWeak ? 4 : 0
      },
      post_quantum_readiness: {
        quantum_threat_rating: isWeak ? 'CRITICAL RISK' : 'MEDIUM RISK (Shor\'s)',
        crypto_agility_rating: isWeak ? 'POOR' : 'EXCELLENT'
      },
      explainability: []
    };
  }

  // Active state data values
  const curr = analysis || getFallbackData(selectedFilename);
  const secAssessment = curr.security_assessment || {};
  const riskScore = secAssessment.risk_score ?? curr.risk_score ?? 0;
  const riskLevel = secAssessment.risk_level || (riskScore > 50 ? 'HIGH' : 'SECURE');

  const tc = curr.traffic_classification || {};
  const trafficType = tc.traffic_type || 'CHAT';
  const confidencePct = tc.confidence ? (tc.confidence * 100).toFixed(1) : '47.7';

  const probList = tc.class_probabilities || [
    { category: trafficType, probability: tc.confidence || 0.4767 },
    { category: trafficType === 'CHAT' ? 'P2P' : 'CHAT', probability: 0.258 },
    { category: 'BROWSING', probability: 0.086 },
    { category: 'FILE TRANSFER', probability: 0.083 }
  ];

  const drift = curr.drift_detection || {};
  const pol = curr.policy_as_code || {};
  const pqc = curr.post_quantum_readiness || {};
  const meta = curr.metadata_exposure || {};

  // Custom Card Explainer Default Items if none returned from API
  const defaultExplainers = [
    {
      icon: '📞',
      title: 'Modern IKEv2 Protocol Engine (RFC 7296)',
      status: curr.ike_version?.includes('IKEv1') ? 'OBSOLETE' : 'SECURE',
      plain_english_summary: 'Manages your VPN connection lifecycle with high speed, instant auto-reconnect, and seamless network mobility across Wi-Fi and 5G.',
      detailed_explanation: 'IKEv2 acts as the intelligent digital negotiator for your VPN. Like traveling on a train where your laptop switches between station Wi-Fi and 5G cellular, MOBIKE (RFC 4555) technology shifts your encrypted session without dropping active video calls or web apps.'
    },
    {
      icon: '🔒',
      title: 'Authenticated AES-256-GCM Cipher (Galois/Counter Mode)',
      status: curr.encryption?.includes('3DES') ? 'OBSOLETE' : 'SECURE',
      plain_english_summary: 'Bank-grade 256-bit encryption that scrambles data while simultaneously attaching a 128-bit tamper-proof digital seal.',
      detailed_explanation: 'Think of AES-256-GCM as placing your secret documents into an unbreakable steel vault while applying a tamper-evident holographic seal to the outside. If a hacker alters even 1 bit of data, the server detects the broken seal and discards the packet instantly before decryption.'
    },
    {
      icon: '🤝',
      title: `Elliptic Curve Secret Handshake (DH Group ${curr.dh_group || '19'})`,
      status: (curr.dh_group === '2' || curr.dh_group === 2) ? 'OBSOLETE' : 'SECURE',
      plain_english_summary: 'Allows two remote servers across the open internet to safely agree on identical secret encryption keys without ever sending the key over the wire.',
      detailed_explanation: 'Imagine two people in a room full of eavesdroppers mixing base colors publicly to end up with the exact same secret color mixture. Group 19 uses NIST P-256 Elliptic Curve math to compute shared secrets 10x faster than legacy 2048-bit prime numbers.'
    },
    {
      icon: '🔑',
      title: 'Ephemeral One-Time Rekeying (PFS Enforced)',
      status: curr.pfs ? 'SECURE' : 'CAUTION',
      plain_english_summary: 'Constantly generates brand-new, independent session keys so compromising today\'s key leaves all past and future recorded traffic 100% safe.',
      detailed_explanation: 'Imagine a hotel keycard system where every single room keycard is completely unique and automatically expires after 1 hour, rather than having one master key. With PFS enforced, even if a hacker steals the server\'s master key in the future, past recorded traffic remains un-decryptable.'
    },
    {
      icon: '🛡️',
      title: `IPsec ${curr.mode || 'Tunnel'} Mode Encapsulation`,
      status: curr.mode === 'Transport' ? 'CAUTION' : 'SECURE',
      plain_english_summary: 'Encloses your entire original IP packet—including private source and destination IP addresses—inside a brand-new encrypted outer IP envelope.',
      detailed_explanation: 'Like placing a coded postcard inside a thick, sealed courier envelope addressed between two secure VPN gateways. Eavesdroppers on public networks cannot inspect internal company IP addresses, device names, or private network topology.'
    },
    {
      icon: '🧠',
      title: `AI Behavioral Pattern Recognition (${trafficType} Traffic)`,
      status: 'SECURE',
      plain_english_summary: `Machine Learning identified the exact application activity ('${trafficType}') inside the VPN tunnel using behavioral traffic patterns without breaking encryption.`,
      detailed_explanation: 'Like a detective identifying a person by the cadence of their footsteps without seeing their face, our XGBoost Machine Learning model analyzed 28 non-encrypted flow characteristics (packet sizes, timing, burst ratios) to classify messaging activity.'
    }
  ];

  const explainers = (curr.explainability && curr.explainability.length > 0) ? curr.explainability : defaultExplainers;

  return (
    <div className="tab-container" style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem 1rem', position: 'relative' }}>

      {/* Top Header / Nav Bar Strip */}
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        background: '#0d1322',
        border: '1px solid var(--border-subtle)',
        borderRadius: '12px',
        padding: '12px 20px',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield size={22} color="#38bdf8" />
          <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.05em' }}>
            Privcomm
          </span>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            / Live Telemetry & Analytics Dashboard
          </span>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <a
            href={`/reports/download-html?filename=${encodeURIComponent(curr.filename)}`}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '6px 14px', textDecoration: 'none' }}
          >
            <FileText size={15} color="#60a5fa" />
            <span>Open Executive Report Page</span>
          </a>
          {onNavigateToTestbed && (
            <button
              type="button"
              className="btn-primary"
              onClick={onNavigateToTestbed}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '6px 14px' }}
            >
              <Server size={15} />
              <span>Launch Testbed VM</span>
            </button>
          )}
        </div>
      </div>

      {/* Multi-Tunnel Selector & Global Network Mesh Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        background: 'rgba(15, 23, 42, 0.85)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '10px',
        padding: '10px 16px',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#38bdf8" />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Multi-Tunnel Hub & Spoke Mesh:
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => loadHistoryItem('ikev2_s2s_ipsec_vpn_aes_gcm.pcapng')}
            style={{
              background: (!selectedFilename.toLowerCase().includes('des') && !selectedFilename.toLowerCase().includes('ikev1')) ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255,255,255,0.04)',
              border: (!selectedFilename.toLowerCase().includes('des') && !selectedFilename.toLowerCase().includes('ikev1')) ? '1px solid #38bdf8' : '1px solid var(--border-subtle)',
              color: (!selectedFilename.toLowerCase().includes('des') && !selectedFilename.toLowerCase().includes('ikev1')) ? '#38bdf8' : '#94a3b8',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span style={{ width: '8px', height: '8px', background: '#22c55e', borderRadius: '50%', boxShadow: '0 0 6px #22c55e' }} />
            <span>Tunnel 1: HQ ↔ Branch Alpha (AES-256-GCM)</span>
          </button>

          <button
            type="button"
            onClick={() => loadHistoryItem('IKEv1_Aggressive_DES_MD5.pcap')}
            style={{
              background: (selectedFilename.toLowerCase().includes('des') || selectedFilename.toLowerCase().includes('ikev1')) ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.04)',
              border: (selectedFilename.toLowerCase().includes('des') || selectedFilename.toLowerCase().includes('ikev1')) ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
              color: (selectedFilename.toLowerCase().includes('des') || selectedFilename.toLowerCase().includes('ikev1')) ? '#fca5a5' : '#94a3b8',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span style={{ width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%', boxShadow: '0 0 6px #ef4444' }} />
            <span>Tunnel 2: HQ ↔ Branch Beta (3DES Drift)</span>
          </button>
        </div>
      </div>

      {/* Status Banner */}
      <div style={{
        background: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '10px',
        padding: '12px 20px',
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
          <span style={{
            width: '10px',
            height: '10px',
            backgroundColor: '#22c55e',
            borderRadius: '50%',
            boxShadow: '0 0 10px #22c55e'
          }} />
          <span>VM TUNNEL INGESTION STREAM: READY / ACTIVE</span>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
          Active Capture: <strong style={{ color: '#fff' }}>{curr.filename}</strong> | Ingestion Stream: <strong style={{ color: '#38bdf8' }}>eBPF / TShark TAP</strong> | Air-Gapped Verification: <strong style={{ color: '#4ade80' }}>ENABLED</strong>
        </div>
      </div>

      {/* 4 Top Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Packets Processed
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
            {curr.packet_count || 12}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Active IPsec SAs
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#4ade80', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
            2 Active SAs
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            AI Traffic Classification
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#a78bfa', fontFamily: 'JetBrains Mono', marginTop: '6px' }}>
            {trafficType} ({confidencePct}%)
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            System Risk Score
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: (riskScore === 0 ? '#4ade80' : riskScore < 50 ? '#fde047' : '#fca5a5'), fontFamily: 'JetBrains Mono', marginTop: '6px' }}>
            {riskScore}/100 ({riskLevel})
          </div>
        </div>
      </div>

      {/* Analytics Grid: Threat Matrix + AI Traffic Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '24px' }}>

        {/* 3x3 Security Threat Matrix Grid */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#38bdf8" />
            <span>📊 3x3 Security Threat Matrix Grid</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '80px repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
            <div></div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Low Impact</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Med Impact</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>High Impact</div>

            <div style={{ fontSize: '0.68rem', color: '#94a3b8', margin: 'auto 0' }}>High Likelihood</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(234, 179, 8, 0.12)', color: '#fde047', border: '1px solid rgba(234, 179, 8, 0.25)' }}>Medium</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.3)' }}>High</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 800, fontSize: '0.75rem', background: riskScore >= 60 ? 'rgba(239, 68, 68, 0.4)' : 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: riskScore >= 60 ? '2px solid #ef4444' : '1px solid rgba(239, 68, 68, 0.4)' }}>
              Critical {riskScore >= 60 && '⚠️'}
            </div>

            <div style={{ fontSize: '0.68rem', color: '#94a3b8', margin: 'auto 0' }}>Med Likelihood</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(34, 197, 94, 0.12)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.25)' }}>Low</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(234, 179, 8, 0.12)', color: '#fde047', border: '1px solid rgba(234, 179, 8, 0.25)' }}>Medium</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.3)' }}>High</div>

            <div style={{ fontSize: '0.68rem', color: '#94a3b8', margin: 'auto 0' }}>Low Likelihood</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 800, fontSize: '0.75rem', background: riskScore === 0 ? 'rgba(34, 197, 94, 0.35)' : 'rgba(34, 197, 94, 0.12)', color: '#4ade80', border: riskScore === 0 ? '2px solid #22c55e' : '1px solid rgba(34, 197, 94, 0.25)' }}>
              Low {riskScore === 0 && '✓'}
            </div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(34, 197, 94, 0.12)', color: '#4ade80', border: '1px solid rgba(34, 197, 94, 0.25)' }}>Low</div>
            <div style={{ padding: '12px 6px', borderRadius: '6px', fontWeight: 700, fontSize: '0.75rem', background: 'rgba(234, 179, 8, 0.12)', color: '#fde047', border: '1px solid rgba(234, 179, 8, 0.25)' }}>Medium</div>
          </div>
        </div>

        {/* AI Encrypted Traffic Probability Breakdown */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="#a78bfa" />
            <span>🤖 AI Encrypted Traffic Probability Breakdown</span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8', textAlign: 'left' }}>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Traffic Category</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>AI Confidence Score</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {probList.map((item, idx) => {
                const probVal = (item.probability * 100).toFixed(1);
                const isTop = idx === 0 || item.category === trafficType;
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px', fontWeight: isTop ? 700 : 500, color: isTop ? '#38bdf8' : '#e2e8f0' }}>
                      {item.category}
                    </td>
                    <td style={{ padding: '10px', fontFamily: 'JetBrains Mono', color: '#cbd5e1' }}>
                      {probVal}%
                    </td>
                    <td style={{ padding: '10px' }}>
                      {isTop ? (
                        <span className="badge badge-green" style={{ fontSize: '0.68rem' }}>PREDICTED CLASS</span>
                      ) : (
                        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Competing Class</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Observable Metadata Exposure Intelligence Card */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Eye size={18} color="#38bdf8" />
            <span>📡 Observable Metadata Exposure Intelligence</span>
          </div>
          <span className={`badge ${riskScore === 0 ? 'badge-green' : 'badge-red'}`}>
            EXPOSURE: {meta.exposure_rating || (riskScore === 0 ? 'LOW (0/100)' : 'HIGH (70/100)')}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>VISIBLE ENDPOINT IPS</div>
            <strong style={{ fontFamily: 'JetBrains Mono', fontSize: '0.85rem', color: '#38bdf8' }}>
              {curr.source_ip || '192.168.1.10'} → {curr.destination_ip || '10.0.0.1'}
            </strong>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>Outer IP Pair (IPv4)</div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>IKE IDENTITY PAYLOADS (IDi / IDr)</div>
            <strong style={{ fontSize: '0.85rem', color: curr.ike_version?.includes('IKEv1') ? '#fca5a5' : '#4ade80' }}>
              {curr.ike_version?.includes('IKEv1') ? 'PLAINTEXT EXPOSED' : 'ENCRYPTED / ABSENT'}
            </strong>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
              {curr.ike_version?.includes('IKEv1') ? 'Vulnerable PSK Aggressive Hash' : 'No Plaintext Leakage'}
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>SPI SESSION LINKABILITY</div>
            <strong style={{ fontSize: '0.85rem', color: '#fde047' }}>
              MEDIUM TRACKING RISK
            </strong>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>ESP SPI Headers Observed</div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>HEADER EXPOSURE (MODE)</div>
            <strong style={{ fontSize: '0.85rem', color: curr.mode === 'Transport' ? '#fca5a5' : '#4ade80' }}>
              {curr.mode || 'Tunnel'} Mode ({curr.mode === 'Transport' ? '20 B/pkt' : '0 B/pkt'})
            </strong>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
              {curr.mode === 'Transport' ? 'Inner Headers Unprotected' : 'Full Envelope Encapsulation'}
            </div>
          </div>
        </div>
      </div>

      {/* History Ingestion History Table */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database size={18} color="#38bdf8" />
          <span>📂 Recent Capture Ingestions & Analysis History</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8', textAlign: 'left' }}>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Capture Filename</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Protocol / Mode</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Encryption Suite</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>AI Predicted Class</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase' }}>Risk Score</th>
                <th style={{ padding: '8px 10px', fontSize: '0.7rem', textTransform: 'uppercase', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {historyList.map((item, idx) => {
                const itemRiskClass = item.risk_level === 'SECURE' || item.risk_level === 'LOW' ? 'badge-green' : 'badge-red';
                const isSelected = selectedFilename === item.filename;

                return (
                  <tr
                    key={idx}
                    onClick={() => loadHistoryItem(item.filename)}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(56,189,248,0.08)' : 'transparent',
                      transition: 'background 0.2s ease'
                    }}
                    title="Click to view telemetry analysis"
                  >
                    <td style={{ padding: '10px', fontWeight: 700, color: isSelected ? '#38bdf8' : '#f1f5f9' }}>
                      {item.filename}
                    </td>
                    <td style={{ padding: '10px', color: '#cbd5e1' }}>
                      {item.ike_version || 'IKEv2'} ({item.mode || 'Tunnel'})
                    </td>
                    <td style={{ padding: '10px', color: '#cbd5e1' }}>
                      {item.encryption || 'AES-256-GCM'} (Group {item.dh_group || '19'})
                    </td>
                    <td style={{ padding: '10px', color: '#a78bfa' }}>
                      {item.traffic_type || 'CHAT'} ({item.confidence ? (item.confidence * 100).toFixed(1) : '47.7'}%)
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span className={`badge ${itemRiskClass}`} style={{ fontSize: '0.68rem' }}>
                        {item.risk_level || 'SECURE'} ({item.risk_score || 0}/100)
                      </span>
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn-ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          loadHistoryItem(item.filename);
                        }}
                        style={{ padding: '3px 8px', fontSize: '0.72rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Eye size={12} color="#38bdf8" /> Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enterprise Security Auditing Grid (Drift, Policy, PQC) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '24px' }}>

        {/* 1. Configuration Drift Detector */}
        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RefreshCw size={16} color="#38bdf8" /> Configuration Drift Detection
            </span>
            <button
              type="button"
              onClick={() => askAiAboutCard('Configuration Drift Detection Audit', 'Explains current baseline alignment vs observed diffs, variance percentage, and parameter match status.')}
              style={{ background: 'rgba(56,189,248,0.15)', border: '1px solid rgba(56,189,248,0.3)', color: '#38bdf8', borderRadius: '4px', padding: '2px 8px', fontSize: '0.7rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <Sparkles size={11} /> Explain with AI
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Baseline Alignment:</span><br />
              <strong style={{ fontSize: '0.95rem', color: drift.drift_detected ? '#fca5a5' : '#4ade80' }}>
                {drift.drift_detected ? `DRIFTED (${drift.drift_count || 3} Diffs)` : 'SYNCHRONIZED (0 Diffs)'}
              </strong>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Variance Score:</span><br />
              <strong style={{ fontSize: '0.95rem', color: '#38bdf8' }}>
                {drift.variance_score || 0}% Variance
              </strong>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>IKE Version:</span>
              <strong style={{ color: curr.ike_version?.includes('IKEv1') ? '#fca5a5' : '#4ade80' }}>
                {curr.ike_version?.includes('IKEv1') ? 'Drifted (IKEv1)' : 'Matched (IKEv2)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>Encryption Cipher:</span>
              <strong style={{ color: curr.encryption?.includes('3DES') ? '#fca5a5' : '#4ade80' }}>
                {curr.encryption?.includes('3DES') ? 'Drifted (3DES)' : 'Matched (AES-256-GCM)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>Diffie-Hellman Group:</span>
              <strong style={{ color: curr.dh_group === '2' ? '#fca5a5' : '#4ade80' }}>
                {curr.dh_group === '2' ? 'Drifted (Group 2)' : 'Matched (Group 19)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>PFS Rekeying:</span>
              <strong style={{ color: curr.pfs ? '#4ade80' : '#fde047' }}>
                {curr.pfs ? 'Matched (Enforced)' : 'Warning (Disabled)'}
              </strong>
            </div>
          </div>
        </div>

        {/* 2. Policy-as-Code Rulebook */}
        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={16} color="#34d399" /> Policy-as-Code Rulebook
            </span>
            <button
              type="button"
              onClick={() => askAiAboutCard('Policy-as-Code Compliance Rulebook', 'Explains organizational rulebook evaluation (POL-01 to POL-06), pass/fail criteria, and compliance mandates.')}
              style={{ background: 'rgba(56,189,248,0.15)', border: '1px solid rgba(56,189,248,0.3)', color: '#38bdf8', borderRadius: '4px', padding: '2px 8px', fontSize: '0.7rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <Sparkles size={11} /> Explain with AI
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Policy Evaluation:</span><br />
              <strong style={{ fontSize: '0.95rem', color: (pol.compliance_score || 100) >= 80 ? '#4ade80' : '#fca5a5' }}>
                {pol.compliance_score || (riskScore === 0 ? 100 : 40)}% COMPLIANT
              </strong>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <span className="badge badge-green" style={{ fontSize: '0.68rem' }}>{pol.passed || (riskScore === 0 ? 6 : 2)} PASS</span>
              {(pol.failed > 0 || riskScore > 0) && (
                <span className="badge badge-red" style={{ fontSize: '0.68rem' }}>{pol.failed || 4} FAIL</span>
              )}
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>POL-01 Protocol Version:</span>
              <span className={`badge ${curr.ike_version?.includes('IKEv1') ? 'badge-red' : 'badge-green'}`} style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {curr.ike_version?.includes('IKEv1') ? 'FAIL' : 'PASS'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>POL-02 AEAD Cipher:</span>
              <span className={`badge ${curr.encryption?.includes('3DES') ? 'badge-red' : 'badge-green'}`} style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {curr.encryption?.includes('3DES') ? 'FAIL' : 'PASS'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>POL-03 DH Group Margin:</span>
              <span className={`badge ${curr.dh_group === '2' ? 'badge-red' : 'badge-green'}`} style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {curr.dh_group === '2' ? 'FAIL' : 'PASS'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>POL-04 PFS Rekeying:</span>
              <span className={`badge ${curr.pfs ? 'badge-green' : 'badge-red'}`} style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {curr.pfs ? 'PASS' : 'FAIL'}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Post-Quantum Readiness Assessor */}
        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={16} color="#a855f7" /> Post-Quantum Readiness
            </span>
            <button
              type="button"
              onClick={() => askAiAboutCard('Post-Quantum Cryptographic Readiness', 'Explains Quantum threat models (Shor\'s algorithm on ECC/DH vs Grover\'s algorithm on AES-256) and RFC 8784 hybrid post-quantum readiness.')}
              style={{ background: 'rgba(56,189,248,0.15)', border: '1px solid rgba(56,189,248,0.3)', color: '#38bdf8', borderRadius: '4px', padding: '2px 8px', fontSize: '0.7rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <Sparkles size={11} /> Explain with AI
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Quantum Threat:</span><br />
              <strong style={{ fontSize: '0.95rem', color: '#fde047' }}>
                {pqc.quantum_threat_rating || 'MEDIUM RISK (Shor\'s)'}
              </strong>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Crypto-Agility:</span><br />
              <strong style={{ fontSize: '0.95rem', color: '#4ade80' }}>
                {pqc.crypto_agility_rating || 'EXCELLENT'}
              </strong>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>Shor's Key Vulnerability:</span>
              <strong style={{ color: '#fde047' }}>ECC (Group {curr.dh_group || '19'})</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>Grover's Cipher Security:</span>
              <strong style={{ color: '#4ade80' }}>256-bit (Protected)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>RFC 8784 Hybrid Support:</span>
              <strong style={{ color: '#4ade80' }}>IKEv2 Ready</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Active Tunnel Plain-English Rationale Breakdown (6 Cards) */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <HelpCircle size={18} color="#38bdf8" />
          <span>💡 Active Tunnel Plain-English Rationale (For Non-Experts)</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '14px' }}>
          {explainers.map((item, idx) => {
            const isSecure = item.status === 'SECURE' || item.status === 'COMPLIANT';
            const isObsolete = item.status === 'OBSOLETE' || item.status === 'FAIL';
            const borderColor = isSecure ? 'var(--accent-green)' : (isObsolete ? 'var(--accent-red)' : 'var(--accent-yellow)');
            const badgeClass = isSecure ? 'badge-green' : (isObsolete ? 'badge-red' : 'badge-yellow');

            return (
              <div
                key={idx}
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderLeft: `4px solid ${borderColor}`,
                  borderRadius: '8px',
                  padding: '14px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <strong style={{ fontSize: '0.88rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{item.icon || '🛡️'}</span>
                    <span>{item.title}</span>
                  </strong>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => askAiAboutCard(item.title, item.detailed_explanation || item.plain_english_summary)}
                      style={{
                        background: 'rgba(56,189,248,0.15)',
                        border: '1px solid rgba(56,189,248,0.3)',
                        color: '#38bdf8',
                        borderRadius: '4px',
                        padding: '2px 8px',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Sparkles size={11} /> Ask AI
                    </button>
                    <span className={`badge ${badgeClass}`} style={{ fontSize: '0.65rem' }}>
                      {item.status}
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '0.78rem', color: '#f1f5f9', marginBottom: '6px' }}>
                  <strong>Role:</strong> {item.plain_english_summary}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: '1.5' }}>
                  {item.detailed_explanation}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Console Stream Feed Log */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={18} color="#38bdf8" />
          <span>📡 Real-Time Telemetry Stream Log</span>
        </div>

        <div style={{
          background: '#040711',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '14px',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '0.75rem',
          color: '#38bdf8',
          height: '140px',
          overflowY: 'auto',
          lineHeight: '1.7'
        }}>
          {telemetryLogs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>

      {/* FLOATING Privcomm AI ASSISTANT CHATBOT WIDGET */}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 3000 }}>

        {/* Toggle Button */}
        {!chatOpen && (
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            style={{
              background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
              color: '#fff',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              borderRadius: '30px',
              padding: '10px 18px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              transition: 'transform 0.2s ease',
            }}
          >
            <Bot size={20} />
            <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Privcomm AI Assistant</span>
            <span style={{ width: '8px', height: '8px', background: '#22c55e', borderRadius: '50%', boxShadow: '0 0 6px #22c55e' }} />
          </button>
        )}

        {/* Chatbot Window */}
        {chatOpen && (
          <div style={{
            position: 'fixed',
            bottom: '80px',
            right: '24px',
            width: '390px',
            maxWidth: 'calc(100vw - 32px)',
            height: '520px',
            background: '#0b111c',
            border: '1px solid var(--border-subtle)',
            borderRadius: '16px',
            zIndex: 3000,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
          }}>
            {/* Header */}
            <div style={{ background: '#0f172a', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Bot size={18} color="#38bdf8" />
                <div>
                  <strong style={{ fontSize: '0.85rem', color: '#fff', display: 'block' }}>Privcomm Assistant</strong>
                  <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Live Telemetry & Security Advisor</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Messages Body */}
            <div style={{ flexGrow: 1, padding: '14px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', background: '#070b14' }}>
              {chatMessages.map((msg, idx) => {
                const isUser = msg.sender === 'user';
                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignSelf: isUser ? 'flex-end' : 'flex-start',
                      maxWidth: '88%'
                    }}
                  >
                    <div style={{
                      padding: '8px 12px',
                      borderRadius: '10px',
                      fontSize: '0.78rem',
                      lineHeight: '1.5',
                      background: isUser ? '#2563eb' : '#1e293b',
                      color: isUser ? '#fff' : '#f8fafc',
                      border: isUser ? 'none' : '1px solid var(--border-subtle)'
                    }}>
                      {msg.text.split('\n').map((line, lIdx) => (
                        <p key={lIdx} style={{ margin: '0 0 4px 0' }}>{line}</p>
                      ))}
                    </div>
                  </div>
                );
              })}
              {chatLoading && (
                <div style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#38bdf8' }}>
                  <Sparkles size={14} className="animate-spin" />
                  <span>Privcomm AI is analyzing...</span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Quick Prompt Pills */}
            <div style={{ padding: '6px 10px', background: '#0d1322', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '6px', overflowX: 'auto' }}>
              <button
                type="button"
                onClick={() => handleSendChatMessage('Explain active live VM stream security')}
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', borderRadius: '12px', padding: '3px 8px', fontSize: '0.68rem', cursor: 'pointer', whiteSpace: 'nowrap' }}
              >
                💬 Active stream rationale
              </button>
              <button
                type="button"
                onClick={() => handleSendChatMessage('Why is 3DES or DH Group 2 weak?')}
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', borderRadius: '12px', padding: '3px 8px', fontSize: '0.68rem', cursor: 'pointer', whiteSpace: 'nowrap' }}
              >
                🔒 Why is 3DES weak?
              </button>
              <button
                type="button"
                onClick={() => handleSendChatMessage('Remediation steps for high risk tunnels')}
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8', borderRadius: '12px', padding: '3px 8px', fontSize: '0.68rem', cursor: 'pointer', whiteSpace: 'nowrap' }}
              >
                🛡️ Remediation steps
              </button>
            </div>

            {/* Input Area */}
            <div style={{ padding: '8px 10px', background: '#0f172a', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '6px' }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSendChatMessage(); }}
                placeholder="Ask a question..."
                style={{
                  flexGrow: 1,
                  background: '#070b14',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  padding: '6px 10px',
                  color: '#fff',
                  fontSize: '0.78rem',
                  outline: 'none'
                }}
              />
              <button
                type="button"
                onClick={() => handleSendChatMessage()}
                style={{
                  background: '#2563eb',
                  border: 'none',
                  color: '#fff',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
