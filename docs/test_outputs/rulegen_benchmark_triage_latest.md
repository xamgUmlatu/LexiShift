# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\rulegen_benchmark_en_es_latest.json`
- pairs_processed: 1
- failing_or_review_count: 11

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:derecho` | derecho | REVIEW | top1_not_in_expected_set | straight | straight, right, upright |
| en-es | `en-es:cuadro` | cuadro | REVIEW | top1_not_in_expected_set | square | square, picture, frame |
| en-es | `en-es:cuenta` | cuenta | REVIEW | top1_not_in_expected_set | count | count, account, bead |
| en-es | `en-es:red` | red | REVIEW | top1_not_in_expected_set | web | web, net, network |
| en-es | `en-es:señal` | señal | REVIEW | top1_not_in_expected_set | sign | sign, signal |
| en-es | `en-es:archivo` | archivo | REVIEW | top1_not_in_expected_set | archive | archive, file |
| en-es | `en-es:trama` | trama | REVIEW | top1_not_in_expected_set | weave | weave, plot, grid |
| en-es | `en-es:navegador` | navegador | REVIEW | top1_not_in_expected_set | navigating | navigating, navigator, browser |
| en-es | `en-es:registro` | registro | REVIEW | top1_not_in_expected_set | registration | registration, register, entry |
| en-es | `en-es:patrón` | patrón | REVIEW | top1_not_in_expected_set | patron | patron, boss, pattern |
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
    "Observed top3 sources: straight, right, upright"
  ],
  "candidate_forbidden_top1": [
    "straight"
  ],
  "candidate_expected_any": [
    "straight",
    "right",
    "upright"
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
    "Observed top3 sources: square, picture, frame"
  ],
  "candidate_forbidden_top1": [
    "square"
  ],
  "candidate_expected_any": [
    "square",
    "picture",
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
    "Observed top1 source: count",
    "Observed top3 sources: count, account, bead"
  ],
  "candidate_forbidden_top1": [
    "count"
  ],
  "candidate_expected_any": [
    "count",
    "account",
    "bead"
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
    "Observed top3 sources: web, net, network"
  ],
  "candidate_forbidden_top1": [
    "web"
  ],
  "candidate_expected_any": [
    "web",
    "net",
    "network"
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
    "Observed top3 sources: weave, plot, grid"
  ],
  "candidate_forbidden_top1": [
    "weave"
  ],
  "candidate_expected_any": [
    "weave",
    "plot",
    "grid"
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
    "Observed top3 sources: navigating, navigator, browser"
  ],
  "candidate_forbidden_top1": [
    "navigating"
  ],
  "candidate_expected_any": [
    "navigating",
    "navigator",
    "browser"
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
    "Observed top3 sources: registration, register, entry"
  ],
  "candidate_forbidden_top1": [
    "registration"
  ],
  "candidate_expected_any": [
    "registration",
    "register",
    "entry"
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
    "Observed top3 sources: patron, boss, pattern"
  ],
  "candidate_forbidden_top1": [
    "patron"
  ],
  "candidate_expected_any": [
    "patron",
    "boss",
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
