# en-es Semantic Veto Active-Only Inventory Replay

- Status: `ok`
- Decision: `inventory_shaped_replay_ready_for_runtime_smoke`
- Generated: `2026-05-09T22:53:21Z`
- Families: `16`
- Cases: `63`
- Packaged/applied rows: `32` / `32`

## Policy

- Policy: `active_only_inventory_replay_tfidf_v1`
- Scorer/context/evidence: `tfidf_cosine` / `masked_sentence` / `all_evidence_text`
- Thresholds: min active `0.05`, min margin `0.0`

## Metrics

| Mode | Accuracy | Replace recall | Harmful | False abstains | Predicted replaces |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base` | 0.5556 | 0.1250 | 0 | 28 | 4 |
| `candidate` | 0.7143 | 0.5000 | 2 | 16 | 18 |

## Delta

- Decision accuracy: `+0.1587`
- Replace recall: `+0.3750`
- Harmful replacements: `+2`
- False abstains: `-12`

## Changed Cases

| Case | Gold | Base | Candidate | Sentence |
| --- | --- | --- | --- | --- |
| `en-es:full-family-repaired-full:emotion:emoci-n:002` | `replace` | `abstain` | `replace` | She hid every emotion during the interview. |
| `en-es:full-family-repaired-full:stall:cuadra:001` | `replace` | `abstain` | `replace` | The horse returned to its stall after training. |
| `en-es:full-family-repaired-full:handiwork:artesan-a:002` | `replace` | `abstain` | `replace` | Each carved bowl showed careful handiwork. |
| `en-es:full-family-repaired-full:billow:oleaje:001` | `replace` | `abstain` | `replace` | A dark billow rolled across the harbor. |
| `en-es:full-family-repaired-full:billow:oleaje:003` | `abstain` | `abstain` | `replace` | Smoke began to billow from the warehouse. |
| `en-es:full-family-repaired-full:recover:sanar:001` | `replace` | `abstain` | `replace` | The patient will recover after several weeks of rest. |
| `en-es:full-family-repaired-full:recover:sanar:002` | `replace` | `abstain` | `replace` | His ankle began to recover after therapy. |
| `en-es:full-family-repaired-full:snore:roncar:002` | `replace` | `abstain` | `replace` | She could hear her roommate snore through the wall. |
| `en-es:full-family-repaired-full:snore:roncar:003` | `abstain` | `abstain` | `replace` | A loud snore came from the next room. |
| `en-es:full-family-repaired-full:current:contempor-neo:002` | `replace` | `abstain` | `replace` | Current research focuses on smaller batteries. |
| `en-es:full-family-repaired-full:parrot:loro:001` | `replace` | `abstain` | `replace` | A green parrot perched above the doorway. |
| `en-es:full-family-repaired-full:adder:v-bora:001` | `replace` | `abstain` | `replace` | An adder slid through the grass near the path. |
| `en-es:full-family-repaired-full:pair:par:002` | `replace` | `abstain` | `replace` | The report compared each pair of measurements. |
| `en-es:full-family-repaired-full:health:salud:001` | `replace` | `abstain` | `replace` | Regular exercise improved his health. |

## Runtime Boundary

- `candidate inventory is an experiment artifact, not a helper-published sidecar`
- `replay uses the no-spend TF-IDF policy that produced the active-only score-contribution result`
- `production helper smoke still needs the actual publication family and configured runtime policy`
