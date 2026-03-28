# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_a_combined_frontier_v1_64cases_20260328.json`
- pairs_processed: 1
- failing_or_review_count: 6

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right, right-hand |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square, rectangle |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, tally, account |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net, mesh |
| en-es | `en-es:sacar` | sacar | REVIEW | top1_not_in_expected_set | withdraw | withdraw, draw, unsheathe |
| en-es | `en-es:batería` | batería | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | drummer | drummer, set |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight, right, right-hand"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
    "right",
    "right-hand"
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
    "Observed top1 source: square",
    "Observed top3 sources: square, rectangle"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "rectangle"
  ]
}
```

### en-es / en-es:cuenta
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: count",
    "Observed top3 sources: count, tally, account"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "tally",
    "account"
  ]
}
```

### en-es / en-es:red
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: web",
    "Observed top3 sources: web, net, mesh"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "net",
    "mesh"
  ]
}
```

### en-es / en-es:sacar
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: withdraw",
    "Observed top3 sources: withdraw, draw, unsheathe"
  ],
  "candidate_forbidden_top1": [
    "withdraw"
  ],
  "candidate_expected_any": [
    "withdraw",
    "draw",
    "unsheathe"
  ]
}
```

### en-es / en-es:batería
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: drummer",
    "Observed top3 sources: drummer, set"
  ],
  "candidate_forbidden_top1": [
    "drummer"
  ],
  "candidate_expected_any": [
    "drummer",
    "set"
  ]
}
```
