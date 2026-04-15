# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_ja_demotion_off_single_20260408.json`
- pairs_processed: 1
- failing_or_review_count: 7

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-ja | `en-ja:先生` | 先生 | FAIL | expected_candidate_missing_from_top3 | elder | elder |
| en-ja | `en-ja:本` | 本 | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | jeans | jeans |
| en-ja | `en-ja:犬` | 犬 | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | radical | radical |
| en-ja | `en-ja:雪` | 雪 | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | hair | hair |
| en-ja | `en-ja:飲む` | 飲む | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-ja | `en-ja:売る` | 売る | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | betray | betray |
| en-ja | `en-ja:分かる` | 分かる | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |

## Suggested Case Patches

### en-ja / en-ja:先生
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: elder",
    "Observed top3 sources: elder"
  ],
  "candidate_forbidden_top1": [
    "elder"
  ],
  "candidate_expected_any": [
    "elder"
  ]
}
```

### en-ja / en-ja:本
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: jeans",
    "Observed top3 sources: jeans"
  ],
  "candidate_forbidden_top1": [
    "jeans"
  ],
  "candidate_expected_any": [
    "jeans"
  ]
}
```

### en-ja / en-ja:犬
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: radical",
    "Observed top3 sources: radical"
  ],
  "candidate_forbidden_top1": [
    "radical"
  ],
  "candidate_expected_any": [
    "radical"
  ]
}
```

### en-ja / en-ja:雪
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: hair",
    "Observed top3 sources: hair"
  ],
  "candidate_forbidden_top1": [
    "hair"
  ],
  "candidate_expected_any": [
    "hair"
  ]
}
```

### en-ja / en-ja:飲む
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-ja / en-ja:売る
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: betray",
    "Observed top3 sources: betray"
  ],
  "candidate_forbidden_top1": [
    "betray"
  ],
  "candidate_expected_any": [
    "betray"
  ]
}
```

### en-ja / en-ja:分かる
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```
