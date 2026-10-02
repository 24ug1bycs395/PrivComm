"""Tests for active probe consent and allowlist barriers."""

import hashlib

from probe import allowlist
from probe.consent import check_double_barrier


def test_double_barrier(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "probe_allowlist.json"
    monkeypatch.setattr(allowlist, "ALLOWLIST_FILE", str(allowlist_path))
    target = "192.0.2.10"
    token = hashlib.sha256(f"PRIVCOMM-PROBE-CONSENT:{target}".encode()).hexdigest()
    assert not check_double_barrier(target, token)[0]
    allowlist.add_to_allowlist(target, "tester", "integration test")
    assert check_double_barrier(target, token)[0]
    assert not check_double_barrier(target, "wrong")[0]


def test_allowlist_crud(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(allowlist, "ALLOWLIST_FILE", str(tmp_path / "allowlist.json"))
    allowlist.add_to_allowlist("192.0.2.11", "tester", "test")
    assert allowlist.is_allowed("192.0.2.11")
    assert len(allowlist.list_allowlist()) == 1
    allowlist.remove_from_allowlist("192.0.2.11")
    assert not allowlist.is_allowed("192.0.2.11")
