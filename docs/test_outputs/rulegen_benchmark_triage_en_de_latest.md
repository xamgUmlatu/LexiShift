# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- pairs_processed: 1
- failing_or_review_count: 4

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Haus` | Haus | REVIEW | top1_not_in_expected_set | establishment | establishment, institution, house |
| en-de | `en-de:Schule` | Schule | REVIEW | top1_not_in_expected_set | pod | pod, school, group |
| en-de | `en-de:Weg` | Weg | REVIEW | top1_not_in_expected_set | alley | alley, way, walk |
| en-de | `en-de:Zeit` | Zeit | REVIEW | top1_not_in_expected_set | spell | spell, time, faff |

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
