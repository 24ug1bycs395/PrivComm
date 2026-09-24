import React, { useState, useEffect } from 'react';
import {
  Database,
  RefreshCw,
  FileText,
  Download,
  Shield,
  Clock,
  ArrowRight,
  ExternalLink,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

export default function HistoryVaultTab({ onSelectAnalysis }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (e) {
      console.error('Failed to load analysis history', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-container" style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      <div className="section-header-badge" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
        <Database size={18} color="#38bdf8" />
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8', letterSpacing: '0.05em' }}>
          ANALYSIS VAULT & PERSISTENCE
        </span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', margin: '0 0 0.5rem 0' }}>
            Historical PCAP Analysis Records
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>
            Unified archive of all audited PCAP captures, ML traffic classifications, and compliance assessment records.
          </p>
        </div>
        <button
          type="button"
          className="btn-ghost"
          onClick={fetchHistory}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.5rem 0.85rem' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Vault</span>
        </button>
      </div>

      <div className="glass-card" style={{ padding: '1.25rem' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 1rem auto' }} />
            <div>Loading historical analysis records...</div>
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            <Database size={32} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: '#94a3b8' }}>No Analysis Runs Recorded Yet</div>
            <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
              Upload a PCAP capture or run a strongSwan testbed scenario to populate the persistence vault.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#64748b', textAlign: 'left', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  <th style={{ padding: '10px 12px' }}>Timestamp</th>
                  <th style={{ padding: '10px 12px' }}>Capture File</th>
                  <th style={{ padding: '10px 12px' }}>Protocol</th>
                  <th style={{ padding: '10px 12px' }}>Traffic Class</th>
                  <th style={{ padding: '10px 12px' }}>Risk Level</th>
                  <th style={{ padding: '10px 12px' }}>Findings</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const assessment = job.security_assessment || {};
                  const riskLevel = assessment.risk_level || 'SECURE';
                  const traffic = job.traffic_classification || {};
                  const isHighRisk = riskLevel === 'HIGH' || riskLevel === 'CRITICAL';
                  const filename = job.filename || 'capture.pcap';

                  return (
                    <tr key={job.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                        {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td style={{ padding: '12px', fontWeight: 600, color: '#f1f5f9' }}>
                        {filename}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>
                          {job.ike_version || 'IPsec / IKEv2'}
                        </span>
                      </td>
                      <td style={{ padding: '12px', color: '#38bdf8', fontWeight: 500 }}>
                        {traffic.traffic_type || 'Encrypted IPsec'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span className={`badge ${isHighRisk ? 'badge-red' : 'badge-green'}`} style={{ fontSize: '0.72rem' }}>
                          {riskLevel}
                        </span>
                      </td>
                      <td style={{ padding: '12px', color: '#cbd5e1' }}>
                        {assessment.findings_count || (assessment.findings ? assessment.findings.length : 0)} issues
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', gap: '8px' }}>
                          <a
                            href={`/reports/download-html?filename=${filename}`}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-ghost"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            title="Open Executive HTML Report"
                          >
                            <FileText size={13} /> HTML
                          </a>
                          <button
                            type="button"
                            className="btn-primary"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            onClick={() => {
                              if (onSelectAnalysis) onSelectAnalysis(job);
                            }}
                          >
                            Inspect <ArrowRight size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
