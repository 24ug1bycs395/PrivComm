from fastapi.testclient import TestClient

from main import app
from services.testbed.config_generator import StrongSwanConfigGenerator
from services.testbed.models import PRESET_SCENARIOS, ScenarioDefinition, TestbedTopology
from services.testbed.orchestrator import TestbedOrchestrator


def test_scenario_default_hash_algorithm():
    """Verify ScenarioDefinition defaults to SHA-256 and accepts custom hash types."""
    scenario = ScenarioDefinition(
        id="test-tunnel",
        name="Test Tunnel",
        description="Testing hash configuration"
    )
    assert scenario.hash_algorithm == "SHA-256"


def test_all_presets_have_default_hash():
    """Verify all built-in testbed scenarios have an explicit valid hash algorithm."""
    valid_hashes = {"SHA-256", "SHA-384", "SHA-512", "MD5", "SHA-1"}
    for preset in PRESET_SCENARIOS:
        assert hasattr(preset, "hash_algorithm")
        assert preset.hash_algorithm in valid_hashes
        if "weak" in preset.id:
            assert preset.hash_algorithm == "MD5"
        elif "cnsa" in preset.id or "ipv6-tunnel" in preset.id:
            assert preset.hash_algorithm == "SHA-384"
        else:
            assert preset.hash_algorithm in {"SHA-256", "SHA-384"}


def test_handshake_integrity_is_not_claimed_from_configured_parameters():
    """Configured proposals are context, not cryptographic handshake evidence."""
    topology = TestbedTopology()

    s_sha256 = ScenarioDefinition(
        id="test-sha256",
        name="SHA-256 Tunnel",
        description="Testing SHA-256 handshake integrity",
        hash_algorithm="SHA-256",
        pre_shared_key="super-secret-test-value",
    )
    res_sha256 = TestbedOrchestrator.compute_handshake_integrity(s_sha256, topology)
    assert res_sha256["status"] == "NOT_VERIFIED"
    assert res_sha256["verification_method"] == "configuration_only"
    assert res_sha256["configured_parameters"]["integrity"] == "SHA-256"
    assert "handshake_digest" not in res_sha256
    assert "super-secret-test-value" not in repr(res_sha256)

    s_sha384 = ScenarioDefinition(
        id="test-sha384",
        name="SHA-384 Tunnel",
        description="Testing SHA-384 handshake integrity",
        hash_algorithm="SHA-384"
    )
    res_sha384 = TestbedOrchestrator.compute_handshake_integrity(s_sha384, topology)
    assert res_sha384["status"] == "NOT_VERIFIED"
    assert res_sha384["configured_parameters"]["integrity"] == "SHA-384"

    s_md5 = ScenarioDefinition(
        id="test-md5",
        name="MD5 Legacy Tunnel",
        description="Testing MD5 handshake integrity",
        hash_algorithm="MD5",
        is_weak_compliance=True
    )
    res_md5 = TestbedOrchestrator.compute_handshake_integrity(s_md5, topology)
    assert res_md5["status"] == "NOT_VERIFIED"
    assert res_md5["configured_parameters"]["integrity"] == "MD5"


def test_config_generator_proposal_incorporates_hash():
    """Verify strongSwan configuration dynamically incorporates selected hash into proposals."""
    topology = TestbedTopology()

    # Scenario with SHA-384
    s384 = ScenarioDefinition(
        id="test-prop-384",
        name="Prop 384",
        description="Prop with SHA-384",
        encryption="AES-256-GCM",
        hash_algorithm="SHA-384"
    )
    conf384 = StrongSwanConfigGenerator.generate_swanctl_conf(s384, topology, is_initiator=True)
    assert "prfsha384" in conf384

    # Scenario with 3DES + MD5
    s_md5 = ScenarioDefinition(
        id="test-prop-md5",
        name="Prop MD5",
        description="Prop with MD5",
        encryption="3DES-CBC",
        hash_algorithm="MD5"
    )
    conf_md5 = StrongSwanConfigGenerator.generate_swanctl_conf(s_md5, topology, is_initiator=True)
    assert "3des-md5" in conf_md5

    # Scenario with AES-256-CBC + SHA-512
    s512 = ScenarioDefinition(
        id="test-prop-512",
        name="Prop 512",
        description="Prop with SHA-512",
        encryption="AES-256-CBC",
        hash_algorithm="SHA-512"
    )
    conf512 = StrongSwanConfigGenerator.generate_swanctl_conf(s512, topology, is_initiator=True)
    assert "aes256-sha512" in conf512


def test_api_scenarios_includes_hash_algorithm():
    """Verify GET /api/testbed/scenarios returns hash_algorithm in all scenario objects."""
    client = TestClient(app)
    response = client.get("/api/testbed/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) > 0
    for s in scenarios:
        assert "hash_algorithm" in s
        assert s["hash_algorithm"] in ["SHA-256", "SHA-384", "SHA-512", "MD5", "SHA-1"]
