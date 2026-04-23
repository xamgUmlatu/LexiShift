# Semantic Routing Sentence Veto Decision Ladder

- Status: `ok`
- Generated: `2026-04-23T05:06:48Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v9.json`
- Pair: `en-es`
- Base scorer: `sentence_transformer_cosine`
- Base context / evidence: `masked_sentence` / `all_evidence_text`
- Base phrase / rescue: `noun_family_frame_guard` / `sense_label_near_tie_active_rescue`
- Base hard thresholds: `min_active=0.0`, `min_margin=0.0`

## Frozen Hard-Replace Baseline

- Hard replace precision / recall: `96.7%` / `80.6%`
- Hard harmful replace / false abstain: `1.9%` / `19.4%`

## Best Overall

- Config: `soft:a=0.55:m=-0.03`
- Soft affordance count / true / false: `4` / `4` / `0`
- Hard replace recall / harmful replace: `80.6%` / `1.9%`
- Replace-or-soft recall / lift: `91.7%` / `11.1%`
- Soft precision / noise: `100.0%` / `0.0%`
- Surfaced precision / missed replace rate: `97.1%` / `8.3%`
- Soft true-positive samples: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

## Best By Soft-False-Positive Budget

- Budget: `soft_false_positive_count <= 0`
- Config: `soft:a=0.55:m=-0.03`
- Soft affordance count / true / false: `4` / `4` / `0`
- Hard replace recall / harmful replace: `80.6%` / `1.9%`
- Replace-or-soft recall / lift: `91.7%` / `11.1%`
- Soft precision / noise: `100.0%` / `0.0%`
- Surfaced precision / missed replace rate: `97.1%` / `8.3%`
- Soft true-positive samples: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

- Budget: `soft_false_positive_count <= 1`
- Config: `soft:a=0.55:m=-0.03`
- Soft affordance count / true / false: `4` / `4` / `0`
- Hard replace recall / harmful replace: `80.6%` / `1.9%`
- Replace-or-soft recall / lift: `91.7%` / `11.1%`
- Soft precision / noise: `100.0%` / `0.0%`
- Surfaced precision / missed replace rate: `97.1%` / `8.3%`
- Soft true-positive samples: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

- Budget: `soft_false_positive_count <= 2`
- Config: `soft:a=0.55:m=-0.03`
- Soft affordance count / true / false: `4` / `4` / `0`
- Hard replace recall / harmful replace: `80.6%` / `1.9%`
- Replace-or-soft recall / lift: `91.7%` / `11.1%`
- Soft precision / noise: `100.0%` / `0.0%`
- Surfaced precision / missed replace rate: `97.1%` / `8.3%`
- Soft true-positive samples: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

## Top Configs

| Rank | soft_active | soft_margin | Soft Cnt | Soft True | Soft False | Replace+Soft Recall | Recall Lift | Soft Precision | Soft Noise | Surfaced Precision | Missed Replace |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.55 | -0.03 | 4 | 4 | 0 | 91.7% | 11.1% | 100.0% | 0.0% | 97.1% | 3 |
| 2 | 0.58 | -0.03 | 3 | 3 | 0 | 88.9% | 8.3% | 100.0% | 0.0% | 97.0% | 4 |
| 3 | 0.60 | -0.03 | 2 | 2 | 0 | 86.1% | 5.6% | 100.0% | 0.0% | 96.9% | 5 |
| 4 | 0.55 | -0.02 | 2 | 2 | 0 | 86.1% | 5.6% | 100.0% | 0.0% | 96.9% | 5 |
| 5 | 0.60 | -0.02 | 1 | 1 | 0 | 83.3% | 2.8% | 100.0% | 0.0% | 96.8% | 6 |
| 6 | 0.58 | -0.02 | 1 | 1 | 0 | 83.3% | 2.8% | 100.0% | 0.0% | 96.8% | 6 |
| 7 | 0.60 | 0.00 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
| 8 | 0.60 | -0.01 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
| 9 | 0.58 | 0.00 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
| 10 | 0.58 | -0.01 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
| 11 | 0.55 | 0.00 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
| 12 | 0.55 | -0.01 | 0 | 0 | 0 | 80.6% | 0.0% | n/a | 0.0% | 96.7% | 7 |
