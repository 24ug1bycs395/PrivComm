import pytest

import services.protocol_engine as protocol_engine
from analyzer.vendor_config_parser import VendorConfigParser


def test_cisco_parser_preserves_unknown_values_and_only_parses_present_peer():
    parsed = VendorConfigParser.parse_config(
        "crypto isakmp policy 10\n encr 3des\n hash md5\n group 2\n",
        override_vendor=VendorConfigParser.VENDOR_CISCO,
    )

    assert parsed["ike_version"] == "IKEv1"
    assert parsed["encryption"] == "3DES-CBC"
    assert parsed["integrity"] == "HMAC-MD5-96"
    assert parsed["dh_group"] == "2"
    assert parsed["mode"] is None
    assert parsed["pfs"] is None
    assert parsed["source_ip"] is None
    assert parsed["destination_ip"] is None
    assert parsed["field_provenance"]["mode"] == "UNKNOWN"
    assert parsed["field_provenance"]["encryption"] == "PARSED"


def test_strongswan_parser_does_not_infer_unconfigured_pfs_or_mode():
    parsed = VendorConfigParser.parse_config(
        "connections {\n  vpn {\n    version = 2\n"
        "    proposals = aes256gcm16-prfsha256-ecp256\n  }\n}\n"
    )

    assert parsed["vendor"] == VendorConfigParser.VENDOR_STRONGSWAN
    assert parsed["ike_version"] == "IKEv2"
    assert parsed["encryption"] == "AES-256-GCM"
    assert parsed["dh_group"] == "19"
    assert parsed["prf"] == "SHA256"
    assert parsed["pfs"] is None
    assert parsed["mode"] is None
    assert parsed["source_ip"] is None
    assert parsed["destination_ip"] is None


def test_fortinet_multiple_dh_groups_are_not_misreported_as_negotiated_group():
    parsed = VendorConfigParser.parse_config(
        "config vpn ipsec phase1-interface\n"
        " edit vpn\n"
        "  set ike-version 2\n"
        "  set proposal aes256gcm-prfsha256\n"
        "  set dhgrp 19 14\n"
        " next\n"
        "end\n"
    )

    assert parsed["ike_version"] == "IKEv2"
    assert parsed["encryption"] == "AES-256-GCM"
    assert parsed["dh_group"] is None
    assert parsed["pfs"] is None
    assert parsed["destination_ip"] is None


def test_unrecognized_generic_text_is_rejected_instead_of_returning_fabricated_config():
    with pytest.raises(ValueError, match="No supported IPsec configuration fields"):
        VendorConfigParser.parse_config("this is not an IPsec configuration")


def test_malformed_xml_is_rejected_instead_of_falling_back_to_defaults():
    with pytest.raises(ValueError, match="Invalid pfSense/OPNsense XML"):
        VendorConfigParser.parse_config(
            "<ipsec><phase1><iketype>ikev2</phase1>",
            override_vendor=VendorConfigParser.VENDOR_PFSENSE,
        )


def test_vendor_config_analysis_does_not_invent_capture_or_traffic_evidence(monkeypatch):
    received = {}
    monkeypatch.setattr(
        protocol_engine,
        "build_unified_analysis_report",
        lambda ingest, traffic, findings, recommendations, risk: (
            received.update(ingest=ingest, traffic=traffic) or {
                "explainability": [],
                "security_assessment": {},
            }
        ),
    )
    monkeypatch.setattr(protocol_engine, "generate_html_report", lambda report, path: path)
    monkeypatch.setattr(
        "reports.report_generator.save_json_report",
        lambda report, path: None,
    )

    result = protocol_engine.ProtocolIdentificationEngine().analyze_vendor_config(
        "crypto isakmp policy 10\n encr 3des\n group 2\n",
        filename="test.cfg",
        vendor=VendorConfigParser.VENDOR_CISCO,
    )

    assert received["traffic"] is None
    assert received["ingest"]["flow_features"] is None
    assert received["ingest"]["source_ip"] is None
    assert result.analysis_source == "vendor_config"
    assert result.traffic_classification is None
    assert result.esp_detected is None
    assert result.replay_protection is None
    assert result.data_provenance["encryption"] == "PARSED"
    assert result.data_provenance["pfs"] == "UNKNOWN"
