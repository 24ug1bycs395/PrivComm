# Copilot instructions for `ipsecAnalyzer-SIH26`

## Repository shape and architecture

This repository is an IPsec/VPN capture analyzer with three connected surfaces:

- **Python analysis pipeline (repository root):** `main.py` exposes CLI commands, the FastAPI app, and the Streamlit launcher. `analyzer/pcap_ingestion.py` validates a capture, parses it with TShark when available, falls back to Scapy, and combines protocol and flow results. `services/protocol_engine.py` orchestrates the same pipeline for the API.
- **Protocol and flow analysis:** `analyzer/ike_parser.py` and `analyzer/esp_parser.py` extract observable IKE/ESP/AH data; `analyzer/ipsec_parser.py` normalizes it into the shared IPsec configuration shape; `analyzer/flow_extractor.py` produces the numerical flow features expected by the classifier. Keep unobservable values as `"unknown"` rather than inferring them.
- **Classification and assessment:** `ml/model_loader.py` loads the pre-trained artifacts from `models/` (or `traffic-classifier/models/`), and `ml/xgboost_adapter.py` aligns features and returns the traffic class/probabilities. `security/policy_engine.py` evaluates the normalized IPsec configuration against `config/security_policy.yaml`; `security/risk.py` and `security/recommendations.py` turn findings into the final assessment.
- **Reports and interfaces:** `reports/report_generator.py` defines the unified JSON/report shape and batch CSV output; `reports/html_report_generator.py` creates executive HTML. `routers/protocol.py` provides `/analyze/protocol`, `/analyze/sample`, `/analyze/sample-weak`, and report-download endpoints. The React app in `frontend/` calls those relative endpoints. The FastAPI root serves `frontend/dist` when it exists and otherwise falls back to the legacy root `index.html`, `style.css`, and `script.js`. `dashboard/app.py` is a separate Streamlit UI using the same analysis functions.

The intended data flow is:

```text
PCAP/PCAPNG -> TShark or Scapy ingestion
            -> IKE/ESP/AH parsing + flow feature extraction
            -> pre-trained XGBoost classification
            -> YAML policy evaluation
            -> findings, recommendations, risk, JSON/HTML reports
```

Keep new capture sources compatible with this ingestion contract so a future strongSwan testbed can feed captures into the same pipeline.

## Setup and commands

### Python backend

Use Python 3.10 or newer. Install the root runtime/API dependencies from the root manifest:

```bash
pip install -r requirements.txt
```

The root `requirements.txt` contains the FastAPI/uvicorn, PyShark/Scapy, model, configuration, Streamlit, and test dependencies. The separate `traffic-classifier/requirements.txt` is for the data-science/training workflow; install it only when working on that pipeline.

TShark/Wireshark is an external Windows dependency. The code searches `TSHARK_PATH`, then `PATH`, then standard Wireshark installation locations. Verify the environment with:

```bash
python main.py check-dependencies
```

Run the main interfaces:

```bash
python main.py server       # FastAPI + web UI at http://localhost:8000
python main.py dashboard   # Streamlit dashboard at http://localhost:8501
```

Analyze captures and write reports:

```bash
python main.py analyze --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng
python main.py analyze --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng --output results/report.json --export-html results/executive_report.html
python main.py batch --input samples/ --output results/
```

### Tests

The checked-in tests use `unittest` classes and can be run with the standard library:

```bash
python -m unittest discover tests
python -m unittest tests.test_security_engine
python -m unittest tests.test_security_engine.TestSecurityEngine.test_secure_configuration
```

Pytest is also listed in the root dependencies, so an equivalent run is:

```bash
pytest
pytest tests/test_security_engine.py
pytest tests/test_security_engine.py -k secure_configuration
```

`tests/test_protocol_engine.py` is an end-to-end test: it builds a synthetic IKEv2/ESP capture, invokes the engine, and calls the FastAPI endpoint. It expects the current `ProtocolAnalysisResult` behavior and may produce report files under `results/`.

### Frontend

The frontend is an independent Vite project:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
```

There is currently no frontend lint or test script in `frontend/package.json`. During local development, run the Python server separately because the React code uses relative API paths such as `/analyze/protocol`.

### Traffic-classifier workflow

Run these commands from `traffic-classifier/` after installing its requirements:

```bash
python src/inspect_dataset.py --data-path ../consolidated_traffic_data.csv
python src/preprocess.py --data-path ../consolidated_traffic_data.csv
python src/train.py
python src/evaluate.py
python src/predict.py --sample
python src/predict.py --input sample.json
```

This workflow writes processed data, encoders, model metadata, model artifacts, and evaluation reports. Do not retrain or replace the existing classifier when changing the analyzer unless the task explicitly concerns model training.

## Repository-specific conventions

- **Use the shared pipeline:** API, CLI, and Streamlit paths should compose the existing ingestion, classifier, policy, risk, recommendation, and report helpers instead of implementing a parallel analysis flow.
- **Preserve the report contract:** Unified results have `capture`, `ipsec`, `traffic_classification`, and `security_assessment` sections. Changes to one producer should be checked against CLI output, API response models, dashboard access, and HTML/JSON exporters.
- **Do not invent packet facts:** parser and normalization code must preserve `"unknown"`/`None` when a capture cannot reveal a parameter. In particular, PFS and replay-window details are not inferred from ordinary observation.
- **TShark is preferred but optional:** use the TShark JSON path for protocol dissection when available; maintain the Scapy fallback for environments without TShark. Flow features are extracted with Scapy even when TShark supplies protocol metadata.
- **Policy is data-driven:** security thresholds and approved/forbidden algorithms belong in `config/security_policy.yaml`. `security/policy_engine.py` has a fallback policy for missing/unreadable YAML; keep policy comparisons consistent with the normalized names emitted by the parsers.
- **Model schema is authoritative:** inference must use the feature order and class metadata loaded from the model artifacts. Preserve the engineered features (`bytes_per_pkt`, `fiat_biat_ratio`, `log_duration`, `log_bytes_sec`, `log_pkts_sec`) and return explicit status values such as `insufficient_features`, `model_error`, or `inference_error`.
- **Paths are currently working-directory relative:** commands are expected to run from the repository root, and model/config/sample/result locations are resolved with relative paths. Avoid changing this assumption without updating all launchers and documentation.
- **API upload lifecycle:** `/analyze/protocol` accepts `.pcap`, `.pcapng`, or `.cap`, writes the upload to a temporary file, analyzes it, and removes the temporary file in `finally`. Preserve validation and cleanup when changing upload handling.
- **Sample weak scenario is intentionally simulated:** `/analyze/sample-weak` analyzes the bundled sample but overrides the returned fields/findings to demonstrate a weak legacy configuration. Do not mistake it for a second capture file or a parser regression.
- **Generated artifacts are not source inputs:** analysis results under `results/`, caches, and build/dependency directories are ignored or generated. Keep durable model metadata and required sample captures separate from transient report output.
- **Frontend integration uses relative URLs:** do not hard-code a different API origin in components unless adding an explicit proxy/configuration. The Vite build is copied/served through `frontend/dist` by the FastAPI app.
