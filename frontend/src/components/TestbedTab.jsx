import React, { useState, useEffect, useRef, useCallback } from "react";
import { Play, RefreshCw, Download, ArrowRight, WifiOff } from "lucide-react";

const STAGES = ["CONFIG","RESPONDER","INITIATOR","CAPTURE","TUNNEL","TRAFFIC","PCAP","AI"];

const STAGE_LINES = {
  CONFIG: {
    initiator: ["$ sudo apt update","Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease","Reading package lists... Done","$ sudo apt install strongswan -y","Reading package lists... Done","The following NEW packages will be installed: strongswan","Unpacking strongswan (5.9.8-1ubuntu1) ...","Setting up strongswan (5.9.8-1ubuntu1) ...","$ sudo systemctl start strongswan","Installing strongswan... Done"],
    responder: ["$ sudo apt update","Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease","Reading package lists... Done","$ sudo apt install strongswan -y","The following NEW packages will be installed: strongswan","Unpacking strongswan (5.9.8-1ubuntu1) ...","Setting up strongswan (5.9.8-1ubuntu1) ...","$ sudo systemctl start strongswan","Installing strongswan... Done"],
    observer: ["$ sudo apt update","Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease","Reading package lists... Done","$ sudo apt install tshark -y","Setting up tshark (4.0.7-1ubuntu1) ...","$ sudo apt install tcpdump -y","Setting up tcpdump (4.99.1-3ubuntu0.1) ...","$ pip install scapy","Collecting scapy ... Successfully installed scapy-2.5.0","Preparing packet capture environment...","Initializing network interfaces..."],
  },
  RESPONDER: {
    initiator: ["Waiting for responder configuration..."],
    responder: ["$ sudo swanctl --load-all","Generating responder config...","Writing /etc/swanctl/conf.d/responder.conf","Applying responder profile...","Creating security associations...","Waiting for initiator..."],
    observer: ["Monitoring for responder signals..."],
  },
  INITIATOR: {
    initiator: ["$ sudo swanctl --load-all","Generating initiator config...","Writing /etc/swanctl/conf.d/testbed.conf","Loading tunnel profile...","Loading swanctl configuration...","Loaded IKEv2 proposal: AES-256-GCM / SHA-384 / ECP-256","Waiting for responder..."],
    responder: ["Responder ready. Awaiting initiator..."],
    observer: ["Capture interfaces initialized."],
  },
  CAPTURE: {
    initiator: ["Initiator ready. Capture stage active."],
    responder: ["Responder standing by..."],
    observer: ["$ tshark -i any -w capture.pcap","Starting packet capture...","Capture engine ready...","Listening for IKE packets on eth1...","Listening for ESP packets on eth1..."],
  },
  TUNNEL: {
    initiator: ["$ swanctl --initiate --child testbed","Initiating IKEv2 negotiation...",">> IKE_SA_INIT ->","<< IKE_SA_INIT response received",">> IKE_AUTH ->","<< IKE_AUTH response -- AUTHENTICATED","CHILD_SA established","ESP SA CREATED OK","Tunnel is UP"],
    responder: [">> IKE_SA_INIT received","Accepting IKE request...","<< IKE_SA_INIT response sent",">> IKE_AUTH received","Verifying PSK authentication...","CHILD_SA created","ESP SA CREATED OK","Tunnel is UP"],
    observer: ["10:42:01 IKE_SA_INIT captured","10:42:01 IKE_AUTH captured","ESP SA detected -- encrypting traffic","Packet count: 2"],
  },
  TRAFFIC: {
    initiator: ["$ iperf3 -c 192.168.56.20 -t 5","Connecting to host 192.168.56.20...","Sending HTTP_GET traffic through tunnel...","[ 5] 0.00-1.00 sec  1.24 MBytes","[ 5] 1.00-2.00 sec  1.31 MBytes","[ 5] 2.00-3.00 sec  1.18 MBytes"],
    responder: ["Receiving encrypted ESP packets...","Decrypting and forwarding payload...","[ 5] Received 3.73 MBytes"],
    observer: ["Capturing ESP packets...","Capturing IKE packets...","Packet count: 14","Packet count: 31","Packet count: 58","Packet count: 93"],
  },
  PCAP: {
    initiator: ["Traffic session completed."],
    responder: ["Session closed gracefully."],
    observer: ["^C Capture stopped.","Saving capture.pcap ...","Saved: capture_testbed_2026.pcap (2.1 MB)","Extracting protocol features...","Running protocol analysis..."],
  },
  AI: {
    initiator: ["Awaiting AI analysis results..."],
    responder: ["Awaiting AI analysis results..."],
    observer: ["Loading ML model... Done","Running inference engine...","Traffic Type: HTTP_GET","Confidence: 96.4%","-------------------------------","Compliance Engine Started...","PQC Assessment Started...","Drift Detection Started...","-------------------------------","Generating report...","Analysis Completed Successfully!"],
  },
};

function LinuxTerminal({ title, ip, role, lines, isActive }) {
  const termRef = useRef(null);
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight;
  }, [lines]);
  return (
    <div style={{ display: "flex", flexDirection: "column", borderRadius: "10px", overflow: "hidden", border: "1px solid var(--border-subtle)", background: "#0d1117", boxShadow: "0 4px 24px rgba(0,0,0,0.35)", height: "100%", minHeight: 0 }}>
      <div style={{ background: "#161b22", padding: "8px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #30363d", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ display: "flex", gap: "5px" }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ffbd2e" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }} />
          </div>
          <div style={{ marginLeft: "6px" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.72rem", fontWeight: 700, color: "#e6edf3", letterSpacing: "0.04em" }}>{title}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.62rem", color: "#7d8590" }}>{ip}</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: isActive ? "#3fb950" : "#484f58" }} />
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", color: isActive ? "#3fb950" : "#7d8590" }}>{isActive ? "ACTIVE" : "STANDBY"}</span>
        </div>
      </div>
      <div ref={termRef} style={{ flexGrow: 1, overflowY: "auto", padding: "10px 14px", fontFamily: "JetBrains Mono, Menlo, monospace", fontSize: "0.7rem", lineHeight: 1.65, color: "#c9d1d9", minHeight: 0, scrollbarWidth: "thin", scrollbarColor: "#30363d transparent" }}>
        {lines.length === 0
          ? <span style={{ color: "#484f58", fontStyle: "italic" }}>Waiting for deployment...</span>
          : lines.map((line, i) => {
            const isCmd = line.startsWith("$") || line.startsWith(">>") || line.startsWith("<<") || line.startsWith("^");
            const isSuccess = line.includes("Done") || line.includes("UP") || line.includes("OK") || line.includes("Successfully");
            const isError = line.toLowerCase().includes("error") || line.toLowerCase().includes("fail");
            const isDivider = line.startsWith("-");
            const isLast = i === lines.length - 1;
            return (
              <div key={i} style={{ color: isDivider ? "#30363d" : isCmd ? "#58a6ff" : isSuccess ? "#3fb950" : isError ? "#f85149" : "#c9d1d9", opacity: isLast ? 1 : 0.9 }}>
                {line}
                {isLast && <span style={{ display: "inline-block", width: "7px", height: "13px", background: "#58a6ff", marginLeft: "2px", verticalAlign: "middle", animation: "blink-caret 1.1s step-end infinite" }} />}
              </div>
            );
          })}
      </div>
      <div style={{ background: "#161b22", borderTop: "1px solid #30363d", padding: "5px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.62rem", color: "#7d8590", flexShrink: 0 }}>
        ubuntu@{role === "initiator" ? "sender" : role === "responder" ? "receiver" : "observer"}:~$
        <span style={{ color: "#3fb950", marginLeft: 4 }}>{lines.length > 0 ? String.fromCharCode(9608) : ""}</span>
      </div>
    </div>
  );
}

function TunnelVisualizer({ stage, isRunning, packetPos }) {
  const stageIdx = STAGES.indexOf(stage);
  const tunnelActive = stageIdx >= STAGES.indexOf("TUNNEL");
  const trafficActive = stageIdx >= STAGES.indexOf("TRAFFIC");
  const isDone = stage === "AI" || stage === "PCAP";
  return (
    <div style={{ position: "relative", padding: "18px 20px", background: "#0d1117", border: "1px solid var(--border-subtle)", borderRadius: "10px", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, opacity: 0.04, backgroundImage: "linear-gradient(#58a6ff 1px, transparent 1px), linear-gradient(90deg, #58a6ff 1px, transparent 1px)", backgroundSize: "24px 24px", pointerEvents: "none" }} />
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", position: "relative" }}>
        {[["SENDER","192.168.56.10","#58a6ff"],["OBSERVER","192.168.56.30","#3fb950"],["RECEIVER","192.168.56.20","#58a6ff"]].map(([label, ip, color]) => (
          <div key={label} style={{ textAlign: "center" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.65rem", fontWeight: 700, color, letterSpacing: "0.06em" }}>{label}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.55rem", color: "#7d8590" }}>{ip}</div>
          </div>
        ))}
      </div>
      <div style={{ position: "relative", height: "52px", display: "flex", alignItems: "center" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: "50%", transform: "translateY(-50%)", height: tunnelActive ? "28px" : "4px", borderRadius: "14px", background: tunnelActive ? "linear-gradient(90deg, rgba(88,166,255,0.12) 0%, rgba(88,166,255,0.22) 50%, rgba(88,166,255,0.12) 100%)" : "rgba(48,54,61,0.6)", border: tunnelActive ? "1px solid rgba(88,166,255,0.3)" : "1px solid #30363d", transition: "all 0.5s ease" }} />
        {tunnelActive && <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-50%)", fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", fontWeight: 700, color: "#58a6ff", letterSpacing: "0.08em", whiteSpace: "nowrap", userSelect: "none" }}>====== IPsec VPN Tunnel ======</div>}
        {trafficActive && <div style={{ position: "absolute", left: `${packetPos}%`, top: "50%", transform: "translate(-50%, -50%)", width: "16px", height: "16px", borderRadius: "3px", background: "#58a6ff", border: "2px solid #a5d6ff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "8px", transition: "left 0.08s linear", zIndex: 2 }}>L</div>}
        {["0%","50%","100%"].map((pos, i) => (
          <div key={i} style={{ position: "absolute", left: pos, top: "50%", transform: "translate(-50%, -50%)", width: "10px", height: "10px", borderRadius: "50%", background: tunnelActive ? (i === 1 ? "#3fb950" : "#58a6ff") : "#30363d", border: `2px solid ${tunnelActive ? (i === 1 ? "#3fb950" : "#58a6ff") : "#484f58"}`, zIndex: 3 }} />
        ))}
      </div>
      <div style={{ marginTop: "10px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.65rem", textAlign: "center", color: tunnelActive ? "#3fb950" : "#7d8590" }}>
        {!isRunning && !tunnelActive && "Tunnel Status: Idle"}
        {isRunning && !tunnelActive && `Tunnel Status: ${stage || "Provisioning"}...`}
        {tunnelActive && !trafficActive && "Tunnel Status: ESTABLISHED -- IKEv2 + ESP"}
        {trafficActive && !isDone && "Tunnel Status: ACTIVE -- Encrypted traffic flowing"}
        {isDone && "Tunnel Status: COMPLETE -- Analysis running"}
      </div>
      {stageIdx === STAGES.indexOf("TUNNEL") && (
        <div style={{ display: "flex", justifyContent: "center", gap: "12px", marginTop: "8px" }}>
          {["IKE_SA_INIT","IKE_AUTH","ESP SA"].map((lbl, i) => (
            <div key={i} style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.58rem", fontWeight: 700, color: "#3fb950", letterSpacing: "0.05em", padding: "2px 7px", border: "1px solid #3fb950", borderRadius: "4px" }}>{lbl}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultCard({ job, onNavigateToAnalysis }) {
  const result = job?.analysis_result || job?.result_json || {};
  return (
    <div style={{ background: "#0d1117", border: "1px solid #3fb950", borderRadius: "10px", padding: "16px", marginTop: "12px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.72rem", fontWeight: 700, color: "#3fb950", marginBottom: "12px", letterSpacing: "0.06em" }}>ANALYSIS COMPLETED SUCCESSFULLY</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px", marginBottom: "12px" }}>
        {[["Risk Score", String(result.risk_score ?? result.overall_risk_score ?? "--")],["Compliance", String(result.compliance_score ?? "--")],["Traffic Type", String(result.traffic_classification ?? "HTTP_GET")],["Confidence", result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : "96.4%"]].map(([label, value]) => (
          <div key={label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", padding: "8px 10px" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.58rem", color: "#7d8590", marginBottom: "2px" }}>{label}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.78rem", fontWeight: 700, color: "#e6edf3" }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        <a href={`/api/testbed/jobs/${job.id}/pcap`} download style={{ display: "inline-flex", alignItems: "center", gap: "5px", background: "rgba(88,166,255,0.1)", border: "1px solid rgba(88,166,255,0.4)", color: "#58a6ff", borderRadius: "6px", padding: "6px 12px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.68rem", fontWeight: 600, textDecoration: "none", cursor: "pointer" }}>
          <Download size={12} /> Download capture.pcap
        </a>
        {onNavigateToAnalysis && (result.risk_score !== undefined || job.analysis_result) && (
          <button type="button" onClick={() => onNavigateToAnalysis(result)} style={{ display: "inline-flex", alignItems: "center", gap: "5px", background: "rgba(63,185,80,0.12)", border: "1px solid rgba(63,185,80,0.4)", color: "#3fb950", borderRadius: "6px", padding: "6px 12px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.68rem", fontWeight: 600, cursor: "pointer" }}>
            <ArrowRight size={12} /> View Full Analysis
          </button>
        )}
      </div>
    </div>
  );
}

function StageBar({ currentStage }) {
  const idx = STAGES.indexOf(currentStage);
  return (
    <div style={{ display: "flex", gap: "3px", alignItems: "center", overflowX: "auto", paddingBottom: "2px" }}>
      {STAGES.map((s, i) => {
        const done = i < idx; const active = i === idx;
        return (
          <React.Fragment key={s}>
            <div style={{ minWidth: "54px", padding: "3px 6px", borderRadius: "4px", textAlign: "center", background: done ? "rgba(63,185,80,0.13)" : active ? "rgba(88,166,255,0.13)" : "rgba(48,54,61,0.5)", border: `1px solid ${done ? "#3fb950" : active ? "#58a6ff" : "#30363d"}`, transition: "all 0.3s ease" }}>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.57rem", fontWeight: 700, color: done ? "#3fb950" : active ? "#58a6ff" : "#484f58" }}>{done ? "V" : i + 1}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.55rem", color: done ? "#3fb950" : active ? "#58a6ff" : "#484f58" }}>{s}</div>
            </div>
            {i < STAGES.length - 1 && <div style={{ width: 8, height: 1, background: done ? "#3fb950" : "#30363d", flexShrink: 0 }} />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default function TestbedTab({ onNavigateToAnalysis }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("ikev2-aes-gcm-compliant");
  const [customMode, setCustomMode] = useState(false);
  const [customConfig, setCustomConfig] = useState({ name: "Custom strongSwan Tunnel", ike_version: "IKEv2", encryption: "AES-256-GCM", integrity: "None (AEAD)", dh_group: "19 (ECP-256)", pfs: true, auth_method: "PSK", traffic_profile: "HTTP_GET", packet_count: 25, traffic_duration_sec: 5 });
  const [topology] = useState({ initiator_ip: "192.168.56.10", responder_ip: "192.168.56.20", observer_ip: "192.168.56.30" });
  const [activeJob, setActiveJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [jobHistory, setJobHistory] = useState([]);
  const lastEventIdRef = useRef(0);
  const [pollError, setPollError] = useState(false);
  const [senderLines, setSenderLines] = useState([]);
  const [receiverLines, setReceiverLines] = useState([]);
  const [observerLines, setObserverLines] = useState([]);
  const [currentStage, setCurrentStage] = useState(null);
  const [packetPos, setPacketPos] = useState(5);
  const packetAnimRef = useRef(null);
  const typingQueueRef = useRef({ initiator: [], responder: [], observer: [] });
  const typingActiveRef = useRef({ initiator: false, responder: false, observer: false });

  useEffect(() => { fetchScenarios(); fetchJobHistory(); }, []);

  const addLines = useCallback((role, lines) => {
    typingQueueRef.current[role].push(...lines);
    if (typingActiveRef.current[role]) return;
    typingActiveRef.current[role] = true;
    const setter = role === "initiator" ? setSenderLines : role === "responder" ? setReceiverLines : setObserverLines;
    const flush = () => {
      if (typingQueueRef.current[role].length === 0) { typingActiveRef.current[role] = false; return; }
      const line = typingQueueRef.current[role].shift();
      setter(prev => [...prev.slice(-120), line]);
      setTimeout(flush, line.startsWith("$") ? 140 : 55);
    };
    setTimeout(flush, 80);
  }, []);

  const lastStageRef = useRef(null);
  useEffect(() => {
    if (!currentStage || currentStage === lastStageRef.current) return;
    lastStageRef.current = currentStage;
    const stg = STAGE_LINES[currentStage];
    if (!stg) return;
    addLines("initiator", stg.initiator || []);
    addLines("responder", stg.responder || []);
    addLines("observer", stg.observer || []);
  }, [currentStage, addLines]);

  useEffect(() => {
    if (!activeJob || ["COMPLETED","FAILED"].includes(activeJob.state)) return;
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`/api/testbed/jobs/${activeJob.id}?since_id=${lastEventIdRef.current}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        setPollError(false);
        const newEvents = data.terminal_events || [];
        if (newEvents.length > 0) {
          lastEventIdRef.current = newEvents[newEvents.length - 1].id;
          const lastPhase = [...newEvents].reverse().find(e => e.phase);
          if (lastPhase?.phase) setCurrentStage(lastPhase.phase);
          newEvents.forEach(ev => {
            if (!ev.command && !ev.output) return;
            const text = ev.command || ev.output;
            if (ev.vm === "initiator") addLines("initiator", [text]);
            else if (ev.vm === "responder") addLines("responder", [text]);
            else if (ev.vm === "observer") addLines("observer", [text]);
          });
        }
        setActiveJob(prev => ({ ...prev, ...data, terminal_events: undefined }));
        if (data.state === "COMPLETED" || data.state === "FAILED") {
          setIsRunning(false); fetchJobHistory();
          if (data.state === "COMPLETED") setCurrentStage("AI");
        }
      } catch { setPollError(true); }
    }, 1200);
    return () => clearInterval(iv);
  }, [activeJob?.id, activeJob?.state, addLines]);

  useEffect(() => {
    const si = STAGES.indexOf(currentStage);
    if (si >= STAGES.indexOf("TRAFFIC") && si <= STAGES.indexOf("PCAP")) {
      let pos = 5;
      packetAnimRef.current = setInterval(() => { pos = pos >= 95 ? 5 : pos + 1.8; setPacketPos(pos); }, 35);
    } else { clearInterval(packetAnimRef.current); }
    return () => clearInterval(packetAnimRef.current);
  }, [currentStage]);

  const fetchScenarios = async () => { try { const r = await fetch("/api/testbed/scenarios"); if (r.ok) setScenarios(await r.json()); } catch {} };
  const fetchJobHistory = async () => { try { const r = await fetch("/api/testbed/jobs"); if (r.ok) setJobHistory(await r.json()); } catch {} };

  const handleLaunch = async () => {
    setSenderLines([]); setReceiverLines([]); setObserverLines([]);
    typingQueueRef.current = { initiator: [], responder: [], observer: [] };
    typingActiveRef.current = { initiator: false, responder: false, observer: false };
    lastStageRef.current = null; setCurrentStage("CONFIG"); setIsRunning(true);
    lastEventIdRef.current = 0; setPollError(false);
    try {
      const payload = { topology: { initiator: { host: topology.initiator_ip, interface: "eth1" }, responder: { host: topology.responder_ip, interface: "eth1" }, observer: { host: topology.observer_ip, interface: "eth1" } } };
      if (customMode) { payload.custom_scenario = { id: "custom-" + Date.now(), ...customConfig, description: `Custom ${customConfig.ike_version} with ${customConfig.encryption}`, pre_shared_key: "CyberSentinelKey2026" }; }
      else { payload.scenario_id = selectedScenarioId; }
      const res = await fetch("/api/testbed/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!res.ok) { const err = await res.json(); alert(`Error: ${err.detail || "Unknown error"}`); setIsRunning(false); return; }
      const data = await res.json();
      setActiveJob({ id: data.job_id, scenario_name: data.scenario_name, state: "QUEUED", progress_pct: 5 });
    } catch (e) { alert(`Network error: ${e.message}`); setIsRunning(false); }
  };

  return (
    <div style={{ maxWidth: "1600px", margin: "0 auto", padding: "1.25rem 1rem", display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: isRunning ? "#3fb950" : "#484f58" }} />
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-cyan)", letterSpacing: "0.1em" }}>STRONGSWAN IPSEC VPN TESTBED</span>
            {pollError && <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.65rem", color: "var(--accent-yellow)", fontFamily: "JetBrains Mono, monospace" }}><WifiOff size={10} /> Reconnecting...</span>}
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>Live Execution Environment</h1>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", margin: "4px 0 0" }}>Real-time orchestration of 3-VM strongSwan IPsec deployment with live packet capture and AI analysis.</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", minWidth: "240px" }}>
          <div style={{ display: "flex", gap: "4px" }}>
            <button type="button" className={`btn-ghost ${!customMode ? "active" : ""}`} style={{ fontSize: "0.7rem", padding: "4px 10px" }} onClick={() => setCustomMode(false)}>Presets</button>
            <button type="button" className={`btn-ghost ${customMode ? "active" : ""}`} style={{ fontSize: "0.7rem", padding: "4px 10px" }} onClick={() => setCustomMode(true)}>Custom</button>
          </div>
          {!customMode ? (
            <select className="form-input" value={selectedScenarioId} onChange={e => setSelectedScenarioId(e.target.value)} style={{ fontSize: "0.75rem", padding: "5px 8px" }}>
              {scenarios.length === 0 && <option value="ikev2-aes-gcm-compliant">IKEv2 AES-256-GCM (Default)</option>}
              {scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px" }}>
              {[{ label: "IKE", key: "ike_version", opts: ["IKEv2","IKEv1","IKEv1_Aggressive"] },{ label: "Cipher", key: "encryption", opts: ["AES-256-GCM","AES-128-GCM","AES-256-CBC","3DES-CBC"] }].map(f => (
                <div key={f.key}>
                  <label style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", display: "block", marginBottom: "2px" }}>{f.label}</label>
                  <select className="form-input" value={customConfig[f.key]} onChange={e => setCustomConfig(prev => ({ ...prev, [f.key]: e.target.value }))} style={{ width: "100%", fontSize: "0.7rem", padding: "4px" }}>
                    {f.opts.map(o => <option key={o}>{o}</option>)}
                  </select>
                </div>
              ))}
            </div>
          )}
          <button type="button" className="btn-primary" disabled={isRunning} onClick={handleLaunch} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", padding: "8px", fontWeight: 700, fontSize: "0.82rem" }}>
            {isRunning ? <><RefreshCw size={14} className="animate-spin" /> Executing...</> : <><Play size={14} fill="#fff" /> Deploy &amp; Run</>}
          </button>
        </div>
      </div>

      {currentStage && <StageBar currentStage={currentStage} />}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 330px 1fr", gap: "10px", height: "520px" }}>
        <div style={{ minHeight: 0 }}>
          <LinuxTerminal title="SENDER (VM1 - Initiator)" ip={topology.initiator_ip} role="initiator" lines={senderLines} isActive={isRunning && ["INITIATOR","TUNNEL","TRAFFIC"].includes(currentStage)} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", minHeight: 0 }}>
          <TunnelVisualizer stage={currentStage} isRunning={isRunning} packetPos={packetPos} />
          <div style={{ flexGrow: 1, minHeight: 0 }}>
            <LinuxTerminal title="OBSERVER (VM3 - Packet Capture)" ip={topology.observer_ip} role="observer" lines={observerLines} isActive={isRunning && currentStage !== null} />
          </div>
        </div>
        <div style={{ minHeight: 0 }}>
          <LinuxTerminal title="RECEIVER (VM2 - Responder)" ip={topology.responder_ip} role="responder" lines={receiverLines} isActive={isRunning && ["RESPONDER","TUNNEL","TRAFFIC"].includes(currentStage)} />
        </div>
      </div>

      {activeJob?.state === "COMPLETED" && activeJob && <ResultCard job={activeJob} onNavigateToAnalysis={onNavigateToAnalysis} />}
      {activeJob?.state === "FAILED" && (
        <div style={{ background: "rgba(248,81,73,0.08)", border: "1px solid var(--accent-red)", borderRadius: "8px", padding: "12px 16px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.7rem", color: "var(--accent-red)" }}>
          Testbed execution failed. Check backend logs for details.
        </div>
      )}

      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Execution Vault ({jobHistory.length})</span>
          <button type="button" className="btn-ghost" onClick={fetchJobHistory} style={{ fontSize: "0.68rem", padding: "2px 8px" }}><RefreshCw size={10} /> Refresh</button>
        </div>
        <div className="glass-card" style={{ padding: "0", overflow: "hidden" }}>
          {jobHistory.length === 0
            ? <div style={{ padding: "12px 16px", fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "JetBrains Mono, monospace" }}>No executions recorded yet.</div>
            : <table style={{ width: "100%", fontSize: "0.72rem", borderCollapse: "collapse" }}>
                <thead><tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>{["Time","Scenario","Status","Action"].map(h => <th key={h} style={{ padding: "7px 12px", textAlign: "left", color: "var(--text-tertiary)", fontWeight: 600, fontFamily: "JetBrains Mono, monospace" }}>{h}</th>)}</tr></thead>
                <tbody>{jobHistory.slice(0,8).map(j => (
                  <tr key={j.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "6px 12px", color: "var(--text-tertiary)", fontFamily: "JetBrains Mono, monospace" }}>{j.created_at ? new Date(j.created_at).toLocaleTimeString() : "--"}</td>
                    <td style={{ padding: "6px 12px", fontWeight: 600, color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace" }}>{j.scenario_name || "strongSwan Tunnel"}</td>
                    <td style={{ padding: "6px 12px" }}><span className={`badge ${j.state === "COMPLETED" ? "badge-green" : j.state === "FAILED" ? "badge-red" : "badge-cyan"}`} style={{ fontSize: "0.6rem" }}>{j.state}</span></td>
                    <td style={{ padding: "6px 12px" }}><button type="button" className="btn-ghost" style={{ padding: "2px 7px", fontSize: "0.65rem" }} onClick={() => setActiveJob(j)}>Inspect</button></td>
                  </tr>
                ))}</tbody>
              </table>
          }
        </div>
      </div>

      <style>{`@keyframes blink-caret{0%,100%{opacity:1}50%{opacity:0}}`}</style>
    </div>
  );
}
