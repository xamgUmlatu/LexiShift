# `en-es` Broad Sweep Runbook

Status: active experiment runbook
Role: Runbook / operational
Purpose: Define the staged `en-es` broad-sweep order, named presets, and artifact/output discipline for the first large PC-side sweep pass.
Last updated: 2026-03-28
Last verified: 2026-03-28

## Scope

This runbook is for the first broad `en-es` sweep family only.

It assumes:

- current benchmark dataset source: `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
- current canonical resource family: Kaikki forward + Kaikki reverse
- current benchmark engine: compiled `en-es` sweep path with warm-path caching and numeric `numpy` score projection
- current expanded benchmark case count: `64`

It does **not** redefine the canonical latest benchmark contract.
It defines experiment-stage runs that should write to experiment-specific artifact paths.

## Stage Order

### Stage 0: Canonical Replay

Goal:

- confirm the local machine still reproduces the current canonical `en-es` baseline before the larger sweep family

Expected current canonical metrics:

- objective `126.188`
- `Top1 90.62%`
- `Top3 96.88%`
- `ForbidTop1 1.56%`
- `ForbidAny 3.12%`

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

The benchmark dataset is now expanded from `57` to `64` `en-es` cases.
The added 2026-03-28 batch is:

- `canal`
- `clave`
- `gato`
- `masa`
- `señal`
- `batería`
- `llevar`

On the current canonical latest run:

- `6` of those `7` new cases pass
- the new hard fail is `batería`
- the older `acabar` and `coger` forbidden-side failures remain on the default canonical surface

Current canonical `64`-case baseline:

- objective `126.188`
- `Top1 90.62%`
- `Top3 96.88%`
- `ForbidTop1 1.56%`
- `ForbidAny 3.12%`
- exact-tie count `12`
- config `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Focused reruns on the expanded `64`-case set now show a stricter tradeoff than the earlier `57`-case frontier:

- `en_es_stage_a_admission_frontier_v2`
  - best objective `136.281`
  - exact-tie count `14`
  - best config `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
  - `Top1 90.62%`
  - `Top3 92.19%`
  - `ForbidTop1 1.56%`
  - `ForbidAny 0.00%`
  - `AvgRules 1.30`
  - experiment triage count `6`
  - interpretation:
    - fixes the lingering `acabar` / `coger` forbidden-side leakage
    - but trims recall too hard for `cuadro`, `cuenta`, `red`, and `sacar`

- `en_es_stage_a_combined_frontier_v1`
  - best objective `133.844`
  - exact-tie count `12`
  - best config `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
  - `Top1 90.62%`
  - `Top3 96.88%`
  - `ForbidTop1 1.56%`
  - `ForbidAny 0.00%`
  - `AvgRules 2.17`
  - experiment triage count `6`
  - interpretation:
    - preserves the broader top-3 surface
    - still removes `forbidden_any`
    - but does not beat the stricter admission objective

- `en_es_stage_a_reverse_frontier_v2`
  - best objective `127.438`
  - no longer competitive with the current admission-led frontier on the expanded dataset

- `en_es_stage_a_family_followup_v1`
  - best objective `126.188`
  - existing exposed family-set variants remain effectively flat on the expanded dataset

Important direct-source finding for `batería`:

- the Kaikki forward pack does contain a battery sense
- current stored translations include `large and rechargeable battery`, `drum kit, drum set`, `set (collection of things)`, and `drummer`
- current benchmark failure is therefore not a raw-source absence
- the immediate issue is that the current rulegen path is not surfacing a useful bare `battery` candidate from the longer source phrase

Current follow-up order:

1. keep the `64`-case expanded benchmark as the new baseline
2. expose a few more normalized family/category controls beyond the current `mg+gl+hft+rr+aef` set
3. rerun focused family/category and winner-neighborhood sweeps on the expanded set
4. if the plateau holds, move into targeted rulegen work for `batería`, `cuadro`, and `sacar`

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
