# `en-es` Broad Sweep Runbook

Status: active experiment runbook
Role: practical sweep execution guide
Purpose: Define the staged `en-es` broad-sweep order, named presets, and artifact/output discipline for the first large PC-side sweep pass.
Last updated: 2026-03-28
Last verified: 2026-03-28

## Scope

This runbook is for the first broad `en-es` sweep family only.

It assumes:

- current benchmark dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
- current canonical resource family: Kaikki forward + Kaikki reverse
- current benchmark engine: compiled `en-es` sweep path with warm-path caching and numeric `numpy` score projection

It does **not** redefine the canonical latest benchmark contract.
It defines experiment-stage runs that should write to experiment-specific artifact paths.

## Stage Order

### Stage 0: Canonical Replay

Goal:

- confirm the local machine still reproduces the current canonical `en-es` baseline before the larger sweep family

Expected current canonical metrics:

- objective `129.474`
- `Top1 91.23%`
- `Top3 98.25%`
- `ForbidTop1 0.00%`
- `ForbidAny 3.51%`

Preset:

- `en_es_canonical_matrix`

### Stage A1: Toggle Frontier

Goal:

- widen the current toggle/policy frontier inside the fixed Kaikki/Kaikki resource lane
- determine whether `var`, `pos`, `rev`, `kdem`, `kprov`, `xamb`, and `xspec` still behave as stable winners or mostly create equivalent plateaus

Preset:

- `en_es_stage_a_toggle_frontier_v1`

### Stage A2: Admission / Cap Sweep

Goal:

- test `max_definitions_per_target`, `max_rules_per_target`, `confidence_threshold`, and `semantic_demotion_scale` with the current stable reverse/policy assumptions held fixed

Preset:

- `en_es_stage_a_admission_matrix_v1`

### Stage A3: Scoring-Weight Sweep

Goal:

- test the core rule-score weights without conflating them with major toggle flips

Preset:

- `en_es_stage_a_scoring_weight_matrix_v1`

### Stage A4: Reverse-Weight Sweep

Goal:

- test base reverse-check weight families while holding the non-reverse surface steady

Preset:

- `en_es_stage_a_reverse_weight_matrix_v1`

### Stage A5: Exact-Hit Sweep

Goal:

- test reverse exact-hit ambiguity and specificity as a focused sub-problem rather than mixing them into every earlier matrix

Preset:

- `en_es_stage_a_exact_hit_matrix_v1`

### Stage A6: Family Follow-up

Goal:

- test a small number of Kaikki risk-family sets only after the scalar/toggle frontier is understood

Preset:

- `en_es_stage_a_family_followup_v1`

### Stage A7: Admission Frontier Deepening

Goal:

- deepen the `md=2` admission winner neighborhood around the later `mr=2` result
- test whether tighter admission settings or finer threshold spacing improve the Stage A2 win

Preset:

- `en_es_stage_a_admission_frontier_v2`

### Stage A8: Reverse Frontier Deepening

Goal:

- deepen the reverse-weight winner neighborhood around match bonus, near bonus, near-rank max, miss penalty, and specificity
- determine whether the reverse gain is a broad plateau or a narrower stable region

Preset:

- `en_es_stage_a_reverse_frontier_v2`

### Stage A9: Combined Winner Neighborhood

Goal:

- combine the strongest Stage A2 and Stage A4 neighborhoods
- test whether the admission and reverse improvements stack cleanly or compete with each other

Preset:

- `en_es_stage_a_combined_frontier_v1`

### Stage B: Resource Matrix

Goal:

- compare the best few Stage A configs across resource-family lanes after the fixed-resource broad sweep is understood

This stage should not start as a giant cartesian product.
Take the best few Stage A configs first, then compare resource lanes.

Suggested lanes:

- Kaikki forward + Kaikki reverse
- Kaikki forward + FreeDict reverse
- Kaikki forward + no reverse
- FreeDict forward + FreeDict reverse

## Artifact Discipline

Do not overwrite canonical `*_latest` artifacts during broad experiments.

Use experiment-specific outputs, for example:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_toggle_frontier_v1_20260328.json`
- `docs/test_outputs/experiments/rulegen_en_es_stage_a_toggle_frontier_v1_20260328.md`
- `docs/test_outputs/experiments/rulegen_en_es_stage_a_toggle_frontier_v1_20260328.html`
- `docs/test_outputs/experiments/rulegen_en_es_stage_a_toggle_frontier_v1_20260328_timing.json`

## Minimum Reporting For Each Stage

For every stage, report at least:

- best config(s)
- exact-tie count
- near-best frontier summary
- case-level changes for:
  - `cuadro`
  - `sacar`
  - `acabar`
  - `coger`
- which knobs became stable winners
- which knobs mostly produced equivalent outcomes

## Frontier Rule

Do not report only one winning config when the objective plateau is flat.

Retain:

- all exact ties
- a small near-best frontier
- config-outcome equivalence structure where possible

## Example Command Pattern

Canonical shape:

```powershell
.\.venv\Scripts\python.exe scripts\testing\rulegen_benchmark.py `
  --preset en_es_stage_a_toggle_frontier_v1 `
  --json-output docs\test_outputs\experiments\rulegen_en_es_stage_a_toggle_frontier_v1_20260328.json `
  --markdown-output docs\test_outputs\experiments\rulegen_en_es_stage_a_toggle_frontier_v1_20260328.md `
  --html-output docs\test_outputs\experiments\rulegen_en_es_stage_a_toggle_frontier_v1_20260328.html `
  --timing-json-output docs\test_outputs\experiments\rulegen_en_es_stage_a_toggle_frontier_v1_20260328_timing.json
```

Resource-matrix example shape:

```powershell
.\.venv\Scripts\python.exe scripts\testing\rulegen_benchmark.py `
  --preset en_es_stage_a_scoring_weight_matrix_v1 `
  --translation-dict-en-es C:\path\to\forward.sqlite `
  --translation-dict-es-en C:\path\to\reverse.sqlite `
  --json-output docs\test_outputs\experiments\rulegen_en_es_resource_matrix_lane_20260328.json
```

## Current Non-Goals

Do not expand the first broad sweep to include:

- embedding-led scoring
- multi-source agreement scoring
- trait-conditioned runtime routing
- broad lexical multiword-admission policy changes

Those remain later questions.

## Current 2026-03-28 Frontier Findings

Stage A already established:

- the broad toggle/policy space is mostly a plateau
- the main actionable gains came from admission settings and reverse weights
- the next high-value work is not another giant broad sweep

Current follow-up order:

1. `en_es_stage_a_admission_frontier_v2`
2. `en_es_stage_a_reverse_frontier_v2`
3. `en_es_stage_a_combined_frontier_v1`

The combined stage is important because the Stage A2 and Stage A4 wins improved different parts of the objective surface:

- admission improved `AvgRules` and reduced `ForbidAny`
- reverse weights removed the remaining forbidden-any cases entirely

So the next question is whether those benefits stack in one frontier or whether they trade off.

Latest verified follow-up result on this PC:

- the current strongest `en-es` config is still admission-led
- `md=2`, `mr=2`, `thr=0.000`, `sd=0.50`, `var=on`, `pos=on`, `rev=on`, `kdem=on`, `kprov=0.10`
- objective `139.333`
- `Top1 91.23%`
- `Top3 98.25%`
- `ForbidAny 0.00%`
- `AvgRules 1.81`
- triage count `5`

Later follow-up interpretation:

- the reverse-frontier deepening pass did not beat the earlier reverse sweep
- the first combined winner-neighborhood pass underperformed because it was centered on the older `mr=3` admission winner
- a second combined re-check around the true `md=2` / `mr=2` frontier matched the admission-led objective but did not beat it
- the remaining plateau suggests reverse fine-tuning is mostly neutral once the tighter admission surface is in place

Current Stage B verified resource-lane conclusion on this PC:

- the full Stage B resource-family rerun has now been completed with an explicit local FreeDict `eng-spa.tei` override
- Kaikki forward + Kaikki reverse remains the best lane at objective `139.333`
- Kaikki forward + FreeDict reverse is slightly worse at objective `137.684`
  - it loses one top1 case (`hasta`: `until` -> `even`)
  - it still keeps `ForbidAny 0.00%`
- Kaikki forward + reverse disabled is clearly worse at objective `132.351`
- FreeDict forward remains non-competitive in every tested reverse lane
  - FreeDict + FreeDict reverse is slightly better than FreeDict + Kaikki reverse, but both remain far below the Kaikki-forward lane

Current local resource state:

- this PC now has a local FreeDict `eng-spa.tei` reverse pack
- this PC now also has a local `freq-es-cde.sqlite`
- installed-resource `en-es` helper diagnostics now report no missing inputs
- a no-persist helper `run_rulegen` smoke now succeeds locally for `en-es`
- there is no longer a resource-availability blocker for the current `en-es` benchmark/resource matrix on this PC
