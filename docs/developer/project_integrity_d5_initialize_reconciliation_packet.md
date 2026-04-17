# D5 Initialize Reconciliation Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted initialize tests, synthetic SRS harness rerun, semantic Phase 0 baseline rerun, and one local `en-es` initialize smoke
Purpose: bound the D5 slice around initialize-time inventory mutation plus publication-family preservation so later refresh/reset/runtime reconciliation work can build on an explicit initialize contract
Source-of-truth: packet only; executable truth still lives in helper code, tests, local validation runs, and the current semantic publication contract
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D5`
- Title: initialize-set reconciliation
- Pass type: verification-first checkpoint with initialize/publication boundary pinning

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/engine.py`
- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/rulegen_outputs.py`

Primary tests/evidence surface:

- `core/tests/helper/test_helper_engine.py`
- `core/tests/srs/test_srs_lp_e2e.py`
- `scripts/testing/srs_quality_harness.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- refresh-set mutation semantics
- reset cleanup semantics
- runtime diagnostics join behavior
- extension/UI workflow wiring
- due-aware serving as a product claim
- helper-rule runtime confidence gating

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- initialize is the first mutation flow that now couples explicit inventory persistence to immediate rulegen/publication
- if this seam drifts, the system can still look superficially healthy while inventory membership and publication artifacts diverge
- the highest-risk failure mode is overclaiming initialize as "done" while quietly dropping the semantic publication-family guarantees

## Contract Sketch

The intended current initialize contract is:

1. initialize remains an executable mutation flow, not just a planning or preview surface
2. initialize resolves pair resources, sizing defaults, and profile context through the current helper engine contract
3. store mutation happens first, then active membership is derived from `initial_active_preview`
4. active inventory persistence is explicit:
   - `replace_pair=True` rebaselines the pair-local active ids
   - non-replace initialization merges newly initialized active ids with the already resolved active inventory
   - `last_initialized_at` is stamped when the inventory is saved
5. follow-up rule generation runs against those explicit `active_item_ids`
6. helper publication still uses the current-branch semantic publication family:
   - ruleset
   - snapshot
   - optional semantic inventory
   - publication manifest
7. initialize still forwards `semantic_inventory=getattr(rulegen_output, "semantic_inventory", None)` into `write_rulegen_outputs(...)`
8. current synthetic harness coverage for this publication family remains strongest on `en-ja` and `en-de`; this packet adds a local `en-es` initialize smoke but does not claim new harness coverage there

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Initialize persists explicit pair-local inventory and stamps initialize-time metadata. | `helper/use_cases/initialize_set.py` | targeted `core/tests/helper/test_helper_engine.py` initialize coverage | `verified for this slice` |
| Replace-vs-merge inventory behavior remains explicit and pair-scoped. | `initialize_set.py`, inventory helpers | targeted `core/tests/helper/test_helper_engine.py` initialize coverage | `verified for this slice` |
| Follow-up rulegen runs against active inventory and still forwards optional semantic inventory into publication. | `initialize_set.py`, `helper/rulegen.py`, `helper/rulegen_outputs.py` | targeted initialize helper test | `verified for this slice` |
| Real initialize publication still produces ruleset/snapshot/semantic inventory/manifest under local LP execution. | initialize flow plus helper publication | `core/tests/srs/test_srs_lp_e2e.py`, local `en-es` initialize smoke | `verified for this slice` |
| Broader SRS publication/runtime quality remains green except for the known due-aware warning. | synthetic SRS harness | `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json` | `verified for this slice` |
| Semantic publication/runtime protections remain intact while initialize is audited. | D1 Phase 0 protected suite | semantic baseline rerun during D5 validation | `verified for this slice` |

## Invariants

1. keep initialize publication on the current semantic artifact family
2. do not treat initialize success as proof that refresh/reset/runtime reconciliation is complete
3. keep explicit inventory membership and publication-family generation alignment coupled during initialize
4. keep due-aware serving caveats explicit rather than laundering them through initialize evidence
5. keep pair-coverage limits explicit where harness support is still narrower than the overall LP set

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Plain initialize append | pair items grow and active inventory persists |
| Replace-pair initialize | old pair items are removed and pair-local active inventory is reset |
| Pair-policy default initialize | helper still resolves current pair sizing/rulegen defaults |
| Publication-family initialize | rulegen runs against active inventory and publishes semantic family artifacts |
| Local LP smoke | real initialize publication works on supported LPs and one local `en-es` smoke |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/helper/test_helper_engine.py::TestHelperEngineInitializeSrsSet core/tests/srs/test_srs_lp_e2e.py::TestSrsLpE2E::test_en_ja_e2e_initialize_and_refresh_publish_outputs core/tests/srs/test_srs_lp_e2e.py::TestSrsLpE2E::test_en_de_e2e_initialize_and_refresh_publish_outputs -q`
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- local `en-es` initialize smoke in a temp workspace using synthetic `freq-es-cde.sqlite`, explicit forward `spa-eng.tei`, and default reverse `eng-spa.tei`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify that initialize still writes explicit active inventory before publication
2. confirm initialize publication still routes through the current semantic artifact family
3. make pair-coverage limits explicit instead of implying that the harness already covers every SRS-selectable LP

## Outcome

Result:

- initialize still persists explicit active inventory and stamps `last_initialized_at`
- initialize still runs follow-up rulegen against the derived active inventory and routes publication through the current ruleset + snapshot + semantic inventory + manifest family
- helper initialize tests reran green (`6 passed` including `en-ja` and `en-de` LP e2e initialize/refresh publication coverage)
- the synthetic SRS quality harness reran with `pass=15 warn=1 fail=0`; the remaining warning is the already-known due-aware publication caveat, not an initialize regression
- a local tempdir `en-es` initialize smoke also succeeded with `applied=True`, `targets=40`, `rules=40`, and emitted semantic inventory plus publication manifest paths
- the semantic Phase 0 baseline suite reran green (`27 passed`), so the initialize checkpoint still sits on top of the protected semantic base
