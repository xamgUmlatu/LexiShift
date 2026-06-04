# Semantic Routing Sentence Veto Decision Ladder

- Status: `ok`
- Generated: `2026-04-23T19:15:28Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Pair: `en-es`
- Base scorer: `sentence_transformer_cosine`
- Base context / evidence: `masked_sentence` / `all_evidence_text`
- Base phrase / rescue: `noun_family_frame_guard` / `sense_label_near_tie_active_rescue`
- Base hard thresholds: `min_active=0.0`, `min_margin=0.0`

## Frozen Hard-Replace Baseline

- Hard replace precision / recall: `96.7%` / `76.3%`
- Hard harmful replace / false abstain: `1.8%` / `23.7%`

## Best Overall

- Config: `soft:a=0.60:m=0.00`
- Soft affordance count / true / false: `0` / `0` / `0`
- Hard replace recall / harmful replace: `76.3%` / `1.8%`
- Replace-or-soft recall / lift: `76.3%` / `0.0%`
- Soft precision / noise: `n/a` / `0.0%`
- Surfaced precision / missed replace rate: `96.7%` / `23.7%`

## Best By Soft-False-Positive Budget

- Budget: `soft_false_positive_count <= 0`
- Config: `soft:a=0.60:m=0.00`
- Soft affordance count / true / false: `0` / `0` / `0`
- Hard replace recall / harmful replace: `76.3%` / `1.8%`
- Replace-or-soft recall / lift: `76.3%` / `0.0%`
- Soft precision / noise: `n/a` / `0.0%`
- Surfaced precision / missed replace rate: `96.7%` / `23.7%`

- Budget: `soft_false_positive_count <= 1`
- Config: `soft:a=0.60:m=0.00`
- Soft affordance count / true / false: `0` / `0` / `0`
- Hard replace recall / harmful replace: `76.3%` / `1.8%`
- Replace-or-soft recall / lift: `76.3%` / `0.0%`
- Soft precision / noise: `n/a` / `0.0%`
- Surfaced precision / missed replace rate: `96.7%` / `23.7%`

- Budget: `soft_false_positive_count <= 2`
- Config: `soft:a=0.60:m=0.00`
- Soft affordance count / true / false: `0` / `0` / `0`
- Hard replace recall / harmful replace: `76.3%` / `1.8%`
- Replace-or-soft recall / lift: `76.3%` / `0.0%`
- Soft precision / noise: `n/a` / `0.0%`
- Surfaced precision / missed replace rate: `96.7%` / `23.7%`

## Top Configs

| Rank | soft_active | soft_margin | Soft Cnt | Soft True | Soft False | Replace+Soft Recall | Recall Lift | Soft Precision | Soft Noise | Surfaced Precision | Missed Replace |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.60 | 0.00 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 2 | 0.60 | -0.01 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 3 | 0.58 | 0.00 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 4 | 0.58 | -0.01 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 5 | 0.55 | 0.00 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 6 | 0.55 | -0.01 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 7 | 0.52 | 0.00 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 8 | 0.50 | 0.00 | 0 | 0 | 0 | 76.3% | 0.0% | n/a | 0.0% | 96.7% | 9 |
| 9 | 0.52 | -0.01 | 1 | 0 | 1 | 76.3% | 0.0% | 0.0% | 1.8% | 93.5% | 9 |
| 10 | 0.50 | -0.01 | 1 | 0 | 1 | 76.3% | 0.0% | 0.0% | 1.8% | 93.5% | 9 |
| 11 | 0.58 | -0.03 | 5 | 3 | 2 | 84.2% | 7.9% | 60.0% | 3.5% | 91.4% | 6 |
| 12 | 0.60 | -0.03 | 4 | 2 | 2 | 81.6% | 5.3% | 50.0% | 3.5% | 91.2% | 7 |
