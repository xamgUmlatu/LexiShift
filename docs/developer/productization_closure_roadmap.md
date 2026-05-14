# Productization Closure Roadmap

Status: active roadmap
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 doc-reference check, state check, and diff hygiene after Lane 2 code-disposition inventory, semantic family evidence expansion, semantic-veto, semantic-LLM, semantic-shadow, and source-admission sub-registries
Purpose: sequence the work needed to turn the current large proof-of-concept system into a safer, more testable product before further corpus or semantic-veto expansion
Source-of-truth: roadmap only; current truth still lives in source code, tests, generated evidence, `feature_state_matrix.md`, and seam-specific canonical docs.
Related docs:
- `productization_lane1_doc_disposition_inventory.md`
- `productization_lane2_code_disposition_inventory.md`
- `productization_lane2_semantic_testing_script_registry.md`
- `productization_lane3_feature_state_truth_inventory.md`
- `productization_lane4_validation_gate_inventory.md`
- `productization_lane5_runtime_seam_inventory.md`
- `project_health_remediation_workstream.md`
- `project_integrity_stabilization_runbook.md`
- `project_integrity_stabilization_backlog.md`
- `documentation_governance.md`
- `feature_state_matrix.md`
- `../srs/README.md`
- `../gui/README.md`
- `../language_pairs/README.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`

## Purpose

LexiShift has enough working pieces to behave like a product, but the current
state is still closer to a large integrated proof of concept than a fully
closed product contract.

The next phase should focus on productization closure before expansion:

1. remove or demote stale documentation,
2. remove, quarantine, or clearly label old and tentative code paths,
3. reconcile implemented/default-on/verified status,
4. consolidate the verification commands future agents should trust,
5. close the highest-risk runtime and data lifecycle gaps.

The goal is not theoretical perfection. The goal is a development surface where
major product claims are traceable, repeatable, and not contradicted by stale
docs, one-off scripts, generated snapshots, or dormant code.

## Expansion Posture

Corpus and semantic-veto expansion should be paused-but-prepared while this
closure work runs.

Allowed during closure:

1. no-spend source audits,
2. documentation of candidate source requirements,
3. local-only experiments that do not change defaults,
4. evidence collection that clarifies current state.

Not allowed until closure reaches a cleaner checkpoint:

1. promoting a new frequency or corpus pack as default,
2. launching another paid semantic-veto generation wave,
3. broadening product claims from current 2k installed-resource evidence,
4. using generated artifacts as authority without a current source/code/test
   pointer,
5. changing acceptance thresholds or baselines to make expansion appear ready.

The existing expansion plan remains useful, but it should stay behind this
closure gate. Use `../rulegen/semantic_veto_srs_corpus_expansion_plan.md` for
source-readiness work and `../rulegen/semantic_veto_denominator_current_state.md`
for the current active-only denominator posture.

## Closure Standard

A product surface is closure-ready only when these states are separated:

| State | Required Evidence |
| --- | --- |
| Implemented | Source code exists on the intended path and is wired into the expected caller. |
| Default-on | Runtime defaults, manifests, settings, or install paths cause real users to hit it. |
| Verified | Repeatable tests, harnesses, smokes, or generated evidence cover the product claim. |
| Documented | Canonical docs describe current behavior, not just intent. |
| Safe to expand | Remaining risks are named and do not block expansion or user safety. |

If a surface fails one of these checks, keep it explicit in
`feature_state_matrix.md`, a lane-specific packet, or the owning canonical doc.

## Roadmap Lanes

### Lane 1: Redundant And Stale Documentation

Goal:
- make current truth easy to find by reducing old, duplicate, or misleading
  documentation.

Primary checks:

1. identify docs making present-tense product claims,
2. classify each as canonical current, planning/WIP, generated evidence, or
   archive,
3. migrate surviving value before retiring a stale doc,
4. remove generated-output references that are being treated as architecture
   authority,
5. update routing docs only after the replacement path is clear.

Outputs:

- doc disposition table,
- updated routing links,
- archive or demotion notes,
- `python3 scripts/dev/check_doc_references.py` passing.

Current Lane 1 progress:

- maintained-doc metadata normalization is complete except for ignored generated
  evidence snapshots and intentionally non-standard project-integrity packets,
- `docs/developer/project_integrity_packet_index.md` groups the 51 packet docs
  without moving them,
- `docs/rulegen/semantic_rulegen_authority_map.md` now routes semantic-veto,
  semantic-routing, reverse-check, and rulegen claim types,
- dated March 2026 reverse-check `en-es` review snapshots moved to
  `docs/archive/rulegen/` after surviving policy/status value was routed into
  active rulegen references,
- `docs/srs/README.md`, `docs/gui/README.md`, and
  `docs/language_pairs/README.md` now provide supersession routing for their
  domains,
- no SRS, GUI, or language-pair docs were archived during the supersession
  reviews.

Remaining Lane 1 decision:

- either select a packet archive destination and move packet groups behind the
  packet index, or leave the packets indexed in place and move to Lane 2.

### Lane 2: Redundant, Dead, Or Tentative Code

Goal:
- reduce implementation ambiguity before more product behavior is layered on
  top.

Primary checks:

1. find unused scripts, one-off probes, duplicate adapters, and dormant runtime
   paths,
2. prove whether they are imported, tested, documented, or still part of a
   current workflow,
3. delete code only when the runtime and historical value are both understood,
4. quarantine retained experiments with clear names and docs,
5. add or preserve tests when a cleanup changes a real contract.

Disposition labels:

| Label | Meaning |
| --- | --- |
| Keep | Current code path with evidence or active ownership. |
| Extract | Valuable code hidden inside an overloaded module. |
| Quarantine | Experimental or one-off code worth preserving but not product authority. |
| Archive | Historical artifact with migrated surviving value. |
| Delete | No current caller, no current evidence value, and no needed historical role. |

Current Lane 2 progress:

- `docs/developer/productization_lane2_code_disposition_inventory.md` now
  records the first code/script disposition scan.
- A fresh project-health report showed `3` advisory violations and `7`
  near-limit warnings before the first code split; after the Lane 2 hotlist
  splits the report shows `0` advisory violations and `0` near-limit warnings.
- No code has been deleted. The first refactor preserved the original
  sentence-veto support import facade while moving implementation into focused
  support modules, and the prompt-runner refactor preserved the existing CLI and
  import surface while moving common, journal, intake, and no-spend
  safety/replay helpers into focused modules. Follow-up splits cleared the
  remaining semantic-script and extension semantic-context near-limit warnings.
- `docs/developer/productization_lane2_semantic_testing_script_registry.md`
  now provides the v0 family registry and marks
  the project-health hotlist files as former violations or former warnings.
- The first Lane 2 evidence-expansion pass classified additional semantic
  script families by docs, tests, script importers, and generated-artifact
  ownership signals. It found no safe delete candidates and moved the next work
  to family sub-registries for `semantic_veto_*`, `semantic_llm_*`, and
  `semantic_shadow_*`.
- The first semantic-veto sub-registry split the 131 `semantic_veto_*` scripts
  into current no-spend expansion support, active-only operator tooling,
  paid/live generation runners, product-quality research, sampling/review/repair
  research, and comparator/diagnostic lanes. It found no safe delete candidate;
  the next Lane 2 sub-registries are `semantic_llm_*` and `semantic_shadow_*`.
- The first semantic-LLM sub-registry split the 31 `semantic_llm_*` scripts into
  prompt runner/safety, prototype admission, example-frame generation, and
  reviewed/source-insertion support. It found no safe delete candidate and
  preserved the live-spend boundary as the main cleanup constraint.
- The first semantic-shadow sub-registry split the 23 `semantic_shadow_*`
  scripts into inventory/policy/review, gold/veto/seed proxy,
  sweep/candidate-source, and experiment matrix/compare lanes. It found no safe
  delete candidate and recorded the direct script-level test gap for future
  refactors.
- The source/admission sub-registry classified 33 lower-density source,
  adapter, fixture, phrase-control, and source-class probe scripts. It found no
  safe delete candidate and closed the first semantic-script classification
  layer; deeper Lane 2 work should now start from a specific
  generated-artifact ownership decision.

### Lane 3: Feature-State Truth Pass

Goal:
- make status claims reliable across the whole product.

Primary checks:

1. compare docs, code, tests, and generated evidence for each major system,
2. keep `implemented`, `default-on`, and `verified` separate,
3. record known contradictions until they are actually resolved,
4. avoid marking planned or analysis-only behavior as shipped,
5. update `feature_state_matrix.md` only when state or evidence changes.

Priority surfaces:

- semantic veto runtime and pack lifecycle,
- SRS admission, refresh, reset, and publication,
- rulegen LP support and onboarding,
- helper/native messaging routes,
- browser replacement runtime behavior,
- packaging and platform parity.

Current Lane 3 progress:

- `docs/developer/productization_lane3_feature_state_truth_inventory.md`
  now records the first feature-state claim ledger.
- The first slice, L3-A, reconciles semantic runtime and semantic pack
  lifecycle claims across code, tests, canonical docs, and the current feature
  matrix.
- The main correction is now explicit: semantic admission is default-on only
  when the current SRS publication is capable, named pack install remains
  operator-only, and runtime decision policy exists even though rendered
  soft-affordance UX is still planned/partial.
- L3-B now records the SRS admission/publication truth pass. No feature-state
  status change was needed: frequency bootstrap, active inventory, explicit
  refresh publication, and reset are current seams; profile bootstrap,
  broad profile growth, due-only serving, automatic adaptive refresh, and
  runtime confidence gating remain non-default or planned as previously
  documented.
- L3-C now records the helper/native-host route truth pass. No feature-state
  status change was needed: configured native-messaging routes, diagnostics,
  semantic inventory/admission, SRS workflow routes, profile routes, and
  explicit semantic pack install are implemented/verified seams; same-browser
  host-path sharing, extension-installed proof, and release-certification
  limits remain known gaps.
- L3-D now records the rulegen LP support/onboarding truth pass. No
  feature-state status change was needed: runtime rulegen modes exist for
  `en-ja`, `de-en`, `en-de`, `en-es`, and `es-en`, but only `en-es` and
  `en-de` currently have machine-readable LP profiles and dedicated latest
  benchmark lanes. Case files, runtime support, profile conformance, and
  promotion readiness should remain separate status claims.
- L3-E now records the browser replacement runtime truth pass and corrects a
  stale scan-order claim: full scans already prioritize visible and
  near-viewport nodes, while page budgets add deterministic within-band
  distribution. It also keeps due-serving, runtime confidence filtering,
  debug semantic overrides, non-rendered `soft_affordance`, and debug-gated
  runtime diagnostics as separate status claims.
- L3-F now records the packaging/platform parity truth pass. No feature-state
  status change was needed: `check` remains the default repo-safety gate,
  `build`/`build:report` remain build contracts, hosted Ubuntu
  `build:ci:report` remains a partial non-GUI lane, and Windows parity remains
  a required evidence gate rather than full release certification.

### Lane 4: Verification Gate Consolidation

Goal:
- make the trusted development loop obvious and repeatable.

Primary checks:

1. reconcile documented commands with `scripts/package.json`,
2. keep local hooks aligned with repo-safety commands,
3. identify which gates are required for docs-only, SRS, rulegen, semantic
   runtime, packaging, and platform-parity changes,
4. remove stale command recipes,
5. keep generated artifacts tied to their producing command.

Expected command families:

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed`
- `npm --prefix scripts run check`
- SRS quality harness when SRS surfaces change
- rulegen benchmark/quality/triage loop when rulegen scoring, filtering, POS,
  or LP tuning changes
- semantic publication/runtime tests when semantic helper/runtime paths change

Current Lane 4 progress:

- `docs/developer/productization_lane4_validation_gate_inventory.md` now maps
  change types to the smallest honest validation bundle, while preserving
  `scripts/package.json` as the command authority.
- The first Lane 4 slice separates branch-scope, local/staged, report-producing,
  SRS, rulegen, semantic runtime, helper/native-host, packaging/platform parity,
  GitHub Pages, CWS, and release/product-ops gates.
- It also records artifact freshness rules so `*_latest` outputs stay evidence
  snapshots from the run that produced them, not architecture authority.
- The second Lane 4 slice routes `local_setup.md`, `ai_workflow.md`, and
  `scripts/README.md` back to the validation-gate inventory and corrects their
  build-lane wording so Windows full `build:report` coverage is not flattened
  into the unsupported-host `build:ci:report` partial lane.
- The third Lane 4 slice records handoff artifact freshness policy: refresh
  generated workflow artifacts only when their producing command is part of the
  honest validation bundle, render summaries from matching source JSON, and call
  historical artifacts historical instead of refreshing heavyweight outputs for
  timestamp freshness.

### Lane 5: High-Risk Runtime Seams

Goal:
- close the paths most likely to create user-visible breakage.

Primary checks:

1. browser DOM scanning and visible-first replacement ordering,
2. helper/native-host request and response contracts,
3. semantic-veto admission, publication, fallback, and diagnostics,
4. SRS admission, due serving, refresh/reset, and feedback paths,
5. resource install/update and default data-root behavior,
6. runtime failure diagnostics and recovery.

Each runtime closure pass needs a before-edit truth table and a validation
bundle. Do not mix unrelated runtime surfaces in the same pass.

Current Lane 5 progress:

- `docs/developer/productization_lane5_runtime_seam_inventory.md` now records
  L5-A, the due-aware SRS runtime serving closure slice.
- L5-A keeps helper publication broad over the active/admitted inventory, but
  helper-published SRS rules now carry `metadata.rulegen.srs` due-state
  metadata and the extension SRS gate filters future-due helper rules at
  runtime.
- The SRS quality harness now verifies the runtime due-active count is bounded
  by the due count in the feedback scenario, while keeping the absence of a
  dedicated due-only publication artifact explicit.
- L5-B changes semantic admission's unavailable-scoring default from
  `legacy_on_unavailable` to `abstain_on_unavailable`, aligning extension
  runtime/profile/diagnostic defaults with the helper-side safety default while
  preserving `legacy_on_unavailable` as an explicit compatibility policy.
- L5-C keeps semantic scoring behavior unchanged but carries fallback
  `reason_codes` into aggregate scan/runtime diagnostics as
  `semantic_fallback_reason_counts`, so non-ready metadata, inventory failures,
  and helper decision-service failures are distinguishable from the options
  diagnostics surface.
- L5-D contains thrown helper semantic decision-service exceptions inside the
  semantic gate, converting them to the existing fail-closed fallback reason
  code instead of rejecting the page scan.
- L5-E contains thrown semantic inventory-resolution exceptions inside the
  semantic gate, converting them to the existing fail-closed
  `semantic_inventory_unavailable` path instead of rejecting the page scan.
- The Lane 5 remaining-seam triage now marks no known browser-extension
  runtime fail-open blocker remaining for the SRS/semantic admission path; the
  next broad expansion blocker shifts to Lane 6 data provenance and pack
  lifecycle work.

### Lane 6: Data Provenance And Pack Lifecycle

Goal:
- make local resources, generated SQLite, manifests, source files, licenses, and
  install locations auditable.

Primary checks:

1. source file provenance and license status,
2. generated SQLite schema and metadata,
3. manifest-backed pack identity,
4. installed-vs-manual resource paths,
5. default data-root behavior,
6. generated artifact freshness and producing command.

This lane is the bridge back to corpus expansion. It should close source and
pack uncertainty before any larger Spanish corpus is promoted.

### Lane 7: Product Ops And Release Readiness

Goal:
- ensure the product can be installed, updated, diagnosed, and recovered without
  depending on developer memory.

Primary checks:

1. build/package workflow,
2. native messaging install and helper startup,
3. macOS and Windows parity where relevant,
4. local diagnostics and logs,
5. failure-mode runbooks,
6. release/update rollback behavior.

## Per-Slice Review Template

Use this template before editing in any lane:

| Field | Required Answer |
| --- | --- |
| Lane | Which roadmap lane is active? |
| Slice | What exact surface is being reviewed? |
| Product claim | What user or developer promise is under review? |
| Current implementation | Which files actually implement it? |
| Default path | How does a real runtime reach it, if at all? |
| Verification | Which tests, harnesses, smokes, or artifacts prove it? |
| Redundancy/staleness risk | Which docs or code paths may be obsolete or duplicated? |
| Closure action | Keep, fix, test, demote, archive, quarantine, delete, or defer. |
| Validation bundle | The smallest command set that honestly covers the slice. |

## Recommended Initial Sequence

Start with the lanes that reduce future confusion before touching behavior:

1. Lane 1: redundant and stale documentation,
2. Lane 2: redundant, dead, or tentative code inventory,
3. Lane 3: feature-state truth pass,
4. Lane 4: verification gate consolidation,
5. Lane 5: highest-risk runtime seams,
6. Lane 6: data provenance and pack lifecycle,
7. Lane 7: product ops and release readiness.

The first concrete pass should produce an inventory, not a broad deletion PR:

1. list canonical docs and stale candidates,
2. list old/tentative scripts and code paths,
3. classify each item with a disposition label,
4. pick only one or two low-risk cleanup actions,
5. leave the rest as explicit follow-up slices.

## Resume Criteria For Expansion

Resume corpus and semantic-veto expansion only after:

1. current docs route cleanly to canonical sources,
2. obsolete docs/code are either removed, archived, or clearly labeled,
3. feature-state contradictions are explicit and not hidden in chat,
4. verification gates are documented and passing for the touched area,
5. the current 2k installed-resource denominator remains preserved as a
   baseline,
6. source provenance and pack lifecycle expectations are clear enough to audit a
   candidate 5k-10k Spanish corpus.

At that point, expansion should restart through the existing corpus-expansion
audit, SRS Zipf bridge, denominator audit, and semantic-veto generation decision
sequence.
