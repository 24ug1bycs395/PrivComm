# Build: AI-Powered IPsec VPN Protocol Analyzer & Security Assessment Framework

## Context

I am building an IPsec VPN Protocol Analyzer and Security Assessment Framework.

I already have a trained **XGBoost traffic-classification model**. Its purpose is:

> Given extracted network-flow features, classify the traffic type, such as:
>
> * VoIP
> * Web browsing
> * Video streaming
> * Email
> * DNS
> * etc.

**Do NOT retrain or replace this XGBoost model unless absolutely necessary.**

The goal now is to build the rest of the analyzer around it.

I do NOT have my final IPsec VM testbed yet. Therefore, the system must initially work with existing `.pcap` / `.pcapng` files. Later, I will connect a strongSwan-based IPsec VM testbed to the same pipeline.

---

# 1. Overall Architecture

Build the application around this architecture:

PCAP / PCAPNG
|
v
TShark / PCAP Ingestion
|
+-------------------------+
|                         |
v                         v
IPsec/IKE Analyzer          Flow Feature Extractor
|                         |
v                         v
Configuration Data             XGBoost
|                         |
v                         v
Security Assessment       Traffic Classification
|                         |
+------------+------------+
|
v
Unified Analysis
|
v
Findings + Recommendations
|
v
JSON Report

Keep the architecture modular so that later the input can become:

strongSwan VM testbed
|
v
TShark capture
|
v
PCAP
|
v
SAME ANALYZER

Do not redesign the analyzer when VMs are added.

---

# 2. First Task: Environment Detection and Dependency Setup

The project will run on Windows initially.

Check whether the following are installed:

* Python 3.10+
* TShark
* Wireshark installation path
* tshark executable available in PATH

The application should have a startup/dependency check such as:

```bash
python main.py --check-dependencies
```

It should report:

```text
Python: ✓
TShark: ✓
TShark version: ...
Wireshark: ✓/Not required
XGBoost model: ✓
```

If TShark is not installed, provide clear Windows installation instructions in `README.md`.

Do not automatically download/install software without user approval.

The README should explain that installing Wireshark normally provides TShark as well.

Also support configuring the TShark executable path through an environment variable, for example:

```text
TSHARK_PATH=C:\Program Files\Wireshark\tshark.exe
```

Do not hard-code a machine-specific path.

---

# 3. PCAP Ingestion

Create a module responsible for accepting:

```text
.pcap
.pcapng
```

Example:

```bash
python main.py analyze --pcap samples/ipsec_sample.pcapng
```

The ingestion layer must:

* validate that the file exists
* validate the extension
* invoke TShark safely using subprocess
* capture stdout/stderr
* handle TShark errors
* never crash the application because of malformed input
* return a structured analysis result

Do not manually parse PCAP binary structures unless absolutely necessary.

Prefer TShark's protocol dissectors and field extraction.

---

# 4. IPsec Detection

Determine whether the capture contains IPsec-related traffic.

Detect, where observable:

* IKE
* IKEv1
* IKEv2
* ESP
* AH

Produce something like:

```json
{
  "ipsec_detected": true,
  "ike_detected": true,
  "ike_version": "IKEv2",
  "esp_detected": true,
  "ah_detected": false
}
```

If something cannot be determined:

```json
{
  "ike_version": "unknown"
}
```

NEVER invent a value.

---

# 5. IKE / IPsec Configuration Extraction

Extract configuration information that is actually observable from the capture.

Potential fields include:

* IKE version
* encryption algorithm
* integrity/authentication algorithm
* Diffie-Hellman group
* Security Association information
* SPI
* proposal information
* lifetime information where observable
* IPsec protocol
* tunnel/transport indicators where reliably observable
* PFS-related information where reliably observable
* replay-related information where reliably observable

Create a normalized structure such as:

```json
{
  "ipsec": {
    "detected": true,
    "ike_version": "IKEv2",
    "mode": "unknown",
    "encryption": "AES-256-GCM",
    "integrity": "AEAD",
    "dh_group": 19,
    "pfs": "unknown",
    "replay_protection": "unknown",
    "sa_lifetime": null
  }
}
```

Important:

Do NOT assume that an ESP packet alone reveals the complete VPN configuration.

Configuration extraction should primarily use IKE/security-association information.

If the PCAP does not contain enough information, return:

```text
unknown
```

and record why the field could not be determined.

---

# 6. Packet and Flow Feature Extraction

Create a reusable flow feature extractor.

Extract features useful for traffic classification, such as:

* source IP
* destination IP
* protocol
* source port
* destination port
* flow duration
* packet count
* byte count
* packet rate
* byte rate
* packet-size statistics
* inter-arrival-time statistics
* forward/backward packet statistics
* forward/backward byte statistics

Do NOT assume the exact feature names of my existing XGBoost model.

First inspect the existing model interface and determine:

1. What features it expects
2. Their exact order
3. Any preprocessing/scaling
4. Label encoding
5. Class names
6. Model serialization format

Build an adapter:

```text
Extracted Flow Features
        |
        v
XGBoost Adapter
        |
        v
Existing XGBoost Model
        |
        v
Traffic Class + Confidence
```

Do not modify the trained model unless required for compatibility.

---

# 7. XGBoost Integration

The existing XGBoost model should answer ONLY:

> "What type of traffic does this flow resemble?"

Example:

```json
{
  "traffic_type": "Video Streaming",
  "confidence": 0.93
}
```

Do NOT use the XGBoost model to make security decisions such as:

* weak encryption
* weak DH
* PFS disabled
* replay protection
* bad SA lifetime

Those should be handled by the security assessment engine.

If there is insufficient data to produce the exact feature vector required by the existing model, return:

```json
{
  "traffic_classification": {
    "status": "insufficient_features"
  }
}
```

Do not silently fabricate features.

---

# 8. Security Policy Engine

Build a separate deterministic security rules engine.

The engine should compare the extracted configuration against a configurable security policy.

Example policy file:

```yaml
encryption:
  approved:
    - AES-256-GCM
    - AES-256-CBC

dh_groups:
  approved:
    - 14
    - 19
    - 20
    - 21

pfs:
  required: true

replay_protection:
  required: true
```

Do NOT hard-code all policy decisions into Python.

The policy must be editable.

---

# 9. Security Findings

The engine should produce structured findings.

Example:

```json
{
  "finding_id": "IPSEC-DH-001",
  "category": "Key Exchange",
  "severity": "HIGH",
  "title": "DH group does not meet configured policy",
  "observed": "Group 2",
  "expected": "Approved DH group",
  "recommendation": "Use an approved stronger DH group."
}
```

Possible categories:

* Encryption
* Integrity
* Key Exchange
* PFS
* Replay Protection
* SA Lifetime
* Protocol Version
* Tunnel/Transport Mode
* Configuration Compliance

Do not label something insecure merely because the parser failed to observe it.

For example:

```text
PFS = unknown
```

must NOT become:

```text
PFS = disabled
```

Instead:

```text
status = not_observable
```

---

# 10. Recommendation Engine

Create a recommendation layer separate from the detection layer.

For every confirmed finding, provide:

* current configuration
* expected configuration
* reason
* recommended action

Example:

```text
Finding:
Weak DH configuration

Current:
DH Group 2

Recommendation:
Use an approved stronger DH group.

Reason:
The current group does not satisfy the configured security baseline.
```

Do not claim a configuration is universally insecure.

The recommendation should be based on the project's configured policy.

---

# 11. Security Risk Calculation

Implement a transparent risk calculation.

Do NOT use another ML model for the initial version.

Example:

```text
HIGH finding    → weighted risk contribution
MEDIUM finding  → weighted risk contribution
LOW finding     → weighted risk contribution
```

Generate:

```json
{
  "risk": {
    "score": 72,
    "level": "HIGH",
    "method": "deterministic_policy_weighting"
  }
}
```

Document the scoring methodology.

Do not make the score arbitrary or opaque.

---

# 12. Final Analysis Result

The complete output should look approximately like:

```json
{
  "capture": {
    "filename": "sample.pcapng",
    "packet_count": 12345
  },

  "ipsec": {
    "detected": true,
    "ike_version": "IKEv2",
    "encryption": "AES-256-GCM",
    "integrity": "AEAD",
    "dh_group": 19,
    "mode": "Tunnel",
    "pfs": "unknown",
    "replay_protection": "unknown"
  },

  "traffic_classification": {
    "traffic_type": "Video Streaming",
    "confidence": 0.93
  },

  "security_assessment": {
    "risk_level": "MEDIUM",
    "findings": [],
    "recommendations": []
  }
}
```

---

# 13. CLI

Implement a simple CLI:

```bash
python main.py --help
```

Commands:

```bash
python main.py check-dependencies

python main.py analyze --pcap samples/sample.pcap

python main.py analyze --pcap samples/sample.pcap --output results/result.json

python main.py batch --input samples/ --output results/
```

The batch command should process an entire directory automatically.

---

# 14. Batch Processing

Support:

```text
samples/
├── capture1.pcap
├── capture2.pcapng
├── capture3.pcap
└── capture4.pcapng
```

Run:

```bash
python main.py batch --input samples/
```

Produce:

```text
results/
├── capture1.json
├── capture2.json
├── capture3.json
└── capture4.json
```

Also produce a summary CSV:

```text
summary.csv
```

with columns such as:

```text
capture
ipsec_detected
ike_version
encryption
dh_group
traffic_type
traffic_confidence
risk_level
finding_count
```

---

# 15. Logging and Error Handling

Implement useful logs:

```text
[INFO] Loading PCAP
[INFO] Running TShark
[INFO] Detected IKEv2
[INFO] Detected ESP
[INFO] Extracting IPsec parameters
[INFO] Running traffic classifier
[INFO] Running security assessment
[INFO] Analysis completed
```

Handle:

* missing TShark
* invalid PCAP
* empty PCAP
* unsupported protocol
* malformed packet
* missing XGBoost model
* missing expected model features
* TShark timeout
* subprocess errors

---

# 16. Project Structure

Use a clean structure similar to:

```text
ipsec-analyzer/
│
├── main.py
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   └── security_policy.yaml
│
├── analyzer/
│   ├── pcap_ingestion.py
│   ├── tshark.py
│   ├── ipsec_parser.py
│   ├── ike_parser.py
│   ├── esp_parser.py
│   └── flow_extractor.py
│
├── security/
│   ├── policy_engine.py
│   ├── findings.py
│   ├── recommendations.py
│   └── risk.py
│
├── ml/
│   ├── xgboost_adapter.py
│   └── model_loader.py
│
├── reports/
│   └── report_generator.py
│
├── samples/
│
├── results/
│
└── tests/
    ├── test_ipsec_parser.py
    ├── test_security_engine.py
    └── test_xgboost_adapter.py
```

Adapt this structure if the existing project already has an established architecture.

---

# 17. Testing Strategy

Before using VMs, test using existing IPsec PCAP files.

The system must be able to:

1. Load a PCAP
2. Detect IPsec
3. Detect IKE/ESP
4. Extract whatever configuration information is actually available
5. Represent unavailable information as unknown
6. Extract flow features
7. Run my existing XGBoost model
8. Run deterministic security rules
9. Produce recommendations
10. Produce JSON/CSV output

Create unit tests using sample data.

---

# 18. Future VM Integration

Design the system so that later I can add:

```text
strongSwan VM 1
strongSwan VM 2
```

The future pipeline will be:

```text
Configuration Generator
        |
        v
strongSwan VM Testbed
        |
        v
Traffic Generator
        |
        v
TShark
        |
        v
PCAP
        |
        v
THIS ANALYZER
```

The analyzer itself should not need major architectural changes.

---

# 19. Important Scope Boundary

Do NOT implement automatic VPN reconfiguration yet.

For now:

```text
Detect
   ↓
Assess
   ↓
Recommend
```

Later we may add:

```text
Detect
   ↓
Assess
   ↓
Recommend
   ↓
Generate strongSwan configuration
   ↓
Apply after administrator approval
   ↓
Re-test
```

---

# 20. Important Security/Correctness Rule

Never invent protocol information.

If a PCAP cannot establish:

```text
PFS
SA lifetime
Tunnel/Transport mode
Encryption
DH group
```

then report:

```text
unknown / not_observable
```

rather than guessing.

The analyzer should distinguish:

```text
confirmed
inferred
unknown
```

where appropriate.

---

# 21. Deliverables

At the end of this implementation I want:

1. Working Python PCAP analyzer
2. TShark integration
3. IPsec/IKE/ESP parser
4. Existing XGBoost integration
5. Configurable security policy
6. Deterministic security assessment engine
7. Recommendation engine
8. Risk calculation
9. JSON output
10. CSV batch output
11. CLI
12. Unit tests
13. README with Windows setup instructions
14. Example PCAP analysis

Do not build a frontend yet.

Focus first on making the backend analysis pipeline reliable and testable.

Before writing large amounts of code, inspect the existing repository and existing XGBoost model, determine its expected feature schema, and preserve the existing model rather than duplicating its functionality.
