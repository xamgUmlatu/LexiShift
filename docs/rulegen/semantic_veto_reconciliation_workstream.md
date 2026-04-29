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

## Next-Agent Handoff

Start here. This is the canonical handoff for the reconciliation workstream.

Current state:

- Workstream status: active.
- Active pass: `runtime_path`; the core browser/helper YES/NO path is now
  mapped in this document and the registry, including bootstrap, settings,
  helper-cache, transport, background bridge, native dispatch, helper use case,
  policy, scoring, and final DOM rendering surfaces.
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

- Continue the `runtime_path` pass only if another runtime-adjacent surface is
  discovered.
- Otherwise move to the next queued reconciliation pass and keep the runtime
  map stable unless code changes.
- Keep nearby research or diagnostic files non-runtime in the registry.
- Do not make a runtime policy change during this pass.

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
