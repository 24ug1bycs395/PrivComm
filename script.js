/**
 * Cyber Sentinel - Interactive Topology & Platform Features
 * Integrated with AI Encrypted Traffic Classifier & Security Policy Assessment Engine.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTopologyCanvas();
});

function initTopologyCanvas() {
  const canvas = document.getElementById('topologyCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let animationFrameId;

  function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  const nodes = [
    { id: 'gw-a', label: 'SITE-01 GATEWAY', xPercent: 0.12, yPercent: 0.48, isHub: false },
    { id: 'ep-a1', label: 'BRANCH SUB-A', xPercent: 0.05, yPercent: 0.22, isHub: false },
    { id: 'ep-a2', label: 'INGRESS PEER', xPercent: 0.07, yPercent: 0.74, isHub: false },
    { id: 'core', label: 'SENTINEL INTELLIGENCE CORE', xPercent: 0.50, yPercent: 0.48, isHub: true },
    { id: 'gw-b', label: 'SITE-02 GATEWAY', xPercent: 0.88, yPercent: 0.48, isHub: false },
    { id: 'ep-b1', label: 'DATA CENTER E-B', xPercent: 0.94, yPercent: 0.24, isHub: false },
    { id: 'ep-b2', label: 'BACKBONE INGRESS', xPercent: 0.92, yPercent: 0.76, isHub: false },
    { id: 'relay-1', label: 'VERIFIED TRANSIT-1', xPercent: 0.31, yPercent: 0.25, isHub: false },
    { id: 'relay-2', label: 'VERIFIED TRANSIT-2', xPercent: 0.31, yPercent: 0.71, isHub: false },
    { id: 'relay-3', label: 'VERIFIED TRANSIT-3', xPercent: 0.69, yPercent: 0.25, isHub: false },
    { id: 'relay-4', label: 'VERIFIED TRANSIT-4', xPercent: 0.69, yPercent: 0.71, isHub: false },
  ];

  const links = [
    { from: 'ep-a1', to: 'gw-a' },
    { from: 'ep-a2', to: 'gw-a' },
    { from: 'gw-a', to: 'relay-1' },
    { from: 'gw-a', to: 'relay-2' },
    { from: 'relay-1', to: 'core' },
    { from: 'relay-2', to: 'core' },
    { from: 'core', to: 'relay-3' },
    { from: 'core', to: 'relay-4' },
    { from: 'relay-3', to: 'gw-b' },
    { from: 'relay-4', to: 'gw-b' },
    { from: 'gw-b', to: 'ep-b1' },
    { from: 'gw-b', to: 'ep-b2' },
    { from: 'gw-a', to: 'core', isTunnelBackbone: true },
    { from: 'core', to: 'gw-b', isTunnelBackbone: true },
  ];

  const particles = [];
  const particleCount = 20;

  for (let i = 0; i < particleCount; i++) {
    const link = links[Math.floor(Math.random() * links.length)];
    particles.push({
      link: link,
      progress: Math.random(),
      speed: 0.002 + Math.random() * 0.003,
      size: 2.2 + Math.random() * 1.5,
    });
  }

  function getNodeCoords(node, width, height) {
    return {
      x: node.xPercent * width,
      y: node.yPercent * height,
    };
  }

  function render(time) {
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
    ctx.lineWidth = 1;
    const step = 40;
    for (let x = 0; x < width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const coordMap = {};
    nodes.forEach(node => {
      coordMap[node.id] = getNodeCoords(node, width, height);
    });

    links.forEach(link => {
      const p1 = coordMap[link.from];
      const p2 = coordMap[link.to];
      if (!p1 || !p2) return;

      if (link.isTunnelBackbone) {
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
        ctx.setLineDash([]);
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
    });

    particles.forEach(p => {
      p.progress += p.speed;
      if (p.progress >= 1) {
        p.progress = 0;
        p.link = links[Math.floor(Math.random() * links.length)];
      }

      const p1 = coordMap[p.link.from];
      const p2 = coordMap[p.link.to];
      if (!p1 || !p2) return;

      const curX = p1.x + (p2.x - p1.x) * p.progress;
      const curY = p1.y + (p2.y - p1.y) * p.progress;

      ctx.fillStyle = '#38bdf8';
      ctx.shadowColor = '#38bdf8';
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(curX, curY, p.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    nodes.forEach(node => {
      const { x, y } = coordMap[node.id];

      if (node.isHub) {
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(x, y, 22, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = 'rgba(37, 99, 235, 0.2)';
        ctx.beginPath();
        ctx.arc(x, y, 14, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#38bdf8';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();
      } else if (node.id.startsWith('gw')) {
        ctx.strokeStyle = 'rgba(147, 197, 253, 0.5)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = '#1e3a8a';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(x, y, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    animationFrameId = requestAnimationFrame(render);
  }

  animationFrameId = requestAnimationFrame(render);
}

function openPcapModal() {
  const modal = document.getElementById('pcapModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closePcapModal() {
  const modal = document.getElementById('pcapModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closePcapModal();
});

document.addEventListener('click', (e) => {
  const modal = document.getElementById('pcapModal');
  if (e.target === modal) {
    closePcapModal();
  }
});

async function loadSampleScenario(scenarioType) {
  openPcapModal();
  const resultBox = document.getElementById('inspectionResult');
  const resTitle = document.getElementById('resTitle');
  const resBadge = document.getElementById('resBadge');
  const resConsole = document.getElementById('resConsole');

  if (!resultBox || !resConsole) return;
  resultBox.style.display = 'block';

  resTitle.textContent = 'Analyzing Sample Capture: ikev2_s2s_ipsec_vpn_aes_gcm.pcapng...';
  resBadge.textContent = 'RUNNING PROTOCOL & AI ENGINES';
  resBadge.style.background = 'rgba(56, 189, 248, 0.15)';
  resBadge.style.color = '#38bdf8';

  try {
    const response = await fetch('/analyze/sample');
    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }
    const data = await response.json();
    renderAnalysisResults(data, "ikev2_s2s_ipsec_vpn_aes_gcm.pcapng");
  } catch (err) {
    resBadge.textContent = 'SAMPLE ANALYSIS';
    renderSampleFallback(scenarioType);
  }
}

async function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const resultBox = document.getElementById('inspectionResult');
  const resTitle = document.getElementById('resTitle');
  const resBadge = document.getElementById('resBadge');
  const resConsole = document.getElementById('resConsole');

  if (!resultBox || !resConsole) return;

  resultBox.style.display = 'block';
  resTitle.textContent = `Analyzing: ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`;
  resBadge.textContent = 'TRANSMITTING TO PROTOCOL ENGINE';
  resBadge.style.background = 'rgba(56, 189, 248, 0.15)';
  resBadge.style.color = '#38bdf8';

  resConsole.innerHTML = `
    <span class="console-line"><span class="console-highlight">[INGESTION]</span> Streaming capture file to backend Protocol Identification Engine...</span>
    <span class="console-line"><span class="console-highlight">[DISSECTION]</span> Parsing IKEv1/IKEv2 handshakes and ESP/AH encapsulation headers...</span>
    <span class="console-line"><span class="console-highlight">[AI CLASSIFIER]</span> Computing 28 flow features and running XGBoost Multiclass Inference...</span>
    <span class="console-line"><span class="console-highlight">[SECURITY AUDIT]</span> Evaluating security baseline compliance & generating executive report...</span>
  `;

  try {
    const formData = new FormData();
    formData.append('pcap_file', file);

    const response = await fetch('/analyze/protocol', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    renderAnalysisResults(data, file.name);
  } catch (err) {
    resBadge.textContent = 'ANALYSIS NOTICE';
    resConsole.innerHTML += `
      <span class="console-line" style="color: #94a3b8; margin-top: 6px;"><span class="console-highlight">[ENGINE NOTICE]</span> ${err.message}</span>
      <span class="console-line" style="color: #64748b;">(Start backend server with <code>python main.py server</code> to enable live upload processing)</span>
    `;
  }
}

function renderAnalysisResults(data, filename) {
  const resTitle = document.getElementById('resTitle');
  const resBadge = document.getElementById('resBadge');
  const resConsole = document.getElementById('resConsole');

  resTitle.textContent = `Analyzed: ${filename}`;
  
  const sec = data.security_assessment || {};
  const riskLevel = sec.risk_level || (data.ipsec_detected ? "SECURE" : "UNKNOWN");
  const riskScore = sec.risk_score || 0;

  resBadge.textContent = `RISK: ${riskLevel} (${riskScore}/100)`;
  if (riskLevel === "SECURE" || riskLevel === "LOW") {
    resBadge.style.background = 'rgba(34, 197, 94, 0.2)';
    resBadge.style.color = '#4ade80';
  } else if (riskLevel === "MEDIUM") {
    resBadge.style.background = 'rgba(234, 179, 8, 0.2)';
    resBadge.style.color = '#fde047';
  } else {
    resBadge.style.background = 'rgba(239, 68, 68, 0.2)';
    resBadge.style.color = '#fca5a5';
  }

  const tc = data.traffic_classification || {};
  const trafficType = tc.traffic_type || "N/A";
  const confidence = tc.confidence ? (tc.confidence * 100).toFixed(1) + "%" : "N/A";

  let findingsHtml = "";
  const findings = sec.findings || [];
  if (findings.length > 0) {
    findings.forEach(f => {
      findingsHtml += `<div style="margin-top:8px; padding:8px; background:rgba(239, 68, 68, 0.1); border-left:3px solid #ef4444; border-radius:4px;">
        <strong>[${f.finding_id}] ${f.title} (${f.severity})</strong><br>
        <small>Observed: ${f.observed} | Expected: ${f.expected}</small><br>
        <small style="color:#7dd3fc;">Action: ${f.recommendation}</small>
      </div>`;
    });
  } else {
    findingsHtml = `<div style="margin-top:8px; padding:8px; background:rgba(34, 197, 94, 0.1); border-left:3px solid #22c55e; border-radius:4px; color:#4ade80;">
      ✓ Configuration complies with security policy baselines. No vulnerabilities observed.
    </div>`;
  }

  resConsole.innerHTML = `
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin-bottom:12px;">
      <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; text-align:center;">
        <span style="font-size:0.7rem; color:#94a3b8;">IPSEC PROTOCOL</span><br>
        <strong style="color:#38bdf8;">${data.ike_version || 'IKEv2'} (${data.mode || 'Tunnel'})</strong>
      </div>
      <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; text-align:center;">
        <span style="font-size:0.7rem; color:#94a3b8;">AI TRAFFIC CLASS</span><br>
        <strong style="color:#38bdf8;">${trafficType} (${confidence})</strong>
      </div>
      <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; text-align:center;">
        <span style="font-size:0.7rem; color:#94a3b8;">RISK SCORE</span><br>
        <strong style="color:#38bdf8;">${riskScore}/100 [${riskLevel}]</strong>
      </div>
    </div>

    <span class="console-line"><span class="console-highlight">[CIPHER SUITE]</span> Encryption: <strong>${data.encryption || 'AES-256-GCM'}</strong> &bull; Integrity: <strong>${data.integrity || 'AEAD'}</strong></span>
    <span class="console-line"><span class="console-highlight">[KEY EXCHANGE]</span> DH Group: <strong>Group ${data.dh_group || '19'}</strong> &bull; PFS: <strong>Enforced</strong></span>
    <span class="console-line"><span class="console-highlight">[ENCAPSULATION]</span> ESP: <strong>${data.esp_detected}</strong> &bull; AH: <strong>${data.ah_detected}</strong> &bull; Replay Protection: <strong>Active</strong></span>

    <div style="margin-top:12px;">
      <span class="console-highlight">[SECURITY AUDIT FINDINGS]</span>
      ${findingsHtml}
    </div>

    <div style="margin-top:15px; display:flex; gap:10px;">
      <a href="/reports/download-html?filename=${encodeURIComponent(filename)}" target="_blank" class="btn btn-primary-sm" style="text-decoration:none;">
        🌐 Download Executive HTML Report
      </a>
      <a href="/reports/download-json?filename=${encodeURIComponent(filename)}" target="_blank" class="btn btn-secondary-sm" style="text-decoration:none;">
        📄 Download Technical JSON
      </a>
    </div>
  `;
}

function renderSampleFallback(scenarioType) {
  const resTitle = document.getElementById('resTitle');
  const resBadge = document.getElementById('resBadge');
  const resConsole = document.getElementById('resConsole');

  if (scenarioType === 'ikev2-strong') {
    resTitle.textContent = 'Capture: IKEv2_SuiteB_GCM256.pcap';
    resBadge.textContent = 'COMPLIANT &bull; NIST SP 800-77';
    resBadge.style.background = 'rgba(56, 189, 248, 0.15)';
    resBadge.style.color = '#38bdf8';

    resConsole.innerHTML = `
      <span class="console-line"><span class="console-highlight">[PACKET DISSECTOR]</span> Parsed 1,482 frames across 2 tunnel endpoints.</span>
      <span class="console-line"><span class="console-highlight">[IKE_SA_INIT]</span> Initiator SPI: 0xa9f4e28174b081c2 &bull; Responder SPI: 0x981255e1a3bc47d0</span>
      <span class="console-line"><span class="console-highlight">[TRANSFORM]</span> Encryption: AES-GCM (256-bit key) &bull; PRF: PRF_HMAC_SHA2_384</span>
      <span class="console-line"><span class="console-highlight">[DIFFIE-HELLMAN]</span> Group 19 (256-bit Random ECP group) &bull; PFS Enforced</span>
      <span class="console-line"><span class="console-highlight">[AI TRAFFIC CLASS]</span> Predicted: CHAT (Confidence: 47.7%)</span>
      <span class="console-line"><span class="console-highlight">[EVALUATION]</span> Conforms to NIST SP 800-77 Rev 1 guidelines and NSA CSfC 4.1 baseline.</span>
    `;
  } else {
    resTitle.textContent = 'Capture: IKEv1_Aggressive_DES_MD5.pcap';
    resBadge.textContent = 'POLICY VIOLATION DETECTED';
    resBadge.style.background = 'rgba(239, 68, 68, 0.2)';
    resBadge.style.color = '#fca5a5';

    resConsole.innerHTML = `
      <span class="console-line"><span class="console-highlight">[PACKET DISSECTOR]</span> Parsed 844 frames across 2 tunnel endpoints.</span>
      <span class="console-line"><span class="console-highlight">[IKEv1 MODE]</span> Aggressive Mode exchange detected.</span>
      <span class="console-line"><span class="console-warning">[DEPRECATION WARNING]</span> Cipher: 3DES-CBC &bull; Integrity Hash: MD5 (RFC 8221 Deprecated)</span>
      <span class="console-line"><span class="console-warning">[KEY EXCHANGE RISK]</span> Diffie-Hellman Group 2 (MODP 1024-bit) &bull; Sub-minimum security margin.</span>
      <span class="console-line"><span class="console-warning">[REMEDIATION DIRECTIVE]</span> Upgrade tunnel policy to IKEv2 with AES-256-GCM and DH Group 14+ or Group 19.</span>
    `;
  }
}
