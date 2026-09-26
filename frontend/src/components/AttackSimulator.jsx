import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, CircleStop, Play, RefreshCw, ShieldAlert, Terminal } from 'lucide-react';

const FALLBACK_OPTIONS = [
  { id: 'mitm', name: 'Man-in-the-middle', description: 'Models an untrusted relay between the VPN gateways.', signal: 'Peer path and identity mismatch' },
  { id: 'replay', name: 'IKE / ESP replay', description: 'Models stale exchange and packet sequence observations.', signal: 'Duplicate sequence and nonce detection' },
  { id: 'weak_proposal', name: 'Weak proposal downgrade', description: 'Models a negotiation offering deprecated crypto suites.', signal: 'Policy rejected legacy proposal' },
  { id: 'tunnel_disruption', name: 'Tunnel disruption', description: 'Models scoped latency and tunnel flap telemetry.', signal: 'Child SA health degradation' },
];

const TYPE_LABELS = Object.fromEntries(FALLBACK_OPTIONS.map((option) => [option.id, option.name]));

export default function AttackSimulator({ isTestbedConnected = false, topology }) {
  const [options, setOptions] = useState(FALLBACK_OPTIONS);
  const [sessions, setSessions] = useState([]);
  const [selectedType, setSelectedType] = useState('mitm');
  const [target, setTarget] = useState('gateway-1 ↔ gateway-2');
  const [attackVm, setAttackVm] = useState({ status: 'ready', address: '192.168.56.40' });
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState('');

  const activeSession = useMemo(() => sessions.find((session) => session.status === 'running'), [sessions]);
  const refresh = useCallback(async () => {
    try {
      const response = await fetch('/api/testbed/attack-simulations');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const apiOptions = data.options?.map((option) => ({ ...option, id: String(option.id) })) || [];
      setOptions(apiOptions.length > 0 ? apiOptions : FALLBACK_OPTIONS);
      setSessions(data.sessions || []);
      setAttackVm(data.attack_vm || { status: 'ready', address: '192.168.56.40' });
      setMessage('');
    } catch (error) {
      setMessage('Simulation API unavailable. The control surface is ready when the backend is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const startSimulation = async () => {
    setRunning(true);
    setMessage('');
    try {
      const response = await fetch('/api/testbed/attack-simulations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_type: selectedType, target, topology }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail || `Unable to start simulation (HTTP ${response.status})`);
      }
      await refresh();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setRunning(false);
    }
  };

  const stopSimulation = async (sessionId) => {
    try {
      const response = await fetch(`/api/testbed/attack-simulations/${sessionId}/stop`, { method: 'POST' });
      if (!response.ok) throw new Error('Unable to stop simulation');
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section className={`glass-card attack-simulator ${!isTestbedConnected ? 'is-locked' : ''}`} aria-label="Attack simulator">
      <div className="attack-simulator-header">
        <div>
          <div className="attack-eyebrow"><ShieldAlert size={15} /> CONTROLLED SECURITY EXERCISE</div>
          <h2>Attack Simulator</h2>
          <p>{isTestbedConnected ? 'Run telemetry-only scenarios from a separate, isolated Attack VM.' : 'Connect all testbed nodes before starting an attack simulation.'}</p>
        </div>
        <div className={`attack-vm-status ${attackVm.status === 'running' ? 'is-running' : ''}`}>
          <Activity size={16} />
          <span><strong>Attack VM</strong><small>{attackVm.address} · {attackVm.status}</small></span>
        </div>
      </div>

      <div className="attack-option-grid">
        {options.map((option) => (
          <button
            type="button"
            key={option.id}
            className={`attack-option ${selectedType === option.id ? 'selected' : ''}`}
            onClick={() => setSelectedType(option.id)}
            disabled={!isTestbedConnected || Boolean(activeSession)}
          >
            <span>{option.name}</span>
            <small>{option.description}</small>
            <em>{option.signal}</em>
          </button>
        ))}
      </div>

      <div className="attack-controls">
        <label>
          Target path
          <select value={target} onChange={(event) => setTarget(event.target.value)} disabled={!isTestbedConnected || Boolean(activeSession)}>
            <option>gateway-1 ↔ gateway-2</option>
            <option>client-1 ↔ gateway-1</option>
          </select>
        </label>
        {activeSession ? (
          <button type="button" className="attack-stop-button" onClick={() => stopSimulation(activeSession.id)}>
            <CircleStop size={16} /> Stop simulation
          </button>
        ) : (
          <button type="button" className="attack-start-button" onClick={startSimulation} disabled={!isTestbedConnected || running || loading}>
            <Play size={15} /> {running ? 'Starting...' : 'Start simulation'}
          </button>
        )}
        <button type="button" className="attack-refresh-button" onClick={refresh} title="Refresh simulation state" aria-label="Refresh simulation state">
          <RefreshCw size={16} />
        </button>
      </div>

      {!isTestbedConnected && (
        <div className="attack-locked-state">
          <AlertTriangle size={15} /> Attack simulations unlock after all three testbed nodes report online.
        </div>
      )}

      {message && <div className="attack-message"><AlertTriangle size={15} /> {message}</div>}

      {activeSession && (
        <div className="attack-active-state">
          <div className="attack-active-title"><Terminal size={15} /> {TYPE_LABELS[activeSession.attack_type] || activeSession.attack_type} is running</div>
          <span>{activeSession.target} · Detection: {activeSession.detection}</span>
        </div>
      )}

      {sessions.length > 0 && (
        <div className="attack-session-list">
          <div className="attack-session-heading">Recent simulation evidence</div>
          {sessions.slice().reverse().map((session) => (
            <div className="attack-session" key={session.id}>
              <div className="attack-session-main">
                {session.status === 'running' ? <Activity size={14} /> : <CheckCircle size={14} />}
                <strong>{TYPE_LABELS[session.attack_type] || session.attack_type}</strong>
                <span>{session.status}</span>
              </div>
              <ul>{session.evidence?.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
