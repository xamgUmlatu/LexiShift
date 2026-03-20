# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json`
- pairs_processed: 4
- failing_or_review_count: 17

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Haus` | Haus | REVIEW | top1_not_in_expected_set | establishment | establishment, institution, house |
| en-de | `en-de:Schule` | Schule | REVIEW | top1_not_in_expected_set | pod | pod, school, group |
| en-de | `en-de:Weg` | Weg | REVIEW | top1_not_in_expected_set | alley | alley, way, walk |
| en-de | `en-de:Zeit` | Zeit | REVIEW | top1_not_in_expected_set | spell | spell, time, faff |
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | bed | bed |
| en-es | `en-es:planta` | planta | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | sole | sole |
| en-es | `en-es:derecho` | derecho | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | claim | claim |
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | bed | bed |
| en-es | `en-es:cargo` | cargo | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | accusal | accusal |
| en-es | `en-es:masa` | masa | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | lump | lump |
| en-es | `en-es:caso` | caso | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | affair | affair |
| en-es | `en-es:vista` | vista | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | appearance | appearance |
| en-ja | `en-ja:世界` | 世界 | REVIEW | top1_not_in_expected_set | society | society |
| es-en | `es-en:house` | house | FAIL | expected_candidate_missing_from_top3 | casalicio | casalicio |
| es-en | `es-en:love` | love | FAIL | expected_candidate_missing_from_top3 | cero | cero |
| es-en | `es-en:money` | money | FAIL | expected_candidate_missing_from_top3 | pasta | pasta |
| es-en | `es-en:time` | time | FAIL | expected_candidate_missing_from_top3 | mes | mes |

## Suggested Case Patches

### en-de / en-de:Haus
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: establishment",
    "Observed top3 sources: establishment, institution, house"
  ],
  "candidate_forbidden_top1": [
    "establishment"
  ],
  "candidate_expected_any": [
    "establishment",
    "institution",
    "house"
  ]
}
```

### en-de / en-de:Schule
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: pod",
    "Observed top3 sources: pod, school, group"
  ],
  "candidate_forbidden_top1": [
    "pod"
  ],
  "candidate_expected_any": [
    "pod",
    "school",
    "group"
  ]
}
```

### en-de / en-de:Weg
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: alley",
    "Observed top3 sources: alley, way, walk"
  ],
  "candidate_forbidden_top1": [
    "alley"
  ],
  "candidate_expected_any": [
    "alley",
    "way",
    "walk"
  ]
}
```

### en-de / en-de:Zeit
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: spell",
    "Observed top3 sources: spell, time, faff"
  ],
  "candidate_forbidden_top1": [
    "spell"
  ],
  "candidate_expected_any": [
    "spell",
    "time",
    "faff"
  ]
}
```

### en-es / en-es:madre
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed"
  ]
}
```

### en-es / en-es:planta
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: sole",
    "Observed top3 sources: sole"
  ],
  "candidate_forbidden_top1": [
    "sole"
  ],
  "candidate_expected_any": [
    "sole"
  ]
}
```

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: claim",
    "Observed top3 sources: claim"
  ],
  "candidate_forbidden_top1": [
    "claim"
  ],
  "candidate_expected_any": [
    "claim"
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
    "Observed top1 source: bed",
    "Observed top3 sources: bed"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed"
  ]
}
```

### en-es / en-es:cargo
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: accusal",
    "Observed top3 sources: accusal"
  ],
  "candidate_forbidden_top1": [
    "accusal"
  ],
  "candidate_expected_any": [
    "accusal"
  ]
}
```

### en-es / en-es:masa
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: lump",
    "Observed top3 sources: lump"
  ],
  "candidate_forbidden_top1": [
    "lump"
  ],
  "candidate_expected_any": [
    "lump"
  ]
}
```

### en-es / en-es:caso
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: affair",
    "Observed top3 sources: affair"
  ],
  "candidate_forbidden_top1": [
    "affair"
  ],
  "candidate_expected_any": [
    "affair"
  ]
}
```

### en-es / en-es:vista
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: appearance",
    "Observed top3 sources: appearance"
  ],
  "candidate_forbidden_top1": [
    "appearance"
  ],
  "candidate_expected_any": [
    "appearance"
  ]
}
```

### en-ja / en-ja:世界
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: society",
    "Observed top3 sources: society"
  ],
  "candidate_forbidden_top1": [
    "society"
  ],
  "candidate_expected_any": [
    "society"
  ]
}
```

### es-en / es-en:house
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: casalicio",
    "Observed top3 sources: casalicio"
  ],
  "candidate_forbidden_top1": [
    "casalicio"
  ],
  "candidate_expected_any": [
    "casalicio"
  ]
}
```

### es-en / es-en:love
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: cero",
    "Observed top3 sources: cero"
  ],
  "candidate_forbidden_top1": [
    "cero"
  ],
  "candidate_expected_any": [
    "cero"
  ]
}
```

### es-en / es-en:money
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: pasta",
    "Observed top3 sources: pasta"
  ],
  "candidate_forbidden_top1": [
    "pasta"
  ],
  "candidate_expected_any": [
    "pasta"
  ]
}
```

### es-en / es-en:time
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: mes",
    "Observed top3 sources: mes"
  ],
  "candidate_forbidden_top1": [
    "mes"
  ],
  "candidate_expected_any": [
    "mes"
  ]
}
```
