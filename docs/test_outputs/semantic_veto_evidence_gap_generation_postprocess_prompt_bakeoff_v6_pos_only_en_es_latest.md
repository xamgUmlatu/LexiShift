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
| Medium eval-overlap items | 6 |
| POS-weak items | 3 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 48 |
| Items with model topic-frame labels | 48 |
| High shadow-confusable items | 1 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 48 | 0.6703 | 0.4583 | 4 | 26 | 19 | 4 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 48 | 0.6923 | 0.5000 | 4 | 24 | 21 | 4 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 48 | 0.7033 | 0.4792 | 2 | 25 | 21 | 3 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 48 | 0.4945 | 0.0833 | 2 | 44 | 2 | 3 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 46 | 0.6484 | 0.4167 | 4 | 28 | 17 | 4 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 46 | 0.6813 | 0.4375 | 2 | 27 | 19 | 3 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 45 | 0.6923 | 0.4583 | 2 | 26 | 20 | 3 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 48 | 0.7033 | 0.4792 | 2 | 25 | 21 | 3 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 42 | 0.6703 | 0.4167 | 2 | 28 | 18 | 3 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 24 | 0.5714 | 0.2500 | 3 | 36 | 10 | 4 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 48 | 0.7033 | 0.4792 | 2 | 25 | 21 | 3 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:american:americano:003`: The dashboard listed American as an internal project code.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:american:americano:003`: The dashboard listed American as an internal project code.

### `sentence_only_all`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:american:americano:003`: The dashboard listed American as an internal project code.
- `en-es:full-family-repaired-full:rebate:descuento:001`: The store offered a rebate on the new refrigerator.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:american:americano:003`: The dashboard listed American as an internal project code.
- `en-es:full-family-repaired-full:smile:sonre-r:004`: She used a smile to thank the nurse.

### `no_high_eval_overlap_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

### `conservative_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

### `quality_top1_sentence_only`
- `en-es:full-family-repaired-full:break:quebrar:002`: A dry branch can break under sudden pressure.
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:004`: She used a smile to thank the nurse.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.

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
