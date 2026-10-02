"""
4-Tier Provenance System for PrivComm Security Findings.

Every security parameter carries a provenance tier that records *how* the value
was obtained.  This makes false-pass findings structurally impossible:

    OBSERVED  — value was confirmed directly from wire traffic / active probe
    PARSED    — value was extracted from a static configuration file
    INFERRED  — value was produced by an ML model or heuristic (confidence attached)
    UNKNOWN   — value could not be determined; rule emits CANNOT_ASSESS

Design principles:
  - Rules that receive an UNKNOWN fact MUST NOT emit a PASS verdict.
  - Rules that receive an INFERRED fact MUST attach the confidence score.
  - The provenance tier travels alongside every SecurityFinding as a first-class field.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Tier enumeration
# ---------------------------------------------------------------------------

class ProvenanceTier(str, Enum):
    """Ordered tiers from highest to lowest certainty."""

    OBSERVED = "OBSERVED"   # confirmed from live wire / active IKE probe
    PARSED   = "PARSED"     # extracted from a static config file
    INFERRED = "INFERRED"   # produced by ML model or heuristic
    UNKNOWN  = "UNKNOWN"    # could not be determined


# Certainty ordering (higher index = lower certainty)
_TIER_ORDER = [
    ProvenanceTier.OBSERVED,
    ProvenanceTier.PARSED,
    ProvenanceTier.INFERRED,
    ProvenanceTier.UNKNOWN,
]


def weaker_tier(a: ProvenanceTier, b: ProvenanceTier) -> ProvenanceTier:
    """Return the tier with lower certainty (used when merging two sources)."""
    return a if _TIER_ORDER.index(a) >= _TIER_ORDER.index(b) else b


# ---------------------------------------------------------------------------
# Tagged fact — a value plus its provenance
# ---------------------------------------------------------------------------

@dataclass
class ProvenancedFact:
    """
    A security parameter value annotated with its provenance tier.

    Attributes:
        value:       The raw parameter value (str, int, bool, None, …).
        tier:        How this value was obtained.
        source:      Human-readable description of the source
                     (e.g. "IKE_SA_INIT response packet", "swanctl.conf §connections").
        confidence:  Optional confidence score in [0.0, 1.0], only meaningful for INFERRED.
        note:        Optional extra annotation (e.g. "retransmit deduplicated").
    """

    value: Any
    tier: ProvenanceTier
    source: str = ""
    confidence: Optional[float] = None
    note: str = ""

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def observed(cls, value: Any, source: str = "", note: str = "") -> "ProvenancedFact":
        """Wire-confirmed value."""
        return cls(value=value, tier=ProvenanceTier.OBSERVED, source=source, note=note)

    @classmethod
    def parsed(cls, value: Any, source: str = "", note: str = "") -> "ProvenancedFact":
        """Static-config extracted value."""
        return cls(value=value, tier=ProvenanceTier.PARSED, source=source, note=note)

    @classmethod
    def inferred(
        cls,
        value: Any,
        source: str = "",
        confidence: float = 0.5,
        note: str = "",
    ) -> "ProvenancedFact":
        """ML / heuristic produced value."""
        return cls(
            value=value,
            tier=ProvenanceTier.INFERRED,
            source=source,
            confidence=round(confidence, 4),
            note=note,
        )

    @classmethod
    def unknown(cls, note: str = "") -> "ProvenancedFact":
        """Value could not be determined."""
        return cls(value=None, tier=ProvenanceTier.UNKNOWN, source="", note=note)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_known(self) -> bool:
        """True unless the tier is UNKNOWN."""
        return self.tier is not ProvenanceTier.UNKNOWN

    @property
    def is_assessable(self) -> bool:
        """
        True when a rule may emit a deterministic verdict.
        UNKNOWN → cannot assess; rules must not pass or fail on this fact.
        """
        return self.tier is not ProvenanceTier.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d

    def __repr__(self) -> str:
        conf_str = f", conf={self.confidence:.2f}" if self.confidence is not None else ""
        return (
            f"ProvenancedFact({self.tier.value}: {self.value!r}"
            f"{conf_str}"
            f"{', ' + self.source if self.source else ''})"
        )


# ---------------------------------------------------------------------------
# Provenance context — a dict of named facts for one analysis run
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceContext:
    """
    Container that holds ProvenancedFacts for every IPsec parameter in a run.

    Usage::

        ctx = ProvenanceContext()
        ctx.set("ike_version", ProvenancedFact.observed("IKEv2", source="IKE_SA_INIT pkt"))
        ctx.set("encryption",  ProvenancedFact.inferred("AES-256-GCM", confidence=0.85))
        ctx.set("dh_group",    ProvenancedFact.unknown())

        fact = ctx.get("dh_group")
        if not fact.is_assessable:
            # emit CANNOT_ASSESS — do NOT emit PASS
            ...
    """

    _facts: dict[str, ProvenancedFact] = field(default_factory=dict, repr=False)

    def set(self, key: str, fact: ProvenancedFact) -> None:
        """Store a fact. Overwrites previous value for the same key."""
        self._facts[key] = fact

    def get(self, key: str) -> ProvenancedFact:
        """
        Retrieve a fact by key.
        Returns ProvenancedFact.unknown() if the key was never set.
        """
        return self._facts.get(key, ProvenancedFact.unknown(note=f"key '{key}' not set"))

    def value_of(self, key: str, default: Any = None) -> Any:
        """Shortcut to retrieve just the raw value (or *default* if UNKNOWN)."""
        fact = self.get(key)
        return fact.value if fact.is_known else default

    def tier_of(self, key: str) -> ProvenanceTier:
        """Return the provenance tier for *key* (UNKNOWN if never set)."""
        return self.get(key).tier

    def summary(self) -> dict[str, dict[str, Any]]:
        """Serialise the entire context to a plain dict for JSON output."""
        return {k: v.to_dict() for k, v in self._facts.items()}

    def all_keys(self) -> list[str]:
        return list(self._facts.keys())

    def unknown_keys(self) -> list[str]:
        return [k for k, v in self._facts.items() if not v.is_known]

    def observed_keys(self) -> list[str]:
        return [k for k, v in self._facts.items() if v.tier is ProvenanceTier.OBSERVED]


# ---------------------------------------------------------------------------
# Helper: build a ProvenanceContext from the ipsec_config dict produced by
#         analyzer/ipsec_parser.py  (which uses string sentinel "unknown")
# ---------------------------------------------------------------------------

_SOURCE_PCAP = "passive PCAP wire analysis"
_SOURCE_RFC4303 = "RFC 4303 arithmetic cipher elimination"


def build_context_from_ipsec_config(ipsec_config: dict[str, Any]) -> ProvenanceContext:
    """
    Wrap an existing ipsec_config dict (from ipsec_parser.synthesize_ipsec_config)
    in a ProvenanceContext, assigning tiers based on available evidence.

    Tier assignment heuristic (no config-file parser yet in PrivComm):
    - Value present and non-"unknown"  → OBSERVED (came from wire / PCAP)
    - RFC 4303 arithmetic provenance   → INFERRED (with confidence from rfc4303 result)
    - Value is None / "unknown"        → UNKNOWN
    """
    ctx = ProvenanceContext()

    def _tier_for(val: Any, key: str) -> ProvenancedFact:
        if val is None or val == "unknown":
            return ProvenancedFact.unknown(note=f"{key} not present in capture")
        return ProvenancedFact.observed(val, source=_SOURCE_PCAP)

    # Core IPsec parameters
    for key in (
        "ike_version",
        "exchange_type",
        "initiator_spi",
        "responder_spi",
        "dh_group",
        "integrity",
        "prf",
        "mode",
        "ip_version",
        "source_ip",
        "destination_ip",
    ):
        ctx.set(key, _tier_for(ipsec_config.get(key), key))

    # Encryption: may have been overridden by RFC 4303 arithmetic
    enc_val = ipsec_config.get("encryption")
    enc_prov = ipsec_config.get("encryption_provenance", "")
    if enc_prov == "rfc4303_arithmetic":
        rfc_conf: float = float(ipsec_config.get("rfc4303_confidence", 0.85))
        ctx.set(
            "encryption",
            ProvenancedFact.inferred(
                enc_val,
                source=_SOURCE_RFC4303,
                confidence=rfc_conf,
                note="sole viable cipher after block-size elimination",
            ),
        )
    else:
        ctx.set("encryption", _tier_for(enc_val, "encryption"))

    # PFS: only observable from CREATE_CHILD_SA with KE payload
    pfs_val = ipsec_config.get("pfs")
    if pfs_val in (None, "unknown"):
        ctx.set(
            "pfs",
            ProvenancedFact.unknown(
                note="PFS requires CREATE_CHILD_SA + DH payload in capture"
            ),
        )
    else:
        ctx.set("pfs", ProvenancedFact.observed(pfs_val, source=_SOURCE_PCAP))

    # SA lifetime: only observable from IKE_AUTH (usually encrypted)
    lifetime = ipsec_config.get("sa_lifetime")
    if lifetime is None:
        ctx.set(
            "sa_lifetime",
            ProvenancedFact.unknown(
                note="SA lifetime is carried in encrypted IKE_AUTH payload"
            ),
        )
    else:
        ctx.set("sa_lifetime", ProvenancedFact.observed(lifetime, source=_SOURCE_PCAP))

    # Key length (may be parsed from SA transform attribute)
    kl = ipsec_config.get("key_length")
    if kl is None:
        ctx.set("key_length", ProvenancedFact.unknown(note="key_length not in SA proposals"))
    else:
        ctx.set("key_length", ProvenancedFact.observed(kl, source=_SOURCE_PCAP))

    return ctx
