# Rulegen LP Support Guide

Status: Active reference
Role: Canonical current
Purpose:
- Explain the current rulegen mechanism stack in one place.
- Make new language-pair support easier to extend without rediscovering `en-es` by code spelunking.
- Define the benchmark/probe workflow used to justify pair-level ranking changes.
Last updated: 2026-04-04
Last verified: 2026-04-04 against `core/lexishift_core/rulegen/`, `scripts/testing/`, and latest `en-de` / `en-es` benchmark artifacts
Source-of-truth: current rulegen support reference; implementation truth lives in source code and generated benchmark artifacts
Verification:
- `core/lexishift_core/rulegen/adapters.py`
- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `scripts/testing/rulegen_benchmark.py`
- `scripts/testing/rulegen_probe_words.py`
- `docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- `docs/test_outputs/rulegen_benchmark_summary_latest.md`

## Why This Doc Exists

`rule_generation_technical.md` explains the generalized pipeline and `rulegen_congruity_implementation_plan.md` records the top-3/scoring hardening history, but neither one is a clean "how do we support the next LP?" entrypoint.

This guide is the current implementation-facing map for:

1. what mechanism layers exist,
2. which ones are generic vs LP-specific,
3. how benchmark artifacts are recorded,
4. how to add pair quality machinery without mixing multiple causes at once.

## Rulegen Support Layers

Think about LP support as a ladder. New LPs should start at the bottom and add higher layers only after the lower ones are observable and benchmarked.

### 1. Shared pipeline and shared sweep surface

Current shared layers:

- Pair dispatch: `core/lexishift_core/rulegen/adapters.py`
- Candidate generation pipeline: `core/lexishift_core/rulegen/generation.py`
- Ranking utilities: `core/lexishift_core/rulegen/ranking.py`
- Benchmark runner: `scripts/testing/rulegen_benchmark.py`
- Benchmark sweep surface: `scripts/testing/rulegen_benchmark_sweep.py`
- Benchmark reporting/artifacts: `scripts/testing/rulegen_benchmark_reporting.py`
- Probe/debug seam: `scripts/testing/rulegen_probe_words.py`

These are the generic seams that every LP should use before adding pair-specific logic.

### 2. Baseline LP candidate generation

Every LP needs:

- a pair config dataclass in `core/lexishift_core/rulegen/pairs/`
- candidate source loading from the pair's dictionaries
- candidate normalization/filtering
- score signals that at least cover:
  - dictionary priority
  - dictionary-order decay (`gloss_index`)
  - optional POS match
  - optional variant penalty
  - optional phrase penalty

This is the current baseline state for `en-de`.

### 3. Pair-specific lexical hygiene

Before richer ranking work, an LP usually needs pair-specific protection against junk glosses and known learner-hostile defaults.

Current seam:

- exact phrase-level gloss overrides in `core/lexishift_core/rulegen/semantic_demotion.py`
- attached as `semantic_demotion` metadata in pair sources when `enable_exact_gloss_demotions=True`
- scaled by `semantic_demotion_scale` when the override layer is enabled

Important policy:

- canonical benchmark lanes keep exact phrase-level overrides off,
- these overrides are a long-tail escape hatch, not evidence of general ranking quality,
- generalizable ranking signals should come before expanding this list.

### 4. Pair-specific scoring and selection machinery

These are stronger LP-specific ranking layers beyond the baseline:

- definition-group interleaving / cap behavior
- late-sense competition penalties
- reverse-check scoring
- source provenance and risk-family demotions
- live policy overlays from richer source metadata
- embedding or other secondary signals

Not every LP needs every mechanism. The point is to make the mechanism inventory explicit rather than copying `en-es` wholesale.

## Current Mechanism Inventory

Use this table when evaluating a pair.

| Mechanism | Shared sweep knob exists | `en-es` | `en-de` | Notes |
|---|---|---|---|---|
| Max definitions / max rules / threshold | Yes | Yes | Yes | Baseline admission/cap layer. |
| POS scoring | Yes | Yes | Yes | Shared weight surface; pair must emit usable POS metadata. |
| Variants | Yes | Yes | Yes | Pair-specific morphology behavior still differs. |
| Exact phrase-level demotion overrides | Yes | Opt-in | Opt-in | Default-off for canonical benchmarks. |
| Reverse-check | Yes | Yes | No | `en-de` sweep exposes knobs but adapter/pair do not consume them yet. |
| Kaikki live demotion | Yes | Yes | No | `en-de` currently has no Kaikki policy layer. |
| Kaikki risk-family controls | Yes | Yes | No | Same as above. |
| Late-sense competition penalty | Yes | Yes | No | `en-es` uses this via Kaikki policy; `en-de` does not. |
| Provenance competition scoring | No generic seam | Yes | No | Currently pair-specific to richer `en-es` implementation. |
| Compiled pair resources | Partly | Yes | No | Primarily a performance/inspection advantage today. |

Important operational rule:

- A sweep knob only matters if the pair actually consumes that mechanism.
- Do not interpret low-sensitivity sweeps as "weights are done" when half the knobs are inert for the pair.

## Benchmark Artifacts: What Is Saved

The benchmark loop writes structured artifacts, not just summaries.

Default outputs:

- benchmark JSON
- benchmark Markdown summary
- benchmark HTML report
- quality gate JSON/Markdown
- triage JSON/Markdown

The benchmark JSON records:

- dataset path and dataset metadata
- exact preset/CLI sweep arguments
- objective weights
- resolved resource paths and checksums
- timing
- per-pair run list
- best-run summary
- best-run per-case results

Current schema anchors:

- case/result/summary objects: `core/lexishift_core/rulegen/benchmarking.py`
- run payloads: `scripts/testing/rulegen_benchmark_models.py`
- top-level report payload: `scripts/testing/rulegen_benchmark_reporting.py`

Important detail:

- every run is saved in the JSON artifact,
- full `case_results` are always included for `best_run`,
- full `case_results` for every run require `--include-case-results`.

Also note:

- `*_latest` artifacts are overwritten on rerun,
- dated or explicitly named artifacts should be kept when preserving historical baselines.

## Probe Artifacts: What They Answer

The probe tool is the diagnostic companion to the benchmark.

Current seam:

- `scripts/testing/rulegen_probe_words.py`

Use it to answer:

1. Is the desired answer absent entirely?
2. Is it present uncapped but ranked too low?
3. Is it dropped only after definition cap/grouping?
4. Is a bad early dictionary gloss outranking a sane learner-default answer?

That distinction is what tells you whether to change:

- the benchmark contract,
- dictionary/source choice,
- lexical demotions,
- ranking/capping logic,
- or a richer LP-specific mechanism.

## LP Bring-Up Workflow

Use this order for new or immature LPs.

### Phase A. Make the pair benchmarkable

Minimum bar:

1. adapter wiring exists,
2. baseline pair config exists,
3. LP-specific benchmark case file exists,
4. pair-scoped benchmark/gate/triage commands exist,
5. probe seam exists for that pair.

Do not start tuning until these exist.

### Phase B. Record a baseline

Freeze for one cycle:

1. current case file,
2. current resources,
3. current benchmark preset,
4. latest benchmark/gate/triage artifacts.

That baseline is the reference for later deltas.

### Phase C. Add one isolated mechanism at a time

Examples of isolated changes:

- add pair-specific lexical demotions
- add late-sense competition
- add reverse-check wiring
- swap source lane from FreeDict to Kaikki with scoring held fixed

Avoid combining:

- case edits plus ranking edits,
- source swaps plus scoring changes,
- multiple new mechanisms in one comparison pass.

### Phase D. Sweep after the pair has enough live signals

Sweeps are useful only after the pair has real mechanisms to vary.

Signs a pair is not ready for broader sweeps yet:

- sweep knobs are mostly inert for the pair,
- gate shows low sensitivity / low unique metric vectors,
- probe shows obvious junk gloss ordering problems that no current knob can fix.

In that state, add machinery first. Sweep second.

## How To Decide Whether A Case Or The System Is Wrong

Use this decision order:

1. Is the current top-1 genuinely acceptable as the learner-default answer?
2. If not, is the good answer present in uncapped results?
3. If yes, does it disappear only because of cap/grouping?
4. If the good answer is absent, is the problem source data or candidate extraction?

Only relax a benchmark case when this remains true:

> Even if I had never seen the current system output, I would still define the case this way.

If that sentence is false, change the system, not the test.

## Suggested LP Support Checklist

Use this checklist before opening a new tuning workstream.

- Pair adapter exists and uses the shared benchmark/probe harness.
- LP-local benchmark case file exists under `docs/test_inputs/rulegen_benchmark_cases/`.
- Pair-scoped latest benchmark/gate/triage artifacts exist.
- Probe support exists for the pair.
- Current resources and checksums are recorded in the benchmark artifact.
- Mechanism inventory is explicit:
  - lexical demotion
  - POS scoring
  - variants
  - cap/grouping behavior
  - reverse-check
  - richer source-policy overlays
  - embeddings/secondary signals
- The pair has at least one accepted baseline artifact set before broader sweeps.

## Current Practical Guidance For New LP Work

Use `en-es` as the richest implementation example, but not as a mandate to port everything immediately.

Recommended order:

1. get the pair benchmarkable,
2. add probe support,
3. record a baseline,
4. add lexical hygiene,
5. add one richer ranking mechanism at a time,
6. only then expand sweeps,
7. only after evidence exists, promote new defaults or update policy docs.

This keeps LP bring-up explainable, benchmarkable, and easier to resume after a break.
