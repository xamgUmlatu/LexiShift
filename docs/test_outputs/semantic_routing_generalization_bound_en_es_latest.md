# en-es Semantic Veto Generalization Bound

- Status: `ok`
- Generated: `2026-04-23T19:15:19Z`
- Pair: `en-es`
- Confidence method: `cluster_bootstrap_plus_leave_one_cluster_out`
- Bootstrap iterations: `2000`
- Confidence level: `0.95`
- Random seed: `1729`
- Important caveat: fixed-shadow and veto-proxy rows are different evaluation surfaces. This report estimates a corridor, not one single deploy KPI.

## Current Corridor

- Best current source-only blocker lane: `borrowed_trigger_auto_shadows`
- Source-only abstain-recall conservative floor: `0.0%`
- Source-only harmful-allow conservative ceiling: `100.0%`
- Fixed-shadow replace-recall conservative floor: `15.8%`
- Fixed-shadow harmful-replace conservative ceiling: `0.0%`
- Evaluated runtime reference lane: `Sentence-transformer phrase-guard candidate`
- Runtime reference replace-recall conservative floor: `63.2%`
- Runtime reference harmful-replace conservative ceiling: `5.3%`
- Runtime reference false-abstain conservative ceiling: `36.8%`
- Experimental phrase-guard lane: `Sentence-transformer active-sense phrase-guard experiment`
- Experimental phrase-guard replace-recall conservative floor: `63.2%`
- Experimental phrase-guard harmful-replace conservative ceiling: `0.0%`
- Experimental phrase-guard false-abstain conservative ceiling: `36.8%`
- Evaluated runtime ladder lane: `Sentence-transformer zero-noise soft ladder`
- Runtime ladder replace-or-soft recall conservative floor: `63.2%`
- Runtime ladder soft-noise conservative ceiling: `0.0%`
- Evaluated rescue-overlay lane: `Sentence-transformer widened-rescue candidate (simulated)`
- Rescue-overlay replace-recall conservative floor: `71.1%`
- Rescue-overlay harmful-replace conservative ceiling: `5.3%`
- Rescue-overlay false-abstain conservative ceiling: `28.9%`
- Experimental phrase-guard overlay lane: `Sentence-transformer active-sense phrase-guard overlay (simulated)`
- Experimental phrase-guard overlay replace-recall conservative floor: `71.1%`
- Experimental phrase-guard overlay harmful-replace conservative ceiling: `0.0%`
- Experimental phrase-guard overlay false-abstain conservative ceiling: `28.9%`

## Fixed-Shadow Bounds

### Fixed-shadow runtime control

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 73.7% | 66.3% to 81.1% | 72.2% | 66.3% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 34.2% | 15.8% to 52.6% | 30.6% | 15.8% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 65.8% | 47.4% to 84.2% | 69.4% | 84.2% |
| winner_accuracy | 63.2% | 53.9% to 72.4% | 61.1% | 53.9% |
| shadow_winner_accuracy | 31.6% | 15.8% to 50.0% | 27.8% | 15.8% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:bank:banco | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:check:cheque | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
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
| decision_accuracy | 80.0% | 68.6% to 91.4% | 76.7% | 68.6% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 50.0% | 21.4% to 78.6% | 41.7% | 21.4% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 50.0% | 21.4% to 78.6% | 58.3% | 78.6% |
| winner_accuracy | 67.9% | 57.1% to 82.1% | 62.5% | 57.1% |
| shadow_winner_accuracy | 35.7% | 14.3% to 64.3% | 25.0% | 14.3% |

#### Cluster Breakdown

| Cluster | Rows | Primary Read | Risk Read |
| --- | ---: | ---: | ---: |
| en-es:sentence-veto:ball:pelota | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:board:tablero | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:branch:sucursal | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:cell:celula | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:drink:bebida | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:match:partido | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:spring:primavera | 5 | 0.0% | 0.0% |

### Fixed-shadow runtime control [held_out]

- Cluster key: `family_id`
- Cluster count: `12`
- Config: `scorer_id='tfidf_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.05, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 70.0% | 61.7% to 80.0% | 67.3% | 61.7% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 25.0% | 4.2% to 50.0% | 18.2% | 4.2% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 75.0% | 50.0% to 95.8% | 81.8% | 95.8% |
| winner_accuracy | 60.4% | 50.0% to 72.9% | 56.8% | 50.0% |
| shadow_winner_accuracy | 29.2% | 8.3% to 50.0% | 22.7% | 8.3% |

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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 50.0% | 0.0% |

### Sentence-transformer phrase-guard candidate

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 89.5% | 83.2% to 94.7% | 88.9% | 83.2% |
| replace_precision | 96.7% | 89.3% to 100.0% | 96.4% | 89.3% |
| replace_recall | 76.3% | 63.2% to 89.5% | 75.0% | 63.2% |
| harmful_replace_rate | 1.8% | 0.0% to 5.3% | 1.9% | 5.3% |
| false_abstain_rate | 23.7% | 10.5% to 36.8% | 25.0% | 36.8% |
| winner_accuracy | 88.2% | 81.6% to 94.7% | 87.5% | 81.6% |
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
- Cluster count: `12`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 85.0% | 76.7% to 93.3% | 83.6% | 76.7% |
| replace_precision | 94.1% | 81.2% to 100.0% | 93.3% | 81.2% |
| replace_recall | 66.7% | 50.0% to 83.3% | 63.6% | 50.0% |
| harmful_replace_rate | 2.8% | 0.0% to 8.3% | 3.0% | 8.3% |
| false_abstain_rate | 33.3% | 16.7% to 50.0% | 36.4% | 50.0% |
| winner_accuracy | 83.3% | 75.0% to 91.7% | 81.8% | 75.0% |
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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard experiment

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 90.5% | 85.3% to 95.8% | 90.0% | 85.3% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 76.3% | 63.2% to 89.5% | 75.0% | 63.2% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 23.7% | 10.5% to 36.8% | 25.0% | 36.8% |
| winner_accuracy | 88.2% | 81.6% to 94.7% | 87.5% | 81.6% |
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
- Cluster count: `12`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 86.7% | 80.0% to 93.3% | 85.5% | 80.0% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 66.7% | 50.0% to 83.3% | 63.6% | 50.0% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 33.3% | 16.7% to 50.0% | 36.4% | 50.0% |
| winner_accuracy | 83.3% | 75.0% to 91.7% | 81.8% | 75.0% |
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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer zero-noise soft ladder

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 76.3% | 63.2% to 89.5% | 75.0% | 63.2% |
| hard_harmful_replace_rate | 1.8% | 0.0% to 5.3% | 1.9% | 5.3% |
| replace_or_soft_recall | 76.3% | 63.2% to 89.5% | 75.0% | 63.2% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 96.7% | 89.7% to 100.0% | 96.4% | 89.7% |
| remaining_missed_replace_rate | 23.7% | 10.5% to 36.8% | 25.0% | 36.8% |

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

### Sentence-transformer zero-noise soft ladder [tune]

- Cluster key: `family_id`
- Cluster count: `7`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 92.9% | 78.6% to 100.0% | 91.7% | 78.6% |
| hard_harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| replace_or_soft_recall | 92.9% | 78.6% to 100.0% | 91.7% | 78.6% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| remaining_missed_replace_rate | 7.1% | 0.0% to 21.4% | 8.3% | 21.4% |

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

### Sentence-transformer zero-noise soft ladder [held_out]

- Cluster key: `family_id`
- Cluster count: `12`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| hard_replace_recall | 66.7% | 50.0% to 83.3% | 63.6% | 50.0% |
| hard_harmful_replace_rate | 2.8% | 0.0% to 8.3% | 3.0% | 8.3% |
| replace_or_soft_recall | 66.7% | 50.0% to 83.3% | 63.6% | 50.0% |
| soft_noise_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| surfaced_precision | 94.1% | 81.2% to 100.0% | 93.3% | 81.2% |
| remaining_missed_replace_rate | 33.3% | 16.7% to 50.0% | 36.4% | 50.0% |

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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer widened-rescue candidate (simulated)

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 92.6% | 86.3% to 97.9% | 92.2% | 86.3% |
| replace_precision | 97.0% | 90.0% to 100.0% | 96.8% | 90.0% |
| replace_recall | 84.2% | 71.1% to 94.7% | 83.3% | 71.1% |
| harmful_replace_rate | 1.8% | 0.0% to 5.3% | 1.9% | 5.3% |
| false_abstain_rate | 15.8% | 5.3% to 28.9% | 16.7% | 28.9% |
| winner_accuracy | 92.1% | 85.5% to 97.4% | 91.7% | 85.5% |
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
- Cluster count: `12`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 88.3% | 80.0% to 96.7% | 87.3% | 80.0% |
| replace_precision | 94.7% | 83.3% to 100.0% | 94.1% | 83.3% |
| replace_recall | 75.0% | 54.2% to 91.7% | 72.7% | 54.2% |
| harmful_replace_rate | 2.8% | 0.0% to 8.3% | 3.0% | 8.3% |
| false_abstain_rate | 25.0% | 8.3% to 45.8% | 27.3% | 45.8% |
| winner_accuracy | 87.5% | 77.1% to 95.8% | 86.4% | 77.1% |
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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
| en-es:sentence-veto:seal:sello | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:table:mesa | 5 | 100.0% | 0.0% |
| en-es:sentence-veto:trip:viaje | 5 | 50.0% | 0.0% |
| en-es:sentence-veto:watch:reloj | 5 | 100.0% | 0.0% |

### Sentence-transformer active-sense phrase-guard overlay (simulated)

- Cluster key: `family_id`
- Cluster count: `19`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True, experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 93.7% | 88.4% to 97.9% | 93.3% | 88.4% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 84.2% | 71.1% to 94.7% | 83.3% | 71.1% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 15.8% | 5.3% to 28.9% | 16.7% | 28.9% |
| winner_accuracy | 92.1% | 85.5% to 97.4% | 91.7% | 85.5% |
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
- Cluster count: `12`
- Config: `scorer_id='sentence_transformer_cosine', context_view='masked_sentence', evidence_view='all_evidence_text', min_active_score=0.0, min_margin=0.0, phrase_control_mode='noun_family_frame_guard', phrase_guard_pos_scope='active_only', active_rescue_mode='sense_label_near_tie_active_rescue', backup_evidence_view='sense_label', primary_margin_floor=-0.05, backup_margin_floor=0.02, simulated=True, experimental=True`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| decision_accuracy | 90.0% | 81.7% to 96.7% | 89.1% | 81.7% |
| replace_precision | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| replace_recall | 75.0% | 54.2% to 91.7% | 72.7% | 54.2% |
| harmful_replace_rate | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| false_abstain_rate | 25.0% | 8.3% to 45.8% | 27.3% | 45.8% |
| winner_accuracy | 87.5% | 77.1% to 95.8% | 86.4% | 77.1% |
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
| en-es:sentence-veto:report:informe | 5 | 0.0% | 0.0% |
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
| overall_accuracy | 81.7% | 73.4% to 90.2% | 81.6% | 73.4% |
| abstain_recall | 6.1% | 0.0% to 20.5% | 0.0% | 0.0% |
| harmful_allow_rate | 93.9% | 79.5% to 100.0% | 100.0% | 100.0% |
| allow_precision | 82.0% | 73.5% to 90.4% | 81.9% | 73.5% |
| overblocking_rate | 0.7% | 0.0% to 2.2% | 0.7% | 2.2% |

### Source-only auto shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 59.1% | 41.7% to 79.5% | 58.1% | 41.7% |
| abstain_recall | 0.0% | 0.0% to 0.0% | 0.0% | 0.0% |
| harmful_allow_rate | 100.0% | 100.0% to 100.0% | 100.0% | 100.0% |
| allow_precision | 59.1% | 41.7% to 79.5% | 58.1% | 41.7% |
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
| overall_accuracy | 81.7% | 73.9% to 89.1% | 81.6% | 73.9% |
| abstain_recall | 12.1% | 0.0% to 24.4% | 6.7% | 0.0% |
| harmful_allow_rate | 87.9% | 75.6% to 100.0% | 93.3% | 100.0% |
| allow_precision | 82.7% | 74.7% to 90.2% | 82.6% | 74.7% |
| overblocking_rate | 2.1% | 0.0% to 4.9% | 2.1% | 4.9% |

### Source-only borrowed-trigger shadows [tune]

- Cluster key: `trigger`
- Cluster count: `34`
- Config: `source_id='borrowed_trigger_auto_shadows'`

| Metric | Point | Bootstrap CI | Held-out worst | Conservative bound |
| --- | ---: | ---: | ---: | ---: |
| overall_accuracy | 61.4% | 45.3% to 79.5% | 60.5% | 45.3% |
| abstain_recall | 11.1% | 0.0% to 25.0% | 6.2% | 0.0% |
| harmful_allow_rate | 88.9% | 75.0% to 100.0% | 93.8% | 100.0% |
| allow_precision | 61.0% | 43.5% to 81.1% | 60.0% | 43.5% |
| overblocking_rate | 3.8% | 0.0% to 12.5% | 4.0% | 12.5% |

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
