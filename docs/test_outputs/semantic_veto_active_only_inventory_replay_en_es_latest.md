# en-es Semantic Veto Active-Only Inventory Replay

- Status: `ok`
- Decision: `inventory_shaped_replay_ready_for_runtime_smoke`
- Generated: `2026-05-09T02:04:34Z`
- Families: `24`
- Cases: `91`
- Packaged/applied rows: `45` / `45`

## Policy

- Policy: `active_only_inventory_replay_tfidf_v1`
- Scorer/context/evidence: `tfidf_cosine` / `masked_sentence` / `all_evidence_text`
- Thresholds: min active `0.05`, min margin `0.0`

## Metrics

| Mode | Accuracy | Replace recall | Harmful | False abstains | Predicted replaces |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base` | 0.5055 | 0.0833 | 1 | 44 | 5 |
| `candidate` | 0.7363 | 0.5000 | 0 | 24 | 24 |

## Delta

- Decision accuracy: `+0.2308`
- Replace recall: `+0.4167`
- Harmful replacements: `-1`
- False abstains: `-20`

## Changed Cases

| Case | Gold | Base | Candidate | Sentence |
| --- | --- | --- | --- | --- |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `abstain` | `replace` | Set the image offset to twelve pixels from the left edge. |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `abstain` | `replace` | She tried to bridle her anger during the meeting. |
| `en-es:full-family-repaired-full:bridle:reprimir:002` | `replace` | `abstain` | `replace` | The lawyer had to bridle his frustration after the ruling. |
| `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `abstain` | `replace` | She booked an appointment with a dentist near the station. |
| `en-es:full-family-repaired-full:bouillon:caldo:001` | `replace` | `abstain` | `replace` | Add bouillon to the rice for a richer flavor. |
| `en-es:full-family-repaired-full:bouillon:caldo:002` | `replace` | `abstain` | `replace` | The recipe starts with bouillon and fresh herbs. |
| `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | The coalition hoped to control parliament after the election. |
| `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `abstain` | `replace` | A small council continued to control the territory after the coup. |
| `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `replace` | `abstain` | The study included a control group and a treatment group. |
| `en-es:full-family-repaired-full:rumanian:rumano:001` | `replace` | `abstain` | `replace` | The museum displayed Rumanian folk costumes. |
| `en-es:full-family-repaired-full:salesman:vendedor:001` | `replace` | `abstain` | `replace` | The salesman explained the warranty in detail. |
| `en-es:full-family-repaired-full:begin:comenzar:001` | `replace` | `abstain` | `replace` | The lecture will begin at nine. |
| `en-es:full-family-repaired-full:among:entre:001` | `replace` | `abstain` | `replace` | The letter was hidden among the old books. |
| `en-es:full-family-repaired-full:heart:coraz-n:001` | `replace` | `abstain` | `replace` | Her heart was beating quickly after the race. |
| `en-es:full-family-repaired-full:american:americano:001` | `replace` | `abstain` | `replace` | The museum displayed American quilts. |
| `en-es:full-family-repaired-full:rebate:descuento:002` | `replace` | `abstain` | `replace` | Customers receive a rebate after mailing the form. |
| `en-es:full-family-repaired-full:govern:gobernar:001` | `replace` | `abstain` | `replace` | The elected council will govern the province. |
| `en-es:full-family-repaired-full:brother:hermano:001` | `replace` | `abstain` | `replace` | My brother still lives near our parents. |
| `en-es:full-family-repaired-full:entirely:enteramente:001` | `replace` | `abstain` | `replace` | The decision was entirely voluntary. |
| `en-es:full-family-repaired-full:entirely:enteramente:002` | `replace` | `abstain` | `replace` | She was entirely satisfied with the meal. |

## Runtime Boundary

- `candidate inventory is an experiment artifact, not a helper-published sidecar`
- `replay uses the no-spend TF-IDF policy that produced the active-only score-contribution result`
- `production helper smoke still needs the actual publication family and configured runtime policy`
