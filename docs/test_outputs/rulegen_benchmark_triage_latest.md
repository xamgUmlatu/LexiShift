# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- pairs_processed: 1
- failing_or_review_count: 11

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, watercourse, mother |
| en-es | `en-es:planta` | planta | FAIL | top1_is_forbidden | sole | sole, plant |
| en-es | `en-es:derecho` | derecho | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | claim | claim, presumption, pretence |
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, picture |
| en-es | `en-es:orden` | orden | FAIL | forbidden_candidate_present | order | order, warrant, writ |
| en-es | `en-es:cargo` | cargo | FAIL | top1_is_forbidden, forbidden_candidate_present | accusal | accusal, accusation, function |
| en-es | `en-es:plaza` | plaza | FAIL | forbidden_candidate_present | plaza | plaza, square, publicsquare |
| en-es | `en-es:masa` | masa | FAIL | top1_is_forbidden, forbidden_candidate_present | lump | lump, mass, dough |
| en-es | `en-es:caso` | caso | FAIL | top1_is_forbidden | affair | affair, case, matter |
| en-es | `en-es:parte` | parte | FAIL | forbidden_candidate_present | part | part, parthian, share |
| en-es | `en-es:vista` | vista | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | appearance | appearance, aspect, look |

## Suggested Case Patches

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

### en-es / en-es:planta
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: sole",
    "Observed top3 sources: sole, plant"
  ],
  "candidate_forbidden_top1": [
    "sole"
  ],
  "candidate_expected_any": [
    "sole",
    "plant"
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
    "Observed top3 sources: claim, presumption, pretence"
  ],
  "candidate_forbidden_top1": [
    "claim"
  ],
  "candidate_expected_any": [
    "claim",
    "presumption",
    "pretence"
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
    "Observed top3 sources: bed, picture"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "picture"
  ]
}
```

### en-es / en-es:orden
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: order",
    "Observed top3 sources: order, warrant, writ"
  ],
  "candidate_forbidden_top1": [
    "order"
  ],
  "candidate_expected_any": [
    "order",
    "warrant",
    "writ"
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
    "Observed top3 sources: accusal, accusation, function"
  ],
  "candidate_forbidden_top1": [
    "accusal"
  ],
  "candidate_expected_any": [
    "accusal",
    "accusation",
    "function"
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
    "Observed top1 source: plaza",
    "Observed top3 sources: plaza, square, publicsquare"
  ],
  "candidate_forbidden_top1": [
    "plaza"
  ],
  "candidate_expected_any": [
    "plaza",
    "square",
    "publicsquare"
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
    "Observed top3 sources: lump, mass, dough"
  ],
  "candidate_forbidden_top1": [
    "lump"
  ],
  "candidate_expected_any": [
    "lump",
    "mass",
    "dough"
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
    "Observed top3 sources: affair, case, matter"
  ],
  "candidate_forbidden_top1": [
    "affair"
  ],
  "candidate_expected_any": [
    "affair",
    "case",
    "matter"
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
    "Observed top1 source: part",
    "Observed top3 sources: part, parthian, share"
  ],
  "candidate_forbidden_top1": [
    "part"
  ],
  "candidate_expected_any": [
    "part",
    "parthian",
    "share"
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
    "Observed top3 sources: appearance, aspect, look"
  ],
  "candidate_forbidden_top1": [
    "appearance"
  ],
  "candidate_expected_any": [
    "appearance",
    "aspect",
    "look"
  ]
}
```
