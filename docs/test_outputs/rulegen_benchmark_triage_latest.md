# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- pairs_processed: 1
- failing_or_review_count: 36

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:madre` | madre | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, mother, watercourse |
| en-es | `en-es:planta` | planta | FAIL | top1_is_forbidden | sole | sole, plant |
| en-es | `en-es:derecho` | derecho | FAIL | top1_is_forbidden, forbidden_candidate_present | claim | claim, right, presumption |
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present | bed | bed, picture |
| en-es | `en-es:cargo` | cargo | FAIL | top1_is_forbidden, forbidden_candidate_present | accusal | accusal, function, accusation |
| en-es | `en-es:masa` | masa | FAIL | top1_is_forbidden, forbidden_candidate_present | lump | lump, dough, paste |
| en-es | `en-es:caso` | caso | FAIL | top1_is_forbidden | affair | affair, case, matter |
| en-es | `en-es:parte` | parte | FAIL | forbidden_candidate_present | part | part, parthian, share |
| en-es | `en-es:vista` | vista | FAIL | top1_is_forbidden | appearance | appearance, sight, view |
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
| en-es | `en-es:tabla` | tabla | REVIEW | top1_not_in_expected_set | shelf | shelf, board, lath |
| en-es | `en-es:malla` | malla | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:quitar` | quitar | FAIL | expected_candidate_missing_from_top3 | abstract | abstract, takeaway |
| en-es | `en-es:meter` | meter | FAIL | expected_candidate_missing_from_top3 | place | place, put, putdown |
| en-es | `en-es:salir` | salir | REVIEW | top1_not_in_expected_set | exit | exit, depart, goout |
| en-es | `en-es:subir` | subir | REVIEW | top1_not_in_expected_set | ascend | ascend, lift, rise |
| en-es | `en-es:coger` | coger | REVIEW | top1_not_in_expected_set | clutch | clutch, grab, get |
| en-es | `en-es:clave` | clave | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:masa` | masa | REVIEW | top1_not_in_expected_set | lump | lump, dough, paste |
| en-es | `en-es:señal` | señal | REVIEW | top1_not_in_expected_set | mark | mark, signal, sign |
| en-es | `en-es:llevar` | llevar | REVIEW | top1_not_in_expected_set | bring | bring, carry, wear |
| en-es | `en-es:empleo` | empleo | FAIL | expected_candidate_missing_from_top3 | post | post |
| en-es | `en-es:rejilla` | rejilla | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:ocupación` | ocupación | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-es | `en-es:carretera` | carretera | FAIL | expected_candidate_missing_from_top3 | motorway | motorway |
| en-es | `en-es:reja` | reja | FAIL | expected_candidate_missing_from_top3 | barrier | barrier, fence |

## Suggested Case Patches

### en-es / en-es:madre
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed, mother, watercourse"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed",
    "mother",
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
    "Observed top3 sources: claim, right, presumption"
  ],
  "candidate_forbidden_top1": [
    "claim"
  ],
  "candidate_expected_any": [
    "claim",
    "right",
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
    "Observed top3 sources: accusal, function, accusation"
  ],
  "candidate_forbidden_top1": [
    "accusal"
  ],
  "candidate_expected_any": [
    "accusal",
    "function",
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
    "Observed top3 sources: lump, dough, paste"
  ],
  "candidate_forbidden_top1": [
    "lump"
  ],
  "candidate_expected_any": [
    "lump",
    "dough",
    "paste"
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
    "Observed top3 sources: appearance, sight, view"
  ],
  "candidate_forbidden_top1": [
    "appearance"
  ],
  "candidate_expected_any": [
    "appearance",
    "sight",
    "view"
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
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: shelf",
    "Observed top3 sources: shelf, board, lath"
  ],
  "candidate_forbidden_top1": [
    "shelf"
  ],
  "candidate_expected_any": [
    "shelf",
    "board",
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
    "Observed top3 sources: place, put, putdown"
  ],
  "candidate_forbidden_top1": [
    "place"
  ],
  "candidate_expected_any": [
    "place",
    "put",
    "putdown"
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
    "Observed top3 sources: exit, depart, goout"
  ],
  "candidate_forbidden_top1": [
    "exit"
  ],
  "candidate_expected_any": [
    "exit",
    "depart",
    "goout"
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
    "Observed top1 source: ascend",
    "Observed top3 sources: ascend, lift, rise"
  ],
  "candidate_forbidden_top1": [
    "ascend"
  ],
  "candidate_expected_any": [
    "ascend",
    "lift",
    "rise"
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
    "Observed top3 sources: clutch, grab, get"
  ],
  "candidate_forbidden_top1": [
    "clutch"
  ],
  "candidate_expected_any": [
    "clutch",
    "grab",
    "get"
  ]
}
```

### en-es / en-es:clave
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:masa
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: lump",
    "Observed top3 sources: lump, dough, paste"
  ],
  "candidate_forbidden_top1": [
    "lump"
  ],
  "candidate_expected_any": [
    "lump",
    "dough",
    "paste"
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
    "Observed top1 source: mark",
    "Observed top3 sources: mark, signal, sign"
  ],
  "candidate_forbidden_top1": [
    "mark"
  ],
  "candidate_expected_any": [
    "mark",
    "signal",
    "sign"
  ]
}
```

### en-es / en-es:llevar
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: bring",
    "Observed top3 sources: bring, carry, wear"
  ],
  "candidate_forbidden_top1": [
    "bring"
  ],
  "candidate_expected_any": [
    "bring",
    "carry",
    "wear"
  ]
}
```

### en-es / en-es:empleo
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: post",
    "Observed top3 sources: post"
  ],
  "candidate_forbidden_top1": [
    "post"
  ],
  "candidate_expected_any": [
    "post"
  ]
}
```

### en-es / en-es:rejilla
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:ocupación
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-es / en-es:carretera
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: motorway",
    "Observed top3 sources: motorway"
  ],
  "candidate_forbidden_top1": [
    "motorway"
  ],
  "candidate_expected_any": [
    "motorway"
  ]
}
```

### en-es / en-es:reja
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: barrier",
    "Observed top3 sources: barrier, fence"
  ],
  "candidate_forbidden_top1": [
    "barrier"
  ],
  "candidate_expected_any": [
    "barrier",
    "fence"
  ]
}
```
