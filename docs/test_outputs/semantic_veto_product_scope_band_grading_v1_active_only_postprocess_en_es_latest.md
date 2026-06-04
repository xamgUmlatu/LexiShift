# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T22:30:43Z`
- Active generated items audited: `36`
- Families: `18`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 1 |
| Medium eval-overlap items | 4 |
| POS-weak items | 12 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 0 |
| Items with model topic-frame labels | 0 |
| High shadow-confusable items | 0 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 36 | 0.6571 | 0.3889 | 2 | 22 | 15 | 2 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 36 | 0.6571 | 0.3889 | 2 | 22 | 15 | 2 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 36 | 0.6857 | 0.4444 | 2 | 20 | 17 | 2 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 36 | 0.4857 | 0.0556 | 2 | 34 | 3 | 2 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 35 | 0.6571 | 0.3611 | 1 | 23 | 14 | 1 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 35 | 0.6857 | 0.4167 | 1 | 21 | 16 | 1 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 24 | 0.6429 | 0.3333 | 1 | 24 | 13 | 1 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 36 | 0.6857 | 0.4444 | 2 | 20 | 17 | 2 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 23 | 0.6429 | 0.3056 | 0 | 25 | 12 | 0 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 18 | 0.5714 | 0.1667 | 0 | 30 | 7 | 0 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 36 | 0.6857 | 0.4444 | 2 | 20 | 17 | 2 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:except:excepto:004`: The report will except incomplete surveys from the total.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.
- `en-es:full-family-repaired-full:except:excepto:004`: The report will except incomplete surveys from the total.

### `sentence_only_all`
- `en-es:full-family-repaired-full:bar:cercar:003`: They met at the bar after work.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:cite:mencionar:005`: The dashboard listed Cite as an internal project code.
- `en-es:full-family-repaired-full:except:excepto:004`: The report will except incomplete surveys from the total.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:except:excepto:004`: The report will except incomplete surveys from the total.

### `no_high_eval_overlap_sentence_only`
- `en-es:full-family-repaired-full:bar:cercar:003`: They met at the bar after work.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:bar:cercar:003`: They met at the bar after work.
- `en-es:full-family-repaired-full:smile:sonre-r:003`: Her smile returned after the good news.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:bar:cercar:003`: They met at the bar after work.
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
