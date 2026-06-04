# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T00:20:45Z`
- Active generated items audited: `48`
- Families: `24`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 2 |
| Medium eval-overlap items | 5 |
| POS-weak items | 6 |
| Definition-like sentence items | 1 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 0 |
| Items with model topic-frame labels | 0 |
| High shadow-confusable items | 1 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 48 | 0.6813 | 0.4375 | 2 | 27 | 18 | 2 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 48 | 0.6813 | 0.4375 | 2 | 27 | 18 | 2 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 48 | 0.7253 | 0.5208 | 2 | 23 | 22 | 2 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 48 | 0.4835 | 0.0625 | 2 | 45 | 1 | 3 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 46 | 0.6813 | 0.4167 | 1 | 28 | 17 | 1 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 46 | 0.7363 | 0.5000 | 0 | 24 | 21 | 0 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 42 | 0.6923 | 0.4583 | 2 | 26 | 19 | 2 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 47 | 0.7253 | 0.5208 | 2 | 23 | 22 | 2 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 38 | 0.6813 | 0.3958 | 0 | 29 | 16 | 0 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 24 | 0.6154 | 0.2708 | 0 | 35 | 11 | 1 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 48 | 0.7253 | 0.5208 | 2 | 23 | 22 | 2 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:smile:sonre-r:005`: The dashboard listed Smile as an internal project code.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:smile:sonre-r:005`: The dashboard listed Smile as an internal project code.

### `sentence_only_all`
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:offset:distancia:002`: The sensor has a small offset from the center line.
- `en-es:full-family-repaired-full:rebate:descuento:001`: The store offered a rebate on the new refrigerator.
- `en-es:full-family-repaired-full:smile:sonre-r:005`: The dashboard listed Smile as an internal project code.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:smile:sonre-r:005`: The dashboard listed Smile as an internal project code.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `quality_top1_sentence_only`
- `en-es:full-family-repaired-full:break:quebrar:002`: A dry branch can break under sudden pressure.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

## Recommendations

- Treat evidence_note text as an active experimental variable; note-only evidence moved decisions, so sentence-only should be the safer promotion candidate.
- Prefer sentence-only evidence for the next generated batch because it preserves or improves the control without explanatory-note leakage.
- Use the conservative sentence-only view as the safety check before any paid scale-up; it removes high-overlap and weak-POS rows while keeping the denominator fixed.

## Limitations

- `offline no-spend postprocess over already generated active-only rows`
- `heuristic POS and overlap labels are diagnostic, not gold labels`
- `note-only views are diagnostics and should not be promoted as runtime evidence`
- `same selected-family denominator is held across views for comparability`
- `this does not validate shadow or no-winner generation at scale`
