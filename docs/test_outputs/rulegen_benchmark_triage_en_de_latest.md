# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- pairs_processed: 1
- failing_or_review_count: 21

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Haus` | Haus | REVIEW | top1_not_in_expected_set | establishment | establishment, institution, house |
| en-de | `en-de:Schule` | Schule | REVIEW | top1_not_in_expected_set | pod | pod, school, group |
| en-de | `en-de:Weg` | Weg | REVIEW | top1_not_in_expected_set | alley | alley, way, walk |
| en-de | `en-de:Zeit` | Zeit | FAIL | forbidden_candidate_present | spell | spell, time, most |
| en-de | `en-de:Sprache` | Sprache | FAIL | forbidden_candidate_present | diction | diction, language, tongue |
| en-de | `en-de:Fenster` | Fenster | FAIL | forbidden_candidate_present | box | box, window, out |
| en-de | `en-de:Tag` | Tag | FAIL | forbidden_candidate_present | tag | tag, day, most |
| en-de | `en-de:Stunde` | Stunde | FAIL | forbidden_candidate_present | lesson | lesson, hour, period |
| en-de | `en-de:Kopf` | Kopf | FAIL | forbidden_candidate_present | mind | mind, spirit, head |
| en-de | `en-de:Gesicht` | Gesicht | FAIL | forbidden_candidate_present | facies | facies, appearance, face |
| en-de | `en-de:Ohr` | Ohr | FAIL | forbidden_candidate_present | hearing | hearing, audition, ear |
| en-de | `en-de:Fuß` | Fuß | FAIL | forbidden_candidate_present | base | base, foot, head |
| en-de | `en-de:Straße` | Straße | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | avenue | avenue, alley, strait |
| en-de | `en-de:Idee` | Idee | FAIL | forbidden_candidate_present | notion | notion, inspiration, idea |
| en-de | `en-de:Preis` | Preis | FAIL | expected_candidate_missing_from_top3 | award | award, cost, pot |
| en-de | `en-de:Chef` | Chef | REVIEW | top1_not_in_expected_set | chief | chief, boss |
| en-de | `en-de:Fall` | Fall | FAIL | forbidden_candidate_present | case | case, fall, instance |
| en-de | `en-de:Zug` | Zug | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | strain | strain, trait, characteristic |
| en-de | `en-de:Stimme` | Stimme | FAIL | forbidden_candidate_present | part | part, partbook, voice |
| en-de | `en-de:Geschichte` | Geschichte | REVIEW | top1_not_in_expected_set | tale | tale, story, history |
| en-de | `en-de:Grund` | Grund | FAIL | top1_is_forbidden, expected_candidate_missing_from_top3 | motive | motive, motivation, bottom |

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
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: spell",
    "Observed top3 sources: spell, time, most"
  ],
  "candidate_forbidden_top1": [
    "spell"
  ],
  "candidate_expected_any": [
    "spell",
    "time",
    "most"
  ]
}
```

### en-de / en-de:Sprache
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: diction",
    "Observed top3 sources: diction, language, tongue"
  ],
  "candidate_forbidden_top1": [
    "diction"
  ],
  "candidate_expected_any": [
    "diction",
    "language",
    "tongue"
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
    "Observed top1 source: tag",
    "Observed top3 sources: tag, day, most"
  ],
  "candidate_forbidden_top1": [
    "tag"
  ],
  "candidate_expected_any": [
    "tag",
    "day",
    "most"
  ]
}
```

### en-de / en-de:Stunde
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: lesson",
    "Observed top3 sources: lesson, hour, period"
  ],
  "candidate_forbidden_top1": [
    "lesson"
  ],
  "candidate_expected_any": [
    "lesson",
    "hour",
    "period"
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
    "Observed top3 sources: mind, spirit, head"
  ],
  "candidate_forbidden_top1": [
    "mind"
  ],
  "candidate_expected_any": [
    "mind",
    "spirit",
    "head"
  ]
}
```

### en-de / en-de:Gesicht
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: facies",
    "Observed top3 sources: facies, appearance, face"
  ],
  "candidate_forbidden_top1": [
    "facies"
  ],
  "candidate_expected_any": [
    "facies",
    "appearance",
    "face"
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
    "Observed top3 sources: hearing, audition, ear"
  ],
  "candidate_forbidden_top1": [
    "hearing"
  ],
  "candidate_expected_any": [
    "hearing",
    "audition",
    "ear"
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
    "Observed top3 sources: base, foot, head"
  ],
  "candidate_forbidden_top1": [
    "base"
  ],
  "candidate_expected_any": [
    "base",
    "foot",
    "head"
  ]
}
```

### en-de / en-de:Straße
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: avenue",
    "Observed top3 sources: avenue, alley, strait"
  ],
  "candidate_forbidden_top1": [
    "avenue"
  ],
  "candidate_expected_any": [
    "avenue",
    "alley",
    "strait"
  ]
}
```

### en-de / en-de:Idee
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: notion",
    "Observed top3 sources: notion, inspiration, idea"
  ],
  "candidate_forbidden_top1": [
    "notion"
  ],
  "candidate_expected_any": [
    "notion",
    "inspiration",
    "idea"
  ]
}
```

### en-de / en-de:Preis
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: award",
    "Observed top3 sources: award, cost, pot"
  ],
  "candidate_forbidden_top1": [
    "award"
  ],
  "candidate_expected_any": [
    "award",
    "cost",
    "pot"
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

### en-de / en-de:Fall
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: case",
    "Observed top3 sources: case, fall, instance"
  ],
  "candidate_forbidden_top1": [
    "case"
  ],
  "candidate_expected_any": [
    "case",
    "fall",
    "instance"
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
    "Observed top1 source: strain",
    "Observed top3 sources: strain, trait, characteristic"
  ],
  "candidate_forbidden_top1": [
    "strain"
  ],
  "candidate_expected_any": [
    "strain",
    "trait",
    "characteristic"
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
    "Observed top3 sources: part, partbook, voice"
  ],
  "candidate_forbidden_top1": [
    "part"
  ],
  "candidate_expected_any": [
    "part",
    "partbook",
    "voice"
  ]
}
```

### en-de / en-de:Geschichte
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: tale",
    "Observed top3 sources: tale, story, history"
  ],
  "candidate_forbidden_top1": [
    "tale"
  ],
  "candidate_expected_any": [
    "tale",
    "story",
    "history"
  ]
}
```

### en-de / en-de:Grund
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: motive",
    "Observed top3 sources: motive, motivation, bottom"
  ],
  "candidate_forbidden_top1": [
    "motive"
  ],
  "candidate_expected_any": [
    "motive",
    "motivation",
    "bottom"
  ]
}
```
