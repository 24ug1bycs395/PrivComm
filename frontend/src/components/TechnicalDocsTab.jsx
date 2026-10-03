import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, FileText, Folder, Check, Download, LoaderCircle } from 'lucide-react';

const sections = [
  ['overview', '1. Executive Overview'], ['architecture', '2. System Architecture & Processing Pipeline'],
  ['dissection', '3. Packet Ingestion & Protocol Dissection Engine'], ['classifier', '4. AI Traffic Classification Engine'],
  ['compliance', '5. NIST SP 800-77 Compliance Engine'], ['anomaly', '6. Behavioral Anomaly Detection Engine'],
  ['pqc', '7. Post-Quantum Cryptography Readiness Assessment'], ['testbed', '8. Multi-Node Testbed Infrastructure'], ['api', '9. REST API Reference'],
];
const SectionHeading = ({ id, children }) => <h2 id={id} className="gdoc-section-heading">{children}</h2>;
const Subheading = ({ children }) => <h3 className="gdoc-subheading">{children}</h3>;
const BulletList = ({ children }) => <ul className="gdoc-list">{children}</ul>;

const getSafeFilename = (documentTitle, extension) => {
  const base = documentTitle
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/[. ]+$/g, '') || 'PrivComm Technical Documentation';
  return `${base}.${extension}`;
};

const getInlineRuns = (node, docx, styles = {}) => {
  if (node.nodeType === Node.TEXT_NODE) {
    return node.textContent ? [new docx.TextRun({ text: node.textContent, ...styles })] : [];
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return [];
  if (node.tagName === 'BR') return [new docx.TextRun({ text: '', breakLine: true })];

  const nextStyles = { ...styles };
  if (['B', 'STRONG'].includes(node.tagName)) nextStyles.bold = true;
  if (['I', 'EM'].includes(node.tagName)) nextStyles.italics = true;
  if (node.tagName === 'CODE') {
    nextStyles.font = 'Courier New';
    nextStyles.color = '174EA6';
  }
  return Array.from(node.childNodes).flatMap((child) => getInlineRuns(child, docx, nextStyles));
};

const createDocxBlocks = (article, docx) => {
  const blocks = [];
  const appendNode = (node) => {
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName;
    if (tag === 'H1' || tag === 'H2' || tag === 'H3') {
      const headingLevel = tag === 'H1' ? docx.HeadingLevel.TITLE : tag === 'H2' ? docx.HeadingLevel.HEADING_1 : docx.HeadingLevel.HEADING_2;
      blocks.push(new docx.Paragraph({ text: node.textContent.trim(), heading: headingLevel, spacing: { before: 240, after: 120 } }));
      return;
    }
    if (tag === 'P') {
      const runs = getInlineRuns(node, docx);
      if (runs.length) blocks.push(new docx.Paragraph({ children: runs, spacing: { after: 120, line: 276 } }));
      return;
    }
    if (tag === 'UL' || tag === 'OL') {
      Array.from(node.children).filter((child) => child.tagName === 'LI').forEach((item) => {
        blocks.push(new docx.Paragraph({
          children: getInlineRuns(item, docx),
          bullet: { indent: 360 },
          spacing: { after: 60 },
        }));
      });
      return;
    }
    if (tag === 'TABLE') {
      const tableRows = Array.from(node.querySelectorAll('tr')).map((row) => new docx.TableRow({
        children: Array.from(row.children).map((cell) => new docx.TableCell({
          children: [new docx.Paragraph({ children: getInlineRuns(cell, docx) })],
          shading: cell.tagName === 'TH' ? { fill: 'F1F3F4' } : undefined,
          width: { size: Math.floor(100 / Math.max(row.children.length, 1)), type: docx.WidthType.PERCENTAGE },
        })),
      }));
      if (tableRows.length) {
        blocks.push(new docx.Table({
          rows: tableRows,
          width: { size: 100, type: docx.WidthType.PERCENTAGE },
          borders: Object.fromEntries(['top', 'bottom', 'left', 'right', 'insideHorizontal', 'insideVertical'].map((side) => [
            side,
            { style: docx.BorderStyle.SINGLE, size: 1, color: 'DADCE0' },
          ])),
        }));
        blocks.push(new docx.Paragraph({ text: '' }));
      }
      return;
    }
    if (node.classList.contains('gdoc-code-line')) {
      blocks.push(new docx.Paragraph({
        children: [new docx.TextRun({ text: node.textContent.trim(), font: 'Courier New', color: '3C4043' })],
        spacing: { before: 120, after: 180 },
      }));
      return;
    }
    if (tag === 'DIV' || tag === 'HEADER' || tag === 'FOOTER') {
      Array.from(node.children).forEach(appendNode);
      return;
    }
    if (tag === 'SPAN') {
      const text = node.textContent.trim();
      if (text) blocks.push(new docx.Paragraph({ text, spacing: { after: 80 } }));
      return;
    }
    if (!node.children.length && node.textContent.trim()) {
      blocks.push(new docx.Paragraph({ children: getInlineRuns(node, docx), spacing: { after: 80 } }));
      return;
    }
    Array.from(node.children).forEach(appendNode);
  };

  Array.from(article.children).forEach(appendNode);
  return blocks;
};

export default function TechnicalDocsTab() {
  const [activeSection, setActiveSection] = useState('overview');
  const [outlineOpen, setOutlineOpen] = useState(true);
  const [title, setTitle] = useState('PrivComm — IPsec VPN Intelligence & Traffic Classification Platform');
  const [exporting, setExporting] = useState('');
  const [exportError, setExportError] = useState('');
  const docRef = useRef(null);

  useEffect(() => {
    const root = docRef.current;
    if (!root) return undefined;
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (visible[0]) setActiveSection(visible[0].target.id);
    }, { root, rootMargin: '-12% 0px -70% 0px', threshold: [0.1, 0.35, 0.6] });
    sections.forEach(([id]) => { const element = document.getElementById(id); if (element) observer.observe(element); });
    return () => observer.disconnect();
  }, []);
  const jumpTo = (id) => { setActiveSection(id); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); };

  const downloadPdf = async () => {
    setExporting('pdf');
    setExportError('');
    try {
      const [{ default: html2pdf }, article] = await Promise.all([
        import('html2pdf.js'),
        Promise.resolve(docRef.current?.querySelector('.gdoc-page')),
      ]);
      if (!article) throw new Error('The document content is not available for export.');
      const exportRoot = article.cloneNode(true);
      const coverTitle = exportRoot.querySelector('.gdoc-cover h1');
      if (coverTitle) coverTitle.textContent = title;
      await html2pdf().set({
        margin: [12, 14, 14, 14],
        filename: getSafeFilename(title, 'pdf'),
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, scrollY: 0 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['css', 'legacy'], avoid: ['tr', '.gdoc-section-heading'] },
      }).from(exportRoot).save();
    } catch (error) {
      console.error('Failed to export technical documentation as PDF.', error);
      setExportError(`PDF export failed: ${error.message}`);
    } finally {
      setExporting('');
    }
  };

  const downloadDocx = async () => {
    setExporting('docx');
    setExportError('');
    try {
      const docx = await import('docx');
      const article = docRef.current?.querySelector('.gdoc-page');
      if (!article) throw new Error('The document content is not available for export.');
      const exportRoot = article.cloneNode(true);
      const coverTitle = exportRoot.querySelector('.gdoc-cover h1');
      if (coverTitle) coverTitle.textContent = title;
      const document = new docx.Document({
        sections: [{
          properties: {
            page: {
              size: { width: 11906, height: 16838 },
              margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
            },
          },
          children: createDocxBlocks(exportRoot, docx),
        }],
      });
      const blob = await docx.Packer.toBlob(document);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = getSafeFilename(title, 'docx');
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      console.error('Failed to export technical documentation as DOCX.', error);
      setExportError(`DOCX export failed: ${error.message}`);
    } finally {
      setExporting('');
    }
  };

  return (
    <div className="gdoc-shell">
      <div className="gdoc-topbar">
        <div className="gdoc-file-icon"><FileText size={25} strokeWidth={1.7} /></div>
        <div className="gdoc-title-wrap"><input aria-label="Document title" value={title} onChange={(event) => setTitle(event.target.value)} /><div className="gdoc-file-meta"><span>Starred</span><span>Last edit was a few seconds ago</span></div></div>
        <div className="gdoc-export-actions" aria-label="Download document">
          <button type="button" className="gdoc-export-button" onClick={downloadDocx} disabled={Boolean(exporting)} aria-label="Download as DOCX">
            {exporting === 'docx' ? <LoaderCircle size={15} className="gdoc-export-spinner" /> : <Download size={15} />}
            <span>{exporting === 'docx' ? 'Preparing…' : 'DOCX'}</span>
          </button>
          <button type="button" className="gdoc-export-button gdoc-export-button-primary" onClick={downloadPdf} disabled={Boolean(exporting)} aria-label="Download as PDF">
            {exporting === 'pdf' ? <LoaderCircle size={15} className="gdoc-export-spinner" /> : <Download size={15} />}
            <span>{exporting === 'pdf' ? 'Preparing…' : 'PDF'}</span>
          </button>
        </div>
      </div>
      {exportError && <div className="gdoc-export-error" role="alert">{exportError}</div>}
      <div className="gdoc-workspace">
        {outlineOpen ? (
          <aside className="gdoc-outline" aria-label="Document outline">
            <div className="gdoc-outline-title">
              <span>Document outline</span>
              <button
                type="button"
                title="Collapse outline"
                aria-label="Collapse document outline"
                onClick={() => setOutlineOpen(false)}
              >
                <ChevronLeft size={16} />
              </button>
            </div>
            <div className="gdoc-outline-list">{sections.map(([id, label]) => <button key={id} className={`gdoc-outline-item ${activeSection === id ? 'active' : ''}`} onClick={() => jumpTo(id)}>{label}</button>)}</div>
            <div className="gdoc-outline-footer"><Folder size={15} /> Technical documentation</div>
          </aside>
        ) : (
          <button
            type="button"
            className="gdoc-outline-reopen"
            title="Show document outline"
            aria-label="Show document outline"
            onClick={() => setOutlineOpen(true)}
          >
            <ChevronRight size={17} />
          </button>
        )}
        <div className="gdoc-editor-wrap">
          <main className="gdoc-editor" ref={docRef}><article className="gdoc-page">
            <header className="gdoc-cover"><div className="gdoc-cover-kicker">TECHNICAL DOCUMENTATION</div><h1>{title}</h1><p className="gdoc-lede">A production-grade platform for analyzing, assessing, and securing encrypted VPN infrastructure in real time.</p><div className="gdoc-cover-rule" /><div className="gdoc-cover-grid"><span><b>Document owner</b>Team SatyaSetu26</span><span><b>Classification</b>Technical documentation</span><span><b>Last Updated</b>30 September 2026</span></div></header>
            <SectionHeading id="overview">1. Executive Overview</SectionHeading><p><strong>PrivComm</strong> is a production-grade IPsec VPN Intelligence and Traffic Classification platform designed to analyze, assess, and secure encrypted VPN infrastructures in real time.</p><p>The platform combines:</p><BulletList><li>Deep Protocol Dissection</li><li>AI-Powered Traffic Classification</li><li>Automated Security Assessment</li><li>Compliance Validation</li><li>Behavioral Anomaly Detection</li></BulletList><p>It provides actionable security intelligence without decrypting protected VPN payloads.</p><Subheading>Core Capabilities</Subheading><Subheading>Deep Packet Dissection</Subheading><p>Extracts observable IPsec and IKE parameters including:</p><BulletList><li>IKEv1 / IKEv2 Protocol Version</li><li>Security Parameter Index (SPI)</li><li>Encryption Algorithms</li><li>Integrity Algorithms</li><li>Diffie-Hellman Groups</li><li>Perfect Forward Secrecy (PFS)</li><li>Tunnel &amp; Transport Modes</li></BulletList><Subheading>AI Traffic Classification</Subheading><p>Uses a trained XGBoost classifier to identify encrypted application traffic based on statistical flow behavior.</p><p>Supported classes include:</p><BulletList><li>Chat</li><li>VoIP</li><li>Streaming</li><li>P2P</li><li>File Transfer</li><li>Web Browsing</li><li>DNS</li><li>Gaming</li><li>Other encrypted traffic categories</li></BulletList><Subheading>Automated Compliance Assessment</Subheading><p>Evaluates VPN configurations against:</p><BulletList><li>NIST SP 800-77 Rev.1</li><li>FIPS 140-3</li><li>Post-Quantum Cryptography Readiness Standards</li></BulletList>
            <SectionHeading id="architecture">2. System Architecture &amp; Processing Pipeline</SectionHeading><p>PrivComm separates protocol analysis, machine learning, compliance validation, and reporting into independent processing stages.</p><Subheading>End-to-End Workflow</Subheading><div className="gdoc-workflow"><span>PCAP File / Live VPN Stream</span><b>↓</b><span>Packet Ingestion Engine</span><b>↓</b><span>Protocol Dissection Layer<br /><small>(TShark / Scapy)</small></span><b>↓</b><span>Feature Extraction Engine<br /><small>(28 Statistical Features)</small></span><div className="gdoc-branch"><span>ML Engine</span><span>Compliance Engine</span></div><b>↓</b><span>Risk Assessment Layer</span><b>↓</b><span>Reports &amp; Dashboard</span></div><Subheading>Major Components</Subheading><BulletList><li>Packet Ingestion and Protocol Dissection</li><li>Machine Learning Classification</li><li>Compliance and Risk Assessment</li><li>Behavioral Monitoring and Reporting</li></BulletList>
            <SectionHeading id="dissection">3. Packet Ingestion &amp; Protocol Dissection Engine</SectionHeading><p>PrivComm utilizes:</p><BulletList><li>TShark</li><li>Scapy</li></BulletList><p>for structured packet analysis.</p><Subheading>Protocol Coverage</Subheading><BulletList><li>IKE Handshake Analysis</li><li>ESP Analysis</li><li>Tunnel Detection</li><li>Security Parameter Extraction</li></BulletList><Subheading>Observable Parameters</Subheading><p>The engine extracts:</p><BulletList><li>IKE Version</li><li>Initiator SPI</li><li>Responder SPI</li><li>Encryption Algorithms</li><li>Integrity Algorithms</li><li>PRF Algorithms</li><li>Diffie-Hellman Groups</li><li>Exchange Types</li><li>Encapsulation Mode</li></BulletList><Subheading>Zero-Payload Inspection Model</Subheading><p>PrivComm never decrypts ESP payloads. Instead, analysis is performed using:</p><BulletList><li>Protocol Metadata</li><li>Cryptographic Negotiation Parameters</li><li>Packet Timing Characteristics</li><li>Statistical Flow Features</li></BulletList><p>This ensures privacy-preserving security assessment.</p>
            <SectionHeading id="classifier">4. AI Traffic Classification Engine</SectionHeading><p>The machine learning subsystem classifies encrypted traffic without payload inspection.</p><Subheading>Model Used</Subheading><p><strong>XGBoost Multi-Class Classifier</strong></p><Subheading>Feature Set</Subheading><p>The model uses 28 statistical flow features including:</p><BulletList><li>Duration</li><li>Total FIAT / BIAT</li><li>Min, max, and mean FIAT / BIAT</li><li>Flow packets per second</li><li>Flow bytes per second</li><li>Flow inter-arrival times</li><li>Active and idle time</li><li>Bytes per packet</li><li>FIAT/BIAT ratio</li><li>Log duration and throughput features</li></BulletList><Subheading>Training Configuration</Subheading><p>Dataset split:</p><BulletList><li>Training: 70%</li><li>Validation: 15%</li><li>Testing: 15%</li></BulletList><p className="gdoc-code-line">n_estimators = 400<br />max_depth = 8<br />learning_rate = 0.08<br />objective = multi:softprob</p><Subheading>Output</Subheading><p>The model predicts:</p><BulletList><li>Traffic Class</li><li>Classification Confidence</li><li>Probability Distribution</li></BulletList><p>across 14 encrypted application categories.</p>
            <SectionHeading id="compliance">5. NIST SP 800-77 Compliance Engine</SectionHeading><p>PrivComm evaluates VPN configurations using predefined security policies.</p><table className="gdoc-table"><thead><tr><th>Policy ID</th><th>Requirement</th><th>Benchmark</th></tr></thead><tbody><tr><td>POL-01</td><td>Protocol Modernity</td><td>IKEv2 Required</td></tr><tr><td>POL-02</td><td>Encryption Strength</td><td>AES-GCM Preferred</td></tr><tr><td>POL-03</td><td>Diffie-Hellman Security</td><td>DH Group ≥ 14</td></tr><tr><td>POL-04</td><td>Perfect Forward Secrecy</td><td>Mandatory</td></tr><tr><td>POL-05</td><td>Integrity Protection</td><td>MD5 &amp; SHA1 Rejected</td></tr><tr><td>POL-06</td><td>Encapsulation Mode</td><td>Tunnel Mode Preferred</td></tr></tbody></table><Subheading>Compliance Outputs</Subheading><BulletList><li>Security Score</li><li>Risk Score</li><li>Policy Violations</li><li>Recommended Remediations</li></BulletList>
            <SectionHeading id="anomaly">6. Behavioral Anomaly Detection Engine</SectionHeading><p>PrivComm continuously monitors VPN telemetry and identifies unusual behavior patterns.</p><Subheading>Detection Capabilities</Subheading><BulletList><li>Replay Attacks</li><li>Traffic Burst Anomalies</li><li>Tunnel Instability</li><li>Session Drift</li><li>Sequence Number Violations</li><li>High-Entropy Exfiltration Patterns</li></BulletList><Subheading>Methodology</Subheading><p>Uses historical VPN behavior baselines and anomaly detection models to identify deviations from expected activity.</p>
            <SectionHeading id="pqc">7. Post-Quantum Cryptography Readiness Assessment</SectionHeading><p>PrivComm evaluates readiness for next-generation cryptographic standards.</p><Subheading>Assessment Areas</Subheading><BulletList><li>Hybrid Key Exchange Support</li><li>ML-KEM (Kyber) Readiness</li><li>RFC 9370 Compatibility</li><li>Quantum Vulnerability Assessment</li></BulletList><Subheading>Identifies</Subheading><p>Potential exposure to:</p><p><strong>Harvest Now, Decrypt Later (HNDL) attacks.</strong></p>
            <SectionHeading id="testbed">8. Multi-Node Testbed Infrastructure</SectionHeading><p>PrivComm includes an isolated IPsec VPN testbed for protocol validation and attack simulation.</p><Subheading>Node Topology</Subheading><table className="gdoc-table"><thead><tr><th>Node</th><th>Address</th><th>Role</th></tr></thead><tbody><tr><td>Initiator</td><td>192.168.56.10</td><td>VPN Client</td></tr><tr><td>Responder</td><td>192.168.56.20</td><td>VPN Gateway</td></tr><tr><td>Observer</td><td>192.168.56.30</td><td>Monitoring Node</td></tr></tbody></table><Subheading>Supported Activities</Subheading><BulletList><li>Tunnel Establishment</li><li>Traffic Injection</li><li>Packet Capture</li><li>Security Assessment</li><li>Attack Simulation</li></BulletList><div className="gdoc-callout"><strong>Future Roadmap</strong><p>Enterprise deployment support through Docker Containers, Kubernetes, AWS, Microsoft Azure, and Google Cloud Platform with scalable packet capture and monitoring infrastructure.</p></div>
            <SectionHeading id="api">9. REST API Reference</SectionHeading><table className="gdoc-table"><thead><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr></thead><tbody><tr><td>POST</td><td>/analyze/protocol</td><td>Upload and analyze PCAP files</td></tr><tr><td>GET</td><td>/analyze/sample</td><td>Retrieve compliant VPN assessment</td></tr><tr><td>GET</td><td>/analyze/sample-weak</td><td>Retrieve non-compliant VPN assessment</td></tr><tr><td>GET</td><td>/api/history</td><td>View historical assessments</td></tr><tr><td>GET</td><td>/reports/download-html</td><td>Download executive audit report</td></tr></tbody></table><Subheading>Key Features Summary</Subheading><div className="gdoc-check-list">{['Deep IPsec Protocol Analysis', 'AI-Powered Encrypted Traffic Classification', 'NIST Compliance Validation', 'Behavioral Anomaly Detection', 'Post-Quantum Readiness Assessment', 'Risk & Security Scoring', 'Live VPN Monitoring', 'Multi-Node Testbed Validation'].map((item) => <div key={item}><Check size={14} /> {item}</div>)}</div><footer className="gdoc-page-footer">PrivComm technical documentation <span>•</span> Internal reference</footer>
          </article></main>
        </div>
      </div>
    </div>
  );
}
