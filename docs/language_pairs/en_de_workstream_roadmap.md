# `en-de` Workstream Roadmap

Status: active planning doc
Role: Planning / WIP
Purpose: define the German-target `en-de` quality workstream now that baseline pair enablement exists and the next step is to give the lane a durable benchmark/gate/triage surface modeled on `en-es` without pretending the pair is already at `en-es` maturity.
Last updated: 2026-06-09
Last verified: 2026-06-09 en-de Leipzig source-frequency default implementation, scoped rulegen gate refresh, SRS harness, and LP conformance/resource audits
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
- do not treat current resource/runtime enablement as quality parity
- do not promote reverse-check or Kaikki-style provenance work before the
  baseline lane is stable enough to measure them
- do not invent a separate benchmark architecture for `en-de`

## Current Starting Point

What already exists:

- `en-de` has a real pair capability and rulegen mode
- `en-de` resolves the normalized translation-pack seam through `freedict-de-en`
- the pair is benchmarkable in the shared rulegen harness
- the pair has baseline helper / adapter / POS / SRS coverage
- the pair has source-stack setup resources for `freq-de-default`,
  `freedict-de-en`, `freedict-en-de`, and the English source-frequency prior
- the installed helper/resource smoke now shows `en-de` is usable in the
  runtime/SRS beta path when those resources are present

Current known benchmark picture:

- dataset size is `58` targets in the latest advisory artifact
- latest top3-first Leipzig default run: `top1=86.21%`, `top3=100.00%`,
  `forbidden_top1=0.00%`, `forbidden_any=15.52%`, and
  `avg_rules_per_target=2.29`
- latest scoped quality gate passes the current advisory floors; delta checks
  still warn with `DELTA_SCOPE_BASELINE_MISSING` until an `en-de` machine
  delta baseline is promoted
- product acceptance: the current scoped advisory result is accepted for
  current beta/onboarding use as of 2026-06-09, without claiming hard-gated
  parity with `en-es`
- latest triage has `12` actionable items (`9` FAIL, `3` REVIEW). The failures
  are forbidden-any cases rather than forbidden-top1 cases, so the correct cue
  is retained in top3 but some broad/default glosses still need severity-aware
  cleanup.
- the installed English source-frequency prior used by `en-de` rulegen is now
  `freq-en-leipzig-default/main.sqlite` from Leipzig English News 2025 1M,
  with `113,401` kept English lemmas; `freq-en-coca.sqlite` remains a fallback
  compatibility artifact

2026-06-09 source-frequency implementation checkpoint:

- A temporary `wordfreq` 60k English SQLite is the strongest observed research
  signal so far: a focused top3-preserving sweep reached `86.21%` top1,
  `100.00%` top3, `0.00%` forbidden-top1, and `9` forbidden-any cases.
  Keep this as evidence that broad English source frequency is high leverage,
  not as the first production pack choice: upstream `wordfreq` docs explicitly
  discourage converting the data to flat formats because attribution/license
  context and normalization code are not separable.
- `freq-en-leipzig-default` is now implemented as an app-managed local build
  from Leipzig English News 2025 1M, reusing the existing Leipzig frequency
  builder shape. It is wired as the default English source-frequency prior for
  `en-de` rulegen and as the default English frequency source for English
  target/bootstrap lanes, with `freq-en-coca` retained only as fallback.
- Leipzig 2025 100K produced the same best focused score as 1M in this small
  benchmark (`84.48%` top1 / `98.28%` top3), but 1M remains the safer default
  candidate until download/runtime tradeoffs are measured.
- The canonical top3-first refresh now keeps every expected answer in top3.
  Remaining forbidden-any hits are mostly broad/defaultness cases
  (`Schule -> pod`, `Zeit -> spell/most`, `Fenster -> box`, `Tag -> tag`,
  `Kopf -> mind`, `Ohr -> hearing/audition`, `Fuß -> head`, `Zug -> strain`,
  `Stimme -> part`).

Recommended next scoring order:

1. Leave the current scoped `en-de` result accepted for beta/advisory use, and
   defer machine delta-baseline promotion until a release-gate decision needs
   it.
2. Keep reverse-check as a follow-up TODO, not the next automatic fix. It is promising
   for cases like `Fenster -> box`, `Tag -> tag`, `Fuß -> base/head`, and
   `Zug -> strain`, but early experiments did not beat the best frequency-only
   configuration.
3. Keep a severity-aware forbidden-any review as a TODO. Some forbidden labels
   are truly bad for teaching, while others are valid-but-non-default senses
   such as `Tag -> tag`; do not chase zero forbidden-any before separating
   severity from correctness.
4. Keep English POS/defaultness enrichment as a later TODO if source frequency
   plus retuning leaves systematic broad-sense failures such as
   `Stimme -> part` or `Kopf -> mind`.

What does not exist yet:

- no promoted reverse-check lane or default-on decision
- no `en-es`-style richer scoring frontier
- no hard-gated pair status
- no promoted `en-de` machine delta baseline
- no default `en-de` semantic/veto reference pack

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

- partially wired; not promoted

Goal:

- decide whether `en-de` should become a promoted reverse-check pair after the baseline lane is stable

Entry rule:

- do not start this phase just because `en-es` has reverse-check
- do not promote it unless the `en-de` baseline lane is stable enough that
  reverse evidence can be measured cleanly

Completed low-level wiring:

1. add reverse resource resolution
2. add reverse metadata emission
3. add ranking-hook support
4. add pair-specific tests

Remaining promotion work:

1. add a committed reverse experimental lane,
2. compare it against the current `rev=off` advisory and Kaikki lanes,
3. only then decide whether any default-on policy is warranted.

Current checkpoint:

- reverse resource resolution, metadata emission, ranking-hook support, and pair/probe tests are now wired
- first focused Kaikki reverse experiment exists locally, but the tested `rev=on` setting did not beat `rev=off`
- no committed promoted reverse lane or default-on decision yet

Definition of done:

- `en-de` has committed reverse-lane artifact evidence strong enough to justify
  either a promoted next-step workstream or an explicit "do not promote yet"
  decision.

## Phase 4: Pair-Specific Scoring Frontier

Status:

- not started

Goal:

- decide which `en-de`-specific scoring work is actually justified after the baseline and reverse story are clearer

Possible candidates:

- optional machine delta-baseline promotion after release-gate review
- dictionary-structure/default-sense handling for broad glosses
- limited reverse-aware scoring for false-friend/defaultness cases
- severity-aware forbidden-any triage so valid loan/non-default senses do not
  get treated like truly wrong translations
- later provenance-like additions if the pair resources ever justify them

Non-goal:

- do not copy the `en-es` Kaikki frontier just because it exists

Definition of done:

- the pair has a justified next scoring workstream rather than a generic wish list

## Current Open Risks

1. `en-de` can now look more mature than it is because runtime/SRS smoke passes; docs must keep runtime beta, advisory rulegen quality, and hard-gated parity separate.
2. The current scoped rulegen quality gate passes and is product-accepted for beta use, but delta checks intentionally warn until a machine baseline is promoted.
3. The current failures still look like lexical-quality/default-gloss failures first, not obviously reverse-check failures.
4. There is no committed `en-de` semantic/veto reference artifact, so semantic parity and false-abstain cleanup should not be claimed before a real reference pack is generated and evaluated.
5. Topic coverage is limited: current profile/topic plumbing can carry topic preferences, but `freq-de-default` does not provide topic columns and the Options UI exposes only a supported subset for `en-de`.

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
4. the scoped advisory gate passes its current floors
5. the lane still clearly says:
   - advisory, not hard-gated
   - no promoted reverse-check lane yet
   - no richer scoring frontier yet

Only after that should the workstream move toward promoted reverse-check or
deeper pair-specific tuning.
