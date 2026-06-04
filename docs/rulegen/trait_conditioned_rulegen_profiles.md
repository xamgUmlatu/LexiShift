# Trait-Conditioned Rulegen Profiles

Status: active proposal
Role: Planning / WIP
Purpose: Define a data-driven path for choosing rulegen scoring/filtering profiles from runtime-computable word traits instead of relying on one global parameter setting or human-tagged case labels.
Last updated: 2026-04-11
Last verified: 2026-04-11 planning review against current semantic-shadow and benchmark metadata surfaces
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

So the medium-term goal is:

- keep a strong global baseline,
- but also learn when different rulegen profiles are better for different trait families of targets.

## Non-Goals

This work should not become:

- manual human tagging of benchmark words as the runtime source of truth,
- arbitrary per-word memorization,
- a black-box model that is impossible to audit,
- an excuse to skip the global benchmark baseline.

The router must use only features that can be computed for arbitrary runtime targets.

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

## Automatic Feature Checklist

Rule:

- any feature we eventually use for runtime routing or profile selection must be derivable automatically for arbitrary targets
- precomputation is allowed
- benchmark-only human labels may still exist for diagnosis, but they must not become routing inputs

### A. Analysis-only labels

These are useful for slicing benchmark results and understanding failures.
They are not valid future routing inputs unless we later discover an automatic derivation path.

- [x] benchmark `tier`
- [x] benchmark expectation labels such as `expected_top1_any` vs `expected_any`
- [x] semantic-shadow slice labels already used in reports:
  - `semantic_family`
  - `trigger_shape`
  - `overlap_topology`
  - `reviewed_expectation`
- [ ] broader human labels such as:
  - `ambiguity_kind`
  - `domain`
  - `english_trigger_profile`
  - `shadow_requirement`

Implementation status:

- current benchmark files can carry manual `slice_tags` and `slice_dimensions`
- current semantic-shadow reports already aggregate several benchmark-only slice dimensions
- no benchmark-only human label is allowed to become a future runtime routing dependency by default

### B. Production-eligible automatic features already implemented somewhere

These are automatic or precomputable today, but they do not yet live in one shared canonical feature-vector surface.

- [x] active-side support
- [x] active-profile fallback support
- [x] same-POS support and cross-POS mismatch penalty
- [x] source convergence via `multi_source_candidate_support`
- [x] semantic-bridge support and bridge score
- [x] forward-neighborhood overlap score
- [x] target-frequency metadata as an optional research signal
- [x] target-vs-active frequency-similarity score as an optional research signal
- [x] failure-stage classification in semantic-shadow evaluation:
  - `seed_missing`
  - `candidate_missing`
  - `promotion_miss`

Current limitation:

- these features exist as scoring fields, diagnostics fields, or optional experiment knobs
- they are not yet emitted as one shared per-case `feature_vector`
- runtime and benchmark still do not consume them through one common extractor

### C. Production-eligible automatic features not yet implemented

These are the next feature families worth adding because they are both useful and operationally honest.

#### Target lexical structure

- [ ] target POS inventory size
- [ ] target sense count
- [ ] target gloss count
- [ ] target qualifier density
- [ ] target domain-tag density
- [ ] target multiword / orthography profile

#### Trigger-family structure

- [ ] mined trigger-family size
- [ ] mined trigger-family alias entropy
- [ ] shared-trigger degree across targets
- [ ] borrowed-seed ratio
- [ ] seed-source mix

#### Candidate-pool structure

- [x] active candidate count as a first-class emitted feature
- [x] candidate-pool size
- [x] promoted-candidate count
- [x] candidate source-family histogram
- [x] candidate POS distribution
- [ ] support-score variance
- [ ] top1-vs-top2 support margin

#### Stronger discriminative signals

- [ ] non-current-trigger alias hit count
- [ ] trigger-family reentry score
- [ ] family-diversity support score

### D. Infrastructure still missing

These are the pieces required before any serious trait-conditioned learning or profile routing can be trusted.

- [x] shared feature extractor module used by semantic-shadow benchmark analysis and future production paths
- [x] canonical per-case `feature_vector` schema
- [x] semantic-shadow experiment outputs that emit the feature vector per case
- [x] matrix and compare reports that aggregate by automatic feature buckets
- [ ] profile bank built on top of automatic features rather than benchmark-only labels
- [ ] simple interpretable selector over named profiles

Current implementation note:

- the canonical semantic-shadow feature surface now lives in `core/lexishift_core/rulegen/semantic_shadow_feature_vector.py`
- veto row results emit both raw `feature_vector` and bucketed `feature_dimensions`
- automatic feature buckets now flow into the existing veto `slice_summaries`, so compare and matrix artifacts can aggregate them without a second reporting stack

### E. Current recommendation

Do not expand benchmark JSON with many new manual tags first.

Prefer this order:

1. keep a small amount of human slice metadata for diagnosis
2. implement a shared automatic feature extractor
3. emit a canonical `feature_vector` artifact in semantic-shadow experiments
4. use those automatic features for sweeps, aggregation, and future routing

That keeps the benchmark useful without teaching the production system to depend on non-runtime information.

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

## Anti-Overfitting Rules

This feature has real overfitting risk.

Required protections:

- keep the global baseline benchmark active
- compare against a single-profile baseline
- require enough cases per trait region before drawing conclusions
- use held-out or future-added cases to verify profile-routing gains
- do not ship a router that only improves a tiny benchmark corner while hurting general behavior

## Implementation Phases

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

- a dedicated shared trait extractor
- per-case trait emission in benchmark outputs
- profile-bank definition
- routing analysis and later runtime routing

## Recommended Near-Term Next Step

Do not implement routing yet.

The next concrete step should be:

1. build the shared trait extractor
2. expose trait vectors in benchmark outputs
3. use the PC-side broad sweep to study which configurations win by feature region

That keeps the work rigorous and data-driven before policy complexity increases.
