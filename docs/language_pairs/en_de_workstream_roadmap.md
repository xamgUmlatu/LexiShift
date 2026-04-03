# `en-de` Workstream Roadmap

Status: active planning doc
Role: execution roadmap / advisory quality-lane plan
Purpose: define the German-target `en-de` quality workstream now that baseline pair enablement exists and the next step is to give the lane a durable benchmark/gate/triage surface modeled on `en-es` without pretending the pair is already at `en-es` maturity.
Last updated: 2026-04-03
Last verified: 2026-04-03
Source-of-truth: planning doc only; executable truth still lives in code, tests, benchmark artifacts, and `docs/developer/feature_state_matrix.md`.

## Scope

This roadmap is for the German-target lane:

- `en-de`

It is not the same workstream as:

- `de-en`

Naming rule:

- LP keys are directional `source-target`
- so German target means `en-de`, not `de-en`

Primary goal:

- bring `en-de` up from "implemented and benchmarkable" to "named advisory quality lane with repeatable artifacts, clear next steps, and explicit rollout criteria"

Primary non-goals:

- do not claim `en-de` is already at `en-es` quality maturity
- do not block the quality-lane scaffold on the missing `freq-de-default.sqlite`
- do not front-load reverse-check or Kaikki-style provenance work before the baseline lane is stable enough to measure them
- do not invent a separate benchmark architecture for `en-de`

## Current Starting Point

What already exists:

- `en-de` has a real pair capability and rulegen mode
- `en-de` resolves the normalized translation-pack seam through `freedict-de-en`
- the pair is benchmarkable in the shared rulegen harness
- the pair has baseline helper / adapter / POS / SRS coverage
- the pair already has dated benchmark evidence from the all-pairs advisory run family

Current known benchmark picture:

- dataset size is `16` targets
- the best committed dated advisory run is still `top1=75.00%`, `top3=100.00%`
- current actionable REVIEW cases are:
  - `Haus`
  - `Schule`
  - `Weg`
  - `Zeit`

What does not exist yet:

- no reverse-check implementation
- no `en-es`-style richer scoring frontier
- no hard-gated pair status
- no broad enough benchmark corpus to support strong pair-level claims

## What "Dedicated Lane" Means For `en-de`

The `en-de` workstream should heavily reuse the `en-es` structure.

That means:

1. a named benchmark shape
2. named latest artifacts
3. named summary artifacts
4. named wrapper commands
5. a pair-scoped gate path so the lane only reports `en-de` quality problems
6. an explicit roadmap that separates:
   - baseline lane
   - reverse-check rollout
   - later scoring-frontier work

It does **not** mean:

- copying the `en-es` algorithm stack into `en-de`
- requiring Kaikki-specific machinery before the lane is useful
- pretending every pair needs a custom benchmark framework

The structure should mirror `en-es`.
The pair-specific logic should only be added when the failures justify it.

## Lessons To Reuse From `en-es`

### 1. Copy the lane structure before copying pair logic

`en-es` is useful partly because it has stable latest artifacts, summaries, and a recognizable workstream shape.

Implication for `en-de`:

- create the named lane first
- keep it advisory until evidence is strong enough for hard-gate status

### 2. Baseline lexical quality comes before advanced scoring

The current `en-de` failures are broad lexical-choice failures, not proof that the pair immediately needs the full `en-es` frontier.

Implication:

- first improve case coverage and lexical-choice observability
- only then decide whether reverse-check or another signal is the best next step

### 3. Reverse-check is a phase, not the first milestone

`en-es` only became a real reverse-check workstream after the pair already had a stable lane to compare against.

Implication:

- `en-de` should first have a clean non-reverse advisory lane
- reverse-check should become the next workstream only if the baseline lane stays stable enough to expose real gains

### 4. Do not overfit the policy before the dataset expands

`en-de` currently has enough cases to expose some failure families, but not enough to support strong pair-level optimization claims.

Implication:

- grow the case set before tightening the pair too aggressively

## High-Level Goal

Success for this workstream is:

1. `en-de` has a first-class advisory benchmark/gate/triage lane
2. the lane has a named preset and named wrapper commands
3. the lane has current latest artifacts that are easy to inspect and compare
4. the next phase after the baseline lane is explicit:
   - dataset expansion / lexical cleanup first
   - reverse-check decision second
   - richer scoring frontier only after that

Success is not:

- "`en-de` now matches `en-es`"

## Phase Order

## Phase 0: Naming And Lane Scaffold

Status:

- implemented enough for the first advisory lane

Goal:

- give `en-de` the same recognizable operating shape as `en-es`, without hard-gating it

Concrete work:

1. add a named `en-de` canonical preset
2. add named package commands for:
   - benchmark/gate/triage
   - human-facing summaries
3. add dedicated latest artifact paths
4. document the lane in workflow/state docs

Definition of done:

- a contributor can run one obvious command to refresh the `en-de` advisory lane

## Phase 1: Baseline Advisory Lane

Status:

- active

Goal:

- make `en-de` measurable as its own pair rather than only as a row inside all-pairs artifacts

Concrete work:

1. keep current latest artifacts refreshed from the named lane
2. keep current failures explicit rather than burying them under `en-es` policy work
3. avoid mixing reverse-check or provenance hypotheses into the baseline lane

Definition of done:

- `en-de` has current benchmark, gate, triage, and summary artifacts under dedicated `*_latest` paths

## Phase 2: Dataset Expansion And Failure-To-Case Promotion

Status:

- in progress

Goal:

- make the benchmark broad enough to support pair-specific quality work

Concrete work:

1. expand beyond the current `16` cases
2. preserve the current REVIEW cases as anchor failures
3. add harder polysemy / lexical-competition cases instead of only common-word smoke
4. keep triage-to-case promotion explicit

Definition of done:

- `en-de` has a broader case family surface and the current top-1 failures are represented durably in the dataset

## Phase 3: Reverse-Check Decision

Status:

- not started

Goal:

- decide whether `en-de` should become a reverse-check pair after the baseline lane is stable

Entry rule:

- do not start this phase just because `en-es` has reverse-check
- start it only if the `en-de` baseline lane is stable enough that reverse evidence can be measured cleanly

Concrete work if started:

1. add reverse resource resolution
2. add reverse metadata emission
3. add ranking-hook support
4. add pair-specific tests
5. add a separate reverse experimental lane before any default-on decision

Current checkpoint:

- reverse resource resolution, metadata emission, ranking-hook support, and pair/probe tests are now wired
- first focused Kaikki reverse experiment exists locally, but the tested `rev=on` setting did not beat `rev=off`
- no committed promoted reverse lane or default-on decision yet

Definition of done:

- `en-de` reaches at least `wired` in the reverse-check rollout matrix with committed artifact evidence

## Phase 4: Pair-Specific Scoring Frontier

Status:

- not started

Goal:

- decide which `en-de`-specific scoring work is actually justified after the baseline and reverse story are clearer

Possible candidates:

- lexical-choice signals
- dictionary-structure handling
- limited reverse-aware scoring
- later provenance-like additions if the pair resources ever justify them

Non-goal:

- do not copy the `en-es` Kaikki frontier just because it exists

Definition of done:

- the pair has a justified next scoring workstream rather than a generic wish list

## Current Open Risks

1. `freq-de-default.sqlite` is still missing in the current workspace, so practical initialize/refresh work remains blocked even though benchmark refresh is possible.
2. The current case set is too small for strong optimization claims.
3. The current failures still look like lexical-quality failures first, not obviously reverse-check failures.
4. `en-de` can now look more mature than it is because it has a named lane; the docs must keep advisory and hard-gated status separate.

## Primary Evidence And Code Anchors

- `core/lexishift_core/helper/lp_capabilities.py`
- `core/lexishift_core/helper/pair_resources.py`
- `core/lexishift_core/rulegen/adapters.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `docs/developer/ai_workflow.md`
- `docs/developer/feature_state_matrix.md`
- `docs/rulegen/reverse_check_rollout_matrix.md`
- `docs/test_inputs/rulegen_benchmark_cases/en_de.json`
- `docs/test_inputs/rulegen_benchmark_presets.json`
- `scripts/package.json`

## Current Decision Rule

For now, treat `en-de` as acceptable to move forward when all of these are true:

1. the dedicated advisory lane exists and is refreshable
2. latest artifacts are present and current
3. failures are visible in triage rather than hidden in prose
4. the lane still clearly says:
   - advisory, not hard-gated
   - no reverse-check yet
   - no richer scoring frontier yet

Only after that should the workstream move toward reverse-check or deeper pair-specific tuning.
