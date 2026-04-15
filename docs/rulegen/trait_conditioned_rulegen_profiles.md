# Trait-Conditioned Rulegen Profiles

Status: active proposal
Role: Planning / WIP
Purpose: Define a data-driven path for choosing rulegen scoring/filtering profiles from runtime-computable word traits instead of relying on one global parameter setting or human-tagged case labels.
Last updated: 2026-03-29
Last verified: 2026-03-29
Source-of-truth: planning doc only; current executable truth still lives in code, benchmark artifacts, and the feature-state ledger.

## Motivation

The current benchmark architecture is good at finding the best global average configuration.

That is useful, but it assumes one configuration should win for all target words.

The recent `en-es` Kaikki work already suggests that is not true:

- function-word-adjacent cases wanted special filtering behavior:
  - `ese`
  - `hasta`
  - `según`
- phrase-sensitive lexical verbs want different candidate admission behavior:
  - `sacar`
- highly polysemous nouns want stronger lexical competition logic:
  - `cuadro`
  - `cuenta`
  - `red`
- beginner-facing pedagogy and advanced technical vocabulary may rationally prefer different aggressiveness on:
  - domain-sense demotion
  - slang/register suppression
  - lexical multiword admission

Related cross-cutting model:

- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`

So the medium-term goal is:

- keep a strong global baseline,
- but also learn when different rulegen profiles are better for different trait families of targets.

## Current Readiness

This direction is now concrete enough to plan seriously, but not mature enough to ship.

Current `en-es` evidence after the expanded `100`-case benchmark and the latest frozen-profile reruns:

- a practical profile bank already exists on the current benchmark surface:
  - canonical recall-oriented baseline
  - admission-tight precision profile
  - combined balanced profile
  - family-followup high-objective profile
- those profiles now differ clearly on:
  - rule volume
  - top-3 breadth
  - objective tradeoffs
- they do **not** yet consistently flip the remaining stubborn review winners:
  - `derecho`
  - `cuadro`
  - `cuenta`
  - `red`
  - `señal`
  - `archivo`
  - `trama`
  - `navegador`
  - `registro`
  - `patrón`
  - `mando`

Current conclusion:

- it is now appropriate to start offline trait/profile analysis
- it is still too early to ship runtime profile routing
- the first hardened benchmark-side trait contract is now landed on the broader suite
- the emitted `trait_summary` is now split into:
  - `router_input`
  - `result_shape`
  - `benchmark_only`
- the first frozen profile-bank comparison on the `71`-case suite found no top-1 winner differences, the rerun on the `77`-case suite was the first real split, the `83`-case suite kept that pattern, the `94`-case suite kept that shape, and the current `100`-case suite still keeps it:
  - `1` top-1 winner difference across:
    - canonical
    - admission-tight
    - combined-balanced
    - family-followup
  - now `0` cases with top-3 coverage differences
  - the current top-1-sensitive case is `móvil`:
    - canonical top1: `mobile phone`
    - tighter profiles top1: `mobile`
  - the current profile bank still mostly changes rule volume and objective, but it is no longer true that it never changes top-1 identity
- the first trait-region aggregation on top of that frozen bank is also now complete:
  - `admission-tight` and `family-followup` currently tie as the best objective profiles in most regions
  - canonical is currently the only profile with the extra top-1 win on `móvil`
  - those region-level wins are still mostly about recall breadth and rule volume, not a broad routing-ready pattern
- the next required move is targeted suite growth and repeated profile-bank analysis on those separating regions, not immediate embedding-led scoring
- the current `móvil` split is exactly the kind of evidence we want more of before any runtime routing proposal
- the latest suite tranche widened the review-only ranking surface with `registro`, `patrón`, and `mando`, but still did not create a second top-1-sensitive profile split

## Non-Goals

This work should not become:

- manual human tagging of benchmark words as the runtime source of truth,
- arbitrary per-word memorization,
- a black-box model that is impossible to audit,
- an excuse to skip the global benchmark baseline.

The router must use only features that can be computed for arbitrary runtime targets.

## Difficulty And Proficiency Must Stay Separate

This routing work touches difficulty, but it should not overload the term.

Keep these distinct:

- lexical / rulegen difficulty:
  - how ambiguous, phrase-sensitive, or noisy a target is
- learner-facing vocabulary difficulty:
  - how suitable that word is for a learner at a given stage
- user proficiency:
  - external context such as self-report, placement, or known-lemma coverage
- observed SRS difficulty:
  - how hard that item has proven to be after exposure

Important rule:

- rulegen routing should primarily learn from lexical/rulegen-side features
- user proficiency is an allowed external context input
- user proficiency must not be inferred from the target word alone

That is the same separation described in:

- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`

## Core Decision

The system should use **runtime-computable trait vectors**, not human-assigned labels.

That means:

- offline analysis may still use human interpretation to understand results,
- but runtime policy choice must depend only on features derivable from the target word, its candidate set, and the active resources/configuration.

This is required because the production system must make the same decision for:

- benchmark words,
- newly admitted SRS words,
- arbitrary future targets not seen during tuning.

## High-Level Architecture

The intended architecture is:

1. trait extractor
- deterministic feature extraction from runtime-available signals

2. profile bank
- a small number of named rulegen profiles

3. benchmark analysis
- run profiles across the benchmark suite
- record per-case outcomes with feature vectors

4. router training / design
- learn which profile wins for which feature regions
- start with simple interpretable routing

5. runtime profile selection
- compute the same feature vector online
- choose the profile before final scoring/filtering/ranking

## Preferred Group-Discovery Method

Do not start by inventing a rigid tag system like:

- beginner-safe
- technical
- phrase-heavy

Those labels are useful for discussion, but they should not be the routing source of truth.

Preferred discovery flow:

1. freeze a small profile bank
2. emit runtime-computable trait vectors per case
3. compute per-profile reward per case
4. fit a shallow policy tree or equivalent interpretable router

Why:

- it discovers useful groups after the fact
- it chooses group boundaries from outcomes, not intuition
- it gives a compact and auditable answer to:
  - "which profile should this kind of word use?"

Good complementary methods:

- outcome-space clustering followed by a simple explainer
- subgroup discovery / compact rule lists

Methods to avoid first:

- plain clustering on words alone
- opaque neural routing
- large hand-maintained tag taxonomies

## Shared Trait Extractor

The benchmark and runtime must use the same trait extraction code.

It should live in a reusable module rather than in benchmark-only scripts.

First expected trait families:

### 1. Target-side lexical traits

- normalized POS
- POS family:
  - noun
  - verb
  - adjective
  - adverb
  - determiner/pronoun/preposition/conjunction/particle
- morphology or script hints from `word_package`
- frequency rank / percentile when available

### 2. Candidate-set shape traits

- candidate count
- surviving definition count
- top-1 vs top-2 score gap
- reverse-hit count / reverse ambiguity
- reverse exact-hit specificity / fanout
- multiword-candidate dependence
- phrase-heavy candidate set
- proportion of candidates that were variants

### 3. Dictionary-structure traits

- sense count
- raw gloss count
- gloss-list structure:
  - semicolon-heavy
  - comma-list heavy
  - parenthetical heavy
  - phrase-heavy
- later-sense survival patterns

### 4. Metadata traits

- Kaikki marker families:
  - register/region
  - government/law
  - math/geometry
  - hunting/fishing/tools
  - abbreviation/ellipsis/form-of
- multi-source agreement or disagreement
- source-side lexical frequency and source-target frequency-gap signals when those are live
- translation-box metadata richness

### 5. Runtime-context traits

These should stay separate from lexical traits:

- learner stage / curriculum mode
- pair objective or profile context
- future content-mode settings such as:
  - beginner
  - core vocabulary
  - advanced technical

Important rule:

- do not infer learner stage from the word itself
- learner stage is an external control input, not a lexical property

When later SRS/product context exists, likely external inputs include:

- estimated proficiency band
- target challenge center/spread
- optional target vocabulary label
- content mode such as:
  - core vocabulary
  - balanced
  - advanced / technical

## Profile Bank

Do not jump directly to arbitrary per-word weights.

Start with a small number of named profiles.

Illustrative examples:

- `baseline`
- `function_word_sensitive`
- `phrase_friendly`
- `technical_tolerant`
- `beginner_bias`

Each profile can differ in:

- weight sets
- filter toggles
- phrase-admission policy
- sense-risk demotion strength
- reverse-check weighting
- source-frequency / frequency-gap weighting
- agreement weighting
- future resource gating decisions

The goal is a small profile bank with strong evidence, not unconstrained combinatorics at runtime.

## Benchmark And Analysis Changes

Before runtime routing exists, use this architecture analytically.

Needed benchmark additions:

1. emit trait vectors per case
- each benchmark case result should carry the extracted runtime-computable trait summary

2. preserve profile identity
- when a run is executed under a named profile or preset, keep that profile name explicit in artifacts

3. support case-by-case winner analysis
- compare which profiles win on which trait regions

4. support aggregated trait reports
- for example:
  - which profiles win on high-ambiguity nouns
  - which profiles win on phrase-dependent verbs
  - which profiles win on domain-marked technical terms

The first use of this system should be:

- offline analysis and experiment design,
- not immediate runtime routing.

## Router Design

The first router should be simple and inspectable.

Preferred early forms:

- decision tree
- compact ruleset
- shallow linear/logistic classifier

Avoid first:

- opaque neural routing
- per-word lookup tables
- large cascading heuristics with no benchmark visibility

The router output should initially choose among a few named profiles, not generate arbitrary weights.

## Why Human Tags Are Not Enough

Human review labels are still useful for diagnosis, but they are not sufficient for runtime routing.

Reasons:

- they do not scale to arbitrary future targets
- they are subjective
- they do not exist at runtime
- they tempt the system toward benchmark memorization

Human analysis should therefore be used to:

- design better runtime-computable features,
- interpret failures,
- decide whether a new profile is pedagogically valid.

## Beginner vs Technical Mode

This feature is especially promising for learner-stage-aware policy.

Likely beginner-oriented profile behavior:

- stronger slang/register suppression
- stronger technical/domain demotion
- stricter phrase admission
- preference for broader everyday senses

Likely advanced-oriented profile behavior:

- weaker technical/domain demotion
- more tolerance for specialized vocabulary
- more willingness to keep precise multiword lexical cues
- more tolerance for rare but accurate source phrases

This should be routed by:

- lexical traits
- plus explicit learner-stage/context input

It should not be routed by:

- hidden assumptions from the word alone

This is intentionally compatible with the later SRS onboarding problem:

- a learner may start the SRS journey at an intermediate band
- that choice is separate from lexical ambiguity
- but both can feed the same eventual routing/planning stack as distinct inputs

## Anti-Overfitting Rules

This feature has real overfitting risk.

Required protections:

- keep the global baseline benchmark active
- compare against a single-profile baseline
- require enough cases per trait region before drawing conclusions
- use held-out or future-added cases to verify profile-routing gains
- do not ship a router that only improves a tiny benchmark corner while hurting general behavior

## Implementation Phases

### Phase 0. Benchmark Expansion

- expand the benchmark suite again before learning routed policy
- add more cases for the current remaining pressure types:
  - broad-vs-niche polysemy
  - lexical preference / ranking boundaries
  - phrase-sensitive verbs
  - domain competition
- use the broader suite to reduce overfitting risk before profile-learning claims

Current checkpoint:

- two explicit `en-es` benchmark-expansion tranches are now complete
- the current suite is `88` cases
- the latest tranche increased breadth without widening the actionable review set
- benchmark `case_results` payloads now emit a first `trait_summary` seam for offline analysis
- that is enough evidence to move the immediate next step from more blind expansion to hardening and using the trait/profile instrumentation

### Phase 1. Feature Extraction Architecture

- create a shared trait extractor module
- make it callable from both benchmark and runtime
- keep raw and normalized traits available
- do not change runtime behavior yet

### Phase 2. Benchmark Trait Emission

- emit per-case trait vectors into benchmark artifacts
- add summary tooling for trait-region wins and regressions
- keep scoring behavior unchanged

### Phase 3. Profile Bank

- define a small set of named profiles
- map profiles to existing rulegen knobs
- keep profiles explicit and benchmarkable
- first planned profile bank:
  - canonical
  - admission-tight
  - combined-balanced
  - family-followup

### Phase 4. Offline Routing Analysis

- determine which profiles help which feature regions
- start with interpretable routing logic
- do not ship runtime routing yet

### Phase 5. Runtime Routing

- compute the same feature vector online
- choose among named profiles before final rule generation
- keep routing explainable in diagnostics

## Early Candidate Signals Already Available

This direction is feasible because much of the needed raw signal is already present or partially wired:

- candidate provenance in `en_es.py`
- normalized Kaikki marker families in `kaikki_views.py`
- reverse ambiguity signals in `ranking.py`
- frozen benchmark inputs and portable replay in the benchmark/bundle tooling
- named benchmark methodologies in the preset system

So the main missing parts are:

- broader runtime reuse of the new shared trait extractor
- per-case aggregated trait analysis/reporting
- profile-bank definition
- routing analysis and later runtime routing

## Recommended Near-Term Next Step

Do not implement routing yet.

The next concrete step should be:

1. use the first trait-region aggregation as evidence that profile choice is presently changing recall breadth and rule volume more than top-1 winners
2. expand the suite further in the regions that are currently separating profile averages:
   - dense multi-bucket nouns
   - communication/network competition
   - math/geometry and mechanics/tool competition
3. only after that, revisit another suite-expansion tranche, embeddings, or other new signal families in the profile-analysis loop

That keeps the work rigorous and data-driven before policy complexity increases.
