# Semantic Veto Reconciliation Workstream

Status: active workstream
Role: Planning / WIP
Purpose: keep the semantic sentence-veto runtime, research harnesses, data artifacts, and promotion claims aligned while the work spans many turns
Last updated: 2026-04-30
Last verified: 2026-04-30 against `semantic_sentence_veto_algorithm.md`, `semantic_source_admission_program.md`, `semantic_decision_rule_comparison_plan.md`, and `semantic_veto_system_registry_en_es.json`
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

Diagnostics and ledgers:

- `docs/test_inputs/semantic_decision_research_lanes_en_es.json` plus
  `scripts/testing/semantic_decision_research_lanes_summary.py`: tracks research
  lane state without collapsing everything into a generic done/completed state.
- `scripts/testing/semantic_source_failure_class_mining_en_es.py`: reads
  admission, held-out, source, and margin artifacts to expose reusable failure
  classes, breadth gaps, and overfit risk.
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

## Action Ledger

Action items live in `docs/test_inputs/semantic_veto_system_registry_en_es.json`
and render into `docs/test_outputs/semantic_veto_system_registry_latest.md`.
Each row has a priority, status, owning pass, source artifacts, evidence needed,
validation, and promotion impact.

Current highest-priority actions:

- `P0` `materialize_current_wave6_lane`: make the current wave6 lane
  fresh-checkout runnable, or demote local-only latest reports to provisional
  evidence.
- `P1` `scorer_backed_rescue_policy_confirmation`: done; the recommended rescue
  policy passes scorer-backed offline validation over the current 54-row suite.
- `P1` `source_trigger_overfit_audit`: verify authorization-frame evidence is
  source-triggered class behavior, not browser-case or target-lemma shaping.

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
- Action ledger: active; start with `breadth_expansion_gate`.
- Current candidate remains research-only:
  `wave6_auth_frame_raw_sentence_surface_pos_rescue`.
- Runtime policy change: none.
- Registry audit status: `ok`.

Read in this order:

1. `docs/rulegen/semantic_veto_reconciliation_workstream.md`
2. `docs/test_outputs/semantic_veto_system_registry_latest.md`
3. `docs/test_inputs/semantic_veto_system_registry_en_es.json`
4. `docs/rulegen/semantic_sentence_veto_algorithm.md`

First task:

- Continue the `best_candidate` pass by defining the next breadth test before
  tuning the current 16-family wave further.
- Keep action items updated as cracks are discovered or resolved.
- Keep durable inputs, generated evidence, control artifacts, and local
  uncommitted experiment outputs separate.
- Do not treat generated reports under `latest` names as architecture authority.
- Reopen `research_harness` only if a new active harness appears or an existing
  harness changes question/role.

Recommended first validation:

```bash
python3 scripts/testing/semantic_veto_system_registry_summary.py --fail-on-issue

PYTHONPATH=apps/gui/src:core python3 -m pytest \
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
