# PrivComm: AI-Driven IPsec VPN Protocol Analysis & Security Assessment Platform
## Technical Documentation & Problem Statement Alignment

---

### Executive Problem Statement Alignment

#### Background
Virtual Private Networks (VPNs) are fundamental to secure communication over untrusted networks. Among the available VPN technologies, IPsec is widely adopted across enterprise, government, military, and cloud infrastructures because of its ability to provide confidentiality, integrity, and authentication.

However, the security of an IPsec deployment depends on multiple factors, including the chosen cryptographic algorithms, authentication mechanisms, key exchange protocols, and operational mode (Tunnel or Transport). Misconfigurations, outdated cipher suites, improper key management, or protocol implementation flaws can significantly weaken the overall security posture.

Traditional protocol analysis tools provide packet-level visibility but often require expert interpretation. There is a growing need for intelligent systems capable of automatically analyzing IPsec deployments, identifying protocol characteristics, assessing security risks, and generating actionable recommendations.

#### Problem Description
Design and develop an **AI-driven protocol analysis platform** capable of automatically analysing IPsec VPN deployments established under different security configurations. The platform inspects captured traffic or live network streams, identifies protocol characteristics, infers VPN operating modes, evaluates cryptographic configurations, predicts encapsulated application traffic inside ESP-IPsec, and generates automated security assessment reports.

The solution assists analysts in understanding the security posture of IPsec deployments without requiring manual packet inspection.

---

### Core Functional Capabilities

#### a) VPN Testbed Generation
PrivComm incorporates an automated laboratory environment capable of establishing IPsec VPNs using multiple configurations, supporting:
- **Operational Modes:** Tunnel Mode and Transport Mode
- **Encryption Suites:** AES-128, AES-256, AES-GCM (128/256), AES-CBC (128/256)
- **Integrity & Authentication:** AES-CBC + HMAC-SHA256, HMAC-SHA384, HMAC-SHA512, MD5, SHA-1
- **Key Exchange & DH Groups:** Different DH Groups (MODP Group 2, Group 5, Group 14, ECP Group 19, Group 20, Group 21)
- **Forward Secrecy:** Perfect Forward Secrecy (PFS) enabled vs. PFS disabled
- **Network Protocol Stacks:** Dual-stack IPv4 and IPv6 communication
- **Application Traffic Injected:** VoIP, WhatsApp, E-mail, Web-browsing, ICMP, Video streaming, File Transfer (FT), and P2P

#### b) Traffic Capture
Acquires network traces using tools such as Wireshark, TCP-dump, and custom packet capture utilities. The captured dataset includes:
- **IKE Negotiation:** IKEv1 (Main Mode, Aggressive Mode, Quick Mode) and IKEv2 (IKE_SA_INIT, IKE_AUTH, CREATE_CHILD_SA)
- **ESP Packets:** RFC 4303 Encapsulating Security Payload packets with SPI, sequence numbers, IV, ciphertext, and ICV
- **AH Packets:** RFC 4302 Authentication Header packets (optional support)
- **Normal Communication:** Background and unencrypted payload traffic for comparative flow baselining

#### c) AI-Based Protocol Identification
Develops an AI classification engine capable of automatically identifying:
- **IPsec Protocol & IKE Version:** Automatic discrimination between IKEv1 and modern IKEv2
- **Operating Mode Inference:** Tunnel Mode vs Transport Mode detection
- **Encryption Algorithm:** Extraction of AES-GCM, AES-CBC, ChaCha20-Poly1305, or legacy 3DES/DES
- **Authentication Algorithm:** Detection of HMAC-SHA256, HMAC-SHA384, HMAC-SHA512, MD5, or SHA-1
- **Key Exchange Method:** Group identification across Diffie-Hellman parameters
- **Security Association Characteristics:** SPI mapping, initiator/responder identifiers, sequence state, and lifetime limits
- **Predict Type of Traffic Inside ESP-IPsec:** Uses a trained XGBoost AI classification engine operating on 28 statistical flow features to infer application classes (VoIP, WhatsApp, E-mail, Web-browsing, ICMP, Video streaming) without decrypting ESP payloads.

#### d) Security Assessment
Automatically evaluates:
- **Cryptographic Strength:** Verification of modern AEAD ciphers vs vulnerable CBC block ciphers
- **Configuration Compliance:** Audit against NIST SP 800-77 Rev 1, FIPS 140-3, and NSA CSfC baselines
- **Security Association Parameters:** Validation of key lifetimes, rekeying boundaries, and initiator/responder consistency
- **Key Lifetime:** Detection of over-extended SA lifetimes exceeding safe security bounds
- **Replay Protection:** Verification of anti-replay sequence number windows and detection of duplicate/out-of-order packets
- **Forward Secrecy Configuration:** Auditing whether Perfect Forward Secrecy (PFS) is enforced on Child SAs
- **Cipher Suite Strength:** Detection of deprecated primitives (3DES, MD5, SHA-1, DH Groups < 14)
- **Metadata Exposure:** Evaluation of traffic analysis vulnerability, side-channel leakages, and inner header protection

#### e) Outputs & Deliverables
The framework produces comprehensive assessment outputs:
- **Comprehensive Security Score:** 0–100 benchmark of overall IPsec VPN security posture
- **Traffic Analysis & Metadata Inference:** Flow rate, burstiness, inter-arrival time stats, and predicted ESP application class
- **Executive Report & Technical Report:** Standalone executive HTML reports and granular JSON technical assessments
- **Risk Score & Threat Matrix:** Quantitative risk scoring and calibrated 3x3 Threat Matrix (Likelihood vs Impact)
- **AI Confidence Score:** Probabilistic confidence score for all AI-based protocol and ESP traffic predictions
- **Working Software Prototype:** Production-grade FastAPI backend with high-fidelity React interactive dashboard
- **Interactive Dashboard:** Live and historical inspection, packet stream visualizer, and telemetry monitoring
- **Technical Documentation & Walkthrough:** Comprehensive architectural specs and step-by-step guides
- **Dataset Used for Training/Testing:** `consolidated_traffic_data.csv` (14 encrypted application classes)

---

## System Architecture

The application accepts PCAP/PCAPNG network traces (captured via Wireshark, TCP-dump, or custom capture utilities) through FastAPI, extracts observable IKE, ESP, AH, IP, and flow information, classifies encrypted traffic with the trained XGBoost AI classification engine, evaluates the result against the editable security policy, and exposes JSON and HTML reports to the React frontend.

```text
Wireshark / TCP-dump PCAP or Live Network Stream
                      |
                      v
        TShark / Scapy Packet Ingestion
                      |
                      v
  IKE / ESP Parser & Flow Feature Extraction
                      |
        +-------------+-------------+
        |                           |
        v                           v
AI Classification Engine     Security Policy Engine
(Predicts ESP Traffic)      (Cryptographic Strength & Compliance)
        |                           |
        +-------------+-------------+
                      v
             Report Generator
                      |
       Executive & Technical Reports
  (Security Score, Risk Score, Threat Matrix, AI Confidence)
                      |
                      v
          React Interactive Dashboard
```

TShark is preferred for structured dissection when available, while Scapy provides packet-level fallback and protocol inspection. Encrypted IKE_AUTH and ESP contents remain explicitly protected under the zero-payload inspection model.

---

## Module Reference

- `analyzer/`: Ingests Wireshark/TCP-dump captures and normalizes IKE, ESP, AH, IP, endpoint, mode (Tunnel vs Transport), and flow observations. Primary input is a PCAP path and output is a structured ingest result containing `ipsec` configuration and flow features.
- `security/`: Evaluates policy compliance, finding definitions, risk scoring, recommendations, explainability, replay protection, and post-quantum readiness checks. Consumes normalized IPsec configurations and ML predictions to emit findings, recommendations, comprehensive security scores, and 3x3 threat matrices.
- `ml/`: Loads the trained XGBoost AI classification model and aligns extracted flow features with the 28-column schema. Accepts flow feature dictionaries and returns predicted traffic classes (VoIP, WhatsApp, E-mail, Web-browsing, Video streaming, etc.), AI Confidence Scores, and class probabilities.
- `reports/`: Combines protocol, AI inference, and security outputs into unified JSON Technical Reports and standalone Executive HTML Reports.
- `services/testbed/`: Manages VPN Testbed Generation, scenario definitions, strongSwan configuration generation, VM orchestration, multi-configuration traffic injection (Tunnel/Transport mode, AES-128/256/GCM, DH groups, PFS, IPv4/IPv6), packet capture retrieval, and asynchronous job execution.
- `routers/`: Defines the FastAPI HTTP boundary. `protocol.py` handles PCAP uploads, sample analysis, report generation, history, and AI assistant queries. `testbed.py` exposes scenario execution, capture retrieval, and live job status.
- `db/`: Persistence abstraction for analysis jobs, testbed sessions, and stored PCAP/report artifacts.

---

## Dataset Description

`consolidated_traffic_data.csv` is the source dataset for training and testing the AI traffic classification engine. The target contains 14 classes: `BROWSING`, `CHAT`, `FT`, `MAIL`, `P2P`, `STREAMING`, `VOIP`, and their corresponding `VPN-*` variants (e.g., `VPN-BROWSING`, `VPN-CHAT`, `VPN-FT`, `VPN-MAIL`, `VPN-P2P`, `VPN-STREAMING`, `VPN-VOIP`).

The model uses all 28 feature columns recorded in `models/model_metadata.json`:

```text
duration, total_fiat, total_biat, min_fiat, min_biat, max_fiat, max_biat,
mean_fiat, mean_biat, flowPktsPerSecond, flowBytesPerSecond,
min_flowiat, max_flowiat, mean_flowiat, std_flowiat,
min_active, mean_active, max_active, std_active,
min_idle, mean_idle, max_idle, std_idle, bytes_per_pkt,
fiat_biat_ratio, log_duration, log_bytes_sec, log_pkts_sec
```

Preprocessing loads the raw CSV, separates `traffic_type` from numeric features, handles invalid or missing values, derives rate/ratio/log features, encodes the 14 labels, preserves the feature schema, and writes stratified train (70%), validation (15%), and test (15%) arrays.

---

## AI Model Training & Benchmarks

The production AI classification engine is an XGBoost multi-class gradient-boosted tree model configured with:
- `n_estimators = 400`
- `max_depth = 8`
- `learning_rate = 0.08`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `objective = multi:softprob`
- `num_class = 14`
- `eval_metric = mlogloss`
- Early stopping rounds: 20 (best iteration: 276)
- Validation accuracy: **91.17%**

Comparison models evaluated during benchmarking:
- Random Forest (300 estimators, max depth 20): ~89.7% validation accuracy
- Logistic Regression (standardized features, max_iter=500): ~48.4% validation accuracy

---

## Security Assessment & Policy Engine

`config/security_policy.yaml` is evaluated at runtime to enforce deterministic security audits. Evaluated controls include:
- `POL-01`: Protocol Modernity — Mandates IKEv2; flags deprecated IKEv1.
- `POL-02`: Cryptographic Strength — Evaluates cipher suite strength (requires AES-GCM; flags AES-CBC + HMAC; rejects 3DES/DES).
- `POL-03`: Diffie-Hellman Security — Verifies DH Groups (rejects MODP Group 2, Group 5; mandates Group ≥ 14 or ECP Group 19/20).
- `POL-04`: Perfect Forward Secrecy — Validates PFS configuration across CHILD_SA negotiations.
- `POL-05`: Integrity & PRF Protection — Rejects obsolete MD5 and SHA-1 algorithms; enforces SHA-256+.
- `POL-06`: Operational Encapsulation Mode — Evaluates Tunnel Mode vs Transport Mode (prefers Tunnel Mode to minimize metadata exposure).
- `POL-07`: Key Lifetime & Replay Protection — Validates SA lifetime parameters (default 28,800s) and anti-replay sequence windows.

Findings are weighted (`HIGH=30`, `MEDIUM=15`, `LOW=5`), contributing to the Risk Score and 3x3 Threat Matrix, while compliance score reflects passed vs total checks.

---

## REST API Reference

Protocol routes in `routers/protocol.py`:
| Method | Path | Description & PS Output | Request / Response Shape |
|---|---|---|---|
| POST | `/analyze/protocol` | Analyze uploaded Wireshark/TCP-dump PCAP. | Multipart `pcap_file`; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample` | Analyze bundled compliant IPsec capture. | No body; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample-weak` | Analyze simulated legacy weak IPsec capture. | No body; `ProtocolAnalysisResult`. |
| GET | `/api/report-data` | Read report data for a capture filename. | Query `filename`; JSON report object. |
| GET | `/api/history` | Return analysis history vault. | No body; JSON list. |
| GET | `/reports/download-html` | Download Executive Report (HTML). | Query `filename`; HTML file response. |
| GET | `/reports/download-json` | Download Technical Report (JSON). | Query `filename`; JSON file response. |
| GET | `/api/jobs` | List recent persisted analysis jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/jobs/{job_id}` | Get one persisted analysis job. | Path `job_id`; JSON job record. |
| POST | `/api/chat` | AI-assisted protocol & risk query assistant. | `ChatRequest`; JSON assistant response. |

Testbed routes in `routers/testbed.py`:
| Method | Path | Description & PS Output | Request / Response Shape |
|---|---|---|---|
| GET | `/api/testbed/scenarios` | List built-in VPN testbed scenarios. | No body; list of `ScenarioDefinition`. |
| POST | `/api/testbed/run` | Queue automated multi-configuration testbed run. | `TestbedRunRequest`; queued job id and state. |
| GET | `/api/testbed/jobs` | List testbed execution jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/testbed/jobs/{job_id}` | Read testbed state, logs, and completed results. | Path `job_id`; `TestbedJobStatus`-shaped JSON. |
| GET | `/api/testbed/jobs/{job_id}/pcap`| Download captured testbed PCAP network trace. | Path `job_id`; PCAP file response. |

---

## Deployment & Execution

```bash
# Docker Compose Deployment
docker compose up

# Vagrant Multi-Node strongSwan Testbed
vagrant up

# Local Development Server
pip install -r requirements.txt
cd frontend
npm install
npm run dev
```
