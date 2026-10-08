# IPsec Analyzer Technical Documentation

## System Architecture

The application accepts PCAP/PCAPNG capture files, live network traffic, or static firewall configuration files through FastAPI, extracts observable IKE, ESP, AH, IP, and flow information without payload decryption, evaluates RFC 4303 arithmetic block cipher elimination, classifies encrypted traffic with the trained 28-feature XGBoost model, checks behavioral anomalies using IsolationForest rolling windows, audits the deployment against NIST SP 800-77 / FIPS 140-3 policies and Mosca theorem post-quantum readiness, creates RFC 8032 Ed25519 Merkle tree audit proofs, generates CycloneDX CBOMs, and exposes JSON, HTML, PDF, and interactive React telemetry to engineers and security reviewers.

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

TShark is preferred for structured dissection when available, while Scapy and `analyzer.pcap_decoder` provide packet-level fallback and zero-dependency inspection. Encrypted IKE_AUTH and ESP contents remain strictly protected under a zero-payload model: no payloads are decrypted, and cipher properties are inferred through negotiation proposals, RFC 4303 block length modulo arithmetic, and statistical flow dynamics.

## Module Reference

`analyzer/` ingests captures, parses raw frames, and normalizes IKE, ESP, AH, IP, endpoint, mode, and flow observations. Submodules include `pcap_decoder.py` (pure binary decoder), `rfc4303.py` (arithmetic cipher elimination), `flow_extractor.py` (28 statistical flow features), `metadata_exposure.py` (passive privacy exposure metrics), and `vendor_config_parser.py` (Cisco, Fortinet, pfSense, Libreswan, strongSwan configuration parser and hardened remediation generator).

`anomaly/` hosts the behavioral anomaly detection engine. It extracts rolling-window time series features (`feature_adapter.py`), executes IsolationForest scoring against calibrated normal baselines (`service.py`), identifies top contributing feature deviations, and exposes REST endpoints (`routes.py`).

`security/` contains policy evaluation, finding definitions, risk scoring, recommendations, explainability, drift detection, post-quantum readiness checks, and LLM-assisted explanations (`llm_explainer.py`). Submodules include `policy_engine.py` (NIST SP 800-77 rules), `pqc_assessor.py` (Mosca theorem and RFC 9370 hybrid key exchange checks), `downgrade_baseline.py` (cryptographic drift tracking), and `risk.py` (3x3 Threat Matrix).

`ml/` loads the trained XGBoost model artifacts (`model_loader.py`) and aligns extracted flow features with the 28-column model schema (`xgboost_adapter.py`). It accepts a feature dictionary and returns the predicted traffic class, calibrated confidence, and softprob probability vector.

`seal/` implements cryptographic attestation and audit proofs. It constructs a canonical SHA-256 Merkle tree over analysis findings (`merkle.py`), signs the Merkle root using RFC 8032 Ed25519 cryptography (`signer.py`), generates compliance certificates (`attestation.py`), and provides verification routes (`engine.py`).

`probe/` provides active IKE handshake discovery. It enforces cryptographic operator consent validation (`consent.py`), strict CIDR/IP allowlist filtering (`allowlist.py`), and non-destructive IKEv1/IKEv2 Security Association probing and vendor fingerprinting (`scanner.py`, `fingerprint.py`).

`reports/` combines protocol, ML, and security outputs into unified JSON, standalone executive HTML reports (`html_report_generator.py`), high-fidelity PDF documents (`pdf_report_generator.py`), and CycloneDX-compatible Cryptographic Bills of Materials (`crypto_bom.py`).

`services/testbed/` coordinates the automated strongSwan VPN testbed across 4 isolated nodes (Initiator, Responder, Observer, Attacker). It manages configuration generation (`config_generator.py`), remote SSH control (`ssh_controller.py`), packet capture management (`capture_manager.py`), live event publishing (`event_store.py`), and safe control-plane attack simulations (`attack_simulator.py`).

`routers/` defines the FastAPI HTTP boundary. `protocol.py` handles PCAP and vendor config analysis, report downloads, history, jobs, and chat assistant queries. `testbed.py` handles scenario execution and attack telemetry. `seal.py` handles audit seal creation, verification, and public keys.

`db/` provides the dual-mode persistence abstraction for analysis jobs, testbed jobs, and report artifacts. It supports Supabase PostgreSQL with Row-Level Security (`supabase_client.py`) and auto-falls back to local JSON/SQLite databases (`repository.py`).

## Dataset Description

`consolidated_traffic_data.csv` is the source dataset for encrypted traffic classification. The target contains 14 classes: `BROWSING`, `CHAT`, `FT`, `MAIL`, `P2P`, `STREAMING`, `VOIP`, and the corresponding `VPN-*` variants.

The model uses all 28 feature columns recorded in `models/model_metadata.json`:

```text
duration, total_fiat, total_biat, min_fiat, min_biat, max_fiat, max_biat,
mean_fiat, mean_biat, flowPktsPerSecond, flowBytesPerSecond,
min_flowiat, max_flowiat, mean_flowiat, std_flowiat,
min_active, mean_active, max_active, std_active,
min_idle, mean_idle, max_idle, std_idle, bytes_per_pkt,
fiat_biat_ratio, log_duration, log_bytes_sec, log_pkts_sec
```

Preprocessing loads the raw CSV, separates `traffic_type` from numeric features, handles invalid or missing values, derives rate/ratio/log features, encodes the 14 labels, preserves the feature schema, and writes stratified train, validation, and test arrays to the processed NPZ artifact.

## ML Model Training

The production model is XGBoost with `n_estimators=400`, `max_depth=8`, `learning_rate=0.08`, `subsample=0.8`, `colsample_bytree=0.8`, objective `multi:softprob`, `num_class=14`, `eval_metric=mlogloss`, `random_state=42`, and histogram tree construction. Early stopping is configured for 20 rounds. The recorded best iteration is 276.

The split is 70% training, 15% validation, and 15% test. Training uses balanced sample weights and evaluates on the validation set during boosting. The training script also fits comparison models: Random Forest uses 300 trees, max depth 20, balanced class weights, and seed 42; Logistic Regression uses standardized features and `max_iter=500`. In the recorded metadata, Random Forest validation accuracy is approximately 0.897 and Logistic Regression validation accuracy is approximately 0.484. XGBoost uses multiclass log loss as its evaluation metric; the metadata does not record a comparable XGBoost accuracy value.

## Security Policy Engine

`config/security_policy.yaml` is loaded at runtime. Edit the approved/forbidden cipher lists, DH groups, integrity and PRF requirements, protocol versions, PFS/replay requirements, traffic-specific baselines, risk weights, or the `sa_lifetime` block, then restart the API process. The lifetime default is 28,800 seconds and unknown lifetimes are reported as `not_observable`, never as an insecure value.

The policy-as-code controls are:

- `POL-01` checks protocol modernity and requires IKEv2.
- `POL-02` checks encryption strength and flags prohibited or non-AEAD ciphers.
- `POL-03` checks the Diffie-Hellman group and rejects weak groups.
- `POL-04` checks whether Perfect Forward Secrecy is enforced.
- `POL-05` rejects obsolete MD5 and SHA-1 integrity/PRF algorithms.
- `POL-06` checks encapsulation mode and prefers tunnel mode because it hides inner network addressing.

The primary security evaluator emits findings with severity weights from the policy (`HIGH=30`, `MEDIUM=15`, `LOW=5`). The risk module sums finding weights and clamps the result to the application’s 0-100 scale, while the policy-as-code report separately calculates a compliance score as passed rules divided by total rules.

## API Endpoints Reference

### Protocol & Ingestion Routes (`routers/protocol.py`)

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| POST | `/analyze/protocol` | Analyze an uploaded PCAP/PCAPNG with optional baseline recording. | Multipart `pcap_file`, queries `tunnel_id`, `record_baseline`; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample` | Analyze the bundled compliant sample capture. | No body; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample-weak` | Return simulated weak legacy IPsec assessment. | No body; `ProtocolAnalysisResult`. |
| POST | `/analyze/vendor-config` | Parse raw firewall configuration text (Cisco, Fortinet, pfSense, strongSwan). | JSON `{config_text, filename, vendor}`; `ProtocolAnalysisResult`. |
| POST | `/analyze/vendor-config/upload` | Upload a configuration file for parsing and remediation. | Multipart `config_file`, form `vendor`; `ProtocolAnalysisResult`. |
| GET | `/analyze/vendor-config/samples` | List bundled sample configuration templates. | No body; JSON dictionary of sample configs. |
| GET | `/api/report-data` | Read report data for a capture filename. | Query `filename`; JSON report object. |
| GET | `/api/history` | Return in-memory analysis history. | No body; JSON list. |
| GET | `/reports/download-html` | Download an executive HTML report. | Query `filename`; HTML file response. |
| GET | `/reports/download-pdf` | Download an executive PDF report. | Query `filename`; PDF file response. |
| GET | `/reports/download-json` | Download a JSON technical report. | Query `filename`; JSON file response. |
| GET | `/reports/download-cbom` | Download a CycloneDX Cryptographic Bill of Materials. | Query `filename`; JSON file response (`privcomm.cbom.v1`). |
| GET | `/api/jobs` | List recent persisted PCAP analysis jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/jobs/{job_id}` | Get one persisted analysis job by ID. | Path `job_id`; JSON job record. |
| POST | `/api/chat` | Ask the AI Sentinel assistant a protocol/risk question. | `ChatRequest`; JSON assistant response. |

### Active IKE Probing Routes (`routers/protocol.py` + `probe/`)

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| POST | `/probe/ike` | Run a consent-gated active IKE handshake probe. | `IkeProbeRequest` with consent token; `IkeProbeResult`. |
| GET | `/probe/allowlist` | List active authorized probe targets. | No body; JSON list of allowed CIDR/IP targets. |
| POST | `/probe/allowlist/add` | Add an exact IP to the authorized probe allowlist. | JSON `{ip: string}`; JSON success response. |
| DELETE | `/probe/allowlist/remove/{ip}` | Remove an IP from the probe allowlist. | Path `ip`; JSON success response. |

### Behavioral Anomaly Routes (`anomaly/routes.py`)

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| GET | `/api/anomaly/status` | Get IsolationForest model status, threshold, and feature schema. | No body; `AnomalyModelStatus`. |
| GET | `/api/anomaly/baseline` | Get learned normal baseline metrics (median, IQR) for 32 features. | No body; list of `AnomalyBaselineMetric`. |
| POST | `/api/anomaly/predict` | Run anomaly detection on a single flow feature dictionary. | JSON feature vector; `AnomalyPredictionResult`. |
| POST | `/api/anomaly/analyze-pcap` | Analyze rolling time windows across an entire PCAP capture. | Multipart `pcap_file`, query `window_sec`; `AnomalyPcapAnalysisResponse`. |

### Cryptographic Audit Seal Routes (`routers/seal.py`)

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| POST | `/api/seal/create` | Generate an RFC 8032 Ed25519-signed Merkle tree audit seal. | JSON `SealRequest` (findings/report claims); `AuditSeal`. |
| POST | `/api/seal/verify` | Verify a signed Merkle audit seal against claim data. | JSON `VerifySealRequest`; `VerifySealResponse` with boolean validity. |
| POST | `/api/seal/attest` | Generate a compliance attestation certificate from a seal. | JSON `{seal: AuditSeal}`; JSON compliance certificate. |
| GET | `/api/seal/public-key` | Retrieve the active Ed25519 verification public key. | No body; JSON `{public_key: string}`. |

### Multi-Node Testbed Routes (`routers/testbed.py`)

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| GET | `/api/testbed/scenarios` | List built-in scenario definitions (Tunnel/Transport, AES-GCM, DH). | No body; list of `ScenarioDefinition`. |
| POST | `/api/testbed/run` | Queue an automated asynchronous strongSwan scenario execution. | `TestbedRunRequest`; queued job ID and initial state. |
| GET | `/api/testbed/jobs` | List testbed execution jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/testbed/jobs/{job_id}` | Read testbed execution state, streaming logs, and PCAP result. | Path `job_id`; `TestbedJobStatus`-shaped JSON. |
| GET | `/api/testbed/jobs/{job_id}/pcap` | Download the PCAP captured from the Observer node. | Path `job_id`; PCAP file response. |
| GET / POST | `/api/testbed/check-nodes` | Test SSH and reachability across testbed nodes. | Optional topology JSON; node reachability status. |
| GET | `/api/testbed/attack-simulations` | List supported attack telemetry simulations and active sessions. | No body; JSON attack options and sessions. |
| POST | `/api/testbed/attack-simulations` | Launch a safe control-plane attack simulation (MITM, replay, downgrade). | `AttackSimulationRequest`; `AttackSimulation` state. |
| POST | `/api/testbed/attack-simulations/{session_id}/stop` | Terminate an active attack telemetry simulation. | Path `session_id`; JSON stopped status. |

## Deployment Guide

For Docker deployment, configure the environment file and start the stack:

```bash
docker compose up
```

For the Vagrant strongSwan testbed, install the required virtualization provider and run:

```bash
vagrant up
```

For local development, install the Python dependencies and start the frontend development server:

```bash
pip install -r requirements.txt
cd frontend
npm install
npm run dev
```

The backend reads environment settings from `.env.example` as the project template. The important settings include database/storage configuration, `SECURITY_POLICY_PATH`, API host/port settings, and optional object-storage credentials used by `db/storage.py`. Copy the template to `.env` and provide values appropriate for the local or container environment; do not commit secrets.

The React development server proxies API calls to the FastAPI service according to the frontend configuration. In production, serve the built frontend and run FastAPI behind the deployment’s reverse proxy or container service.
