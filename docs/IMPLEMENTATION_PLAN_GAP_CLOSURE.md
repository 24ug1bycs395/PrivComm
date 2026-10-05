# PrivComm gap-closure implementation plan

**Date:** 2026-10-03  
**Scope:** Close the product-evidence and workflow gaps in the supplied competitor comparison.  
**Planning basis:** The six gaps and strategy notes supplied by the user, repository inspection, and the public competitor sources linked below. This is a brownfield plan, not an authorization to run active tests against third-party networks.

## Implementation checkpoint — 2026-10-03

The repository has implemented and locally validated the evidence/safety foundations
and policy/export work noted by checked tasks below. The complete Python suite reports
79 passed tests (3 warnings); the Vite production build succeeds with a >500 kB chunk
warning. This is a local run, not a CI result. Remaining work is intentionally visible:
no licensed independent-capture corpus was added, the deployed classifier has not been
retrained or re-evaluated, ablations have not been run with repeated grouped splits,
and no candidate approval/apply/fresh-capture retest workflow exists yet. The CBOM
endpoint and `privcomm.cbom.v1` output are present, but a formal schema validator and
per-component policy/confidence fields are still needed. The Mosca assessor computes
the inequality from caller-provided point estimates; it does not model uncertainty
ranges.

## Summary

Prioritize credibility and safe reproducibility before adding more dashboard features. PrivComm already has a strongSwan testbed, PCAP ingestion and analysis, a multi-vendor configuration-analysis path in the current worktree, a behavioral-model evaluation workflow, field-level provenance labels, a policy file, PQC assessment code, and active-probe consent checks. The principal gaps are that those foundations do not yet form a consistently evidenced, independently validated, end-to-end user workflow.

Deliver in this order:

1. Make testbed and active-probe claims auditable, scoped, and safe.
2. Harden parsers with deterministic fuzzing and independently sourced real-capture regression tests; expose precise packet evidence.
3. Publish reproducible model cards and ablations based on capture-grouped evaluation, not just headline scores.
4. Add versioned policy overlays, downgrade tracking, crypto inventory export, and source-backed CNSA 2.0 / Mosca-oriented assessment.
5. Join configuration remediation to a preview, isolated application, capture, and retest loop.

Do not increase test count merely to match competitor numbers. Track collected and passing tests, fuzz inputs, corpus coverage, and validation axes separately.

## Current-state findings

| Area | Present foundation in this worktree | Remaining gap / planning implication |
|---|---|---|
| Config ingestion | Vendor-specific static-config parsing and endpoints exist; missing parameters remain unknown and the response identifies the input as `vendor_config`. | Parser confidence is still limited by global text matching and does not yet support reviewable, approval-bound remediation candidates. |
| Testbed and attacks | strongSwan orchestration and PCAP retrieval exist; the attack simulator is telemetry-only. Scenario configuration no longer overwrites missing capture observations, and configured values are not labeled a handshake attestation. | Keep future real actions explicitly authorized and confined to the isolated testbed; add an end-to-end approved apply/fresh-capture/retest flow. |
| Probe consent | The probe requires exact allowlist membership and a short-lived HMAC token scoped to the target IP. | Provision and restrict the server secret and testbed allowlist operationally; no token-minting endpoint is provided. |
| Parser evidence | The custom PCAP decoder now carries capture identity and frame/byte references into result/report/UI paths. Static vendor config analysis now leaves absent fields and packet-only facts unverified. | Independent real-capture regressions and provenance review of every vendor grammar remain open. |
| External captures | A bundled sample and strict real-strongSwan testbed dataset generation exist. | There is not yet a maintained, independently sourced, hash-verified capture corpus with external ground truth and automated regression coverage. |
| ML evidence | An XGBoost model card, classifier calibration metrics, anomaly-model card generation, and a capture-grouped split implementation are present. Existing checked-in XGBoost metrics are still row-level (6,149 test samples, 91.12% accuracy); the dataset has no capture/source ID. | Grouped evaluation, repeated-split ablations, and external evaluation cannot be claimed until suitable source IDs/captures are available and the evaluation is run. |
| Policy / PQC | The policy overlay, authenticated baseline recording/comparison, capture-backed `privcomm.cbom.v1` export, and source-cited PQC/Mosca boundaries are implemented. Unknown values do not imply compliance. | The CBOM still needs formal schema validation and richer per-component confidence/policy context. CNSA applicability is reported, not assessed for compliance; Mosca accepts caller point estimates, not uncertainty ranges. |
| Remediation and retest | Vendor templates are review-required suggestions; testbed scenario results are no longer overwritten with configured values. | No candidate approval, isolated config apply, fresh retest capture, or evidence-backed before/after comparison workflow exists yet. Do not claim a retest from telemetry or score deltas. |
| Test volume | The full local pytest run collected and passed 79 tests, with 3 warnings; it is not a CI baseline. A deterministic malformed-packet sweep covers the dependency-free decoder. | Add IKE-parser mutation coverage, CI reporting, scheduled fuzzing, and independent-capture regressions. Do not compare declaration counts with executed tests. |

The testbed no longer labels an HMAC synthesized from configured parameters as a
verified handshake attestation. It reports configuration context as not verified and
does not overwrite capture analysis with scenario values. The UI likewise no longer
substitutes mock analysis when a sample endpoint fails or displays default crypto
values as observed facts. Raw classifier top-class scores are labeled uncalibrated.

The deterministic malformed-input sweep covers 128 generated packet records in the
custom decoder; it does not yet exercise `ike_parser.py` or run as a scheduled
fuzzing job. Grouped preprocessing preserves capture IDs through cleaning while
excluding them from model features, but the current dataset has no such ID and the
deployed model was not retrained. Feature-ablation commands exist but no grouped,
repeated-split ablation was run. The CBOM export remains partial as described above.
The Mosca calculation uses caller-provided point estimates; no uncertainty range is
modeled.

The current worktree had unrelated in-progress changes when inspected. Implementation must preserve them and confirm the config-ingestion changes are reviewed and committed independently before relying on them as a baseline.

## Competitor evidence reviewed

The comparison below is limited to public sources that could be unambiguously located and inspected. It does not independently verify every number or claim in the supplied comparison.

| Public source | Verifiable signal relevant to this plan |
|---|---|
| [CipherGuard](https://github.com/Git-huber2007/CipherGuard) [fuzz tests](https://github.com/Git-huber2007/CipherGuard/blob/main/tests/test_fuzz.py) and [real-capture tests](https://github.com/Git-huber2007/CipherGuard/blob/main/tests/test_realworld.py) | The checked-in tests exercise mutated/malformed IKE inputs and real captures with externally grounded expectations. This supports prioritizing parser robustness and independent fixtures, rather than simply increasing ordinary unit-test totals. |
| [RAKSHAK.VYUH](https://github.com/Muneerali199/rakshak-vyuh) [corpus tests](https://github.com/Muneerali199/rakshak-vyuh/blob/main/crates/vyuh-core/tests/corpus.rs) and [robustness tests](https://github.com/Muneerali199/rakshak-vyuh/blob/main/crates/vyuh-core/tests/robustness.rs) | Its public README describes a passive-only analyzer with RFC-cited, packet-numbered findings. Checked-in Rust tests assert selected IKE facts against tcpdump/live-gateway ground truth and exercise truncation, byte corruption, and length escalation against a real-capture corpus. Its robustness test notes that a missing generated corpus means the run proves nothing; PrivComm's CI should require corpus presence for any job that claims real-capture coverage. |
| [VaultScope](https://github.com/shivansh193/vaultscope) [dataset datasheet](https://github.com/shivansh193/vaultscope/blob/main/data/DATASHEET.md) | The datasheet documents 300 captures, labels, integrity manifests, matrix coverage, generation conditions, and known limits (including single-tunnel/lab-clean data and untested vendors). This is a useful standard for dataset disclosure, not proof that those measurements transfer to production. |
| [OMEGA](https://github.com/Prasanna-ETH/IPsec) [comparison API](https://github.com/Prasanna-ETH/IPsec/blob/master/backend/app/api/compare.py), [comparison engine](https://github.com/Prasanna-ETH/IPsec/blob/master/backend/app/engines/comparison_engine.py), and [pipeline tests](https://github.com/Prasanna-ETH/IPsec/blob/master/backend/tests/test_pipeline.py) | Public source includes frame-numbered evidence fields (and optional raw bytes) and a baseline/remediation capture comparison API with tests. The inspected comparison implementation defaults missing posture fields and treats a negative risk-score delta as verification; PrivComm should adopt the useful comparison workflow while requiring evidence-backed observations and explicit unknowns before claiming remediation is verified. |
| [TunnelTrace-AI](https://github.com/sharancode3/TunnelTrace-AI) | Located by repository search. The user-supplied comparison attributes a closed-loop retest advantage to TunnelTrace; this plan treats that as a product requirement, not as an independently verified implementation claim. |
| X-Ray and “IPsec Sentinel” | The names in the supplied notes did not resolve unambiguously to the intended public repositories in this inspection. Their specific claims and the stated competitor test-count range remain user-provided inputs until repository URLs/owners are supplied. |

## Requirements

- **REQ-001 — Robust validation:** Parser and API behavior must be exercised with malformed/adversarial inputs, a measured test baseline, and repeatable testbed scenarios.
- **REQ-002 — Independent capture validation:** Validate supported parsing and policy behavior against legally usable, independently sourced captures with recorded provenance, checksums, and expected observations.
- **REQ-003 — Defensible ML evidence:** Publish dataset/model cards, held-out metrics, calibration evidence, ablations, and limitations for the production classifier and the behavioral detector.
- **REQ-004 — Traceable evidence:** Every packet-derived finding or key observation should link to the capture identity and a precise frame/byte location where available; unknown or inferred values must remain labeled as such.
- **REQ-005 — Useful crypto posture:** Support an organization-specific policy overlay, per-tunnel downgrade/baseline tracking, CBOM export, and transparent CNSA 2.0 / Mosca-oriented readiness information.
- **REQ-006 — Closed-loop retest:** Allow a user to review a suggested configuration fix, validate it, run it only in an authorized lab or supported offline validator, and compare a subsequent analysis with the baseline.
- **REQ-007 — Active-tool safety:** Clearly separate passive analysis, simulation, lab activity, and active probing. Deny active activity outside the explicit authorization and scope boundary.

## Technical approach and invariants

- Keep the existing shared pipeline: ingestion → IKE/ESP/AH parsing and flow features → classification → policy → findings/recommendations → unified report.
- Add evidence metadata to the existing result contract; do not create a separate parser or classifier path for external captures.
- Split datasets by capture, run, or originating source before windowing. Do not put windows from one capture/run on both sides of a train/test split.
- Keep controlled/synthetic and observed data explicitly distinguished. Publish no model metric without sample counts, split method, class support, and limitations.
- Treat policy configuration and observed negotiation as separate records. A policy finding must not be presented as proof that an observed tunnel negotiated a prohibited option unless the capture supports that claim.
- Retest should default to preview/dry-run. Never automatically push a generated configuration to an external/production gateway as part of this scope.
- Preserve the existing dirty worktree and avoid retraining/replacing the deployed XGBoost artifact until the reproducible evaluation demonstrates a justified model change.

## Implementation steps

### Step 1: [Cross-cutting] Establish safe scope and a trustworthy baseline

- **Requirements:** REQ-001, REQ-006, REQ-007
- **Description:** Record actual test collection and baseline results; clarify the execution mode of the current attack simulator; harden authorization and testbed boundaries before extending active behavior.

#### Tasks

- [ ] T001 [Plan:1.1] Run the existing Python test suite in CI and record collected, passed, failed, and skipped counts by test layer in the CI summary; retain the baseline artifacts without changing the model.
- [ ] T002 [Plan:1.1] Add scoped parser fuzz/property tests around `analyzer/pcap_decoder.py` and `analyzer/ike_parser.py`; require deterministic seeds, bounded input sizes, no uncaught parser exceptions, and a time-bounded CI smoke corpus, with a larger scheduled corpus.
- [x] T003 [Plan:1.2] Update `services/testbed/attack_simulator.py` and its API/UI surfaces so modeled telemetry cannot be described as a live attack; return explicit execution mode and evidence that matches actual behavior.
- [x] T004 [Plan:1.2] Replace the reproducible target-derived probe token in `probe/consent.py` with auditable, expiring authorization; default active destinations to the isolated testbed allowlist and test denial for missing, expired, malformed, and out-of-scope authorization in `tests/test_probe_consent.py`.

### Step 2: [US1] Validate parsers against independent captures and expose packet evidence

- **Requirements:** REQ-001, REQ-002, REQ-004
- **Description:** Build an external regression corpus with stable checksums and expected facts, then thread packet locations from ingestion through reports and the UI.

#### Tasks

- [ ] T005 [US1] [Plan:2.1] Add a small licensed/redistributable independent PCAP fixture set and manifest under `tests/fixtures/pcap/` with source URL, license, SHA-256, capture conditions, expected observable IKE/ESP facts, and documented unsupported/unknown fields.
- [ ] T006 [US1] [Plan:2.1] Add parametrized regressions in `tests/test_pcap_decoder.py`, `tests/test_ipsec_parser.py`, and `tests/test_protocol_engine.py` that compare parsed protocol facts with the fixture manifest on both the TShark path and the Scapy fallback where available.
- [x] T007 [US1] [Plan:2.2] Extend `analyzer/pcap_decoder.py` result records with frame index and capture-record byte range, then attach protocol-payload offsets to IKE/ESP evidence without losing original-file coordinate semantics.
- [x] T008 [US1] [Plan:2.2] Extend `models/protocol_analysis.py`, `services/protocol_engine.py`, `reports/report_generator.py`, and `frontend/src/components/AnalyzerWorkspace.jsx` to preserve and display evidence references with capture hash, frame, timestamp, and byte range; represent absent locations as unavailable, not fabricated.
- [x] T009 [US1] [Plan:2.2] Add round-trip tests proving evidence offsets select the expected original bytes for PCAP and PCAPNG fixtures and proving evidence survives the API/report serialization path.

### Step 3: [US2] Publish defensible classifier and anomaly-model evidence

- **Requirements:** REQ-003
- **Description:** Make evaluation capture-aware and repeatable; publish evidence and caveats without implying probability calibration or production generalization where not demonstrated.

#### Tasks

- [ ] T010 [US2] [Plan:3.1] Audit `traffic-classifier/src/preprocess.py`, `traffic-classifier/src/train.py`, and the current train/validation/test artifacts for duplicate and source leakage; split by source/capture before creating windows and record the split manifest.
- [x] T011 [US2] [Plan:3.1] Add a reproducible model-card generator for the existing XGBoost classifier and `ml/anomaly` detector, recording dataset source/version, row and capture counts, class support, split method, feature list, training parameters, per-class metrics, calibration definition, and known limitations.
- [ ] T012 [US2] [Plan:3.2] Add controlled feature ablations for rate/volume features, timing features, and remaining features; report held-out per-class and macro metrics with confidence intervals or repeated split variation, and retain the current artifact unless comparison justifies a change.
- [x] T013 [US2] [Plan:3.2] Evaluate probability calibration for XGBoost (for example reliability plots and expected calibration error) and false-positive behavior for the anomaly detector; update UI/report text so raw scores and calibrated probabilities are not conflated.
- [ ] T014 [US2] [Plan:3.2] Add a capture-grouped external evaluation mode for independently sourced captures and report unavailable classes/metrics explicitly rather than silently substituting generated data.

### Step 4: [US3] Add policy context, downgrade monitoring, and cryptographic inventory

- **Requirements:** REQ-004, REQ-005
- **Description:** Keep the shipped baseline policy immutable by customer choice; layer organization rules and per-tunnel history over observed configuration, then export a machine-readable cryptographic bill of materials.

#### Tasks

- [x] T015 [US3] [Plan:4.1] Add a versioned policy-overlay schema and loader alongside `config/security_policy.yaml`; define deterministic merge/precedence, validation errors, and finding provenance so organization overrides cannot silently rewrite baseline rules.
- [x] T016 [US3] [Plan:4.1] Add a persisted per-tunnel baseline keyed by stable peer/tunnel identity and emit a downgrade/drift finding only when a newly observed negotiation regresses from a previously observed baseline or explicit policy; cover missing history and identity changes in tests.
- [ ] T017 [US3] [Plan:4.2] Extend `security/pqc_assessor.py` and policy data to map observed algorithms and key sizes to a versioned CNSA 2.0 profile; include source, version, date, applicability, and unknown status, and do not equate “CNSA-aligned” with certification.
- [ ] T018 [US3] [Plan:4.2] Add a versioned, source-cited Mosca-style exposure timeline that accepts data-retention/sensitivity and migration-lead-time inputs, exposes assumptions/ranges, and never presents a forecast date as a guaranteed quantum-break deadline.
- [ ] T019 [US3] [Plan:4.2] Define a versioned CBOM JSON schema and export endpoint/report action containing observed crypto algorithms, parameters, protocol roles, evidence references, confidence/provenance, policy context, and explicit unknowns; add schema and export round-trip tests.

### Step 5: [US4] Connect remediation to a safe apply-and-retest workflow

- **Requirements:** REQ-005, REQ-006, REQ-007
- **Description:** Turn existing recommendations and vendor configuration diffs into a reviewable candidate, validate it in an isolated path, and compare a real retest result to the original analysis.

#### Tasks

- [ ] T020 [US4] [Plan:5.1] Add a typed remediation candidate/result model that links a finding, original configuration, proposed diff, policy version, approval state, and validation result; preserve vendor and source-file identity from config ingestion.
- [ ] T021 [US4] [Plan:5.1] Add a preview-and-approve API/UI flow using the existing vendor configuration path; default to no external side effects and reject unsupported vendor transformations rather than returning a success-shaped diff.
- [ ] T022 [US4] [Plan:5.1] Add isolated testbed apply/retest orchestration using the generated candidate only when it maps safely to a supported strongSwan scenario; collect a fresh PCAP through the strict real-capture path and pass it through the existing analysis pipeline.
- [ ] T023 [US4] [Plan:5.2] Add before/after comparison for policy findings, negotiated parameters, and evidence references in the report/UI; distinguish “validated in testbed,” “validated offline,” “not retested,” and “failed retest,” and never substitute defaults for missing observations or declare success from a risk-score delta alone.
- [ ] T024 [US4] [Plan:5.2] Add end-to-end tests for weak configuration → proposed fix → approval → isolated retest → improved/unchanged result, including parser failure, capture unavailable, rejected candidate, and rollback/stop behavior.

## Testing strategy and release gates

- **Test layers:** Fast deterministic unit/property tests on every change; API/report integration tests; scheduled larger fuzz runs; external-capture regressions with pinned fixture manifests; isolated strongSwan integration tests; frontend workflow smoke test for evidence, CBOM download, and remediation state.
- **Parser acceptance:** Malformed/truncated inputs produce structured parse errors or an explicit rejection, never a fabricated successful finding or uncaught parser exception. Keep a bounded deterministic fuzz smoke suite in CI and a larger scheduled corpus; every discovered failure becomes a minimized regression fixture.
- **Independent-capture acceptance:** Every fixture has verified source/license, SHA-256, conditions, expected facts, and explicit known limitations. Tests must be skippable only when the separately provisioned corpus is intentionally absent; CI must run with the corpus present.
- **Evidence acceptance:** For supported packet formats, report locations map back to the exact fixture bytes and frame; the serialized API and generated report preserve the same references. Unknown values remain unknown.
- **ML acceptance:** Every published metric is reproducible from a checked-in command/config and names the evaluation split, source/capture count, support, and leakage controls. Ablations compare the same grouped held-out partitions. Calibration claims are accompanied by a metric/plot and sample count.
- **Policy acceptance:** Baseline and overlay behavior is deterministic and explainable; baseline drift requires a previous observation or an explicit policy, and each generated finding states which source drove it.
- **Closed-loop acceptance:** The default path is preview-only. A “retested” success requires a fresh analysis result from a new capture or a clearly labeled offline validator; baseline and retest facts must be observed or explicitly marked unknown, never filled with security-shaped defaults. A risk-score delta alone and simulated telemetry cannot satisfy this gate.
- **Safety acceptance:** Active probes and testbed attack workflows reject out-of-scope targets, missing/expired authorization, and unsupported execution modes. UI, API response, and audit evidence describe whether an operation was simulated, offline-validated, or actually run in the isolated testbed.

## Requirement mapping

| Requirement | Plan items | Completion evidence |
|---|---|---|
| REQ-001 — Robust validation | 1.1, 2.1 | Test baseline/CI summary, deterministic fuzz tests, and real-capture parser regressions in `tests/`. |
| REQ-002 — Independent capture validation | 2.1 | Licensed fixture corpus, provenance/checksum manifest, and TShark/Scapy regression results. |
| REQ-003 — Defensible ML evidence | 3.1, 3.2 | Dataset/model cards, grouped split manifest, ablation results, calibration report, and limitations. |
| REQ-004 — Traceable evidence | 2.2, 4.1 | Frame/byte evidence in API/report/UI, offset round-trip tests, and finding provenance. |
| REQ-005 — Useful crypto posture | 4.1, 4.2, 5.1 | Policy overlay, downgrade history, sourced CNSA/Mosca assessment, CBOM schema/export, remediation candidate records. |
| REQ-006 — Closed-loop retest | 5.1, 5.2 | Preview/approval flow, isolated retest result, before/after report, and end-to-end workflow tests. |
| REQ-007 — Active-tool safety | 1.2, 5.1 | Auditable authorization, explicit execution-mode contracts, scope-denial tests, and safe default behavior. |

## Suggested delivery sequence

1. **Trust/safety gate:** T001–T004.
2. **Evidence and parser reliability:** T005–T009.
3. **Evaluation transparency:** T010–T014.
4. **Policy and cryptographic inventory:** T015–T019.
5. **Closed-loop demonstration:** T020–T024.

The strongest demo is: analyze a known weak configuration, show a finding anchored to packet or configuration evidence, preview and approve the proposed change, apply it only in the isolated testbed, capture again, and show a verified before/after result. If the testbed is unavailable, the UI must label the outcome as not retested rather than simulating success.
