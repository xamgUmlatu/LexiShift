# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.json`
- pairs_processed: 1
- failing_or_review_count: 5

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right, upright |
| en-es | `en-es:cuadro` | cuadro | REVIEW | top1_not_in_expected_set | square | square, rectangle, table |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, account, operation |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net, network |
| en-es | `en-es:sacar` | sacar | FAIL | expected_candidate_missing_from_top3 | withdraw | withdraw |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight, right, upright"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
    "right",
    "upright"
  ]
}
```

### en-es / en-es:cuadro
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: square",
    "Observed top3 sources: square, rectangle, table"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "rectangle",
    "table"
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
    "Observed top3 sources: count, account, operation"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "account",
    "operation"
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
    "Observed top3 sources: web, net, network"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "net",
    "network"
  ]
}
```

### en-es / en-es:sacar
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: withdraw",
    "Observed top3 sources: withdraw"
  ],
  "candidate_forbidden_top1": [
    "withdraw"
  ],
  "candidate_expected_any": [
    "withdraw"
  ]
}
```
