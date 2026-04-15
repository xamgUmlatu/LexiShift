# `en-es` Dataset Expansion Tranche 6

- Date: `2026-03-29`
- Benchmark baseline artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)

## Added Cases

- `enlace`
- `pantalla`
- `sitio`
- `aplicación`
- `mensaje`
- `nodo`

## Canonical Outcomes

- `enlace` -> `link, bond, connection`
- `pantalla` -> `screen, lampshade, earring`
- `sitio` -> `site, siege, ranch`
- `aplicación` -> `application, use`
- `mensaje` -> `message, speech`
- `nodo` -> `node`

## Canonical Summary

- case count: `94`
- objective: `134.064`
- `Top1`: `91.49%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.90`

## Interpretation

- All six additions currently pass on the canonical latest config.
- This tranche mostly strengthened the baseline rather than surfacing new triage.
- The new cases still add useful coverage in the computing/network region:
  - `enlace` pressures link-vs-relationship competition.
  - `pantalla` pressures interface-vs-object drift.
  - `sitio` pressures site-vs-place-vs-siege competition.
  - `aplicación`, `mensaje`, and `nodo` extend cleaner reference nouns without introducing noise.
- Because this tranche did not add new actionable cases, the next most useful suite-growth step should probably be another harder pressure tranche rather than more easy-smoke coverage in the same region.
