# en-es Semantic Veto Active-Only Helper Runtime Smoke

- Status: `ok`
- Decision: `manual_testing_ready`
- Generated: `2026-05-09T02:08:15Z`
- Fixture data root: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root`
- Profile: `default`
- Decision policy: `en_es_sentence_veto_v2`
- Fallback policy: `abstain_on_unavailable`

## Publication Family

- Ruleset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root/srs/profiles/default/srs_ruleset_en-es.json`
- Snapshot: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`
- Semantic inventory: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`
- Manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`

## Runtime Smoke Metrics

- Rules: `24`
- Families: `24`
- Cases: `91`
- Active-only competition sets: `14`
- Shadowed competition sets: `10`
- Policy decisions: `91`
- Fallback decisions: `0`
- Decision accuracy on repaired-full smoke denominator: `0.7692`
- Replace recall: `0.5833`
- Harmful replaces: `1`
- False abstains: `20`

## Manual Test Notes

- The fixture data root is isolated; point LEXISHIFT_DATA_DIR at it for manual helper/app tests.
- With no explicit override, active-only fixture inventories auto-select en_es_sentence_veto_v2.
- The production default en_es_sentence_veto_v3 still requires sentence_transformers/model availability.
- Expected user-facing outcome remains binary: replace or abstain.

Use this environment override for manual helper/app smoke tests:

```bash
export LEXISHIFT_DATA_DIR='/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-poc-v5-helper-runtime-smoke-data-root'
```

## Sample Decisions

| Case | Gold | Decision | Source | Active | Shadow | Margin | Sentence |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `en-es:full-family-repaired-full:break:quebrar:001` | `replace` | `abstain` | `policy` | 0.0191 | 0.0000 | 0.0191 | The old plate began to break along the rim. |
| `en-es:full-family-repaired-full:break:quebrar:002` | `replace` | `replace` | `policy` | 0.1243 | 0.0138 | 0.1105 | A dry branch can break under sudden pressure. |
| `en-es:full-family-repaired-full:break:quebrar:003` | `abstain` | `abstain` | `policy` | 0.0370 | 0.0131 | 0.0239 | A news alert can break the broadcast without warning. |
| `en-es:full-family-repaired-full:break:quebrar:004` | `abstain` | `abstain` | `policy` | 0.0087 | 0.0655 | -0.0568 | Her internship became the break that launched her career. |
| `en-es:full-family-repaired-full:break:quebrar:005` | `abstain` | `abstain` | `policy` | 0.0089 | 0.0343 | -0.0254 | The dashboard listed Break as an internal project code. |
| `en-es:full-family-repaired-full:bar:cercar:001` | `replace` | `replace` | `policy` | 0.0528 | 0.0000 | 0.0528 | Workers will bar the storage yard with temporary fencing. |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `replace` | `policy` | 0.1013 | 0.0000 | 0.1013 | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:bar:cercar:003` | `abstain` | `abstain` | `policy` | 0.0135 | 0.0000 | 0.0135 | They met at the bar after work. |
| `en-es:full-family-repaired-full:bar:cercar:004` | `abstain` | `abstain` | `policy` | 0.0318 | 0.0000 | 0.0318 | The violin enters on the second bar of the song. |
| `en-es:full-family-repaired-full:bar:cercar:005` | `abstain` | `abstain` | `policy` | 0.0108 | 0.0380 | -0.0271 | The dashboard listed Bar as an internal project code. |
| `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `replace` | `policy` | 0.0950 | 0.0000 | 0.0950 | Set the image offset to twelve pixels from the left edge. |
| `en-es:full-family-repaired-full:offset:distancia:002` | `replace` | `replace` | `policy` | 0.1010 | 0.0251 | 0.0760 | The sensor has a small offset from the center line. |
| `en-es:full-family-repaired-full:offset:distancia:003` | `abstain` | `abstain` | `policy` | 0.0368 | 0.0000 | 0.0368 | The rebate helped offset the higher shipping cost. |
| `en-es:full-family-repaired-full:offset:distancia:004` | `abstain` | `abstain` | `policy` | 0.0437 | 0.0345 | 0.0093 | The invoice showed a small offset for the returned item. |
| `en-es:full-family-repaired-full:offset:distancia:005` | `abstain` | `abstain` | `policy` | 0.0305 | 0.0000 | 0.0305 | The dashboard listed Offset as an internal project code. |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `replace` | `policy` | 0.1403 | 0.0726 | 0.0677 | She tried to bridle her anger during the meeting. |
