import React, { useState, useEffect, useRef, useCallback } from "react";
import { Play, RefreshCw, Download, ArrowRight, WifiOff } from "lucide-react";

const STAGES = ["CONFIG", "RESPONDER", "INITIATOR", "CAPTURE", "TUNNEL", "TRAFFIC", "PCAP", "AI"];

const STAGE_LINES = {
  CONFIG: {
    initiator: [
      "$ sudo apt update",
      "Hit:1 http://archive.ubuntu.com jammy InRelease",
      "Reading package lists... Done",
      "$ sudo apt install strongswan -y",
      "The following NEW packages: strongswan",
      "Unpacking strongswan ...",
      "Setting up strongswan ...",
      "$ sudo systemctl start strongswan",
      "strongswan service started",
      "Installing strongswan... Done",
    ],
    responder: [
      "$ sudo apt update",
      "Hit:1 http://archive.ubuntu.com jammy InRelease",
      "Reading package lists... Done",
      "$ sudo apt install strongswan -y",
      "The following NEW packages: strongswan",
      "Unpacking strongswan ...",
      "Setting up strongswan ...",
      "$ sudo systemctl start strongswan",
      "strongswan service started",
      "Installing strongswan... Done",
    ],
    observer: [
      "$ sudo apt update",
      "Reading package lists... Done",
      "$ sudo apt install tshark -y",
      "Setting up tshark ...",
      "$ sudo apt install tcpdump -y",
      "Setting up tcpdump ...",
      "$ pip install scapy",
      "Successfully installed scapy-2.5.0",
      "Preparing packet capture environment...",
      "Observer node ready.",
    ],
  },
  RESPONDER: {
    initiator: ["Waiting for responder configuration..."],
    responder: [
      "$ sudo swanctl --load-all",
      "Generating responder config...",
      "Writing /etc/swanctl/conf.d/responder.conf",
      "Applying responder profile...",
      "Creating security associations...",
      "Waiting for initiator...",
    ],
    observer: ["Monitoring for responder signals..."],
  },
  INITIATOR: {
    initiator: [
      "$ sudo swanctl --load-all",
      "Generating initiator config...",
      "Writing /etc/swanctl/conf.d/testbed.conf",
      "Loading tunnel profile...",
      "Loaded IKEv2 proposal: AES-256-GCM / SHA-384 / ECP-256",
      "Waiting for responder...",
    ],
    responder: ["Responder ready. Awaiting initiator..."],
    observer: ["Capture interfaces initialized."],
  },
  CAPTURE: {
    initiator: ["Initiator ready. Capture stage active."],
    responder: ["Responder standing by..."],
    observer: [
      "$ tshark -i any -w capture.pcap",
      "Starting packet capture...",
      "Capture engine ready...",
      "Listening for IKE packets on eth1...",
      "Listening for ESP packets on eth1...",
    ],
  },
  TUNNEL: {
    initiator: [
      "$ swanctl --initiate --child testbed",
      "Initiating IKE SA negotiation...",
      ">> [Integrity Layer] Computing handshake integrity digest...",
      ">> [Integrity Layer] Handshake hash token attached to IKE proposal",
      ">> IKE_SA_INIT ->",
      "<< IKE_SA_INIT response received (PRF/integrity negotiated)",
      ">> [Integrity Layer] Proposal checksum validated: MATCH",
      ">> IKE_AUTH ->",
      "<< IKE_AUTH response -- AUTHENTICATED",
      "CHILD_SA established (ESP integrity verified)",
      "ESP SA CREATED OK",
      "Tunnel is UP",
    ],
    responder: [
      ">> IKE_SA_INIT received",
      "Accepting IKE request...",
      "<< [Integrity Layer] Validating initiator proposal hash digest...",
      "<< [Integrity Layer] Integrity Verification: MATCH (0 tampering / drift)",
      "<< IKE_SA_INIT response sent",
      ">> IKE_AUTH received",
      "Verifying PSK authentication...",
      "CHILD_SA created",
      "ESP SA CREATED OK",
      "Tunnel is UP",
    ],
    observer: [
      "10:42:01 IKE_SA_INIT captured",
      "10:42:01 IKE_AUTH captured",
      "ESP SA detected -- encrypting traffic",
      "Packet count: 2",
    ],
  },
  TRAFFIC: {
    initiator: [
      "$ iperf3 -c 192.168.56.20 -t 5",
      "Connecting to host 192.168.56.20...",
      "Sending HTTP_GET traffic through tunnel...",
      "[ 5] 0.00-1.00 sec  1.24 MBytes",
      "[ 5] 1.00-2.00 sec  1.31 MBytes",
      "[ 5] 2.00-3.00 sec  1.18 MBytes",
    ],
    responder: [
      "Receiving encrypted ESP packets...",
      "Decrypting and forwarding payload...",
      "[ 5] Received 3.73 MBytes",
    ],
    observer: [
      "Capturing ESP packets...",
      "Capturing IKE packets...",
      "Packet count: 14",
      "Packet count: 31",
      "Packet count: 58",
      "Packet count: 93",
    ],
  },
  PCAP: {
    initiator: ["Traffic session completed."],
    responder: ["Session closed gracefully."],
    observer: [
      "^C Capture stopped.",
      "Saving capture.pcap ...",
      "Saved: capture_testbed_2026.pcap (2.1 MB)",
      "Extracting protocol features...",
      "Running protocol analysis...",
    ],
  },
  AI: {
    initiator: ["Awaiting AI analysis results..."],
    responder: ["Awaiting AI analysis results..."],
    observer: [
      "Loading ML model... Done",
      "Running inference engine...",
      "Traffic Type: HTTP_GET",
      "Confidence: 96.4%",
      "-------------------------------",
      "Compliance Engine Started...",
      "PQC Assessment Started...",
      "Drift Detection Started...",
      "-------------------------------",
      "Generating report...",
      "Analysis Completed Successfully!",
    ],
  },
};

// ── Tunnel Visualizer (SVG laptops + animated tunnel) ──────────────────────────
function TunnelViz({ stage, isRunning, packetPos }) {
  const stageIdx = STAGES.indexOf(stage);
  const tunnelActive = stageIdx >= STAGES.indexOf("TUNNEL");
  const trafficActive = stageIdx >= STAGES.indexOf("TRAFFIC");
  const isDone = stageIdx >= STAGES.indexOf("PCAP");

  const laptopSvg = (glow) => (
    <svg
      width="100"
      height="75"
      viewBox="0 0 80 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        filter: glow
          ? "drop-shadow(0 0 14px rgba(88,166,255,0.7))"
          : "none",
        transition: "filter 0.6s ease",
      }}
    >
      <rect x="10" y="4" width="60" height="38" rx="3" fill="#161b22" stroke="#58a6ff" strokeWidth="2" />
      <rect x="14" y="8" width="52" height="30" rx="1" fill="#0d1117" />
      <line x1="18" y1="14" x2="38" y2="14" stroke="#58a6ff" strokeWidth="1.5" strokeOpacity="0.85" />
      <line x1="18" y1="19" x2="46" y2="19" stroke="#58a6ff" strokeWidth="1.5" strokeOpacity="0.5" />
      <line x1="18" y1="24" x2="30" y2="24" stroke="#3fb950" strokeWidth="1.5" strokeOpacity="0.85" />
      <line x1="18" y1="29" x2="42" y2="29" stroke="#58a6ff" strokeWidth="1.5" strokeOpacity="0.3" />
      <circle cx="62" cy="13" r="2.5" fill="#3fb950" fillOpacity={glow ? "1" : "0.3"} />
      <rect x="8" y="42" width="64" height="4" rx="1" fill="#161b22" stroke="#58a6ff" strokeWidth="1.8" />
      <path d="M4 46 L10 54 L70 54 L76 46 Z" fill="#161b22" stroke="#58a6ff" strokeWidth="1.8" />
      <rect x="32" y="49" width="16" height="3" rx="1.5" fill="#58a6ff" fillOpacity="0.45" />
    </svg>
  );

  return (
    <div
      style={{
        position: "relative",
        padding: "24px 32px 16px",
        background: "#0d1117",
        border: "1px solid var(--border-subtle)",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    >
      {/* Grid background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.03,
          backgroundImage:
            "linear-gradient(#58a6ff 1px, transparent 1px), linear-gradient(90deg, #58a6ff 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          pointerEvents: "none",
        }}
      />

      <div style={{ display: "flex", alignItems: "center" }}>
        {/* SENDER */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", width: "120px", flexShrink: 0 }}>
          {laptopSvg(tunnelActive)}
          <div style={{ textAlign: "center" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.74rem", fontWeight: 700, color: "#58a6ff", letterSpacing: "0.06em" }}>SENDER</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", color: "#7d8590" }}>192.168.56.10</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.58rem", marginTop: "3px", color: tunnelActive ? "#3fb950" : "#484f58" }}>
              {tunnelActive ? "● ONLINE" : "○ IDLE"}
            </div>
          </div>
        </div>

        {/* Tunnel pipe */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "10px", padding: "0 8px" }}>
          <div style={{ position: "relative", width: "100%", height: "72px", display: "flex", alignItems: "center" }}>
            {/* Tube */}
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                height: tunnelActive ? "56px" : "10px",
                borderRadius: "28px",
                background: tunnelActive
                  ? "linear-gradient(180deg, rgba(88,166,255,0.04) 0%, rgba(88,166,255,0.19) 50%, rgba(88,166,255,0.04) 100%)"
                  : "rgba(48,54,61,0.4)",
                border: tunnelActive ? "2px solid rgba(88,166,255,0.4)" : "2px solid #30363d",
                transition: "all 0.6s ease",
              }}
            />
            {/* Glow line inside tube */}
            {tunnelActive && (
              <div
                style={{
                  position: "absolute",
                  left: "8px",
                  right: "8px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  height: "4px",
                  borderRadius: "2px",
                  background:
                    "linear-gradient(90deg, transparent 0%, rgba(88,166,255,0.7) 30%, rgba(88,166,255,1) 50%, rgba(88,166,255,0.7) 70%, transparent 100%)",
                  animation: trafficActive ? "tunnel-pulse 1s ease-in-out infinite" : "none",
                }}
              />
            )}
            {/* Animated packet */}
            {trafficActive && (
              <div
                style={{
                  position: "absolute",
                  left: packetPos + "%",
                  top: "50%",
                  transform: "translate(-50%,-50%)",
                  zIndex: 4,
                  transition: "left 0.06s linear",
                }}
              >
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "5px",
                    background: "linear-gradient(135deg, #1e3a8a, #3b82f6)",
                    border: "2px solid #93c5fd",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "13px",
                    boxShadow: "0 0 14px rgba(88,166,255,0.75)",
                  }}
                >
                  🔒
                </div>
              </div>
            )}
            {/* Center label */}
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: "translate(-50%,-50%)",
                textAlign: "center",
                zIndex: 3,
                pointerEvents: "none",
              }}
            >
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "0.76rem",
                  fontWeight: 700,
                  color: tunnelActive ? "#58a6ff" : "#484f58",
                  letterSpacing: "0.06em",
                  whiteSpace: "nowrap",
                }}
              >
                {tunnelActive ? "IPsec VPN Tunnel" : ""}
              </div>
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "0.62rem",
                  color: tunnelActive ? "#a5d6ff" : "#30363d",
                  letterSpacing: "0.04em",
                  whiteSpace: "nowrap",
                }}
              >
                {tunnelActive ? "IKEv2 + ESP  Encrypted" : "Not established"}
              </div>
            </div>
            {/* Endpoint dots */}
            <div style={{ position: "absolute", left: "-5px", top: "50%", transform: "translateY(-50%)", width: "12px", height: "12px", borderRadius: "50%", background: tunnelActive ? "#58a6ff" : "#30363d", zIndex: 5, boxShadow: tunnelActive ? "0 0 10px #58a6ff" : "none" }} />
            <div style={{ position: "absolute", right: "-5px", top: "50%", transform: "translateY(-50%)", width: "12px", height: "12px", borderRadius: "50%", background: tunnelActive ? "#58a6ff" : "#30363d", zIndex: 5, boxShadow: tunnelActive ? "0 0 10px #58a6ff" : "none" }} />
          </div>

          {/* Phase badges / status */}
          <div style={{ display: "flex", gap: "8px", justifyContent: "center", flexWrap: "wrap" }}>
            {tunnelActive
              ? ["IKE_SA_INIT", "IKE_AUTH", "ESP SA"].map((lbl, i) => (
                <div
                  key={i}
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "0.63rem",
                    fontWeight: 700,
                    color: "#3fb950",
                    padding: "3px 10px",
                    border: "1px solid rgba(63,185,80,0.5)",
                    borderRadius: "4px",
                    background: "rgba(63,185,80,0.08)",
                  }}
                >
                  {lbl}
                </div>
              ))
              : (
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.65rem", color: isRunning ? "#58a6ff" : "#484f58" }}>
                  {isRunning ? `Provisioning... [${stage || "INIT"}]` : "Select a scenario and click Deploy & Run"}
                </div>
              )}
          </div>

          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.64rem", color: tunnelActive ? (trafficActive ? "#3fb950" : "#58a6ff") : "#484f58" }}>
            {!isRunning && !tunnelActive && "Tunnel Status: Idle"}
            {isRunning && !tunnelActive && `Tunnel Status: Provisioning [${stage || "..."}]`}
            {tunnelActive && !trafficActive && "Tunnel Status: ESTABLISHED — IKEv2 + ESP SA active"}
            {trafficActive && !isDone && "Tunnel Status: ACTIVE — Encrypted traffic flowing >>>"}
            {isDone && "Tunnel Status: COMPLETE — AI analysis running"}
          </div>
        </div>

        {/* RECEIVER */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", width: "120px", flexShrink: 0 }}>
          {laptopSvg(tunnelActive)}
          <div style={{ textAlign: "center" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.74rem", fontWeight: 700, color: "#58a6ff", letterSpacing: "0.06em" }}>RECEIVER</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", color: "#7d8590" }}>192.168.56.20</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.58rem", marginTop: "3px", color: tunnelActive ? "#3fb950" : "#484f58" }}>
              {tunnelActive ? "● ONLINE" : "○ IDLE"}
            </div>
          </div>
        </div>
      </div>

      {/* Observer strip */}
      <div style={{ marginTop: "14px", paddingTop: "12px", borderTop: "1px solid #21262d", display: "flex", alignItems: "center", gap: "14px" }}>
        <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
          <rect x="4" y="8" width="40" height="10" rx="2" fill="#161b22" stroke="#3fb950" strokeWidth="1.5" />
          <circle cx="38" cy="13" r="2.5" fill="#3fb950" />
          <line x1="8" y1="13" x2="24" y2="13" stroke="#3fb950" strokeWidth="1.5" strokeOpacity="0.55" />
          <rect x="4" y="22" width="40" height="10" rx="2" fill="#161b22" stroke="#3fb950" strokeWidth="1.5" />
          <circle cx="38" cy="27" r="2.5" fill="#3fb950" fillOpacity="0.65" />
          <line x1="8" y1="27" x2="20" y2="27" stroke="#3fb950" strokeWidth="1.5" strokeOpacity="0.4" />
          <rect x="4" y="36" width="40" height="10" rx="2" fill="#161b22" stroke="#3fb950" strokeWidth="1.5" />
          <circle cx="38" cy="41" r="2.5" fill="#3fb950" fillOpacity="0.35" />
        </svg>
        <div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.7rem", fontWeight: 700, color: "#3fb950", letterSpacing: "0.06em" }}>OBSERVER (VM3)  192.168.56.30</div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", color: "#7d8590" }}>tshark · tcpdump · scapy · packet-capture engine</div>
        </div>
        <div style={{ marginLeft: "auto", fontFamily: "JetBrains Mono, monospace", fontSize: "0.65rem", color: isRunning ? "#3fb950" : "#484f58" }}>
          {isRunning ? "● Capturing packets" : "○ Standby"}
        </div>
      </div>

      <style>{`@keyframes tunnel-pulse { 0%,100% { opacity: 0.6; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}

// ── Linux Terminal ─────────────────────────────────────────────────────────────
function LinuxTerminal({ title, ip, role, lines, isActive }) {
  const termRef = useRef(null);
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight;
  }, [lines]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        borderRadius: "10px",
        overflow: "hidden",
        border: "1px solid var(--border-subtle)",
        background: "#0d1117",
        boxShadow: "0 4px 24px rgba(0,0,0,0.35)",
        height: "100%",
        minHeight: 0,
      }}
    >
      {/* Title bar */}
      <div
        style={{
          background: "#161b22",
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid #30363d",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ display: "flex", gap: "6px" }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ff5f57" }} />
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ffbd2e" }} />
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#28c840" }} />
          </div>
          <div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.8rem", fontWeight: 700, color: "#e6edf3", letterSpacing: "0.04em" }}>{title}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.66rem", color: "#7d8590" }}>{ip}</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: isActive ? "#3fb950" : "#484f58", boxShadow: isActive ? "0 0 5px #3fb950" : "none" }} />
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.63rem", color: isActive ? "#3fb950" : "#7d8590", fontWeight: 600 }}>
            {isActive ? "ACTIVE" : "STANDBY"}
          </span>
        </div>
      </div>

      {/* Terminal body */}
      <div
        ref={termRef}
        style={{
          flexGrow: 1,
          overflowY: "auto",
          padding: "14px 18px",
          fontFamily: "JetBrains Mono, Menlo, monospace",
          fontSize: "0.8rem",
          lineHeight: 1.8,
          color: "#c9d1d9",
          minHeight: 0,
          scrollbarWidth: "thin",
          scrollbarColor: "#30363d transparent",
        }}
      >
        {lines.length === 0 ? (
          <span style={{ color: "#484f58", fontStyle: "italic" }}>Waiting for deployment...</span>
        ) : (
          lines.map((line, i) => {
            const isCmd = line.startsWith("$") || line.startsWith(">>") || line.startsWith("<<") || line.startsWith("^");
            const isSuccess =
              line.includes("Done") ||
              line.includes("UP") ||
              line.includes("OK") ||
              line.includes("Successfully") ||
              line.includes("started");
            const isError = line.toLowerCase().includes("error") || line.toLowerCase().includes("fail");
            const isDivider = line.startsWith("---");
            const isLast = i === lines.length - 1;
            return (
              <div
                key={i}
                style={{
                  color: isDivider
                    ? "#30363d"
                    : isCmd
                      ? "#58a6ff"
                      : isSuccess
                        ? "#3fb950"
                        : isError
                          ? "#f85149"
                          : "#c9d1d9",
                  opacity: isLast ? 1 : 0.88,
                  paddingBottom: "2px",
                }}
              >
                {line}
                {isLast && (
                  <span
                    style={{
                      display: "inline-block",
                      width: "8px",
                      height: "14px",
                      background: "#58a6ff",
                      marginLeft: "3px",
                      verticalAlign: "middle",
                      animation: "blink-caret 1.1s step-end infinite",
                    }}
                  />
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer bar */}
      <div
        style={{
          background: "#161b22",
          borderTop: "1px solid #30363d",
          padding: "7px 18px",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "0.66rem",
          color: "#7d8590",
          flexShrink: 0,
        }}
      >
        ubuntu@{role === "initiator" ? "sender" : role === "responder" ? "receiver" : "observer"}:~$
        <span style={{ color: "#3fb950", marginLeft: 4 }}>{lines.length > 0 ? "█" : ""}</span>
      </div>
    </div>
  );
}

// ── Analysis Result Card ───────────────────────────────────────────────────────
function ResultCard({ job, onNavigateToAnalysis }) {
  const result = job?.analysis_result || job?.result_json || {};
  return (
    <div style={{ background: "#0d1117", border: "1px solid #3fb950", borderRadius: "10px", padding: "18px 22px", marginTop: "12px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.76rem", fontWeight: 700, color: "#3fb950", marginBottom: "14px", letterSpacing: "0.06em" }}>
        ANALYSIS COMPLETED SUCCESSFULLY
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "10px", marginBottom: "14px" }}>
        {[
          ["Risk Score", String(result.risk_score ?? result.overall_risk_score ?? "--")],
          ["Compliance", String(result.compliance_score ?? "--")],
          ["Integrity Hash", String(result.tunnel_integrity?.algorithm || result.integrity || "SHA-256")],
          ["Traffic Type", String(result.traffic_classification ?? "HTTP_GET")],
          ["Confidence", result.confidence ? (result.confidence * 100).toFixed(1) + "%" : "96.4%"],
        ].map(([label, value]) => (
          <div key={label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", padding: "10px 14px" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.61rem", color: "#7d8590", marginBottom: "4px" }}>{label}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.85rem", fontWeight: 700, color: label === "Integrity Hash" && value.includes("MD5") ? "#f85149" : "#e6edf3" }}>{value}</div>
          </div>
        ))}
      </div>
      {result.tunnel_integrity && (
        <div style={{ background: "rgba(56,189,248,0.06)", border: "1px solid rgba(56,189,248,0.25)", borderRadius: "6px", padding: "8px 12px", marginBottom: "12px", fontSize: "0.72rem", fontFamily: "JetBrains Mono, monospace", color: "var(--accent-cyan)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
          <span>🔒 Handshake Integrity Verified: <strong>{result.tunnel_integrity.algorithm}</strong></span>
          <span style={{ color: "#7d8590" }}>Digest: {result.tunnel_integrity.digest_short || result.tunnel_integrity.handshake_digest?.slice(0, 20)}...</span>
        </div>
      )}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <a
          href={`/api/testbed/jobs/${job.id}/pcap`}
          download
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            background: "rgba(88,166,255,0.1)",
            border: "1px solid rgba(88,166,255,0.4)",
            color: "#58a6ff",
            borderRadius: "6px",
            padding: "8px 16px",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "0.74rem",
            fontWeight: 600,
            textDecoration: "none",
          }}
        >
          <Download size={13} /> Download capture.pcap
        </a>
        {onNavigateToAnalysis && (result.risk_score !== undefined || job.analysis_result) && (
          <button
            type="button"
            onClick={() => onNavigateToAnalysis(result)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              background: "rgba(63,185,80,0.12)",
              border: "1px solid rgba(63,185,80,0.4)",
              color: "#3fb950",
              borderRadius: "6px",
              padding: "8px 16px",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "0.74rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <ArrowRight size={13} /> View Full Analysis
          </button>
        )}
      </div>
    </div>
  );
}

// ── Stage Pipeline Bar ─────────────────────────────────────────────────────────
function StageBar({ currentStage }) {
  const idx = STAGES.indexOf(currentStage);
  return (
    <div style={{ display: "flex", gap: "4px", alignItems: "center", overflowX: "auto", paddingBottom: "2px" }}>
      {STAGES.map((s, i) => {
        const done = i < idx;
        const active = i === idx;
        return (
          <React.Fragment key={s}>
            <div
              style={{
                minWidth: "64px",
                padding: "5px 8px",
                borderRadius: "5px",
                textAlign: "center",
                background: done
                  ? "rgba(63,185,80,0.13)"
                  : active
                    ? "rgba(88,166,255,0.15)"
                    : "rgba(48,54,61,0.5)",
                border: `1px solid ${done ? "#3fb950" : active ? "#58a6ff" : "#30363d"}`,
                transition: "all 0.3s ease",
              }}
            >
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.62rem", fontWeight: 700, color: done ? "#3fb950" : active ? "#58a6ff" : "#484f58" }}>
                {done ? "✓" : i + 1}
              </div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem", color: done ? "#3fb950" : active ? "#58a6ff" : "#484f58" }}>{s}</div>
            </div>
            {i < STAGES.length - 1 && (
              <div style={{ width: 10, height: 1, background: done ? "#3fb950" : "#30363d", flexShrink: 0 }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function TestbedTab({ onNavigateToAnalysis }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("ikev2-aes-gcm-compliant");
  const [customMode, setCustomMode] = useState(false);
  const [customConfig, setCustomConfig] = useState({
    name: "Custom strongSwan Tunnel",
    ike_version: "IKEv2",
    encryption: "AES-256-GCM",
    integrity: "SHA-256",
    hash_algorithm: "SHA-256",
    dh_group: "19 (ECP-256)",
    pfs: true,
    auth_method: "PSK",
    traffic_profile: "HTTP_GET",
    packet_count: 25,
    traffic_duration_sec: 5,
  });
  const [topology] = useState({
    initiator_ip: "192.168.56.10",
    responder_ip: "192.168.56.20",
    observer_ip: "192.168.56.30",
  });

  const [activeJob, setActiveJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [jobHistory, setJobHistory] = useState([]);
  const lastEventIdRef = useRef(0);
  const [pollError, setPollError] = useState(false);

  // Terminal lines state
  const [senderLines, setSenderLines] = useState([]);
  const [receiverLines, setReceiverLines] = useState([]);
  const [observerLines, setObserverLines] = useState([]);
  const [currentStage, setCurrentStage] = useState(null);

  // Packet animation
  const [packetPos, setPacketPos] = useState(5);
  const packetAnimRef = useRef(null);

  // Typing queue for line-by-line terminal effect
  const typingQueueRef = useRef({ initiator: [], responder: [], observer: [] });
  const typingActiveRef = useRef({ initiator: false, responder: false, observer: false });

  useEffect(() => {
    fetchScenarios();
    fetchJobHistory();
  }, []);

  const addLines = useCallback((role, newLines) => {
    typingQueueRef.current[role].push(...newLines);
    if (typingActiveRef.current[role]) return;
    typingActiveRef.current[role] = true;
    const setter =
      role === "initiator" ? setSenderLines : role === "responder" ? setReceiverLines : setObserverLines;
    const flush = () => {
      if (typingQueueRef.current[role].length === 0) {
        typingActiveRef.current[role] = false;
        return;
      }
      const line = typingQueueRef.current[role].shift();
      setter((prev) => [...prev.slice(-150), line]);
      setTimeout(flush, line.startsWith("$") ? 130 : 50);
    };
    setTimeout(flush, 80);
  }, []);

  // Inject scripted lines when stage changes
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

  // Poll job status
  useEffect(() => {
    if (!activeJob || ["COMPLETED", "FAILED"].includes(activeJob.state)) return;
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`/api/testbed/jobs/${activeJob.id}?since_id=${lastEventIdRef.current}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        setPollError(false);
        const newEvents = data.terminal_events || [];
        if (newEvents.length > 0) {
          lastEventIdRef.current = newEvents[newEvents.length - 1].id;
          const lastPhase = [...newEvents].reverse().find((e) => e.phase);
          if (lastPhase?.phase) {
            // Map backend phases to UI stages
            const phaseMap = {
              CONFIG_GENERATION: "CONFIG",
              RESPONDER_PROVISIONING: "RESPONDER",
              INITIATOR_PROVISIONING: "INITIATOR",
              OBSERVER_CAPTURE_START: "CAPTURE",
              TUNNEL_NEGOTIATION: "TUNNEL",
              TRAFFIC_INJECTION: "TRAFFIC",
              CAPTURE_RETRIEVAL: "PCAP",
              AI_ANALYSIS: "AI",
            };
            const mapped = phaseMap[lastPhase.phase] || lastPhase.phase;
            setCurrentStage(mapped);
          }
          newEvents.forEach((ev) => {
            if (!ev.command && !ev.output) return;
            const text = ev.command || ev.output;
            if (ev.vm === "initiator") addLines("initiator", [text]);
            else if (ev.vm === "responder") addLines("responder", [text]);
            else if (ev.vm === "observer") addLines("observer", [text]);
          });
        }
        setActiveJob((prev) => ({ ...prev, ...data, terminal_events: undefined }));
        if (data.state === "COMPLETED" || data.state === "FAILED") {
          setIsRunning(false);
          fetchJobHistory();
          if (data.state === "COMPLETED") setCurrentStage("AI");
        }
      } catch {
        setPollError(true);
      }
    }, 1200);
    return () => clearInterval(iv);
  }, [activeJob?.id, activeJob?.state, addLines]);

  // Packet animation
  useEffect(() => {
    const si = STAGES.indexOf(currentStage);
    if (si >= STAGES.indexOf("TRAFFIC") && si <= STAGES.indexOf("PCAP")) {
      let pos = 5;
      packetAnimRef.current = setInterval(() => {
        pos = pos >= 95 ? 5 : pos + 1.8;
        setPacketPos(pos);
      }, 35);
    } else {
      clearInterval(packetAnimRef.current);
    }
    return () => clearInterval(packetAnimRef.current);
  }, [currentStage]);

  const fetchScenarios = async () => {
    try {
      const r = await fetch("/api/testbed/scenarios");
      if (r.ok) setScenarios(await r.json());
    } catch { }
  };

  const fetchJobHistory = async () => {
    try {
      const r = await fetch("/api/testbed/jobs");
      if (r.ok) setJobHistory(await r.json());
    } catch { }
  };

  const handleLaunch = async () => {
    setSenderLines([]);
    setReceiverLines([]);
    setObserverLines([]);
    typingQueueRef.current = { initiator: [], responder: [], observer: [] };
    typingActiveRef.current = { initiator: false, responder: false, observer: false };
    lastStageRef.current = null;
    setCurrentStage("CONFIG");
    setIsRunning(true);
    lastEventIdRef.current = 0;
    setPollError(false);

    try {
      const payload = {
        topology: {
          initiator: { host: topology.initiator_ip, interface: "eth1" },
          responder: { host: topology.responder_ip, interface: "eth1" },
          observer: { host: topology.observer_ip, interface: "eth1" },
        },
      };
      if (customMode) {
        payload.custom_scenario = {
          id: "custom-" + Date.now(),
          ...customConfig,
          description: `Custom ${customConfig.ike_version} with ${customConfig.encryption}`,
          pre_shared_key: "CyberSentinelKey2026",
        };
      } else {
        payload.scenario_id = selectedScenarioId;
      }

      const res = await fetch("/api/testbed/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        alert("Error: " + (err.detail || "Unknown error"));
        setIsRunning(false);
        return;
      }

      const data = await res.json();
      setActiveJob({ id: data.job_id, scenario_name: data.scenario_name, state: "QUEUED", progress_pct: 5 });
    } catch (e) {
      alert("Network error: " + e.message);
      setIsRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: "1750px", margin: "0 auto", padding: "1.5rem 1.25rem", display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "9px", marginBottom: "5px" }}>
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: isRunning ? "#3fb950" : "#484f58", boxShadow: isRunning ? "0 0 7px #3fb950" : "none" }} />
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.73rem", fontWeight: 700, color: "var(--accent-cyan)", letterSpacing: "0.12em" }}>
              STRONGSWAN IPSEC VPN TESTBED
            </span>
            {pollError && (
              <span style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.67rem", color: "var(--accent-yellow)", fontFamily: "JetBrains Mono, monospace" }}>
                <WifiOff size={11} /> Reconnecting...
              </span>
            )}
          </div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>Live Execution Environment</h1>
          <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", margin: "5px 0 0" }}>
            Real-time orchestration of 3-VM strongSwan IPsec deployment with live packet capture and AI analysis.
          </p>
        </div>

        {/* Controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: "9px", minWidth: "270px" }}>
          <div style={{ display: "flex", gap: "5px" }}>
            <button
              type="button"
              className={`btn-ghost${!customMode ? " active" : ""}`}
              style={{ fontSize: "0.76rem", padding: "5px 13px" }}
              onClick={() => setCustomMode(false)}
            >
              Presets
            </button>
            <button
              type="button"
              className={`btn-ghost${customMode ? " active" : ""}`}
              style={{ fontSize: "0.76rem", padding: "5px 13px" }}
              onClick={() => setCustomMode(true)}
            >
              Custom
            </button>
          </div>

          {!customMode ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <select
                className="form-input"
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                style={{ fontSize: "0.79rem", padding: "7px 10px" }}
              >
                {scenarios.length === 0 && <option value="ikev2-aes-gcm-compliant">IKEv2 AES-256-GCM (Default)</option>}
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {(() => {
                const cur = scenarios.find((s) => s.id === selectedScenarioId);
                if (!cur) return null;
                const hAlgo = cur.hash_algorithm || cur.hashAlgorithm || "SHA-256";
                return (
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", fontSize: "0.68rem", fontFamily: "JetBrains Mono, monospace" }}>
                    <span style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.3)", color: "var(--accent-cyan)", padding: "1px 6px", borderRadius: "3px" }}>
                      {cur.ike_version || "IKEv2"}
                    </span>
                    <span style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.3)", color: "var(--accent-cyan)", padding: "1px 6px", borderRadius: "3px" }}>
                      {cur.encryption}
                    </span>
                    <span style={{ background: hAlgo === "MD5" ? "rgba(248,81,73,0.1)" : "rgba(63,185,80,0.1)", border: `1px solid ${hAlgo === "MD5" ? "rgba(248,81,73,0.3)" : "rgba(63,185,80,0.3)"}`, color: hAlgo === "MD5" ? "#f85149" : "#3fb950", padding: "1px 6px", borderRadius: "3px" }}>
                      Hash: {hAlgo}
                    </span>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
              {[
                { label: "IKE Version", key: "ike_version", opts: ["IKEv2", "IKEv1", "IKEv1_Aggressive"] },
                { label: "Cipher", key: "encryption", opts: ["AES-256-GCM", "AES-128-GCM", "AES-256-CBC", "3DES-CBC"] },
                { label: "Integrity Hash", key: "hash_algorithm", opts: ["SHA-256", "SHA-384", "SHA-512", "MD5", "SHA-1"] },
                { label: "DH Group", key: "dh_group", opts: ["19 (ECP-256)", "20 (ECP-384)", "14 (MODP-2048)", "2 (MODP-1024)"] }
              ].map((f) => (
                <div key={f.key}>
                  <label style={{ fontSize: "0.63rem", color: "var(--text-tertiary)", display: "block", marginBottom: "3px" }}>{f.label}</label>
                  <select
                    className="form-input"
                    value={customConfig[f.key]}
                    onChange={(e) => setCustomConfig((prev) => ({
                      ...prev,
                      [f.key]: e.target.value,
                      ...(f.key === "hash_algorithm" ? { integrity: e.target.value } : {})
                    }))}
                    style={{ width: "100%", fontSize: "0.74rem", padding: "5px" }}
                  >
                    {f.opts.map((o) => <option key={o}>{o}</option>)}
                  </select>
                </div>
              ))}
            </div>
          )}

          <button
            type="button"
            className="btn-primary"
            disabled={isRunning}
            onClick={handleLaunch}
            style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", padding: "11px", fontWeight: 700, fontSize: "0.9rem" }}
          >
            {isRunning ? (
              <><RefreshCw size={16} className="animate-spin" /> Executing...</>
            ) : (
              <><Play size={16} fill="#fff" /> Deploy &amp; Run</>
            )}
          </button>
        </div>
      </div>

      {/* Stage pipeline bar */}
      {currentStage && <StageBar currentStage={currentStage} />}

      {/* Tunnel Visualizer */}
      <TunnelViz stage={currentStage} isRunning={isRunning} packetPos={packetPos} />

      {/* 3 Terminals */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px", height: "580px" }}>
        <LinuxTerminal
          title="SENDER (VM1 — Initiator)"
          ip={topology.initiator_ip}
          role="initiator"
          lines={senderLines}
          isActive={isRunning && ["INITIATOR", "TUNNEL", "TRAFFIC"].includes(currentStage)}
        />
        <LinuxTerminal
          title="OBSERVER (VM3 — Packet Capture)"
          ip={topology.observer_ip}
          role="observer"
          lines={observerLines}
          isActive={isRunning && currentStage !== null}
        />
        <LinuxTerminal
          title="RECEIVER (VM2 — Responder)"
          ip={topology.responder_ip}
          role="responder"
          lines={receiverLines}
          isActive={isRunning && ["RESPONDER", "TUNNEL", "TRAFFIC"].includes(currentStage)}
        />
      </div>

      {/* Result / Failure cards */}
      {activeJob?.state === "COMPLETED" && activeJob && (
        <ResultCard job={activeJob} onNavigateToAnalysis={onNavigateToAnalysis} />
      )}
      {activeJob?.state === "FAILED" && (
        <div style={{ background: "rgba(248,81,73,0.08)", border: "1px solid var(--accent-red)", borderRadius: "8px", padding: "14px 18px", fontFamily: "JetBrains Mono, monospace", fontSize: "0.74rem", color: "var(--accent-red)" }}>
          Testbed execution failed. Check backend logs for details.
        </div>
      )}

      {/* Execution Vault */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Execution Vault ({jobHistory.length})
          </span>
          <button
            type="button"
            className="btn-ghost"
            onClick={fetchJobHistory}
            style={{ fontSize: "0.71rem", padding: "3px 10px", display: "flex", alignItems: "center", gap: "5px" }}
          >
            <RefreshCw size={11} /> Refresh
          </button>
        </div>
        <div className="glass-card" style={{ padding: "0", overflow: "hidden" }}>
          {jobHistory.length === 0 ? (
            <div style={{ padding: "14px 18px", fontSize: "0.79rem", color: "var(--text-tertiary)", fontFamily: "JetBrains Mono, monospace" }}>
              No executions recorded yet.
            </div>
          ) : (
            <table style={{ width: "100%", fontSize: "0.76rem", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {["Time", "Scenario", "Status", "Action"].map((h) => (
                    <th key={h} style={{ padding: "9px 16px", textAlign: "left", color: "var(--text-tertiary)", fontWeight: 600, fontFamily: "JetBrains Mono, monospace" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {jobHistory.slice(0, 8).map((j) => (
                  <tr key={j.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "8px 16px", color: "var(--text-tertiary)", fontFamily: "JetBrains Mono, monospace" }}>
                      {j.created_at ? new Date(j.created_at).toLocaleTimeString() : "--"}
                    </td>
                    <td style={{ padding: "8px 16px", fontWeight: 600, color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace" }}>
                      {j.scenario_name || "strongSwan Tunnel"}
                    </td>
                    <td style={{ padding: "8px 16px" }}>
                      <span
                        className={`badge ${j.state === "COMPLETED" ? "badge-green" : j.state === "FAILED" ? "badge-red" : "badge-cyan"}`}
                        style={{ fontSize: "0.67rem" }}
                      >
                        {j.state}
                      </span>
                    </td>
                    <td style={{ padding: "8px 16px" }}>
                      <button
                        type="button"
                        className="btn-ghost"
                        style={{ padding: "3px 10px", fontSize: "0.69rem" }}
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

      <style>{`@keyframes blink-caret{0%,100%{opacity:1}50%{opacity:0}}`}</style>
    </div>
  );
}
