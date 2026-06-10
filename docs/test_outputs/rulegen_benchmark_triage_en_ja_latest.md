# Rulegen Benchmark Triage

- benchmark_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
- pairs_processed: 1
- failing_or_review_count: 1

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-ja | `en-ja:世界` | 世界 | FAIL | forbidden_candidate_present | society | society, sphere |

## Suggested Case Patches

### en-ja / en-ja:世界
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: society",
    "Observed top3 sources: society, sphere"
  ],
  "candidate_forbidden_top1": [
    "society"
  ],
  "candidate_expected_any": [
    "society",
    "sphere"
  ]
}
```
