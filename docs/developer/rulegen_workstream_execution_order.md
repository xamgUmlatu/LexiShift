# Rulegen Workstream Execution Order

Status: active plan
Role: Planning / WIP
Purpose: Record the explicit recommended order of work for the current rulegen quality workstream, with emphasis on `en-es` Kaikki quality, benchmark methodology, portability, and later adaptive profile work.
Last updated: 2026-03-26
Last verified: 2026-03-26
Source-of-truth: planning doc only; current executable truth still lives in code, tests, benchmark artifacts, and `docs/developer/feature_state_matrix.md`.

## Scope

This doc is the ordered execution plan for the current rulegen quality workstream.

It is meant to answer:

1. what to do now,
2. what to do during the PC sweep,
3. what to do immediately after the sweep,
4. what is explicitly deferred.

Current focus:

- Kaikki-backed `en-es` rulegen quality
- benchmark methodology and reproducibility
- controlled extension of scoring/filtering architecture
- later trait-conditioned routing work

## Current Starting Point

Current canonical `en-es` benchmark:

- `Top1`: `89.58%`
- `Top3`: `97.92%`
- `ForbidTop1`: `0.00%`
- best config:
  - `md=3 mr=none thr=0.000 sd=1.00 var=off pos=on rev=on xamb=off w_pos=0.100 kdem=off kfam=mg+gl+hft+rr+aef`

Current remaining triage targets:

- `derecho`
- `cuadro`
- `cuenta`
- `red`
- `sacar`

Current infrastructure already in place:

- Kaikki forward and reverse dictionary pipeline
- benchmark/gate/triage loop
- named benchmark presets
- portable benchmark bundle export/replay
- Kaikki provenance and marker-family scaffolding
- reverse ambiguity signal
- first Kaikki live-demotion scaffolding
- trait-conditioned profile feature now documented as a planned later phase

## Ordering Principles

These are the rules for sequencing the work:

1. fix missing signal before tuning weight around it
2. fix reproducibility before large compute
3. prefer architectural seams before policy complexity
4. expand dataset before trusting fine-grained optimization
5. keep benchmark methodology stable while exploratory sweeps happen elsewhere
6. separate lexical traits from learner-stage/context decisions

## Phase 0: Freeze And Reproduce

Status:

- completed enough to proceed

Goal:

- make broad sweeps reproducible and portable

Completed items:

- pair-local benchmark resources
- resource checksums
- frozen `word_package` snapshots
- named benchmark presets
- portable bundle export/replay
- PC handoff runbook

Why this phase had to come first:

- broad compute on a non-reproducible setup is low value
- future result comparisons need frozen resource/input state

Remaining ergonomic only item:

- optional single-file archive/import support

This is explicitly **not** blocking the next phases.

## Phase 1: Finish The Current `en-es` Algorithmic Frontier

Status:

- active
- highest short-term value

Goal:

- reduce the remaining `en-es` misses before broader global tuning dominates the workstream

### Phase 1A. `cuadro`

Priority:

- highest algorithmic priority

Reason:

- it is the only clearly hard remaining miss in the canonical lane

Current problem:

- geometry-like senses still dominate:
  - `square`
  - `rectangle`
  - `frame`

Likely needed:

- better lexical-sense competition
- stronger pedagogical handling of ambiguous exact reverse hits
- more use of Kaikki sense/domain metadata for broad-vs-niche competition

What not to do first:

- do not assume reverse ambiguity penalty alone will solve it
- do not treat it as a benchmark-label issue

### Phase 1B. `sacar`

Priority:

- high, but after `cuadro`

Reason:

- it is more of a phrase-policy gap than a general ranking failure

Current problem:

- good short phrasal-verb candidates are not admitted cleanly enough
- current best top1 like `withdraw` is narrow and pedagogically suboptimal

Likely needed:

- targeted short lexical phrase admission
- probably 2-word phrasal-verb handling
- likely paired with reverse support and phrase penalties

What not to do first:

- do not simply turn on global multiword admission

### Phase 1C. `cuenta`, `red`, `derecho`

Priority:

- medium

Reason:

- these are closer to ranking/preference/review questions than structural pipeline failures

Likely needed:

- benchmark-label review where warranted
- mild ranking adjustments
- maybe stronger lexical competition or domain-family handling

What not to do first:

- do not overfit the whole system around these cases before `cuadro` and phrase policy are improved

## Phase 2: Expand The Benchmark Dataset

Status:

- not optional
- should happen before trusting large parameter spaces

Goal:

- make future sweeps more informative and less brittle

Add cases for:

- lexical polysemy:
  - more `cuadro`-like cases
  - more `cuenta`-like cases
  - more `red`-like cases
- short verb phrases:
  - more `sacar`-like cases
- technical/domain competition:
  - broad everyday sense vs legal/government/math/etc.
- review-boundary cases:
  - cases where multiple top1s may be pedagogically acceptable

Why this phase is before the broad sweep:

- current dataset is strong enough for directional experiments
- current dataset is still too small/coarse for confident high-dimensional tuning

## Phase 3: Run The Broad PC Sweep

Status:

- ready once Phase 1 and enough of Phase 2 are complete

Goal:

- search the larger currently-exposed parameter space on frozen inputs

Use:

- the portable bundle
- named preset methodologies
- non-canonical PC-side output paths

Current exposed dimensions worth sweeping:

- reverse on/off and reverse weights
- exact-hit ambiguity values
- Kaikki live demotion on/off and family sets
- POS scoring weights
- semantic demotion scale
- definition caps
- rule caps
- variant inclusion
- score weights

What this phase is for:

- finding the best current global settings
- identifying interactions between already-live signals

What this phase is not for:

- solving missing-signal problems like phrase admission by brute-force weight search

## Phase 4: Expose The Next Hidden But Real Knobs

Status:

- do after the first broad sweep, unless Phase 1 specifically forces one sooner

Goal:

- expand the truly usable search/design space with knobs that already exist or are very near-complete

Most important candidates:

1. expose `allow_multiword_glosses` to the benchmark harness
2. expose richer Kaikki live-demotion controls:
   - per-family strengths
   - competition-scope controls
3. expose or formalize gloss-decay behavior if it proves important
4. decide whether to expose filter toggles for:
   - stopword filter
   - length filter
   - inflection filter

Why not first:

- each exposed knob expands the search space
- it is better to understand current active dimensions before multiplying them further

## Phase 5: Hook Up Missing Signals

Status:

- after current global sweep and the next exposed-knob pass

Goal:

- add new sources of evidence that current tuning cannot substitute for

Highest-value missing signals:

### 5A. Multi-source agreement bonus

Why:

- one of the strongest still-missing ranking signals
- especially valuable when multiple resources corroborate a candidate

Current status:

- documented/planned
- not implemented

### 5B. Embeddings-based scoring

Why:

- currently benchmark-exposed as a weight but effectively inert for `en-es`

Current status:

- architecture/docs mention it
- no meaningful `en-es` embedding signal is active in current rulegen

### 5C. Runtime apply-time polysemy safeguards

Why:

- some bad replacements are better suppressed at application time than “solved” fully upstream

Current status:

- planned only

### 5D. Better lexical phrase policy

Why:

- still the real fix path for `sacar` and similar cases

Current status:

- only grammatical/function-word phrase exceptions are mature

## Phase 6: Trait Extraction And Offline Profile Analysis

Status:

- do only after the global baseline and missing-signal work are in better shape

Goal:

- move from one global optimum toward data-driven profile selection by runtime-computable traits

This phase should include:

1. shared trait extractor
2. per-case trait emission in benchmark artifacts
3. small named profile bank
4. offline analysis of which profiles win by feature region

This phase should not yet include:

- live runtime routing
- arbitrary per-word weight selection

Why this is later:

- otherwise we risk building adaptive logic on top of a still-underpowered signal set

## Phase 7: Runtime Profile Routing

Status:

- later

Goal:

- choose among a small number of named profiles using runtime-computable traits plus explicit learner/context signals

This phase should require:

- strong offline evidence
- interpretable router
- global-baseline comparison
- holdout validation or future-case verification

This phase must keep separate:

- lexical traits
- learner-stage/context settings

## Explicitly Deferred Work

These are real ideas, but they are not on the immediate critical path.

### Deferred but likely

- Kaikki synonym extraction/runtime wiring
- generic multi-pair Kaikki pack generation
- optional single-file bundle archive/import ergonomics

### Deferred until later product-policy decisions

- admission-side filtering of grammar-heavy targets
- stronger learner-stage-specific behavior

### Deferred because current foundation is not ready

- black-box per-word or opaque model-based routing
- unconstrained runtime profile explosion

## Things We Should Not Confuse

These distinctions matter:

- `cuadro` is an algorithmic miss
- `sacar` is mostly a phrase-policy gap
- `derecho`, `cuenta`, and `red` are closer to ranking/preference questions
- embeddings weight is exposed, but embeddings are not meaningfully active for `en-es`
- Kaikki demotion is scaffolded, but the best current run still keeps it off
- reverse ambiguity is real and implemented, but it is not the main next unlock by itself

## Recommended Concrete Order

If we follow one explicit path, it should be:

1. finish `cuadro`
2. design and test narrow lexical phrase admission for `sacar`
3. expand the benchmark dataset around polysemy and short phrases
4. run the broad PC sweep on frozen bundle inputs
5. review sweep winners and expose the next most valuable hidden knobs
6. implement multi-source agreement
7. decide whether embeddings are worth wiring next
8. build the shared trait extractor
9. emit per-case trait vectors
10. define a small profile bank
11. do offline trait-conditioned profile analysis
12. only then consider runtime profile routing

## Operational Rule

When in doubt:

- prefer improving objective signal and reproducible measurement before adding adaptive complexity

That is the main ordering principle of this whole workstream.
