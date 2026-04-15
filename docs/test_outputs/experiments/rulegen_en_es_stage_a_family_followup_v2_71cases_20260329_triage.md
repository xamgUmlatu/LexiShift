# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_a_family_followup_v2_71cases_20260329.json`
- pairs_processed: 1
- failing_or_review_count: 5

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right |
| en-es | `en-es:cuadro` | cuadro | REVIEW | top1_not_in_expected_set | square | square, picture |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, account |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net |
| en-es | `en-es:señal` | señal | REVIEW | top1_not_in_expected_set | sign | sign, signal |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight, right"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
    "right"
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
    "Observed top3 sources: square, picture"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "picture"
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
    "Observed top3 sources: count, account"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
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
    "Observed top3 sources: web, net"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "net"
  ]
}
```

### en-es / en-es:señal
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: sign",
    "Observed top3 sources: sign, signal"
  ],
  "candidate_forbidden_top1": [
    "sign"
  ],
  "candidate_expected_any": [
    "sign",
    "signal"
  ]
}
```
