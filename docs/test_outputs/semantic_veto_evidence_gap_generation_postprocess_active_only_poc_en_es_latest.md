# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T00:09:47Z`
- Active generated items audited: `48`
- Families: `24`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 3 |
| Medium eval-overlap items | 6 |
| POS-weak items | 1 |
| Definition-like sentence items | 2 |
| Target lemma in evidence note | 1 |
| Items with model POS-frame labels | 0 |
| Items with model topic-frame labels | 0 |
| High shadow-confusable items | 1 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 48 | 0.7363 | 0.5208 | 1 | 23 | 22 | 1 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 48 | 0.7363 | 0.5208 | 1 | 23 | 22 | 1 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 48 | 0.7363 | 0.5417 | 2 | 22 | 23 | 2 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 48 | 0.5055 | 0.0833 | 1 | 44 | 1 | 1 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 45 | 0.7253 | 0.4792 | 0 | 25 | 20 | 0 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 45 | 0.7363 | 0.5000 | 0 | 24 | 21 | 0 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 47 | 0.7143 | 0.5000 | 2 | 24 | 21 | 2 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 46 | 0.7363 | 0.5417 | 2 | 22 | 23 | 2 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 41 | 0.6923 | 0.4167 | 0 | 28 | 17 | 0 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 24 | 0.6154 | 0.2708 | 0 | 35 | 11 | 1 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 48 | 0.7363 | 0.5417 | 2 | 22 | 23 | 2 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `sentence_only_all`
- `en-es:full-family-repaired-full:bridle:reprimir:004`: He began to bridle at the accusation.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:rebate:descuento:001`: The store offered a rebate on the new refrigerator.

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
- Add an admission or postprocess guard for target lemmas inside evidence_note, even though sentence-level target leakage was already blocked.

## Limitations

- `offline no-spend postprocess over already generated active-only rows`
- `heuristic POS and overlap labels are diagnostic, not gold labels`
- `note-only views are diagnostics and should not be promoted as runtime evidence`
- `same selected-family denominator is held across views for comparability`
- `this does not validate shadow or no-winner generation at scale`
