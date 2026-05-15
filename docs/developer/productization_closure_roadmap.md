# Productization Closure Roadmap

Status: active roadmap
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 doc-reference check, state check, diff hygiene, profile backup smoke, unreferenced-script routing review, regenerated project-structure inventory, generated-output unnecessary audit, review-only generated-output resolution, experiment-payload retention audit, generated-only experiment-family routing review, rulegen experiment-family relocation, root-dated rulegen evidence relocation, root-dated semantic repair duplicate removal, stabilization backlog scope-boundary sync, and source-bundle promotion pinning policy
Purpose: sequence the work needed to turn the current large proof-of-concept system into a safer, more testable product before further corpus or semantic-veto expansion
Source-of-truth: roadmap only; current truth still lives in source code, tests, generated evidence, `feature_state_matrix.md`, and seam-specific canonical docs.
Related docs:
- `productization_lane1_doc_disposition_inventory.md`
- `productization_lane2_code_disposition_inventory.md`
- `productization_lane2_semantic_testing_script_registry.md`
- `productization_lane3_feature_state_truth_inventory.md`
- `productization_lane4_validation_gate_inventory.md`
- `productization_lane5_runtime_seam_inventory.md`
- `productization_lane6_data_provenance_inventory.md`
- `project_health_remediation_workstream.md`
- `project_integrity_stabilization_runbook.md`
- `project_integrity_stabilization_backlog.md`
- `documentation_governance.md`
- `feature_state_matrix.md`
- `../test_outputs/dev_workflow/project_structure_latest.md`
- `../test_outputs/dev_workflow/experiment_payload_retention_latest.md`
- `../../scripts/dev/project_structure_inventory.py`
- `../../scripts/dev/experiment_payload_retention_audit.py`
- `../srs/README.md`
- `../gui/README.md`
- `../language_pairs/README.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md`
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

Current Lane 6 progress:

- `docs/developer/productization_lane6_data_provenance_inventory.md` now
  records L6-A through L6-Zc: current pack/source provenance inventory, pack
  provenance sidecar contract, pack lifecycle audit command, semantic pack
  provenance and lineage, en-es candidate readiness runbook, app-managed
  non-semantic installer provenance, manual resource settings disposition
  audit, constrained manual import/backfill contract, safe manual-settings
  backfill, semantic source-lineage publication, existing-install provenance
  sidecar backfill, external/manual import preflight, provenance review
  posture, strict pack lifecycle review gate, promotion evidence bundle, and
  app-managed build/parser lineage, raw artifact checksum capture, and converter
  source digests, catalog source-identity classification, safe source-version
  writer/backfill, dated Kaikki source-dump gating, source-bundle lineage for
  generated DE frequency output, embedding/manual checksum lineage, frequency
  SQLite artifact metrics, source-bundle checksum coverage reporting, and
  generated DE pipeline component checksum capture, executable provenance
  promotion policy, and source-bundle promotion pinning policy.
- L6-A maps the pack catalog, pack source manifest, installed-pack manifests,
  pack refs/resolvers, semantic pack-copy manifest, profile publication
  manifest, generated evidence artifacts, and current en-es corpus-expansion
  audit boundary.
- L6-B adds `core/lexishift_core/helper/pack_provenance.py`, an executable
  `provenance.json` validator for source identity, explicit license status,
  source pointers, raw artifact checksums, build mode, generated artifact
  identity, and optional corpus metrics.
- L6-C adds `scripts/testing/pack_lifecycle_audit.py`, a read-only JSON and
  Markdown audit for installed manifests, optional provenance sidecars, semantic
  pack copies, profile publication manifests, catalog pack ids, and optional
  candidate SQLite metadata.
- L6-D makes copied semantic packs write a validated `provenance.json` sidecar
  and a manifest `lineage` block that records the source inventory path/hash,
  source inventory generation fields when present, normalized inventory hash,
  and semantic inventory counts.
- L6-E adds
  `docs/rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md`, a
  copy-pasteable sequence for pack lifecycle audit, source-readiness audit, SRS
  Zipf bridge, denominator audit, and canonical doc updates before any expanded
  Spanish corpus promotion.
- L6-F makes app-managed translation, frequency, and embedding installs write
  conservative `provenance.json` sidecars with source URL, Wayback URL when
  present, source filename, build mode, SQLite filename when present, generated
  artifact identity, and `requires_review` license status.
- L6-G makes the lifecycle audit report saved manual/external resource
  settings, including language, frequency, embedding, embedding-pair, and legacy
  secondary-resource paths. Missing manual paths and app-managed artifacts still
  stored in manual maps are `review` findings; managed artifacts in manual maps
  receive disposition `migrate_to_managed_pack_id`.
- L6-H records the UX/lifecycle decision: external resource selection is a
  constrained license/import fallback for exact supported artifact shapes, not a
  broad file-picker product path. The lifecycle audit now reports expected
  manual artifact formats and flags unsupported existing manual files, while
  the embedding picker rejects unsupported file types and no longer exposes an
  all-files filter.
- L6-Ia adds a dry-run/apply settings backfill for the safe case where saved
  manual paths already point at manifest-backed app-managed SQLite pack roots.
- L6-Ja propagates semantic source lineage into profile publication manifests
  and teaches the lifecycle audit to report publication source-lineage
  presence.
- L6-Ka adds a dry-run/apply provenance sidecar backfill for catalog-backed
  app-managed installs that predate sidecar-writing installers.
- L6-La adds a read-only external/manual import preflight command that validates
  exact supported artifact shape, previews provenance, and keeps manual linking
  separate from managed import/promotion readiness.
- L6-Ma makes the lifecycle audit distinguish schema-valid sidecars from
  release/promotion readiness by reporting license status, source pointer type,
  raw checksum coverage, generated artifact checksum presence, and review
  reasons.
- L6-Na adds `--fail-on-review` as the strict pack lifecycle gate for
  promotion/release checks while preserving non-strict local audit behavior.
- L6-Oa adds `scripts/testing/pack_lifecycle_promotion_evidence.py`, an
  executable promotion bundle gate that verifies lifecycle, source-readiness,
  SRS Zipf bridge, and denominator artifacts together for frequency-pack
  candidate promotion.
- L6-Pa makes app-managed sidecars and existing-install sidecar backfill record
  build command and parser config when already known, and teaches the lifecycle
  audit to report source/build lineage presence.
- L6-Qa makes new app-managed translation downloads and frequency conversions
  hash available raw/downloaded or parsed source artifacts before cleanup and
  write SHA-1/SHA-256 into sidecar `source.raw_artifacts`.
- L6-Ra makes app-managed install/finalization paths and safe existing-install
  sidecar backfill record `build.converter_version` as
  `source_sha256:<module-or-script>:<digest>` when no package-level converter
  version exists.
- L6-Sa adds `scripts/testing/pack_lifecycle_source_identity_plan.py`, a
  read-only source-version/source-dump decision surface. Current catalog
  classification is `8` safe-to-write candidates, `2` label-only cases, `16`
  policy-needed cases, and `1` source-bundle case.
- L6-Ta adds `core/lexishift_core/helper/pack_source_identity.py` as the shared
  classifier and wires app-managed sidecar writing plus existing-install
  backfill to write durable source identity only for `safe_to_write` rows.
  Current mutation is source-version-only for FreeDict, Japanese WordNet,
  English WordNet, and BCCWJ-style release/version evidence; label-only,
  policy-needed, and source-bundle rows remain withheld from
  source-version/source-dump writes.
- L6-Ua makes the Kaikki source-dump policy explicit: `enwiktionary` alone is a
  dump-family label and remains withheld, while dated dump markers normalize to
  `enwiktionary:YYYY-MM-DD` and can pass through the same safe writer.
- L6-Va adds optional `source.source_bundle` provenance and wires the generated
  German frequency pipeline sidecar/backfill path to record component URL
  lineage for the Leipzig corpus, FreeDict/OdeNet/OpenThesaurus whitelist
  resources, german-pos-dict POS resources, and Morfologik tooling.
- L6-Wa captures app-managed embedding raw-vector checksums when the conversion
  source is still available during finalization, and makes the read-only
  external import preflight compute file checksums automatically when the
  operator did not provide them.
- L6-Xa writes narrow generated-artifact metrics for readable frequency SQLite
  sidecars: row count, distinct non-empty lemmas, rows with POS, and rows with
  topic/domain metadata.
- L6-Ya validates optional component checksums on source-bundle components and
  makes lifecycle lineage report source-bundle component checksum coverage
  separately from bundle presence/component count.
- L6-Za makes new app-managed generated DE frequency builds expose local
  component paths before cleanup, compute SHA-1/SHA-256 for matching available
  source-bundle components, and write the checked bundle into the provenance
  sidecar.
- L6-Zb extracts the promotion-oriented provenance checks into
  `scripts/testing/pack_lifecycle_policy.py`, writes `provenance_policy` verdicts
  into lifecycle audit rows, and makes the promotion evidence gate require a
  present, ready policy verdict.
- L6-Zc makes source-bundle promotion stricter: URL-recorded but unpinned
  source bundles now remain review findings until the sidecar declares a
  promotion-grade pinned lineage status.
- The main finding is explicit: managed pack roots and publication manifests
  exist, but installed manifests are not complete source/license/generation
  provenance records, existing/manual/legacy paths can still lack sidecar-backed
  provenance, and executable policy gating can block unresolved review items
  without approving sources; the promotion bundle can prove required artifacts
  and policy verdicts are present and passing without creating missing
  policy-gated source-dump, license-approval, package/release-version,
  non-installer checksum, or complete source-bundle component checksum/pinning
  lineage.
- The next Lane 6 slices should add actual source-bundle pinning/source-policy
  evidence and full schema/metric policy where the current sidecars still carry
  only partial evidence. Current Kaikki rows also still need an actual dated
  dump acquisition/pinning decision before they can gain sidecar `source_dump`,
  and generated-pipeline bundles still need complete component checksum coverage
  for reused/missing inputs, license-review, and pinning decisions before
  promotion-grade evidence.
  Source-version mutation is now limited to the `safe_to_write` classification
  rows and must not expand to `label_only`/`needs_policy` rows without source
  policy.
- A full manual import UX remains deliberately deferred until a concrete
  license-restricted source scenario proves which narrow import/link path is
  actually needed.

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

### Cross-Lane: Project Structure Review

Goal:
- keep the whole repository layout visible enough that redundant docs, stale
  generated artifacts, tentative scripts, and ambiguous ownership boundaries can
  be reviewed before new expansion work adds more surface area.

Current progress:

- `scripts/dev/project_structure_inventory.py` now provides a read-only path
  enumeration and structure-review candidate report.
- `npm --prefix scripts run inventory:structure` writes latest JSON and
  Markdown artifacts under `docs/test_outputs/dev_workflow/`.
- `scripts/dev/generated_output_unnecessary_audit.py` now provides the stricter
  deletion-readiness mechanism. `npm --prefix scripts run inventory:unnecessary`
  writes latest JSON and Markdown artifacts under `docs/test_outputs/dev_workflow/`
  and separates `definite_prune`, `review_only`, and `retain` groups.
- `scripts/dev/experiment_payload_retention_audit.py` now provides a read-only
  family-level retention review for `docs/test_outputs/experiments`.
  `npm --prefix scripts run inventory:experiments` writes latest JSON and
  Markdown artifacts under `docs/test_outputs/dev_workflow/`.
- The latest snapshot enumerates `4,018` non-ignored paths: `3,822` files and
  `196` directories, with `2,355` candidate-signal paths and `0`
  unreferenced-script candidates.
- The dominant structure signal is generated-evidence accumulation:
  `docs/test_outputs` accounts for `2,393` paths, including `683` files under
  `docs/test_outputs/experiments`.
- Generated-output retention review now has first-class inventory buckets for
  baselines, dev-workflow operational reports, experiment payloads, SRS journey
  evidence, audit evidence, older phase/sample evidence, root latest aliases,
  and root dated snapshots. These buckets do not hide any paths; they make the
  next prune/archive pass class-based instead of size-based.
- First manual generated-output cleanup removed the unreferenced
  `rulegen_benchmark_expanded_smoke` root-output triplet. It had no
  non-output references and was superseded by later benchmark evidence, so it
  was deleted rather than archived.
- Semantic source-packaging review stayed local and removed only copied install
  roots for `en-es-active-only-combined-full-v1-tranche-001` through
  `en-es-active-only-combined-full-v1-tranche-010`. The top-level normalized
  evidence and semantic inventory files remain source evidence, tranche `011`
  remains the active install-root fixture referenced by the runbook, and
  product-scope/helper/native-host smoke roots remain retained while current
  docs or tests route through them.
- Root dated generated-output review removed unreferenced semantic-veto LLM
  pilot repair admission and generation-run reports from 2026-05-05. The raw
  response bundles and experiment-batch generated-row payloads remain retained
  because the current `latest` merge artifacts still carry those provenance
  references.
- The same root dated review removed four unreferenced derived report views:
  all-pairs benchmark HTML/Markdown, reverse-far-hit benchmark HTML, and
  all-pairs triage Markdown. Referenced JSON evidence and referenced summary
  Markdown remain retained.
- The first generated-output unnecessary audit found `0` `definite_prune`
  groups, `4` `review_only` groups, and `16` retained groups. The review-only
  findings are unreferenced root-dated JSON/provenance outputs, so they are not
  safe for automatic deletion without a surviving summary or downstream artifact
  decision.
- The review-only findings were resolved manually. The broad March 2026
  `en-es` expansion-candidates probe was deleted because the selected rev-on
  and rev-off probe artifacts plus the archived aggressive-expansion summary
  preserve the surviving evidence. The one-off `hora` probe was deleted because
  it had no current routing or canonical downstream summary. The stale
  reverse-far-hit quality-gate JSON was deleted because current and archived
  reverse-check evidence routes through benchmark, triage, probe, and current
  gate artifacts instead. The root semantic-veto LLM repair `002` generated-row
  copy was deleted because the current merge uses repairs `001` and `003`;
  raw-response and experiment-batch artifacts remain retained for provenance.
  The regenerated unnecessary-output audit now reports `0` `definite_prune`
  groups, `0` `review_only` groups, and `1` retained group.
- The first experiment-payload retention audit classified `11` experiment
  families covering `670` files and `122,313,459` bytes. It found no
  unreferenced experiment family.
- Generated-only family review resolved
  `docs/test_outputs/experiments/semantic_veto_evidence_gap_augmented_datasets`
  as retained intermediate provenance for the semantic-veto evidence-gap
  score-contribution reports. The producer now exposes the exact
  repo-relative output family as a code constant, and the regenerated retention
  audit reports all `11` experiment families as routed: `0` generated-linked,
  `0` experiment-linked, `0` self-linked-review, and `0` unrouted-review
  families.
- Root-level rulegen experiment review moved the 97 March 28 broad-sweep files
  from loose `docs/test_outputs/experiments/rulegen_en_es_*` paths into
  `docs/test_outputs/experiments/rulegen_en_es_broad_sweep_20260328/`. The
  runbook and internal summary/triage references were mechanically updated, so
  the artifacts are retained but no longer appear as root-level experiment
  clutter.
- Root-dated rulegen evidence review moved the 13 referenced March 2026 rulegen
  artifacts out of the `docs/test_outputs` root and into two named evidence
  families:
  `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/` and
  `docs/test_outputs/experiments/rulegen_pair_stability_snapshot_20260321/`.
  The reverse-check matrix script, archived analysis docs, feature-state
  references, and generated evidence references were updated.
- Root-dated semantic repair review removed the two remaining root-level repair
  generated-row payload copies:
  `semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_001.json` and
  `semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_003.json`.
  Both were byte-identical to already-retained files in
  `docs/test_outputs/experiments/semantic_veto_llm_pilot_batches/`; the latest
  generated-row assembly JSON/Markdown now points at the retained experiment
  payloads. The regenerated structure report has no root-dated snapshot bucket,
  and the experiment retention audit reports `13` routed families covering
  `683` files with `0` unrouted-review families.
- The first unreferenced-script heuristic initially reported three candidates:
  `scripts/dev/srs_selector_demo.py`, `scripts/dev/test_embeddings.py`, and
  `scripts/testing/semantic_shadow_review_queue_en_es.py`. Review found no
  deletion candidates: the two dev scripts are manual probe/demo utilities now
  routed in `scripts/README.md`, and the semantic-shadow review queue is an
  active generated-evidence producer now routed through `feature_state_matrix.md`
  and the script registry.
- Duplicate filename/stem rows are candidate signals only. They mostly identify
  generated evidence families and repeated runtime naming patterns, not
  immediate cleanup approval.
- First cleanup action: the unreferenced legacy root diagram
  `diagrams/lexishift_flow.mmd` moved to
  `docs/archive/diagrams/lexishift_flow_legacy.mmd`. Current maintained diagram
  sources remain under `docs/architecture/diagrams/`, with rendered assets under
  `docs/assets/diagrams/`.
- Ignored-but-real review started with the inventory's ignored file sample. The
  hand-written GUI test `apps/gui/tests/test_main_ruleset_ui.py` is now allowed
  through `.gitignore` and tracked. The local vocabulary export, generated CWS
  preflight report, and PyInstaller build output remain ignored local artifacts.
- Odd tracked artifact review started with `scripts/default.profraw` and
  `scripts/backup_profiles_suisui_takeya.sh`. The zero-byte LLVM profiling
  artifact was removed and `*.profraw` is now ignored. The personal profile
  backup helper was replaced with reusable `scripts/backup_profiles.sh`, while
  `scripts/restore_profiles_backup.sh` now documents the generic backup naming
  shape.

Structural cleanup checkpoint:

- The generated-output cleanup loop is good enough to pause when the current
  reports show `0` `definite_prune` groups, `0` `review_only` groups, no
  root-dated snapshot bucket, all experiment families routed, and `0`
  unreferenced-script candidates.
- Further cleanup should continue only when it has a clearly named product-risk
  target, such as a misleading doc, a stale feature-state claim, an untested
  runtime seam, or a redundant latest-alias family with a proven canonical
  replacement.
- Do not keep shuffling generated evidence only because the inventory still has
  large counts; root-level latest aliases and duplicate-stem rows are expected
  to remain broad signals until a stronger retention policy is chosen.

Current resume rule:

1. Do not restart broad structural cleanup by default; the current generated
   evidence, experiment-retention, and unreferenced-script reports are already
   good enough to pause.
2. Prefer Lane 6 data-source download lifecycle follow-through as the next
   high-value productization slice: source-bundle source-policy evidence,
   source-version/dump policy, license/review policy, exact import
   preflight/backfill, and promotion evidence where the current sidecars still
   carry partial evidence.
3. If SRS work resumes instead, treat planner execution breadth as the open
   follow-on. Due-aware runtime serving is already verified when helper SRS due
   metadata is present; a dedicated due-only publication artifact remains
   shelved.
4. Reopen structural cleanup only for a named product-risk reason, then prove
   exact references, generated-artifact ownership, and historical value before
   archiving or deleting anything.

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
