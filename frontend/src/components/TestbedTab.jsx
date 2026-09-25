import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Radio,
  Wifi,
  WifiOff,
  ChevronDown,
  ChevronRight,
  Activity,
  Eye,
  Send
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
  // In-memory event accumulator — merges events from each poll
  const [terminalEvents, setTerminalEvents] = useState([]);
  const lastEventIdRef = useRef(0);
  const [pollError, setPollError] = useState(false);
  const [expandedEvents, setExpandedEvents] = useState({});
  const activeJobIdRef = useRef(null);
  const feedRef = useRef(null);
  const isNearBottomRef = useRef(true);

  // Fetch scenarios and recent jobs on mount
  useEffect(() => {
    fetchScenarios();
    fetchJobHistory();
  }, []);

  // Smart auto-scroll: only scroll if already near the bottom
  const handleFeedScroll = useCallback(() => {
    if (!feedRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
    isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 80;
  }, []);

  useEffect(() => {
    if (feedRef.current && isNearBottomRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [terminalEvents]);

  // Poll active job status — uses since_id to only fetch new events
  useEffect(() => {
    const TERMINAL_STATES = ['COMPLETED', 'FAILED'];
    if (!activeJob || TERMINAL_STATES.includes(activeJob.state)) return;

    activeJobIdRef.current = activeJob.id;

    const interval = setInterval(async () => {
      try {
        const sinceId = lastEventIdRef.current;
        const url = `/api/testbed/jobs/${activeJob.id}?since_id=${sinceId}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setPollError(false);

        // Merge new events into local accumulator
        const newEvents = data.terminal_events || [];
        if (newEvents.length > 0) {
          setTerminalEvents(prev => {
            const merged = [...prev, ...newEvents];
            // Cap to 200 locally too
            return merged.slice(-200);
          });
          lastEventIdRef.current = newEvents[newEvents.length - 1].id;
        }

        // Update job state (without overwriting local events)
        setActiveJob(prev => ({ ...prev, ...data, terminal_events: undefined }));

        if (data.state === 'COMPLETED' || data.state === 'FAILED') {
          setIsRunning(false);
          fetchJobHistory();
        }
      } catch (err) {
        console.error('Failed to poll testbed status:', err);
        setPollError(true);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [activeJob?.id, activeJob?.state]);

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
      // Reset event accumulator for the new job
      setTerminalEvents([]);
      lastEventIdRef.current = 0;
      setExpandedEvents({});
      setPollError(false);
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

        {/* Right Column: VM Activity HUD & Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* VM Activity Dashboard Card */}
          <div className="glass-card" style={{ padding: '1.25rem' }}>
            {/* Header Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={16} color="#38bdf8" />
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Live Execution Dashboard
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {pollError && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#f59e0b' }}>
                    <WifiOff size={12} /> Reconnecting...
                  </span>
                )}
                {activeJob && (
                  <span className={`badge ${
                    activeJob.state === 'COMPLETED' ? 'badge-green' :
                    activeJob.state === 'FAILED' ? 'badge-red' : 'badge-cyan'
                  }`}>
                    {activeJob.state}
                  </span>
                )}
              </div>
            </div>

            {/* Substep Pipeline Strip */}
            {activeJob && (
              <SubstepPipeline events={terminalEvents} state={activeJob.state} />
            )}

            {/* VM Node Status Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', margin: '1rem 0' }}>
              {[
                { role: 'initiator', label: 'Initiator VM', icon: Send, host: topology.initiator_ip, color: '#38bdf8' },
                { role: 'responder', label: 'Responder VM', icon: Server, host: topology.responder_ip, color: '#a78bfa' },
                { role: 'observer', label: 'Observer', icon: Eye, host: topology.observer_ip, color: '#34d399' },
              ].map(({ role, label, icon: Icon, host, color }) => {
                const roleEvents = terminalEvents.filter(e => e.vm === role);
                const lastEvent = roleEvents[roleEvents.length - 1];
                const vmState = lastEvent?.status || (activeJob ? 'pending' : 'idle');
                return (
                  <VMNodeCard
                    key={role}
                    label={label}
                    icon={Icon}
                    host={host}
                    color={color}
                    vmState={vmState}
                    lastEvent={lastEvent}
                    hasActivity={roleEvents.length > 0}
                  />
                );
              })}
            </div>

            {/* Command Activity Feed */}
            <div
              ref={feedRef}
              onScroll={handleFeedScroll}
              style={{
                maxHeight: '280px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                scrollbarWidth: 'thin',
              }}
            >
              {terminalEvents.length === 0 && (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '2rem',
                  color: '#334155',
                  gap: '8px'
                }}>
                  <Terminal size={32} style={{ opacity: 0.3 }} />
                  <span style={{ fontSize: '0.82rem', fontStyle: 'italic' }}>
                    {activeJob ? 'Waiting for pipeline to start...' : 'Select a scenario and deploy to see live VM activity here.'}
                  </span>
                </div>
              )}
              {terminalEvents.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  expanded={!!expandedEvents[event.id]}
                  onToggle={() => setExpandedEvents(prev => ({ ...prev, [event.id]: !prev[event.id] }))}
                />
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
                    const analysisResult = activeJob.analysis_result || activeJob.result_json;
                    if (onNavigateToAnalysis && analysisResult) onNavigateToAnalysis(analysisResult);
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

/* ═══════════════════════════════════════════════════════════════
   Sub-components
═══════════════════════════════════════════════════════════════ */

const VM_ROLE_COLORS = {
  initiator: '#38bdf8',
  responder: '#a78bfa',
  observer: '#34d399',
  system: '#94a3b8',
};

const VM_ROLE_LABELS = {
  initiator: 'Initiator',
  responder: 'Responder',
  observer: 'Observer',
  system: 'Orchestrator',
};

/** Animated status dot */
function StatusDot({ status }) {
  const color =
    status === 'success' ? '#34d399' :
    status === 'error' ? '#f87171' :
    status === 'running' ? '#38bdf8' :
    status === 'connecting' ? '#f59e0b' :
    '#475569';

  return (
    <span style={{
      display: 'inline-block',
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: color,
      flexShrink: 0,
      boxShadow: (status === 'running' || status === 'connecting')
        ? `0 0 6px ${color}` : 'none',
      animation: (status === 'running' || status === 'connecting')
        ? 'pulse-glow 1.4s ease-in-out infinite' : 'none',
    }} />
  );
}

/** VM node status card — lights up when a VM becomes active */
function VMNodeCard({ label, icon: Icon, host, color, vmState, lastEvent, hasActivity }) {
  const isDim = !hasActivity;

  const stateLabel =
    vmState === 'running' ? 'ACTIVE' :
    vmState === 'success' ? 'DONE' :
    vmState === 'error' ? 'ERROR' :
    vmState === 'connecting' ? 'CONNECTING' :
    vmState === 'pending' ? 'WAITING' : 'IDLE';

  const stateBadgeColor =
    vmState === 'success' ? { bg: 'rgba(52, 211, 153, 0.12)', border: '#34d399', text: '#34d399' } :
    vmState === 'error'   ? { bg: 'rgba(248, 113, 113, 0.12)', border: '#f87171', text: '#f87171' } :
    vmState === 'running' || vmState === 'connecting'
                          ? { bg: `rgba(56,189,248,0.10)`, border: '#38bdf8', text: '#38bdf8' } :
    { bg: 'rgba(15,23,42,0.4)', border: 'rgba(255,255,255,0.06)', text: '#475569' };

  return (
    <div style={{
      padding: '0.85rem',
      borderRadius: '10px',
      background: hasActivity ? `${stateBadgeColor.bg}` : 'rgba(10,15,28,0.5)',
      border: `1px solid ${hasActivity ? stateBadgeColor.border : 'rgba(255,255,255,0.06)'}`,
      opacity: isDim ? 0.5 : 1,
      transition: 'all 0.4s ease',
    }}>
      {/* Icon + Label Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
        <Icon size={14} color={hasActivity ? color : '#475569'} />
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: hasActivity ? color : '#475569', letterSpacing: '0.04em' }}>
          {label.toUpperCase()}
        </span>
      </div>

      {/* Host */}
      <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: '8px', fontFamily: 'monospace' }}>
        {host}
      </div>

      {/* Status Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
        <StatusDot status={vmState} />
        <span style={{ fontSize: '0.68rem', fontWeight: 700, color: stateBadgeColor.text }}>
          {stateLabel}
        </span>
      </div>

      {/* Last activity snippet */}
      {lastEvent?.output && (
        <div style={{
          marginTop: '6px',
          fontSize: '0.65rem',
          color: '#64748b',
          fontFamily: 'monospace',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {lastEvent.output}
        </div>
      )}
    </div>
  );
}

/** Collapsible activity card for a single event */
function EventCard({ event, expanded, onToggle }) {
  const vmColor = VM_ROLE_COLORS[event.vm] || '#94a3b8';
  const vmLabel = VM_ROLE_LABELS[event.vm] || event.vm;
  const hasOutput = event.output && event.output.trim().length > 0;

  const typeIcon =
    event.type === 'complete' ? '✓' :
    event.type === 'error'    ? '✗' :
    event.type === 'connection' ? '⟳' :
    event.type === 'status'   ? '●' :
    event.type === 'command'  ? '$' : '·';

  const cardBg =
    event.status === 'error'   ? 'rgba(248,113,113,0.07)' :
    event.status === 'success' ? 'rgba(52,211,153,0.06)' :
    'rgba(15,23,42,0.35)';

  const borderColor =
    event.status === 'error'   ? 'rgba(248,113,113,0.3)' :
    event.status === 'success' ? 'rgba(52,211,153,0.2)' :
    event.status === 'running' ? 'rgba(56,189,248,0.15)' :
    'rgba(255,255,255,0.05)';

  return (
    <div style={{
      background: cardBg,
      border: `1px solid ${borderColor}`,
      borderRadius: '7px',
      padding: '0.6rem 0.75rem',
      transition: 'background 0.2s ease',
      animation: 'slide-in-up 0.2s ease',
    }}>
      {/* Main row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
        {/* Status dot */}
        <StatusDot status={event.status} />

        {/* VM badge */}
        <span style={{
          fontSize: '0.6rem',
          fontWeight: 700,
          color: vmColor,
          background: `${vmColor}18`,
          border: `1px solid ${vmColor}40`,
          borderRadius: '4px',
          padding: '1px 5px',
          letterSpacing: '0.04em',
          flexShrink: 0,
        }}>
          {vmLabel.toUpperCase()}
        </span>

        {/* Type chip */}
        <span style={{
          fontSize: '0.6rem',
          color: '#64748b',
          fontFamily: 'monospace',
          flexShrink: 0,
        }}>
          {typeIcon}
        </span>

        {/* Primary text */}
        <span style={{
          fontSize: '0.75rem',
          color: event.status === 'error' ? '#fca5a5' : event.status === 'success' ? '#6ee7b7' : '#cbd5e1',
          fontFamily: event.type === 'command' || event.type === 'output' ? 'monospace' : 'inherit',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          flex: 1,
          minWidth: 0,
        }}>
          {event.command || event.output || '—'}
        </span>

        {/* Timestamp */}
        <span style={{ fontSize: '0.62rem', color: '#475569', flexShrink: 0 }}>
          {event.timestamp}
        </span>

        {/* Expand toggle if there's extra output */}
        {hasOutput && event.type !== 'output' && (
          <button
            type="button"
            onClick={onToggle}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#64748b', padding: '0 2px', flexShrink: 0,
            }}
          >
            {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>
        )}
      </div>

      {/* Expanded output */}
      {expanded && hasOutput && event.type !== 'output' && (
        <div style={{
          marginTop: '6px',
          padding: '6px 8px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '5px',
          fontFamily: 'monospace',
          fontSize: '0.7rem',
          color: '#94a3b8',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}>
          {event.output}
        </div>
      )}
    </div>
  );
}

/** Detailed 8-step substep pipeline strip */
const PHASES = [
  { id: 'CONFIG_GENERATION',       label: 'Config',     short: '1' },
  { id: 'RESPONDER_PROVISIONING',  label: 'Responder',  short: '2' },
  { id: 'INITIATOR_PROVISIONING',  label: 'Initiator',  short: '3' },
  { id: 'OBSERVER_CAPTURE_START',  label: 'Capture',    short: '4' },
  { id: 'TUNNEL_NEGOTIATION',      label: 'Tunnel',     short: '5' },
  { id: 'TRAFFIC_INJECTION',       label: 'Traffic',    short: '6' },
  { id: 'CAPTURE_RETRIEVAL',       label: 'PCAP',       short: '7' },
  { id: 'AI_ANALYSIS',             label: 'AI',         short: '8' },
];

function SubstepPipeline({ events, state }) {
  // Determine which phases have appeared in the event stream
  const seenPhases = new Set(events.map(e => e.phase).filter(Boolean));
  const activePhase = [...seenPhases].pop(); // last seen phase

  // All phases up-to-but-not-including active are "done"
  const activeIdx = PHASES.findIndex(p => p.id === activePhase);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '2px',
      padding: '8px 0 6px',
      overflowX: 'auto',
      scrollbarWidth: 'none',
    }}>
      {PHASES.map((phase, idx) => {
        const isDone = (activeIdx > idx) || state === 'COMPLETED';
        const isActive = idx === activeIdx && state !== 'COMPLETED' && state !== 'FAILED';
        const isFailed = state === 'FAILED' && idx === activeIdx;

        const bg =
          isFailed ? 'rgba(248,113,113,0.2)' :
          isDone    ? 'rgba(52,211,153,0.15)' :
          isActive  ? 'rgba(56,189,248,0.15)' :
          'rgba(15,23,42,0.5)';

        const border =
          isFailed ? '#f87171' :
          isDone    ? '#34d399' :
          isActive  ? '#38bdf8' :
          'rgba(255,255,255,0.06)';

        const textColor =
          isFailed ? '#f87171' :
          isDone    ? '#34d399' :
          isActive  ? '#38bdf8' :
          '#475569';

        return (
          <React.Fragment key={phase.id}>
            <div style={{
              minWidth: 52,
              padding: '4px 6px',
              borderRadius: '5px',
              background: bg,
              border: `1px solid ${border}`,
              textAlign: 'center',
              transition: 'all 0.3s ease',
              animation: isActive ? 'pulse-glow 1.4s ease-in-out infinite' : 'none',
            }}>
              <div style={{ fontSize: '0.58rem', fontWeight: 800, color: textColor }}>
                {isDone ? '✓' : isFailed ? '✗' : phase.short}
              </div>
              <div style={{ fontSize: '0.6rem', color: textColor, fontWeight: 600 }}>
                {phase.label}
              </div>
            </div>
            {idx < PHASES.length - 1 && (
              <div style={{
                width: 12,
                height: 1,
                background: isDone ? '#34d399' : 'rgba(255,255,255,0.08)',
                flexShrink: 0,
                transition: 'background 0.3s ease',
              }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
