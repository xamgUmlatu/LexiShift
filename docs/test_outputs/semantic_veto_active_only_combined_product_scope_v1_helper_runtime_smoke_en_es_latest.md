# en-es Semantic Veto Active-Only Helper Runtime Smoke

- Status: `ok`
- Decision: `manual_testing_ready`
- Generated: `2026-05-09T22:54:33Z`
- Fixture data root: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root`
- Profile: `default`
- Decision policy: `en_es_sentence_veto_v2`
- Fallback policy: `abstain_on_unavailable`

## Publication Family

- Ruleset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root/srs/profiles/default/srs_ruleset_en-es.json`
- Snapshot: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`
- Semantic inventory: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`
- Manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`

## Runtime Smoke Metrics

- Rules: `49`
- Families: `49`
- Cases: `189`
- Active-only competition sets: `26`
- Shadowed competition sets: `23`
- Policy decisions: `189`
- Fallback decisions: `0`
- Decision accuracy on repaired-full smoke denominator: `0.7249`
- Replace recall: `0.4898`
- Harmful replaces: `2`
- False abstains: `50`

## Manual Test Notes

- The fixture data root is isolated; point LEXISHIFT_DATA_DIR at it for manual helper/app tests.
- With no explicit override, active-only fixture inventories auto-select en_es_sentence_veto_v2.
- The production default en_es_sentence_veto_v3 still requires sentence_transformers/model availability.
- Expected user-facing outcome remains binary: replace or abstain.

Use this environment override for manual helper/app smoke tests:

```bash
export LEXISHIFT_DATA_DIR='/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-product-scope-v1-helper-runtime-smoke-data-root'
```

## Sample Decisions

| Case | Gold | Decision | Source | Active | Shadow | Margin | Sentence |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `en-es:full-family-repaired-full:break:quebrar:001` | `replace` | `abstain` | `policy` | 0.0160 | 0.0000 | 0.0160 | The old plate began to break along the rim. |
| `en-es:full-family-repaired-full:break:quebrar:002` | `replace` | `replace` | `policy` | 0.1226 | 0.0127 | 0.1099 | A dry branch can break under sudden pressure. |
| `en-es:full-family-repaired-full:break:quebrar:003` | `abstain` | `abstain` | `policy` | 0.0325 | 0.0121 | 0.0204 | A news alert can break the broadcast without warning. |
| `en-es:full-family-repaired-full:break:quebrar:004` | `abstain` | `abstain` | `policy` | 0.0072 | 0.0683 | -0.0611 | Her internship became the break that launched her career. |
| `en-es:full-family-repaired-full:break:quebrar:005` | `abstain` | `abstain` | `policy` | 0.0073 | 0.0289 | -0.0216 | The dashboard listed Break as an internal project code. |
| `en-es:full-family-repaired-full:bar:cercar:001` | `replace` | `abstain` | `policy` | 0.0414 | 0.0000 | 0.0414 | Workers will bar the storage yard with temporary fencing. |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `replace` | `policy` | 0.1176 | 0.0000 | 0.1176 | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:bar:cercar:003` | `abstain` | `abstain` | `policy` | 0.0399 | 0.0000 | 0.0399 | They met at the bar after work. |
| `en-es:full-family-repaired-full:bar:cercar:004` | `abstain` | `abstain` | `policy` | 0.0378 | 0.0000 | 0.0378 | The violin enters on the second bar of the song. |
| `en-es:full-family-repaired-full:bar:cercar:005` | `abstain` | `abstain` | `policy` | 0.0126 | 0.0328 | -0.0201 | The dashboard listed Bar as an internal project code. |
| `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `replace` | `policy` | 0.0766 | 0.0000 | 0.0766 | Set the image offset to twelve pixels from the left edge. |
| `en-es:full-family-repaired-full:offset:distancia:002` | `replace` | `replace` | `policy` | 0.0821 | 0.0233 | 0.0588 | The sensor has a small offset from the center line. |
| `en-es:full-family-repaired-full:offset:distancia:003` | `abstain` | `abstain` | `policy` | 0.0302 | 0.0000 | 0.0302 | The rebate helped offset the higher shipping cost. |
| `en-es:full-family-repaired-full:offset:distancia:004` | `abstain` | `abstain` | `policy` | 0.0379 | 0.0278 | 0.0101 | The invoice showed a small offset for the returned item. |
| `en-es:full-family-repaired-full:offset:distancia:005` | `abstain` | `abstain` | `policy` | 0.0267 | 0.0000 | 0.0267 | The dashboard listed Offset as an internal project code. |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `replace` | `policy` | 0.1409 | 0.0786 | 0.0623 | She tried to bridle her anger during the meeting. |
