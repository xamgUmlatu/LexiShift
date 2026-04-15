# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_a_admission_frontier_v2_83cases_20260329.json`
- pairs_processed: 1
- failing_or_review_count: 8

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square |
| en-es | `en-es:cuenta` | cuenta | FAIL | expected_candidate_missing_from_top3 | count | count, tally |
| en-es | `en-es:red` | red | FAIL | expected_candidate_missing_from_top3 | web | web, mesh |
| en-es | `en-es:señal` | señal | REVIEW | top1_not_in_expected_set | sign | sign |
| en-es | `en-es:archivo` | archivo | REVIEW | top1_not_in_expected_set | archive | archive |
| en-es | `en-es:trama` | trama | REVIEW | top1_not_in_expected_set | weave | weave, weft |
| en-es | `en-es:navegador` | navegador | FAIL | expected_candidate_missing_from_top3 | navigating | navigating |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
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
    "Observed top1 source: square",
    "Observed top3 sources: square"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square"
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

### en-es / en-es:señal
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: sign",
    "Observed top3 sources: sign"
  ],
  "candidate_forbidden_top1": [
    "sign"
  ],
  "candidate_expected_any": [
    "sign"
  ]
}
```

### en-es / en-es:archivo
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: archive",
    "Observed top3 sources: archive"
  ],
  "candidate_forbidden_top1": [
    "archive"
  ],
  "candidate_expected_any": [
    "archive"
  ]
}
```

### en-es / en-es:trama
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: weave",
    "Observed top3 sources: weave, weft"
  ],
  "candidate_forbidden_top1": [
    "weave"
  ],
  "candidate_expected_any": [
    "weave",
    "weft"
  ]
}
```

### en-es / en-es:navegador
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: navigating",
    "Observed top3 sources: navigating"
  ],
  "candidate_forbidden_top1": [
    "navigating"
  ],
  "candidate_expected_any": [
    "navigating"
  ]
}
```
