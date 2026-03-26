# Trait-Conditioned Rulegen Profiles

Status: active proposal
Role: Planning / WIP
Purpose: Define a data-driven path for choosing rulegen scoring/filtering profiles from runtime-computable word traits instead of relying on one global parameter setting or human-tagged case labels.
Last updated: 2026-03-26
Last verified: 2026-03-26
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
