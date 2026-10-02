# IPsec Analyzer Technical Documentation

## System Architecture

The application accepts PCAP/PCAPNG files through FastAPI, extracts observable IKE, ESP, AH, IP, and flow information, classifies encrypted traffic with the trained XGBoost adapter, evaluates the result against the editable security policy, and exposes JSON and HTML reports to the React frontend.

```text
PCAP / PCAPNG
      |
      v
TShark / Scapy packet ingestion
      |
      v
IKE / ESP parser and flow feature extraction
      |
      +----------------------+
      |                      |
      v                      v
XGBoost adapter       Security Policy Engine
      |                      |
      +----------+-----------+
                 v
          Report Generator
                 |
        JSON / HTML assessment
                 |
                 v
              React UI
```

TShark is preferred for structured dissection when available, while Scapy provides packet-level fallback and protocol inspection. Encrypted IKE_AUTH and ESP contents remain explicitly marked as unobservable unless the required decryption material is supplied.

## Module Reference

`analyzer/` ingests captures and normalizes IKE, ESP, AH, IP, endpoint, mode, and flow observations. Its primary input is a PCAP path and its output is a structured ingest result containing `ipsec` configuration and flow features.

`security/` contains policy evaluation, finding definitions, risk scoring, recommendations, explainability, drift detection, and post-quantum readiness checks. It consumes the normalized IPsec configuration and traffic classification, then emits findings, recommendations, scores, and assessment metadata.

`ml/` loads the trained XGBoost artifacts and aligns extracted flow features with the 28-column model schema. It accepts a feature dictionary and returns the predicted traffic class, confidence, and model status.

`reports/` combines protocol, ML, and security outputs into unified JSON and standalone executive HTML reports. Inputs are the ingest result, traffic prediction, findings, recommendations, and risk result; outputs are persisted report files and report dictionaries.

`services/testbed/` manages scenario definitions, strongSwan configuration generation, VM orchestration, traffic injection, packet capture retrieval, and asynchronous testbed jobs. It consumes a scenario and topology and produces a captured PCAP, job status, and analysis result.

`routers/` defines the FastAPI HTTP boundary. `protocol.py` handles uploads, sample analysis, report access, history, jobs, and assistant requests. `testbed.py` exposes scenario execution and job/PCAP management.

`db/` provides the persistence abstraction for analysis jobs, testbed jobs, and stored PCAP/report artifacts. It accepts serialized result dictionaries and returns saved records, lists, or download locations.

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

Protocol routes are registered by `routers/protocol.py`:

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| POST | `/analyze/protocol` | Analyze an uploaded PCAP/PCAPNG. | Multipart `pcap_file`; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample` | Analyze the bundled compliant sample. | No body; `ProtocolAnalysisResult`. |
| GET | `/analyze/sample-weak` | Return the simulated weak legacy assessment. | No body; `ProtocolAnalysisResult`. |
| GET | `/api/report-data` | Read report data for a capture filename. | Query `filename`; JSON report object. |
| GET | `/api/history` | Return in-memory analysis history. | No body; JSON list. |
| GET | `/reports/download-html` | Download an executive HTML report. | Query `filename`; HTML file response. |
| GET | `/reports/download-json` | Download a JSON report. | Query `filename`; JSON file response. |
| GET | `/api/jobs` | List recent persisted PCAP analysis jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/jobs/{job_id}` | Get one persisted analysis job. | Path `job_id`; JSON job record. |
| POST | `/api/chat` | Ask the report assistant a question. | `ChatRequest`; JSON assistant response. |

Testbed routes are registered with the `/api/testbed` prefix in `routers/testbed.py`:

| Method | Path | Description | Request / response shape |
|---|---|---|---|
| GET | `/api/testbed/scenarios` | List built-in scenario definitions. | No body; list of `ScenarioDefinition`. |
| POST | `/api/testbed/run` | Queue an asynchronous strongSwan scenario. | `TestbedRunRequest`; queued job id and state. |
| GET | `/api/testbed/jobs` | List testbed jobs. | Query `limit` 1-100; JSON list. |
| GET | `/api/testbed/jobs/{job_id}` | Read state, logs, and completed results. | Path `job_id`; `TestbedJobStatus`-shaped JSON. |
| GET | `/api/testbed/jobs/{job_id}/pcap` | Download a job’s captured PCAP. | Path `job_id`; PCAP file response. |

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
