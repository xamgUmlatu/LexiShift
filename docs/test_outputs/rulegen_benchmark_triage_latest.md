# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- pairs_processed: 1
- failing_or_review_count: 8

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right, upright |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square, frame, rectangle |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, account, bead |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net, network |
| en-es | `en-es:sacar` | sacar | REVIEW | top1_not_in_expected_set | withdraw | withdraw, draw, unsheathe |
| en-es | `en-es:acabar` | acabar | FAIL | forbidden_candidate_present | finish | finish, cum, exhaust |
| en-es | `en-es:coger` | coger | FAIL | forbidden_candidate_present | take | take, fuck, catch |
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
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: square",
    "Observed top3 sources: square, frame, rectangle"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "frame",
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
    "Observed top3 sources: count, account, bead"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "account",
    "bead"
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

### en-es / en-es:acabar
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: finish",
    "Observed top3 sources: finish, cum, exhaust"
  ],
  "candidate_forbidden_top1": [
    "finish"
  ],
  "candidate_expected_any": [
    "finish",
    "cum",
    "exhaust"
  ]
}
```

### en-es / en-es:coger
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: take",
    "Observed top3 sources: take, fuck, catch"
  ],
  "candidate_forbidden_top1": [
    "take"
  ],
  "candidate_expected_any": [
    "take",
    "fuck",
    "catch"
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
