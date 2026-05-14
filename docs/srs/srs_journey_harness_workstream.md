# SRS Journey Harness Workstream

Status: Active implementation
Role: Planning / WIP
Last updated: 2026-03-21
Purpose: define a reusable end-to-end SRS journey harness that proves bootstrap, feedback, scheduling, admission refresh, publication, and runtime-facing set changes with enough detail for retroactive analysis and pedagogical playback review.
Source-of-truth: planning doc for harness scope and acceptance criteria; current implemented behavior remains defined by helper/SRS code and generated evidence.

## Why This Exists

LexiShift now has enough SRS pieces to prove small synthetic behaviors, but not yet a durable item-level journey.

Today we can already verify:
- bootstrap/publication/runtime artifact presence for `en-ja` and `en-de`
- feedback-driven growth/pause/resume counts for `en-ja`
- helper/runtime count alignment bounds

But the current synthetic harness stops short of the questions we actually need before broader SRS feature work:
- which specific items enter `S`
- which items become due or fade out of the due queue
- which items are actually published into the runtime-facing ruleset
- how repeated feedback changes item-level scheduler state over time
- whether exposure without feedback changes anything it should not
- whether the current publication behavior reflects admitted `S` or due subset `D`

This workstream exists to close that gap without overloading the current synthetic SRS quality harness.

## Current Verified Building Blocks

The codebase is already modular enough to support a reusable harness.

### Helper/engine entrypoints

The harness should use the existing helper APIs rather than custom one-off plumbing:
- `core/lexishift_core/helper/engine.py`
  - `initialize_srs_set(...)`
  - `refresh_srs_set(...)`
  - `apply_feedback(...)`
  - `apply_exposure(...)`
  - `get_srs_runtime_diagnostics(...)`
  - `load_ruleset(...)`
  - `load_snapshot(...)`

### Use-case seams

The helper already separates bootstrap, refresh, and signal mutation into dedicated use cases:
- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/signals.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`

### Existing synthetic harness

The current synthetic lane remains useful as a smoke harness and should stay separate:
- `scripts/testing/srs_quality_harness.py`
- `scripts/testing/srs_quality_summary.py`

### Documented model and current known gap

The intended SRS model is already documented:
- due set `D` exists as a runtime view
- due items should be served first
- exposure is non-authoritative
- bootstrap admission and refresh are separate from scheduling

Current known gap remains explicit:
- helper publication appears to cover admitted items more broadly than the due subset in the current synthetic scenario

The new journey harness must keep this gap explicit instead of hiding it.

## Scope

### Primary goal

Prove the plain working SRS journey, with enough detail for retroactive analysis:
1. initialize `S`
2. publish runtime-facing helper outputs
3. observe admitted, due, and published sets
4. apply feedback and exposure events
5. advance time deterministically
6. refresh admissions/publication
7. verify item inflow, outflow, fade-out, stickiness, and growth behavior

### Non-goals for first version

The first version does not try to prove:
- pedagogical optimality
- browser/UI feel in real browsing
- extension confidence-gating correctness
- context-aware replacement quality
- full profile-driven growth intelligence

Those can be layered later.

## Harness Structure

This should be a new harness family, not a single monolithic script.

Planned files:
- `scripts/testing/srs_journey_harness.py`
- `scripts/testing/srs_journey_summary.py`
- `scripts/testing/srs_journey_html.py`
- `scripts/testing/srs_journey_harness_support.py`
- `scripts/testing/srs_journey_review_support.py`
- `core/tests/dev/test_srs_journey_harness.py`
- `core/tests/dev/test_srs_journey_summary.py`
- `core/tests/dev/test_srs_journey_html.py`

## Harness Lanes

The harness should support multiple lanes so we can isolate different parts of the SRS stack.

### Lane A: deterministic core journey

Purpose:
- prove scheduler/admission/publication mechanics without rulegen quality noise

Characteristics:
- deterministic clock
- deterministic candidate universe
- deterministic publication payloads
- helper APIs remain real

What it proves:
- item-level state transitions
- growth pause/resume
- due behavior
- admitted vs published relationships

### Lane B: publication-contract lane

Purpose:
- focus specifically on admitted `S` vs due subset `D` vs published runtime set `P`

Characteristics:
- same deterministic fixture style as Lane A
- stronger comparisons among `S`, `D`, and `P`

What it proves:
- whether publication is due-aware
- whether mismatches are stable and inspectable

### Lane C: real full-E2E lane

Purpose:
- prove the integrated journey with real publication/rulegen behavior

Characteristics:
- real helper APIs
- real rule publication
- deterministic clock and scenario sequencing still preferred

What it proves:
- the actual system works end to end, not just the isolated scheduler logic

Current implemented scenarios:
- `en-ja_real_publication_v1`
  - deterministic clock and synthetic resources
  - actual seed builder
  - synthetic `en-ja` resources
  - real helper/rulegen publication path
- `en-es_real_publication_v1`
  - deterministic clock and synthetic resources
  - actual seed builder
  - synthetic `en-es` FreeDict + frequency resources
  - real helper/rulegen publication path
- `en-ja_installed_data_journey_v1`
  - deterministic clock with installed local BCCWJ + JMdict resources staged into an isolated temp helper root
  - dynamic cohort assignment from actual admitted and newly selected lemmas
  - real helper/rulegen publication path
- `en-es_installed_data_journey_v1`
  - deterministic clock with installed local Spanish frequency + FreeDict resources staged into an isolated temp helper root
  - dynamic cohort assignment from actual admitted and newly selected lemmas
  - real helper/rulegen publication path
- current `en-ja` and `en-es` journey artifacts are not the Lane 5 due-aware
  runtime-serving authority; use `scripts/testing/srs_quality_harness.py` and
  `docs/test_outputs/srs_quality_latest.json` for the helper due metadata plus
  extension-gate contract

### Lane D: edge-behavior lane

Purpose:
- prove real-but-messy interaction patterns are coherent and inspectable

Current implemented edge scenarios:
- repeated feedback for the same word in one short session
- exposure without feedback
- exposure-only refresh after a low-retention gate is already active

Later edge scenarios:
- refresh under high due pressure
- recovery after low retention

## Pair Rollout

### First pair

Start with `en-ja`.

Reason:
- already covered by the current synthetic SRS harness
- good enough current stability for scheduler-focused work
- less confounded by current `en-es` rulegen quality work

### Second pair

Extend to `en-es` after the first lane is stable.

Reason:
- it is materially more complete than `en-de`
- it gives better parity with the current mature rulegen/product surface
- it exercises FreeDict-based publication on the stronger non-`en-ja` path

### Third pair

Extend to `en-de` after `en-es` parity is stable.

### Later pairs

Only expand further after the harness contract is stable and the first three pairs produce useful artifacts.

## Scenario Model

Each scenario should be declarative and reusable.

Recommended scenario fields:
- `name`
- `pair`
- `profile_id`
- `lane`
- `contract_mode`
- `settings`
- `bootstrap`
- `candidate_universe`
- `cohorts`
- `phases`
- `expected_outcomes`

### Cohorts

The first scenario should use three cohorts:
- stable/easy cohort
- difficult/review-heavy cohort
- frontier/not-yet-admitted cohort

This is the minimum useful structure for proving fade-out, stickiness, and new-item inflow.

### Phases

Each phase should declare:
- `label`
- `clock_step`
- `feedback_events`
- `exposure_events`
- `refresh` yes/no
- `expectations`

## Time Model

The harness should use deterministic synthetic time.

Default behavior:
- fixed timestamps
- explicit short same-session gaps
- explicit hour/day jumps between refresh phases

Reason:
- repeatability matters more than wall-clock realism
- we still need enough temporal structure to resemble plausible user behavior

Implementation preference:
- explicit optional time injection where feasible
- fallback to tightly scoped patching only if necessary

## Data Capture Requirements

The JSON artifact should be analysis-first, not just summary-first.

### Scenario manifest

Capture:
- pair
- lane
- contract mode
- profile id
- settings
- candidate universe
- cohort definitions
- clock schedule

### Raw operation payloads

Capture:
- initialize payload
- refresh payloads
- runtime diagnostics payloads
- ruleset metadata
- snapshot metadata

### Signal/event log

Capture:
- every feedback event
- every exposure event
- timestamp
- order index
- lemma
- rating where relevant

### Per-phase snapshots

For every phase capture:
- admitted set `S`
- due set `D`
- published set `P`
- per-item scheduler fields
- exposures count
- history summary
- counts for `S`, `D`, `P`

### Phase deltas

For every phase transition capture:
- admitted in
- admitted out
- due in
- due out
- published in
- published out

### Optional archival mode

Support an archival mode that stores dated, phase-level artifacts for deep investigation while keeping `latest` aliases for routine workflow use.

## Publication Contract Modes

The harness should not pretend the admitted-vs-due question is already resolved.

Planned contract modes:
- `observe_current_behavior`
- `require_due_aware_publication`

Initial default:
- `observe_current_behavior`

Meaning:
- publication broader than due subset is a surfaced warning, not a hidden assumption

Later, if due-aware serving becomes the real implemented contract, the same harness can tighten this into a failure condition.

## Assertions

### Bootstrap assertions

- initialization applies successfully
- store, ruleset, and snapshot exist
- admitted count matches expected bootstrap active count
- published count does not exceed admitted inventory without explicit explanation

### Scheduler assertions

- repeated `easy` / `good` increases interval and reduces near-term due pressure for that item cohort
- repeated `again` / `hard` keeps items closer to due
- scheduler state is inspectable after each phase

### Growth assertions

- high retention admits new items when capacity exists
- low retention pauses new admissions
- recovery resumes new admissions
- admissions stay within caps

### Exposure assertions

- exposure-only events are recorded and visible
- exposure-only events do not count as feedback-window events
- exposure-only behavior does not silently drive retention-based admission logic

### Publication-scope assertions

- `S`, `D`, and `P` are all reported separately
- contract-mode findings are explicit
- publication scope drift is visible in the report

## Documentation Deliverables

### Planning doc

This file is the current planning source for the workstream.

### Operational doc updates after implementation begins

Update when commands exist:
- `scripts/README.md`
- `docs/developer/local_setup.md`
- `docs/developer/developer_reference.md`

### Feature-state tracking

Add/update an item in:
- `docs/developer/feature_state_matrix.md`

Suggested row name:
- `SRS Journey E2E Harness`

### Generated evidence

Planned artifact root:
- `docs/test_outputs/srs_journey/`

Planned initial artifacts:
- `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.json`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.md`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.html`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.json`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.md`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.html`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.json`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.md`
- `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.html`

Generated evidence remains evidence, not architecture authority.

## Acceptance Criteria

Do not call this harness complete until all of the following are true.

1. Deterministic replay
   - repeated runs produce the same item-level behavior aside from timestamps/paths explicitly marked variable

2. Item-level visibility
   - each phase exposes `S`, `D`, `P`, scheduler state, exposures, and deltas

3. Cohort proof
   - stable cohort fades from near-term due pressure
   - difficult cohort remains or resurfaces
   - frontier cohort enters only when policy allows

4. Growth pause/resume proof
   - high retention admits
   - low retention pauses
   - recovery resumes

5. Exposure proof
   - exposure-only scenarios are visible and non-authoritative for retention logic

6. Publication-contract proof
   - admitted-vs-due-vs-published relationships are explicit and machine-readable

7. Human review artifact
   - Markdown summary exists for concise handoff
   - interactive HTML playback exists for full pedagogical inspection without opening raw JSON only

8. Regression safety
   - targeted tests pass
   - existing synthetic SRS quality harness still passes
   - standard repo safety remains clean

## Implementation Phases

### Phase 0: planning and schema lock

Deliverables:
- this planning doc
- JSON schema outline
- lane definitions
- artifact layout

### Phase 1: deterministic core journey lane

Deliverables:
- reusable scenario support
- deterministic time control
- item-level phase snapshots
- JSON artifact for `en-ja`

#### Phase 1 exact lane scope

Phase 1 is intentionally narrow.

Included:
- helper/API-driven bootstrap
- helper/API-driven feedback application
- helper/API-driven refresh
- item-level `S` / `D` / `P` snapshots
- deterministic publication payloads
- deterministic clock
- cohort-based fade/stick/growth checks

Excluded until later phases:
- browser/runtime automation
- real rulegen lexical quality
- extension confidence gating
- exposure-only contract checks as a blocking lane

#### Phase 1 exact artifact shape

Top-level JSON shape:

```json
{
  "version": 1,
  "generated_at": "...",
  "plan_doc": "docs/srs/srs_journey_harness_workstream.md",
  "scenario": {},
  "initialize": {},
  "phases": [],
  "summary": {},
  "findings": []
}
```

Scenario payload:

```json
{
  "name": "en-ja_core_journey_v1",
  "pair": "en-ja",
  "lane": "deterministic_core_journey",
  "contract_mode": "observe_current_behavior",
  "profile_id": "default",
  "settings": {
    "max_active_items": 8,
    "max_new_items_per_day": 2
  },
  "bootstrap": {
    "set_top_n": 200,
    "initial_active_count": 3,
    "replace_pair": true
  },
  "candidate_universe": [],
  "cohorts": {},
  "clock": {}
}
```

Per-phase payload:

```json
{
  "label": "high_retention_growth",
  "step_index": 2,
  "now": "...",
  "events_applied": {
    "feedback": [],
    "exposure": []
  },
  "refresh": {
    "requested": true,
    "payload": {}
  },
  "runtime": {
    "diagnostics": {},
    "ruleset_path": "...",
    "snapshot_path": "..."
  },
  "sets": {
    "admitted": [],
    "due": [],
    "published": []
  },
  "counts": {
    "admitted": 0,
    "due": 0,
    "published": 0
  },
  "deltas": {
    "admitted_in": [],
    "admitted_out": [],
    "due_in": [],
    "due_out": [],
    "published_in": [],
    "published_out": []
  },
  "items": [],
  "findings": []
}
```

Per-item payload:

```json
{
  "lemma": "alpha",
  "cohort": "stable",
  "status": "review",
  "next_due": "...",
  "stability": 0.0,
  "difficulty": 0.0,
  "retrievability": 0.0,
  "scheduler_state": "review",
  "scheduler_step": null,
  "last_review": "...",
  "exposures": 0,
  "history_count": 0,
  "recent_history": [],
  "in_admitted": true,
  "in_due": false,
  "in_published": true
}
```

#### Phase 1 exact scenario definition

Scenario name:
- `en-ja_core_journey_v1`

Synthetic candidate universe:
- `alpha`
- `beta`
- `gamma`
- `delta`
- `epsilon`
- `zeta`
- `eta`

Cohorts:
- `stable`: `alpha`, `beta`
- `difficult`: `gamma`
- `frontier`: `delta`, `epsilon`, `zeta`, `eta`

Deterministic publication behavior:
- publish one canonical rule per admitted lemma
- the rule target string only exists to reflect set membership
- no lexical/ranking quality is being tested in this lane

Reason:
- Phase 1 is isolating SRS journey mechanics, not rulegen quality

#### Phase 1 exact phases

1. `bootstrap_publish`
   - initialize `S`
   - publish deterministic runtime artifacts
   - expected admitted: `alpha`, `beta`, `gamma`

2. `baseline_observe`
   - no new events
   - capture initial `S`, `D`, `P`

3. `high_retention_growth`
   - apply 8 total `good` / `easy` events across `alpha` and `beta`
   - advance clock by 1 day
   - refresh
   - expect:
     - at least one frontier item admitted
     - `alpha`/`beta` trending away from near-term due pressure

4. `low_retention_pause`
   - apply 8 total `again` / `hard` events concentrated on `gamma`
   - advance clock by 1 day
   - refresh
   - expect:
     - no new admissions
     - reason code reflects retention pause or due-pressure pause

5. `recovery_resume`
   - apply 8 total `good` / `easy` events across `gamma` and newest admitted items
   - advance clock by 1 day
   - refresh
   - expect:
     - new admissions resume
     - difficult cohort remains more active than stable cohort

6. `fade_check`
   - advance clock by 7 days
   - no new feedback
   - capture `S`, `D`, `P`
   - expect:
     - stable cohort is less represented in `D`
     - difficult cohort is more represented in `D`
     - published/admitted/due relationships remain explicit

#### Phase 1 exact findings to emit

Required finding codes:
- `SRS_JOURNEY_BOOTSTRAP_APPLIED`
- `SRS_JOURNEY_RUNTIME_ARTIFACTS_PRESENT`
- `SRS_JOURNEY_HIGH_RETENTION_ADMITS`
- `SRS_JOURNEY_LOW_RETENTION_PAUSES`
- `SRS_JOURNEY_RECOVERY_RESUMES`
- `SRS_JOURNEY_STABLE_COHORT_FADES`
- `SRS_JOURNEY_DIFFICULT_COHORT_STICKS`
- `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`

### Phase 2: summary renderer and tests

Deliverables:
- Markdown summary
- targeted tests for harness and summary

### Phase 3: publication-contract lane and edge cases

Deliverables:
- explicit `S` vs `D` vs `P` findings
- duplicate-feedback scenario
- exposure-only scenario
- due-pressure scenario

Current state:
- duplicate-feedback scenario implemented in `en-ja_edge_behaviors_v1`
- exposure-only scenario implemented in `en-ja_edge_behaviors_v1`
- due-pressure-specific edge scenario still pending

### Phase 4: real full-E2E lane

Deliverables:
- same journey structure with real publication/rulegen behavior
- paired comparison against deterministic lane where useful

Current state:
- `en-ja_real_publication_v1` implemented
- `en-es_core_journey_v1`, `en-es_edge_behaviors_v1`, and `en-es_real_publication_v1` implemented
- current `en-ja` and `en-es` artifacts show complete word-package coverage and complete due publication
- later expansion still needed for `en-de` and less synthetic resources

### Phase 5: second pair and workflow integration

Deliverables:
- `en-es` support
- follow-on `en-de` support
- package-script wrappers if warranted
- script routing docs updated
- feature-state row updated from planning to implemented when true

## Open Questions

1. Should the journey harness adopt the Lane 5 runtime due-metadata check, or stay focused on item-level journey flow?
2. How much explicit time injection is worth plumbing versus scoped patching?
3. Do we want the real full-E2E lane to be mandatory in routine workflow, or advisory until it stabilizes?

## Immediate Next Step

The next planning deliverable should be a concrete schema and lane spec for Phase 1:
- exact JSON structure
- exact phase names
- exact event model
- exact scenario cohorts for `en-ja`
