# Cyber Sentinel — AI-Assisted IPsec VPN Security Intelligence Platform

An end-to-end Python framework for analyzing network capture files (`.pcap`, `.pcapng`), extracting IPsec / IKEv1 / IKEv2 / ESP security parameters, classifying network traffic using a pre-trained **XGBoost Encrypted Traffic Classifier**, and evaluating security configurations against a deterministic, context-aware security policy.

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
│   (Cyber Sentinel Web UI, JSON & HTML Export)  │
└────────────────────────────────────────────────┘
```

---

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

---

## 🌐 Running the Web Applications

### 1. Launch Cyber Sentinel Web Platform (Web UI + APIs)
Launch the primary Cyber Sentinel Web Platform:

```bash
python main.py server
```
* **Web UI URL**: Open [http://localhost:8000](http://localhost:8000) in your browser.
* **Features**: Drag-and-drop `.pcap` / `.pcapng` upload, reference scenario loading, AI traffic classification display, risk scoring, security audit findings, and one-click download buttons for **Executive HTML** and **Technical JSON** reports!

### 2. Launch Streamlit Analytics Dashboard
Launch the alternative Streamlit analytics dashboard:

```bash
python main.py dashboard
```
* **Dashboard URL**: Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 💻 CLI Commands

### Analyze a Single Capture File
Analyze a `.pcap` or `.pcapng` file and export both JSON and Executive HTML reports:

```bash
python main.py analyze --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng --output results/report.json --export-html results/executive_report.html
```

### Batch Process a Directory of Captures
Process all `.pcap` / `.pcapng` files in a directory and generate individual reports plus a batch `summary.csv`:

```bash
python main.py batch --input samples/ --output results/
```

---

## 🧪 Unit Testing

Run the full test suite:

```bash
python -m unittest discover tests
```
