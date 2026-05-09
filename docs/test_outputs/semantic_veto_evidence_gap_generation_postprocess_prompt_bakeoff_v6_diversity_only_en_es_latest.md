# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T00:20:45Z`
- Active generated items audited: `48`
- Families: `24`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 4 |
| Medium eval-overlap items | 7 |
| POS-weak items | 2 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 48 |
| Items with model topic-frame labels | 48 |
| High shadow-confusable items | 0 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 48 | 0.6703 | 0.5000 | 6 | 24 | 21 | 6 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 48 | 0.6593 | 0.5000 | 7 | 24 | 21 | 7 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 48 | 0.7033 | 0.5208 | 4 | 23 | 23 | 5 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 48 | 0.5055 | 0.1042 | 2 | 43 | 2 | 2 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 44 | 0.6484 | 0.4167 | 4 | 28 | 17 | 4 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 44 | 0.6703 | 0.4167 | 2 | 28 | 18 | 3 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 46 | 0.7033 | 0.5208 | 4 | 23 | 23 | 5 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 48 | 0.7033 | 0.5208 | 4 | 23 | 23 | 5 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 42 | 0.6703 | 0.4167 | 2 | 28 | 18 | 3 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 24 | 0.6044 | 0.2708 | 1 | 35 | 11 | 2 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 48 | 0.7033 | 0.5208 | 4 | 23 | 23 | 5 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:german:alem-n:003`: The dashboard listed German as an internal project code.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:german:alem-n:003`: The dashboard listed German as an internal project code.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `sentence_only_all`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:german:alem-n:003`: The dashboard listed German as an internal project code.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:german:alem-n:003`: The dashboard listed German as an internal project code.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `no_high_eval_overlap_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `conservative_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `quality_top1_sentence_only`
- `en-es:full-family-repaired-full:break:quebrar:002`: A dry branch can break under sudden pressure.
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:offset:distancia:004`: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:003`: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

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
