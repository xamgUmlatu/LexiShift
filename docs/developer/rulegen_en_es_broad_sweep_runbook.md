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
