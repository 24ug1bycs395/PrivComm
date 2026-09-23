<<<<<<< HEAD
# AI-Powered IPsec VPN Protocol Analyzer & Security Assessment Framework

An end-to-end Python framework for analyzing network capture files (`.pcap`, `.pcapng`), extracting IPsec / IKEv1 / IKEv2 / ESP security parameters, classifying network traffic using a pre-trained **XGBoost Encrypted Traffic Classifier**, and evaluating security configurations against a deterministic, editable security policy.

---

## 🏗 System Architecture

```text
               .pcap / .pcapng Capture
                         │
                         ▼
        ┌─────────────────────────────────┐
        │     TShark / PCAP Ingestion     │
        └────────────────┬────────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌────────────────────┐      ┌────────────────────┐
│ IPsec/IKE Analyzer │      │   Flow Extractor   │
└──────────┬─────────┘      └──────────┬─────────┘
           │                           │
           ▼                           ▼
┌────────────────────┐      ┌────────────────────┐
│ Configuration Data │      │   XGBoost Model    │
└──────────┬─────────┘      └──────────┬─────────┘
           │                           │
           ▼                           ▼
┌────────────────────┐      ┌────────────────────┐
│Security Assessment │      │Traffic Class + Conf│
└──────────┬─────────┘      └──────────┬─────────┘
           └─────────────┬─────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────┐
│            Unified Analysis Report             │
│            (JSON Output & Summary CSV)         │
└────────────────────────────────────────────────┘
=======
<div align="center">

# Cyber Sentinel
### AI-Powered IPsec VPN Protocol Analysis & Security Assessment Framework
**Developed for Smart India Hackathon (SIH)**

[![SIH](https://img.shields.io/badge/Smart%20India%20Hackathon-2024%2F2025%2F2026-blue?style=for-the-badge&logo=shield)](https://sih.gov.in)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%7C%20Dashboard-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Security](https://img.shields.io/badge/Security-NIST%20SP%20800--77-red?style=for-the-badge&logo=security)](https://csrc.nist.gov/publications/detail/sp/800-77/rev-1/final)

<p align="center">
  <strong>Automated VPN Traffic Inspection • Cryptographic Strength Evaluation • AI Risk Scoring • Compliance Audit Reporting</strong>
</p>

---

</div>

## 📌 Table of Contents
- [Executive Overview](#-executive-overview)
- [The Problem & Impact](#-the-problem--impact)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Project Directory Structure](#-project-directory-structure)
- [Technology Stack](#-technology-stack)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
  - [Command-Line Interface (CLI)](#1-command-line-interface-cli)
  - [Interactive SOC Dashboard](#2-interactive-soc-dashboard)
- [Cryptographic & Compliance Standards](#-cryptographic--compliance-standards)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License & Acknowledgments](#-license--acknowledgments)

---

## 🌐 Executive Overview

**Cyber Sentinel** is an enterprise-grade, AI-assisted security assessment platform engineered to audit, evaluate, and monitor **IPsec (Internet Protocol Security) VPN tunnels**.

In enterprise and sovereign government networks, IPsec is the de facto standard for site-to-site and remote-access confidentiality. However, misconfigured transforms, deprecated algorithms (e.g., DES/3DES, MD5, low-order Diffie-Hellman groups), and improper SA rekeying frequently leave networks vulnerable to eavesdropping, downgrade exploits, and man-in-the-middle (MITM) attacks.

**Cyber Sentinel** automates the entire lifecycle of IPsec protocol verification:
1. Ingests raw PCAP capture files or live network stream telemetry.
2. Decodes IKEv1/IKEv2 handshakes and ESP/AH protocol negotiations.
3. Quantifies cryptographic strength and identifies security misconfigurations.
4. Uses Machine Learning models to score risk, spot anomalous re-key patterns, and flag anomalous tunnel behaviors.
5. Generates human-readable compliance summaries and remediation guides for security operators.

---

## ⚠️ The Problem & Impact

| Challenge | Traditional Approach | Cyber Sentinel Solution |
| :--- | :--- | :--- |
| **Protocol Auditing** | Manual inspection using Wireshark packet-by-packet | Automated DPI parses entire sessions in milliseconds |
| **Crypto Evaluation** | Static manual review against security advisories | Dynamic policy engine mapping against NIST SP 800-77 & NSA CSfC |
| **Anomaly Detection** | Threshold-based static alarms with high false positives | ML-driven baseline profiling for rekey intervals, jitter, and replay attacks |
| **Audit Reporting** | Days spent creating manual audit documentation | One-click automated PDF/JSON compliance & executive reports |

---

## ✨ Key Features

- **Deep Packet Inspection (DPI) Engine**:
  - Full dissection of **IKEv1** (Main Mode, Aggressive Mode, Quick Mode) and **IKEv2** (IKE_SA_INIT, IKE_AUTH, CREATE_CHILD_SA).
  - Identification of Security Parameter Indexes (SPI), Cookie values, Payload types, Transform types, and proposal matrices.
- **Cryptographic Rigor Assessment**:
  - Evaluation of Encryption Ciphers (`AES-GCM`, `AES-CBC`, `ChaCha20-Poly1305`, `3DES`, `Blowfish`).
  - Integrity & PRF Hash validation (`SHA-256`, `SHA-384`, `SHA-512`, `MD5`, `SHA-1`).
  - Diffie-Hellman Group audits (DH Groups 1, 2, 5 flagged as insecure; DH Groups 14, 19, 20, 21 verified).
  - PFS (Perfect Forward Secrecy) enforcement validation.
- **AI-Powered Risk & Anomaly Scoring**:
  - Multi-factor risk engine producing a unified **Posture Score (0 - 100)**.
  - Anomaly detection targeting packet drop surges, rekey failures, Aggressive Mode credential exposure, and potential replay attacks.
- **Automated Remediation & Reporting**:
  - Generates executive reports with CVSS-aligned severity ratings.
  - Produces remediation snippets for major firewall and gateway vendors (**Cisco IOS**, **Fortinet FortiGate**, **pfSense**, **StrongSwan**, and **Juniper JunOS**).
- **Interactive SOC Dashboard**:
  - Real-time tunnel topology visualizer.
  - Active tunnel health metrics, crypto breakdown charts, and security incident timeline.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph INGESTION["1. Ingestion Layer"]
        A1["PCAP Upload (.pcap, .pcapng)"]
        A2["Live Interface Sniffing (Scapy / AF_PACKET)"]
    end

    subgraph DECODER["2. Protocol Dissection & DPI Engine"]
        B1["IKEv1 / IKEv2 Dissector"]
        B2["ESP / AH Transport & Tunnel Parser"]
        B3["Security Association (SA) Matrix Extractor"]
    end

    subgraph ANALYZER["3. Intelligence & AI Assessment Core"]
        C1["Cryptographic Rule Engine (NIST/NSA CSfC)"]
        C2["AI Risk Scoring & Anomaly Detection"]
        C3["CVE & Weakness Signature Database"]
    end

    subgraph OUTPUT["4. Presentation & Analytics"]
        D1["Interactive SOC Web Dashboard"]
        D2["FastAPI REST & WebSocket Endpoints"]
        D3["Automated PDF / JSON / CSV Audit Reports"]
    end

    INGESTION --> DECODER
    DECODER --> ANALYZER
    ANALYZER --> OUTPUT
>>>>>>> 378daef7b72a00c38ac58a8c5fac3e26d3977501
```

---

<<<<<<< HEAD
## 🛠 Prerequisites & Environment Setup

### 1. Python Environment
Requires **Python 3.10+**. Install required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Wireshark / TShark (Recommended)
Installing Wireshark on Windows automatically includes `tshark.exe` (typically at `C:\Program Files\Wireshark\tshark.exe`).

* **If TShark is in PATH**: The analyzer will automatically detect and use it.
* **If TShark is in a custom path**: Set the `TSHARK_PATH` environment variable:
  ```powershell
  $env:TSHARK_PATH="C:\Program Files\Wireshark\tshark.exe"
  ```
* **Fallback**: If TShark is not installed, the framework seamlessly falls back to the built-in Scapy packet parsing engine.

---

## 🚦 Startup & Dependency Check

Run the dependency check command to verify Python, TShark/Wireshark, and trained ML model status:

```bash
python main.py check-dependencies
```

Example Output:

```text
--- AI-Powered IPsec VPN Protocol Analyzer Startup Check ---
Python: [OK] (v3.10.9)
TShark: [OK] (C:\Program Files\Wireshark\tshark.exe)
TShark version: TShark (Wireshark) 4.2.0
Wireshark: [OK]
XGBoost model: [OK] (Artifacts found at 'traffic-classifier\models')
-----------------------------------------------------------
=======
## 📁 Project Directory Structure

```text
ipsecAIanalyzer-SIH26/
├── backend/
│   ├── app/
│   │   ├── api/                   # REST API routes (endpoints for upload, metrics, reports)
│   │   ├── core/                  # Configuration, logging, and security settings
│   │   ├── engine/                # Core packet processing & DPI engine
│   │   │   ├── ike_parser.py      # IKEv1/IKEv2 dissector
│   │   │   ├── esp_analyzer.py    # ESP/AH payload & integrity checker
│   │   │   └── crypto_eval.py     # Cipher & DH group security validator
│   │   ├── ml/                    # AI/ML anomaly detection models
│   │   │   ├── model.py           # Anomaly detector & risk scorer
│   │   │   └── train.py           # Training pipelines & feature extraction
│   │   ├── reports/               # Report generators (PDF, JSON, HTML)
│   │   └── main.py                # FastAPI application entry point
│   ├── tests/                     # Unit & integration test suites
│   └── requirements.txt           # Backend dependencies
├── frontend/                      # Interactive SOC UI (React / Next.js / Vite)
│   ├── src/
│   │   ├── components/            # Reusable UI widgets & graphs
│   │   ├── pages/                 # Dashboard, Analysis, Reports pages
│   │   └── services/              # API communication layer
│   ├── package.json
│   └── vite.config.js
├── datasets/                      # Sample PCAP captures for verification & tests
│   ├── ikev1_aggressive_mode.pcap
│   ├── ikev2_aes_gcm_sample.pcap
│   └── weak_des_dh2_sample.pcap
├── docs/                          # Architecture diagrams, API specs, and presentations
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🧰 Technology Stack

### **Backend & Core Engine**
- **Language**: Python 3.10+
- **Framework**: FastAPI (Asynchronous high-throughput API)
- **Packet Dissection**: Scapy, PyShark / TShark, dpkt
- **AI / Machine Learning**: Scikit-Learn, PyTorch / XGBoost, Pandas, NumPy
- **Reporting Engine**: WeasyPrint / ReportLab, Jinja2

### **Frontend & Visual Analytics**
- **Framework**: React 18 / Vite or Next.js
- **Styling**: Vanilla CSS / TailwindCSS / Glassmorphic SOC Dark Theme
- **Data Visualization**: Chart.js, Recharts, Cytoscape.js (for network topology)
- **Icons**: Lucide Icons

---

## 🚀 Installation & Setup

### Prerequisites
- **Python**: `3.10` or higher
- **Node.js**: `18.x` or higher (for frontend dashboard)
- **Packet Capture Library**: 
  - **Linux**: `libpcap-dev` (`sudo apt-get install libpcap-dev tshark`)
  - **Windows**: [Npcap](https://npcap.com/) (installed with WinPcap API compatibility)
  - **macOS**: `brew install libpcap wireshark`

---

### 1. Clone the Repository
```bash
git clone https://github.com/KrishJain4234/ipsecAIanalyzer-SIH26.git
cd ipsecAIanalyzer-SIH26
```

### 2. Backend Setup & Run

```bash
# Clone the repository
git clone https://github.com/KrishJain4234/ipsecAnalyzer-SIH26.git
cd ipsecAnalyzer-SIH26

# Create and activate a virtual environment
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Start the backend API server
uvicorn main:app --reload
```

The API will be live at `http://localhost:8000`
Interactive Swagger docs: `http://localhost:8000/docs`

### 3. Frontend (Homepage)

Open `index.html` directly in a browser, **or** serve it locally:

```bash
python -m http.server 4321
# Open http://localhost:4321 in your browser
```

### 4. Run Tests

```bash
# From the project root
python -m pytest tests/ -v
# Or run the engine test directly
$env:PYTHONPATH="."; python tests/test_protocol_engine.py
>>>>>>> 378daef7b72a00c38ac58a8c5fac3e26d3977501
```

---

<<<<<<< HEAD
## 💻 CLI Usage

### 1. Analyze a Single Capture File

Analyze a `.pcap` or `.pcapng` file and print the unified JSON analysis to the console:

```bash
python main.py analyze --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng
```

Save the output report to a JSON file:

```bash
python main.py analyze --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng --output results/report.json
```

### 2. Batch Process a Directory of Captures

Process all `.pcap` / `.pcapng` files in a directory and generate individual JSON reports plus a batch `summary.csv`:

```bash
python main.py batch --input samples/ --output results/
```

Generated `results/summary.csv` columns:
- `capture`
- `ipsec_detected`
- `ike_version`
- `encryption`
- `dh_group`
- `traffic_type`
- `traffic_confidence`
- `risk_level`
- `finding_count`

---

## 🔒 Security Policy Customization

Security rules are managed deterministically in `config/security_policy.yaml`:

```yaml
encryption:
  approved:
    - "AES-256-GCM"
    - "AES-128-GCM"
    - "AES-256-CBC"
  forbidden:
    - "DES"
    - "3DES"

dh_groups:
  approved: [14, 19, 20, 21, 28]
  forbidden: [1, 2, 5]

protocol:
  approved_versions: ["IKEv2"]
  disapproved_versions: ["IKEv1"]

risk_weights:
  HIGH: 30
  MEDIUM: 15
  LOW: 5
```

* Unobservable parameters (e.g., PFS when unobserved) are reported as `"unknown"` / `"not_observable"` and are **never** falsely flagged as security violations.

---

## 🧪 Unit Testing

Run the full test suite:

```bash
python -m unittest discover tests
=======
## 🔌 API Reference — Core Feature 1

### POST `/analyze/protocol`

Analyzes an uploaded PCAP/PCAPNG file and returns structured IPsec protocol characteristics.

**Request**

| Parameter   | Type   | Description                        |
|-------------|--------|------------------------------------|
| `pcap_file` | file   | PCAP or PCAPNG capture file upload |

Content-Type: `multipart/form-data`

**Example (curl)**

```bash
curl -X POST http://localhost:8000/analyze/protocol \
  -F "pcap_file=@capture.pcap"
```

**Example Response**

```json
{
  "ipsec_detected": true,
  "ike_version": "IKEv2",
  "esp_detected": true,
  "ah_detected": false,
  "mode": "Tunnel",
  "encryption": "AES-256-GCM",
  "integrity": "AEAD",
  "dh_group": "14",
  "pfs": true,
  "replay_protection": true,
  "ip_version": "IPv4",
  "source_ip": "192.168.1.10",
  "destination_ip": "10.0.0.1"
}
```

### GET `/health`

Returns API server health status.

```json
{
  "status": "operational",
  "service": "Cyber Sentinel Protocol Identification Engine",
  "version": "1.0.0"
}
>>>>>>> 378daef7b72a00c38ac58a8c5fac3e26d3977501
```

---

<<<<<<< HEAD
## 🌐 Future VM Testbed Pipeline

The architecture is designed to integrate seamlessly with strongSwan IPsec testbed VMs:

```text
  Config Generator ──► strongSwan VMs ──► Traffic Generator ──► TShark / PCAP ──► THIS ANALYZER
```
=======

## 💻 Usage Guide

### 1. Command-Line Interface (CLI)
Cyber Sentinel can be executed directly as a standalone CLI tool for CI/CD pipelines or headless servers:

```bash
# Analyze a sample PCAP file
python -m app.engine.cli --pcap datasets/weak_des_dh2_sample.pcap --output-format json

# Generate an audit report in PDF
python -m app.engine.cli --pcap datasets/ikev2_aes_gcm_sample.pcap --export-pdf report.pdf
```

### 2. Interactive SOC Dashboard
1. Open `http://localhost:5173` in your browser.
2. Drag and drop any `.pcap` or `.pcapng` capture file into the **Upload Portal**.
3. View real-time parsing results:
   - **Protocol Version**: IKEv1 vs IKEv2 detection.
   - **Encryption & Hash Integrity**: Identified transforms tagged as `SECURE`, `DEPRECATED`, or `CRITICAL`.
   - **Diffie-Hellman Group**: Key-exchange strength assessment.
   - **Posture Score**: Computed risk rating with actionable remediation steps.
4. Export the findings with a single click to an **Executive Summary PDF**.

---

## 📜 Cryptographic & Compliance Standards

Cyber Sentinel evaluates IPsec configurations against recognized cybersecurity benchmarks:

- **NIST SP 800-77 Rev. 1**: *Guide to IPsec VPNs*
- **RFC 7296**: *Internet Key Exchange Protocol Version 2 (IKEv2)*
- **RFC 4301 / 4303**: *Security Architecture for the Internet Protocol & ESP*
- **NSA Commercial National Security Algorithm (CNSA) Suite**: Quantum-resistant migration standards.
- **ANSSI / BSI VPN Guidelines**: European national technical guidance for secure IPsec tunnels.

---

## 🗺️ Roadmap

- [x] Core IKEv1 and IKEv2 payload extraction engine.
- [x] Cryptographic policy auditor and posture scoring.
- [x] Interactive web dashboard prototype.
- [ ] Post-Quantum Cryptography (PQC) hybrid key exchange detection (ML-KEM, Kyber).
- [ ] Automated firewall configuration generator (export hardened configurations for Cisco, Fortinet, and StrongSwan).
- [ ] Live distributed capture agents for enterprise multi-site VPN gateways.

---

## 🤝 Contributing

Contributions are welcome! If you would like to improve parser coverage, add protocol dissectors, or refine ML anomaly algorithms:

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/NewTransformParser`).
3. Commit your changes (`git commit -m "Add parser for ChaCha20-Poly1305"`).
4. Push to the branch (`git push origin feature/NewTransformParser`).
5. Open a Pull Request.

---
>>>>>>> 378daef7b72a00c38ac58a8c5fac3e26d3977501
