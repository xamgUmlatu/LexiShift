# Rulegen Benchmark Triage

- benchmark_json: `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json`
- pairs_processed: 1
- failing_or_review_count: 4

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-de | `en-de:Arbeit` | Arbeit | FAIL | expected_candidate_missing_from_top3 | toil | toil |
| en-de | `en-de:Kind` | Kind | REVIEW | top1_not_in_expected_set | kid | kid |
| en-de | `en-de:Fall` | Fall | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | fall | fall |
| en-de | `en-de:Grund` | Grund | REVIEW | top1_not_in_expected_set | ground | ground |

## Suggested Case Patches

### en-de / en-de:Arbeit
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: toil",
    "Observed top3 sources: toil"
  ],
  "candidate_forbidden_top1": [
    "toil"
  ],
  "candidate_expected_any": [
    "toil"
  ]
}
```

### en-de / en-de:Kind
```json
{
  "action": "review_labels",
  "priority": "medium",
  "notes": [
    "Review expected_top1_any labels or scoring weights for this case.",
    "Observed top1 source: kid",
    "Observed top3 sources: kid"
  ],
  "candidate_forbidden_top1": [
    "kid"
  ],
  "candidate_expected_any": [
    "kid"
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
    "Observed top1 source: fall",
    "Observed top3 sources: fall"
  ],
  "candidate_forbidden_top1": [
    "fall"
  ],
  "candidate_expected_any": [
    "fall"
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
    "Observed top1 source: ground",
    "Observed top3 sources: ground"
  ],
  "candidate_forbidden_top1": [
    "ground"
  ],
  "candidate_expected_any": [
    "ground"
  ]
}
```
