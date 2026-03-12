# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
- pairs_processed: 1
- failing_or_review_count: 1

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-es | `en-es:cuadro` | cuadro | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | bed | bed |

## Suggested Case Patches

### en-es / en-es:cuadro
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: bed",
    "Observed top3 sources: bed"
  ],
  "candidate_forbidden_top1": [
    "bed"
  ],
  "candidate_expected_any": [
    "bed"
  ]
}
```
