# Project Integrity Stabilization Backlog

Status: active backlog
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 scope-boundary sync against `feature_state_matrix.md`, `productization_closure_roadmap.md`, `srs_admission_merge_seam_map.md`, due-aware SRS evidence, and confidence-gating evidence
Purpose: break the stabilization program into small seam-scoped passes that improve trustworthiness without broad mixed cleanup
Source-of-truth: planning doc only; current truth still lives in code, tests, `feature_state_matrix.md`, and seam-specific evidence artifacts
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane2_code_disposition_inventory.md`
- `project_integrity_stabilization_runbook.md`
- `documentation_governance.md`
- `feature_state_matrix.md`
- `project_health_gate_structure.md`
- `project_health_remediation_workstream.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `../rulegen/semantic_routing_implementation_roadmap.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_data_contract.md`
- `../srs/srs_profile_schema.md`

## Purpose

The stabilization runbook is intentionally strict, but the active seams are too large to treat as single tasks.

This backlog translates that runbook into a queue of bite-sized passes with:

1. one concrete seam,
2. one claim set,
3. one validation bundle,
4. one clean checkpoint.

Use this as the planning surface for sequencing work.
Do not treat it as evidence that any listed slice is already verified.

## Operating Rules

Every pass should aim to stay within:

1. one functional seam,
2. one to three docs,
3. one to three code modules,
4. one focused validation bundle,
5. one intentional checkpoint commit.

Do not mix:

- doc routing cleanup,
- contract changes,
- structural refactors,
- benchmark/policy tuning,
- and unrelated state-ledger updates

into the same pass unless they are inseparable at that seam.

Execution rule:

- every backlog item must follow the per-slice checklist in `project_integrity_stabilization_runbook.md`
- do not start a slice until the bounded re-onboarding packet, pre-edit truth table, and validation bundle are explicit

## Current Working Snapshot (2026-05-16)

Verified for the current backlog refresh:

- branch: `codex/veto-data-sources-exp`
- recent checkpoint commits on this branch:
  - `96329b34` (`Remove duplicate semantic repair root payloads`)
  - `755ae9ca` (`Group dated rulegen evidence artifacts`)
  - `83eafdfd` (`Group rulegen broad sweep experiment artifacts`)
  - `6124a757` (`Route evidence gap augmented datasets`)
- worktree: clean at the start of this scope-boundary sync; this is a usable restart point for the next bounded slice
- canonical doc-reference gate: passing
- `git diff --check`: clean on the current working tree before this doc update

Current structural pressure from the latest advisory project-health report:

- advisory violations: none
- near-limit watchlist: none

Recent branch-state implications:

1. The earlier "clean-tree baseline" snapshot is now historical only; use the latest checkpoint commit plus the current dirty-worktree reality when planning the next pass.
2. Structural-health pressure that shifted into semantic testing/support
   scripts and extension semantic-context runtime code has been cleared for the
   current hotlist. There are no current advisory violations or near-limit
   warnings.
3. Generated evidence files are normal ongoing work on this branch, but the
   current structure cleanup loop is now pause-worthy: generated-output
   unnecessary audit reports `0` definite-prune groups and `0` review-only
   groups, experiment retention reports all experiment families routed, and the
   project-structure inventory reports `0` unreferenced-script candidates.
4. Do not reopen broad structural cleanup by default. Continue only for a
   concrete product risk, stale state claim, runtime seam, or proven duplicate
   with a surviving canonical artifact.

Scope boundary after the latest evidence sync:

Resolved or narrowed:

1. SRS profile fixed-allowlist and unknown-key behavior is no longer an open
   contradiction; `project_integrity_sp2_profile_schema_packet.md` and
   `srs_admission_merge_seam_map.md` verify the fixed `v1` allowlist.
2. Nested `constraints` / `sizing` fields are descriptive mirrors, while helper
   request sizing remains top-level-authoritative; this is now documented as
   current behavior, not an unknown.
3. Due-aware SRS serving is verified at the runtime gate when helper SRS due
   metadata is present. The remaining limitation is narrower: there is still no
   dedicated due-only helper publication artifact.
4. Extension-side confidence gating is verified as not implemented for live
   helper-published rule activation. Keep it planned/shelved until a real
   settings surface, runtime code path, and tests are intentionally added.

Still open:

1. Planner docs describe multiple strategies, but executable default behavior
   remains dominated by frequency bootstrap. `profile_bootstrap` and
   `profile_growth` are implemented in limited non-default lanes.
2. `core/lexishift_core/srs/profile_bootstrap.py` remains a structural hotspot,
   but it should be split only when SRS admission work resumes.
3. Data-source download lifecycle follow-through remains the clearest
   cleanup-adjacent product-ops follow-on.

## Validation Bundles

Use the smallest bundle that honestly covers the seam.

### V0: baseline hygiene

```bash
python3 scripts/dev/check_doc_references.py
git diff --check
```

### V1: changed-scope repo safety

```bash
npm --prefix scripts run check:changed
```

### V2: semantic publication/runtime seam

```bash
python3 -m pytest \
  core/tests/rulegen/test_semantic_publication.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py \
  core/tests/helper/test_rulegen_outputs.py \
  core/tests/architecture/test_extension_structure.py \
  core/tests/dev/test_helper_translation_dict_entrypoints.py \
  -q
```

### V3: SRS seam

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json
```

Add targeted SRS/unit tests for the touched modules.

### V4: rulegen scoring/filtering/POS seam

```bash
python3 scripts/testing/rulegen_benchmark.py \
  --pairs en-es \
  --json-output docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --markdown-output docs/test_outputs/rulegen_benchmark_en_es_latest.md \
  --html-output docs/test_outputs/rulegen_benchmark_en_es_latest.html

python3 scripts/testing/rulegen_quality_gate.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --policy-json docs/test_inputs/rulegen_quality_policy.json \
  --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json \
  --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json \
  --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json

python3 scripts/testing/rulegen_benchmark_triage.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --json-out docs/test_outputs/rulegen_benchmark_triage_latest.json \
  --markdown-out docs/test_outputs/rulegen_benchmark_triage_latest.md
```

Add targeted tests for the touched rulegen modules.

## Backlog

## Wave A: Baseline, Routing, And Truth Surfaces

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| A1 | Baseline checkpoint refresh | Reconfirm protected base files, clean-tree assumptions, and current checkpoint notes before broader stabilization continues. | V0 | none |
| A2 | Developer routing audit | Make sure `docs/developer/README.md`, `docs/architecture/README.md`, and linked routing docs still point to the right current vs planning surfaces. | V0 | A1 |
| A3 | Project-health workstream refresh | Reconcile `project_health_remediation_workstream.md` with the actual current advisory report so the live snapshot is no longer stale. | V0, V1 | A1 |
| A4 | State-ledger contradiction review | Recheck `feature_state_matrix.md` mismatch items and expand them only where code/doc disagreement is already known. | V0, V1 | A1 |

## Wave B: Semantic Routing Contract Reconciliation

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| B1 | Semantic publication contract audit | Reconcile current helper outputs, `generation_id`, manifest behavior, and reset semantics with the docs. | V0, V2 | A2 |
| B2 | Semantic runtime contract audit | Reconcile extension/runtime docs with current default-off behavior, fallback policy, eligible-match gating, and `semantic_admit_batch` usage. | V0, V2 | A2 |
| B3 | Semantic data-contract audit | Make the docs precise about current pointer strength by LP, current sidecar contents, and what is still planning-only. | V0, V2 | B1 |
| B4 | Semantic diagnostics join-point audit | Verify diagnostics fields across helper/runtime/cache layers and narrow docs where current fields are still transitional. | V0, V2 | B1, B2 |
| B5 | `en-es` publication PoC boundary cleanup | Make it explicit everywhere that emitted-sibling `ready` pointers are a narrow PoC, not full shadow-mined runtime readiness. | V0, V2 | B1, B3 |
| B6 | Semantic roadmap pruning pass | Reduce overlap among semantic routing planning docs so current contract, near-term implementation ladder, and research lanes are easier to distinguish. | V0 | B1, B2, B3 |

## Wave C: SRS Profile / Admission Contract Reconciliation

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| C1 | SRS profile schema truth pass | Narrow `docs/srs/srs_profile_schema.md` to the fixed `v1` signal allowlist and the current top-level sizing authority. | V0, V1 | A4 |
| C2 | Extension SRS settings contract audit | Verify `signals_methods.js`, `srs_profile_methods.js`, and planning docs agree on what the options UI really persists and edits today. | V0, V1 | C1 |
| C3 | Planner-strategy truth pass | Align planner docs and state ledger with the fact that frequency bootstrap still dominates executable behavior. | V0, V1, V3 | C1 |
| C4 | Due-aware serving audit | Decide whether current end-to-end behavior is actually due-aware; either verify it with evidence or keep the item explicitly planned. | V0, V1, V3 | C3 |
| C5 | Confidence-gating audit | Verify whether any live extension-side helper-rule confidence filter exists; if not, narrow the docs and leave it planned. | V0, V1 | A4 |

## Wave D: SRS Admission Selective-Port Execution

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| D1 | Phase-0 semantic baseline freeze refresh | Reconfirm the protected semantic files and baseline tests before more admission work lands. | V0, V2 | B1, B2 |
| D2 | Admission core audit | Re-verify `admission_features.py`, `profile_bootstrap.py`, and related tests/scripts as additive admission core, separate from helper publication. | V0, V1, targeted tests | C3 |
| D3 | Explicit active inventory persistence | Verify/add the pair-local inventory seam (`inventory.py`, helper paths, serialization) without disturbing semantic publication. | V0, V1, targeted tests | D1 |
| D4 | Admission preview/rebalance helper API | Verify helper engine and CLI preview/rebalance surfaces without regressing semantic helper APIs. | V0, V1, targeted tests | D3 |
| D5 | Initialize-set reconciliation | Reconcile `initialize_set.py` with explicit active inventory plus the current semantic publication family. | V0, V1, V3 | D4 |
| D6 | Refresh/reset reconciliation | Reconcile `refresh_set.py` and `reset.py` with inventory-aware mutation while preserving semantic publication and manifest cleanup behavior. | V0, V1, V3 | D5 |
| D7 | Runtime diagnostics join point | Make diagnostics report both semantic publication state and active inventory state consistently. | V0, V1, V3 | D6 |
| D8 | Extension/UI admission wiring audit | Verify the SRS options/controller surfaces that edit admission preferences and call preview/rebalance flows. | V0, V1, targeted UI/controller tests | D4 |

## Wave E: Data-Source Normalization Follow-Through

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| E1 | Translation-pack holdout audit | Identify benchmark/tooling paths that still assume TEI or legacy flat paths where managed SQLite-first resolution should now be canonical. | V0, V1, targeted tests | A4 |
| E2 | Frequency-pack holdout audit | Verify frequency pack id/path resolution, runtime diagnostics, and remaining legacy fallback assumptions. | V0, V1, targeted tests | E1 |
| E3 | Embedding-pack settings/runtime split audit | Verify managed-id vs manual-path separation in settings/runtime and narrow docs where temporary path maps still exist internally. | V0, V1, targeted tests | E1 |
| E4 | Installed-vs-manual UI contract cleanup | Ensure the settings docs and UI language still describe managed resources as the default and manual paths as compatibility surfaces. | V0, V1 | E1, E2, E3 |

## Wave F: Structural Health Remediation

These passes should remain behavior-preserving unless the slice explicitly targets behavior.
Any pass that touches rulegen scoring, filtering, POS, or publication logic must use V4.

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| F1 | `en_es.py` seam map | Identify natural internal seams in `core/lexishift_core/rulegen/pairs/en_es.py` before moving code. | V0 | B3 |
| F2 | `en_es.py` extraction 1 | Extract non-scoring helpers such as provenance/record shaping or inventory assembly into a support module. | V0, V1, V4 | F1 |
| F3 | `en_es.py` extraction 2 | Extract candidate filtering / ranking helpers into a clear local seam while preserving outputs. | V0, V1, V4 | F2 |
| F4 | `en_es.py` extraction 3 | Reduce the top-level pair module to orchestration plus exported pair contract. | V0, V1, V4 | F3 |
| F5 | `generation.py` split | Separate orchestration from reusable generation helpers so rulegen flow is easier to reason about and test. | V0, V1, V4 | F4 |
| F6 | `en_de.py` split | Apply the same seam-first split discipline to `core/lexishift_core/rulegen/pairs/en_de.py`. | V0, V1, V4 | F5 |
| F7 | `rulegen_probe_words.py` split | Reduce the oversized script into orchestration plus support modules without changing CLI behavior. | V0, V1, targeted tests | F5 |
| F8 | Semantic shadow inventory split | Split `semantic_shadow_inventory.py` along mining vs shaping/reporting seams. | V0, V1, targeted tests | B6 |
| F9 | Semantic shadow evaluation split | Split `semantic_shadow_evaluation.py` along scoring vs report/summary seams. | V0, V1, targeted tests | F8 |
| F10 | `profile_bootstrap.py` split | Separate profile normalization/scoring from reporting/diagnostics helpers before more admission work accumulates there. | V0, V1, V3 | C3 |
| F11 | `dict_loaders.py` split | Split dictionary-format loaders from shared normalization/resolution helpers. | V0, V1, targeted tests | E1 |
| F12 | `helper/engine.py` import-pressure pass | Extract low-cohesion helper API groupings only if the split matches real use-case seams. | V0, V1, targeted tests | D7 |
| F13 | `helper/rulegen.py` import-pressure pass | Separate publication/runtime glue from helper orchestration where it reduces join-point risk. | V0, V1, targeted tests | B4, D7 |
| F14 | SRS options `workflows.js` preventive split | Split the near-limit SRS workflows controller before it becomes another hotspot. | V0, V1, targeted controller tests | D8 |
| F15 | GUI dialogs preventive split | Extract distinct dialog/theme or helper flows from `apps/gui/src/dialogs.py` only where the seam is already real. | V0, V1, targeted tests | E4 |
| F16 | Settings language-packs preventive split | Continue reducing `apps/gui/src/settings_language_packs.py` if new normalization work increases pressure again. | V0, V1, targeted tests | E4 |

Reference for `F1` through `F4`:

- `rulegen_en_es_seam_map.md`

## Wave G: Evidence And Workflow Integrity

| ID | Slice | Goal | Validation | Dependencies |
|---|---|---|---|---|
| G1 | State-ledger evidence refresh discipline | Ensure each stabilization pass updates `feature_state_matrix.md` only when status or evidence actually changes. | V0, V1 | A4 |
| G2 | Canonical evidence-path hygiene | Remove or narrow any doc references that cite generated artifacts as architecture truth instead of evidence. | V0 | A2, B6 |
| G3 | Project-health baseline decision | After enough hotspot work lands, decide whether the project-health workstream can move back toward zero-warning operating discipline. | V0, V1 | F1-F16 |

## Recommended Initial Sequence

If the goal is to reduce confusion before reducing code size, the original
sequence was:

1. A2 `Developer routing audit`
2. A3 `Project-health workstream refresh`
3. A4 `State-ledger contradiction review`
4. B1 `Semantic publication contract audit`
5. B2 `Semantic runtime contract audit`
6. C1 `SRS profile schema truth pass`
7. C3 `Planner-strategy truth pass`
8. C4 `Due-aware serving audit`
9. C5 `Confidence-gating audit`
10. D1 `Phase-0 semantic baseline freeze refresh`

Current 2026-05-16 resume rule:

- Do not restart this full sequence by default.
- Treat C1, C4, and C5 as answered enough for scope control: C1 is fixed
  allowlist/top-level sizing authority, C4 is runtime due-aware serving when
  helper metadata is present, and C5 is planned/not implemented for live
  helper-rule activation.
- If SRS admission work resumes, start from C3/D2 rather than redoing C1/C4/C5.
- If no SRS admission work is active, prefer the data-source download lifecycle
  follow-through or a specifically named product-risk seam.

If the goal is to start structural cleanup as soon as the contracts are explicit, begin the refactor queue after `B3` and `C3`, starting with `F1` through `F5`.

## Post-Closure Follow-On Queue (2026-04-21)

The core stabilization and secondary-pass closure work is now complete on the current branch.

What remains is not "unfinished cleanup" in the same sense.
It is a smaller follow-on queue that should be handled selectively rather than reopening the whole program by default.

Recommended posture:

1. keep only one bounded low-hanging follow-on active at a time
2. explicitly shelve deeper or product-shaping items until they are chosen on purpose
3. do not restart the full structural queue unless a later branch change makes it necessary again

### Worth Doing Soon

| Priority | Follow-on | Why it is still worth doing | Current recommendation |
|---|---|---|---|
| `1` | data-source download lifecycle follow-through | This is the main operability improvement left in the cleanup-adjacent queue: remote-overridable download URLs, explicit failure classification, and a lightweight source-audit workflow. | treat as the only clear low-hanging follow-on if one more bounded cleanup slice is wanted |
| `2` | SRS planner execution follow-through | The remaining SRS ambiguity is planner execution breadth, not due-aware runtime serving. Frequency bootstrap still dominates default execution while profile strategies stay limited/non-default. | shelve unless admission work resumes intentionally |
| `3` | project-health baseline decision | This determines whether the repo should return toward zero-warning structural discipline after the recent hotspot reductions. | shelve until more day-to-day work lands or until we are ready to change enforcement expectations |

### Explicitly Shelved For Now

These are valid future programs, but they should not be mistaken for remaining stabilization debt:

- extension confidence gating for helper-published rules
- dedicated due-only helper publication artifact
- narrower Share Center export/import schemas beyond the current compatibility wording
- broader preventive structural splits (`F12` through `F16`) unless new work in those files makes the split timely
- any restart of broad semantic/rulegen cleanup without a new concrete seam or regression signal

### Default Resume Order

If follow-on work resumes later, prefer this order:

1. data-source download lifecycle
2. SRS planner execution follow-through
3. project-health baseline decision

Everything below that should stay shelved until selected as a deliberate next program.

## Definition Of Done For This Backlog

This backlog has served its purpose when:

1. the highest-risk seams have fresh contract docs and fresh evidence,
2. explicit contradictions are either resolved or still clearly logged,
3. the largest hotspot files have been reduced along real seams,
4. another contributor can resume the stabilization program from one checkpoint note instead of rediscovering the system.
