# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_es_stage_a_combined_frontier_v1_100cases_20260329.json`
- pairs_processed: 1
- failing_or_review_count: 12

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right, right-hand |
| en-es | `en-es:cuadro` | cuadro | REVIEW | top1_not_in_expected_set | square | square, picture |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, tally, account |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net, mesh |
| en-es | `en-es:señal` | señal | REVIEW | top1_not_in_expected_set | sign | sign, signal |
| en-es | `en-es:archivo` | archivo | REVIEW | top1_not_in_expected_set | archive | archive, file |
| en-es | `en-es:trama` | trama | REVIEW | top1_not_in_expected_set | weave | weave, weft, plot |
| en-es | `en-es:navegador` | navegador | REVIEW | top1_not_in_expected_set | navigating | navigating, navigator |
| en-es | `en-es:móvil` | móvil | REVIEW | top1_not_in_expected_set | mobile | mobile, mobile phone, cellular |
| en-es | `en-es:registro` | registro | REVIEW | top1_not_in_expected_set | registration | registration, record, register |
| en-es | `en-es:patrón` | patrón | REVIEW | top1_not_in_expected_set | patron | patron, pattern |
| en-es | `en-es:mando` | mando | REVIEW | top1_not_in_expected_set | command | command, gamepad, controller |

## Suggested Case Patches

### en-es / en-es:derecho
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: straight",
    "Observed top3 sources: straight, right, right-hand"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
    "right",
    "right-hand"
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
    "Observed top3 sources: count, tally, account"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "tally",
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
    "Observed top3 sources: web, net, mesh"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "net",
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

### en-es / en-es:archivo
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: archive",
    "Observed top3 sources: archive, file"
  ],
  "candidate_forbidden_top1": [
    "archive"
  ],
  "candidate_expected_any": [
    "archive",
    "file"
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
    "Observed top3 sources: weave, weft, plot"
  ],
  "candidate_forbidden_top1": [
    "weave"
  ],
  "candidate_expected_any": [
    "weave",
    "weft",
    "plot"
  ]
}
```

### en-es / en-es:navegador
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: navigating",
    "Observed top3 sources: navigating, navigator"
  ],
  "candidate_forbidden_top1": [
    "navigating"
  ],
  "candidate_expected_any": [
    "navigating",
    "navigator"
  ]
}
```

### en-es / en-es:móvil
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: mobile",
    "Observed top3 sources: mobile, mobile phone, cellular"
  ],
  "candidate_forbidden_top1": [
    "mobile"
  ],
  "candidate_expected_any": [
    "mobile",
    "mobile phone",
    "cellular"
  ]
}
```

### en-es / en-es:registro
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: registration",
    "Observed top3 sources: registration, record, register"
  ],
  "candidate_forbidden_top1": [
    "registration"
  ],
  "candidate_expected_any": [
    "registration",
    "record",
    "register"
  ]
}
```

### en-es / en-es:patrón
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: patron",
    "Observed top3 sources: patron, pattern"
  ],
  "candidate_forbidden_top1": [
    "patron"
  ],
  "candidate_expected_any": [
    "patron",
    "pattern"
  ]
}
```

### en-es / en-es:mando
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: command",
    "Observed top3 sources: command, gamepad, controller"
  ],
  "candidate_forbidden_top1": [
    "command"
  ],
  "candidate_expected_any": [
    "command",
    "gamepad",
    "controller"
  ]
}
```
