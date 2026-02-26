# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_polysemic_demotion_latest.json`
- pairs_processed: 4
- failing_or_review_count: 12

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Haus` | Haus | REVIEW | top1_not_in_expected_set | establishment | establishment, institution, house |
| en-de | `en-de:Schule` | Schule | REVIEW | top1_not_in_expected_set | pod | pod, school, group |
| en-de | `en-de:Weg` | Weg | REVIEW | top1_not_in_expected_set | alley | alley, way, walk |
| en-de | `en-de:Zeit` | Zeit | REVIEW | top1_not_in_expected_set | spell | spell, time, faff |
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, watercourse, mother |
| en-ja | `en-ja:山` | 山 | FAIL | forbidden_candidate_present | mountain | mountain, hill, mine |
| en-ja | `en-ja:世界` | 世界 | FAIL | forbidden_candidate_present | society | society, sphere, circle |
| en-ja | `en-ja:愛` | 愛 | FAIL | forbidden_candidate_present | love | love, affection, care |
| es-en | `es-en:house` | house | REVIEW | top1_not_in_expected_set | casalicio | casalicio, casa, teatro |
| es-en | `es-en:love` | love | REVIEW | top1_not_in_expected_set | cero | cero, nada, amor |
| es-en | `es-en:money` | money | FAIL | expected_candidate_missing_from_top3 | pasta | pasta, cobres, lana |
| es-en | `es-en:time` | time | FAIL | expected_candidate_missing_from_top3 | mes | mes, semestre, temporada |

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
    "Observed top3 sources: bed, watercourse, mother"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "watercourse",
    "mother"
  ]
}
```

### en-ja / en-ja:山
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: mountain",
    "Observed top3 sources: mountain, hill, mine"
  ],
  "candidate_forbidden_top1": [
    "mountain"
  ],
  "candidate_expected_any": [
    "mountain",
    "hill",
    "mine"
  ]
}
```

### en-ja / en-ja:世界
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: society",
    "Observed top3 sources: society, sphere, circle"
  ],
  "candidate_forbidden_top1": [
    "society"
  ],
  "candidate_expected_any": [
    "society",
    "sphere",
    "circle"
  ]
}
```

### en-ja / en-ja:愛
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: love",
    "Observed top3 sources: love, affection, care"
  ],
  "candidate_forbidden_top1": [
    "love"
  ],
  "candidate_expected_any": [
    "love",
    "affection",
    "care"
  ]
}
```

### es-en / es-en:house
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: casalicio",
    "Observed top3 sources: casalicio, casa, teatro"
  ],
  "candidate_forbidden_top1": [
    "casalicio"
  ],
  "candidate_expected_any": [
    "casalicio",
    "casa",
    "teatro"
  ]
}
```

### es-en / es-en:love
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: cero",
    "Observed top3 sources: cero, nada, amor"
  ],
  "candidate_forbidden_top1": [
    "cero"
  ],
  "candidate_expected_any": [
    "cero",
    "nada",
    "amor"
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
    "Observed top3 sources: pasta, cobres, lana"
  ],
  "candidate_forbidden_top1": [
    "pasta"
  ],
  "candidate_expected_any": [
    "pasta",
    "cobres",
    "lana"
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
    "Observed top3 sources: mes, semestre, temporada"
  ],
  "candidate_forbidden_top1": [
    "mes"
  ],
  "candidate_expected_any": [
    "mes",
    "semestre",
    "temporada"
  ]
}
```
