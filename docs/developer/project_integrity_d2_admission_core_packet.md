# D2 Admission Core Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted admission-core tests/scripts plus semantic Phase 0 baseline rerun
Purpose: bound the D2 slice around the additive SRS admission core so later inventory and helper workflow ports can build on it without blurring it into the semantic publication/runtime base
Source-of-truth: packet only; executable truth still lives in code, tests, scripts, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D2`
- Title: admission core audit
- Pass type: verification-only checkpoint with additive-core contract pinning

## Exact Seam

Primary code surface:

- `core/lexishift_core/srs/admission_features.py`
- `core/lexishift_core/srs/profile_bootstrap.py`
- `core/lexishift_core/srs/set_planner.py`
- `core/lexishift_core/helper/rulegen.py`

Primary tests/evidence surface:

- `core/tests/srs/test_profile_bootstrap.py`
- `core/tests/dev/test_srs_admission_preference_sanity.py`
- `core/tests/dev/test_srs_frequency_topic_coverage.py`
- `core/tests/srs/test_srs_set_planner.py`
- `core/tests/helper/test_helper_engine.py`
- `scripts/testing/srs_admission_preference_sanity.py`
- `scripts/testing/srs_frequency_topic_coverage.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- explicit active inventory persistence
- rebalance execution details
- initialize/refresh publication reconciliation
- due-aware serving
- helper-rule runtime confidence gating
- structural refactor of `profile_bootstrap.py` beyond confirming that its current contract remains additive

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the admission core now influences planning, preview, and future bootstrap behavior, so drift here can quietly change later D-phase assumptions
- the highest-risk mistake would be treating admission-core scoring and diagnostics as if they had already replaced helper publication/runtime contracts
- this seam is easier to miss than to crash because most failure modes look like overclaimed present-tense docs, not hard exceptions

## Contract Sketch

The intended current admission-core contract is:

1. `admission_features.py` owns the normalization and utility-signal substrate for profile-aware admission scoring
2. `profile_bootstrap.py` owns candidate-trait extraction, signal-pack construction, reranking, and diagnostics for profile-aware bootstrap exploration
3. planner/helper execution still treat that profile-aware layer as additive:
   - diagnostics and reranking are executable
   - bootstrap execution still falls back to `frequency_bootstrap`
4. none of that admission-core machinery replaces the semantic publication/runtime family
5. the structural size of `profile_bootstrap.py` remains a health concern, but not a D2 contract change

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Admission profile normalization and utility-signal shaping remain executable and separately testable. | `admission_features.py`, `profile_bootstrap.py` | `core/tests/srs/test_profile_bootstrap.py` | `verified for this slice` |
| Synthetic sanity/coverage scripts still validate the profile-aware admission-core signal path. | `profile_bootstrap.py`, testing scripts | `core/tests/dev/test_srs_admission_preference_sanity.py`, `core/tests/dev/test_srs_frequency_topic_coverage.py`, direct script runs | `verified for this slice` |
| Planner/helper still surface profile-bootstrap diagnostics while executable bootstrap falls back to frequency bootstrap. | `set_planner.py`, `helper/rulegen.py`, helper engine | `core/tests/srs/test_srs_set_planner.py`, targeted `core/tests/helper/test_helper_engine.py` coverage | `verified for this slice` |
| Admission core remains additive and does not displace the semantic publication/runtime base. | admission-core modules vs semantic Phase 0 suite | D1 Phase 0 suite rerun during D2 validation | `verified for this slice` |

## Invariants

1. admission-core normalization/reranking must stay separable from semantic helper publication
2. planner diagnostics must not be summarized as if they were already a different executable bootstrap path
3. profile-aware reranking evidence must not be mistaken for end-to-end helper publication changes
4. semantic Phase 0 protections must continue to hold while admission-core work advances
5. structural pressure in `profile_bootstrap.py` should be tracked as health work, not hidden inside contract claims

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Neutral profile context | reranking stays close to neutral frequency order |
| Explicit topic preferences | profile-aware lifts remain visible in tests/scripts |
| Topic-column coverage audit | frequency-source topic columns still satisfy the admission-core expectations |
| Planner/helper bootstrap request | diagnostics surface profile bootstrap while execution stays on `frequency_bootstrap` |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/srs/test_profile_bootstrap.py core/tests/dev/test_srs_admission_preference_sanity.py core/tests/dev/test_srs_frequency_topic_coverage.py core/tests/srs/test_srs_set_planner.py core/tests/helper/test_helper_engine.py -k "profile_bootstrap or srs_admission_preference_sanity or srs_frequency_topic_coverage or preview_returns_profile_bootstrap_payload_without_mutating_store or preview_executes_real_profile_bootstrap_with_seed_topic_columns or test_plan_srs_set_surfaces_profile_bootstrap_diagnostics" -q`
- `python3 scripts/testing/srs_admission_preference_sanity.py`
- `python3 scripts/testing/srs_frequency_topic_coverage.py --db <synthetic_db> --frontier-limit 2`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. confirm the admission-core modules still describe an additive layer instead of a silent helper/runtime rewrite
2. rerun both the admission-core tests/scripts and the semantic baseline suite
3. refresh the selective-port Phase 1 note so later D-phase slices inherit an explicit, dated admission-core checkpoint

## Outcome

Result:

- admission-core normalization, candidate-trait extraction, signal-pack scoring, and synthetic sanity/coverage scripts remain executable
- planner/helper behavior still keeps `profile_bootstrap` as diagnostics plus reranking context while executable bootstrap falls back to `frequency_bootstrap`
- no helper semantic publication files needed to move for D2
- the semantic Phase 0 suite still reran green alongside this slice, which keeps the additive-core claim honest
- `profile_bootstrap.py` still warrants later structural health work, but that remains separate from the D2 contract
