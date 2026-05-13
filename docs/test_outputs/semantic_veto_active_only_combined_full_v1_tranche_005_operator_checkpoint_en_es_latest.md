# en-es Semantic Veto Operator Product Checkpoint

- Status: `ok`
- Decision: `operator_product_checkpoint_success`
- Pair: `en-es`
- Pack: `en-es-active-only-combined-full-v1-tranche-005`
- Runtime policy: `en_es_sentence_veto_v2`
- Product thresholds: `min_active_score=0.015`, `min_margin=0.0`
- Basis: operator accepted the tranche-005 automated follow-through summary as good enough to proceed
- Latest hands-on browser-extension smoke remains: `en-es-active-only-combined-full-v1-tranche-003`

## Operator Read

The 261-rule active-only tranche-005 pack is accepted as good enough to proceed
to the next reviewed data tranche.

This checkpoint is based on the tranche-005 follow-through artifacts: repaired
admission, source packaging, combined pack build, isolated install, and
automated public-page scan. It is not a claim that the operator repeated the
same hands-on browser smoke flow used for tranche-003.

## Automated Evidence

- Covered source-target families: `261 / 570`
- Normalized evidence rows: `534`
- Installed helper rules: `261`
- Live-page scan review rows: `120`
- Live-page scan replaces: `70`
- Live-page scan abstains: `50`
- Fallback decisions: `0`
- Page fetch errors: `0`

## Accepted Imperfections

- False abstains remain acceptable.
- Some harmful replacements are expected in this soft-assist PoC.
- This does not prove broad `en-es` language-wide accuracy.
- Later paid tranches still require source-target review and no-spend planning.

## Scope

This report records a product checkpoint, not a statistical accuracy estimate.
It is enough to move the data-generation workflow forward, while keeping
hands-on browser smoke and automated follow-through as separate evidence types.
