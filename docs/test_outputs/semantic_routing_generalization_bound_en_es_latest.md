# en-es Semantic Veto Generalization Bound

- Status: `ok`
- Generated: `2026-04-12T23:44:45Z`
- Pair: `en-es`
- Confidence method: `cluster_bootstrap_plus_leave_one_cluster_out`
- Bootstrap iterations: `2000`
- Confidence level: `0.95`
- Random seed: `1729`
- Important caveat: fixed-shadow and veto-proxy rows are different evaluation surfaces. This report estimates a corridor, not one single deploy KPI.

## Current Corridor

- Best current source-only blocker lane: `borrowed_trigger_auto_shadows`
- Source-only abstain-recall conservative floor: `31.8%`
- Source-only harmful-allow conservative ceiling: `68.2%`
- Fixed-shadow replace-recall conservative floor: `12.5%`
- Fixed-shadow harmful-replace conservative ceiling: `0.0%`

## Fixed-Shadow Bounds

### Fixed-shadow scorer control

- Cluster key: `family_id`
- Cluster count: `8`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='off', active_rescue_mode='off'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 77.5% | 65.0% to 90.0% | 74.3% | 65.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 43.8% | 12.5% to 75.0% | 35.7% | 12.5% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 56.2% | 25.0% to 87.5% | 64.3% | 87.5% |
| winner_accuracy | 75.0% | 59.4% to 90.6% | 71.4% | 59.4% |
| shadow_winner_accuracy | 50.0% | 18.8% to 81.2% | 42.9% | 18.8% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 0.0% | 0.0% |

### Fixed-shadow scorer control [tune]

- Cluster key: `family_id`
- Cluster count: `4`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='off', active_rescue_mode='off'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 75.0% | 60.0% to 90.0% | 66.7% | 60.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 37.5% | 0.0% to 75.0% | 16.7% | 0.0% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 62.5% | 25.0% to 100.0% | 83.3% | 100.0% |
| winner_accuracy | 68.8% | 50.0% to 87.5% | 58.3% | 50.0% |
| shadow_winner_accuracy | 37.5% | 0.0% to 75.0% | 16.7% | 0.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 0.0% | 0.0% |

### Fixed-shadow scorer control [held_out]

- Cluster key: `family_id`
- Cluster count: `4`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='off', active_rescue_mode='off'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 80.0% | 60.0% to 100.0% | 73.3% | 60.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 50.0% | 0.0% to 100.0% | 33.3% | 0.0% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 50.0% | 0.0% to 100.0% | 66.7% | 100.0% |
| winner_accuracy | 81.2% | 62.5% to 100.0% | 75.0% | 62.5% |
| shadow_winner_accuracy | 62.5% | 25.0% to 100.0% | 50.0% | 25.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |

## Blocker-Generation Bounds

### Curated overlap oracle

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='curated_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| abstain_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| harmful_allow_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| allow_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Curated overlap oracle [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='curated_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| abstain_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| harmful_allow_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| allow_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Curated overlap oracle [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='curated_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| abstain_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| harmful_allow_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| allow_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Reviewed-trigger auto shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 95.4% | 91.8% to 98.3% | 95.3% | 91.8% |
| abstain_recall | 75.8% | 56.2% to 90.0% | 72.4% | 56.2% |
| harmful_allow_rate | 24.2% | 10.0% to 43.8% | 27.6% | 43.8% |
| allow_precision | 94.7% | 90.1% to 98.0% | 94.6% | 90.1% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Reviewed-trigger auto shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 84.1% | 72.3% to 94.9% | 82.5% | 72.3% |
| abstain_recall | 61.1% | 33.3% to 83.3% | 50.0% | 33.3% |
| harmful_allow_rate | 38.9% | 16.7% to 66.7% | 50.0% | 66.7% |
| allow_precision | 78.8% | 61.8% to 93.5% | 78.1% | 61.8% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Reviewed-trigger auto shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 97.1% | 90.6% to 100.0% | 96.8% | 90.6% |
| abstain_recall | 93.3% | 75.0% to 100.0% | 91.7% | 75.0% |
| harmful_allow_rate | 6.7% | 0.0% to 25.0% | 8.3% | 25.0% |
| allow_precision | 95.0% | 84.2% to 100.0% | 94.7% | 84.2% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Source-only auto shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 87.4% | 81.2% to 93.4% | 87.2% | 81.2% |
| abstain_recall | 45.5% | 25.0% to 66.7% | 40.0% | 25.0% |
| harmful_allow_rate | 54.5% | 33.3% to 75.0% | 60.0% | 75.0% |
| allow_precision | 88.5% | 81.6% to 94.8% | 88.4% | 81.6% |
| overblocking_rate | 2.8% | 0.7% to 5.8% | 2.8% | 5.8% |

### Source-only auto shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 72.7% | 58.7% to 88.4% | 71.4% | 58.7% |
| abstain_recall | 38.9% | 13.6% to 61.1% | 31.2% | 13.6% |
| harmful_allow_rate | 61.1% | 38.9% to 86.4% | 68.8% | 86.4% |
| allow_precision | 69.4% | 52.4% to 88.2% | 68.6% | 52.4% |
| overblocking_rate | 3.8% | 0.0% to 13.0% | 4.0% | 13.0% |

### Source-only auto shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 73.5% | 55.3% to 91.7% | 71.0% | 55.3% |
| abstain_recall | 53.3% | 14.1% to 87.5% | 41.7% | 14.1% |
| harmful_allow_rate | 46.7% | 12.5% to 85.9% | 58.3% | 85.9% |
| allow_precision | 70.8% | 48.3% to 95.2% | 69.6% | 48.3% |
| overblocking_rate | 10.5% | 0.0% to 26.3% | 11.1% | 26.3% |

### Source-only borrowed-trigger shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 89.1% | 83.3% to 94.3% | 88.9% | 83.3% |
| abstain_recall | 54.5% | 31.8% to 74.3% | 48.3% | 31.8% |
| harmful_allow_rate | 45.5% | 25.7% to 68.2% | 51.7% | 68.2% |
| allow_precision | 90.2% | 83.9% to 95.9% | 90.1% | 83.9% |
| overblocking_rate | 2.8% | 0.7% to 5.7% | 2.8% | 5.7% |

### Source-only borrowed-trigger shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 79.5% | 66.0% to 92.3% | 77.5% | 66.0% |
| abstain_recall | 55.6% | 25.0% to 83.3% | 42.9% | 25.0% |
| harmful_allow_rate | 44.4% | 16.7% to 75.0% | 57.1% | 75.0% |
| allow_precision | 75.8% | 58.8% to 91.2% | 75.0% | 58.8% |
| overblocking_rate | 3.8% | 0.0% to 12.5% | 4.0% | 12.5% |

### Source-only borrowed-trigger shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 73.5% | 54.0% to 92.9% | 71.0% | 54.0% |
| abstain_recall | 53.3% | 13.2% to 90.0% | 41.7% | 13.2% |
| harmful_allow_rate | 46.7% | 10.0% to 86.8% | 58.3% | 86.8% |
| allow_precision | 70.8% | 46.7% to 95.2% | 69.6% | 46.7% |
| overblocking_rate | 10.5% | 0.0% to 27.8% | 11.1% | 27.8% |

### No shadow veto

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='no_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 81.1% | 72.4% to 89.7% | 81.0% | 72.4% |
| abstain_recall | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| harmful_allow_rate | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 81.1% | 72.4% to 89.7% | 81.0% | 72.4% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### No shadow veto [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='no_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 59.1% | 40.0% to 79.5% | 58.1% | 40.0% |
| abstain_recall | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| harmful_allow_rate | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 59.1% | 40.0% to 79.5% | 58.1% | 40.0% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### No shadow veto [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='no_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 55.9% | 35.7% to 82.1% | 54.5% | 35.7% |
| abstain_recall | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| harmful_allow_rate | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 55.9% | 35.7% to 82.1% | 54.5% | 35.7% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
