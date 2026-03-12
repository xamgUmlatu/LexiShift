# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
- pairs_processed: 1
- failing_or_review_count: 3

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:madre` | madre | FAIL | forbidden_candidate_present | mother | mother, bed, watercourse |
| en-es | `en-es:derecho` | derecho | FAIL | forbidden_candidate_present | right | right, claim, straight |
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, picture |

## Suggested Case Patches

### en-es / en-es:madre
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: mother",
    "Observed top3 sources: mother, bed, watercourse"
  ],
  "candidate_forbidden_top1": [
    "mother"
  ],
  "candidate_expected_any": [
    "mother",
    "bed",
    "watercourse"
  ]
}
```

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: right",
    "Observed top3 sources: right, claim, straight"
  ],
  "candidate_forbidden_top1": [
    "right"
  ],
  "candidate_expected_any": [
    "right",
    "claim",
    "straight"
  ]
}
```

### en-es / en-es:cuadro
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed, picture"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "picture"
  ]
}
```
