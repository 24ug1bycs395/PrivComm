import json

from reports.crypto_bom import build_crypto_bom
from security.downgrade_baseline import (
    baseline_record_authorized,
    compare_tunnel_baseline,
    record_tunnel_baseline,
)
from security.drift_detector import detect_configuration_drift
from security.policy_engine import evaluate_ipsec_security, load_security_policy
from security.pqc_assessor import evaluate_post_quantum_readiness


def test_policy_overlay_overrides_lists_and_rejects_unknown_keys(tmp_path) -> None:
    baseline_path = "config/security_policy.yaml"
    overlay_path = tmp_path / "policy-overlay.yaml"
    overlay_path.write_text(
        "encryption:\n  approved:\n    - AES-128-GCM\n",
        encoding="utf-8",
    )

    policy = load_security_policy(baseline_path, str(overlay_path))
    assert policy["encryption"]["approved"] == ["AES-128-GCM"]
    assert "3DES" in policy["encryption"]["forbidden"]
    findings = evaluate_ipsec_security(
        {
            "detected": True,
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "dh_group": 19,
            "pfs": "unknown",
        },
        policy_path=baseline_path,
        overlay_path=str(overlay_path),
    )
    assert "IPSEC-ENC-002" in {finding.finding_id for finding in findings}

    overlay_path.write_text("encryption:\n  approved: []\n  typo: true\n", encoding="utf-8")
    try:
        load_security_policy(baseline_path, str(overlay_path))
    except ValueError as exc:
        assert "unsupported keys" in str(exc)
    else:
        raise AssertionError("Unsupported overlay keys must be rejected.")


def test_missing_policy_does_not_silently_fallback(tmp_path) -> None:
    missing = tmp_path / "absent.yaml"
    try:
        load_security_policy(str(missing), overlay_path=None)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Missing policy must be reported, not replaced silently.")


def test_pqc_assessment_preserves_unknowns_and_does_not_claim_ikev2_is_pqc() -> None:
    unknown = evaluate_post_quantum_readiness(
        {"ike_version": "IKEv2", "dh_group": "unknown", "encryption": "unknown"}
    )
    assert unknown["pqc_status"] == "INSUFFICIENT_EVIDENCE"
    assert unknown["readiness_score"] is None
    assert unknown["pqc_checks"][2]["status"] == "NOT_VERIFIED"
    assert unknown["cnsa_2"]["status"] == "NOT_ASSESSED"
    assert unknown["mosca_timeline"]["status"] == "NOT_ASSESSED"

    classical = evaluate_post_quantum_readiness(
        {"ike_version": "IKEv2", "dh_group": "19", "encryption": "AES-256-GCM"}
    )
    assert classical["pqc_status"] == "CLASSICAL_KEY_EXCHANGE_OBSERVED"
    assert classical["crypto_agility_rating"] == "UNVERIFIED"


def test_mosca_timeline_only_uses_caller_supplied_estimates() -> None:
    result = evaluate_post_quantum_readiness(
        {
            "data_shelf_life_years": 10,
            "migration_lead_time_years": 15,
            "estimated_crqc_years": 20,
        }
    )
    assert result["mosca_timeline"]["status"] == "MIGRATION_WINDOW_EXCEEDS_HORIZON"


def test_downgrade_baseline_requires_known_comparable_observations(tmp_path) -> None:
    path = str(tmp_path / "tunnel-baselines.json")
    config = {
        "ike_version": "IKEv2",
        "encryption": "AES-256-GCM",
        "dh_group": "19",
        "pfs": True,
        "mode": "Tunnel",
        "integrity": "AEAD",
        "replay_protection": "unknown",
    }
    assert compare_tunnel_baseline("branch-a", config, path)["status"] == "NO_BASELINE"
    record_tunnel_baseline("branch-a", config, "a" * 64, path)

    comparison = compare_tunnel_baseline(
        "branch-a",
        {
            **config,
            "ike_version": "IKEv1",
            "encryption": "3DES-CBC",
            "pfs": "unknown",
        },
        path,
    )
    assert comparison["status"] == "DOWNGRADE"
    assert comparison["downgrade_detected"] is True
    assert next(item for item in comparison["field_comparisons"] if item["field"] == "pfs")[
        "status"
    ] == "INSUFFICIENT_EVIDENCE"


def test_baseline_recording_requires_separate_operator_secret(monkeypatch) -> None:
    monkeypatch.delenv("IPSEC_BASELINE_AUTH_SECRET", raising=False)
    assert not baseline_record_authorized(None)
    assert not baseline_record_authorized("short")
    monkeypatch.setenv("IPSEC_BASELINE_AUTH_SECRET", "operator-secret-of-at-least-32-bytes")
    assert baseline_record_authorized("operator-secret-of-at-least-32-bytes")
    assert not baseline_record_authorized("different-operator-secret-of-at-least-32")


def test_drift_unknown_fields_are_unverified_not_drifted() -> None:
    report = detect_configuration_drift(
        {"ike_version": "unknown", "encryption": None, "dh_group": "unknown", "pfs": "unknown"}
    )
    assert report["drift_detected"] is False
    assert report["drift_status"] == "UNVERIFIED"
    assert all(field["status"] == "UNVERIFIED" for field in report["field_diffs"])


def test_cbom_records_only_known_values_and_packet_evidence() -> None:
    cbom = build_crypto_bom(
        {
            "ike_version": "IKEv2",
            "encryption": "unknown",
            "dh_group": None,
            "integrity": "AEAD",
        },
        "b" * 64,
        [{
            "frame_number": 9,
            "protocol": "IKE",
            "capture_byte_offset": 50,
            "capture_byte_length": 60,
            "fields": {
                "ike_version": {
                    "value": "IKEv2",
                    "capture_byte_offset": 67,
                    "capture_byte_length": 1,
                }
            },
        }],
    )
    assert cbom["schema_version"] == "privcomm.cbom.v1"
    assert {item["source_field"] for item in cbom["components"]} == {"ike_version", "integrity"}
    ike = next(item for item in cbom["components"] if item["source_field"] == "ike_version")
    assert ike["evidence"][0]["capture_byte_offset"] == 67
    assert {item["field"] for item in cbom["unresolved"]} >= {"encryption", "dh_group"}
    json.dumps(cbom)
