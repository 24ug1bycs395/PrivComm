from analyzer.provenance import INFERRED, OBSERVED, PARSED, UNKNOWN, build_data_provenance


def test_provenance_distinguishes_wire_parsed_inferred_and_unknown() -> None:
    provenance = build_data_provenance(
        ingest_result={
            "status": "success",
            "ip_version": "IPv4",
            "source_ip": "10.0.0.1",
            "destination_ip": "10.0.0.2",
        },
        ipsec={
            "ike_version": "IKEv2",
            "encryption": "AES-256-GCM",
            "integrity": "AEAD",
            "dh_group": "14",
            "mode": "Tunnel",
            "mode_confidence": "high",
            "pfs": "unknown",
        },
        traffic_classification={"status": "success", "traffic_type": "VIDEO_STREAM"},
        behavioral_anomaly={"overall_prediction": "normal"},
        metadata_exposure={"exposure_findings": []},
        rfc4303_elimination={"viable_ciphers": ["AES-256-GCM"]},
    )

    assert provenance["ip_version"] == OBSERVED
    assert provenance["ike_version"] == PARSED
    assert provenance["mode"] == INFERRED
    assert provenance["traffic_classification"] == INFERRED
    assert provenance["pfs"] == UNKNOWN


def test_rfc4303_cipher_override_is_marked_inferred() -> None:
    provenance = build_data_provenance(
        ingest_result={"status": "success"},
        ipsec={"encryption": "AES-256-GCM", "encryption_provenance": "rfc4303_arithmetic"},
        traffic_classification=None,
        behavioral_anomaly=None,
        metadata_exposure=None,
        rfc4303_elimination={"viable_ciphers": ["AES-256-GCM"]},
    )
    assert provenance["encryption"] == INFERRED
