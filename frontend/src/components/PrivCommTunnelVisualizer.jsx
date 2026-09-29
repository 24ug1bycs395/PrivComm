import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTheme } from '../ThemeContext';
import { 
  Radio, 
  RotateCcw, 
  Play, 
  Pause, 
  AlertTriangle,
  Cpu,
  ShieldCheck
} from 'lucide-react';

/**
 * PrivCommTunnelVisualizer
 * Minimalist, high-fidelity vector blueprint visualization for the PrivComm IPSec VPN tunnel.
 *
 * Core Concept:
 *   - Flared vector blueprint tunnel casing (Sender -> IPSec Tunnel -> Observer -> Receiver)
 *   - Strictly 1 or 2 discrete packets traversing at a time (clean, slow, and observable)
 *   - Zero visual clutter, no bulky cards; pure technical line art and subtle phosphor glows
 */

export function PrivCommTunnelVisualizer({
  height = 360,
  autoPlay = true,
  showControls = true,
  showHeader = true,
  showTelemetry = true,
  onPhaseChange = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // Phases:
  // 1: IKEv2 Handshake Negotiation
  // 2: Tunnel Established Resonance
  // 3: Live ESP Packet Streaming (1 or 2 discrete packets)
  const [phase, setPhase] = useState(3);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [anomalyActive, setAnomalyActive] = useState(false);

  // Inspected packet metadata shown in top header pill
  const [inspectedPacket, setInspectedPacket] = useState({
    spi: '0x8F4C10E4',
    seq: 14320,
    proto: 'ESP',
    cipher: 'AES-256-GCM',
    icv: 'VALID',
  });

  // Animated Telemetry Counters
  const [telemetry, setTelemetry] = useState({
    throughput: 84.4,
    pps: 1420,
    packetCount: 18492,
    icvStatus: '100% VALID',
    latency: '0.38 ms',
    integrityRate: '100.0%',
    observerConfidence: '99.9%',
  });

  // Handshake progression state for Phase 1
  const handshakeRef = useRef({
    step: 0,
    progress: 0,
    active: false,
  });

  const anomalyTriggerRef = useRef(false);

  // Trigger Handshake Sequence
  const triggerHandshake = useCallback(() => {
    setPhase(1);
    handshakeRef.current = { step: 0, progress: 0, active: true };
    if (onPhaseChange) onPhaseChange(1);
  }, [onPhaseChange]);

  // Trigger Anomaly Sequence
  const triggerAnomaly = useCallback(() => {
    anomalyTriggerRef.current = true;
    setAnomalyActive(true);
    setTimeout(() => {
      setAnomalyActive(false);
      anomalyTriggerRef.current = false;
    }, 5000);
  }, []);

  // Live telemetry timer: micro-fluctuates throughput & increments count
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTelemetry((prev) => {
        const ppsDelta = Math.floor((Math.random() - 0.48) * 16);
        const newPps = Math.max(1340, Math.min(1520, prev.pps + ppsDelta));
        const throughputJitter = +(84.1 + Math.random() * 0.9).toFixed(1);
        return {
          ...prev,
          throughput: throughputJitter,
          pps: newPps,
          packetCount: prev.packetCount + Math.floor(newPps / 12),
        };
      });
    }, 150);

    return () => clearInterval(interval);
  }, [isPlaying]);

  // Canvas Animation Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width = 0;
    let heightPx = height;

    const resize = () => {
      if (!canvas.parentElement) return;
      const dpr = window.devicePixelRatio || 1;
      width = canvas.parentElement.clientWidth;
      heightPx = height;
      canvas.width = width * dpr;
      canvas.height = heightPx * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${heightPx}px`;
      ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener('resize', resize);

    // Color definitions
    const colors = {
      bluePrimary: isLight ? '#2563EB' : '#3B82F6',
      blueBright: isLight ? '#1D4ED8' : '#60A5FA',
      cyanAccent: isLight ? '#0284C7' : '#06B6D4',
      tubeWall: isLight ? 'rgba(37, 99, 235, 0.35)' : 'rgba(56, 189, 248, 0.45)',
      tubeWallActive: isLight ? 'rgba(37, 99, 235, 0.75)' : 'rgba(56, 189, 248, 0.85)',
      tubeFill: isLight ? 'rgba(37, 99, 235, 0.03)' : 'rgba(56, 189, 248, 0.04)',
      gridLine: isLight ? 'rgba(37, 99, 235, 0.07)' : 'rgba(56, 189, 248, 0.07)',
      textMuted: isLight ? '#475569' : '#94A3B8',
      textBright: isLight ? '#0F172A' : '#F8FAFC',
      textAccent: isLight ? '#1D4ED8' : '#38BDF8',
      anomalyRed: '#EF4444',
      green: '#10B981',
    };

    // Smooth curved streamline trajectory through the flared tunnel
    const getStreamlinePoint = (trackIdx, t, w, h) => {
      const gunX = w * 0.16;
      const centerY = h * 0.52;
      const targetX = w * 0.82;

      const spreads = [-h * 0.30, -h * 0.15, 0, h * 0.15, h * 0.30];
      const targetY = centerY + spreads[trackIdx];

      const p0 = { x: gunX, y: centerY + (trackIdx - 2) * 4 };
      const p1 = { x: w * 0.32, y: centerY + (trackIdx - 2) * 5 };
      const p2 = { x: w * 0.58, y: centerY + spreads[trackIdx] * 0.45 };
      const p3 = { x: targetX, y: targetY };

      const mt = 1 - t;
      const x = mt * mt * mt * p0.x + 3 * mt * mt * t * p1.x + 3 * mt * t * t * p2.x + t * t * t * p3.x;
      const y = mt * mt * mt * p0.y + 3 * mt * mt * t * p1.y + 3 * mt * t * t * p2.y + t * t * t * p3.y;

      return { x, y };
    };

    // Exactly 2 discrete packets traversing at a time (well-spaced and clear)
    const packets = [
      {
        id: 1,
        track: 2, // Center streamline
        t: 0.15,
        speed: 0.0032, // Slow, elegant, easily observable motion
        history: [],
        seq: 14320,
        isAnomaly: false,
      },
      {
        id: 2,
        track: 2, // Center streamline
        t: 0.65, // Spaced half a cycle apart
        speed: 0.0032,
        history: [],
        seq: 14321,
        isAnomaly: false,
      },
    ];

    const observerRings = [];
    let observerScanAngle = 0;
    let verifiedPulse = 0;
    let lastScanTime = 0;

    const render = (now) => {
      ctx.clearRect(0, 0, width, heightPx);
      const w = width;
      const h = heightPx;
      const centerY = h * 0.52;

      const gunX = w * 0.16;
      const targetX = w * 0.82;
      const observerX = w * 0.49;
      const neckTop = centerY - 28;
      const neckBottom = centerY + 28;
      const screenTop = centerY - h * 0.35;
      const screenBottom = centerY + h * 0.35;

      // ─── 1. Minimal Background Technical Grid ──────────────────────────────
      ctx.save();
      ctx.strokeStyle = colors.gridLine;
      ctx.lineWidth = 1;
      const gridSize = 28;

      for (let x = gridSize; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = gridSize; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Corner Crosshairs
      const drawCrosshair = (cx, cy) => {
        ctx.strokeStyle = colors.tubeWall;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx - 5, cy);
        ctx.lineTo(cx + 5, cy);
        ctx.moveTo(cx, cy - 5);
        ctx.lineTo(cx, cy + 5);
        ctx.stroke();
      };
      drawCrosshair(14, 14);
      drawCrosshair(w - 14, 14);
      drawCrosshair(14, h - 14);
      drawCrosshair(w - 14, h - 14);
      ctx.restore();

      // ─── 2. Flared Vector Tunnel Envelope (The Iconic Blueprint Tunnel) ───
      ctx.save();
      const tunnelActive = phase >= 2;

      ctx.beginPath();
      ctx.moveTo(w * 0.05, neckTop);
      ctx.lineTo(gunX, neckTop);
      ctx.bezierCurveTo(w * 0.34, neckTop, w * 0.54, screenTop + 14, targetX, screenTop);
      ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
      ctx.bezierCurveTo(w * 0.54, screenBottom - 14, w * 0.34, neckBottom, gunX, neckBottom);
      ctx.lineTo(w * 0.05, neckBottom);
      ctx.closePath();

      ctx.fillStyle = tunnelActive ? colors.tubeFill : 'rgba(0, 0, 0, 0.015)';
      ctx.fill();

      ctx.lineWidth = tunnelActive ? 1.8 : 1.4;
      ctx.strokeStyle = tunnelActive ? colors.tubeWallActive : colors.tubeWall;
      if (tunnelActive) {
        ctx.shadowColor = colors.cyanAccent;
        ctx.shadowBlur = isLight ? 4 : 10;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Acceleration & Deflection Plates (Top & Bottom)
      ctx.lineWidth = 2.2;
      ctx.strokeStyle = colors.bluePrimary;
      // Top Crypto Acceleration Plate
      ctx.beginPath();
      ctx.moveTo(w * 0.28, neckTop - 8);
      ctx.bezierCurveTo(w * 0.35, neckTop - 7, w * 0.42, neckTop - 18, w * 0.46, neckTop - 30);
      ctx.stroke();

      // Bottom Deflecting Coils (DH-19)
      ctx.beginPath();
      ctx.moveTo(w * 0.28, neckBottom + 8);
      ctx.bezierCurveTo(w * 0.35, neckBottom + 7, w * 0.42, neckBottom + 18, w * 0.46, neckBottom + 30);
      ctx.stroke();

      // Electrostatic field dashes between plates
      ctx.setLineDash([3, 4]);
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.18)' : 'rgba(56, 189, 248, 0.2)';
      for (let fx = w * 0.30; fx < w * 0.44; fx += 14) {
        ctx.beginPath();
        ctx.moveTo(fx, neckTop - 4);
        ctx.lineTo(fx, neckBottom + 4);
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.restore();

      // ─── 3. Streamline Trajectories (Dotted Transit Guide Lines) ───────────
      ctx.save();
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.16)' : 'rgba(56, 189, 248, 0.16)';
      ctx.setLineDash([4, 6]);

      for (let tIdx = 0; tIdx < 5; tIdx++) {
        ctx.beginPath();
        for (let step = 0; step <= 36; step++) {
          const pt = getStreamlinePoint(tIdx, step / 36, w, h);
          if (step === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.restore();

      // ─── 4. Left Node: SENDER GATEWAY (192.168.56.10 / Initiator) ────────
      ctx.save();
      const gunLeft = w * 0.05;
      const gunWidth = gunX - gunLeft;

      ctx.fillStyle = isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.85)';
      ctx.strokeStyle = colors.bluePrimary;
      ctx.lineWidth = 1.8;
      ctx.strokeRect(gunLeft, neckTop, gunWidth, neckBottom - neckTop);
      ctx.fillRect(gunLeft, neckTop, gunWidth, neckBottom - neckTop);

      // Sender internal cathode / crypto grids
      ctx.strokeStyle = colors.cyanAccent;
      ctx.lineWidth = 1.4;
      for (let gx = gunLeft + 8; gx < gunX - 6; gx += 6) {
        ctx.beginPath();
        ctx.moveTo(gx, centerY - 12);
        ctx.lineTo(gx, centerY + 12);
        ctx.stroke();
      }

      // Emitter Core Glow
      const emitterPulse = Math.sin(now * 0.003) * 2 + 5;
      ctx.beginPath();
      ctx.arc(gunX - 10, centerY, emitterPulse, 0, Math.PI * 2);
      ctx.fillStyle = colors.cyanAccent;
      ctx.shadowColor = colors.cyanAccent;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.restore();

      // ─── 5. Right Node: RECEIVER GATEWAY (192.168.56.20 / Target) ─────────
      ctx.save();
      // Thick Lead Glass Backing
      ctx.lineWidth = 6;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.35)' : 'rgba(59, 130, 246, 0.4)';
      ctx.beginPath();
      ctx.moveTo(targetX + 6, screenTop);
      ctx.quadraticCurveTo(targetX + 22, centerY, targetX + 6, screenBottom);
      ctx.stroke();

      // Phosphorescent Active Target Coating
      ctx.lineWidth = 2.8;
      ctx.strokeStyle = colors.cyanAccent;
      ctx.shadowColor = colors.cyanAccent;
      ctx.shadowBlur = isLight ? 6 : 14;
      ctx.beginPath();
      ctx.moveTo(targetX, screenTop);
      ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Small Comb Ticks along the screen
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = colors.blueBright;
      for (let sy = screenTop + 8; sy < screenBottom; sy += 9) {
        ctx.beginPath();
        ctx.moveTo(targetX - 3, sy);
        ctx.lineTo(targetX + 3, sy);
        ctx.stroke();
      }

      // Decrypted Plaintext Egress Rays (Volumetric Light Cone)
      ctx.save();
      const egressGrad = ctx.createLinearGradient(targetX, centerY, w * 0.98, centerY);
      egressGrad.addColorStop(0, isLight ? 'rgba(37, 99, 235, 0.24)' : 'rgba(6, 182, 212, 0.35)');
      egressGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = egressGrad;
      ctx.beginPath();
      ctx.moveTo(targetX + 8, screenTop + 14);
      ctx.lineTo(w * 0.98, screenTop - 10);
      ctx.lineTo(w * 0.98, screenBottom + 10);
      ctx.lineTo(targetX + 8, screenBottom - 14);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
      ctx.restore();

      // ─── 6. Center Node: OBSERVER / SENTINEL (192.168.56.30) ──────────────
      ctx.save();
      const obsY = centerY;
      const obsRadius = 24;

      ctx.lineWidth = 1.6;
      ctx.strokeStyle = anomalyActive ? colors.anomalyRed : colors.bluePrimary;
      ctx.beginPath();
      ctx.arc(observerX, obsY, obsRadius, 0, Math.PI * 2);
      ctx.fillStyle = isLight ? 'rgba(255, 255, 255, 0.92)' : 'rgba(10, 15, 29, 0.92)';
      ctx.fill();
      ctx.stroke();

      // Radar Inspection Sweep
      observerScanAngle += 0.025 * (isPlaying ? 1 : 0);
      const sweepEndX = observerX + Math.cos(observerScanAngle) * obsRadius;
      const sweepEndY = obsY + Math.sin(observerScanAngle) * obsRadius;
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.beginPath();
      ctx.moveTo(observerX, obsY);
      ctx.lineTo(sweepEndX, sweepEndY);
      ctx.stroke();

      // Reticle Crosshairs
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.28)' : 'rgba(56, 189, 248, 0.3)';
      ctx.beginPath();
      ctx.moveTo(observerX - obsRadius - 5, obsY);
      ctx.lineTo(observerX + obsRadius + 5, obsY);
      ctx.moveTo(observerX, obsY - obsRadius - 5);
      ctx.lineTo(observerX, obsY + obsRadius + 5);
      ctx.stroke();

      // Core Pulse
      const corePulse = Math.sin(now * 0.004) * 1.5 + 6;
      ctx.beginPath();
      ctx.arc(observerX, obsY, corePulse, 0, Math.PI * 2);
      ctx.fillStyle = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.shadowColor = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.shadowBlur = anomalyActive ? 14 : 9;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Active Inspection Pulse Rings expanding outwards
      for (let r = observerRings.length - 1; r >= 0; r--) {
        const ring = observerRings[r];
        ring.radius += 0.6 * (isPlaying ? 1 : 0);
        ring.alpha -= 0.015 * (isPlaying ? 1 : 0);

        if (ring.alpha <= 0) {
          observerRings.splice(r, 1);
          continue;
        }

        ctx.lineWidth = 1.2;
        ctx.strokeStyle = ring.isAnomaly
          ? `rgba(239, 68, 68, ${ring.alpha})`
          : isLight
            ? `rgba(37, 99, 235, ${ring.alpha})`
            : `rgba(6, 182, 212, ${ring.alpha})`;
        ctx.beginPath();
        ctx.arc(observerX, obsY, ring.radius, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();

      // ─── 7. Phase 1: IKEv2 SA Handshake (4-Step Negotiation) ───────────────
      if (phase === 1) {
        ctx.save();
        const hs = handshakeRef.current;
        if (isPlaying) {
          hs.progress += 0.004;
          if (hs.progress >= 1.0) {
            hs.progress = 0;
            hs.step = hs.step + 1;
            if (hs.step > 3) {
              setPhase(2);
              verifiedPulse = 1.0;
              setTimeout(() => setPhase(3), 1800);
            }
          }
        }

        const isForward = hs.step % 2 === 0;
        const startX = isForward ? gunX : targetX;
        const endX = isForward ? targetX : gunX;
        const currentPacketX = startX + (endX - startX) * hs.progress;
        const packetY = centerY + Math.sin(hs.progress * Math.PI) * (isForward ? -24 : 24);

        const stepNames = [
          '1. IKE_SA_INIT (HDR, SAi1, KEi, Ni) ➔',
          '◀ 2. IKE_SA_INIT_RESP (HDR, SAr1, KEr, Nr)',
          '3. IKE_AUTH Request (HDR, SK {IDi, AUTH}) ➔',
          '◀ 4. IKE_AUTH Response / CHILD_SA [ESTABLISHED]',
        ];
        const stepColors = [colors.cyanAccent, colors.blueBright, '#F59E0B', '#10B981'];

        ctx.beginPath();
        ctx.arc(currentPacketX, packetY, 6.5, 0, Math.PI * 2);
        ctx.fillStyle = stepColors[hs.step];
        ctx.shadowColor = stepColors[hs.step];
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.font = 'bold 9.5px "JetBrains Mono", monospace';
        ctx.fillStyle = colors.textBright;
        ctx.textAlign = 'center';
        ctx.fillText(stepNames[hs.step], currentPacketX, packetY - 14);

        ctx.lineWidth = 1.2;
        ctx.strokeStyle = stepColors[hs.step];
        ctx.setLineDash([2, 3]);
        ctx.beginPath();
        ctx.moveTo(startX, centerY);
        ctx.quadraticCurveTo((startX + endX) / 2, centerY + (isForward ? -36 : 36), currentPacketX, packetY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
      }

      // ─── 8. Phase 2: Tunnel Established Flash ─────────────────────────────
      if (phase === 2 && verifiedPulse > 0) {
        ctx.save();
        ctx.lineWidth = 3;
        ctx.strokeStyle = `rgba(6, 182, 212, ${verifiedPulse})`;
        ctx.shadowColor = colors.cyanAccent;
        ctx.shadowBlur = 18 * verifiedPulse;

        ctx.beginPath();
        ctx.moveTo(gunX, neckTop);
        ctx.bezierCurveTo(w * 0.34, neckTop, w * 0.54, screenTop + 14, targetX, screenTop);
        ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
        ctx.bezierCurveTo(w * 0.54, screenBottom - 14, w * 0.34, neckBottom, gunX, neckBottom);
        ctx.stroke();

        verifiedPulse -= 0.014;
        ctx.restore();
      }

      // ─── 9. Phase 3: Discrete 1 or 2 Packets in Transit ───────────────────
      if (phase >= 2) {
        ctx.save();

        packets.forEach((p) => {
          if (isPlaying) {
            p.isAnomaly = anomalyTriggerRef.current && p.id === 1;

            p.t += p.speed;
            if (p.t > 1.0) {
              p.t = 0;
              p.seq += 2;

              // Screen impact flash
              ctx.save();
              const impactPt = getStreamlinePoint(p.track, 1.0, w, h);
              ctx.beginPath();
              ctx.arc(targetX, impactPt.y, 5, 0, Math.PI * 2);
              ctx.fillStyle = colors.cyanAccent;
              ctx.shadowColor = colors.cyanAccent;
              ctx.shadowBlur = 12;
              ctx.fill();
              ctx.restore();
            }
          }

          const pos = getStreamlinePoint(p.track, p.t, w, h);

          // Phosphor Fading Tail
          p.history.push({ x: pos.x, y: pos.y });
          if (p.history.length > 12) {
            p.history.shift();
          }

          // Trigger Observer scan when packet crosses center
          if (Math.abs(pos.x - observerX) < 10 && now - lastScanTime > 320) {
            lastScanTime = now;
            observerRings.push({
              radius: obsRadius,
              alpha: 0.95,
              isAnomaly: p.isAnomaly,
            });

            setInspectedPacket({
              spi: p.isAnomaly ? '0xDEADBEEF' : `0x8F4C${(p.seq % 9999).toString(16).toUpperCase()}`,
              seq: p.seq,
              proto: p.isAnomaly ? 'MALFORMED' : 'ESP',
              cipher: 'AES-256-GCM',
              icv: p.isAnomaly ? 'CHECKSUM_FAIL' : 'VALID',
            });
          }

          // Render Phosphor Tail
          if (p.history.length > 1) {
            ctx.beginPath();
            ctx.moveTo(p.history[0].x, p.history[0].y);
            for (let hi = 1; hi < p.history.length; hi++) {
              ctx.lineTo(p.history[hi].x, p.history[hi].y);
            }
            ctx.lineWidth = 2.5;
            const trailAlpha = isLight ? 0.45 : 0.65;
            ctx.strokeStyle = p.isAnomaly
              ? `rgba(239, 68, 68, ${trailAlpha})`
              : `rgba(6, 182, 212, ${trailAlpha})`;
            ctx.stroke();
          }

          // Render Sleek Minimal Cyber Packet Capsule
          const capW = 46;
          const capH = 18;
          const capX = pos.x - capW * 0.5;
          const capY = pos.y - capH * 0.5;

          ctx.fillStyle = p.isAnomaly
            ? 'rgba(239, 68, 68, 0.92)'
            : isLight ? 'rgba(37, 99, 235, 0.92)' : 'rgba(2, 132, 199, 0.92)';
          ctx.strokeStyle = p.isAnomaly ? '#EF4444' : colors.cyanAccent;
          ctx.lineWidth = 1.4;
          ctx.shadowColor = p.isAnomaly ? '#EF4444' : colors.cyanAccent;
          ctx.shadowBlur = 10;

          ctx.beginPath();
          ctx.roundRect(capX, capY, capW, capH, 4);
          ctx.fill();
          ctx.stroke();
          ctx.shadowBlur = 0;

          // Packet Capsule Text
          ctx.font = 'bold 8px "JetBrains Mono", monospace';
          ctx.fillStyle = '#FFFFFF';
          ctx.textAlign = 'center';
          ctx.fillText(p.isAnomaly ? 'BAD ICV' : 'ESP #' + (p.seq % 9999), pos.x, pos.y + 3);

          // Mini Data Tag
          ctx.font = '7.5px "JetBrains Mono", monospace';
          ctx.fillStyle = p.isAnomaly ? colors.anomalyRed : colors.textAccent;
          ctx.fillText(p.isAnomaly ? '0xDEADBEEF' : 'AES-GCM', pos.x, capY - 5);
        });

        ctx.restore();
      }

      // ─── 10. Minimalist Technical Blueprint Labels (No Overlapping Boxes) ──
      ctx.save();
      const drawLeader = (text, lx, ly, targetPt, align = 'center') => {
        ctx.font = 'bold 9px "JetBrains Mono", monospace';
        ctx.fillStyle = isLight ? '#1D4ED8' : '#38BDF8';
        ctx.textAlign = align;
        ctx.fillText(text, lx, ly);

        ctx.lineWidth = 1;
        ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.45)' : 'rgba(56, 189, 248, 0.45)';
        ctx.beginPath();
        ctx.moveTo(lx, ly + 3);
        ctx.lineTo(targetPt.x, targetPt.y);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(targetPt.x, targetPt.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = colors.cyanAccent;
        ctx.fill();
      };

      // Clean, minimal callouts positioned with plenty of breathing room
      drawLeader('SENDER GATEWAY', gunX - 10, neckTop - 20, { x: gunX - 10, y: neckTop });
      drawLeader('AES-256-GCM / ESP', w * 0.32, neckBottom + 42, { x: w * 0.32, y: neckBottom + 16 });
      drawLeader('IPSEC ENCRYPTED TUNNEL', w * 0.59, screenTop - 16, { x: w * 0.59, y: screenTop + 4 });
      drawLeader('RECEIVER GATEWAY', targetX, screenTop - 18, { x: targetX, y: screenTop });
      drawLeader('PLAINTEXT EGRESS', w * 0.94, centerY + 32, { x: targetX + 16, y: centerY });

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isLight, height, phase, isPlaying, anomalyActive]);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        borderRadius: 'var(--radius-lg, 12px)',
        background: isLight ? '#F0F6FD' : '#080E1E',
        overflow: 'hidden',
        border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
        fontFamily: 'var(--font-mono, "JetBrains Mono", monospace)',
      }}
    >
      {/* ─── Minimal Header Ribbon ─────────────────────────────────────────── */}
      {showHeader && <div
        style={{
          padding: '10px 16px',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '10px',
          borderBottom: '1px solid var(--border-blueprint, rgba(37,99,235,0.2))',
          background: isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.88)',
        }}
      >
        {/* Left: Clean Title & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '6px',
              background: isLight ? 'rgba(37,99,235,0.08)' : 'rgba(56,189,248,0.12)',
              border: '1px solid var(--border-blueprint, rgba(37,99,235,0.3))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isLight ? '#2563EB' : '#38BDF8',
            }}
          >
            <Radio size={13} className={isPlaying ? 'animate-pulse' : ''} />
          </div>
          <span
            style={{
              fontSize: '0.76rem',
              fontWeight: 700,
              color: isLight ? '#0F172A' : '#F8FAFC',
              letterSpacing: '0.04em',
            }}
          >
            PRIVCOMM SECURE TUNNEL MESH
          </span>
          <span
            style={{
              fontSize: '0.62rem',
              padding: '2px 7px',
              borderRadius: '4px',
              fontWeight: 700,
              background: anomalyActive
                ? 'rgba(239, 68, 68, 0.15)'
                : phase === 1
                  ? 'rgba(245, 158, 11, 0.15)'
                  : 'rgba(16, 185, 129, 0.15)',
              color: anomalyActive
                ? '#EF4444'
                : phase === 1
                  ? '#F59E0B'
                  : '#10B981',
            }}
          >
            {anomalyActive
              ? 'ANOMALY DETECTED // ISOLATING'
              : phase === 1
                ? 'IKEv2 HANDSHAKE'
                : 'TUNNEL ESTABLISHED'}
          </span>
        </div>

        {/* Center / Right: Live Inspection Pill & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          {/* Integrated Inspection Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.64rem',
              background: isLight ? 'rgba(37,99,235,0.06)' : 'rgba(30, 41, 59, 0.7)',
              border: '1px solid var(--border-blueprint, rgba(37,99,235,0.2))',
              color: isLight ? '#475569' : '#94A3B8',
            }}
          >
            <Cpu size={12} color={anomalyActive ? '#EF4444' : isLight ? '#2563EB' : '#38BDF8'} />
            <span>INSPECT:</span>
            <strong style={{ color: isLight ? '#2563EB' : '#60A5FA' }}>{inspectedPacket.spi}</strong>
            <span>SEQ #{inspectedPacket.seq}</span>
            <strong style={{ color: anomalyActive ? '#EF4444' : '#10B981' }}>
              {anomalyActive ? 'DROPPED' : inspectedPacket.icv}
            </strong>
          </div>

          {/* Action Buttons */}
          {showControls && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {/* Play / Pause Toggle */}
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                title={isPlaying ? 'Pause Simulation' : 'Resume Simulation'}
                style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: '1px solid rgba(37,99,235,0.2)',
                  color: isLight ? '#1E293B' : '#F8FAFC',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                {isPlaying ? <Pause size={11} /> : <Play size={11} />}
                <span>{isPlaying ? 'PAUSE' : 'RESUME'}</span>
              </button>

              {/* Handshake Trigger */}
              <button
                type="button"
                onClick={triggerHandshake}
                title="Restart IKEv2 / CHILD_SA Handshake"
                style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: '1px solid rgba(37,99,235,0.2)',
                  color: isLight ? '#2563EB' : '#38BDF8',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <RotateCcw size={11} />
                <span>HANDSHAKE</span>
              </button>

              {/* Inject Anomaly Trigger */}
              <button
                type="button"
                onClick={triggerAnomaly}
                disabled={anomalyActive}
                title="Simulate Malformed / Replayed ESP Packet"
                style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: anomalyActive
                    ? 'rgba(239,68,68,0.2)'
                    : isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: anomalyActive
                    ? '1px solid #EF4444'
                    : '1px solid rgba(37,99,235,0.2)',
                  color: anomalyActive ? '#EF4444' : isLight ? '#D97706' : '#FBBF24',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: anomalyActive ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <AlertTriangle size={11} />
                <span>INJECT ANOMALY</span>
              </button>
            </div>
          )}
        </div>
      </div>}

      {/* ─── 60 FPS HTML5 Canvas Viewport ──────────────────────────────────── */}
      <div style={{ position: 'relative', width: '100%', height: `${height}px` }}>
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            display: 'block',
          }}
        />
      </div>

      {/* ─── Bottom Live Telemetry Metrics Strip ───────────────────────────── */}
      {showTelemetry && <div
        style={{
          padding: '8px 16px',
          background: isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.95)',
          borderTop: '1px solid var(--border-blueprint, rgba(37,99,235,0.2))',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
          fontSize: '0.68rem',
        }}
      >
        <div>
          <span style={{ display: 'block', fontSize: '0.58rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            ESP FLOW THROUGHPUT
          </span>
          <strong style={{ color: isLight ? '#2563EB' : '#38BDF8', fontSize: '0.82rem' }}>
            {telemetry.throughput} Mbps
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.58rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            PACKET AUDIT RATE
          </span>
          <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC', fontSize: '0.82rem' }}>
            {telemetry.pps.toLocaleString()} pps
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.58rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            PACKET SCAN TALLY
          </span>
          <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC', fontSize: '0.82rem' }}>
            {telemetry.packetCount.toLocaleString()} pkts
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.58rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            ICV AUTH INTEGRITY
          </span>
          <strong style={{ color: anomalyActive ? '#EF4444' : '#10B981', fontSize: '0.82rem' }}>
            {anomalyActive ? '99.84% (ISOLATING)' : telemetry.integrityRate}
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.58rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            SESSION LATENCY
          </span>
          <strong style={{ color: isLight ? '#2563EB' : '#38BDF8', fontSize: '0.82rem' }}>
            {telemetry.latency}
          </strong>
        </div>
      </div>}
    </div>
  );
}

export default PrivCommTunnelVisualizer;
