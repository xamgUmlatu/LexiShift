# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_kaikki_noreverse_current_latest.json`
- pairs_processed: 1
- failing_or_review_count: 12

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square, rectangle, frame |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | operation | operation, bill, tab |
| en-es | `en-es:cargo` | cargo | REVIEW | top1_not_in_expected_set | debit | debit, charge, higher-up |
| en-es | `en-es:plaza` | plaza | FAIL | expected_candidate_missing_from_top3 | position | position, bullring |
| en-es | `en-es:parte` | parte | FAIL | expected_candidate_missing_from_top3 | side | side, party, behalf |
| en-es | `en-es:presentar` | presentar | FAIL | expected_candidate_missing_from_top3 | table | table |
| en-es | `en-es:ocurrir` | ocurrir | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:sacar` | sacar | REVIEW | top1_not_in_expected_set | take | take, lift, draw |
| en-es | `en-es:ese` | ese | FAIL | expected_candidate_missing_from_top3 | hello | hello |
| en-es | `en-es:hasta` | hasta | REVIEW | top1_not_in_expected_set | even | even, until |
| en-es | `en-es:según` | según | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |

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
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: square",
    "Observed top3 sources: square, rectangle, frame"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "rectangle",
    "frame"
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
    "Observed top1 source: operation",
    "Observed top3 sources: operation, bill, tab"
  ],
  "candidate_forbidden_top1": [
    "operation"
  ],
  "candidate_expected_any": [
    "operation",
    "bill",
    "tab"
  ]
}
```

### en-es / en-es:cargo
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: debit",
    "Observed top3 sources: debit, charge, higher-up"
  ],
  "candidate_forbidden_top1": [
    "debit"
  ],
  "candidate_expected_any": [
    "debit",
    "charge",
    "higher-up"
  ]
}
```

### en-es / en-es:plaza
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: position",
    "Observed top3 sources: position, bullring"
  ],
  "candidate_forbidden_top1": [
    "position"
  ],
  "candidate_expected_any": [
    "position",
    "bullring"
  ]
}
```

### en-es / en-es:parte
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: side",
    "Observed top3 sources: side, party, behalf"
  ],
  "candidate_forbidden_top1": [
    "side"
  ],
  "candidate_expected_any": [
    "side",
    "party",
    "behalf"
  ]
}
```

### en-es / en-es:presentar
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: table",
    "Observed top3 sources: table"
  ],
  "candidate_forbidden_top1": [
    "table"
  ],
  "candidate_expected_any": [
    "table"
  ]
}
```

### en-es / en-es:ocurrir
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
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
    "Observed top1 source: take",
    "Observed top3 sources: take, lift, draw"
  ],
  "candidate_forbidden_top1": [
    "take"
  ],
  "candidate_expected_any": [
    "take",
    "lift",
    "draw"
  ]
}
```

### en-es / en-es:ese
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: hello",
    "Observed top3 sources: hello"
  ],
  "candidate_forbidden_top1": [
    "hello"
  ],
  "candidate_expected_any": [
    "hello"
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

### en-es / en-es:según
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```
