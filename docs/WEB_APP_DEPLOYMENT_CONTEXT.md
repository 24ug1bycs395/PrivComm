# Deployed Web App Context

This document explains the frontend-only web application deployed to Vercel and the relationship between its browser demo fallbacks and the fully functional local Docker application.

It is intended as context for future developers and AI agents working on this repository.

## Deployment target

The Vercel deployment contains only the React/Vite application in:

```text
frontend/
```

Vercel builds the frontend with:

```text
npm run build
```

The generated static site is emitted to:

```text
frontend/dist/
```

Recommended Vercel project settings:

```text
Root Directory: frontend
Framework: Vite
Build Command: npm run build
Output Directory: dist
```

The Vercel deployment is a frontend-only demonstration. It does not contain the FastAPI server, TShark, Scapy processing, ML inference runtime, strongSwan VMs, SSH orchestration, or server-side persistence.

## Two supported execution modes

### 1. Frontend demo mode / Vercel fallback

The browser demo is designed to remain usable when the FastAPI backend is not deployed or cannot be reached.

The fallback behavior is implemented in the React components themselves:

- `frontend/src/components/AnalyzerWorkspace.jsx`, `TelemetryDashboard.jsx`, and `HistoryVaultTab.jsx`
  - Uses built-in sample analysis data if sample analysis requests fail.
  - The sample results are presentation/demo data, not a PCAP analysis result.
  - Report downloads (Executive PDF & Technical JSON) fall back to static assets bundled in `frontend/public/reports/` and in-memory JSON blob generation when the backend is absent.

- `frontend/src/components/TestbedTab.jsx`
  - Attempts the real `/api/testbed/run` endpoint first.
  - If the backend is unavailable, creates a `demo-*` job ID.
  - Runs the visible testbed stages in the browser using timers and predefined terminal text.
  - Simulates configuration, tunnel negotiation, traffic, capture, and AI stages.
  - Does not require VMs, SSH, strongSwan, TShark, or FastAPI.
  - PCAP capture download falls back to sample captures in `frontend/public/samples/`.

- `frontend/src/components/LiveDashboardTab.jsx`
  - Recognizes `demo-*` jobs and does not poll them as if they were backend jobs.
  - Uses the browser packet generator only when `orchestrationMode === 'FALLBACK_SIM'`.
  - Synthetic packet sizes, classifications, labels, confidence values, and traffic mixes belong only to this fallback path.

The browser fallback is for demonstration and UI interaction. It must not be described as real packet capture, real ML inference, or real VPN traffic.

### 2. Fully functional local/backend mode

The local Docker application remains the authoritative full implementation. It includes:

- React frontend
- FastAPI backend
- PCAP/PCAPNG ingestion
- Scapy/TShark protocol analysis
- XGBoost and anomaly detection models
- Security policy and risk evaluation
- strongSwan testbed orchestration
- SSH control of testbed nodes
- Observer packet capture
- Optional Supabase/cloud persistence

When the backend is available, the frontend attempts to use real API routes first. Real testbed execution must use observer/backend telemetry and captured data. It must not use the browser’s synthetic packet generator.

The backend testbed orchestrator must not emit a hard-coded weighted classification mix during a real run. Per-packet classifications must come from actual observer telemetry or the analysis pipeline. If real classification data is unavailable, the UI should show an unavailable/unclassified state rather than inventing a result.

## Real versus simulated data rules

Keep these boundaries intact:

| Data or behavior | Vercel fallback | Real local/backend mode |
|---|---|---|
| Testbed stages | Browser timers and predefined stage text | Backend job events |
| Packet stream | Browser-generated demo packets | Observer/backend telemetry |
| Traffic classification | Demo-only synthetic classification | Backend/ML result or unclassified |
| PCAP analysis | Built-in sample presentation data | FastAPI analysis pipeline |
| VM/SSH activity | Not performed | Performed by the backend testbed |
| Persistence | Browser state only, where applicable | Backend storage/Supabase/local storage |

Do not move fallback-only constants into the real telemetry path. Do not make a fallback result look like an observed packet, a real ML prediction, or a completed physical VM run.

## Important files

```text
frontend/src/App.jsx
frontend/src/components/AnalyzerWorkspace.jsx
frontend/src/components/TestbedTab.jsx
frontend/src/components/LiveDashboardTab.jsx
frontend/src/components/TelemetryDashboard.jsx
frontend/src/components/HistoryVaultTab.jsx

main.py
routers/
services/testbed/
analyzer/
ml/
models/
db/
Dockerfile
docker-compose.yml
```

`frontend/vite.config.js` contains development-only proxy rules for backend routes. Those proxy rules do not create a backend in the Vercel deployment.

## Docker/local preservation rule

The Dockerfile is intentionally separate from the Vercel deployment and must not be changed merely to support the frontend demo.

Changes for the Vercel demo should normally be limited to the frontend React code and documentation. Backend changes are appropriate only when correcting real backend behavior, such as preventing fake telemetry from being emitted during a genuine testbed run.

The local Docker application must continue to provide the full real workflow independently of the Vercel fallback.

## Guidance for future AI agents

Before changing deployment behavior:

1. Determine whether the change belongs to the browser fallback or the real backend.
2. Keep synthetic data behind an explicit fallback/demo condition.
3. Prefer real observer events, API responses, and analysis results in backend mode.
4. Never silently replace a failed real analysis with a result presented as authentic.
5. Do not modify `Dockerfile` or Docker Compose configuration for a Vercel-only frontend change.
6. Run the frontend production build after React changes.
7. Run Python syntax/tests after backend changes.

The simplest mental model is:

```text
Vercel:
  React UI → browser simulation when backend is absent

Local Docker:
  React UI → FastAPI → real analysis/testbed/storage pipeline
```
