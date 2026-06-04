# en-es Semantic Veto Operator Live Smoke

- Status: `ok`
- Decision: `operator_product_smoke_success`
- Pair: `en-es`
- Pack: `en-es-active-only-combined-full-v1-tranche-002`
- Runtime policy: `en_es_sentence_veto_v2`
- Product thresholds: `min_active_score=0.015`, `min_margin=0.0`
- Install surface: Chrome extension options Advanced debug, default helper data root
- Page tested: https://en.wikipedia.org/wiki/Wikipedia:Acceptable_sources

## Operator Read

The installed 135-rule active-only tranche-002 pack is accepted as a successful
product-feel smoke for the current PoC direction.

Observed behavior on the tested page focused on `acceptable`: roughly two
visible replacements and several abstains. No helper or inventory errors were
reported. The product-soft threshold is accepted as useful enough for now.

## Accepted Imperfections

- False abstains remain visible.
- Some harmful replacements are expected in this soft-assist PoC.
- Narrow source-target mappings such as `tax -> imponer` are not solved here.

## Scope

This report is not a statistical accuracy estimate and does not prove broad
source-target suitability. It only records that the installed pack, options-page
installer flow, and `0.015` active-only policy are good enough to move on from
this live-test checkpoint.
