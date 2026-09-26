import React, { useEffect, useRef } from 'react';
import { useTheme } from '../ThemeContext';

export default function TopologyCanvas() {
  const canvasRef = useRef(null);
  const { theme } = useTheme();
  const isLight = theme === 'light';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resize = () => {
      canvas.width = canvas.parentElement.clientWidth;
      canvas.height = 320;
    };
    resize();
    window.addEventListener('resize', resize);

    const primaryColor = isLight ? '#0284c7' : '#38bdf8';
    const greenColor = isLight ? '#16a34a' : '#34d399';
    const blueColor = isLight ? '#2563eb' : '#3b82f6';

    // Particles for flowing ESP/AH encrypted packets
    const particles = [];
    for (let i = 0; i < 28; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.004,
        size: 2 + Math.random() * 2.5,
        color: Math.random() > 0.35 ? primaryColor : greenColor,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      const nodeA = { x: w * 0.12, y: h * 0.5 };
      const nodeCenter = { x: w * 0.5, y: h * 0.5 };
      const nodeB = { x: w * 0.88, y: h * 0.5 };

      // Connecting Tunnel Mesh Lines
      ctx.lineWidth = 2;
      ctx.strokeStyle = isLight ? 'rgba(2, 132, 199, 0.22)' : 'rgba(56, 189, 248, 0.2)';
      ctx.setLineDash([6, 6]);

      // Path Alpha -> Center
      ctx.beginPath();
      ctx.moveTo(nodeA.x, nodeA.y);
      ctx.bezierCurveTo(w * 0.25, h * 0.25, w * 0.35, h * 0.75, nodeCenter.x, nodeCenter.y);
      ctx.stroke();

      // Path Center -> Beta
      ctx.beginPath();
      ctx.moveTo(nodeCenter.x, nodeCenter.y);
      ctx.bezierCurveTo(w * 0.65, h * 0.25, w * 0.75, h * 0.75, nodeB.x, nodeB.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Flowing Packets Animation
      particles.forEach((p) => {
        p.progress += p.speed;
        if (p.progress > 1) p.progress = 0;

        let px, py;
        if (p.progress < 0.5) {
          const t = p.progress * 2;
          px = (1 - t) * (1 - t) * nodeA.x + 2 * (1 - t) * t * (w * 0.3) + t * t * nodeCenter.x;
          py = (1 - t) * (1 - t) * nodeA.y + 2 * (1 - t) * t * (h * 0.25) + t * t * nodeCenter.y;
        } else {
          const t = (p.progress - 0.5) * 2;
          px = (1 - t) * (1 - t) * nodeCenter.x + 2 * (1 - t) * t * (w * 0.7) + t * t * nodeB.x;
          py = (1 - t) * (1 - t) * nodeCenter.y + 2 * (1 - t) * t * (h * 0.75) + t * t * nodeB.y;
        }

        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Nodes
      [
        { ...nodeA, label: 'GATEWAY ALPHA', sub: 'Site-01 Initiator', color: primaryColor },
        { ...nodeCenter, label: 'SENTINEL CORE', sub: 'ESP/AH Inspector', color: blueColor },
        { ...nodeB, label: 'GATEWAY BETA', sub: 'Site-02 Responder', color: greenColor },
      ].forEach((node) => {
        // Outer circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = isLight ? '#ffffff' : 'rgba(16, 26, 46, 0.9)';
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();

        // Inner core
        ctx.beginPath();
        ctx.arc(node.x, node.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.shadowColor = node.color;
        ctx.shadowBlur = isLight ? 4 : 8;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Text
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillStyle = isLight ? '#0f172a' : '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, node.x, node.y + 36);

        ctx.font = '10px JetBrains Mono, monospace';
        ctx.fillStyle = isLight ? '#475569' : '#94a3b8';
        ctx.fillText(node.sub, node.x, node.y + 50);
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isLight]);

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      borderRadius: 'var(--radius-lg)',
      background: 'var(--bg-card)',
      border: '1px solid var(--border-default)',
      boxShadow: 'var(--shadow-sm)',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-secondary)',
      }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 600, letterSpacing: '0.05em' }}>
          TOPOLOGY_RECON // SECURE SITE-TO-SITE TUNNEL MESH
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--accent-green)', fontWeight: 600 }}>
          ● LIVE TELEMETRY
        </span>
      </div>
      <canvas ref={canvasRef} style={{ width: '100%', height: '320px', display: 'block' }} />
    </div>
  );
}
