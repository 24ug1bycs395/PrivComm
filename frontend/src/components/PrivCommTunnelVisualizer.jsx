import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTheme } from '../ThemeContext';
import { 
  Radio, 
  RotateCcw, 
  Play, 
  Pause, 
  AlertTriangle,
  Cpu
} from 'lucide-react';

/**
 * PrivCommTunnelVisualizer
 * High-fidelity, minimalistic animated network visualization inspired by the CRT
 * electron-beam laboratory schematic style for IPSec VPN security architecture.
 *
 * Visual aesthetics:
 *   - Soft glowing particles with long fading phosphor trails
 *   - Relaxed, graceful, slow scientific electron flow (~18s full traverse)
 *   - Clean vector blueprint graphics without overlapping HUD boxes
 *   - Interactive controls: Pause/Resume, Handshake replay, Anomaly simulation
 */

export function PrivCommTunnelVisualizer({
  height = 360,
  autoPlay = true,
  showControls = true,
  onPhaseChange = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // Phases:
  // 1: TUNNEL_ESTABLISHMENT (IKEv2 Handshake)
  // 2: TUNNEL_VERIFIED (Lock-in & Resonance Surge)
  // 3: LIVE_TRAFFIC_FLOW (Continuous CRT Electron-beam ESP Stream)
  const [phase, setPhase] = useState(3); 
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [anomalyActive, setAnomalyActive] = useState(false);
  const [inspectedPacket, setInspectedPacket] = useState({
    spi: '0x8F4C10E4',
    seq: 14323,
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
  });

  // Handshake progression state for Phase 1
  const handshakeRef = useRef({
    step: 0,
    progress: 0,
    active: false,
  });

  // Anomaly trigger state
  const anomalyTriggerRef = useRef(false);

  // Trigger Handshake Sequence (Phase 1 -> Phase 2 -> Phase 3)
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
    }, 4500);
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

  // Canvas Animation Engine (Silky 60 FPS CRT Electron Simulation with Slow, Graceful Flow)
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

    // Color definitions based on active theme
    const colors = {
      bluePrimary: isLight ? '#2563EB' : '#3B82F6',
      blueBright: isLight ? '#1D4ED8' : '#60A5FA',
      cyanAccent: isLight ? '#0284C7' : '#06B6D4',
      tubeWall: isLight ? 'rgba(37, 99, 235, 0.28)' : 'rgba(59, 130, 246, 0.35)',
      gridLine: isLight ? 'rgba(37, 99, 235, 0.08)' : 'rgba(56, 189, 248, 0.07)',
      textMuted: isLight ? '#475569' : '#94A3B8',
      textBright: isLight ? '#0F172A' : '#F8FAFC',
      anomalyRed: '#EF4444',
    };

    // CRT Electron Streamlines (5 smooth curved trajectories from gun neck to flared target)
    const getStreamlinePoint = (trackIdx, t, w, h) => {
      const gunX = w * 0.16;
      const centerY = h * 0.5;
      const targetX = w * 0.84;

      const spreads = [-h * 0.34, -h * 0.17, 0, h * 0.17, h * 0.34];
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

    // Spaced particles with slow, elegant velocity (~18 seconds per full traverse)
    const particleCount = 26;
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        track: i % 5,
        t: (i / particleCount) + Math.random() * 0.02, // Well-spaced progression
        // Slow and relaxed motion speed:
        speed: 0.00065 + Math.random() * 0.00035,
        size: 1.8 + Math.random() * 1.8,
        history: [], // Stores previous positions for fading phosphor trail
        isCipherBlock: i % 5 === 0,
        seq: 14000 + i * 47,
        isAnomaly: false,
      });
    }

    const observerRings = [];
    let observerScanAngle = 0;
    let verifiedPulse = 0;
    let lastScanTime = 0;

    let lastTimestamp = performance.now();

    const render = (now) => {
      lastTimestamp = now;

      ctx.clearRect(0, 0, width, heightPx);
      const w = width;
      const h = heightPx;
      const centerY = h * 0.5;

      const gunX = w * 0.16;
      const targetX = w * 0.84;
      const observerX = w * 0.50;
      const neckTop = centerY - 32;
      const neckBottom = centerY + 32;
      const screenTop = centerY - h * 0.38;
      const screenBottom = centerY + h * 0.38;

      // ─── 1. Background Technical Grid & Caliper Alignment Marks ───────────
      ctx.save();
      ctx.strokeStyle = colors.gridLine;
      ctx.lineWidth = 1;
      const gridSize = 32;

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

      // Corner Alignment Crosshairs
      const drawCrosshair = (cx, cy) => {
        ctx.strokeStyle = colors.tubeWall;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cx - 6, cy);
        ctx.lineTo(cx + 6, cy);
        ctx.moveTo(cx, cy - 6);
        ctx.lineTo(cx, cy + 6);
        ctx.stroke();
      };
      drawCrosshair(16, 16);
      drawCrosshair(w - 16, 16);
      drawCrosshair(16, h - 16);
      drawCrosshair(w - 16, h - 16);
      ctx.restore();

      // ─── 2. CRT Vacuum Tube Envelope (IPSec Tunnel Casing) ─────────────────
      ctx.save();
      const tunnelActive = phase >= 2;

      ctx.beginPath();
      ctx.moveTo(w * 0.04, neckTop);
      ctx.lineTo(gunX, neckTop);
      ctx.bezierCurveTo(w * 0.34, neckTop, w * 0.56, screenTop + 14, targetX, screenTop);
      ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
      ctx.bezierCurveTo(w * 0.56, screenBottom - 14, w * 0.34, neckBottom, gunX, neckBottom);
      ctx.lineTo(w * 0.04, neckBottom);
      ctx.closePath();

      ctx.fillStyle = tunnelActive
        ? isLight ? 'rgba(37, 99, 235, 0.035)' : 'rgba(59, 130, 246, 0.05)'
        : 'rgba(0, 0, 0, 0.02)';
      ctx.fill();

      ctx.lineWidth = tunnelActive ? 2 : 1.5;
      ctx.strokeStyle = tunnelActive
        ? isLight ? 'rgba(37, 99, 235, 0.75)' : 'rgba(56, 189, 248, 0.8)'
        : colors.tubeWall;
      if (tunnelActive) {
        ctx.shadowColor = colors.cyanAccent;
        ctx.shadowBlur = isLight ? 6 : 14;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Anode & Deflection Plates (Top & Bottom)
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = colors.bluePrimary;
      // Top Acceleration Anode
      ctx.beginPath();
      ctx.moveTo(w * 0.30, neckTop - 8);
      ctx.bezierCurveTo(w * 0.37, neckTop - 7, w * 0.44, neckTop - 22, w * 0.48, neckTop - 36);
      ctx.stroke();

      // Bottom Deflecting Magnet
      ctx.beginPath();
      ctx.moveTo(w * 0.30, neckBottom + 8);
      ctx.bezierCurveTo(w * 0.37, neckBottom + 7, w * 0.44, neckBottom + 22, w * 0.48, neckBottom + 36);
      ctx.stroke();

      // Electrostatic field dashes between plates
      ctx.setLineDash([3, 4]);
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.22)' : 'rgba(56, 189, 248, 0.22)';
      for (let fx = w * 0.32; fx < w * 0.46; fx += 14) {
        ctx.beginPath();
        ctx.moveTo(fx, neckTop - 4);
        ctx.lineTo(fx, neckBottom + 4);
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.restore();

      // ─── 3. Streamline Trajectories (Dotted Beam Flow Lines) ───────────────
      ctx.save();
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.20)' : 'rgba(56, 189, 248, 0.20)';
      ctx.setLineDash([4, 6]);

      for (let tIdx = 0; tIdx < 5; tIdx++) {
        ctx.beginPath();
        for (let step = 0; step <= 40; step++) {
          const pt = getStreamlinePoint(tIdx, step / 40, w, h);
          if (step === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.restore();

      // ─── 4. Left Node: SENDER GATEWAY (Electron Gun / Initiator) ───────────
      ctx.save();
      const gunLeft = w * 0.04;
      const gunWidth = gunX - gunLeft;

      ctx.fillStyle = isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.85)';
      ctx.strokeStyle = colors.bluePrimary;
      ctx.lineWidth = 2;
      ctx.strokeRect(gunLeft, neckTop, gunWidth, neckBottom - neckTop);
      ctx.fillRect(gunLeft, neckTop, gunWidth, neckBottom - neckTop);

      // Gun Cathode Filament Grids
      ctx.strokeStyle = colors.cyanAccent;
      ctx.lineWidth = 1.5;
      for (let gx = gunLeft + 8; gx < gunX - 6; gx += 7) {
        ctx.beginPath();
        ctx.moveTo(gx, centerY - 14);
        ctx.lineTo(gx, centerY + 14);
        ctx.stroke();
      }

      // Emitter Core Glow
      const emitterPulse = Math.sin(now * 0.003) * 2.5 + 5.5;
      ctx.beginPath();
      ctx.arc(gunX - 10, centerY, emitterPulse, 0, Math.PI * 2);
      ctx.fillStyle = colors.cyanAccent;
      ctx.shadowColor = colors.cyanAccent;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.restore();

      // ─── 5. Right Node: RECEIVER GATEWAY (Phosphorescent Target Screen) ────
      ctx.save();
      // Lead Glass Backing
      ctx.lineWidth = 6;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.35)' : 'rgba(59, 130, 246, 0.4)';
      ctx.beginPath();
      ctx.moveTo(targetX + 6, screenTop);
      ctx.quadraticCurveTo(targetX + 22, centerY, targetX + 6, screenBottom);
      ctx.stroke();

      // Phosphorescent Active Target Coating
      ctx.lineWidth = 3;
      ctx.strokeStyle = colors.cyanAccent;
      ctx.shadowColor = colors.cyanAccent;
      ctx.shadowBlur = isLight ? 8 : 16;
      ctx.beginPath();
      ctx.moveTo(targetX, screenTop);
      ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Small Comb Ticks along the screen
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = isLight ? '#2563EB' : '#60A5FA';
      for (let sy = screenTop + 6; sy < screenBottom; sy += 10) {
        ctx.beginPath();
        ctx.moveTo(targetX - 4, sy);
        ctx.lineTo(targetX + 4, sy);
        ctx.stroke();
      }

      // Light Projection / Decrypted Plaintext Egress Rays
      ctx.save();
      const egressGrad = ctx.createLinearGradient(targetX, centerY, w * 0.98, centerY);
      egressGrad.addColorStop(0, isLight ? 'rgba(37, 99, 235, 0.28)' : 'rgba(6, 182, 212, 0.4)');
      egressGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = egressGrad;
      ctx.beginPath();
      ctx.moveTo(targetX + 8, screenTop + 16);
      ctx.lineTo(w * 0.98, screenTop - 12);
      ctx.lineTo(w * 0.98, screenBottom + 12);
      ctx.lineTo(targetX + 8, screenBottom - 16);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
      ctx.restore();

      // ─── 6. Center Node: SENTINEL CORE (Observer & Packet Inspector) ───────
      ctx.save();
      const obsY = centerY;
      const obsRadius = 24;

      ctx.lineWidth = 1.5;
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
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.beginPath();
      ctx.moveTo(observerX, obsY);
      ctx.lineTo(sweepEndX, sweepEndY);
      ctx.stroke();

      // Reticle Crosshairs
      ctx.lineWidth = 1;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.3)' : 'rgba(56, 189, 248, 0.35)';
      ctx.beginPath();
      ctx.moveTo(observerX - obsRadius - 6, obsY);
      ctx.lineTo(observerX + obsRadius + 6, obsY);
      ctx.moveTo(observerX, obsY - obsRadius - 6);
      ctx.lineTo(observerX, obsY + obsRadius + 6);
      ctx.stroke();

      // Core Pulse
      const corePulse = Math.sin(now * 0.004) * 1.5 + 6.5;
      ctx.beginPath();
      ctx.arc(observerX, obsY, corePulse, 0, Math.PI * 2);
      ctx.fillStyle = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.shadowColor = anomalyActive ? colors.anomalyRed : colors.cyanAccent;
      ctx.shadowBlur = anomalyActive ? 16 : 10;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Active Inspection Pulse Rings expanding outwards
      for (let r = observerRings.length - 1; r >= 0; r--) {
        const ring = observerRings[r];
        ring.radius += 0.5 * (isPlaying ? 1 : 0);
        ring.alpha -= 0.012 * (isPlaying ? 1 : 0);

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

      // ─── 7. Phase 1: Slow Handshake Flow (IKE_SA_INIT / IKE_AUTH) ─────────
      if (phase === 1) {
        ctx.save();
        const hs = handshakeRef.current;
        if (isPlaying) {
          hs.progress += 0.0028; // Slow and readable
          if (hs.progress >= 1.0) {
            hs.progress = 0;
            hs.step = (hs.step + 1);
            if (hs.step > 3) {
              setPhase(2);
              verifiedPulse = 1.0;
              setTimeout(() => setPhase(3), 2000);
            }
          }
        }

        const isForward = hs.step % 2 === 0;
        const startX = isForward ? gunX : targetX;
        const endX = isForward ? targetX : gunX;
        const currentPacketX = startX + (endX - startX) * hs.progress;
        const packetY = centerY + Math.sin(hs.progress * Math.PI) * (isForward ? -25 : 25);

        const stepNames = [
          'IKE_SA_INIT (HDR, SAi1, KEi, Ni)',
          'IKE_SA_INIT_RESP (HDR, SAr1, KEr, Nr)',
          'IKE_AUTH (HDR, SK {IDi, AUTH})',
          'CHILD_SA ESTABLISHED (HDR, SK {IDr, AUTH})',
        ];
        const stepColors = [colors.cyanAccent, colors.blueBright, '#F59E0B', '#10B981'];

        ctx.beginPath();
        ctx.arc(currentPacketX, packetY, 7, 0, Math.PI * 2);
        ctx.fillStyle = stepColors[hs.step];
        ctx.shadowColor = stepColors[hs.step];
        ctx.shadowBlur = 14;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.font = 'bold 10px JetBrains Mono, monospace';
        ctx.fillStyle = colors.textBright;
        ctx.textAlign = 'center';
        ctx.fillText(stepNames[hs.step], currentPacketX, packetY - 14);

        ctx.lineWidth = 1.5;
        ctx.strokeStyle = stepColors[hs.step];
        ctx.setLineDash([2, 3]);
        ctx.beginPath();
        ctx.moveTo(startX, centerY);
        ctx.quadraticCurveTo((startX + endX) / 2, centerY + (isForward ? -40 : 40), currentPacketX, packetY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
      }

      // ─── 8. Phase 2: Tunnel Verified Harmonic Flash ────────────────────────
      if (phase === 2 && verifiedPulse > 0) {
        ctx.save();
        ctx.lineWidth = 3.5;
        ctx.strokeStyle = `rgba(6, 182, 212, ${verifiedPulse})`;
        ctx.shadowColor = colors.cyanAccent;
        ctx.shadowBlur = 20 * verifiedPulse;

        ctx.beginPath();
        ctx.moveTo(gunX, neckTop);
        ctx.bezierCurveTo(w * 0.34, neckTop, w * 0.56, screenTop + 14, targetX, screenTop);
        ctx.quadraticCurveTo(targetX + 16, centerY, targetX, screenBottom);
        ctx.bezierCurveTo(w * 0.56, screenBottom - 14, w * 0.34, neckBottom, gunX, neckBottom);
        ctx.stroke();

        verifiedPulse -= 0.012;
        ctx.restore();
      }

      // ─── 9. Phase 3: Relaxed, Slow CRT Electron-Beam Flow ───────────────────
      if (phase >= 2) {
        ctx.save();
        particles.forEach((p, idx) => {
          if (isPlaying) {
            if (anomalyTriggerRef.current && idx === 8) {
              p.isAnomaly = true;
            } else {
              p.isAnomaly = false;
            }

            // Gentle acceleration through deflection region
            const accel = p.t > 0.15 && p.t < 0.6 ? 1.15 : 1.0;
            p.t += p.speed * accel;

            if (p.t > 1.0) {
              p.t = 0;
              p.seq += 85;
              // Screen impact flash
              ctx.save();
              const impactY = getStreamlinePoint(p.track, 1.0, w, h).y;
              ctx.beginPath();
              ctx.arc(targetX, impactY, 4, 0, Math.PI * 2);
              ctx.fillStyle = colors.cyanAccent;
              ctx.shadowColor = colors.cyanAccent;
              ctx.shadowBlur = 10;
              ctx.fill();
              ctx.restore();
            }
          }

          const pos = getStreamlinePoint(p.track, p.t, w, h);

          // Long, smooth phosphor fading trail
          p.history.push({ x: pos.x, y: pos.y });
          if (p.history.length > 14) {
            p.history.shift();
          }

          // Observer scan when packet crosses center
          if (Math.abs(pos.x - observerX) < 10 && now - lastScanTime > 320) {
            lastScanTime = now;
            observerRings.push({
              radius: obsRadius,
              alpha: 0.9,
              isAnomaly: p.isAnomaly,
            });

            if (p.isCipherBlock || p.isAnomaly) {
              setInspectedPacket({
                spi: p.isAnomaly ? '0xDEADBEEF' : `0x8F4C${(p.seq % 9999).toString(16).toUpperCase()}`,
                seq: p.seq,
                proto: p.isAnomaly ? 'MALFORMED' : 'ESP',
                cipher: 'AES-256-GCM',
                icv: p.isAnomaly ? 'CHECKSUM_FAIL' : 'VALID',
              });
            }
          }

          // Render Phosphor Fading Tail
          if (p.history.length > 1) {
            ctx.beginPath();
            ctx.moveTo(p.history[0].x, p.history[0].y);
            for (let hi = 1; hi < p.history.length; hi++) {
              ctx.lineTo(p.history[hi].x, p.history[hi].y);
            }
            ctx.lineWidth = p.size;
            const trailAlpha = isLight ? 0.32 : 0.55;
            ctx.strokeStyle = p.isAnomaly
              ? `rgba(239, 68, 68, ${trailAlpha})`
              : p.track === 2
                ? `rgba(6, 182, 212, ${trailAlpha})`
                : `rgba(59, 130, 246, ${trailAlpha * 0.8})`;
            ctx.stroke();
          }

          // Render Particle Head / Cipher Block
          ctx.beginPath();
          if (p.isCipherBlock) {
            ctx.rect(pos.x - 5, pos.y - 4, 10, 8);
            ctx.fillStyle = p.isAnomaly ? colors.anomalyRed : colors.blueBright;
            ctx.shadowColor = p.isAnomaly ? colors.anomalyRed : colors.cyanAccent;
            ctx.shadowBlur = isLight ? 6 : 12;
            ctx.fill();
            ctx.shadowBlur = 0;
          } else {
            ctx.arc(pos.x, pos.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.isAnomaly
              ? colors.anomalyRed
              : p.track === 2 ? '#E0F2FE' : colors.cyanAccent;
            ctx.shadowColor = p.isAnomaly ? colors.anomalyRed : colors.cyanAccent;
            ctx.shadowBlur = isLight ? 4 : 10;
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        });
        ctx.restore();
      }

      // ─── 10. Blueprint Technical Labels & Leader Lines (Reference Schematic Style) ─
      ctx.save();
      const drawLeader = (text, lx, ly, targetPt, align = 'center') => {
        ctx.font = 'bold 9px JetBrains Mono, monospace';
        ctx.fillStyle = isLight ? '#1D4ED8' : '#38BDF8';
        ctx.textAlign = align;
        ctx.fillText(text, lx, ly);

        ctx.lineWidth = 1;
        ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.4)' : 'rgba(56, 189, 248, 0.4)';
        ctx.beginPath();
        ctx.moveTo(lx, ly + 4);
        ctx.lineTo(targetPt.x, targetPt.y);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(targetPt.x, targetPt.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = colors.cyanAccent;
        ctx.fill();
      };

      // Callouts matching the scientific blueprint
      drawLeader('SENDER GATEWAY // ALPHA (192.168.56.10)', gunX - 12, neckTop - 24, { x: gunX - 12, y: neckTop });
      drawLeader('CRYPTO ACCELERATION PLATES', w * 0.38, neckTop - 30, { x: w * 0.38, y: neckTop - 12 });
      drawLeader('DEFLECTING COILS (DH-19)', w * 0.38, neckBottom + 36, { x: w * 0.38, y: neckBottom + 12 });
      drawLeader('SENTINEL CORE (192.168.56.30)', observerX, neckTop - 24, { x: observerX, y: obsY - obsRadius });
      drawLeader('ESP ENCRYPTED TRAFFIC STREAM', w * 0.60, screenTop + 10, { x: w * 0.60, y: centerY - 28 });
      drawLeader('INGRESS VERIFICATION TARGET', targetX, screenTop - 20, { x: targetX, y: screenTop });
      drawLeader('DECRYPTED PLAINTEXT EGRESS', w * 0.94, centerY + 36, { x: targetX + 18, y: centerY });
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
        background: isLight ? '#F8FAFD' : '#090D1A',
        overflow: 'hidden',
        fontFamily: 'var(--font-mono, JetBrains Mono, monospace)',
      }}
    >
      {/* ─── Clean Header Bar ─────────────────────────────────────────────── */}
      <div
        style={{
          padding: '12px 18px',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1px solid var(--border-blueprint, rgba(37,99,235,0.2))',
          background: isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.9)',
        }}
      >
        {/* Left: Clean Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '6px',
              background: isLight ? 'rgba(37,99,235,0.08)' : 'rgba(56,189,248,0.12)',
              border: '1px solid var(--border-blueprint, rgba(37,99,235,0.3))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isLight ? '#2563EB' : '#38BDF8',
            }}
          >
            <Radio size={15} className={isPlaying ? 'animate-pulse' : ''} />
          </div>
          <span
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: isLight ? '#0F172A' : '#F8FAFC',
              letterSpacing: '0.04em',
            }}
          >
            PRIVCOMM SECURE TUNNEL MESH
          </span>
        </div>

        {/* Center / Right: Status, Live Inspection, and Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          {/* Status Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '20px',
              fontSize: '0.67rem',
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
              border: `1px solid ${
                anomalyActive
                  ? 'rgba(239, 68, 68, 0.35)'
                  : phase === 1
                    ? 'rgba(245, 158, 11, 0.35)'
                    : 'rgba(16, 185, 129, 0.35)'
              }`,
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: 'currentColor',
                boxShadow: '0 0 8px currentColor',
              }}
            />
            {anomalyActive
              ? 'ANOMALY DETECTED // ISOLATING'
              : phase === 1
                ? 'IKEv2 HANDSHAKE'
                : 'SECURE TUNNEL ESTABLISHED'}
          </div>

          {/* Integrated Inspection Data Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.64rem',
              background: isLight ? 'rgba(37,99,235,0.06)' : 'rgba(30, 41, 59, 0.6)',
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

          {/* Controls */}
          {showControls && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {/* Play / Pause Toggle */}
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                title={isPlaying ? 'Pause Simulation' : 'Resume Simulation'}
                style={{
                  padding: '5px 10px',
                  borderRadius: '6px',
                  background: isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
                  color: isLight ? '#1E293B' : '#F8FAFC',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  transition: 'all 0.2s ease',
                }}
              >
                {isPlaying ? <Pause size={12} /> : <Play size={12} />}
                <span>{isPlaying ? 'PAUSE' : 'RESUME'}</span>
              </button>

              {/* Handshake Trigger */}
              <button
                type="button"
                onClick={triggerHandshake}
                title="Restart IKEv2 / CHILD_SA Handshake"
                style={{
                  padding: '5px 10px',
                  borderRadius: '6px',
                  background: isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
                  color: isLight ? '#2563EB' : '#38BDF8',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  transition: 'all 0.2s ease',
                }}
              >
                <RotateCcw size={12} />
                <span>HANDSHAKE</span>
              </button>

              {/* Inject Anomaly Trigger */}
              <button
                type="button"
                onClick={triggerAnomaly}
                disabled={anomalyActive}
                title="Simulate Malformed / Replayed ESP Packet"
                style={{
                  padding: '5px 10px',
                  borderRadius: '6px',
                  background: anomalyActive
                    ? 'rgba(239,68,68,0.2)'
                    : isLight ? '#FFFFFF' : 'rgba(30, 41, 59, 0.7)',
                  border: anomalyActive
                    ? '1px solid #EF4444'
                    : '1px solid var(--border-blueprint, rgba(37,99,235,0.25))',
                  color: anomalyActive ? '#EF4444' : isLight ? '#D97706' : '#FBBF24',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: anomalyActive ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  transition: 'all 0.2s ease',
                }}
              >
                <AlertTriangle size={12} />
                <span>INJECT ANOMALY</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ─── Unobstructed 60 FPS HTML5 Canvas Viewport ─────────────────────── */}
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
      <div
        style={{
          padding: '10px 18px',
          background: isLight ? '#FFFFFF' : 'rgba(15, 23, 42, 0.95)',
          borderTop: '1px solid var(--border-blueprint, rgba(37,99,235,0.2))',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
          fontSize: '0.7rem',
        }}
      >
        <div>
          <span style={{ display: 'block', fontSize: '0.6rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            LIVE THROUGHPUT
          </span>
          <strong style={{ color: isLight ? '#2563EB' : '#38BDF8', fontSize: '0.85rem' }}>
            {telemetry.throughput} Mbps
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.6rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            PACKET RATE (PPS)
          </span>
          <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC', fontSize: '0.85rem' }}>
            {telemetry.pps.toLocaleString()} pps
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.6rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            PACKET AUDIT TALLY
          </span>
          <strong style={{ color: isLight ? '#0F172A' : '#F8FAFC', fontSize: '0.85rem' }}>
            {telemetry.packetCount.toLocaleString()} pkts
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.6rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            ICV AUTH INTEGRITY
          </span>
          <strong style={{ color: anomalyActive ? '#EF4444' : '#10B981', fontSize: '0.85rem' }}>
            {anomalyActive ? '99.84% (ISOLATING)' : telemetry.integrityRate}
          </strong>
        </div>

        <div>
          <span style={{ display: 'block', fontSize: '0.6rem', color: isLight ? '#64748B' : '#94A3B8' }}>
            SESSION LATENCY
          </span>
          <strong style={{ color: isLight ? '#2563EB' : '#38BDF8', fontSize: '0.85rem' }}>
            {telemetry.latency}
          </strong>
        </div>
      </div>
    </div>
  );
}

export default PrivCommTunnelVisualizer;
