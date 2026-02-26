# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.json`
- pairs_processed: 2
- failing_or_review_count: 4

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, watercourse, mother |
| en-ja | `en-ja:山` | 山 | FAIL | forbidden_candidate_present | mountain | mountain, hill, mine |
| en-ja | `en-ja:世界` | 世界 | FAIL | forbidden_candidate_present | society | society, sphere, circle |
| en-ja | `en-ja:愛` | 愛 | FAIL | forbidden_candidate_present | love | love, affection, care |

## Suggested Case Patches

### en-es / en-es:madre
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed, watercourse, mother"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "watercourse",
    "mother"
  ]
}
```

### en-ja / en-ja:山
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: mountain",
    "Observed top3 sources: mountain, hill, mine"
  ],
  "candidate_forbidden_top1": [
    "mountain"
  ],
  "candidate_expected_any": [
    "mountain",
    "hill",
    "mine"
  ]
}
```

### en-ja / en-ja:世界
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: society",
    "Observed top3 sources: society, sphere, circle"
  ],
  "candidate_forbidden_top1": [
    "society"
  ],
  "candidate_expected_any": [
    "society",
    "sphere",
    "circle"
  ]
}
```

### en-ja / en-ja:愛
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: love",
    "Observed top3 sources: love, affection, care"
  ],
  "candidate_forbidden_top1": [
    "love"
  ],
  "candidate_expected_any": [
    "love",
    "affection",
    "care"
  ]
}
```
