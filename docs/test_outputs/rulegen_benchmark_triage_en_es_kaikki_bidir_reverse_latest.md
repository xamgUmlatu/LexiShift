# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_reverse_latest.json`
- pairs_processed: 1
- failing_or_review_count: 9

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right |
| en-es | `en-es:cuadro` | cuadro | FAIL | expected_candidate_missing_from_top3 | square | square |
| en-es | `en-es:plaza` | plaza | FAIL | expected_candidate_missing_from_top3 | bullring | bullring, position |
| en-es | `en-es:parte` | parte | FAIL | expected_candidate_missing_from_top3 | behalf | behalf, party, side |
| en-es | `en-es:presentar` | presentar | FAIL | expected_candidate_missing_from_top3 | table | table |
| en-es | `en-es:ocurrir` | ocurrir | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:sacar` | sacar | REVIEW | top1_not_in_expected_set | draw | draw, lift, make |
| en-es | `en-es:ese` | ese | FAIL | expected_candidate_missing_from_top3 | hello | hello |
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

### en-es / en-es:plaza
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bullring",
    "Observed top3 sources: bullring, position"
  ],
  "candidate_forbidden_top1": [
    "bullring"
  ],
  "candidate_expected_any": [
    "bullring",
    "position"
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
    "Observed top1 source: behalf",
    "Observed top3 sources: behalf, party, side"
  ],
  "candidate_forbidden_top1": [
    "behalf"
  ],
  "candidate_expected_any": [
    "behalf",
    "party",
    "side"
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
    "Observed top1 source: draw",
    "Observed top3 sources: draw, lift, make"
  ],
  "candidate_forbidden_top1": [
    "draw"
  ],
  "candidate_expected_any": [
    "draw",
    "lift",
    "make"
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
