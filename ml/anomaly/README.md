# VPN Behavioral Anomaly Detection

This module is an independent behavioral detector. It does not replace or
modify the existing traffic-classification XGBoost model. It reports whether a
measured traffic window is `normal` or `anomalous`, a calibrated anomaly
ranking score, and measurable baseline deviations that help explain the result.

The detector does not identify a specific attack or compromise from a PCAP.
Scenario names such as `traffic_spike` and `peer_activity_anomaly` describe
controlled behavioral test conditions only.

## Reproducible workflow

Install the project dependencies from the repository root:

```powershell
python -m pip install -r requirements.txt
```

Generate a reproducible controlled dataset:

```powershell
python -m ml.anomaly.generate_dataset --all --samples 1000 --seed 42
```

This writes `datasets/vpn_behavioral_dataset.csv` with normal and anomalous
scenario labels. The rows are synthetic controlled feature records; they are
not presented as real PCAP measurements.

## Generate from the strongSwan testbed

The preferred dataset path is the existing three-node strongSwan testbed. The
command below runs the existing orchestrator, captures traffic on the observer,
downloads the resulting PCAP, and extracts the same behavioral features used
in production inference:

```powershell
python -m ml.anomaly.generate_testbed_dataset `
  --all `
  --runs-per-scenario 3 `
  --window-seconds 60 `
  --output ml/anomaly/datasets/vpn_behavioral_testbed.csv
```

Start the testbed first with `vagrant up` or the repository's Docker testbed
stack. This command enables strict capture mode. If the VMs are unavailable,
SSH fails, or the observer PCAP cannot be downloaded, it stops with an error
instead of silently copying one of the bundled sample PCAPs.

The default scenario mapping is explicit and operational rather than an attack
claim: the compliant IKEv2 scenario is labeled `normal`; rekey stress, DNS
burst, P2P throughput, and multi-tunnel scenarios are labeled as controlled
behavioral anomaly conditions for evaluation. Review and relabel these mappings
when collecting a production dataset.

Extract the same feature schema from a real capture:

```powershell
python -m ml.anomaly.generate_dataset `
  --pcap samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng `
  --window-seconds 60 `
  --pcap-label 0 `
  --output ml/anomaly/datasets/sample_pcap_features.csv
```

The PCAP extractor uses Scapy packet timestamps, sizes, IP endpoints, TCP/UDP/
ICMP headers, observable ESP markers, and UDP 500/4500 IKE markers. It does
not invent decrypted payload fields. Set `--pcap-label 1` only when an operator
has an independent, documented behavioral label.

Train and compare the detectors:

```powershell
python -m ml.anomaly.train
```

Training fits only `normal` rows. It holds out normal windows and anomalous
scenario windows using within-scenario timestamp order. Isolation Forest and a
transparent robust-IQR z-score baseline are compared on validation data; the
selected artifact is evaluated once on the holdout test data.

Artifacts are written to:

- `models/vpn_anomaly_detector.joblib`
- `models/feature_schema.json`
- `models/model_metadata.json`
- `reports/evaluation.json`

## Inference

```python
from ml.anomaly.predict import predict, predict_pcap

result = predict(feature_mapping)
window_results = predict_pcap("samples/ikev2_s2s_ipsec_vpn_aes_gcm.pcapng")
```

The score is not a probability. It is normalized from the detector's raw
anomaly score and calibrated against held-out normal windows:

- `0.0`: strongly consistent with the learned normal baseline
- `1.0`: strongly outside the calibrated normal range

For Isolation Forest, `top_contributing_features` are not tree-level SHAP
attributions. They are the largest robust deviations from the training-normal
median measured in IQR units.

The command-line interface accepts a JSON feature mapping too:

```powershell
python -m ml.anomaly.predict --features '{"duration_sec":60,"packet_count":100}'
```

The complete mapping must contain every column in
`models/feature_schema.json`; the short JSON above is only a shape example and
will correctly fail validation until completed.

## Inference contract

```json
{
  "prediction": "normal",
  "anomaly_score": 0.0,
  "top_contributing_features": [
    {
      "feature": "bytes_per_second",
      "value": 1234.0,
      "reason": "above the learned normal median by 1.40 IQR",
      "baseline_median": 1100.0,
      "baseline_iqr": 95.0
    }
  ],
  "detector": "isolation_forest",
  "score_definition": "Calibrated ranking score; not a probability."
}
```

The JSON above documents the output contract; it is not a claimed evaluation
result.
