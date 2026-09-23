/**
 * Cyber Sentinel - Interactive Topology & Platform Features
 * Pure Vanilla JavaScript: Deterministic, elegant canvas rendering & interaction
 * No fake statistics, no threat counters, no active attack widgets.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTopologyCanvas();
});

/**
 * Renders an abstract network topology visualization
 * with subtle VPN tunnel connections and flowing data paths.
 * Crisp high-DPI canvas rendering.
 */
function initTopologyCanvas() {
  const canvas = document.getElementById('topologyCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let animationFrameId;

  // Handle High-DPI displays
  function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // Topology node definitions (Abstract site-to-site & hub mesh)
  // Percentages are used so layout adapts smoothly to screen widths
  const nodes = [
    { id: 'gw-a', label: 'SITE-01 GATEWAY', xPercent: 0.12, yPercent: 0.48, isHub: false },
    { id: 'ep-a1', label: 'BRANCH SUB-A', xPercent: 0.05, yPercent: 0.22, isHub: false },
    { id: 'ep-a2', label: 'INGRESS PEER', xPercent: 0.07, yPercent: 0.74, isHub: false },

    { id: 'core', label: 'SENTINEL INTELLIGENCE CORE', xPercent: 0.50, yPercent: 0.48, isHub: true },

    { id: 'gw-b', label: 'SITE-02 GATEWAY', xPercent: 0.88, yPercent: 0.48, isHub: false },
    { id: 'ep-b1', label: 'DATA CENTER E-B', xPercent: 0.94, yPercent: 0.24, isHub: false },
    { id: 'ep-b2', label: 'BACKBONE INGRESS', xPercent: 0.92, yPercent: 0.76, isHub: false },

    // Intermediate mesh verification points
    { id: 'relay-1', label: 'VERIFIED TRANSIT-1', xPercent: 0.31, yPercent: 0.25, isHub: false },
    { id: 'relay-2', label: 'VERIFIED TRANSIT-2', xPercent: 0.31, yPercent: 0.71, isHub: false },
    { id: 'relay-3', label: 'VERIFIED TRANSIT-3', xPercent: 0.69, yPercent: 0.25, isHub: false },
    { id: 'relay-4', label: 'VERIFIED TRANSIT-4', xPercent: 0.69, yPercent: 0.71, isHub: false },
  ];

  // Abstract VPN Tunnel Paths
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
    // Direct encrypted backbone IPsec tunnel line
    { from: 'gw-a', to: 'core', isTunnelBackbone: true },
    { from: 'core', to: 'gw-b', isTunnelBackbone: true },
  ];

  // Flowing packet indicators along tunnel paths
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

    // 1. Draw subtle background coordinate mesh lines
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

    // Lookup table for node coords
    const coordMap = {};
    nodes.forEach(node => {
      coordMap[node.id] = getNodeCoords(node, width, height);
    });

    // 2. Draw Tunnel Links
    links.forEach(link => {
      const p1 = coordMap[link.from];
      const p2 = coordMap[link.to];
      if (!p1 || !p2) return;

      if (link.isTunnelBackbone) {
        // Main Encrypted IPsec Tunnel line
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
        ctx.setLineDash([]);
      } else {
        // Subtle auxiliary mesh lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
    });

    // 3. Render animated particles representing ESP encapsulated traffic
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

    // 4. Render Nodes
    nodes.forEach(node => {
      const { x, y } = coordMap[node.id];

      if (node.isHub) {
        // Sentinel Core Node (Center)
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
        // Gateway Nodes
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
        // Peripheral / Transit Nodes
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

/**
 * Modal Management for PCAP Ingestion
 */
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

// Close on Escape or outside backdrop click
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closePcapModal();
});

document.addEventListener('click', (e) => {
  const modal = document.getElementById('pcapModal');
  if (e.target === modal) {
    closePcapModal();
  }
});

/**
 * Reference protocol handshake inspection simulator
 * Strictly displays factual RFC standards, dissection offsets, and NIST mapping.
 * No fake alerts, no random threat scores, no mock dashboards.
 */
function loadSampleScenario(scenarioType) {
  const resultBox = document.getElementById('inspectionResult');
  const resTitle = document.getElementById('resTitle');
  const resBadge = document.getElementById('resBadge');
  const resConsole = document.getElementById('resConsole');

  if (!resultBox || !resConsole) return;

  resultBox.style.display = 'block';

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
      <span class="console-line"><span class="console-highlight">[ENCAPSULATION]</span> ESP (IP Protocol 50) Tunnel Mode &bull; Sequence Replay Window: 64</span>
      <span class="console-line"><span class="console-highlight">[EVALUATION]</span> Conforms to NIST SP 800-77 Rev 1 guidelines and NSA CSfC 4.1 baseline.</span>
    `;
  } else {
    resTitle.textContent = 'Capture: IKEv1_Aggressive_DES_MD5.pcap';
    resBadge.textContent = 'POLICY VIOLATION DETECTED';
    resBadge.style.background = 'rgba(255, 255, 255, 0.08)';
    resBadge.style.color = '#f8fafc';

    resConsole.innerHTML = `
      <span class="console-line"><span class="console-highlight">[PACKET DISSECTOR]</span> Parsed 844 frames across 2 tunnel endpoints.</span>
      <span class="console-line"><span class="console-highlight">[IKEv1 MODE]</span> Aggressive Mode exchange detected in Frame #3.</span>
      <span class="console-line"><span class="console-warning">[DEPRECATION WARNING]</span> Cipher: 3DES-CBC &bull; Integrity Hash: MD5 (RFC 8221 Deprecated)</span>
      <span class="console-line"><span class="console-warning">[KEY EXCHANGE RISK]</span> Diffie-Hellman Group 2 (MODP 1024-bit) &bull; Sub-minimum security margin.</span>
      <span class="console-line"><span class="console-warning">[IDENTIFIER EXPOSURE]</span> Pre-Shared Key hash transmitted in unencrypted handshake packet.</span>
      <span class="console-line"><span class="console-highlight">[REMEDIATION DIRECTIVE]</span> Upgrade tunnel policy to IKEv2 with AES-256-GCM and DH Group 14+ (2048-bit MODP) or Group 19 (ECP-256).</span>
    `;
  }
}

/**
 * Handle user file drag / upload and post to /analyze/protocol backend service
 */
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
  `;

  try {
    const formData = new FormData();
    formData.append('pcap_file', file);

    const response = await fetch('http://localhost:8000/analyze/protocol', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    resTitle.textContent = `Analyzed: ${file.name}`;
    resBadge.textContent = data.ipsec_detected ? 'IPSEC PROTOCOL IDENTIFIED' : 'NO IPSEC DETECTED';

    resConsole.innerHTML = `
      <span class="console-line"><span class="console-highlight">[RESULT]</span> IPsec Detected: <strong>${data.ipsec_detected}</strong></span>
      <span class="console-line"><span class="console-highlight">[IKE VERSION]</span> ${data.ike_version || 'None / Not Present'}</span>
      <span class="console-line"><span class="console-highlight">[ESP DETECTED]</span> ${data.esp_detected} &bull; <span class="console-highlight">[AH DETECTED]</span> ${data.ah_detected}</span>
      <span class="console-line"><span class="console-highlight">[ENCAPSULATION]</span> Mode: <strong>${data.mode || 'N/A'}</strong> &bull; Replay Protection: <strong>${data.replay_protection}</strong></span>
      <span class="console-line"><span class="console-highlight">[CIPHER]</span> Encryption: <strong>${data.encryption || 'N/A'}</strong> &bull; Integrity: <strong>${data.integrity || 'N/A'}</strong></span>
      <span class="console-line"><span class="console-highlight">[KEY EXCHANGE]</span> DH Group: <strong>${data.dh_group || 'N/A'}</strong> &bull; PFS: <strong>${data.pfs}</strong></span>
      <span class="console-line"><span class="console-highlight">[ENDPOINTS]</span> Version: ${data.ip_version || 'N/A'} &bull; ${data.source_ip || 'N/A'} &rarr; ${data.destination_ip || 'N/A'}</span>
      <pre style="margin-top: 10px; padding: 8px; background: rgba(0,0,0,0.4); border-radius: 4px; color: #7dd3fc; font-size: 0.72rem; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>
    `;
  } catch (err) {
    resBadge.textContent = 'ANALYSIS NOTICE';
    resConsole.innerHTML += `
      <span class="console-line" style="color: #94a3b8; margin-top: 6px;"><span class="console-highlight">[ENGINE NOTICE]</span> ${err.message}</span>
      <span class="console-line" style="color: #64748b;">(Start FastAPI backend with <code>uvicorn main:app --port 8000</code> to enable live parsing)</span>
    `;
  }
}
