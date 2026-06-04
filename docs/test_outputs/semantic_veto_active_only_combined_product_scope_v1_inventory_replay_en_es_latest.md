# en-es Semantic Veto Active-Only Inventory Replay

- Status: `ok`
- Decision: `inventory_shaped_replay_ready_for_runtime_smoke`
- Generated: `2026-05-09T22:54:14Z`
- Families: `49`
- Cases: `189`
- Packaged/applied rows: `112` / `112`

## Policy

- Policy: `active_only_inventory_replay_tfidf_v1`
- Scorer/context/evidence: `tfidf_cosine` / `masked_sentence` / `all_evidence_text`
- Thresholds: min active `0.05`, min margin `0.0`

## Metrics

| Mode | Accuracy | Replace recall | Harmful | False abstains | Predicted replaces |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base` | 0.5026 | 0.0510 | 1 | 93 | 6 |
| `candidate` | 0.7196 | 0.4694 | 1 | 52 | 47 |

## Delta

- Decision accuracy: `+0.2169`
- Replace recall: `+0.4184`
- Harmful replacements: `+0`
- False abstains: `-41`

## Changed Cases

| Case | Gold | Base | Candidate | Sentence |
| --- | --- | --- | --- | --- |
| `en-es:full-family-repaired-full:bar:cercar:002` | `replace` | `abstain` | `replace` | The rancher used wire panels to bar the cattle inside the field. |
| `en-es:full-family-repaired-full:offset:distancia:001` | `replace` | `abstain` | `replace` | Set the image offset to twelve pixels from the left edge. |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `replace` | `abstain` | `replace` | She tried to bridle her anger during the meeting. |
| `en-es:full-family-repaired-full:bridle:reprimir:002` | `replace` | `abstain` | `replace` | The lawyer had to bridle his frustration after the ruling. |
| `en-es:full-family-repaired-full:emotion:emoci-n:002` | `replace` | `abstain` | `replace` | She hid every emotion during the interview. |
| `en-es:full-family-repaired-full:dentist:dentista:002` | `replace` | `abstain` | `replace` | She booked an appointment with a dentist near the station. |
| `en-es:full-family-repaired-full:bouillon:caldo:001` | `replace` | `abstain` | `replace` | Add bouillon to the rice for a richer flavor. |
| `en-es:full-family-repaired-full:bouillon:caldo:002` | `replace` | `abstain` | `replace` | The recipe starts with bouillon and fresh herbs. |
| `en-es:full-family-repaired-full:control:gobernar:001` | `replace` | `abstain` | `replace` | The coalition hoped to control parliament after the election. |
| `en-es:full-family-repaired-full:control:gobernar:002` | `replace` | `abstain` | `replace` | A small council continued to control the territory after the coup. |
| `en-es:full-family-repaired-full:control:gobernar:004` | `abstain` | `replace` | `abstain` | The study included a control group and a treatment group. |
| `en-es:full-family-repaired-full:stall:cuadra:001` | `replace` | `abstain` | `replace` | The horse returned to its stall after training. |
| `en-es:full-family-repaired-full:rumanian:rumano:001` | `replace` | `abstain` | `replace` | The museum displayed Rumanian folk costumes. |
| `en-es:full-family-repaired-full:pub:taberna:002` | `replace` | `abstain` | `replace` | The old pub serves soup and local beer. |
| `en-es:full-family-repaired-full:salesman:vendedor:001` | `replace` | `abstain` | `replace` | The salesman explained the warranty in detail. |
| `en-es:full-family-repaired-full:handiwork:artesan-a:002` | `replace` | `abstain` | `replace` | Each carved bowl showed careful handiwork. |
| `en-es:full-family-repaired-full:begin:comenzar:001` | `replace` | `abstain` | `replace` | The lecture will begin at nine. |
| `en-es:full-family-repaired-full:billow:oleaje:001` | `replace` | `abstain` | `replace` | A dark billow rolled across the harbor. |
| `en-es:full-family-repaired-full:among:entre:001` | `replace` | `abstain` | `replace` | The letter was hidden among the old books. |
| `en-es:full-family-repaired-full:recover:sanar:001` | `replace` | `abstain` | `replace` | The patient will recover after several weeks of rest. |
| `en-es:full-family-repaired-full:recover:sanar:002` | `replace` | `abstain` | `replace` | His ankle began to recover after therapy. |
| `en-es:full-family-repaired-full:heart:coraz-n:001` | `replace` | `abstain` | `replace` | Her heart was beating quickly after the race. |
| `en-es:full-family-repaired-full:cite:mencionar:001` | `replace` | `abstain` | `replace` | The report will cite several local witnesses. |
| `en-es:full-family-repaired-full:snore:roncar:002` | `replace` | `abstain` | `replace` | She could hear her roommate snore through the wall. |
| `en-es:full-family-repaired-full:snore:roncar:003` | `abstain` | `abstain` | `replace` | A loud snore came from the next room. |
| `en-es:full-family-repaired-full:current:contempor-neo:002` | `replace` | `abstain` | `replace` | Current research focuses on smaller batteries. |
| `en-es:full-family-repaired-full:parrot:loro:001` | `replace` | `abstain` | `replace` | A green parrot perched above the doorway. |
| `en-es:full-family-repaired-full:american:americano:001` | `replace` | `abstain` | `replace` | The museum displayed American quilts. |
| `en-es:full-family-repaired-full:rebate:descuento:001` | `replace` | `abstain` | `replace` | The store offered a rebate on the new refrigerator. |
| `en-es:full-family-repaired-full:rebate:descuento:002` | `replace` | `abstain` | `replace` | Customers receive a rebate after mailing the form. |

## Runtime Boundary

- `candidate inventory is an experiment artifact, not a helper-published sidecar`
- `replay uses the no-spend TF-IDF policy that produced the active-only score-contribution result`
- `production helper smoke still needs the actual publication family and configured runtime policy`
