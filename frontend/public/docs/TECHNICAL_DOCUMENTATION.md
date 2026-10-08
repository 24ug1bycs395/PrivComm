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

The application accepts PCAP/PCAPNG network traces (captured via Wireshark, TCP-dump, or custom capture utilities), live network streams, or static firewall configurations (Cisco, Fortinet, pfSense, Libreswan, strongSwan) through FastAPI, extracts observable IKE, ESP, AH, IP, and flow information without payload decryption, evaluates RFC 4303 arithmetic block cipher elimination, classifies encrypted traffic with the trained XGBoost AI classification engine, checks behavioral anomalies using IsolationForest rolling windows, evaluates security posture against NIST SP 800-77 / FIPS 140-3 policies and Mosca post-quantum readiness, creates RFC 8032 Ed25519 Merkle tree audit proofs, generates CycloneDX CBOMs, and exposes JSON, HTML, PDF, and interactive React telemetry to engineers and security reviewers.

```text
               +-----------------------------------------------------------+
               |        Network Capture (PCAP/PCAPNG) / Live Stream        |
               |        or Firewall Configurations (Cisco/Fortinet/pfSense)|
               +-----------------------------+-----------------------------+
                                             |
                                             v
               +-----------------------------------------------------------+
               |                 Packet Ingestion & Parsing                |
               |    - TShark Dissector / Scapy Engine / Binary Decoder     |
               |    - Vendor Config AST Lexer (Cisco, Fortinet, pfSense)   |
               |    - SHA-256 Capture Integrity Digest                     |
               +-----------------------------+-----------------------------+
                                             |
                                             v
               +-----------------------------------------------------------+
               |              Zero-Payload Protocol Dissection             |
               |    - IKEv1 / IKEv2 Handshake & Transform Extraction       |
               |    - Operational Mode Inference (Tunnel vs Transport)     |
               |    - RFC 4303 Block Alignment Cipher Elimination          |
               |    - Observable Metadata Exposure & Leakage Scoring       |
               +-----------------------------+-----------------------------+
                                             |
                      +----------------------+----------------------+
                      |                                             |
                      v                                             v
        +---------------------------+                 +---------------------------+
        |   AI & Anomaly Analysis   |                 |    Security Evaluation    |
        | • Flow Extractor (28 dims)|                 | • NIST SP 800-77 Rev 1    |
        | • XGBoost Flow Classifier |                 | • FIPS 140-3 Cryptography |
        |   (14 application classes)|                 | • Mosca PQC (X + Y > Z)   |
        | • IsolationForest Anomaly |                 | • Baseline Drift Tracking |
        |   (rolling window scores) |                 | • 3x3 Threat Risk Matrix  |
        +-------------+-------------+                 +-------------+-------------+
                      |                                             |
                      +----------------------+----------------------+
                                             |
                                             v
               +-----------------------------------------------------------+
               |                 Report & Attestation Engine               |
               |    - 100-Point Security Scorecard & Risk Findings         |
               |    - CycloneDX Cryptographic Bill of Materials (CBOM)     |
               |    - RFC 8032 Ed25519 Merkle Tree Audit Proofs            |
               |    - Automated 1-Click Hardened Remediation CLI Diffs     |
               |    - Executive HTML & High-Fidelity PDF Generation        |
               +-----------------------------+-----------------------------+
                                             |
                      +----------------------+----------------------+
                      |                                             |
                      v                                             v
        +---------------------------+                 +---------------------------+
        |  Persistence & History    |                 |   Analyst Presentation   |
        | • Supabase PostgreSQL     |                 | • React 19 / Vite UI      |
        |   (RLS & Cloud Vault)     |                 | • REST API Endpoints      |
        | • Local SQLite / JSON     |                 | • AI Sentinel Assistant   |
        | • Blob / Storage Service  |                 | • Testbed Remote Control  |
        +---------------------------+                 +---------------------------+
```

TShark is preferred for structured dissection when available, while Scapy and `analyzer.pcap_decoder` provide packet-level fallback and protocol inspection. Encrypted IKE_AUTH and ESP contents remain explicitly protected under the zero-payload inspection model: no payloads are decrypted, and cipher properties are inferred through negotiation proposals, RFC 4303 block length modulo arithmetic, and statistical flow dynamics.

---

## Module Reference

- `analyzer/`: Ingests Wireshark/TCP-dump captures, parses raw frames with pure-binary decoders, evaluates RFC 4303 arithmetic cipher elimination, extracts 28 statistical flow features, quantifies metadata exposure, and parses vendor configs (Cisco, Fortinet, pfSense, Libreswan, strongSwan) with automated remediation diff generation.
- `anomaly/`: Executes behavioral anomaly detection on encrypted flows via IsolationForest and rolling time-window scoring against learned baseline metrics (median, IQR) for 32 features.
- `security/`: Evaluates policy compliance against NIST SP 800-77 and FIPS 140-3, risk scoring, recommendations, explainability, baseline drift tracking, Mosca theorem post-quantum readiness checks, and LLM-assisted explanations.
- `ml/`: Loads the trained XGBoost AI classification model and aligns extracted flow features with the 28-column schema to predict 14 application traffic classes with calibrated AI Confidence Scores.
- `seal/`: Implements cryptographic audit seals via RFC 8032 Ed25519 digital signatures and SHA-256 Merkle tree verification proofs.
- `probe/`: Active IKE handshake scanner with strict operator consent validation and CIDR/IP allowlist filtering.
- `reports/`: Combines protocol, AI inference, and security outputs into unified JSON Technical Reports, standalone Executive HTML Reports, PDF downloads, and CycloneDX CBOMs (`privcomm.cbom.v1`).
- `services/testbed/`: Manages automated strongSwan testbeds across a 4-node topology (Initiator, Responder, Observer, Attacker), scenario generation, traffic injection, live PCAP retrieval, and safe control-plane attack simulations.
- `routers/`: FastAPI HTTP boundary: protocol analysis (`protocol.py`), strongSwan testbed operations (`testbed.py`), and audit attestation seals (`seal.py`).
- `db/`: Dual-mode persistence abstraction supporting Supabase PostgreSQL with Row-Level Security (RLS) and local SQLite/JSON databases.

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

### Protocol & Ingestion Routes (`routers/protocol.py`)
| Method | Path | Description & PS Output | Request / Response Shape |
|---|---|---|---|
| POST | `/analyze/protocol` | Analyze uploaded Wireshark/TCP-dump PCAP with optional baseline tracking. | Multipart `pcap_file`, queries `tunnel_id`, `record_baseline`; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample` | Analyze bundled compliant IPsec capture. | No body; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample-weak` | Analyze simulated legacy weak IPsec capture. | No body; `ProtocolAnalysisResult`. |
| POST | `/analyze/vendor-config` | Parse raw firewall configuration text (Cisco, Fortinet, pfSense, strongSwan). | JSON `{config_text, filename, vendor}`; `ProtocolAnalysisResult`. |
| POST | `/analyze/vendor-config/upload` | Upload a configuration file for parsing and remediation. | Multipart `config_file`, form `vendor`; `ProtocolAnalysisResult`. |
| GET | `/analyze/vendor-config/samples` | List bundled sample configuration templates. | No body; JSON dictionary of sample configs. |
| GET | `/api/report-data` | Read report data for a capture filename. | Query `filename`; JSON report object. |
| GET | `/api/history` | Return analysis history vault. | No body; JSON list. |
| GET | `/reports/download-html` | Download Executive Report (HTML). | Query `filename`; HTML file response. |
| GET | `/reports/download-pdf` | Download Executive Report (PDF). | Query `filename`; PDF file response. |
| GET | `/reports/download-json` | Download Technical Report (JSON). | Query `filename`; JSON file response. |
| GET | `/reports/download-cbom` | Download CycloneDX Cryptographic Bill of Materials. | Query `filename`; JSON file response (`privcomm.cbom.v1`). |
| GET | `/api/jobs` | List recent persisted analysis jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/jobs/{job_id}` | Get one persisted analysis job. | Path `job_id`; JSON job record. |
| POST | `/api/chat` | AI-assisted protocol & risk query assistant. | `ChatRequest`; JSON assistant response. |

### Active IKE Probing Routes (`routers/protocol.py` + `probe/`)
| Method | Path | Description | Request / Response Shape |
|---|---|---|---|
| POST | `/probe/ike` | Run a consent-gated active IKE handshake probe. | `IkeProbeRequest` with consent token; `IkeProbeResult`. |
| GET | `/probe/allowlist` | List active authorized probe targets. | No body; JSON list of allowed CIDR/IP targets. |
| POST | `/probe/allowlist/add` | Add an exact IP to the authorized probe allowlist. | JSON `{ip: string}`; JSON success response. |
| DELETE | `/probe/allowlist/remove/{ip}` | Remove an IP from the probe allowlist. | Path `ip`; JSON success response. |

### Behavioral Anomaly Routes (`anomaly/routes.py`)
| Method | Path | Description | Request / Response Shape |
|---|---|---|---|
| GET | `/api/anomaly/status` | Get IsolationForest model status, threshold, and feature schema. | No body; `AnomalyModelStatus`. |
| GET | `/api/anomaly/baseline` | Get learned normal baseline metrics (median, IQR) for 32 features. | No body; list of `AnomalyBaselineMetric`. |
| POST | `/api/anomaly/predict` | Run anomaly detection on a single flow feature dictionary. | JSON feature vector; `AnomalyPredictionResult`. |
| POST | `/api/anomaly/analyze-pcap` | Analyze rolling time windows across an entire PCAP capture. | Multipart `pcap_file`, query `window_sec`; `AnomalyPcapAnalysisResponse`. |

### Cryptographic Audit Seal Routes (`routers/seal.py`)
| Method | Path | Description | Request / Response Shape |
|---|---|---|---|
| POST | `/api/seal/create` | Generate an RFC 8032 Ed25519-signed Merkle tree audit seal. | JSON `SealRequest` (findings/report claims); `AuditSeal`. |
| POST | `/api/seal/verify` | Verify a signed Merkle audit seal against claim data. | JSON `VerifySealRequest`; `VerifySealResponse`. |
| POST | `/api/seal/attest` | Generate a compliance attestation certificate from a seal. | JSON `{seal: AuditSeal}`; JSON compliance certificate. |
| GET | `/api/seal/public-key` | Retrieve the active Ed25519 verification public key. | No body; JSON `{public_key: string}`. |

### Multi-Node Testbed Routes (`routers/testbed.py`)
| Method | Path | Description & PS Output | Request / Response Shape |
|---|---|---|---|
| GET | `/api/testbed/scenarios` | List built-in VPN testbed scenarios. | No body; list of `ScenarioDefinition`. |
| POST | `/api/testbed/run` | Queue automated multi-configuration testbed run. | `TestbedRunRequest`; queued job id and state. |
| GET | `/api/testbed/jobs` | List testbed execution jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/testbed/jobs/{job_id}` | Read testbed state, logs, and completed results. | Path `job_id`; `TestbedJobStatus`-shaped JSON. |
| GET | `/api/testbed/jobs/{job_id}/pcap`| Download captured testbed PCAP network trace. | Path `job_id`; PCAP file response. |
| GET / POST | `/api/testbed/check-nodes` | Test SSH and reachability across testbed nodes. | Optional topology JSON; node reachability status. |
| GET | `/api/testbed/attack-simulations` | List supported attack telemetry simulations and active sessions. | No body; JSON attack options and sessions. |
| POST | `/api/testbed/attack-simulations` | Launch a safe control-plane attack simulation (MITM, replay, downgrade). | `AttackSimulationRequest`; `AttackSimulation` state. |
| POST | `/api/testbed/attack-simulations/{session_id}/stop` | Terminate an active attack telemetry simulation. | Path `session_id`; JSON stopped status. |

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
