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

Example Output:

```text
--- AI-Powered IPsec VPN Protocol Analyzer Startup Check ---
Python: [OK] (v3.10.9)
TShark: [OK] (C:\Program Files\Wireshark\tshark.exe)
TShark version: TShark (Wireshark) 4.2.0
Wireshark: [OK]
XGBoost model: [OK] (Artifacts found at 'traffic-classifier\models')
-----------------------------------------------------------
```

---

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
```

---

## 🌐 Future VM Testbed Pipeline

The architecture is designed to integrate seamlessly with strongSwan IPsec testbed VMs:

```text
  Config Generator ──► strongSwan VMs ──► Traffic Generator ──► TShark / PCAP ──► THIS ANALYZER
```
