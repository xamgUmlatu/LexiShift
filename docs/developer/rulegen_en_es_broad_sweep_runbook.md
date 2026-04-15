# `en-es` Broad Sweep Runbook

Status: active experiment runbook
Role: practical sweep execution guide
Purpose: Define the staged `en-es` broad-sweep order, named presets, and artifact/output discipline for the first large PC-side sweep pass.
Last updated: 2026-03-29
Last verified: 2026-03-29

## Scope

This runbook is for the first broad `en-es` sweep family only.

It assumes:

- current benchmark dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
- current canonical resource family: Kaikki forward + Kaikki reverse
- current benchmark engine: compiled `en-es` sweep path with warm-path caching and numeric `numpy` score projection
- current expanded benchmark case count: `100`

It does **not** redefine the canonical latest benchmark contract.
It defines experiment-stage runs that should write to experiment-specific artifact paths.

## Stage Order

### Stage 0: Canonical Replay

Goal:

- confirm the local machine still reproduces the current canonical `en-es` baseline before the larger sweep family

Expected current canonical metrics:

- objective `131.180`
- `Top1 89.00%`
- `Top3 100.00%`
- `ForbidTop1 0.00%`
- `ForbidAny 0.00%`

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
- `en_es_stage_a_family_followup_v2`

Current scope of the expanded family surface:

- risk-family sets now support additional normalized families beyond the older `mg+gl+hft+rr+aef` bundle:
  - `art_media`
  - `communication_network`
  - `computing`
  - `mechanics_tools`
  - `music`
  - `biology`
  - `chemistry`
- sweep configs can now also carry explicit per-family demotion overrides through `--kaikki-policy-risk-family-demotion-sets`
- the current verified family-expansion smoke is `en_es_stage_a_family_followup_v2`, which runs `90` configs on the `64`-case dataset and keeps the same current top1/top3 surface while exposing the new `kfd=` config-label segment for non-default family-demotion maps

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
The current next-step order is:

1. use the now-landed `trait_summary` benchmark payload seam as the first offline profile-analysis substrate
2. harden that seam toward a shared runtime/benchmark trait contract
3. compare a small frozen profile bank on the expanded suite
4. only then revisit another suite-expansion tranche, embeddings, or other larger new signal families

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

A second dataset-expansion tranche on `2026-03-29` added:

- `carta`
- `radio`
- `cadena`
- `nota`
- `sección`
- `seña`
- `perfil`

On the current canonical latest run after the targeted `batería` extraction fix, the narrower heuristic-fragment reverse-miss follow-up, and the narrow recurrent exact reverse-attested phrasal-verb follow-up:

- `6` of those `7` new cases pass
- `batería` now passes with top1 `battery`
- `señal` is still a review case because current top-1 remains `sign` while the benchmark now prefers `signal`
- `cuadro` now recovers `picture` into top3 on the default canonical surface
- `sacar` now passes on the default canonical surface with top3 `take out, withdraw, draw`
- a fourth narrow follow-up now suppresses explicit vulgar senses when clean competition exists, which clears `acabar` and `coger` from the actionable set

Current canonical `88`-case baseline:

- objective `133.455`
- `Top1 90.91%`
- `Top3 100.00%`
- `ForbidTop1 0.00%`
- `ForbidAny 0.00%`
- `AvgRules 2.91`
- actionable triage count `8`
- config `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

All seven newly added `2026-03-29` tranche-2 cases currently pass on the canonical latest config:

- `carta` -> `letter, map, menu`
- `radio` -> `radio, radius, radium`
- `cadena` -> `chain`
- `nota` -> `note, mark, memo`
- `sección` -> `section, department`
- `seña` -> `sign, gesture, indication`
- `perfil` -> `profile`

A third dataset-expansion tranche on `2026-03-29` added:

- `archivo`
- `puerto`
- `ratón`
- `tecla`
- `trama`
- `margen`

Current canonical outcomes for those new cases are:

- `archivo` -> `archive, file`
- `puerto` -> `port, harbour`
- `ratón` -> `mouse, hangover`
- `tecla` -> `key, trigger, button`
- `trama` -> `weft, plot, weave`
- `margen` -> `margin, leeway, edge`

Interpretation:

- the new tranche is doing useful work rather than only widening easy passes
- `archivo` and `trama` are now review cases on the canonical latest config
- the other four additions pass on canonical
- the suite is now broad enough to expose the first profile-sensitive top-1 split in the frozen bank

A fourth dataset-expansion tranche on `2026-03-29` added:

- `carpeta`
- `directorio`
- `navegador`
- `celda`
- `pestaña`
- `puente`

Current canonical outcomes for those new cases are:

- `carpeta` -> `folder, cloth, desk`
- `directorio` -> `directory, directive`
- `navegador` -> `navigating, navigator, browser`
- `celda` -> `cell`
- `pestaña` -> `eyelash, flange, tab`
- `puente` -> `bridge, denture`

Interpretation:

- five of the six additions currently pass on the canonical latest config
- `navegador` is a new review case, which is useful because it exposes adjective-vs-noun competition inside a computing-marked region
- this tranche widened the review set without creating any new forbidden-side failures

A fifth dataset-expansion tranche on `2026-03-29` added:

- `móvil`
- `servidor`
- `ventana`
- `hilo`
- `portal`

Current canonical outcomes for those new cases are:

- `móvil` -> `mobile phone, mobile, motive`
- `servidor` -> `server`
- `ventana` -> `window, nostril`
- `hilo` -> `thread, linen, crosshair`
- `portal` -> `portal, porch`

Interpretation:

- all five additions now pass on the canonical latest config after the narrow nominal-compound follow-up
- `móvil` is still the most useful new pressure point:
  - canonical now keeps `mobile phone` top1
  - tighter profiles still regress to bare `mobile`
- this tranche therefore still adds useful pressure around computing / interface nouns, but it no longer contributes a canonical hard fail

The canonical latest benchmark artifact now emits a hardened analysis-only `trait_summary` payload per case.
Current `trait_summary` is split into:

- `router_input`
  - target token/length hints
  - compiled `en-es` candidate-table counts for phrase, variant, reverse-hit, late-sense, POS, and family-marker pressure
- `result_shape`
  - selected-source shape
  - variant / multiword shape
- `benchmark_only`
  - expected/forbidden label counts and match counts

Focused reruns on the expanded `64`-case set after the `batería` extraction fix and the later narrow vulgar-suppression follow-up now show a clearer split between scalar and practical frontiers:

- `en_es_stage_a_admission_frontier_v2`
  - best objective `141.594`
  - best config `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
  - `Top1 92.19%`
  - `Top3 95.31%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
  - `AvgRules 1.30`
  - experiment triage count `5`
  - interpretation:
    - strongest objective-maximizing scalar winner on the currently exposed surface
    - still trims recall meaningfully compared with the broader profiles
    - is best treated as the current precision profile, not the one universal runtime answer

- `en_es_stage_a_combined_frontier_v1`
  - best objective `139.250`
  - best config `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
  - `Top1 92.19%`
  - `Top3 100.00%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
  - `AvgRules 2.16`
  - experiment triage count `5`
  - interpretation:
    - preserves the broader top-3 surface
    - still removes `forbidden_any`
    - is the clearest current balanced profile candidate

- `en_es_stage_a_reverse_frontier_v2`
  - best objective `127.438`
  - no longer competitive with the current admission-led frontier on the expanded dataset

- `en_es_stage_a_family_followup_v1`
  - best objective `126.188`
  - existing exposed family-set variants remain effectively flat on the expanded dataset
- `en_es_stage_a_family_followup_v2`
  - now exists specifically to widen the normalized family/control surface without perturbing the scalar/admission baseline
  - full run on `2026-03-28` after the `batería` fix and later vulgar-suppression follow-up: objective `141.219`, `90` configs, triage count `5`
  - best config `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off`
  - `Top3 100.00%`
  - best run still stayed on the default family-demotion map, though non-default `kfd=...` maps remain benchmark-visible
  - interpretation:
    - the expanded family knobs are now implemented and benchmark-visible
    - this tranche says the family surface is still secondary to the admission/combined frontier
    - but it is now a credible high-objective profile candidate rather than only scaffolding

Important direct-source finding for `batería`:

- the Kaikki forward pack does contain a battery sense
- current stored translations include `large and rechargeable battery`, `drum kit, drum set`, `set (collection of things)`, and `drummer`
- the original benchmark failure was therefore not a raw-source absence
- the immediate issue was that the rulegen path was not surfacing a useful bare `battery` candidate from the longer source phrase
- the current narrow nominal-head recovery heuristic now fixes that case without broadening general multiword admission

Important direct-behavior follow-up for `cuadro`:

- the remaining art-side `picture` candidate was present after the earlier leading-alias extraction work, but it was still being penalized as a reverse miss even though it was only a heuristic gloss fragment, not a directly attested standalone dictionary headword
- the current canonical extraction baseline now suppresses reverse-miss penalties only for heuristic `leading_alias` and `nominal_head` fragments when they do not already have a direct reverse hit
- that narrower follow-up keeps ordinary comma-fragment behavior unchanged while lifting `cuadro` from hard fail to review by surfacing `square, picture, frame`

Current follow-up order:

1. keep the current expanded benchmark suite as the new baseline
2. keep the narrow `batería` head-recovery heuristic as the new extraction baseline
3. keep the narrow recurrent exact reverse-attested phrasal-verb rule as the new `sacar` baseline
4. keep the narrow vulgar-suppression rule as the new baseline for explicit vulgar leakage
5. preserve the expanded family/category sweep surface for future pair work, but do not treat it as the main remaining lever on `en-es`
6. use the new `100`-case suite as the current working baseline for profile analysis
7. use the current `trait_summary` contract to compare the frozen current profile bank:
   - canonical
   - admission-tight
   - combined-balanced
   - family-followup
8. aggregate the frozen-profile results by `router_input` trait regions rather than only by whole-profile metrics
9. only after that, revisit another suite-expansion tranche, embeddings, or other new signal families
10. keep targeted lexical-preference / ranking work for `cuadro`, `derecho`, `cuenta`, `red`, and `señal` on deck once the broader suite/profile evidence is in place

Current profile-bank interpretation:

- the current frontier is no longer just “one winner”
- the most useful current named profiles are:
  - canonical recall-oriented baseline
  - admission-tight precision profile
  - combined balanced profile
  - family-followup high-objective profile
- current evidence says those profiles mainly change:
  - rule volume
  - top-3 breadth
  - objective tradeoffs
- the first frozen profile-bank comparison on the `71`-case suite found no top-1 winner differences, the rerun on the `77`-case suite showed the first real top-1 separation, the `83`-case rerun kept that same pattern, the `94`-case rerun kept it, and the current `100`-case rerun now shows:
  - `1` top-1 winner difference across:
    - canonical
    - admission-tight
    - combined-balanced
    - family-followup
  - `0` cases with top-3 coverage differences
  - the current top-1-sensitive case is:
    - `móvil`
      - canonical: `mobile phone`
      - tighter profiles: `mobile`
- the latest trait-region aggregation on top of that frozen bank is now explicit in:
  - `docs/test_outputs/experiments/rulegen_en_es_profile_bank_analysis_20260329_100cases.json`
  - `docs/test_outputs/experiments/rulegen_en_es_profile_bank_comparison_20260329_100cases.md`
- current trait-region read:
  - `admission-tight` and `family-followup` now tie as the best objective profiles in most regions
  - canonical is now the only profile with the extra top-1 win on `móvil`
- current interpretation:
  - the frozen bank still mainly changes rule volume and objective tradeoffs
  - `móvil` is now concrete evidence that profile choice can flip top-1 on the broader suite
  - the seventh expansion tranche added `registro`, `patrón`, and `mando` as new canonical review cases without creating any new top-1-sensitive split beyond `móvil`
  - runtime routing is still premature, but it is no longer purely hypothetical
- offline profile analysis is therefore justified now, but runtime profile routing is still premature

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
