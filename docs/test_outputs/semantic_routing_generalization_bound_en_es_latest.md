# en-es Semantic Veto Generalization Bound

- Status: `ok`
- Generated: `2026-04-23T05:10:04Z`
- Pair: `en-es`
- Confidence method: `cluster_bootstrap_plus_leave_one_cluster_out`
- Bootstrap iterations: `2000`
- Confidence level: `0.95`
- Random seed: `1729`
- Important caveat: fixed-shadow and veto-proxy rows are different evaluation surfaces. This report estimates a corridor, not one single deploy KPI.

## Current Corridor

- Best current source-only blocker lane: `borrowed_trigger_auto_shadows`
- Source-only abstain-recall conservative floor: `3.2%`
- Source-only harmful-allow conservative ceiling: `96.8%`
- Fixed-shadow replace-recall conservative floor: `16.7%`
- Fixed-shadow harmful-replace conservative ceiling: `0.0%`
- Evaluated runtime reference lane: `Sentence-transformer phrase-guard candidate`
- Runtime reference replace-recall conservative floor: `69.4%`
- Runtime reference harmful-replace conservative ceiling: `5.6%`
- Runtime reference false-abstain conservative ceiling: `30.6%`
- Experimental phrase-guard lane: `Sentence-transformer active-sense phrase-guard experiment`
- Experimental phrase-guard replace-recall conservative floor: `69.4%`
- Experimental phrase-guard harmful-replace conservative ceiling: `0.0%`
- Experimental phrase-guard false-abstain conservative ceiling: `30.6%`
- Evaluated runtime ladder lane: `Sentence-transformer zero-noise soft ladder`
- Runtime ladder replace-or-soft recall conservative floor: `83.3%`
- Runtime ladder soft-noise conservative ceiling: `0.0%`
- Evaluated rescue-overlay lane: `Sentence-transformer widened-rescue candidate (simulated)`
- Rescue-overlay replace-recall conservative floor: `77.8%`
- Rescue-overlay harmful-replace conservative ceiling: `5.6%`
- Rescue-overlay false-abstain conservative ceiling: `22.2%`
- Experimental phrase-guard overlay lane: `Sentence-transformer active-sense phrase-guard overlay (simulated)`
- Experimental phrase-guard overlay replace-recall conservative floor: `77.8%`
- Experimental phrase-guard overlay harmful-replace conservative ceiling: `0.0%`
- Experimental phrase-guard overlay false-abstain conservative ceiling: `22.2%`

## Fixed-Shadow Bounds

### Fixed-shadow runtime control

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 73.3% | 66.7% to 80.0% | 71.8% | 66.7% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 33.3% | 16.7% to 50.0% | 29.4% | 16.7% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 66.7% | 50.0% to 83.3% | 70.6% | 83.3% |
| winner_accuracy | 63.9% | 54.2% to 73.6% | 61.8% | 54.2% |
| shadow_winner_accuracy | 33.3% | 16.7% to 50.0% | 29.4% | 16.7% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 0.0% | 0.0% |

### Fixed-shadow runtime control [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 77.1% | 68.6% to 85.7% | 73.3% | 68.6% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 42.9% | 21.4% to 64.3% | 33.3% | 21.4% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 57.1% | 35.7% to 78.6% | 66.7% | 78.6% |
| winner_accuracy | 67.9% | 57.1% to 82.1% | 62.5% | 57.1% |
| shadow_winner_accuracy | 35.7% | 14.3% to 64.3% | 25.0% | 14.3% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 0.0% | 0.0% |

### Fixed-shadow runtime control [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 70.9% | 61.8% to 80.0% | 68.0% | 61.8% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 27.3% | 4.5% to 50.0% | 20.0% | 4.5% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 72.7% | 50.0% to 95.5% | 80.0% | 95.5% |
| winner_accuracy | 61.4% | 50.0% to 75.0% | 57.5% | 50.0% |
| shadow_winner_accuracy | 31.8% | 9.1% to 54.5% | 25.0% | 9.1% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 50.0% | 0.0% |

### Sentence-transformer phrase-guard candidate

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 91.1% | 85.6% to 96.7% | 90.6% | 85.6% |
| replace_precision | 96.7% | 89.7% to 100.0% | 96.4% | 89.7% |
| replace_recall | 80.6% | 69.4% to 91.7% | 79.4% | 69.4% |
| harmful_replace_rate | 1.9% | 0.0% to 5.6% | 2.0% | 5.6% |
| false_abstain_rate | 19.4% | 8.3% to 30.6% | 20.6% | 30.6% |
| winner_accuracy | 90.3% | 84.7% to 95.8% | 89.7% | 84.7% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 50.0% | 0.0% |

### Sentence-transformer phrase-guard candidate [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 97.1% | 91.4% to 100.0% | 96.7% | 91.4% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 92.9% | 78.6% to 100.0% | 91.7% | 78.6% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 7.1% | 0.0% to 21.4% | 8.3% | 21.4% |
| winner_accuracy | 96.4% | 89.3% to 100.0% | 95.8% | 89.3% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 100.0% | 0.0% |

### Sentence-transformer phrase-guard candidate [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 87.3% | 80.0% to 94.5% | 86.0% | 80.0% |
| replace_precision | 94.1% | 82.3% to 100.0% | 93.3% | 82.3% |
| replace_recall | 72.7% | 59.1% to 86.4% | 70.0% | 59.1% |
| harmful_replace_rate | 3.0% | 0.0% to 9.1% | 3.3% | 9.1% |
| false_abstain_rate | 27.3% | 13.6% to 40.9% | 30.0% | 40.9% |
| winner_accuracy | 86.4% | 79.5% to 93.2% | 85.0% | 79.5% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 50.0% | 33.3% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard experiment

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 92.2% | 87.8% to 96.7% | 91.8% | 87.8% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 80.6% | 69.4% to 91.7% | 79.4% | 69.4% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 19.4% | 8.3% to 30.6% | 20.6% | 30.6% |
| winner_accuracy | 90.3% | 84.7% to 95.8% | 89.7% | 84.7% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 50.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard experiment [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 97.1% | 91.4% to 100.0% | 96.7% | 91.4% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 92.9% | 78.6% to 100.0% | 91.7% | 78.6% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 7.1% | 0.0% to 21.4% | 8.3% | 21.4% |
| winner_accuracy | 96.4% | 89.3% to 100.0% | 95.8% | 89.3% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard experiment [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 89.1% | 83.6% to 94.5% | 88.0% | 83.6% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 72.7% | 59.1% to 86.4% | 70.0% | 59.1% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 27.3% | 13.6% to 40.9% | 30.0% | 40.9% |
| winner_accuracy | 86.4% | 79.5% to 93.2% | 85.0% | 79.5% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer zero-noise soft ladder

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 80.6% | 69.4% to 91.7% | 79.4% | 69.4% |
| hard_harmful_replace_rate | 1.9% | 0.0% to 5.6% | 2.0% | 5.6% |
| replace_or_soft_recall | 91.7% | 83.3% to 100.0% | 91.2% | 83.3% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 97.1% | 91.2% to 100.0% | 96.9% | 91.2% |
| remaining_missed_replace_rate | 8.3% | 0.0% to 16.7% | 8.8% | 16.7% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |

### Sentence-transformer zero-noise soft ladder [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 92.9% | 78.6% to 100.0% | 91.7% | 78.6% |
| hard_harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| replace_or_soft_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| remaining_missed_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 100.0% | 0.0% |

### Sentence-transformer zero-noise soft ladder [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 72.7% | 59.1% to 86.4% | 70.0% | 59.1% |
| hard_harmful_replace_rate | 3.0% | 0.0% to 9.1% | 3.3% | 9.1% |
| replace_or_soft_recall | 86.4% | 72.7% to 100.0% | 85.0% | 72.7% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 95.0% | 85.0% to 100.0% | 94.4% | 85.0% |
| remaining_missed_replace_rate | 13.6% | 0.0% to 27.3% | 15.0% | 27.3% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer widened-rescue candidate (simulated)

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 94.4% | 88.9% to 98.9% | 94.1% | 88.9% |
| replace_precision | 97.0% | 90.6% to 100.0% | 96.8% | 90.6% |
| replace_recall | 88.9% | 77.8% to 97.2% | 88.2% | 77.8% |
| harmful_replace_rate | 1.9% | 0.0% to 5.6% | 2.0% | 5.6% |
| false_abstain_rate | 11.1% | 2.8% to 22.2% | 11.8% | 22.2% |
| winner_accuracy | 94.4% | 88.9% to 98.6% | 94.1% | 88.9% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |

### Sentence-transformer widened-rescue candidate (simulated) [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 100.0% | 0.0% |

### Sentence-transformer widened-rescue candidate (simulated) [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 90.9% | 81.8% to 98.2% | 90.0% | 81.8% |
| replace_precision | 94.7% | 83.3% to 100.0% | 94.1% | 83.3% |
| replace_recall | 81.8% | 68.2% to 95.5% | 80.0% | 68.2% |
| harmful_replace_rate | 3.0% | 0.0% to 9.1% | 3.3% | 9.1% |
| false_abstain_rate | 18.2% | 4.5% to 31.8% | 20.0% | 31.8% |
| winner_accuracy | 90.9% | 84.1% to 97.7% | 90.0% | 84.1% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 50.0% | 33.3% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard overlay (simulated)

- Cluster key: `family_id`
- Cluster count: `18`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True, experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 95.6% | 91.1% to 98.9% | 95.3% | 91.1% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 88.9% | 77.8% to 97.2% | 88.2% | 77.8% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 11.1% | 2.8% to 22.2% | 11.8% | 22.2% |
| winner_accuracy | 94.4% | 88.9% to 98.6% | 94.1% | 88.9% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard overlay (simulated) [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True, experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard overlay (simulated) [held_out]

- Cluster key: `family_id`
- Cluster count: `11`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True, experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 92.7% | 87.3% to 98.2% | 92.0% | 87.3% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 81.8% | 68.2% to 95.5% | 80.0% | 68.2% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 18.2% | 4.5% to 31.8% | 20.0% | 31.8% |
| winner_accuracy | 90.9% | 84.1% to 97.7% | 90.0% | 84.1% |
| shadow_winner_accuracy | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:bank:banco | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:file:archivo | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:order:pedido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:park:parque | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:plant:planta | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:play:obra | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

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
| overall_accuracy | 85.1% | 78.0% to 92.1% | 85.1% | 78.0% |
| abstain_recall | 21.2% | 8.7% to 35.0% | 16.7% | 8.7% |
| harmful_allow_rate | 78.8% | 65.0% to 91.3% | 83.3% | 91.3% |
| allow_precision | 84.5% | 76.6% to 91.9% | 84.4% | 76.6% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Reviewed-trigger auto shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 68.2% | 52.8% to 84.6% | 67.4% | 52.8% |
| abstain_recall | 22.2% | 7.1% to 37.5% | 18.8% | 7.1% |
| harmful_allow_rate | 77.8% | 62.5% to 92.9% | 81.2% | 92.9% |
| allow_precision | 65.0% | 46.7% to 83.3% | 64.1% | 46.7% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Reviewed-trigger auto shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='reviewed_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 64.7% | 46.2% to 85.7% | 63.6% | 46.2% |
| abstain_recall | 20.0% | 0.0% to 45.0% | 8.3% | 0.0% |
| harmful_allow_rate | 80.0% | 55.0% to 100.0% | 91.7% | 100.0% |
| allow_precision | 61.3% | 41.2% to 85.2% | 60.0% | 41.2% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Source-only auto shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 81.7% | 73.6% to 89.7% | 81.6% | 73.6% |
| abstain_recall | 9.1% | 0.0% to 22.7% | 3.3% | 0.0% |
| harmful_allow_rate | 90.9% | 77.3% to 100.0% | 96.7% | 100.0% |
| allow_precision | 82.4% | 74.2% to 90.6% | 82.2% | 74.2% |
| overblocking_rate | 1.4% | 0.0% to 3.5% | 1.4% | 3.5% |

### Source-only auto shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 61.4% | 45.1% to 82.1% | 60.5% | 45.1% |
| abstain_recall | 5.6% | 0.0% to 15.0% | 0.0% | 0.0% |
| harmful_allow_rate | 94.4% | 85.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 60.5% | 43.8% to 81.6% | 59.5% | 43.8% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Source-only auto shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 58.8% | 39.5% to 81.5% | 57.6% | 39.5% |
| abstain_recall | 13.3% | 0.0% to 40.0% | 0.0% | 0.0% |
| harmful_allow_rate | 86.7% | 60.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 58.1% | 37.8% to 84.0% | 56.7% | 37.8% |
| overblocking_rate | 5.3% | 0.0% to 16.7% | 5.6% | 16.7% |

### Source-only borrowed-trigger shadows

- Cluster key: `trigger`
- Cluster count: `156`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 82.9% | 75.5% to 89.8% | 82.8% | 75.5% |
| abstain_recall | 15.2% | 3.2% to 28.0% | 10.0% | 3.2% |
| harmful_allow_rate | 84.8% | 72.0% to 96.8% | 90.0% | 96.8% |
| allow_precision | 83.3% | 75.3% to 90.7% | 83.2% | 75.3% |
| overblocking_rate | 1.4% | 0.0% to 3.6% | 1.4% | 3.6% |

### Source-only borrowed-trigger shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 65.9% | 50.9% to 83.8% | 65.1% | 50.9% |
| abstain_recall | 16.7% | 0.0% to 31.2% | 12.5% | 0.0% |
| harmful_allow_rate | 83.3% | 68.8% to 100.0% | 87.5% | 100.0% |
| allow_precision | 63.4% | 45.7% to 83.3% | 62.5% | 45.7% |
| overblocking_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |

### Source-only borrowed-trigger shadows [held_out]

- Cluster key: `trigger`
- Cluster count: `25`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 58.8% | 39.5% to 82.1% | 57.6% | 39.5% |
| abstain_recall | 13.3% | 0.0% to 40.0% | 0.0% | 0.0% |
| harmful_allow_rate | 86.7% | 60.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 58.1% | 36.8% to 84.0% | 56.7% | 36.8% |
| overblocking_rate | 5.3% | 0.0% to 18.2% | 5.6% | 18.2% |

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
