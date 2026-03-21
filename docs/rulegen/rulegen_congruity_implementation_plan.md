# Rulegen Congruity Hardening: Implementation Plan

Status: Phase 0 complete; Phase 1 implemented (2026-02-19); Phase 2 groundwork implemented (2026-02-23); Phase 3 pair-level tuning resolution implemented (2026-02-23); Phase 4 benchmark harness implemented (2026-02-23); Phase 5 quality gate scaffolding implemented (2026-02-24); Phase 6 polysemy hardening options documented (2026-02-27)

Purpose:
- Record two immediate decisions for rule quality control.
- Define the first implementation phase as an architecture investigation so we place changes in the right layers.
- Provide exact file touchpoints for top-3 limiting and scoring extensions.

## Decisions (Documented, Subject To Future Revision)

1) Top-3 rule source limit per target (temporary policy)
- Decision: limit to the top 3 source candidates per target lemma.
- This is intentionally conservative and reversible.
- Important: limit is applied after normalization/filtering/scoring, not by raw dictionary order.
- Current status: implemented as top-3 dictionary-definition buckets per target.

2) Scoring framework is the long-term direction
- We will expand scoring to improve semantic congruity (for example handling glosses like `looking ...` -> `look like/seem/appear` rather than ambiguous bare forms).
- The framework should stay pair-aware and extensible by signal type, not hardcoded to one language pair.

3) Morphology scope decision (current)
- Context-free morphology stays conservative and plural-focused.
- We do not treat tense/aspect/verb-form morphology as reliable without sentence-level context.
- Context-dependent morphology is explicitly deferred as a future/stretch goal.

4) Generic gloss demotion decision (current)
- Pair-specific generic/noisy glosses may be demoted via ranking metadata (for example `semantic_demotion`) before top-K definition selection.
- Current rollout covers `en-ja`, `en-es`, `en-de`, and `es-en`, with pair defaults in `core/lexishift_core/rulegen/semantic_demotion.py`.
- Sensitivity is controlled by `semantic_demotion_scale` (pair tuning + benchmark sweep knob).

## First Implementation Step: Architecture Investigation (Phase 0)

Goal:
- Build a complete map of current rulegen flow and confirm exact insertion points for:
  - `max_definitions_per_target` (current top-3 policy)
  - new congruity scoring signals

Expected output of this phase:
- A short architecture note in this doc with verified control points.
- No behavior change yet (investigation only).

### A) Entry Points (Helper Use-Cases)

Read and trace:
- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/rulegen_job.py`
- `core/lexishift_core/helper/engine.py`

Why:
- These call `run_rulegen_for_pair(...)` and define how configs are constructed during initialize/refresh/manual rulegen.

### B) Rulegen Orchestration

Read and trace:
- `core/lexishift_core/helper/rulegen.py`

Why:
- Defines `RulegenConfig` and `run_rulegen_for_pair(...)`.
- This is the best place to introduce a new config knob such as `max_definitions_per_target`.

### C) Pair Dispatch

Read and trace:
- `core/lexishift_core/helper/lp_capabilities.py`
- `core/lexishift_core/rulegen/adapters.py`

Why:
- Confirms LP -> adapter mapping and where pair-specific configs are passed.

### D) Candidate Generation (Per Pair)

Read and trace:
- `core/lexishift_core/rulegen/pairs/en_ja.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/es_en.py`

Why:
- Source candidates (definitions/glosses/translations) are enumerated here.
- Candidate metadata such as `gloss_index`, `gloss_total`, and morphology tags are attached here.

### E) Core Pipeline + Scoring

Read and trace:
- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/rulegen/utils.py`

Why:
- Filtering, dedupe, confidence thresholding, and candidate -> `VocabRule` conversion happen here.
- Signal provider extension should be centralized here where possible.

### F) Dictionary Loaders

Read and trace:
- `core/lexishift_core/resources/dict_loaders.py`

Why:
- Ordered gloss extraction/dedup behavior is determined here.
- Needed to distinguish raw dictionary order vs post-score ranking.

### G) Runtime Consumer (Display + Identity)

Read and trace:
- `apps/chrome-extension/content/processing/replacements.js`

Why:
- Confirms canonical identity (`rule.replacement`) vs display surface (`metadata.morphology.target_surface`) behavior remains correct after scoring/limit changes.

## Planned Insertion Points (Current Best Candidate)

Top-3 limit:
- Preferred: enforce after scoring in `RuleGenerationPipeline.generate_results(...)` (`core/lexishift_core/rulegen/generation.py`) using per-target grouping.
- Config source: add `max_definitions_per_target` to `RulegenConfig` in `core/lexishift_core/helper/rulegen.py` and thread through adapters.

Scoring extensions:
- Preferred: extend `SignalProvider` and/or `RuleConfidenceSignals` in `core/lexishift_core/rulegen/generation.py`.
- Pair-specific signal producers live in pair modules (`core/lexishift_core/rulegen/pairs/*.py`) so language-specific semantics stay isolated.

## Architecture Findings (Verified 2026-02-19)

1) All operational rulegen flows converge at one orchestrator
- `core/lexishift_core/helper/use_cases/initialize_set.py` calls `run_rulegen_for_pair_fn(...)` after bootstrap and before output publish.
- `core/lexishift_core/helper/use_cases/refresh_set.py` calls `run_rulegen_for_pair_fn(...)` when refresh applies changes.
- `core/lexishift_core/helper/use_cases/rulegen_job.py` calls `run_rulegen_for_pair_fn(...)` for manual/debug rulegen.
- `core/lexishift_core/helper/engine.py` wires all three use-cases to `run_rulegen_for_pair`.
- Conclusion: `core/lexishift_core/helper/rulegen.py:run_rulegen_for_pair(...)` is the single control point for common config threading.

2) Current config and dispatch path
- `RulegenConfig` lives in `core/lexishift_core/helper/rulegen.py`.
- `run_rulegen_for_pair(...)` converts it into `RulegenAdapterRequest` and calls `run_rules_with_adapter(...)`.
- Adapter selection happens in `core/lexishift_core/rulegen/adapters.py` based on pair capability mode (`en_ja`, `en_de`, `en_es`, `es_en`).
- Phase 1 update: `max_definitions_per_target` is now threaded across `RulegenConfig`, `RulegenAdapterRequest`, pair configs, and `RuleGenerationConfig`.

3) Candidate ordering and glossary metadata
- Pair candidate sources enumerate dictionary gloss lists in source order and emit `metadata.gloss_index`/`metadata.gloss_total`.
- FreeDict-driven pairs (`en_de`, `en_es`, `es_en`) use `load_freedict_glosses_ordered(...)`.
- JA pair uses JMDict entry selection plus ordered gloss collection via `_collect_entry_glosses(...)`.
- Dictionary-loader dedupe preserves first-seen ordering in output lists.

4) Current scoring/filtering execution order
- In `core/lexishift_core/rulegen/generation.py`, `RuleGenerationPipeline.generate_results(...)` executes:
  - candidate iteration
  - dedupe key
  - filters
  - signal extraction
  - score
  - threshold gate
  - append to results
- Phase 1 update: per-target top-K now applies as top-K definition buckets, ranked by dictionary-order scoring.
- Scoring is already pair-extensible through `SimpleSignalProvider` callables and optional embedding signal.

5) Snapshot limits are reporting-only
- `max_snapshot_sources` is only used in `build_snapshot(...)` within `core/lexishift_core/helper/rulegen.py`.
- It trims preview JSON (`targets[].sources`) and does not constrain emitted/stored rules.

6) Extension-side identity vs morphology surface
- Runtime replacement display in `apps/chrome-extension/content/processing/replacements.js` uses:
  - canonical identity: `rule.replacement`
  - optional display surface: `metadata.morphology.target_surface`
- Budget/feedback keying is by canonical `rule.replacement`, preserving lemma-level SRS identity across singular/plural display forms.

## Phase 1 Wiring Targets (Implementation Next)

Top-3 limitation:
- Add `max_definitions_per_target` to:
  - `core/lexishift_core/helper/rulegen.py:RulegenConfig`
  - `core/lexishift_core/rulegen/adapters.py:RulegenAdapterRequest`
  - pair configs and `RuleGenerationConfig` as needed for thread-through
- Enforce in `core/lexishift_core/rulegen/generation.py:RuleGenerationPipeline.generate_results(...)` after scoring/threshold, grouped by `candidate.replacement`.

Scoring framework extension:
- Keep score math and signal container in `core/lexishift_core/rulegen/generation.py`.
- Add pair-specific signal producers in `core/lexishift_core/rulegen/pairs/*.py` (no pair-agnostic leakage of language heuristics).
- Maintain ordered-gloss compatibility by retaining `gloss_index` as a ranking signal.

## Investigation Checklist

- [x] Confirm all initialize/refresh/manual paths pass through the same `run_rulegen_for_pair(...)`.
- [x] Confirm where to inject `max_definitions_per_target` without changing snapshot-only limits.
- [x] Confirm that current `max_snapshot_sources` is reporting-only and does not cap rules.
- [x] Confirm current glossary ordering signal (`gloss_index` + decay) and how it interacts with confidence.
- [x] Confirm test coverage baseline for adapters and helper E2E:
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `core/tests/helper/test_helper_rulegen.py`
  - `core/tests/helper/test_helper_engine.py`
- [x] Define acceptance criteria for phase 1 implementation (top-3 + no regressions).

Acceptance criteria (phase 1):
- For each target lemma, emitted rules are capped at 3 after scoring/threshold.
- Existing snapshot controls (`max_snapshot_sources`) only affect snapshot serialization output.
- Canonical `replacement` identity remains unchanged for morphology variants.
- Existing adapter and helper tests pass; add regression tests for per-target top-K cap.

## Phase 1 (Completed)

Delivered:
- Implemented `max_definitions_per_target=3` (default on) after scoring.
- Added docs notes for this temporary/tunable limit.
- Added tests asserting cap behavior for:
  - `en-es` simple noun
  - `en-ja` reading-filtered item

## Phase 1 Implementation Notes (2026-02-19)

Implemented:
- New ranking framework file:
  - `core/lexishift_core/rulegen/ranking.py`
  - Defines `CandidateRankingMechanism` and `DictionaryEntryOrderRankingMechanism`.
- Pipeline integration:
  - `core/lexishift_core/rulegen/generation.py`
  - Adds `RuleGenerationConfig.max_definitions_per_target`.
  - Applies per-target top-K at the definition bucket level using ranking scores.
- Config threading:
  - `core/lexishift_core/helper/rulegen.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/pairs/*.py`
  - `core/lexishift_core/helper/use_cases/rulegen_job.py`
  - `core/lexishift_core/helper/engine.py`

Current scoring strategy for definition selection:
- Dictionary entry order only (earlier `gloss_index` => higher rank).
- This is intentionally simple and designed to be replaced/extended in `rulegen/ranking.py`.
- Current extension: metadata-driven semantic demotion for known generic glosses across active LP adapters (`en-ja`, `en-es`, `en-de`, `es-en`).

Current morphology strategy:
- Generic context-free inflection paths are limited to plural-focused expansion (`FORM_PLURAL`) in `en_ja` and `en_de`.
- `en-es` continues to use paired noun plural morphology with canonical target identity + surface display metadata.

## Phase 2 Groundwork (Completed 2026-02-23)

Goal:
- Make scoring and emission limits tunable for iterative experiments without entangling pair adapters.

Delivered:
- Shared scoring config model in generation core:
  - `RuleScoringConfig` (`weights` + `pos_match` sub-config)
  - `PosMatchScoringConfig` (`enabled`, exact/compatible bonus, compatibility classes)
  - file: `core/lexishift_core/rulegen/generation.py`
- Optional POS scoring provider resolver:
  - `build_optional_pos_match_provider(...)`
  - file: `core/lexishift_core/rulegen/generation.py`
- New optional per-target final rule cap:
  - `RuleGenerationConfig.max_rules_per_target`
  - enforced after definition cap in pipeline output.
- Full config thread-through (helper -> adapter -> pair pipelines):
  - `core/lexishift_core/helper/rulegen.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_ja.py`
- Rulegen job tuning inputs for CLI/native host experimentation:
  - `core/lexishift_core/helper/engine.py`
  - `core/lexishift_core/helper/use_cases/rulegen_job.py`
  - `scripts/helper/lexishift_native_host.py`
  - `scripts/helper/lexishift_helper.py`
- Probe script tuning flags added:
  - `scripts/testing/rulegen_probe_words.py`

## Phase 3 Pair-Level Tuning Resolution (Completed 2026-02-23)

Goal:
- Make tuning defaults pair-aware while keeping per-run overrides simple and explicit.

Delivered:
- New pair-level tuning registry + resolver:
  - `core/lexishift_core/rulegen/tuning.py`
  - resolution order is `pair defaults -> explicit runtime overrides`.
- Rulegen job integration uses resolved effective tuning values (instead of hard-coded global defaults):
  - `core/lexishift_core/helper/use_cases/rulegen_job.py`
- Helper-side job config now treats tuning values as optional overrides:
  - `core/lexishift_core/helper/engine.py`
- CLI/native-host now pass only explicitly requested overrides:
  - `scripts/helper/lexishift_helper.py`
  - `scripts/helper/lexishift_native_host.py`

Notes:
- Current pair defaults intentionally mirror existing behavior (no quality-policy shift yet).
- Pair-level adjustments can now be applied in one place (`rulegen/tuning.py`) without changing adapter wiring.

Default behavior:
- Preserves existing output profile:
  - `max_definitions_per_target=3` remains default.
  - `max_rules_per_target` defaults to disabled.
  - POS scoring remains enabled with prior bonus defaults.

Added tests:
- Adapter threading + total rule cap behavior:
  - `core/tests/rulegen/test_rulegen_adapters.py`
- POS scoring toggle behavior:
  - `core/tests/rulegen/test_rulegen_pos_metadata.py`
- Helper passthrough defaults:
  - `core/tests/helper/test_helper_rulegen.py`

## Phase 4 Benchmark Harness (Completed 2026-02-23)

Goal:
- Make iterative tuning measurable, repeatable, and comparable across language pairs.

Delivered:
- Benchmark evaluation core:
  - `core/lexishift_core/rulegen/benchmarking.py`
  - Computes per-case outcomes and aggregate metrics:
    - top-1 correctness
    - top-3 containment
    - forbidden top-1/any rates
    - rule density and variant rates
    - weighted objective score
- Sweep runner + leaderboard output:
  - `scripts/testing/rulegen_benchmark.py`
  - Executes parameter grids per pair and ranks runs by objective.
  - Writes JSON, Markdown, and styled HTML reports.
  - HTML dashboard now includes right-click per-source labeling (greenlist/blacklist), decisions export JSON, and LP-by-LP workflow controls (Done/Skip/Next/Prev) with resume state for faster multi-pair curation.
- Label override merge utility:
  - `scripts/testing/apply_rulegen_label_overrides.py`
  - Applies exported labeling decisions back into `docs/test_inputs/rulegen_benchmark_cases.json` (or another dataset copy).
- Starter labeled benchmark dataset:
  - `docs/test_inputs/rulegen_benchmark_cases.json`
  - Includes initial `en-es`, `en-ja`, `en-de`, and `es-en` sanity/congruity cases.
- Breadth expansion (v2):
  - `docs/test_inputs/rulegen_benchmark_cases.json` expanded to 65 labeled cases.
  - Coverage now includes broader core-lexicon checks plus hard cases (`hora`/`時`/`様` style instability guards).

Next extension path:
- Expand labeled cases per pair/domain.
- Add regression gates in CI based on benchmark score floors.

## Phase 5 Quality Gate Scaffolding (Completed 2026-02-24)

Goal:
- Convert benchmark/POS quality expectations from notes into enforceable guardrails.

Delivered:
- New policy contract file:
  - `docs/test_inputs/rulegen_quality_policy.json`
  - defines required/recommended pair coverage, dataset contract, quality floors, delta budgets, saturation thresholds, and POS guardrails.
- New baseline file:
  - `docs/test_outputs/baselines/rulegen_quality_baseline.json`
  - anchors benchmark and POS drift budgets for iterative comparisons.
- New quality gate script:
  - `scripts/testing/rulegen_quality_gate.py`
  - validates benchmark outputs, dataset coverage/tiering, delta budgets, saturation signals, and POS unknown-tag/mismatch drift.
- New triage extractor:
  - `scripts/testing/rulegen_benchmark_triage.py`
  - promotes FAIL/REVIEW benchmark outcomes into explicit follow-up artifacts.
- CI integration (artifact-policy gate):
  - `.github/workflows/ci.yml` runs `rulegen_quality_gate.py` against committed benchmark/POS artifacts.

Notes:
- Current hard-gated benchmark pair is `en-es`; other pairs remain recommended until benchmark artifact cadence is expanded.
- Saturation checks currently warn by default and can be escalated via `--strict-saturation`.

## Phase 6 Polysemy Hardening Options (Documented 2026-02-27, Planned)

Goal:
- Move beyond scalar tuning toward stronger sense-congruity signals, with precision-first behavior for SRS replacements.

Documented option set:
1) Reverse-check scoring
- Add forward/reverse consistency features to ranking (`source -> target` and reverse `target -> source` support).
- Target code touchpoints:
  - `core/lexishift_core/rulegen/pairs/*.py` (attach reverse evidence metadata)
  - `core/lexishift_core/rulegen/ranking.py` (bonus/penalty integration)
- Candidate data sources:
  - FreeDict reverse directions where available.
- Phase 1 implementation spec:
  - `docs/rulegen/reverse_check_scoring_phase1.md`

2) Sense-risk penalties
- Demote specialized/ambiguous senses using qualifier/domain/register cues.
- Target code touchpoints:
  - `core/lexishift_core/resources/dict_loaders.py` (qualifier extraction)
  - `core/lexishift_core/rulegen/pairs/*.py` (metadata)
  - `core/lexishift_core/rulegen/ranking.py` (risk penalties)
- Candidate data sources:
  - FreeDict TEI sense notes/labels, JMDict sense metadata, optional Kaikki/Wiktionary exports.

3) Translation probability + entropy features
- Compute lexical probabilities (`P(target|source)`, `P(source|target)`) and ambiguity entropy from aligned corpora.
- Store features in SQLite and feed rulegen ranking.
- Candidate data sources/tooling:
  - OPUS parallel corpora + `fast_align`.

4) Multi-source agreement bonus
- Reward candidates with corroboration across independent resources.
- Track support count/provenance in candidate metadata and ranking.

5) Runtime abstain guard
- At apply time, abstain on high-risk polysemous cases when confidence margin is weak.
- Emit reason-coded diagnostics for skipped replacements.
- Target code touchpoint:
  - `apps/chrome-extension/content/processing/replacements.js`

6) Embeddings policy (explicit)
- Keep static/contextless embedding similarity as a low-weight auxiliary signal.
- Do not treat static embedding similarity as a primary sense disambiguation mechanism.

Execution note:
- Recommended near-term order for impact:
  1) runtime abstain guard,
  2) reverse-check scoring,
  3) sense-risk penalties,
  4) multi-source agreement,
  5) translation probability/entropy integration.
