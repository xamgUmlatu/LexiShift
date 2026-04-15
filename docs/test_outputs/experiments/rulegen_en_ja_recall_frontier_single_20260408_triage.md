# Rulegen Benchmark Triage

- benchmark_json: `docs\test_outputs\experiments\rulegen_en_ja_recall_frontier_single_20260408.json`
- pairs_processed: 1
- failing_or_review_count: 16

| Pair | Case | Target | Status | Reasons | Top1 | Top3 |
|---|---|---|---|---|---|---|
| en-ja | `en-ja:本` | 本 | FAIL | top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3 | jeans | jeans, pens |
| en-ja | `en-ja:犬` | 犬 | FAIL | top1_is_forbidden, forbidden_candidate_present | radical | radical, dog |
| en-ja | `en-ja:駅` | 駅 | FAIL | forbidden_candidate_present | station | station, food |
| en-ja | `en-ja:色` | 色 | FAIL | forbidden_candidate_present | color | color, mood |
| en-ja | `en-ja:赤` | 赤 | FAIL | forbidden_candidate_present | red | red, communism |
| en-ja | `en-ja:青` | 青 | FAIL | forbidden_candidate_present | blue | blue, black |
| en-ja | `en-ja:黒` | 黒 | FAIL | forbidden_candidate_present | black | black, stone |
| en-ja | `en-ja:明日` | 明日 | FAIL | forbidden_candidate_present | tomorrow | tomorrow, name |
| en-ja | `en-ja:雪` | 雪 | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | hair | hair, ice |
| en-ja | `en-ja:音` | 音 | FAIL | forbidden_candidate_present | sound | sound, rumor |
| en-ja | `en-ja:声` | 声 | FAIL | forbidden_candidate_present | voice | voice, accent |
| en-ja | `en-ja:食べる` | 食べる | FAIL | forbidden_candidate_present | eat | eat, drink |
| en-ja | `en-ja:飲む` | 飲む | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |
| en-ja | `en-ja:買う` | 買う | FAIL | forbidden_candidate_present | buy | buy, value |
| en-ja | `en-ja:売る` | 売る | FAIL | forbidden_candidate_present, expected_candidate_missing_from_top3 | betray | betray, agitate |
| en-ja | `en-ja:分かる` | 分かる | FAIL | expected_candidate_missing_from_top3, no_rules_emitted | - | - |

## Suggested Case Patches

### en-ja / en-ja:本
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: jeans",
    "Observed top3 sources: jeans, pens"
  ],
  "candidate_forbidden_top1": [
    "jeans"
  ],
  "candidate_expected_any": [
    "jeans",
    "pens"
  ]
}
```

### en-ja / en-ja:犬
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: radical",
    "Observed top3 sources: radical, dog"
  ],
  "candidate_forbidden_top1": [
    "radical"
  ],
  "candidate_expected_any": [
    "radical",
    "dog"
  ]
}
```

### en-ja / en-ja:駅
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: station",
    "Observed top3 sources: station, food"
  ],
  "candidate_forbidden_top1": [
    "station"
  ],
  "candidate_expected_any": [
    "station",
    "food"
  ]
}
```

### en-ja / en-ja:色
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: color",
    "Observed top3 sources: color, mood"
  ],
  "candidate_forbidden_top1": [
    "color"
  ],
  "candidate_expected_any": [
    "color",
    "mood"
  ]
}
```

### en-ja / en-ja:赤
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: red",
    "Observed top3 sources: red, communism"
  ],
  "candidate_forbidden_top1": [
    "red"
  ],
  "candidate_expected_any": [
    "red",
    "communism"
  ]
}
```

### en-ja / en-ja:青
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: blue",
    "Observed top3 sources: blue, black"
  ],
  "candidate_forbidden_top1": [
    "blue"
  ],
  "candidate_expected_any": [
    "blue",
    "black"
  ]
}
```

### en-ja / en-ja:黒
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: black",
    "Observed top3 sources: black, stone"
  ],
  "candidate_forbidden_top1": [
    "black"
  ],
  "candidate_expected_any": [
    "black",
    "stone"
  ]
}
```

### en-ja / en-ja:明日
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: tomorrow",
    "Observed top3 sources: tomorrow, name"
  ],
  "candidate_forbidden_top1": [
    "tomorrow"
  ],
  "candidate_expected_any": [
    "tomorrow",
    "name"
  ]
}
```

### en-ja / en-ja:雪
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: hair",
    "Observed top3 sources: hair, ice"
  ],
  "candidate_forbidden_top1": [
    "hair"
  ],
  "candidate_expected_any": [
    "hair",
    "ice"
  ]
}
```

### en-ja / en-ja:音
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: sound",
    "Observed top3 sources: sound, rumor"
  ],
  "candidate_forbidden_top1": [
    "sound"
  ],
  "candidate_expected_any": [
    "sound",
    "rumor"
  ]
}
```

### en-ja / en-ja:声
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: voice",
    "Observed top3 sources: voice, accent"
  ],
  "candidate_forbidden_top1": [
    "voice"
  ],
  "candidate_expected_any": [
    "voice",
    "accent"
  ]
}
```

### en-ja / en-ja:食べる
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: eat",
    "Observed top3 sources: eat, drink"
  ],
  "candidate_forbidden_top1": [
    "eat"
  ],
  "candidate_expected_any": [
    "eat",
    "drink"
  ]
}
```

### en-ja / en-ja:飲む
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```

### en-ja / en-ja:買う
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: buy",
    "Observed top3 sources: buy, value"
  ],
  "candidate_forbidden_top1": [
    "buy"
  ],
  "candidate_expected_any": [
    "buy",
    "value"
  ]
}
```

### en-ja / en-ja:売る
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations.",
    "Observed top1 source: betray",
    "Observed top3 sources: betray, agitate"
  ],
  "candidate_forbidden_top1": [
    "betray"
  ],
  "candidate_expected_any": [
    "betray",
    "agitate"
  ]
}
```

### en-ja / en-ja:分かる
```json
{
  "action": "review_labels",
  "priority": "high",
  "notes": [
    "Review case labels and pair tuning; this case violates hard quality expectations."
  ]
}
```
