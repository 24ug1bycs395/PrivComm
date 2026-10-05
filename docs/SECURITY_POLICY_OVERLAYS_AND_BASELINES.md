# Policy overlays, probe authorization, and downgrade baselines

## Policy overlay

The shipped policy remains at `config/security_policy.yaml`. An optional partial YAML
overlay can be enabled with `SECURITY_POLICY_OVERLAY_PATH`. The overlay may only use
keys already present in the baseline and must preserve each field's YAML type. Nested
maps merge recursively; a list in the overlay replaces the corresponding baseline
list. Unknown keys, malformed YAML, and missing configured files are errors rather
than reasons to silently use a fallback policy.

Example:

```yaml
policy_name: "Acme VPN overlay"
version: "2026-01"
encryption:
  approved:
    - "AES-256-GCM"
  forbidden:
    - "DES"
    - "3DES"
```

Policy findings and policy-as-code checks consume the same effective baseline and
overlay. The report includes the policy name and version. The overlay is configuration,
not a replacement for review of the baseline.

## Per-tunnel downgrade tracking

`POST /analyze/protocol?tunnel_id=<stable-id>&record_baseline=true` records observed
values from that uploaded capture. Recording requires the
`X-PrivComm-Baseline-Authorization` header to match a separately provisioned
`IPSEC_BASELINE_AUTH_SECRET` of at least 32 bytes. The secret must be provisioned
out-of-band and the API must be restricted to authorized operators; it must not be
put in the browser bundle or source control.

The baseline file defaults to `config/tunnel_baselines.json` and can be relocated with
`IPSEC_BASELINES_PATH`. Back it up and restrict filesystem access. A later analysis
with the same `tunnel_id` compares only known fields. Unknown observations remain
`INSUFFICIENT_EVIDENCE`; changed values without a defined strength ordering are
reported as changes, not downgrades. The identifier is operator-supplied and must
represent the same tunnel over time.

Without `record_baseline=true`, supplying `tunnel_id` only compares against existing
history. No history produces `NO_BASELINE`; it does not imply a pass or downgrade.

## Active probe authorization

Active probe execution requires both an exact destination entry in the operator
allowlist and a short-lived HMAC token scoped to that IP. Configure a random
`PROBE_CONSENT_SECRET` of at least 32 bytes on the server. Tokens are for out-of-band
operator use; there is intentionally no unauthenticated token-issuance endpoint.
Tokens expire after at most one hour. Keep the configured allowlist restricted to
testbed addresses and do not expose the probe API to untrusted clients.

## Capture and report evidence

Capture byte offsets are zero-based and ranges are half-open. Every capture analysis
includes a SHA-256 digest and available frame/packet evidence. A reference to an IKE
message is packet context, not proof of encrypted or unobserved configuration. The
exported `privcomm.cbom.v1` inventory records unknown fields explicitly; it is a
PrivComm schema and does not claim CycloneDX conformance.

## Model and PQC evidence boundaries

The classifier evaluation command writes descriptive top-label ECE and multiclass
Brier metrics alongside the untouched test metrics and a model card. It does not
calibrate model probabilities. `--ablation` trains feature-group ablations on the
existing held-out split without replacing the checked-in model. Preprocessing uses
disjoint capture groups only when a capture identifier is present; otherwise the
schema records that evaluation was row-level and capture grouping was unavailable.

PQC output reports unknowns rather than inferring readiness from IKEv2 or an
unobserved DH group. The Mosca-style calculation requires caller-supplied data
shelf-life, migration lead-time, and CRQC-horizon estimates; it is not a forecast.
CNSA 2.0 is identified by profile version and source, but configuration observations
alone do not establish compliance or certification.

## Vendor configuration and testbed evidence

Static vendor configuration parsing is reported as `analysis_source: vendor_config`.
Missing values stay unknown, and packet-only fields such as ESP/AH detection, replay
behavior, and outer IP version are null for this input type. Parsed configuration
values are not presented as negotiated wire observations. A generated vendor snippet
is a review-required template, not an applied patch or verified remediation.

The testbed's configured proposal summary is not a handshake-integrity attestation.
The previous configuration-derived HMAC did not observe either endpoint and must not
be interpreted as proof of matching negotiation or zero tampering. Testbed capture
analysis no longer overwrites missing capture observations with scenario defaults.
Classifier top-class scores are raw and uncalibrated; ECE/Brier output measures
calibration but does not calibrate the model.
