# en-es Food/Cooking Full-Source Review Precision Summary

- Status: `ok`
- Decision: `srs_food_cooking_full_source_review_precision_summary_ready`
- Generated: `2026-05-19T02:26:49+00:00`
- Reviewed rows: `96`
- Accepted rows: `89` (92.7%)
- Strong accepts: `53`
- Light accepts: `36`
- Rejected rows: `7` (7.3%)

## Flow Assessment

- Doing the right thing: `True`
- Reason: The current method separated source discovery, review labels, diagnostic overlay behavior, and runtime admission. The broad source sample accepted most rows while surfacing specific false-positive classes before product lift.
- Next best step: Convert review results into small policy guards, then rerun the audit/review summary before promoting any broader food/cooking overlay.

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
| `B` | 39 | 36 | 25 | 11 | 3 | 7.7% |
| `D` | 5 | 5 | 1 | 4 | 0 | 0.0% |
| `A` | 4 | 4 | 1 | 3 | 0 | 0.0% |

## Precision By Confidence Band

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `high` | 38 | 36 | 25 | 11 | 2 | 5.3% |
| `review` | 34 | 30 | 15 | 15 | 4 | 11.8% |
| `medium` | 22 | 21 | 13 | 8 | 1 | 4.5% |
| `inventory` | 2 | 2 | 0 | 2 | 0 | 0.0% |

## Notable Source Labels

| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `cooking` | 4 | 4 | 3 | 1 | 0 | 0.0% |
| `fish` | 4 | 3 | 0 | 3 | 1 | 25.0% |
| `beverages` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `desserts` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `food_gloss_pattern` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `foods` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `fruits` | 3 | 2 | 1 | 1 | 1 | 33.3% |
| `herbs` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `legumes` | 3 | 2 | 2 | 0 | 1 | 33.3% |
| `meats` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `spices` | 3 | 3 | 3 | 0 | 0 | 0.0% |
| `spices_and_herbs` | 3 | 3 | 1 | 2 | 0 | 0.0% |
| `vegetables` | 3 | 3 | 2 | 1 | 0 | 0.0% |
| `alcoholic_beverages` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `food` | 2 | 2 | 0 | 2 | 0 | 0.0% |
| `food_translation_pattern` | 2 | 2 | 0 | 2 | 0 | 0.0% |
| `primary_translation:beer` | 2 | 2 | 1 | 1 | 0 | 0.0% |
| `primary_translation:food` | 2 | 2 | 1 | 1 | 0 | 0.0% |
| `primary_translation:tomato` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `sauces` | 2 | 2 | 2 | 0 | 0 | 0.0% |
| `seafood` | 2 | 1 | 0 | 1 | 1 | 50.0% |
| `breads` | 1 | 1 | 1 | 0 | 0 | 0.0% |
| `cheeses` | 1 | 1 | 0 | 1 | 0 | 0.0% |
| `dairy_products` | 1 | 1 | 1 | 0 | 0 | 0.0% |

## Rejected Rows

- `claudia`: `reject_secondary_or_obscure_sense` via `C/fruits` - Greengage sense exists, but the dominant entry is a given name.
- `loco`: `reject_secondary_or_obscure_sense` via `C/seafood` - Seafood sense is buried under dominant adjective/person senses.
- `anaranjado`: `reject_wrong_topic` via `B/primary_translation:orange` - The matched sense is orange color, not orange fruit or food.
- `cocobolo`: `reject_wrong_topic` via `C/legumes` - Legume category is misleading here; dominant meaning is a tree/wood, not food.
- `limonero`: `reject_wrong_topic` via `B/primary_translation:lemon` - Matched lemon via tree/seller senses; dominant meaning is not food.
- `cha`: `reject_secondary_or_obscure_sense` via `B/primary_translation:tea` - Tea sense is historical/Philippine Spanish and too obscure for product lift.
- `morena`: `reject_secondary_or_obscure_sense` via `C/fish` - Moray/fish sense is not enough for food lift against dominant person/name senses.

## Policy Guidance

- Continue using review packets before promotion; the high accepted share is meaningful because rejects were caught before overlay lift.
- Treat strong accepted rows as overlay candidates only after provenance and rollback fields are generated.
- Keep light accepted rows as lower-membership or scalar-ready evidence, not binary strong topic evidence.
- Keep Tier D as review-gated discovery even when this sample was mostly acceptable; its broad population is still large and phrase-driven.
- Add guards for fruit-word translation matches that are actually colors, trees, sellers, or plants.
- Penalize name/person/adjective collisions before trusting category-derived food labels.
- Keep botanical category overlap review-gated unless primary translation or food gloss corroborates it.
- Penalize historical, archaic, or region-only terms unless the product explicitly supports that register.

## Limitations

- This summary describes one deterministic 96-row review packet, not the full 2,083-row precision.
- Agent labels remain pending user approval and are not product-overlay approval by themselves.
- High acceptance supports continuing the source path, but false-positive classes still need policy guards.
