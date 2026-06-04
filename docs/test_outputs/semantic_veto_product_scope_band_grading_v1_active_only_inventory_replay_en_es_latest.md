# en-es Semantic Veto Active-Only Inventory Replay

- Status: `ok`
- Decision: `inventory_shaped_replay_ready_for_runtime_smoke`
- Generated: `2026-05-09T22:31:22Z`
- Families: `18`
- Cases: `70`
- Packaged/applied rows: `35` / `35`

## Policy

- Policy: `active_only_inventory_replay_tfidf_v1`
- Scorer/context/evidence: `tfidf_cosine` / `masked_sentence` / `all_evidence_text`
- Thresholds: min active `0.05`, min margin `0.0`

## Metrics

| Mode | Accuracy | Replace recall | Harmful | False abstains | Predicted replaces |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base` | 0.4714 | 0.0000 | 1 | 36 | 1 |
| `candidate` | 0.6857 | 0.4167 | 1 | 21 | 16 |

## Delta

- Decision accuracy: `+0.2143`
- Replace recall: `+0.4167`
- Harmful replacements: `+0`
- False abstains: `-15`

## Changed Cases

| Case | Gold | Base | Candidate | Sentence |
| --- | --- | --- | --- | --- |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:bar:cercar:003` | `abstain` | `abstain` | `replace` | They met at the bar after work. |
| `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `abstain` | `replace` | She booked an appointment with a dentist near the station. |
| `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | The coalition hoped to control parliament after the election. |
| `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `abstain` | `replace` | A small council continued to control the territory after the coup. |
| `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `replace` | `abstain` | The study included a control group and a treatment group. |
| `en-es:full-family-repaired-full:rumanian:rumano:001` | `replace` | `abstain` | `replace` | The museum displayed Rumanian folk costumes. |
| `en-es:full-family-repaired-full:pub:taberna:002` | `replace` | `abstain` | `replace` | The old pub serves soup and local beer. |
| `en-es:full-family-repaired-full:cite:mencionar:001` | `replace` | `abstain` | `replace` | The report will cite several local witnesses. |
| `en-es:full-family-repaired-full:american:americano:001` | `replace` | `abstain` | `replace` | The museum displayed American quilts. |
| `en-es:full-family-repaired-full:endure:durar:001` | `replace` | `abstain` | `replace` | The stone bridge may endure for centuries. |
| `en-es:full-family-repaired-full:govern:gobernar:001` | `replace` | `abstain` | `replace` | The elected council will govern the province. |
| `en-es:full-family-repaired-full:shortage:falta:001` | `replace` | `abstain` | `replace` | The town faced a water shortage during summer. |
| `en-es:full-family-repaired-full:shortage:falta:002` | `replace` | `abstain` | `replace` | A shortage of nurses delayed the clinic opening. |
| `en-es:full-family-repaired-full:except:excepto:002` | `replace` | `abstain` | `replace` | The office is open every day except Sunday. |
| `en-es:full-family-repaired-full:region:comarca:002` | `replace` | `abstain` | `replace` | Local officials met with leaders from the mountain region. |
| `en-es:full-family-repaired-full:owe:deber:002` | `replace` | `abstain` | `replace` | We owe our success to careful planning. |

## Runtime Boundary

- `candidate inventory is an experiment artifact, not a helper-published sidecar`
- `replay uses the no-spend TF-IDF policy that produced the active-only score-contribution result`
- `production helper smoke still needs the actual publication family and configured runtime policy`
