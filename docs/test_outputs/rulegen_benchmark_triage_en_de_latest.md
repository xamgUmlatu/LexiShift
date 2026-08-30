# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- pairs_processed: 1
- failing_or_review_count: 12

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Schule` | Schule | FAIL | forbidden_candidate_present | school | school, group, pod |
| en-de | `en-de:Zeit` | Zeit | FAIL | forbidden_candidate_present | time | time, spell, most |
| en-de | `en-de:Fenster` | Fenster | FAIL | forbidden_candidate_present | box | box, window, out |
| en-de | `en-de:Tag` | Tag | FAIL | forbidden_candidate_present | day | day, tag, most |
| en-de | `en-de:Kopf` | Kopf | FAIL | forbidden_candidate_present | mind | mind, head, spirit |
| en-de | `en-de:Ohr` | Ohr | FAIL | forbidden_candidate_present | hearing | hearing, ear, audition |
| en-de | `en-de:Fuß` | Fuß | FAIL | forbidden_candidate_present | base | base, head, foot |
| en-de | `en-de:Straße` | Straße | REVIEW | top1_not_in_expected_set | avenue | avenue, road, street |
| en-de | `en-de:Chef` | Chef | REVIEW | top1_not_in_expected_set | chief | chief, boss |
| en-de | `en-de:Zug` | Zug | FAIL | forbidden_candidate_present | train | train, strain, move |
| en-de | `en-de:Stimme` | Stimme | FAIL | forbidden_candidate_present | part | part, voice, vote |
| en-de | `en-de:Grund` | Grund | REVIEW | top1_not_in_expected_set | motive | motive, however, cause |

## Suggested Case Patches

### en-de / en-de:Schule
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: school",
    "Observed top3 sources: school, group, pod"
  ],
  "candidate_forbidden_top1": [
    "school"
  ],
  "candidate_expected_any": [
    "school",
    "group",
    "pod"
  ]
}
```

### en-de / en-de:Zeit
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: time",
    "Observed top3 sources: time, spell, most"
  ],
  "candidate_forbidden_top1": [
    "time"
  ],
  "candidate_expected_any": [
    "time",
    "spell",
    "most"
  ]
}
```

### en-de / en-de:Fenster
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: box",
    "Observed top3 sources: box, window, out"
  ],
  "candidate_forbidden_top1": [
    "box"
  ],
  "candidate_expected_any": [
    "box",
    "window",
    "out"
  ]
}
```

### en-de / en-de:Tag
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: day",
    "Observed top3 sources: day, tag, most"
  ],
  "candidate_forbidden_top1": [
    "day"
  ],
  "candidate_expected_any": [
    "day",
    "tag",
    "most"
  ]
}
```

### en-de / en-de:Kopf
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: mind",
    "Observed top3 sources: mind, head, spirit"
  ],
  "candidate_forbidden_top1": [
    "mind"
  ],
  "candidate_expected_any": [
    "mind",
    "head",
    "spirit"
  ]
}
```

### en-de / en-de:Ohr
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: hearing",
    "Observed top3 sources: hearing, ear, audition"
  ],
  "candidate_forbidden_top1": [
    "hearing"
  ],
  "candidate_expected_any": [
    "hearing",
    "ear",
    "audition"
  ]
}
```

### en-de / en-de:Fuß
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: base",
    "Observed top3 sources: base, head, foot"
  ],
  "candidate_forbidden_top1": [
    "base"
  ],
  "candidate_expected_any": [
    "base",
    "head",
    "foot"
  ]
}
```

### en-de / en-de:Straße
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: avenue",
    "Observed top3 sources: avenue, road, street"
  ],
  "candidate_forbidden_top1": [
    "avenue"
  ],
  "candidate_expected_any": [
    "avenue",
    "road",
    "street"
  ]
}
```

### en-de / en-de:Chef
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: chief",
    "Observed top3 sources: chief, boss"
  ],
  "candidate_forbidden_top1": [
    "chief"
  ],
  "candidate_expected_any": [
    "chief",
    "boss"
  ]
}
```

### en-de / en-de:Zug
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: train",
    "Observed top3 sources: train, strain, move"
  ],
  "candidate_forbidden_top1": [
    "train"
  ],
  "candidate_expected_any": [
    "train",
    "strain",
    "move"
  ]
}
```

### en-de / en-de:Stimme
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: part",
    "Observed top3 sources: part, voice, vote"
  ],
  "candidate_forbidden_top1": [
    "part"
  ],
  "candidate_expected_any": [
    "part",
    "voice",
    "vote"
  ]
}
```

### en-de / en-de:Grund
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: motive",
    "Observed top3 sources: motive, however, cause"
  ],
  "candidate_forbidden_top1": [
    "motive"
  ],
  "candidate_expected_any": [
    "motive",
    "however",
    "cause"
  ]
}
```
