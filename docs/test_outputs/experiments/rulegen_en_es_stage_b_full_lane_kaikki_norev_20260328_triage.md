# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_b_full_lane_kaikki_norev_20260328.json`
- pairs_processed: 1
- failing_or_review_count: 7

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, upright |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square, rectangle |
| en-es | `en-es:cuenta` | cuenta | FAIL | expected_candidate_missing_from_top3 | count | count, tally |
| en-es | `en-es:red` | red | FAIL | expected_candidate_missing_from_top3 | web | web, mesh |
| en-es | `en-es:sacar` | sacar | FAIL | expected_candidate_missing_from_top3 | take | take, withdraw |
| en-es | `en-es:hasta` | hasta | REVIEW | top1_not_in_expected_set | even | even, until |
| en-es | `en-es:subir` | subir | REVIEW | top1_not_in_expected_set | raise | raise, climb |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight, upright"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
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
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: count",
    "Observed top3 sources: count, tally"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "tally"
  ]
}
```

### en-es / en-es:red
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: web",
    "Observed top3 sources: web, mesh"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "mesh"
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
    "Observed top1 source: take",
    "Observed top3 sources: take, withdraw"
  ],
  "candidate_forbidden_top1": [
    "take"
  ],
  "candidate_expected_any": [
    "take",
    "withdraw"
  ]
}
```

### en-es / en-es:hasta
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: even",
    "Observed top3 sources: even, until"
  ],
  "candidate_forbidden_top1": [
    "even"
  ],
  "candidate_expected_any": [
    "even",
    "until"
  ]
}
```

### en-es / en-es:subir
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: raise",
    "Observed top3 sources: raise, climb"
  ],
  "candidate_forbidden_top1": [
    "raise"
  ],
  "candidate_expected_any": [
    "raise",
    "climb"
  ]
}
```
