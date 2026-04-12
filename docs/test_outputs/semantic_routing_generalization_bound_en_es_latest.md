# en-es Semantic Veto Generalization Bound

- Status: `ok`
- Generated: `2026-04-12T23:35:58Z`
- Pair: `en-es`
- Confidence method: `cluster_bootstrap_plus_leave_one_cluster_out`
- Bootstrap iterations: `2000`
- Confidence level: `0.95`
- Random seed: `1729`
- Important caveat: fixed-shadow and veto-proxy rows are different evaluation surfaces. This report estimates a corridor, not one single deploy KPI.

## Current Corridor

- Best current source-only blocker lane: `borrowed_trigger_auto_shadows`
- Source-only abstain-recall conservative floor: `33.3%`
- Source-only harmful-allow conservative ceiling: `66.7%`
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

### Reviewed-trigger auto shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 95.4% | 92.0% to 98.4% | 95.3% | 92.0% |
| abstain_recall | 75.8% | 56.5% to 90.9% | 72.4% | 56.5% |
| harmful_allow_rate | 24.2% | 9.1% to 43.5% | 27.6% | 43.5% |
| allow_precision | 94.7% | 90.4% to 98.0% | 94.6% | 90.4% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Source-only auto shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 87.4% | 81.2% to 93.3% | 87.2% | 81.2% |
| abstain_recall | 45.5% | 26.5% to 64.4% | 40.0% | 26.5% |
| harmful_allow_rate | 54.5% | 35.6% to 73.5% | 60.0% | 73.5% |
| allow_precision | 88.5% | 81.6% to 94.6% | 88.4% | 81.6% |
| overblocking_rate | 2.8% | 0.7% to 5.8% | 2.8% | 5.8% |

### Source-only borrowed-trigger shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 89.1% | 83.6% to 94.4% | 88.9% | 83.6% |
| abstain_recall | 54.5% | 33.3% to 74.3% | 48.3% | 33.3% |
| harmful_allow_rate | 45.5% | 25.7% to 66.7% | 51.7% | 66.7% |
| allow_precision | 90.2% | 84.1% to 95.5% | 90.1% | 84.1% |
| overblocking_rate | 2.8% | 0.7% to 5.8% | 2.8% | 5.8% |

### No shadow veto

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='no_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 81.1% | 72.7% to 89.8% | 81.0% | 72.7% |
| abstain_recall | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| harmful_allow_rate | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 81.1% | 72.7% to 89.8% | 81.0% | 72.7% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
