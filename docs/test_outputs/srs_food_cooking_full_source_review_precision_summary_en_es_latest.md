# en-es Food/Cooking Full-Source Review Precision Summary

- Status: `ok`
- Decision: `srs_food_cooking_full_source_review_precision_summary_ready`
- Generated: `2026-05-19T02:40:48+00:00`
- Reviewed rows: `96`
- Accepted rows: `91` (94.8%)
- Strong accepts: `54`
- Light accepts: `37`
- Rejected rows: `5` (5.2%)

## Flow Assessment

- Doing the right thing: `True`
- Reason: The current method separated source discovery, review labels, diagnostic overlay behavior, and runtime admission. The broad source sample accepted most rows while surfacing specific false-positive classes before product lift.
- Next best step: Use the remaining rejects to decide whether another narrow guard pass is worth it, then validate the larger frontier and overlay/admission behavior before any broader food/cooking product lift.

## Findings

- `PASS` `review_rows_loaded`: Review rows were loaded.
- `PASS` `review_rows_labeled`: All review rows are labeled.
- `PASS` `accepted_majority`: Accepted rows outnumber rejects in the reviewed sample.
- `WARN` `policy_guards_still_needed`: Rejected rows identify false-positive classes that should be policy-guarded before promotion.
- `PASS` `label_merge_clean`: Labels merged cleanly.

## Precision By Tier

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C` | 48 | 44 | 26 | 18 | 4 | 8.3% |
| `B` | 38 | 38 | 26 | 12 | 0 | 0.0% |
| `D` | 6 | 5 | 1 | 4 | 1 | 16.7% |
| `A` | 4 | 4 | 1 | 3 | 0 | 0.0% |

## Precision By Confidence Band

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high` | 37 | 37 | 26 | 11 | 0 | 0.0% |
| `review` | 33 | 31 | 15 | 16 | 2 | 6.1% |
| `medium` | 22 | 21 | 13 | 8 | 1 | 4.5% |
| `inventory` | 4 | 2 | 0 | 2 | 2 | 50.0% |

## Notable Source Labels

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fish` | 5 | 3 | 0 | 3 | 2 | 40.0% |
| `cooking` | 4 | 4 | 3 | 1 | 0 | 0.0% |
| `food_gloss_pattern` | 4 | 3 | 1 | 2 | 1 | 25.0% |
| `beverages` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `desserts` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `foods` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `fruits` | 3 | 2 | 1 | 1 | 1 | 33.3% |
| `herbs` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `legumes` | 3 | 2 | 2 | 0 | 1 | 33.3% |
| `meats` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `primary_translation:beer` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `spices` | 3 | 3 | 3 | 0 | 0 | 0.0% |
| `spices_and_herbs` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `vegetables` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `alcoholic_beverages` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `food` | 2 | 2 | 0 | 2 | 0 | 0.0% |
| `food_translation_pattern` | 2 | 2 | 0 | 2 | 0 | 0.0% |
| `primary_translation:food` | 2 | 2 | 1 | 1 | 0 | 0.0% |
| `primary_translation:tomato` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `sauces` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `breads` | 1 | 1 | 1 | 0 | 0 | 0.0% |
| `cheeses` | 1 | 1 | 0 | 1 | 0 | 0.0% |
| `dairy_products` | 1 | 1 | 1 | 0 | 0 | 0.0% |
| `grains` | 1 | 1 | 0 | 1 | 0 | 0.0% |

## Rejected Rows

- `maní forrajero`: `reject_wrong_topic` via `C/legumes` - Pinto peanut/forage crop is botanical or fodder vocabulary here, not learner-facing food/cooking vocabulary.
- `artrodiro`: `reject_wrong_topic` via `C/fish` - Extinct zoological fish term, not food/cooking vocabulary.
- `pavía`: `reject_secondary_or_obscure_sense` via `C/fruits` - Fruit-variety sense exists, but dominant entries are Italian place names and the food sense is too secondary.
- `carnívoro`: `reject_wrong_topic` via `D/food_gloss_pattern` - Meat-eating animal/person vocabulary, not food or cooking vocabulary.
- `reo`: `reject_secondary_or_obscure_sense` via `C/fish` - Sea-trout sense exists, but legal/criminal senses dominate and the fish sense is too secondary for food lift.

## Policy Guidance

- Continue using review packets before promotion; the high accepted share is meaningful because rejects were caught before overlay lift.
- Treat strong accepted rows as overlay candidates only after provenance and rollback fields are generated.
- Keep light accepted rows as lower-membership or scalar-ready evidence, not binary strong topic evidence.
- Keep Tier D as review-gated discovery even when this sample was mostly acceptable; its broad population is still large and phrase-driven.
- Penalize name/person/adjective collisions before trusting category-derived food labels.
- Keep botanical category overlap review-gated unless primary translation or food gloss corroborates it.

## Limitations

- This summary describes one deterministic 96-row review packet, not full-universe precision.
- Agent labels remain pending user approval and are not product-overlay approval by themselves.
- High acceptance supports continuing the source path, but false-positive classes still need policy guards.
