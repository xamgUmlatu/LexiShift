# Semantic Veto Reconciliation Workstream

Status: active workstream
Role: Planning / WIP
Purpose: keep the semantic sentence-veto runtime, research harnesses, data artifacts, and promotion claims aligned while the work spans many turns
Last updated: 2026-05-01
Last verified: 2026-05-01 against `semantic_sentence_veto_algorithm.md`, `semantic_source_admission_program.md`, `semantic_decision_rule_comparison_plan.md`, `semantic_decision_research_lanes_en_es.json`, `semantic_veto_assumption_ledger.md`, `semantic_veto_archive_consolidation.md`, `semantic_veto_artifact_authority_audit.md`, `semantic_veto_local_output_disposition.md`, and `semantic_veto_system_registry_en_es.json`
Source-of-truth: this workstream governs reconciliation process; runtime truth still lives in code, tests, manifests, and generated evidence

## Why This Exists

The semantic veto work now has enough runtime code, research harnesses,
generated evidence, and planning docs that the main risk is coordination drift.
The failure mode to prevent is one artifact making a claim that another artifact
silently invalidates.

This workstream turns cleanup into explicit passes. Each pass has a lens, a
bounded question, an artifact to update, and a stopping rule. The goal is not to
delete research history. The goal is to make current runtime behavior, current
candidate research, diagnostic tools, and historical evidence clearly distinct.

## Non-Negotiable Rules

- Runtime behavior and research candidates must remain separate.
- Generated evidence is evidence, not architecture authority.
- A candidate is not promotable because one latest artifact looks good.
- A mechanism is not failed globally when only one tested form failed.
- Use explicit states, not vague completion language.
- Every pass must preserve unresolved cracks as named follow-up rows.
- No runtime policy change comes from reconciliation alone.

## Durable Artifacts

- Process doc: `docs/rulegen/semantic_veto_reconciliation_workstream.md`
- Assumption ledger: `docs/rulegen/semantic_veto_assumption_ledger.md`
- Archive ledger: `docs/rulegen/semantic_veto_archive_consolidation.md`
- Artifact authority audit:
  `docs/rulegen/semantic_veto_artifact_authority_audit.md`
- Local output disposition:
  `docs/rulegen/semantic_veto_local_output_disposition.md`
- Wave7 breadth runbook:
  `docs/rulegen/semantic_veto_wave7_source_class_breadth_runbook.md`
- Machine registry: `docs/test_inputs/semantic_veto_system_registry_en_es.json`
- Registry renderer/auditor: `scripts/testing/semantic_veto_system_registry_summary.py`
- Latest rendered summary: `docs/test_outputs/semantic_veto_system_registry_latest.md`

## Runtime Path Map

This is the current production browser/helper YES/NO path. It is a runtime
classification map, not a policy change.

```text
apps/chrome-extension/manifest.json
  -> loads background.js plus content runtime modules in dependency order
  -> grants nativeMessaging for helper calls
apps/chrome-extension/content_script.js
  -> wires helper client, helper rules runtime, active-rules runtime, semantic
     gate runtime, DOM scan runtime, settings pipeline, and runtime actions
settings and active-rule readiness
  -> apps/chrome-extension/content/runtime/apply_settings_pipeline.js
     runs active-rule resolution, writes srsSemanticAdmissionEnabled and
     srsSemanticAdmissionFallbackPolicy into current settings, and invokes the
     runtime apply loop
  -> apps/chrome-extension/content/runtime/rules/active_rules_runtime.js
     resolves active SRS-origin rules, ready semantic pointers, and helper or
     helper-cache semantic inventory availability
  -> apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js
     fetches helper rules and helper/cache semantic inventory for readiness
per-text match admission
  -> apps/chrome-extension/content/processing/replacements.js
     finds lexical matches and calls the semantic gate before DOM rendering
  -> apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js
     groups ready semantic matches, applies fallback decisions for unavailable
     rows, calls helper semantic_admit_batch for ready rows, applies debug
     override only when enabled, and retains only effective replace decisions
  -> apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js
     bridges browser runtime calls to helper inventory/admission APIs
  -> apps/chrome-extension/shared/helper/helper_cache.js
     persists and reloads helper-cache semantic inventory for pair/profile
  -> apps/chrome-extension/shared/helper/helper_client.js
     sends native messages for get_semantic_inventory and semantic_admit_batch
  -> apps/chrome-extension/shared/helper/helper_transport_extension.js
     sends content-script requests to the background bridge
  -> apps/chrome-extension/background.js
     forwards helper requests to the native host
  -> scripts/helper/lexishift_native_host.py
     dispatches semantic_admit_batch to the Python helper engine
  -> core/lexishift_core/helper/engine.py
     exposes the helper semantic_admit_batch API
  -> core/lexishift_core/helper/use_cases/semantic_admission.py
     loads the profile semantic inventory and delegates batch decisioning
  -> core/lexishift_core/rulegen/semantic_routing_runtime_policy.py
     resolves the named production policy, prepares matches, applies fallback
     records, fits the scorer batch, and emits decision records
  -> core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py
     builds context/evidence views, computes active and shadow scores, applies
     phrase preemption, and returns replace or abstain
  -> apps/chrome-extension/content/processing/replacements.js
     renders retained replacement spans; abstained semantic matches stay as
     source text
```

Non-runtime neighbors remain explicit: `runtime_diagnostics.py` and extension
diagnostic reporters surface health and evidence only; source-admission and
research harnesses can produce candidate evidence, but they do not alter this
path unless a runtime policy change is made separately.

## Research Harness Map

This map is for choosing the right harness. It does not rank candidates.

Decision-rule and representation harnesses:

- `scripts/testing/semantic_decision_rule_matrix_en_es.py`: compares context
  representation, evidence scope, scorer, aggregation, final YES/NO rule,
  phrase handling, and negative controls from explicit manifests.
- `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`: probes
  prototype evidence plus phrase containment, phrase prototype, and surface-POS
  guard variants on a queue or all-family slice.
- `scripts/testing/semantic_llm_prototype_ablation_matrix_en_es.py`: separates
  source-mode, scorer, context-view, threshold, and guard-shape effects for
  prototype lanes.
- `scripts/testing/semantic_source_margin_policy_sweep_en_es.py`: sweeps
  scalar active/shadow and phrase-prototype margins over fixed evidence and
  held-out suites.
- `scripts/testing/semantic_surface_pos_rescue_policy_sweep_en_es.py`: replays
  fixed score traces to test deterministic surface-POS rescue gates; it does
  not rescore evidence and is not runtime policy.
- `scripts/testing/semantic_surface_pos_rescue_policy_validation_en_es.py`:
  recomputes held-out scorer rows from the evidence batch, then applies the
  recommended rescue gates to confirm the replay candidate offline; it is still
  not runtime policy.

Source-admission and evidence harnesses:

- `scripts/testing/semantic_source_admission_cycle_en_es.py`: runs leakage,
  duplicate, merge, final sense-admission, source-contract, and optional
  ablation checks for a candidate evidence batch.
- `scripts/testing/semantic_source_heldout_validation_en_es.py`: validates one
  configured evidence batch and decision shape against a locked active/shadow
  or phrase/no-winner held-out suite.
- `scripts/testing/semantic_source_row_alignment_audit_en_es.py`: checks
  whether admitted source rows are trigger-adjacent and selector-ready enough
  for context-conditioned or additive source experiments.
- `scripts/testing/semantic_source_frame_gap_plan_en_es.py`: converts row
  alignment gaps into explicit source-frame generation slots; it is planning,
  not accepted evidence.
- `scripts/testing/semantic_phrase_policy_signal_audit_en_es.py`: checks
  phrase-control signal firing without source evidence or semantic scoring.
- `scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py`: builds and
  admission-sweeps automatic non-v10 candidate waves. Pair it with inventory
  candidate, wave-builder, source-support conversion, Wiktextract support,
  held-out validation, and failure-mining artifacts before any breadth claim.
- `scripts/testing/semantic_translation_sense_evidence_batch_en_es.py`: builds
  normalized evidence from source-backed translation-sense text.
- `scripts/testing/semantic_wordnet_alternate_sense_phrase_evidence_en_es.py`:
  builds alternate-sense phrase/no-winner containment rows from WordNet.
- `scripts/testing/semantic_authorization_frame_evidence_en_es.py`: builds
  deterministic authorization-frame rows for source-backed permission-like
  senses.
- `scripts/testing/semantic_source_class_frame_evidence_en_es.py`: builds
  deterministic non-authorization semantic-class frame rows from source-backed
  gloss and translation-sense text.

Diagnostics and ledgers:

- `docs/rulegen/semantic_veto_assumption_ledger.md`: records the current
  candidate's tested, untested, and rejected assumptions, with evidence links
  or required follow-up tests; it is a reconciliation ledger, not a runtime
  policy change.
- `docs/rulegen/semantic_veto_archive_consolidation.md`: records older
  semantic-veto artifacts that remain useful as history, controls, or
  superseded failure baselines; it prevents old `latest` reports from steering
  current candidate decisions.
- `docs/rulegen/semantic_veto_breadth_expansion_gate.md`: defines the next
  `wave7_source_class_breadth_v1` breadth test, including exclusions, class
  buckets, acceptance artifacts, and stop rules; it is definition-only until the
  wave7 artifacts exist.
- `docs/rulegen/semantic_veto_wave7_source_class_breadth_runbook.md`: maps the
  wave7 breadth gate to concrete commands, output paths, stop rules, and setup
  blockers; it is a setup artifact, not executed breadth evidence.
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json` plus
  `scripts/testing/semantic_decision_research_lanes_summary.py`: tracks research
  lane state without collapsing everything into a generic done/completed state.
- `scripts/testing/semantic_source_failure_class_mining_en_es.py`: reads
  admission, held-out, source, and margin artifacts to expose reusable failure
  classes, breadth gaps, and overfit risk.
- `scripts/testing/semantic_wave7_residual_blocker_probe_en_es.py`: reads the
  wave7 phrase-control triage heldout reports plus rescue and margin sweeps to
  classify the remaining blockers before any scalar policy tuning.
- `scripts/testing/semantic_veto_system_registry_summary.py`: audits this
  reconciliation registry; it is not a semantic decision harness.

## Data Artifact Map

This map is for rerunning or interpreting the current lane without borrowing a
stale artifact by accident. It does not make the lane promotion-ready.

Current lane:

- `wave6_auth_frame_raw_sentence_surface_pos_rescue`

Durable inputs:

- `wave6_wiktextract_dataset`: selected source-backed wave6 dataset. This is a
  current input even though its path is under `docs/test_outputs/experiments`.
- `wave6_active_shadow_heldout`: locked 38-row active/shadow heldout suite.
- `wave6_phrase_heldout`: locked 16-row phrase/no-winner heldout suite.

Generated reports for the current lane:

- `auth_frame_admission_report`: source admission, leakage, merge, contract, and
  sense-admission report for the auth-frame candidate batch.
- `auth_frame_active_shadow_validation`: raw-sentence active/shadow validation,
  currently `0` harmful and `0` false abstains over `38` cases.
- `auth_frame_phrase_validation`: raw-sentence phrase/no-winner validation before
  rescue replay, preserving the unrescued phrase harm signal.
- `auth_frame_rescue_replay_report`: fixed-trace rescue replay over active/shadow
  plus phrase/no-winner suites; replay only, not runtime policy.
- `auth_frame_rescue_policy_validation`: scorer-backed offline confirmation of
  the recommended rescue gates, currently `0` harmful and `0` false abstains
  over `54` combined active/shadow plus phrase/no-winner cases.
- `auth_frame_failure_mining`: generated failure-class and breadth-risk ledger.

Control/comparator:

- `wave6_alt_phrase_raw_sentence_control`: raw-sentence surface-POS lane before
  authorization-frame rows. Use this as the control for auth-frame deltas.

Rerun order:

1. translation-sense evidence adapter
2. alternate-sense phrase adapter
3. authorization-frame adapter
4. auth-frame source-admission cycle
5. active/shadow heldout validation
6. phrase/no-winner heldout validation
7. rescue replay over fixed traces
8. scorer-backed rescue policy validation
9. failure-class mining

Cracks preserved by this pass:

- Several generator scripts and latest reports are local experiment artifacts in
  this worktree. Commit or regenerate them before treating this lane as
  fresh-checkout runnable.
- The base dataset is a current candidate input under `test_outputs/experiments`,
  so the registry must keep its role explicit.
- The rescue policy now has scorer-backed offline confirmation, but it is still
  not a runtime policy change or breadth proof.

Wave7 breadth gate:

- `wave7_source_class_breadth_v1` has been executed, but it did not pass.
- Selected wave: 16 fully source-supported families after Wiktextract overlay:
  `like`, `gross`, `cast`, `fix`, `full`, `waste`, `firm`, `even`, `wrong`,
  `meet`, `stretch`, `score`, `crash`, `trim`, `squeeze`, `foul`.
- Source-class breadth: `23` split non-authorization source-detectable
  classes and `90` deterministic class-frame rows across `29` senses.
- Heldout floor: `48` locked cases exist: `32` active/shadow cases and `16`
  phrase/no-winner cases.
- Admission result: `16 / 16` semantic contract, but status `review` due `12`
  leakage rejects, `29` sense rejects, and an empty phrase contract.
- Heldout result: active/shadow validation has `1` harmful replacement and `3`
  false abstains; phrase/no-winner validation has `7` harmful replacements.
- Rescue validation result: `8` harmful replacements and `3` false abstains
  across the combined `48` cases.
- Failure mining result: promotion readiness `blocked`; blocking classes are
  `heldout_harmful_replace` and `additional_heldout_1_harmful_replace`.

Wave7 phrase-control triage:

- Added WordNet alternate-sense phrase/no-winner evidence for the same 16
  families: `179` phrase-control rows across `248` candidate senses.
- Phrase-control admission now reaches `16 / 16` semantic contract and
  `16 / 16` phrase contract with `326` final admitted rows, but remains
  `review` due leakage review and downstream heldout blockers.
- Active/shadow heldout remains blocked: `1` harmful replacement and `2` false
  abstains across `32` cases. The source-class split fixed the previous
  `like` and `full` false abstains; the targeted phrase-preemption guard fixed
  the previous `even` false abstain.
- Phrase/no-winner heldout remains blocked under the current surface-POS shape:
  `6` harmful replacements across `16` cases, even though phrase-control scores
  are now present.
- Rescue sweep over the phrase-control triage traces found `0` passing policies
  across `25` replayed rescue policies.
- No-surface margin sweep found `0` passing combined policies when run with the
  no-surface prototype decision shape: phrase-only rows can pass at several
  margins, but active/shadow false abstains increase enough to block the lane.
- Current blocker split: residual active/source failures are `gross` harmful
  quantity-vs-disgust selection plus `fix` and `meet` false abstains;
  phrase/no-winner still has `6` harmful replacements, and neither rescue nor
  no-surface scalar margin policies produce a combined pass.
- Residual blocker probe:
  `docs/test_outputs/semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`
  classifies the remaining `9` residuals into `5` failure classes and preserves
  the next remediation as targeted shadow/overlap evidence plus phrase/no-winner
  rescue-guard work, not global scalar tuning.

## Action Ledger

Action items live in `docs/test_inputs/semantic_veto_system_registry_en_es.json`
and render into `docs/test_outputs/semantic_veto_system_registry_latest.md`.
Each row has a priority, status, owning pass, source artifacts, evidence needed,
validation, and promotion impact.

Current highest-priority actions:

- `P0` `materialize_current_wave6_lane`: make the current wave6 lane
  fresh-checkout runnable, or demote local-only latest reports to provisional
  evidence.
- `P1` `wave7_source_class_breadth_setup`: done; the wave7 runbook and tracked
  59-trigger exclusion manifest are available.
- `P1` `wave7_source_class_breadth_execution`: done; the gate was executed and
  failed with harmful replacements plus false abstains recorded in failure
  mining.
- `P1` `wave7_blocking_failure_triage`: done; phrase-control evidence restored
  the phrase contract, but heldout blockers remained and are now split into
  active source-signal misses and phrase rescue-policy interaction.
- `P1` `artifact_authority_stale_latest_audit_continuation`: done; the audit
  now records that registered `latest` primary paths are generated, historical,
  or superseded, and that dirty local generated outputs remain
  non-authoritative until disposition.
- `P1` `semantic_methodology_doc_dirty_state_reconcile`: done; methodology docs
  and the decision research ledger now carry the wave6 source/guard finding as
  research-only current-reference material, with the cited generated evidence
  committed and no runtime-policy promotion.
- `P1` `local_semantic_latest_output_disposition`: done; referenced wave2-wave5
  draft inputs are preserved as historical/seed support, remaining semantic
  generated-output churn is classified as local-only, and generic repo-health
  outputs are out of semantic-veto scope.
- `P1` `wave7_active_signal_and_rescue_split`: done; source-class evidence was
  split from broad buckets into source-specific classes, fixing `like` and
  `full` false abstains while preserving the remaining wave7 blockers.
- `P1` `wave7_residual_guard_and_shadow_evidence`: done; the residual blocker
  probe split `gross`, `fix`, `even`, `meet`, and the 6 phrase/no-winner harms
  into separate remediation lanes before any scalar rescue or margin tuning.
- `P1` `wave7_targeted_guard_and_evidence_patch`: done; added a research-only
  strong-active phrase-preemption guard plus targeted `gross`/`fix`
  source-class templates, regenerated the wave7 phrase-control chain, and fixed
  the `even` false abstain while leaving `gross`, `fix`, `meet`, and the 6
  phrase/no-winner harms blocked.
- `P1` `wave7_shadow_overlap_and_phrase_rescue_followup`: queued; repair the
  remaining measured blocker classes without treating the lane as a global
  threshold problem.
- `P1` `scorer_backed_rescue_policy_confirmation`: done; the recommended rescue
  policy passes scorer-backed offline validation over the current 54-row suite.
- `P1` `source_trigger_overfit_audit`: done; authorization-frame evidence is
  audited for source-triggered class behavior, browser-case leakage, and
  target-lemma leakage.
- `P2` `breadth_expansion_gate`: done; the next breadth test is
  `wave7_source_class_breadth_v1`.
- `P2` `assumption_ledger_seed`: done; current candidate assumptions are
  explicit in `semantic_veto_assumption_ledger.md`.
- `P2` `archive_consolidation_triage`: done; selected older source-reference,
  wave5, wave6 precursor, and upper-bound artifacts are labeled historical or
  superseded in the archive ledger and registry.

## Lane Split

This workstream has two live lanes. Keep them separate in future handoffs.

Integrity audit lane:

- First priority: none currently queued.
- Purpose: finish the research-codebase integrity review by checking artifact
  authority, stale `latest` reports, dirty generated outputs, methodology docs,
  and registry classifications.
- Current audit snapshot: the registry has `28` paths with `latest` in the
  primary artifact path; all are classified as `generated_evidence`,
  `historical_reference`, or `superseded`, not runtime truth. Dirty local
  `latest` outputs outside this checkpoint remain non-authoritative until a
  later audit classifies, regenerates, commits, or explicitly excludes them.
- Methodology-doc status: reconciliation links and the wave6 source/guard
  finding are accepted as research-only current-reference material. They do not
  promote a runtime policy and do not replace the registry or quality loop.
- Local-output status: referenced wave2 through wave5 draft inputs were
  committed as historical/seed support; dirty wave5 generated-output churn,
  unreferenced wave6 comparator reports, and generic project-health/rulegen
  outputs remain local-only or out of semantic-veto scope.
- Latest audit report:
  `docs/rulegen/semantic_veto_artifact_authority_audit.md`.
- Rule: do not generate new semantic evidence in this lane unless the user
  explicitly switches back to research.

Research lane:

- Completed action: `wave7_targeted_guard_and_evidence_patch`.
- Result: the targeted guard patch resolved the `even` phrase-preemption false
  abstain and reduced active/shadow false abstains from `3` to `2`. The refreshed
  residual blocker probe now classifies `9` current failures into `5` failure
  classes: `gross` quantity shadow evidence underweighted, `fix` shadow overlap,
  `meet` phrase-control overlap, and phrase/no-winner rescue leakage split into
  dominant vs close phrase-control evidence. The rescue sweep and no-surface
  margin sweep still have `0` combined passing policies, so this remains a
  targeted evidence/rescue-guard problem rather than one scalar threshold
  problem.
- Next queued action: `wave7_shadow_overlap_and_phrase_rescue_followup`.
- Starting artifacts:
  `docs/test_outputs/semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`,
  `docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`,
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.md`,
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.md`,
  `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`,
  and
  `docs/test_outputs/semantic_source_margin_policy_sweep_wave7_source_class_breadth_v1_phrase_control_no_surface_latest.md`.
- Rule: keep this lane research-only until a separate promotion/runtime-policy
  task is explicitly opened.

## Next-Agent Handoff

Start here. This is the canonical handoff for the reconciliation workstream.

Current state:

- Workstream status: active.
- Parked pass: `runtime_path`; the core browser/helper YES/NO path is mapped in
  this document and the registry, including bootstrap, settings, helper-cache,
  transport, background bridge, native dispatch, helper use case, policy,
  scoring, and final DOM rendering surfaces.
- Parked pass: `research_harness`; active harnesses are classified by the
  question they answer.
- Parked pass: `data_artifacts`; the current candidate inputs, generated
  reports, control artifacts, rerun order, and scorer-backed rescue validation
  artifact are explicit.
- Parked pass: `best_candidate`; the current candidate, control, remaining
  blockers, and next breadth gate are explicit.
- Parked pass: `assumptions`; tested, untested, and rejected current-candidate
  assumptions are explicit in `docs/rulegen/semantic_veto_assumption_ledger.md`.
- Parked pass: `archive_consolidation`; selected older source-reference, wave5,
  wave6 precursor, and upper-bound artifacts are labeled historical or
  superseded in `docs/rulegen/semantic_veto_archive_consolidation.md`.
- Parked pass: `local_output_disposition`; remaining local outputs are
  classified in `docs/rulegen/semantic_veto_local_output_disposition.md`.
- Action ledger: reconciliation passes are parked; the next substantive
  semantic-veto work is the research-only
  `wave7_shadow_overlap_and_phrase_rescue_followup` unless a new audit crack
  appears.
- Parked research lane: `wave7_targeted_guard_and_evidence_patch` is complete
  as a partial remediation pass; `wave7_shadow_overlap_and_phrase_rescue_followup`
  is queued and must not be lost, but it is not an audit task.
- Current candidate remains research-only:
  `wave6_auth_frame_raw_sentence_surface_pos_rescue`.
- Next breadth gate: `wave7_source_class_breadth_v1`.
- Latest blocker reports:
  `docs/test_outputs/semantic_wave7_residual_blocker_probe_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`,
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout_validation_latest.md`,
  `docs/test_outputs/semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase_validation_latest.md`,
  and
  `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`.
- Runtime policy change: none.
- Registry audit status: `ok`.

Read in this order:

1. `docs/rulegen/semantic_veto_reconciliation_workstream.md`
2. `docs/rulegen/semantic_veto_artifact_authority_audit.md`
3. `docs/rulegen/semantic_veto_local_output_disposition.md`
4. `docs/test_outputs/semantic_veto_system_registry_latest.md`
5. `docs/test_inputs/semantic_veto_system_registry_en_es.json`
6. `docs/rulegen/semantic_veto_archive_consolidation.md`
7. `docs/rulegen/semantic_veto_assumption_ledger.md`
8. `docs/rulegen/semantic_sentence_veto_algorithm.md`
9. `docs/rulegen/semantic_source_admission_program.md`
10. `docs/rulegen/semantic_decision_rule_comparison_plan.md`
11. `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
12. `docs/rulegen/semantic_veto_wave7_source_class_breadth_runbook.md`
13. `docs/test_outputs/semantic_source_admission_cycle_wave7_source_class_breadth_v1_phrase_control_triage_latest.md`

First task:

- Execute `wave7_shadow_overlap_and_phrase_rescue_followup` only if the user
  wants to continue research remediation; otherwise open a new explicit audit
  pass before changing artifact authority.
- Start from the residual blocker probe, not from a global threshold sweep.
- Keep action items updated as cracks are discovered or resolved.
- Keep durable inputs, generated evidence, control artifacts, and local
  uncommitted experiment outputs separate.
- Do not treat generated reports under `latest` names as architecture authority.
- Do not advance `wave7_shadow_overlap_and_phrase_rescue_followup` unless the user
  explicitly switches from auditing to research remediation.
- Reopen a reconciliation pass only if a new active harness appears, runtime
  policy changes, or another old artifact starts steering current decisions.

Recommended first validation:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue

PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_wave7_residual_blocker_probe_en_es.py \
  core/tests/dev/test_semantic_veto_system_registry_summary.py

python3 scripts/dev/check_doc_references.py

git diff --check
```

## Pass Sequence

### 1. Runtime Path Pass

Question: what code actually participates in the browser-visible YES/NO
decision today?

Output:

- runtime path entries marked `current_runtime`
- all non-runtime but nearby scripts marked research, diagnostic, or historical
- no production-policy claim unless backed by runtime code and tests

Stopping rule:

- the path from eligible match to final `replace` or `abstain` is named in the
  registry and referenced from the system map

### 2. Research Harness Pass

Question: which harness answers which research question?

Output:

- every active sweep/admission/validation script gets a component and state
- duplicate or superseded harnesses are labeled instead of left ambiguous
- each harness states whether it tests context, evidence, scorer, aggregation,
  final decision, phrase handling, or source coverage

Stopping rule:

- a future agent can choose the right harness without scanning every semantic
  script name

### 3. Data And Artifact Pass

Question: which datasets, queues, evidence batches, heldout suites, and reports
are current, exploratory, or historical?

Output:

- current candidate inputs and reports are named as a single lane
- frozen/control inputs are separated from discovery and generated artifacts
- missing hashes or unclear scopes become explicit cracks

Stopping rule:

- the current candidate can be rerun from named inputs without borrowing a
  stale artifact by accident

### 4. Assumption Pass

Question: what assumptions are we relying on without seeing them?

Output:

- assumptions such as raw sentence context, phrase-prototype margins,
  source-triggered authorization frames, and rescue-gate constraints are linked
  to evidence
- assumptions without evidence become queued tests, not folklore

Stopping rule:

- current candidate behavior can be explained as a small list of tested
  assumptions

### 5. Overfit And Leakage Pass

Question: where could the work be shaped to the test cases instead of the
language?

Output:

- case-shaped templates, target-lemma leakage, browser-sentence leakage,
  threshold tuning on heldout, and discovery/eval blending are checked
- negative controls and breadth gaps are listed beside the candidate

Stopping rule:

- the current candidate either survives the audit or is demoted to diagnostic

### 6. Best Candidate Pass

Question: what is the single current path toward quality-gate promotion?

Output:

- one candidate stack
- one control
- one locked active/shadow suite
- one locked phrase/no-winner suite
- one next breadth test
- explicit promotion blockers

Stopping rule:

- future turns know whether to broaden, simplify, promote, or demote the
  current candidate

### 7. Archive And Consolidation Pass

Question: which artifacts should remain reachable but stop steering decisions?

Output:

- historical and superseded rows are marked in the registry
- surviving value is migrated into current docs before any retirement
- no deletion is required unless an artifact actively misleads

Stopping rule:

- old research remains auditable without competing with current truth

## Current Candidate As Of 2026-04-29

The current candidate is still research-only:

- wave6 Wiktextract-supported source dataset
- translation-sense evidence
- WordNet alternate-sense phrase rows
- raw-sentence context
- semantic phrase prototypes
- surface-POS rescue/preemption
- deterministic authorization-frame evidence for source-backed permission-like
  senses
- rescue replay candidate: active margin `0`, phrase margin `0.02`, rescue
  active floor `0.52`, no noun phrase-lead rescue, modifier phrase-lead ceiling
  `0.02`

Current measured read:

- active/shadow wave6 raw-sentence auth-frame lane: `0` harmful, `0` false
  abstains, `100%` recall, `100%` accuracy across `38` cases
- unrescued phrase/no-winner wave6 lane: `2` harmful replacements
- rescue replay over active/shadow plus phrase/no-winner: `12` passing policies
- promotion posture: still `review` because breadth is only `16` families and
  `54` heldout cases

## How To Continue In Later Turns

Start each turn by choosing one pass from the registry. Do not mix pass lenses
unless the workstream document says the pass depends on another one.

Use this loop:

1. Read this workstream and the registry summary.
2. Pick the next pass marked `queued_next` or `in_progress`.
3. Inspect only the docs/code/artifacts in that pass.
4. Update registry rows as evidence is classified.
5. Render the registry summary.
6. Run focused tests and doc hygiene.
7. Report whether the candidate, control, blockers, or next pass changed.

Default validation for registry-only changes:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue

PYTHONPATH=apps/gui/src:core python3 -m pytest \
  core/tests/dev/test_semantic_veto_system_registry_summary.py

git diff --check
```

If a pass touches rulegen scoring, candidate filtering, POS normalization, or
LP tuning, run the rulegen quality loop from `AGENTS.md` instead of treating the
registry checks as sufficient.
