# `de-en` Workstream Roadmap

Status: active planning doc
Role: execution roadmap / proof-LP plan
Purpose: define the concrete `de-en` workstream as the first proof that the generalized translation-pack rulegen contract can support an additional cross-lingual LP without another infrastructure rewrite.
Last updated: 2026-04-03
Last verified: 2026-04-03
Source-of-truth: planning doc only; executable truth still lives in code, tests, and benchmark artifacts.

## Scope

This roadmap is for the first real `de-en` rulegen enablement workstream.

Primary goal:

- make `de-en` a real rulegen-capable LP on top of the generalized translation-pack seam

Primary non-goals:

- do not fully optimize `de-en` before it works end to end
- do not front-load broad sweep infrastructure beyond what is needed for a small first benchmark
- do not block the first `de-en` slice on German frequency work
- do not port the full advanced `en-es` Kaikki policy stack into `de-en` immediately

## Why `de-en` Is The Right First Proof LP

`de-en` is the best next LP because:

- the generalized helper/resource/adapter seam is now clean enough to prove on a second translation pair
- `de-en` is mostly a translation-pack and adapter problem, not a new architecture problem
- it can reuse `freq-en-coca.sqlite` for its first frequency lane
- it gives us a concrete proof that the new generic translation-pack contract is reusable beyond the current `en-es` reference lane

Current relevant resources:

- forward translation pack: `freedict-en-de` (temporary TEI compatibility today; canonical target is compiled SQLite)
- reverse translation pack: `freedict-de-en` (temporary TEI compatibility today; canonical target is compiled SQLite)
- default frequency DB: `freq-en-coca.sqlite`

Related normalization target:

- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/data_source_normalization_architecture.md`

## Current Starting Point

What already exists:

- `de-en` is known in pair capability/readiness metadata
- `de-en` is selectable for SRS
- default frequency for `de-en` is already `freq-en-coca.sqlite`
- generic translation-dictionary naming and normalized pack refs are now implemented at the helper/adapter seam
- `de-en` directional filename defaults now correctly resolve `eng-deu.tei`
- translation language packs now have a first manifest-backed install layout, so `de-en` no longer has to rely only on flat filename discovery when the pack is app-installed

What does not exist yet:

- no `de-en` rulegen adapter path
- no `de-en` pair implementation file analogous to `en_de.py`
- no `de-en` benchmark dataset or benchmark lane
- no `de-en` reverse-check implementation
- no `de-en` pair-specific benchmark/tuning story

So the first milestone is still enablement, not tuning.

## Lessons Carried Forward From `en-es`

The biggest portable lessons from the `en-es` workstream are:

### 1. Forward resource quality matters more than clever tuning

For `en-es`, the decisive quality jump came from moving to the better forward lane and then using reverse as support.

Implication for `de-en`:

- get the forward `eng-deu` lane working cleanly first
- keep reverse-pack identity available from day one
- do not hide provider/direction assumptions in field names or one-off code

### 2. Admission quality often matters more than broad scoring-weight sweeps

For `en-es`, the most profitable sweeps were around:

- `max_definitions_per_target`
- `max_rules_per_target`
- tighter admission surfaces
- a small number of additive structural signals

Implication for `de-en`:

- do not start with giant scoring-weight matrices
- get baseline admission behavior right first

### 3. Structural dictionary handling beats late ranking hacks

For `en-es`, many real wins came from:

- preserving order
- recovering broad candidates from list-shaped glosses
- POS-aware filtering
- not accidentally dropping the correct sense with generic filters

Implication for `de-en`:

- first inspect real FreeDict `eng-deu` entry formats
- do not assume the generic current filters are already correct for German source candidates
- prioritize source-candidate extraction and normalization quality before fancy ranking
- migrate the pair off direct TEI runtime dependency once the normalized compiled-pack layer is ready

### 4. The benchmark must reflect failure families, not just common words

For `en-es`, the benchmark only became truly useful once it included:

- polysemy
- phrase-sensitive verbs
- domain/everyday competition
- forbidden-side failures

Implication for `de-en`:

- start with a small benchmark, but make it family-driven
- do not create a large random word list first

### 5. Preserve metadata/provenance early even if policy stays simple

For `en-es`, preserving provenance and Kaikki metadata gave us later room to add real additive signals.

Implication for `de-en`:

- if the source gives structure we may later want, do not throw it away
- but do not block the first milestone on building the whole future policy stack

## High-Level Goal

The real goal is:

1. `de-en` works end to end through helper, rulegen, diagnostics, and the normalized translation-pack contract
2. `de-en` has a small benchmarkable baseline
3. we only then decide which pair-specific algorithm work is worth doing

Success is not:

- “`de-en` is already fully tuned”

Success is:

- “adding `de-en` did not require a new architectural workstream”

## Phase Order

## Phase 0: Resource And Contract Preflight

Goal:

- verify the generalized seam really covers the first `de-en` use case without additional contract churn

Concrete checks:

- confirm `de-en` forward defaults resolve to `eng-deu.tei`
- confirm reverse defaults resolve to `deu-eng.tei`
- confirm diagnostics surface normalized pack ids/providers for `de-en`
- confirm helper entrypoints can carry the generic translation-pack fields without pair-specific fallback hacks

Definition of done:

- no additional provider-specific naming is required to even talk about `de-en`

## Phase 1: `de-en` Rulegen Enablement

Goal:

- add the first working `de-en` rulegen path

Concrete work:

1. add a `de-en` pair implementation file
- likely mirror the current `en_de.py` structure first
- keep the implementation intentionally simple

2. add `de-en` adapter dispatch
- helper and adapter layers should resolve it via the generalized translation-pack seam

3. wire helper/runtime entrypoints
- `run_rulegen`
- set initialization
- refresh
- runtime diagnostics

4. add focused tests
- adapter dispatch
- missing-resource error behavior
- pack-direction expectations
- helper smoke flows

Definition of done:

- `de-en` can run a basic rulegen smoke through the same generic helper pipeline as existing pairs

## Phase 2: `de-en` Baseline Benchmark Seed

Goal:

- create the smallest useful benchmark slice for `de-en`

Methodology:

- use the same benchmark structure as `en-es`
- keep the initial dataset small
- choose cases by failure-family coverage, not random lexicon sampling

Required initial coverage:

- common noun cases
- common verb cases
- at least a few polysemy cases
- at least a few likely phrase-sensitive cases
- at least a few clearly bad-top1 / forbidden-side cases

Likely first-risk families for `de-en`:

- generic or overly broad German glosses beating better everyday ones
- separable-verb / short-phrase behavior
- noun casing / source-form hygiene
- domain-vs-everyday competition
- reflexive / particle verb noise if present in the source

Definition of done:

- `de-en` has a benchmark that can reveal real policy differences
- the benchmark is still small enough to debug by hand

## Phase 3: Baseline `de-en` Quality Pass

Goal:

- improve baseline `de-en` quality only where real failures appear

Order of operations:

1. inspect raw failure cases
2. fix extraction/normalization issues first
3. then test admission settings
4. only then consider broader scoring changes

What to try first:

- admission knobs
- variant handling
- POS scoring on/off
- single-word vs narrow phrase-admission policy

What to defer:

- big scoring-weight matrices
- embeddings
- trait-conditioned routing
- multi-source agreement

Definition of done:

- `de-en` has a stable baseline that is benchmarkable and explainable

## Phase 4: Reverse-Check And Lane Maturity

Goal:

- decide whether `de-en` benefits materially from reverse support once the forward lane is stable

Concrete work:

- use `deu-eng` as the reverse lane
- compare:
  - forward only
  - forward + reverse
- only add reverse-specific tuning if the signal is clearly useful

Why not earlier:

- `en-es` showed reverse helps once the forward lane is already good enough
- reverse does not rescue a poor candidate pool

Definition of done:

- we know whether reverse support should be part of the canonical `de-en` lane

## Phase 5: Data-Source Follow-through

Goal:

- decide which next data-source investments unlock the most LP value after `de-en` is working

Current best candidate:

- German frequency workflow polish

Why:

- it helps `en-de`
- it helps `de-de`
- it is already a documented missing lane in the broader LP readiness docs

Definition of done:

- we know whether the next adjacent workstream should be:
  - German frequency,
  - deeper `de-en` tuning,
  - or another LP

## Initial `de-en` Implementation Principles

These should stay explicit during implementation:

1. Use the generalized seam directly.
- do not add new provider-specific helper field names

2. Keep the first `de-en` algorithm simple.
- mirror `en_de.py` first
- optimize only after failures are observed

3. Preserve direction clarity.
- `de-en` is distinct from `en-de`
- `eng-deu` is the forward pack for `de-en`
- `deu-eng` is the reverse pack for `de-en`

4. Keep benchmark semantics stable.
- `de-en` should fit the same benchmark artifact structure
- do not fork benchmark methodology just for this pair

5. Do not overfit from one or two words.
- use failure families before inventing pair-specific heuristics

## Validation Plan

For the first `de-en` enablement slice:

1. targeted helper/adapter tests
2. targeted `de-en` pair tests
3. docs check

Once the benchmark slice exists:

1. run the canonical benchmark for `de-en`
2. run the quality gate if/when `de-en` becomes part of the active gated set
3. run benchmark triage extraction

Current expectation:

- `de-en` should start as benchmarked-but-not-hard-gated until the dataset is large enough

## Immediate Next Step

The first concrete implementation step should be:

- Phase 1 only: make `de-en` rulegen-capable through the generalized translation-pack seam

That means:

- add the `de-en` adapter path
- add the first `de-en` pair implementation
- wire helper/runtime entrypoints
- add focused tests

Do not start with:

- a broad `de-en` sweep
- reverse-check tuning
- German frequency work
- monolingual German work

## Handoff Rule

If `de-en` enablement starts requiring another round of generic helper/resource contract churn, stop and update:

- `docs/developer/language_pair_generalization_roadmap.md`

If `de-en` is working cleanly and the next blocker is mostly resource/data quality, stop abstracting and move to:

- `de-en` benchmark seeding
- or German frequency follow-through
