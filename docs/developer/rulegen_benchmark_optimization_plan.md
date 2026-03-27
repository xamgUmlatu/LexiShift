# Rulegen Benchmark Optimization Plan

Status: active implementation plan
Role: planning / architecture
Purpose: Define the non-throwaway optimization plan for the rulegen benchmark stack, with immediate focus on the canonical `en-es` sweep while steering toward a long-term compiled benchmark architecture that can later support vectorized CPU and optional GPU execution.
Last updated: 2026-03-28
Last verified: 2026-03-28
Source-of-truth: planning doc only; executable truth still lives in code, tests, presets, and dated benchmark artifacts.

## Scope

This document covers the benchmark/test stack rooted in:

- `scripts/testing/rulegen_benchmark.py`
- `scripts/testing/rulegen_benchmark_bundle.py`
- `scripts/testing/rulegen_quality_gate.py`
- `scripts/testing/rulegen_benchmark_triage.py`
- `core/lexishift_core/rulegen/adapters.py`
- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`

Primary target:

- accelerate the canonical `en-es` benchmark loop without changing benchmark semantics

Secondary targets:

- improve repeatability and observability of benchmark performance
- split compute from artifact materialization
- create an architecture that can later support vectorized CPU execution and optional GPU execution

Current methodology constraint:

- keep the current named preset methodology as the default benchmark surface
- do not broaden dictionary-combination search beyond the current preset unless a later planning doc explicitly changes benchmark methodology

## Current Starting Point

Current canonical `en-es` benchmark state:

- current reported case count: `57`
- current reported run count: `144`
- current best objective: `129.474`
- current best config:
  - `md=3 mr=none thr=0.000 sd=1.00 var=off pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Current canonical preset dimensions:

- `var`: `true,false`
- `pos`: `true,false`
- `rev`: `false,true`
- `xspec`: `0.0,0.1,0.2`
- `kdem`: `false,true`
- `kprov`: `0.0,0.1,0.2`

Everything else in the canonical preset is intentionally fixed.

Current benchmark objective:

- `+100 * Top1`
- `+60 * Top3`
- `-120 * ForbidTop1`
- `-80 * ForbidAny`
- `-6 * AvgRulesPerTarget`
- `-10 * VariantTop1`

Current implementation shape:

- benchmark runner supports serial or CPU-multiprocess config execution
- pair contexts now preload reusable resources before config evaluation
- `en-es` config evaluation now reuses compiled pair resources when available
- canonical `en-es` benchmark sweeps can now evaluate both `var=off` and `var=on` configs from compiled row tables, so the benchmark no longer has to fall back to the live adapter path for the variant half of the canonical matrix
- compiled `en-es` score-table construction now caches overlay demotion rows on the narrower Kaikki-policy surface instead of recomputing them for every score-weight change
- translation-pack preprocessing now has a backend-neutral persistent path-cache layer:
  - translation headwords can be reused across runs without reparsing the source pack
  - translation gloss base-form inventories can be reused across runs without rescanning the source pack
  - `en-es` reverse-headword expansion can now reuse a cached normalized alias index instead of rebuilding it from every reverse-pack headword on each benchmark run
- benchmark resource checksums now also reuse the same path-cache architecture, so unchanged pack files no longer need to be rehashed across repeated local benchmark runs
- current active `en-es` path is CPU-oriented:
  - SQLite-backed dictionaries
  - string normalization and filtering
  - POS compatibility scoring
  - reverse-check scoring
  - Kaikki provenance and family metadata
  - ranking and reduction
- current benchmark workstream now uses backend-neutral translation-pack record/loader names at the benchmark, adapter, and `en-es` compile boundary, while the underlying compatibility-loader implementation is still shared with the existing FreeDict/Kaikki resource layer
- current active `en-es` path does **not** have a real GPU-heavy embedding or neural-reranker dependency

Latest measured canonical `en-es` smoke on this PC with warm path caches:

- benchmark result still exact at objective `129.474`
- wall clock: about `0.79s`
- `build_resource_payload`: about `0.001s`
- `preload_translation_gloss_records`: about `0.21s`
- `run_config`: about `0.462s` total across `144` configs, or about `0.0032s` average per config

## Hard Requirements

These are non-negotiable:

1. no optimization may silently change benchmark semantics
2. no optimization may change the canonical preset search space unless benchmark methodology is deliberately revised
3. optimized mode must produce benchmark-equivalent outputs to the current serial engine
4. reproducibility must improve, not degrade
5. early optimization phases must not be throwaway work
6. the architecture must converge toward a better final engine, not just a faster script
7. database-specific code must stay behind pack/provider adapters; the benchmark IR and sweep backends must consume normalized pair resources rather than assuming one database technology, one schema family, or one pack per language

## Equivalence Contract

For this plan, "equivalent" means:

- same dataset interpretation
- same resolved resources
- same per-target `word_package` inputs
- same config labels
- same case-level rule ordering, unless a documented tie-normalization rule says otherwise
- same per-run summary metrics
- same benchmark objective score
- same best-run selection under stable sort rules
- same downstream quality-gate and triage conclusions for the same benchmark payload

If exact byte-for-byte artifact identity becomes impossible after refactor, the replacement must still satisfy:

- same semantic content
- stable deterministic serialization
- explicit migration note
- golden tests covering the new canonical artifact shape

## Optimization Principles

The optimization program follows these rules:

1. optimize repeated work before optimizing arithmetic
2. separate one-time compilation work from repeated sweep work
3. optimize for determinism before raw throughput
4. preserve architecture seams that enable later vectorization
5. treat CPU multiprocessing as the first acceleration tier
6. treat GPU execution as a later backend, not as a special-case rewrite

## End-State Architecture

The target architecture is a three-stage benchmark engine:

1. compile stage
2. sweep stage
3. materialization stage

### 1. Compile Stage

Purpose:

- convert dataset + resources + pair state into a frozen benchmark intermediate representation

Inputs:

- benchmark dataset
- resolved dictionary resources
- reverse dictionary resources
- pair-local `word_package` snapshot
- pair capability metadata
- canonical preset metadata

Outputs:

- benchmark IR for each pair

The IR should contain:

- target table
- case table
- candidate table
- static candidate metadata
- feature matrix or equivalent feature tables
- definition-bucket identifiers
- reverse-check raw facts
- Kaikki family and provenance facts
- label masks for expected and forbidden outcomes
- reproducibility metadata:
  - dataset hash
  - resource paths
  - resource checksums
  - preset id
  - compile version

Resource-model rule:

- pair-specific and pack-specific loaders may know how to read TEI, compatibility SQLite, native SQLite, JSONL-derived packs, embedding packs, or future backends
- that backend-specific work must terminate at a normalized pair-resource contract before the benchmark IR is built
- the compile/sweep/materialization layers must not hard-code assumptions such as:
  - SQLite-only access
  - FreeDict-only row semantics
  - one dictionary pack per language direction
  - one reverse-check source per pair
- multiple packs for the same language or pair must remain composable through the same resource abstraction, with benchmark methodology deciding which combinations are active rather than storage format leaking into the sweep engine

Design rule:

- all CPU-heavy parsing and structural normalization that does not depend on sweep weights belongs here
- database technology is an implementation detail of the resource-loading layer, not of the IR or sweep backend

### 2. Sweep Stage

Purpose:

- evaluate many configs against the compiled IR

Inputs:

- benchmark IR
- config matrix
- benchmark objective weights

Outputs:

- run summaries
- optional retained case-level details
- optional retained candidate-level diagnostics for selected runs

Backend policy:

- initial backend: cached CPU serial / multiprocess
- second backend: vectorized CPU
- later backend: optional GPU

Design rule:

- a config should be expressible as data wherever possible

### 3. Materialization Stage

Purpose:

- render benchmark JSON / markdown / HTML and downstream gate / triage surfaces from raw computed runs

Inputs:

- run summaries
- selected case-level details
- benchmark IR metadata

Outputs:

- benchmark JSON
- benchmark markdown
- benchmark HTML
- quality gate artifacts
- triage artifacts

Design rule:

- report generation must not force recomputation of benchmark runs

## Why The Early Work Is Not Throwaway

The first implementation slices must directly support the final architecture:

- resource caching becomes the compile stage's first concrete form
- config multiprocessing becomes the first sweep executor
- timing instrumentation remains useful after every future refactor
- separation of compute from reporting is required by the final architecture
- precomputed candidate inventories become the basis of the benchmark IR

Nothing in the first three phases should be discarded later. At worst, it should be moved behind cleaner interfaces.

## Phase Plan

### Phase 0: Benchmark Equivalence And Profiling

Status:

- in progress
- benchmark timing instrumentation is implemented in `scripts/testing/rulegen_benchmark.py`
- optional `--timing-json-output` is implemented
- targeted dev coverage exists for timing aggregation and render-timing propagation

Goal:

- make current performance measurable
- freeze correctness expectations before acceleration

Required work:

- add timing instrumentation to benchmark execution:
  - resource resolution
  - dictionary loading
  - candidate generation
  - scoring/ranking
  - case evaluation
  - summary generation
  - HTML/markdown rendering
- add an optional timing JSON artifact
- add golden tests for:
  - best config label
  - objective score
  - per-case summary behavior
  - triage and gate equivalence on the same benchmark payload

Acceptance criteria:

- optimized and baseline modes can be compared by timing and correctness
- there is a stable benchmark-equivalence test surface

### Phase 1: Pair-Context Caching

Status:

- in progress
- reusable `PairBenchmarkContext` is implemented
- forward/reverse translation gloss records are preloaded once per pair and threaded through the adapter seam
- per-pair `word_package` snapshots are built once and reused across configs
- benchmark preload now target-scopes the forward translation-record load for canonical pair contexts instead of loading the whole forward dictionary into grouped record objects
- benchmark preload now restores benchmark-equivalent global `gloss_base_forms` through a lightweight full-dictionary translation scan, so `en-es` inflection-artifact behavior stays identical while the heavy record load shrinks

Goal:

- eliminate repeated one-time setup work during the sweep

Required work:

- build a reusable pair benchmark context object
- preload and cache once per pair:
  - forward gloss records
  - reverse gloss records
  - reverse lookup structures
  - normalized gloss mappings
  - base-form inventories for inflection filtering
  - frozen `word_package` snapshot
- plumb preloaded structures into `en-es` rulegen instead of reloading from disk per config

Important boundary:

- this phase must not yet change scoring semantics
- this phase is a refactor around data lifetime, not policy

Acceptance criteria:

- canonical benchmark outputs remain equivalent
- repeated resource loading disappears from the per-config hot path
- the pair benchmark context can later become the seed of the benchmark IR

### Phase 2: Multiprocess Config Execution

Status:

- in progress
- `--jobs` is implemented with Windows `spawn` worker execution
- pair sweeps can evaluate configs in worker processes while preserving deterministic run ordering
- targeted dev coverage exists for parallel timing aggregation

Goal:

- exploit CPU parallelism on the canonical sweep

Required work:

- add a benchmark executor abstraction
- add `--jobs`
- evaluate configs in worker processes
- keep sorting and output deterministic
- ensure pair benchmark context is cheaply available to workers:
  - process-local rebuild if necessary
  - or serialized once and restored cheaply

Platform target:

- optimize for the current Windows workstation first:
  - Intel Core i9-14900K
  - 96 GB RAM
  - fast NVMe storage

Acceptance criteria:

- same outputs as serial mode
- materially lower wall-clock time on the canonical preset
- no nondeterministic artifact ordering

### Phase 3: Compute / Materialization Split

Status:

- in progress
- compute-only mode is implemented via `--compute-only`
- markdown/HTML materialization from an existing benchmark JSON is implemented via `--render-from-json`
- HTML timing payload now snapshots post-markdown timings before render
- `rulegen_pair_audit_cycle.py` now exercises the split explicitly by running benchmark compute first and then rendering from the saved benchmark JSON

Goal:

- make benchmark compute reusable and incremental

Required work:

- add a compute-only benchmark artifact
- make markdown/HTML generation consume raw benchmark results without rerunning rulegen
- make gate and triage consume benchmark payloads without hidden recomputation
- add cache keys based on:
  - dataset hash
  - resource checksums
  - preset id
  - compile version
  - config set

Acceptance criteria:

- HTML/markdown/gate/triage runs do not require rerunning benchmark compute
- repeated analysis work is incremental and deterministic

### Phase 4: Candidate Inventory Compilation

Status:

- in progress
- initial `en-es` compiled target layer is implemented in `core/lexishift_core/rulegen/pairs/en_es.py`
- the benchmark pair context now builds reusable `en-es` compiled resources once per pair and reuses them across configs
- current compiled layer covers static target-side dictionary facts:
  - sanitized gloss entries
  - target word-package / target POS resolution
  - dictionary POS normalization
  - canonical inventories
  - dictionary record views
  - target provenance
  - reverse lookup
  - inflection-filter base forms
- current compiled layer also prebuilds a reusable base candidate inventory for `en-es`:
  - stable per-target candidate ordering
  - static candidate metadata
  - definition-bucket identifiers
  - reverse-check raw facts
  - POS metadata
  - static semantic demotion metadata
- current compiled layer now assigns stable pair-global ids for:
  - target
  - candidate
  - definition bucket
  - Kaikki family markers
- current compiled layer now also emits a row-aligned candidate table with grouped row indexes for:
  - target id
  - definition bucket id
  - Kaikki family marker id
  - candidate id to candidate row id
- `en-es` now also has a config-driven compiled candidate score table that projects current confidence and ranking scores directly from candidate rows with parity coverage against the current scorer and ranking mechanism
- benchmark pair context now also emits a row-aligned compiled case table with:
  - stable case-row ids
  - compiled target ids
  - compiled candidate-row groups per case target
  - normalized expected / expected-top1 / forbidden phrase ids
  - a shared normalized phrase-id table for benchmark labels
- sweep evaluation now also compiles per-target rule rows and evaluates benchmark cases against the compiled case table:
  - normalized rule source rows
  - phrase-id rows aligned to the benchmark phrase table
  - selected-rule candidate-row ids recovered from preserved compiled rulegen metadata
  - compiled top1 confidence and variant flags
  - table-driven case evaluation with parity coverage against the legacy evaluator
- run summary reduction now also consumes a compiled case-result table instead of reducing Python case-result objects in the compiled path:
  - rule counts
  - top1 confidence rows
  - top1/top3/forbidden/variant boolean rows
  - objective summary parity coverage against the legacy summarizer
- compiled-resource `en-es` runs now use a compiled-fact signal provider for score inputs where available:
  - gloss index / gloss decay
  - POS canonical matching
  - variant penalty
  - phrase penalty
- compiled-resource `en-es` runs now also project config-driven candidate score rows into the runtime path:
  - compiled candidate score rows feed runtime scoring inputs through row lookups keyed by stable candidate ids
  - compiled runtime ranking scores now also cover the live Kaikki overlay path by rebuilding effective semantic demotion per candidate row from:
    - family-marker rows
    - per-target competitor-row groups
    - same-canonical competition sets
    - compiled current-sense-position rows
  - canonical `kdem=on` / `kprov>0` configs now reuse compiled ranking rows without changing the benchmark result
  - reverse-check delta and reverse-check strength are now both projected once per candidate row from shared scalar helpers and reused directly by the compiled limiter
  - reverse-hygiene anchor eligibility is now also a shared scalar helper in the live generation layer and a projected compiled row flag, so compiled reverse-definition hygiene no longer reads raw reverse-check fields directly from the candidate table
  - compiled definition limiting now reduces grouped candidate rows through a definition-group summary object that carries sorted row ids, best-row identity, reverse strength, and anchor eligibility forward, instead of recomputing per-group minima and sorts at each reduction step
  - compiled accepted-row filtering now also carries per-target dedupe groups by normalized source phrase, so the non-variant compiled runtime selects the first above-threshold row in each dedupe group directly instead of rebuilding a `seen` set over accepted row ids
  - compiled candidate score rows now also project the direct row sort key used by the compiled selector, so definition-group summaries and max-rules trimming reuse an explicit per-row ordering column instead of rebuilding sort tuples from score and filter tables
  - compiled filter rows now also project explicit definition-group ids, so definition limiting groups rows by stable integer row columns instead of reconstructing mixed tuple/string keys from candidate and filter tables at runtime
  - compiled candidate score rows now also project the full per-target ranked row order, so max-rules trimming can filter a pre-ranked target row table instead of re-sorting selected subsets in place
  - compiled definition-group summaries now also reuse that pre-ranked target row order, so grouped row ordering no longer needs to sort each definition group in place before applying reverse-definition hygiene and group flattening
  - compiled candidate score rows now also use stable numeric phrase-order ids as the final deterministic tie-breaker in row sort keys, so sweep-prep tables no longer need to carry normalized source strings purely for ordering
  - variant-expanded candidates now preserve runtime variant penalties correctly instead of inheriting only the base compiled fact flag
- compiled-resource `en-es` runs now also compile normalization/filter acceptance rows for base candidates:
  - the compiled candidate table now carries normalized source phrases as a reusable row column, so per-config filter and score builders no longer rerun phrase normalization for every candidate row
  - normalized source phrases after the current live normalizer chain
  - row-level acceptance flags for non-empty, gloss-shape, length, possessive, interjection-shadow, stopword, and inflection-artifact checks
  - accepted candidate-row groupings by target id
  - non-variant compiled `en-es` runs now consume those precomputed normalized/filter rows directly instead of rebuilding the live normalizer/filter pipeline in the hot path
- compiled `en-es` filter-table construction now also caches by filter-affecting config signature, so unrelated score or reverse-check sweeps reuse the same compiled filter rows instead of rebuilding identical acceptance tables across the canonical non-variant lanes
- compiled `en-es` score-table construction now also caches by score-affecting config signature, so canonical `var=off` and `var=on` lanes with identical ranking inputs reuse the same compiled row scores instead of recomputing them from scratch
- compiled non-variant `en-es` generation now also resolves base candidates directly from the compiled target-local row index instead of rebuilding a `compiled_candidate_id -> candidate` map on every config run
- benchmark preload now scopes both translation directions without changing canonical `en-es` results:
  - forward preload still loads only benchmark-target forward records while restoring benchmark-equivalent global `gloss_base_forms` through a lightweight full-dictionary translation scan
  - reverse preload now derives its requested headwords from the same sanitized forward gloss fragments that feed candidate generation, instead of from the unsplit raw Kaikki gloss strings
  - reverse preload also runs a lightweight raw-headword scan over the reverse dictionary so normalized demand such as `remove` can still pull raw reverse entries whose stored headword spelling differs from the candidate-normalized form
  - the canonical `en-es` smoke benchmark is back at objective `129.474` after this reverse-scoping slice, so the scoped reverse preload is now parity-safe instead of a speculative optimization
- the shared generation pipeline now preserves reverse-hygiene behavior when the ranking mechanism is a wrapper around `DictionaryEntryOrderRankingMechanism`
- the shared generation layer now also exposes reusable rule materialization and ranking-aware limiting helpers:
  - `VocabRule` materialization from a `RuleCandidate`
  - `RuleGenerationResult` materialization from a `RuleCandidate`
  - ranking-aware definition limiting, interleaving, reverse-definition hygiene, and max-rules-per-target limiting
  - these helpers are now used by both the legacy pipeline path and the compiled `en-es` fast path instead of duplicating result-shaping logic
- generated rules now preserve compiled rulegen ids in rule metadata, so selected rules can be joined back to compiled candidate rows without relying only on normalized phrase text
- non-variant compiled `en-es` generation now has a direct compiled-row result path:
  - `generate_en_es_results(...)` can bypass `build_en_es_pipeline(...)` when compiled resources and the non-variant candidate table are available
  - the fast path materializes candidates directly from compiled accepted row ids, reuses the shared generation helpers for rule materialization and result limiting, and preserves the canonical smoke result
  - dedicated parity coverage now asserts both output equivalence and pipeline bypass for this path
- the non-variant compiled `en-es` fast path now also limits compiled row ids before materialization:
  - accepted compiled rows are grouped, ranked, reverse-hygiene filtered, interleaved, and max-rule-limited directly from the compiled row tables
  - only the surviving compiled row ids are materialized into `RuleGenerationResult` objects
  - dedicated parity coverage now also asserts that compiled fast-path materialization count drops below accepted-row count when definition limiting prunes candidates
- the compiled benchmark path now also consumes flat rule sequences more directly:
  - when a compiled case table is available, benchmark evaluation builds the compiled rule table directly from the adapter’s flat `VocabRule` sequence instead of first constructing `rules_by_target` and then rebuilding compiled rows from that mapping
  - the compiled sweep path now records `group_rules` at `0.0s` in the canonical `en-es` smoke run because the regrouping pass is skipped entirely
  - dedicated benchmark dev coverage now asserts parity between the mapping-based and flat-rule compiled rule-table builders, and parity between compiled case evaluation from grouped rules vs flat rules
- the compiled benchmark path now also materializes `SweepRun.case_results` directly from compiled row tables:
  - when a compiled case table is available, benchmark evaluation builds case-result payload dicts directly from compiled case and rule rows instead of allocating `RulegenBenchmarkCaseResult` objects only to call `to_dict()`
  - the legacy object-returning evaluation path is still preserved for parity tests and non-compiled callers
  - dedicated dev coverage now asserts payload parity against `RulegenBenchmarkCaseResult.to_dict()` and verifies the compiled `_evaluate_sweep_run(...)` path no longer depends on `RulegenBenchmarkCaseResult.to_dict()`
- default sweeps can now defer case-payload materialization until after ranking:
  - when `include_case_results` is off and there is more than one config in the sweep, the benchmark now skips per-case payload dict materialization during the main sweep pass
  - after sorting, only the winning run is re-evaluated with case-payload materialization so the report payload still preserves `best_run.case_results`
  - one-config smokes still materialize case payloads during the main pass so the optimization does not add an unnecessary second run to the canonical smoke workflow
- the benchmark can now evaluate the compiled non-variant `en-es` path without going through adapter-generated `VocabRule`s:
  - the shared `en-es` adapter config builder is now reusable outside the adapter dispatch path, so benchmark evaluation and adapter execution translate `RulegenAdapterRequest` into `EnEsRulegenConfig` identically
  - compiled `en-es` resources now expose a selected-row table for non-variant runs, carrying per-target surviving candidate row ids, top1 confidence, and variant flags directly from the compiled row selector
  - when a compiled `en-es` case table is available and `include_variants=off`, `_evaluate_sweep_run(...)` now builds a compiled benchmark rule table directly from that selected-row table and skips `run_rules_with_adapter(...)` entirely
  - dedicated parity coverage now asserts both compiled-rule-table equivalence against the rule-materializing path and that the benchmark can bypass the adapter on this direct compiled path without changing case outcomes
- compiled `en-es` scoring now uses direct scalar helpers instead of generic scorer/ranking object calls inside the score-table builder:
  - confidence scores are now produced through a shared scalar helper that mirrors `RuleScorer.score(...)`
  - ranking scores are now produced through shared scalar helpers that mirror `DictionaryEntryOrderRankingMechanism.score(...)`
  - the compiled candidate score table now stores additional explicit active-ranking columns for:
    - effective semantic demotion after scale application
    - resolved reverse-check delta
  - this keeps compiled scoring benchmark-equivalent while making more of the hot path explicit row math instead of metadata-to-object reconstruction
- compiled candidate facts and score rows now align more tightly with live rulegen semantics:
  - compiled POS canonicals now resolve from the same nested-or-flat metadata surface as live candidates
  - compiled phrase penalties and ranking source phrases now use the normalized source surface rather than the raw unsanitized gloss fragment text, preventing drift such as `\"To Run\"` being scored as a phrase after live normalization would already reduce it to `run`
- translation-pack preprocessing and benchmark-resource hashing now also have a persistent path-cache layer:
  - `core/lexishift_core/resources/path_cache.py` provides a backend-neutral cache keyed by source-pack path, size, mtime, and logical metadata kind
  - translation gloss base forms, translation headwords, and benchmark resource SHA-256 checksums now reuse that cache instead of rescanning or rehashing unchanged files across repeated runs
  - `en-es` reverse-headword expansion now persists a normalized raw-alias index for the reverse pack, so warm runs no longer rebuild the alias table from every reverse headword on each benchmark invocation
- current measured timing shape on Windows after this slice with warm path caches:
  - `build_resource_payload`: about `0.001s`
  - `preload_translation_gloss_records`: about `0.21s`
  - `compile_pair_context`: about `0.08s`
  - `run_config`: about `0.462s` total / `0.0032s` average across the canonical 144-config serial sweep
  - compiled-path `group_rules`: about `0.00s`
  - end-to-end canonical 144-config serial sweep wall clock: about `0.79s`

Goal:

- convert per-config Python rulegen into compiled reusable candidate data

Required work:

- precompute the candidate universe once per pair / dataset
- assign stable ids for:
  - target
  - case
  - candidate
  - definition bucket
  - family markers
- store static candidate features such as:
  - source dict priority source id
  - gloss index / gloss order
  - phrase flag
  - variant flag
  - source/target/dictionary POS canonicals
  - reverse-check raw facts
  - Kaikki family hits
  - provenance flags
  - semantic demotion metadata
- preserve enough raw metadata for selected-run diagnostics

Important boundary:

- compile stage may move work out of the per-config loop
- compile stage must not collapse away any signal needed by current scoring and ranking semantics

Acceptance criteria:

- benchmark runs can be evaluated from compiled candidate data
- outputs remain benchmark-equivalent to the previous engine

### Phase 5: Vectorized CPU Sweep Backend

Status:

- in progress
- first batch-oriented slice is landed for canonical serial `en-es` sweeps:
  - serial benchmark execution now prebuilds compiled `en-es` requests/configs/filter tables/score tables once per sweep
  - compiled score-table projection can now batch many configs against the same compiled candidate table before the per-run evaluation loop
  - per-run compiled evaluation now reuses prepared filter/score tables instead of rebuilding them in the hot loop
  - serial sweep preparation now also prebuilds compact compiled selected-row tables, moving row selection out of the per-config `run_config` path and avoiding full normalized-source tuple materialization for every config

Goal:

- turn config evaluation into batch numeric work on the compiled candidate IR

Required work:

- express config knobs as dense arrays or structured numeric parameters
- score many configs against many candidates without Python-per-candidate loops where possible
- implement batched reductions for:
  - per-target ranking
  - top1 / top3 extraction
  - forbidden-hit tracking
  - avg-rules counts
  - objective scoring

Important boundary:

- this phase should use vectorized CPU first
- do not jump to GPU before the feature-table model is proven correct

Acceptance criteria:

- vectorized CPU backend remains equivalent to the compiled-reference backend
- benchmark throughput improves again beyond pure multiprocessing

### Phase 6: Optional GPU Sweep Backend

Status:

- planned later

Goal:

- exploit GPU only after the sweep has been converted into a genuinely GPU-shaped problem

Required work:

- implement a backend over the compiled benchmark IR using batched tensor execution
- keep CPU and GPU backends behind the same sweep interface
- restrict GPU work to parts that are truly numeric:
  - feature weighting
  - family-mask weighting
  - reverse-score refinements
  - batched reductions

Non-goal:

- do not move SQLite parsing, string cleanup, or general Python control flow onto the GPU

Acceptance criteria:

- GPU backend matches compiled-reference semantics
- GPU mode is optional and never required for correctness

## Data Model For The Benchmark IR

The benchmark IR should be explicit and versioned.

Minimum tables or equivalent structures:

- `pairs`
- `targets`
- `cases`
- `candidates`
- `definition_buckets`
- `candidate_features`
- `candidate_labels`
- `resource_manifest`
- `compile_manifest`

### Candidate Feature Groups

The IR must retain enough information to reconstruct current scoring:

- dictionary-priority group
- gloss-order / decay group
- POS group
- variant group
- phrase group
- reverse-check group:
  - exact hit
  - reverse rank
  - reverse total
  - near hit eligibility
  - miss / far-hit eligibility
- Kaikki family group
- provenance / competition group
- semantic demotion base group

### Label Groups

The IR must retain enough information to compute benchmark metrics:

- case expected-any mask
- case expected-top1 mask
- case forbidden-top1 mask
- case forbidden-any mask
- target-to-case mapping
- candidate-to-target mapping

## Config Representation

Long-term, each config should be representable as structured data:

- scalar weights
- scalar penalties
- thresholds
- booleans or masks
- family-set vectors

For the current canonical preset, the config representation must preserve these sweep dimensions:

- `include_variants`
- `pos_scoring_enabled`
- `reverse_check_enabled`
- `reverse_check_exact_hit_specificity_bonus`
- `kaikki_policy_live_demotion`
- `kaikki_policy_late_sense_penalty`

And must preserve these fixed values:

- core score weights
- reverse base weights
- `xamb=off`
- current fixed family set
- current definition/rule caps

## Validation Strategy

Every phase must be validated against a reference engine.

Reference policy:

- keep a slow but trusted path available until the compiled/vectorized backends are proven

Validation surfaces:

- unit tests for compile-stage feature extraction
- unit tests for config-to-weight translation
- golden tests for selected benchmark runs
- pair-level equivalence tests for canonical `en-es`
- gate/triage equivalence tests from the same benchmark payload

Validation metrics:

- identical best config
- identical objective score
- identical case-level `top1`/`top3`/forbidden outcomes
- deterministic run ordering

## Rollout Strategy

Rollout should be staged:

1. land profiling and equivalence coverage
2. land pair-context caching
3. land multiprocess execution behind a flag
4. make multiprocess the default once stable
5. land compute/materialization split
6. land compiled candidate IR behind a flag
7. make compiled IR the default reference engine once equivalent
8. land vectorized CPU backend
9. optionally land GPU backend

At no point should the only available engine be an unverified optimized engine.

## Risks And Mitigations

Risk:

- semantic drift during refactor

Mitigation:

- keep golden reference tests
- keep a slow reference path

Risk:

- multiprocessing introduces nondeterministic ordering

Mitigation:

- stable config ids
- stable post-merge sorting

Risk:

- compile stage drops metadata needed for later diagnostics

Mitigation:

- retain raw metadata for selected candidates and runs
- version the IR

Risk:

- GPU work is attempted too early and stalls the real optimization program

Mitigation:

- require compiled IR and vectorized CPU backend first

Risk:

- memory blowup from candidate materialization

Mitigation:

- explicit profiling
- compact categorical encoding
- optional retained-detail levels

## Definition Of Done

The benchmark optimization program is complete when all of the following are true:

- canonical preset semantics are preserved
- benchmark compute is clearly separated from artifact materialization
- pair-local resource loading is no longer repeated per config
- config evaluation scales across CPU workers
- compiled benchmark IR exists and is versioned
- vectorized CPU backend is available and benchmark-equivalent
- optional GPU backend is either implemented behind the same IR or explicitly documented as unnecessary at current scale
- developer docs and feature-state docs reflect the new architecture

## Immediate Next Slice

The next implementation slice should be:

1. move batched score projection one layer deeper into denser config/feature matrices rather than per-config Python objects
2. batch case-summary reduction over the compiled row tables, now that selected-row tables can already be prepared sweep-wide
3. keep the backend-neutral resource contract explicit so the same sweep substrate can later support multiple packs per pair and non-SQLite sources
4. only after the compiled CPU path is table-driven end to end, decide whether adding a tensor dependency for GPU is justified

Why this is the right next slice:

- the current warm-cache serial sweep is already exact and fast, so the remaining worthwhile work is architectural rather than cache churn
- the landed batch-preparation slices already moved score-table projection and selected-row selection into sweep-level preparation, and they now use compact selected-row payloads plus numeric phrase-order tie-breakers instead of carrying string sort payloads, so the next gains come from denser config/feature matrices and batched result reduction rather than more per-config caches
- it keeps CPU and future GPU work on the same compiled benchmark IR instead of creating a separate optimization path
