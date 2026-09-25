# Cyber Sentinel — AI-Assisted IPsec VPN Security Intelligence Platform

An end-to-end cybersecurity framework for analyzing network capture files (`.pcap`, `.pcapng`), extracting IPsec / IKEv1 / IKEv2 / ESP cryptographic parameters, classifying network traffic using a pre-trained **XGBoost Encrypted Traffic Classifier**, evaluating security configurations against context-aware NIST SP 800-77 / FIPS 140-3 policies, and orchestrating a multi-node **strongSwan IPsec VPN Testbed**.

---

## 🏗 System Architecture

```text
               .pcap / .pcapng Capture OR strongSwan Testbed
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
            │   (React Web UI, Cloud DB, JSON & HTML Export) │
            └────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start with Docker (Recommended)

Run the entire platform (Vite React Frontend + FastAPI Backend + TShark Sniffer + ML Models) inside an optimized multi-stage Docker container.

### 1. Build and Run with Docker Compose
```bash
# Build the images and start containers in the background
docker compose up --build -d

# View live application logs
docker compose logs -f

# Check container health and status
docker compose ps

# Stop the running containers
docker compose down
```

### 2. Manual Docker Build & Run (Single Image)
```bash
# Build the Docker image
docker build -t ipsec-analyzer:latest .

# Linux / macOS / Git Bash
docker run --rm -p 8000:8000 \
  --name ipsec-analyzer-app \
  -v ./results:/app/results \
  -v ./captures:/app/captures \
  ipsec-analyzer:latest

# Windows (PowerShell)
docker run --rm -p 8000:8000 `
  --name ipsec-analyzer-app `
  -v ${PWD}/results:/app/results `
  -v ${PWD}/captures:/app/captures `
  ipsec-analyzer:latest
```

* **Web UI**: Open [http://localhost:8000](http://localhost:8000) in your browser.
* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🛠️ Local Development & Manual Build

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ (for building the React frontend)
- **Wireshark / TShark** (optional; built-in Scapy engine activates as fallback)

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run dependency & model check
python main.py check-dependencies
```

### 3. Frontend Build (React + Vite)
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Run frontend in Vite hot-reloading dev mode (port 5173)
npm run dev

# Build production bundle into frontend/dist/ (served by FastAPI)
npm run build

# Return to root directory
cd ..
```

### 4. Run the Backend Server
```bash
# Launch FastAPI server with built React UI
python main.py server
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 strongSwan IPsec VPN Testbed (VirtualBox / Vagrant)

The platform includes an automated 3-node strongSwan validation environment for generating live IKEv1/IKEv2/ESP traffic and security policy violations:
- **VM 1 (Initiator)**: `192.168.56.10` (strongSwan 5.x)
- **VM 2 (Responder)**: `192.168.56.20` (strongSwan 5.x + Nginx)
- **VM 3 (Observer)**: `192.168.56.30` (TShark / tcpdump wire sniffer)

### Launch Testbed VMs:
```bash
# Start all 3 virtual machines in VirtualBox
vagrant up

# Check status of VMs
vagrant status

# SSH into a specific VM if needed
vagrant ssh vm1-initiator

# Destroy / Reset testbed VMs when done
vagrant destroy -f
```

*Once VMs are booted, open [http://localhost:8000](http://localhost:8000), click the **strongSwan Testbed** tab, select a scenario, and hit **"Deploy & Run Testbed Scenario"**!*

---

## 💻 CLI & Batch Analysis Commands

### Analyze a Single Capture File
Analyze a `.pcap` or `.pcapng` file and export both JSON and Executive HTML reports:
```bash
python main.py analyze \
  --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng \
  --output results/report.json \
  --export-html results/executive_report.html
```

### Batch Process a Directory of Captures
Process all `.pcap` / `.pcapng` files in a directory and generate individual reports plus a batch `summary.csv`:
```bash
python main.py batch --input samples/ --output results/
```

## 🔬 Testing & Validation

```bash
# Run integration verification tests (Health, Testbed, Analysis, Vault)
python tests/test_integration.py

# Run unit tests
pytest
```
