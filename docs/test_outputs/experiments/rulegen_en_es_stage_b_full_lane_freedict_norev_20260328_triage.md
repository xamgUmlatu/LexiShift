# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_b_full_lane_freedict_norev_20260328.json`
- pairs_processed: 1
- failing_or_review_count: 27

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | bed | bed, watercourse |
| en-es | `en-es:planta` | planta | FAIL | top1_is_forbidden | sole | sole, plant |
| en-es | `en-es:derecho` | derecho | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | claim | claim, presumption |
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, picture |
| en-es | `en-es:cargo` | cargo | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | accusal | accusal, accusation |
| en-es | `en-es:masa` | masa | FAIL | top1_is_forbidden, forbidden_candidate_present | lump | lump, mass |
| en-es | `en-es:caso` | caso | FAIL | top1_is_forbidden | affair | affair, case |
| en-es | `en-es:parte` | parte | FAIL | forbidden_candidate_present | part | part, parthian |
| en-es | `en-es:vista` | vista | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | appearance | appearance, aspect |
| en-es | `en-es:movimiento` | movimiento | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:área` | área | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:estilo` | estilo | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:presentar` | presentar | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:crear` | crear | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:ocurrir` | ocurrir | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:sacar` | sacar | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:ese` | ese | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:hasta` | hasta | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:según` | según | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:marco` | marco | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:tabla` | tabla | FAIL | expected_candidate_missing_from_top3 | shelf | shelf, lath |
| en-es | `en-es:malla` | malla | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:quitar` | quitar | FAIL | expected_candidate_missing_from_top3 | abstract | abstract, takeaway |
| en-es | `en-es:meter` | meter | FAIL | expected_candidate_missing_from_top3 | place | place, put |
| en-es | `en-es:salir` | salir | REVIEW | top1_not_in_expected_set | exit | exit, goout |
| en-es | `en-es:subir` | subir | FAIL | expected_candidate_missing_from_top3 | ascend | ascend, lift |
| en-es | `en-es:coger` | coger | REVIEW | top1_not_in_expected_set | clutch | clutch, grab |

## Suggested Case Patches

### en-es / en-es:madre
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed, watercourse"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "watercourse"
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
    "Observed top3 sources: claim, presumption"
  ],
  "candidate_forbidden_top1": [
    "claim"
  ],
  "candidate_expected_any": [
    "claim",
    "presumption"
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

### en-es / en-es:cargo
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: accusal",
    "Observed top3 sources: accusal, accusation"
  ],
  "candidate_forbidden_top1": [
    "accusal"
  ],
  "candidate_expected_any": [
    "accusal",
    "accusation"
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
    "Observed top3 sources: lump, mass"
  ],
  "candidate_forbidden_top1": [
    "lump"
  ],
  "candidate_expected_any": [
    "lump",
    "mass"
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
    "Observed top3 sources: affair, case"
  ],
  "candidate_forbidden_top1": [
    "affair"
  ],
  "candidate_expected_any": [
    "affair",
    "case"
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
    "Observed top3 sources: part, parthian"
  ],
  "candidate_forbidden_top1": [
    "part"
  ],
  "candidate_expected_any": [
    "part",
    "parthian"
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
    "Observed top3 sources: appearance, aspect"
  ],
  "candidate_forbidden_top1": [
    "appearance"
  ],
  "candidate_expected_any": [
    "appearance",
    "aspect"
  ]
}
```

### en-es / en-es:movimiento
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:área
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:estilo
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:presentar
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:crear
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
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
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:ese
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:hasta
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
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

### en-es / en-es:marco
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:tabla
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: shelf",
    "Observed top3 sources: shelf, lath"
  ],
  "candidate_forbidden_top1": [
    "shelf"
  ],
  "candidate_expected_any": [
    "shelf",
    "lath"
  ]
}
```

### en-es / en-es:malla
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:quitar
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: abstract",
    "Observed top3 sources: abstract, takeaway"
  ],
  "candidate_forbidden_top1": [
    "abstract"
  ],
  "candidate_expected_any": [
    "abstract",
    "takeaway"
  ]
}
```

### en-es / en-es:meter
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: place",
    "Observed top3 sources: place, put"
  ],
  "candidate_forbidden_top1": [
    "place"
  ],
  "candidate_expected_any": [
    "place",
    "put"
  ]
}
```

### en-es / en-es:salir
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: exit",
    "Observed top3 sources: exit, goout"
  ],
  "candidate_forbidden_top1": [
    "exit"
  ],
  "candidate_expected_any": [
    "exit",
    "goout"
  ]
}
```

### en-es / en-es:subir
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: ascend",
    "Observed top3 sources: ascend, lift"
  ],
  "candidate_forbidden_top1": [
    "ascend"
  ],
  "candidate_expected_any": [
    "ascend",
    "lift"
  ]
}
```

### en-es / en-es:coger
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: clutch",
    "Observed top3 sources: clutch, grab"
  ],
  "candidate_forbidden_top1": [
    "clutch"
  ],
  "candidate_expected_any": [
    "clutch",
    "grab"
  ]
}
```
