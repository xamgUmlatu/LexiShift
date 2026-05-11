# en-es Semantic Veto Active-Only Helper Runtime Smoke

- Status: `ok`
- Decision: `manual_testing_ready`
- Generated: `2026-05-09T22:31:56Z`
- Fixture data root: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root`
- Profile: `default`
- Decision policy: `en_es_sentence_veto_v2`
- Fallback policy: `abstain_on_unavailable`

## Publication Family

- Ruleset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root/srs/profiles/default/srs_ruleset_en-es.json`
- Snapshot: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`
- Semantic inventory: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`
- Manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`

## Runtime Smoke Metrics

- Rules: `18`
- Families: `18`
- Cases: `70`
- Active-only competition sets: `10`
- Shadowed competition sets: `8`
- Policy decisions: `70`
- Fallback decisions: `0`
- Decision accuracy on repaired-full smoke denominator: `0.6714`
- Replace recall: `0.4444`
- Harmful replaces: `3`
- False abstains: `20`

## Manual Test Notes

- The fixture data root is isolated; point LEXISHIFT_DATA_DIR at it for manual helper/app tests.
- With no explicit override, active-only fixture inventories auto-select en_es_sentence_veto_v2.
- The production default en_es_sentence_veto_v3 still requires sentence_transformers/model availability.
- Expected user-facing outcome remains binary: replace or abstain.

Use this environment override for manual helper/app smoke tests:

```bash
export LEXISHIFT_DATA_DIR='/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-product-scope-band-grading-v1-active-only-helper-runtime-smoke-data-root'
```

## Sample Decisions

| Case | Gold | Decision | Source | Active | Shadow | Margin | Sentence |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `en-es:full-family-repaired-full:bar:cercar:001` | `replace` | `abstain` | `policy` | 0.0282 | 0.0000 | 0.0282 | Workers will bar the storage yard with temporary fencing. |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `replace` | `policy` | 0.0812 | 0.0000 | 0.0812 | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:bar:cercar:003` | `abstain` | `replace` | `policy` | 0.0619 | 0.0000 | 0.0619 | They met at the bar after work. |
| `en-es:full-family-repaired-full:bar:cercar:004` | `abstain` | `abstain` | `policy` | 0.0378 | 0.0000 | 0.0378 | The violin enters on the second bar of the song. |
| `en-es:full-family-repaired-full:bar:cercar:005` | `abstain` | `abstain` | `policy` | 0.0130 | 0.0392 | -0.0262 | The dashboard listed Bar as an internal project code. |
| `en-es:full-family-repaired-full:dentist:dentista:001` | `replace` | `abstain` | `policy` | 0.0150 | 0.0000 | 0.0150 | The dentist repaired the chipped tooth before lunch. |
| `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `replace` | `policy` | 0.2219 | 0.0000 | 0.2219 | She booked an appointment with a dentist near the station. |
| `en-es:full-family-repaired-full:dentist:dentista:003` | `abstain` | `abstain` | `policy` | 0.0238 | 0.0000 | 0.0238 | The dashboard listed Dentist as an internal project code. |
| `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `replace` | `policy` | 0.1290 | 0.0000 | 0.1290 | The coalition hoped to control parliament after the election. |
| `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `replace` | `policy` | 0.0883 | 0.0152 | 0.0731 | A small council continued to control the territory after the coup. |
| `en-es:full-family-repaired-full:control:gobernar:003` | `abstain` | `replace` | `policy` | 0.0510 | 0.0000 | 0.0510 | Use the slider to control the volume. |
| `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `abstain` | `policy` | 0.1048 | 0.1212 | -0.0163 | The study included a control group and a treatment group. |
| `en-es:full-family-repaired-full:control:gobernar:005` | `abstain` | `abstain` | `policy` | 0.0122 | 0.0323 | -0.0201 | The dashboard listed Control as an internal project code. |
| `en-es:full-family-repaired-full:rumanian:rumano:001` | `replace` | `replace` | `policy` | 0.1064 | 0.0000 | 0.1064 | The museum displayed Rumanian folk costumes. |
| `en-es:full-family-repaired-full:rumanian:rumano:002` | `replace` | `abstain` | `policy` | 0.0245 | 0.0000 | 0.0245 | The form asked whether he held a Rumanian passport. |
| `en-es:full-family-repaired-full:rumanian:rumano:003` | `abstain` | `abstain` | `policy` | 0.0270 | 0.0000 | 0.0270 | The dashboard listed Rumanian as an internal project code. |
