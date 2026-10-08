# PrivComm

PrivComm is an AI-assisted IPsec VPN security intelligence platform. It reads network captures and VPN configuration files, explains what can be observed about an IPsec deployment, classifies encrypted traffic from flow behaviour, checks the observed or configured posture against a security policy, and produces reports for engineers and security reviewers.

The name means privacy communications: the project helps teams understand and improve private network communications without pretending that encrypted traffic reveals information that is not actually observable.

> This README describes the implementation in this repository as it exists today. It is not a promise that every idea in the product documents is available in every deployment.

## What PrivComm does

- **PCAP/PCAPNG analysis**: parses IKE, ESP, NAT-T, IP, TCP, UDP and ICMP evidence using a built-in decoder, Scapy, and optionally TShark.
- **IPsec identification**: infers IKE version, encryption, integrity, Diffie-Hellman group, mode, peer information, ESP activity and related evidence from observed packets.
- **Encrypted-traffic classification**: uses flow statistics and a bundled XGBoost model to estimate broad traffic classes such as browsing, VoIP, file transfer, P2P, chat, mail and streaming, including VPN variants.
- **Behavioural anomaly detection**: scores rolling traffic windows against a learned normal baseline. This is a separate detector from the traffic classifier.
- **Policy and risk assessment**: evaluates cryptographic algorithms, protocol versions, DH groups, integrity, PFS, replay protection and context-aware recommendations using config/security_policy.yaml.
- **Configuration analysis**: understands selected Cisco, Fortinet, pfSense, strongSwan, libreswan and generic configuration formats when the parser can identify them.
- **Controlled testbed**: can orchestrate strongSwan-style initiator, responder and observer nodes, capture traffic, run scenarios and analyse the resulting PCAP.
- **Evidence and reporting**: creates JSON reports, executive HTML reports, PDF reports, batch CSV summaries and a cryptographic bill of materials.
- **Audit sealing**: can create and verify signed Merkle-based seals and generate a compliance certificate for a report's findings.
- **Web application and API**: exposes a FastAPI backend and a Vite/React frontend, with legacy static HTML assets retained for compatibility.

## What PrivComm is not

PrivComm is an analysis and decision-support tool, not a VPN gateway, packet decrypter, intrusion-prevention system or proof of compromise.

- It does not decrypt IKE_AUTH or ESP payloads without the required keys.
- A PCAP cannot prove hidden endpoint configuration. For example, absence of a visible PFS exchange does not prove that PFS is disabled.
- Traffic classification is statistical. A predicted class is not guaranteed identification of a specific application or website.
- An anomaly result indicates deviation from a learned baseline; it does not identify a particular attack.
- Active probing is consent-gated and intended only for explicitly authorised targets.
- Testbed attack simulations are controlled telemetry scenarios, not a production penetration test.

## Architecture

~~~text
                               +-------------------------------------+
                               |   Vite / React 19 Frontend (SPA)    |
                               |    or Static HTML Web Assets        |
                               +------------------+------------------+
                                                  |
                                                  | HTTP / JSON / Multipart
                                                  v
                               +-------------------------------------+
                               |      FastAPI ASGI Application       |
                               |             (main.py)               |
                               +------------------+------------------+
                                                  |
         +-----------------------+----------------+-----------------------+----------------------+
         |                       |                |                       |                      |
         v                       v                v                       v                      v
    Protocol API            Vendor Config    Anomaly API             Testbed API             Seal API
  routers/protocol.py       & Probe APIs   anomaly/routes.py    routers/testbed.py      routers/seal.py
         |                  routers/protocol.py   |                       |                      |
         |                  probe/scanner.py      |                       |                      |
         v                       v                v                       v                      v
  Protocol Engine          Static Lexer/    Behavioral Engine       4-Node Orchestrator    Ed25519 & Merkle
services/protocol_engine   AST Parsers     anomaly/service.py      services/testbed/      seal/engine.py
         |                       |                |                       |                      |
         +-----------------------+----------------+-----------------------+----------------------+
                                                  |
                                                  v
         +---------------------------------------------------------------------------------------+
         |                              Ingestion & Dissection Core                              |
         |  - PCAP Ingestion: TShark dissection + Scapy fallback + Pure-Python binary decoder    |
         |  - RFC 4303: Zero-payload arithmetic block cipher candidate elimination               |
         |  - Vendor Config Parsers: Cisco IOS/ASA, Fortinet, pfSense XML, Libreswan, strongSwan |
         |  - Metadata Exposure: IP leak analysis, transport mode exposure, SPI correlation     |
         +----------------------------------------+----------------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
           +---------------------------+                     +---------------------------+
           |     AI / ML Pipelines     |                     |    Security Assessment    |
           | • Flow Extractor (28 dims)|                     | • NIST SP 800-77 & FIPS   |
           | • XGBoost Flow Classifier |                     | • Mosca Theorem PQC Check |
           |   (14 application classes)|                     | • Drift & Downgrade Track |
           | • IsolationForest Anomaly |                     | • Context Policy Engine   |
           |   (rolling window scoring)|                     | • CVSS / Risk Calculator  |
           | ml/ + anomaly/            |                     | security/ + config/       |
           +-------------+-------------+                     +-------------+-------------+
                         |                                                 |
                         +------------------------+------------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |           Report Builder            |
                               |        reports/report_generator     |
                               +------------------+------------------+
                                                  |
         +-----------------------+----------------+-----------------------+----------------------+
         |                       |                                        |                      |
         v                       v                                        v                      v
  Unified Analysis JSON    Executive Reports                       CycloneDX CBOM         RFC 8032 Audit Seal
  results/*.json           HTML & PDF Downloads                  privcomm.cbom.v1        Ed25519 Signed Merkle
  results/result.json      reports/html_report_generator.py      reports/crypto_bom.py   seal/signer.py
                           reports/pdf_report_generator.py
                                 |
                                 v
         +---------------------------------------------------------------------------------------+
         |                               Data & Persistence Layer                                |
         |   - Supabase PostgreSQL (Cloud RLS, job history, security assessments, audit seals)   |
         |   - Local SQLite / JSON fallback (Offline air-gapped operation in results/*.json)     |
         |   - Storage Service (PCAP and executive report blob synchronization)                  |
         +---------------------------------------------------------------------------------------+
~~~

### End-to-end processing workflows

PrivComm supports five primary operational workflows:

1. **PCAP / PCAPNG network trace analysis (`/analyze/protocol`):**
   - The client uploads a capture file (`.pcap`, `.pcapng`, `.cap`) or the CLI targets a local file.
   - `analyzer.pcap_ingestion` validates capture headers, extracts packet evidence, and computes SHA-256 integrity digests.
   - TShark executes structured protocol dissection, falling back to Scapy and `analyzer.pcap_decoder` (zero-dependency pure-binary decoder).
   - `analyzer.rfc4303` applies modulo block alignment arithmetic to eliminate incompatible cipher candidates without payload decryption.
   - `analyzer.flow_extractor` generates a 28-dimensional statistical flow feature vector from bidirectional packet cadence.
   - `ml.xgboost_adapter` evaluates the 400-tree gradient boosted model, emitting a 14-class probability distribution and traffic classification.
   - `anomaly.service` computes behavioral anomaly scores and top contributing feature deviations across rolling time windows.
   - `security.policy_engine` audits observed proposals against NIST SP 800-77 Rev 1, FIPS 140-3, and `config/security_policy.yaml`.
   - `security.pqc_assessor` applies Mosca's theorem ($X + Y > Z$) and checks RFC 9370 hybrid key exchange readiness.
   - `security.downgrade_baseline` evaluates cryptographic drift against stored tunnel baselines when `tunnel_id` is specified.
   - `reports.report_generator` synthesizes the findings into a 100-point Security Scorecard, 3x3 Threat Matrix, plain-language explanations, executive HTML/PDF documents, and a CycloneDX CBOM (`privcomm.cbom.v1`).
   - Results are committed to Supabase PostgreSQL or local JSON repositories (`results/`).

2. **Vendor firewall configuration auditing (`/analyze/vendor-config`):**
   - Ingests raw configuration text or uploaded files from Cisco IOS/ASA, Fortinet FortiOS, pfSense/OPNsense XML, Libreswan, or strongSwan.
   - `analyzer.vendor_config_parser` constructs an Abstract Syntax Tree (AST), identifies configured IKE/ESP crypto proposals, and detects obsolete algorithms.
   - Generates automated, vendor-specific 1-click remediation hardening CLI playbooks with before/after syntax diffs.

3. **Multi-node strongSwan testbed & attack simulation (`/api/testbed/*`):**
   - Orchestrates an isolated network topology across 4 nodes (VM1 Initiator, VM2 Responder, VM3 Observer, and VM4 Attacker).
   - Generates strongSwan `swanctl.conf` configurations, activates remote `tcpdump` sniffing, triggers live traffic, and pulls resulting PCAPs into the analysis pipeline.
   - `services.testbed.attack_simulator` provides safe, isolated control-plane attack telemetry simulations (MITM identity mismatch, IKE/ESP replay, weak proposal downgrade, and tunnel disruption).

4. **Consent-gated active IKE probing (`/probe/ike`):**
   - Verifies target authorization against an explicit CIDR/IP allowlist (`probe.allowlist`) and requires cryptographic operator consent tokens (`probe.consent`).
   - Dispatches non-destructive IKEv1/IKEv2 Security Association initiation probes to fingerprint responder vendor implementations and supported transform proposals.

5. **Cryptographic audit sealing & attestation (`/api/seal/*`):**
   - Constructs a SHA-256 Merkle tree over canonical analysis findings (`seal.merkle`).
   - Signs the Merkle root using RFC 8032 Ed25519 twisted Edwards curve cryptography (`seal.signer`).
   - Emits tamper-evident verifiable audit certificates proving findings have not drifted or been altered post-inspection.

## Repository layout

| Path | Purpose |
| --- | --- |
| main.py | FastAPI ASGI application, static SPA serving, CLI entry point and top-level lifecycle orchestration. |
| analyzer/ | PCAP ingestion, pure binary decoding, TShark/Scapy wrappers, RFC 4303 cipher arithmetic, flow feature extraction, metadata leakage analysis, and vendor AST parsers. |
| anomaly/ | Behavioral anomaly detection engine, feature adapter, rolling window analyzer, learned baseline metrics, and anomaly REST routes. |
| routers/ | FastAPI HTTP routing: protocol analysis (`protocol.py`), strongSwan testbed operations (`testbed.py`), and audit attestation seals (`seal.py`). |
| services/ | Protocol engine coordination (`services/protocol_engine.py`) and strongSwan multi-node testbed orchestrator (`services/testbed/`). |
| security/ | NIST/FIPS policy engine, risk scoring, recommendations, explainability, baseline drift tracking, Mosca PQC assessment, and LLM assistant. |
| ml/ | Runtime XGBoost model loaders and 28-feature classification adapters. |
| models/ | Pydantic data schemas (`protocol_analysis.py`), XGBoost models (`xgboost_model.json`), and model metadata. |
| traffic-classifier/ | Training pipeline, synthetic data generation, hyperparameter tuning, and evaluation scripts for the 14-class XGBoost model. |
| probe/ | Active IKE handshake scanner, consent token validation, IP allowlist management, and vendor fingerprinting. |
| seal/ | RFC 8032 Ed25519 digital signature generator, Merkle tree builder, and cryptographic compliance attestation engine. |
| reports/ | Unified JSON report compiler, standalone executive HTML generator, PDF generator, and CycloneDX CBOM serializer. |
| db/ | Dual-mode persistence: Supabase PostgreSQL cloud client with RLS, local JSON/SQLite repositories, and object storage synchronization. |
| config/ | Security policy baseline rules (`security_policy.yaml`). |
| services/testbed/ | 4-node scenario definitions, SSH remote automation, live packet capture management, event stream bus, and safe attack simulator. |
| frontend/ | React 19 + Vite dashboard source, Tailwind-free vanilla CSS design system, and telemetry visualization components. |
| index.html, dashboard.html, report.html, style.css, script.js | Root-level static web assets and standalone viewer pages. |
| samples/ | Reference compliant and weak sample PCAP captures for offline testing. |
| results/ | Runtime storage for generated JSON reports, executive HTML/PDF files, CBOMs, and local job databases. |
| tests/ | Comprehensive pytest test suite covering parsers, security engines, ML classifiers, anomaly detection, seals, and testbed. |
| docker/ | Dockerfiles and entrypoint configurations for application containers and testbed nodes. |
| docs/ | Architectural specifications, technical documentation, deployment guides, and policy baselines. |
| utils/ | Cross-cutting helper routines and formatting utilities. |

## Requirements

### Backend

- Python 3.10 or newer. The Docker image uses Python 3.11.
- Packages from requirements.txt, including FastAPI, Uvicorn, Scapy, NumPy, pandas, scikit-learn, XGBoost, PyYAML, report-generation dependencies and test tooling.
- TShark/Wireshark is optional for the local fallback path, but recommended for richer dissection. Set TSHARK_PATH when it is not on PATH.
- Docker is required for container deployment and the Docker testbed.
- Vagrant/VirtualBox may be used for the alternative VM-based testbed described in the project documentation.

### Frontend

- Node.js 20 or newer is the supported container version.
- The frontend uses Vite, React, lucide-react, html2pdf.js and docx.

## Quick start: local backend

From the repository root:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python main.py check-dependencies
python main.py server
~~~

Open http://localhost:8000. FastAPI's interactive API documentation is available at http://localhost:8000/docs.

On macOS/Linux, activate the environment with source .venv/bin/activate. The server command runs Uvicorn on 0.0.0.0:8000; HOST and PORT are documented environment settings, while the current CLI server function uses port 8000 directly.

## Quick start: Docker

~~~bash
cp .env.example .env
docker compose up --build
~~~

Then open http://localhost:8000. The container installs TShark, tcpdump and the native libraries needed by the analysis stack. The compose file persists results/, mounts config/ read-only, and exposes captures/ for local capture data.

Useful checks:

~~~bash
curl http://localhost:8000/health
docker compose logs -f ipsec-analyzer
~~~

The health response reports whether Supabase is enabled and whether the application is using cloud or local storage.

## Quick start: frontend development

Run the backend on port 8000, then in a second terminal:

~~~bash
cd frontend
npm ci
npm run dev -- --host 0.0.0.0
~~~

The Vite development server normally runs at http://localhost:5173. The Docker development stack can run both services:

~~~bash
docker compose -f docker-compose.dev.yml up --build
~~~

The production Dockerfile builds the frontend first and copies frontend/dist into the Python image. FastAPI serves that built SPA when it exists, and otherwise falls back to the root static pages.

## Command-line usage

### Dependency check

~~~bash
python main.py check-dependencies
~~~

Checks the Python version, TShark availability and bundled model artifacts. TShark is reported as optional because the built-in parser can continue without it.

### Analyse one capture

~~~bash
python main.py analyze \
  --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng \
  --output results/sample.json \
  --export-html results/sample_executive_report.html
~~~

The command prints the unified report and optionally writes JSON and executive HTML files.

### Analyse a directory

~~~bash
python main.py batch --input captures --output results
~~~

This processes .pcap and .pcapng files, creates one JSON and one HTML report per capture, and writes summary.csv.

### Inspect a capture schema

~~~bash
python inspect_pcap.py samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng
~~~

inspect_pcap.py is a focused inspection utility for looking at parsed capture data and the traffic-classification input.

### Legacy dashboard command

python main.py dashboard is retained for compatibility, but the repository does not currently contain the dashboard/app.py file that this command expects. Use python main.py server and the FastAPI-served frontend instead.

## API overview

The exact request and response schemas are generated by FastAPI at /docs and /openapi.json. The main routes are:

| Route | Description |
| --- | --- |
| GET /health | Reports application health and storage mode. |
| POST /analyze | Upload a PCAP for protocol, traffic, security and report analysis. Optional tunnel/baseline parameters are supported by the route. |
| GET /analyze/sample | Analyse the bundled sample capture. |
| GET /analyze/sample-weak | Return a deliberately weak assessment variant used for demonstration/testing. It is not a separate capture. |
| POST /analyze/vendor-config | Analyse vendor configuration text supplied as JSON. |
| POST /analyze/vendor-config/upload | Upload a .cfg, .conf, .txt, .xml or .json vendor configuration file. |
| GET /analyze/vendor-config/samples | List example vendor configurations. |
| POST /anomaly/features | Score a feature mapping with the behavioural anomaly detector. |
| POST /anomaly/pcap | Analyse a PCAP in rolling behavioural windows. |
| GET /anomaly/status | Return anomaly model metadata and readiness. |
| GET /anomaly/baseline | Return learned normal medians and IQR values. |
| GET /api/history | Return lightweight analysis history. |
| GET /api/jobs and GET /api/jobs/{job_id} | List or inspect PCAP analysis jobs. |
| GET /reports/download-json | Download a JSON report by filename. |
| GET /reports/download-html | Download an executive HTML report. |
| GET /reports/download-pdf | Generate or download an executive PDF when report data is available. |
| GET /reports/download-cbom | Download the cryptographic bill of materials. |
| POST /probe/ike | Run an active IKE probe only after consent and allowlist checks pass. |
| GET/POST /probe/allowlist | View or add explicitly approved IPv4 probe targets. |
| DELETE /probe/allowlist/remove/{ip} | Remove an allowlisted target. |
| GET /api/testbed/scenarios | List available controlled testbed scenarios. |
| POST /api/testbed/run | Start a testbed scenario job. |
| GET /api/testbed/jobs/{job_id} | Get testbed job state, logs and terminal events. |
| GET /api/testbed/jobs/{job_id}/pcap | Download a PCAP produced by a testbed job. |
| GET/POST /api/testbed/attack-simulations | Start or list safe, isolated attack-telemetry simulation sessions. |
| POST /seal/create, /seal/verify, /seal/attest | Create, verify or attest a signed audit seal. |
| GET /seal/public-key | Return the current public key used for audit-seal verification. |

Most route groups are mounted without a version prefix. Confirm the current OpenAPI document before building a long-lived client.

## Report contents

The unified report produced by reports.report_generator.build_unified_analysis_report contains:

- capture: filename, path, packet count, SHA-256 and decoder errors;
- packet_evidence: frame-level references, timestamps, protocols, offsets and lengths;
- ipsec: observed protocol and tunnel characteristics;
- traffic_classification: predicted class, confidence and model metadata;
- metadata_exposure: endpoint, identity, SPI and transport-mode exposure observations;
- security_assessment: risk score/level, findings and recommendations;
- explainability: plain-language explanations for the observed posture;
- drift_detection: configuration or posture drift indicators where a baseline is available;
- policy_as_code: rule-level policy evaluation;
- post_quantum_readiness: assessment of migration readiness;
- crypto_bom: cryptographic algorithms and related evidence;
- known_limitations: explicit statements about facts that a capture cannot establish.

The report intentionally distinguishes observed evidence, inferred values and unknown values. Reviewers should read known_limitations and evidence status before treating a finding as an endpoint configuration fact.

## Security policy and risk scoring

The baseline is configured in config/security_policy.yaml. The current policy:

- approves IKEv2 and disapproves IKEv1;
- approves AES-GCM, selected AES-CBC values and named AEAD/HMAC-SHA2 forms;
- forbids DES, 3DES, NULL and RC4;
- approves DH groups 14, 19, 20, 21 and 28;
- forbids DH groups 1, 2 and 5;
- forbids MD5 and SHA-1 integrity/PRF forms;
- requires PFS and replay protection;
- defines context-specific guidance for VoIP and file-transfer traffic;
- uses configurable risk weights of 30 for HIGH, 15 for MEDIUM and 5 for LOW findings;
- warns about unknown SA lifetime only if warn_if_unknown is enabled.

Change this YAML when adapting PrivComm to an organisational standard, and review tests under tests/ when changing rule semantics.

## Machine-learning components

### Encrypted traffic classifier

The bundled XGBoost classifier uses flow-level statistics such as duration, packet/byte rates, inter-arrival-time statistics and active/idle periods. The classifier tooling under traffic-classifier/ supports dataset inspection, preprocessing, training, evaluation and sample prediction. The repository also contains a large runtime model artifact under models/.

The model predicts broad dataset labels, including:

BROWSING, VPN-BROWSING, VOIP, VPN-VOIP, FT, VPN-FT, P2P, VPN-P2P, CHAT, VPN-CHAT, MAIL, VPN-MAIL, STREAMING and VPN-STREAMING.

Model output should be interpreted as statistical classification of flow behaviour, not decrypted application identification.

### Behavioural anomaly detector

The anomaly detector is independent from the XGBoost classifier. It uses a calibrated detector, currently represented by an Isolation Forest artifact and robust baseline statistics. It returns normal or anomalous, a ranking score from 0 to 1, severity, and the largest deviations from the learned normal median/IQR baseline.

See ml/anomaly/README.md for the reproducible dataset, training and inference workflow. A typical workflow is:

~~~bash
python -m ml.anomaly.generate_dataset --all --samples 1000 --seed 42
python -m ml.anomaly.train
python -m ml.anomaly.predict --features '{"duration_sec":60,"packet_count":100}'
~~~

The short JSON above is only a shape example; prediction requires the complete feature schema in models/feature_schema.json.

## Controlled testbed

The testbed stack is defined in docker-compose.testbed.yml and contains:

- vm1-initiator at 192.168.56.10;
- vm2-responder with interfaces on both testbed networks;
- vm3-observer at the network boundary, used for forwarding and capture;
- vm4-attacker for controlled telemetry simulations.

Nodes use NET_ADMIN and NET_RAW capabilities because the testbed creates routes, IPsec traffic and captures. Do not expose this stack to an untrusted network.

Start it with:

~~~bash
docker compose -f docker-compose.testbed.yml up --build -d
~~~

Then use the testbed API or scenario tooling. Testbed jobs move through QUEUED, PROVISIONING, CAPTURING, ANALYZING, COMPLETED and FAILED. The generated PCAP can be downloaded and passed through the same analysis pipeline as any other capture.

## Configuration

Copy .env.example to .env. Important settings include:

| Variable | Meaning |
| --- | --- |
| HOST / PORT | Deployment settings documented for the server. |
| TSHARK_PATH | Optional path to the TShark executable. |
| SECURITY_POLICY_PATH | YAML policy baseline; defaults to config/security_policy.yaml. |
| SUPABASE_URL | Optional Supabase project URL. |
| SUPABASE_ANON_KEY | Optional Supabase anonymous key. |
| SUPABASE_SERVICE_ROLE_KEY | Optional server-side Supabase service-role key. Keep it secret. |
| LLM_BASE_URL, LLM_API_KEY, LLM_MODEL | Optional OpenAI-compatible proxy settings for the backend assistant/explanation path. |
| GEMINI_API_KEY, GEMINI_MODEL | Optional direct Gemini settings. |
| VITE_POLLINATIONS_API_KEY | Optional frontend key for the Cyber Sentinel assistant integration. |

Without Supabase, job/history persistence falls back to local JSON files. Do not commit a real .env file or any API key.

## Optional cloud and AI integrations

The core deterministic parser and policy engine do not require an LLM or cloud database. Supabase is optional. The frontend assistant can call Pollinations.ai and has a local response fallback when the network is unavailable. Backend assistant configuration supports an OpenAI-compatible proxy and Gemini settings where the relevant code path is enabled.

Treat any external AI service as a data-sharing boundary. Captures, configuration text and report context may contain sensitive infrastructure metadata; configure network access and redaction according to your organisation's policy.

## Testing and quality checks

Run the automated tests from the repository root:

~~~bash
python -m pytest
~~~

The test suite covers protocol parsing, PCAP decoding, security rules, policy overlays, explainability, metadata exposure, vendor configurations, anomaly inference, XGBoost adaptation, active-probe consent, provenance, tunnel hashing, report seals and testbed helpers.

For linting and security checks, the project configuration includes Ruff and Bandit settings:

~~~bash
ruff check .
bandit -r . -x tests,frontend,node_modules,.pytest_temp
~~~

Build the frontend separately when changing React code:

~~~bash
cd frontend
npm ci
npm run build
~~~

## Active probing safety model

The IKE probe endpoint uses two barriers before sending a probe:

1. a valid, explicit consent token; and
2. an exact IPv4 target in the active allowlist.

The probe request also records an operator note and performs vendor fingerprinting from the response. Use this only against systems you own or are authorised to assess. The allowlist is a safety control, not a legal authorisation mechanism.

## Audit seals and provenance

The seal/ package provides a tamper-evident packaging layer:

1. findings are canonicalised into Merkle-tree leaves;
2. a Merkle root is calculated;
3. the root and metadata are signed;
4. a seal is stored under the local seals/ directory;
5. later verification checks the signature, root and supplied findings;
6. an attestation endpoint can emit a compliance certificate and mark it VALID or TAMPERED.

The public key is available through the seal API. Preserve the private key securely and separately from report artifacts in any real deployment.

## Operational and security notes

Before deploying beyond a local development environment, review these implementation details:

- FastAPI currently enables permissive CORS with allow_origins=["*"]; place the service behind an authenticated gateway or tighten CORS for production.
- The repository contains upload, report-download, probing and testbed-control endpoints. Add authentication, authorisation, rate limiting and audit logging before exposing them to untrusted users.
- Store Supabase service credentials and LLM/API keys outside source control.
- Treat PCAPs, vendor configs, generated reports and job-history JSON as sensitive data.
- Run the testbed in an isolated network. Its containers receive elevated network capabilities.
- Verify generated reports and seals before using them as compliance evidence.
- Keep model artifacts and policy files versioned together with their metadata so results can be reproduced.

## Known implementation boundaries

- IKEv2 SA lifetime is generally negotiated inside encrypted IKE_AUTH payloads and is not available from a normal unauthenticated PCAP.
- Observed ESP sequence numbers do not establish the configured anti-replay window.
- PFS policy enforcement cannot always be concluded from whether a CREATE_CHILD_SA exchange is visible.
- A traffic class is based on flow behaviour and dataset labels; it is not a decrypted payload label.
- The sample-weak endpoint intentionally mutates the sample result to demonstrate a weak posture.
- The root results/ and captures/ directories are runtime/output locations, not canonical source data.
- The CLI's dashboard subcommand references a missing legacy dashboard/app.py; the maintained web path is the FastAPI server plus the Vite frontend.

## Further documentation

- docs/TECHNICAL_DOCUMENTATION.md — deeper implementation and API context.
- docs/SECURITY_POLICY_OVERLAYS_AND_BASELINES.md — policy and baseline details.
- docs/WEB_APP_DEPLOYMENT_CONTEXT.md — deployment context for the web application.
- docs/IMPLEMENTATION_PLAN_GAP_CLOSURE.md — implementation and gap-closure notes.
- ml/anomaly/README.md — anomaly dataset, training and inference workflow.
- traffic-classifier/README.md — encrypted-traffic classifier pipeline.

## Contributing

When changing a parser, policy rule, model schema or report field:

1. update or add focused tests under tests/;
2. document whether the value is observed, inferred or unknown;
3. preserve evidence references and known limitations;
4. run the test suite and relevant lint/security checks;
5. update this README or linked technical documentation when the public workflow changes.

## License and ownership

No license file is currently present in the repository. Confirm the intended licence and contribution terms with the project owner before redistributing PrivComm or accepting external contributions.
