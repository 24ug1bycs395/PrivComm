"""Tests for signed active-probe consent and allowlist barriers."""

from probe import allowlist, consent
from probe.consent import check_double_barrier, create_consent_token


def test_double_barrier(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "probe_allowlist.json"
    monkeypatch.setattr(allowlist, "ALLOWLIST_FILE", str(allowlist_path))
    monkeypatch.setenv("PROBE_CONSENT_SECRET", "test-secret-that-is-at-least-32-bytes")
    target = "192.0.2.10"
    token = create_consent_token(target)
    assert not check_double_barrier(target, token)[0]
    allowlist.add_to_allowlist(target, "tester", "integration test")
    assert check_double_barrier(target, token)[0]
    assert not check_double_barrier("192.0.2.11", token)[0]
    assert not check_double_barrier(target, "wrong")[0]


def test_consent_requires_server_secret(monkeypatch) -> None:
    monkeypatch.delenv("PROBE_CONSENT_SECRET", raising=False)
    allowed, reason = check_double_barrier("192.0.2.10", "anything")
    assert not allowed
    assert "authorization" in reason.lower()
    try:
        create_consent_token("192.0.2.10")
    except ValueError as exc:
        assert "PROBE_CONSENT_SECRET" in str(exc)
    else:
        raise AssertionError("Token creation must fail without a server-held secret.")


def test_expired_consent_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PROBE_CONSENT_SECRET", "test-secret-that-is-at-least-32-bytes")
    monkeypatch.setattr(consent.time, "time", lambda: 1000)
    token = create_consent_token("192.0.2.10", ttl_seconds=30)
    monkeypatch.setattr(consent.time, "time", lambda: 1030)
    allowed, reason = check_double_barrier("192.0.2.10", token)
    assert not allowed
    assert "expired" in reason.lower()


def test_allowlist_crud(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(allowlist, "ALLOWLIST_FILE", str(tmp_path / "allowlist.json"))
    allowlist.add_to_allowlist("192.0.2.11", "tester", "test")
    assert allowlist.is_allowed("192.0.2.11")
    assert len(allowlist.list_allowlist()) == 1
    allowlist.remove_from_allowlist("192.0.2.11")
    assert not allowlist.is_allowed("192.0.2.11")
