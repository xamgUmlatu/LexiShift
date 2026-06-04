# en-es Semantic Veto Operator Product Checkpoint

- Status: `ok`
- Decision: `operator_product_checkpoint_success`
- Pair: `en-es`
- Pack: `en-es-active-only-combined-full-v1-tranche-011`
- Runtime policy: `en_es_sentence_veto_v2`
- Product thresholds: `min_active_score=0.015`, `min_margin=0.0`
- Basis: operator accepted tranche 011 as OK after reviewing the completed final active-only follow-through summary
- Latest hands-on browser-extension smoke remains: `en-es-active-only-combined-full-v1-tranche-003`

## Operator Read

The 455-rule active-only tranche-011 pack is accepted as the current product
checkpoint for the soft-assist PoC.

This checkpoint is based on the tranche-011 follow-through artifacts: admission,
source packaging, combined pack build, isolated install, automated public-page
scan, and the exhausted active-only generation queue under the current
570-family denominator. It is not a claim that the operator repeated the same
hands-on browser smoke flow used for tranche-003.

## Automated Evidence

- Covered source-target families: `455 / 570`
- Normalized evidence rows: `922`
- Installed helper rules: `455`
- Active-only competition sets: `432`
- Shadowed or mixed competition sets: `23`
- Live-page scan review rows: `120`
- Live-page scan replaces: `68`
- Live-page scan abstains: `52`
- Fallback decisions: `0`
- Page fetch errors: `0`
- Remaining active-only generation queue rows: `0`

## Accepted Imperfections

- False abstains remain acceptable.
- Some harmful replacements are expected in this soft-assist PoC.
- This does not prove broad `en-es` language-wide accuracy.
- The remaining `115` uncovered source-target families are excluded from the
  active-only generation lane unless the denominator or review policy changes.

## Scope

This report records a product checkpoint, not a statistical accuracy estimate.
It is enough to move the current active-only generated-data lane into cleanup
and denominator discussion, while keeping hands-on browser smoke and automated
follow-through as separate evidence types.
