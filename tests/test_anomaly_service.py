"""Tests for VPN Behavioral Anomaly Detection service and API."""

from fastapi.testclient import TestClient

from anomaly.service import get_baseline, get_status, predict_sample
from main import app
from ml.anomaly.generate_dataset import generate_controlled_dataset
from ml.anomaly.schemas import FEATURE_COLUMNS

client = TestClient(app)


def test_anomaly_status():
    status = get_status()
    assert status.status == "ready"
    assert status.feature_count == 32
    assert "packets_per_second" in status.features


def test_anomaly_baseline():
    baseline = get_baseline()
    assert len(baseline) == 32
    feature_names = [b.feature for b in baseline]
    assert "bytes_per_second" in feature_names


def test_normal_sample_prediction():
    normal_df = generate_controlled_dataset("normal", 5, seed=42)
    sample = normal_df.iloc[0].to_dict()
    res = predict_sample(sample)
    assert res.detector is not None
    assert 0.0 <= res.anomaly_score <= 1.0
    assert len(res.top_contributing_features) > 0


def test_traffic_spike_anomaly_prediction():
    spike_df = generate_controlled_dataset("traffic_spike", 5, seed=42)
    sample = spike_df.iloc[0].to_dict()
    res = predict_sample(sample)
    assert res.prediction == "anomalous"
    assert res.anomaly_score > 0.45
    assert res.severity in ("MEDIUM", "HIGH", "CRITICAL")
    top_feature_names = [f.feature for f in res.top_contributing_features]
    assert any(feat in top_feature_names for feat in ["bytes_per_second", "packets_per_second", "byte_count"])


def test_api_status_endpoint():
    resp = client.get("/anomaly/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["feature_count"] == 32


def test_api_baseline_endpoint():
    resp = client.get("/anomaly/baseline")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 32


def test_api_detect_endpoint():
    normal_df = generate_controlled_dataset("normal", 1, seed=99)
    sample = {col: float(normal_df[col].iloc[0]) for col in FEATURE_COLUMNS}
    resp = client.post("/anomaly/detect", json={"features": sample, "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "prediction" in data
    assert "anomaly_score" in data
    assert len(data["top_contributing_features"]) <= 3
