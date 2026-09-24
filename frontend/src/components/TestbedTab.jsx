import React, { useState, useEffect, useRef } from 'react';
import {
  Server,
  Play,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Terminal,
  Download,
  Shield,
  Layers,
  Zap,
  Cpu,
  ArrowRight,
  Clock,
  Radio
} from 'lucide-react';

export default function TestbedTab({ onNavigateToAnalysis }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('ikev2-aes-gcm-compliant');
  const [customMode, setCustomMode] = useState(false);
  
  // Custom Config Form
  const [customConfig, setCustomConfig] = useState({
    name: 'Custom strongSwan Tunnel',
    ike_version: 'IKEv2',
    encryption: 'AES-256-GCM',
    integrity: 'None (AEAD)',
    dh_group: '19 (ECP-256)',
    pfs: true,
    auth_method: 'PSK',
    traffic_profile: 'HTTP_GET',
    packet_count: 25,
    traffic_duration_sec: 5
  });

  // Topology Config
  const [topology, setTopology] = useState({
    initiator_ip: '192.168.56.10',
    responder_ip: '192.168.56.20',
    observer_ip: '192.168.56.30'
  });

  // Job execution state
  const [activeJob, setActiveJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [jobHistory, setJobHistory] = useState([]);
  const logContainerRef = useRef(null);

  // Fetch scenarios and recent jobs on mount
  useEffect(() => {
    fetchScenarios();
    fetchJobHistory();
  }, []);

  // Poll active job status
  useEffect(() => {
    let interval = null;
    if (activeJob && (activeJob.state === 'QUEUED' || activeJob.state === 'PROVISIONING' || activeJob.state === 'CAPTURING' || activeJob.state === 'ANALYZING')) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/testbed/jobs/${activeJob.id}`);
          if (res.ok) {
            const data = await res.json();
            setActiveJob(data);
            if (data.state === 'COMPLETED' || data.state === 'FAILED') {
              setIsRunning(false);
              fetchJobHistory();
            }
          }
        } catch (err) {
          console.error('Failed to poll testbed status:', err);
        }
      }, 1200);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeJob]);

  // Scroll terminal logs to bottom automatically
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [activeJob?.logs]);

  const fetchScenarios = async () => {
    try {
      const res = await fetch('/api/testbed/scenarios');
      if (res.ok) {
        const data = await res.json();
        setScenarios(data);
      }
    } catch (e) {
      console.error('Failed to load scenarios', e);
    }
  };

  const fetchJobHistory = async () => {
    try {
      const res = await fetch('/api/testbed/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobHistory(data);
      }
    } catch (e) {
      console.error('Failed to load jobs', e);
    }
  };

  const handleLaunchScenario = async () => {
    setIsRunning(true);
    try {
      const payload = {
        topology: {
          initiator: { host: topology.initiator_ip, interface: 'eth1' },
          responder: { host: topology.responder_ip, interface: 'eth1' },
          observer: { host: topology.observer_ip, interface: 'eth1' }
        }
      };

      if (customMode) {
        payload.custom_scenario = {
          id: 'custom-' + Date.now(),
          ...customConfig,
          description: `Custom ${customConfig.ike_version} tunnel with ${customConfig.encryption}`,
          pre_shared_key: 'CyberSentinelKey2026'
        };
      } else {
        payload.scenario_id = selectedScenarioId;
      }

      const res = await fetch('/api/testbed/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`Error starting testbed: ${err.detail || 'Unknown error'}`);
        setIsRunning(false);
        return;
      }

      const data = await res.json();
      setActiveJob({
        id: data.job_id,
        scenario_name: data.scenario_name,
        state: 'QUEUED',
        progress_pct: 5,
        logs: ['[00:00:00] Job submitted to orchestrator. Waiting in queue...']
      });
    } catch (e) {
      alert(`Network error starting testbed: ${e.message}`);
      setIsRunning(false);
    }
  };

  const selectedPreset = scenarios.find((s) => s.id === selectedScenarioId);

  return (
    <div className="tab-container" style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header Banner */}
      <div className="section-header-badge" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
        <Server size={18} color="#38bdf8" />
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8', letterSpacing: '0.05em' }}>
          STRONGSWAN IPSEC VPN TESTBED
        </span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', margin: '0 0 0.5rem 0' }}>
            Multi-Node strongSwan Validation Environment
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', maxWidth: '800px', margin: 0 }}>
            Automated orchestration of strongSwan IPsec VPN endpoints (Initiator, Responder, and Observer).
            Deploys live cryptographic configurations, initiates IKE/ESP sessions, captures raw wire packets,
            and feeds them directly to the AI Security Engine.
          </p>
        </div>
      </div>

      {/* Grid Layout: Controls & Scenarios (Left) vs Live Execution Console (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Left Column: Scenarios & Topology */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Topology Overview Card */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Virtual Topology (Host-Only Network)
              </span>
              <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>3-VM MESH</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', textAlign: 'center' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '8px', padding: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 700 }}>VM 1 &bull; INITIATOR</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff', marginTop: '4px' }}>strongSwan 5.x</div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'JetBrains Mono', marginTop: '2px' }}>{topology.initiator_ip}</div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '8px', padding: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#c084fc', fontWeight: 700 }}>VM 2 &bull; RESPONDER</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff', marginTop: '4px' }}>strongSwan 5.x</div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'JetBrains Mono', marginTop: '2px' }}>{topology.responder_ip}</div>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(52, 211, 153, 0.2)', borderRadius: '8px', padding: '0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700 }}>VM 3 &bull; OBSERVER</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff', marginTop: '4px' }}>TShark / tcpdump</div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'JetBrains Mono', marginTop: '2px' }}>{topology.observer_ip}</div>
              </div>
            </div>
          </div>

          {/* Scenario Selector Card */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Cryptographic Test Scenario
              </span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  type="button"
                  className={`btn-ghost ${!customMode ? 'active' : ''}`}
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                  onClick={() => setCustomMode(false)}
                >
                  Presets ({scenarios.length})
                </button>
                <button
                  type="button"
                  className={`btn-ghost ${customMode ? 'active' : ''}`}
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                  onClick={() => setCustomMode(true)}
                >
                  Custom
                </button>
              </div>
            </div>

            {!customMode ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {scenarios.map((s) => {
                  const isSelected = selectedScenarioId === s.id;
                  return (
                    <div
                      key={s.id}
                      onClick={() => setSelectedScenarioId(s.id)}
                      style={{
                        padding: '0.85rem 1rem',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(56, 189, 248, 0.08)' : 'rgba(15, 23, 42, 0.4)',
                        border: isSelected ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.06)',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, color: isSelected ? '#38bdf8' : '#e2e8f0', fontSize: '0.88rem' }}>
                          {s.name}
                        </span>
                        {s.is_weak_compliance ? (
                          <span className="badge badge-red" style={{ fontSize: '0.65rem' }}>POLICY VIOLATION</span>
                        ) : (
                          <span className="badge badge-green" style={{ fontSize: '0.65rem' }}>COMPLIANT</span>
                        )}
                      </div>
                      <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                        {s.description}
                      </p>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <span className="badge badge-gray" style={{ fontSize: '0.68rem' }}>{s.ike_version}</span>
                        <span className="badge badge-gray" style={{ fontSize: '0.68rem' }}>{s.encryption}</span>
                        <span className="badge badge-gray" style={{ fontSize: '0.68rem' }}>DH {s.dh_group}</span>
                        <span className="badge badge-gray" style={{ fontSize: '0.68rem' }}>{s.traffic_profile}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>IKE Version</label>
                    <select
                      className="form-input"
                      value={customConfig.ike_version}
                      onChange={(e) => setCustomConfig({ ...customConfig, ike_version: e.target.value })}
                      style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                    >
                      <option value="IKEv2">IKEv2 (Modern RFC 7296)</option>
                      <option value="IKEv1">IKEv1 Main Mode</option>
                      <option value="IKEv1_Aggressive">IKEv1 Aggressive Mode</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Encryption Cipher</label>
                    <select
                      className="form-input"
                      value={customConfig.encryption}
                      onChange={(e) => setCustomConfig({ ...customConfig, encryption: e.target.value })}
                      style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                    >
                      <option value="AES-256-GCM">AES-256-GCM (AEAD)</option>
                      <option value="AES-128-GCM">AES-128-GCM (AEAD)</option>
                      <option value="AES-256-CBC">AES-256-CBC</option>
                      <option value="3DES-CBC">3DES-CBC (Legacy)</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>DH Key Exchange</label>
                    <select
                      className="form-input"
                      value={customConfig.dh_group}
                      onChange={(e) => setCustomConfig({ ...customConfig, dh_group: e.target.value })}
                      style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                    >
                      <option value="19 (ECP-256)">Group 19 (ECP-256)</option>
                      <option value="20 (ECP-384)">Group 20 (ECP-384)</option>
                      <option value="14 (MODP-2048)">Group 14 (MODP-2048)</option>
                      <option value="2 (MODP-1024)">Group 2 (MODP-1024 - Weak)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Traffic Generator</label>
                    <select
                      className="form-input"
                      value={customConfig.traffic_profile}
                      onChange={(e) => setCustomConfig({ ...customConfig, traffic_profile: e.target.value })}
                      style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                    >
                      <option value="HTTP_GET">Synthetic HTTP Requests</option>
                      <option value="ICMP_ECHO">ICMP Echo Tunnel Ping</option>
                      <option value="IPERF_BURST">iPerf3 High Throughput</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Launch Trigger Button */}
            <div style={{ marginTop: '1.25rem' }}>
              <button
                type="button"
                className="btn-primary"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  fontSize: '0.9rem',
                  fontWeight: 700
                }}
                disabled={isRunning}
                onClick={handleLaunchScenario}
              >
                {isRunning ? (
                  <>
                    <RefreshCw size={18} className="animate-spin" />
                    <span>Executing Testbed Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play size={18} fill="#030712" />
                    <span>Deploy & Run Testbed Scenario</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Execution Console & Live Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Live Pipeline Stepper */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Pipeline Execution State
              </span>
              {activeJob && (
                <span className={`badge ${activeJob.state === 'COMPLETED' ? 'badge-green' : activeJob.state === 'FAILED' ? 'badge-red' : 'badge-cyan'}`}>
                  {activeJob.state}
                </span>
              )}
            </div>

            {/* Stepper Steps */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '1rem' }}>
              {[
                { title: 'Provision', state: 'PROVISIONING' },
                { title: 'Capture Wire', state: 'CAPTURING' },
                { title: 'AI Analysis', state: 'ANALYZING' },
                { title: 'Complete', state: 'COMPLETED' }
              ].map((step, idx) => {
                const isPassed = activeJob?.state === 'COMPLETED' || 
                  (activeJob?.state === 'ANALYZING' && idx < 2) ||
                  (activeJob?.state === 'CAPTURING' && idx < 1);
                const isCurrent = activeJob?.state === step.state;
                return (
                  <div
                    key={step.title}
                    style={{
                      padding: '8px',
                      borderRadius: '6px',
                      textAlign: 'center',
                      background: isCurrent ? 'rgba(56, 189, 248, 0.15)' : isPassed ? 'rgba(52, 211, 153, 0.1)' : 'rgba(15, 23, 42, 0.5)',
                      border: isCurrent ? '1px solid #38bdf8' : isPassed ? '1px solid #34d399' : '1px solid rgba(255, 255, 255, 0.05)'
                    }}
                  >
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: isCurrent ? '#38bdf8' : isPassed ? '#34d399' : '#64748b' }}>
                      STEP {idx + 1}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: isCurrent || isPassed ? '#fff' : '#94a3b8', fontWeight: 600 }}>
                      {step.title}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Terminal Log Console */}
            <div
              ref={logContainerRef}
              style={{
                background: '#090d16',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: '8px',
                padding: '1rem',
                height: '240px',
                overflowY: 'auto',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '0.78rem',
                lineHeight: 1.6,
                color: '#cbd5e1'
              }}
            >
              <div style={{ color: '#38bdf8', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Terminal size={14} />
                <span>strongSwan Orchestrator Output Terminal</span>
              </div>
              {(!activeJob?.logs || activeJob.logs.length === 0) && (
                <div style={{ color: '#475569', fontStyle: 'italic', marginTop: '1rem' }}>
                  No active execution. Select a scenario on the left and click "Deploy & Run Testbed Scenario".
                </div>
              )}
              {activeJob?.logs?.map((l, i) => (
                <div key={i} style={{ color: l.includes('failed') || l.includes('FAILED') ? '#f87171' : l.includes('completed') || l.includes('COMPLETED') ? '#4ade80' : '#cbd5e1' }}>
                  {l}
                </div>
              ))}
            </div>

            {/* Post-Execution Actions */}
            {activeJob?.state === 'COMPLETED' && (
              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <a
                  href={`/api/testbed/jobs/${activeJob.id}/pcap`}
                  download
                  className="btn-ghost"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '0.5rem 0.85rem' }}
                >
                  <Download size={15} color="#38bdf8" />
                  <span>Download PCAP Wire Capture</span>
                </a>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '0.5rem 0.85rem' }}
                  onClick={() => {
                    if (onNavigateToAnalysis) onNavigateToAnalysis(activeJob.analysis_result);
                  }}
                >
                  <ArrowRight size={15} />
                  <span>Open Full Analysis in Live Workspace</span>
                </button>
              </div>
            )}
          </div>

          {/* Past Executions Table */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Testbed Execution Vault ({jobHistory.length})
              </span>
              <button
                type="button"
                className="btn-ghost"
                onClick={fetchJobHistory}
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
              >
                <RefreshCw size={12} /> Refresh
              </button>
            </div>

            <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
              {jobHistory.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#64748b', textAlign: 'center', padding: '1rem' }}>
                  No previous testbed executions recorded yet.
                </div>
              ) : (
                <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#64748b', textAlign: 'left', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <th style={{ padding: '6px 8px' }}>Time</th>
                      <th style={{ padding: '6px 8px' }}>Scenario</th>
                      <th style={{ padding: '6px 8px' }}>Status</th>
                      <th style={{ padding: '6px 8px' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobHistory.map((j) => (
                      <tr key={j.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                        <td style={{ padding: '6px 8px', color: '#94a3b8' }}>
                          {j.created_at ? new Date(j.created_at).toLocaleTimeString() : 'Recent'}
                        </td>
                        <td style={{ padding: '6px 8px', fontWeight: 600, color: '#e2e8f0' }}>
                          {j.scenario_name || 'strongSwan Tunnel'}
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <span className={`badge ${j.state === 'COMPLETED' ? 'badge-green' : 'badge-cyan'}`} style={{ fontSize: '0.65rem' }}>
                            {j.state}
                          </span>
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <button
                            type="button"
                            className="btn-ghost"
                            style={{ padding: '0.2rem 0.4rem', fontSize: '0.7rem' }}
                            onClick={() => setActiveJob(j)}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
