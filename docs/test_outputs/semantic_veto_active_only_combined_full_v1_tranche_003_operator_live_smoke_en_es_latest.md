# en-es Semantic Veto Operator Live Smoke

- Status: `ok`
- Decision: `operator_product_smoke_success`
- Pair: `en-es`
- Pack: `en-es-active-only-combined-full-v1-tranche-003`
- Runtime policy: `en_es_sentence_veto_v2`
- Product thresholds: `min_active_score=0.015`, `min_margin=0.0`
- Install surface: Chrome extension options Advanced debug, default helper data root
- Runtime context fix: split-inline DOM text now supplies surrounding sentence/block context for semantic admission
- Runtime speed fix: semantic admission batching was reported as over 2x faster before approval

## Operator Read

The installed 178-rule active-only tranche-003 pack is accepted as the current
successful product-feel smoke for the soft-assist PoC.

This approval was recorded after the runtime-context bug was fixed. In that bug,
pages such as Wikipedia could split a visible sentence into tiny inline DOM text
nodes, so the helper sometimes scored only a fragment such as `castle` instead
of the surrounding sentence. The approved runtime now gives semantic admission
usable surrounding context while keeping replacement edits local to the matched
text node.

The operator tested tranche-003 in the browser runtime after the context and
speed fixes and reported that it feels good.

## Accepted Imperfections

- False abstains remain acceptable.
- Some harmful replacements are expected in this soft-assist PoC.
- This does not prove broad `en-es` language-wide accuracy.
- New paid tranches still require source-target review and no-spend planning.

## Scope

This report is not a statistical accuracy estimate. It records that the current
tranche-003 pack, options-page installer flow, split-inline semantic context,
and `0.015` active-only policy are good enough to mark the product-smoke
checkpoint successful and move to the next reviewed data tranche when needed.
