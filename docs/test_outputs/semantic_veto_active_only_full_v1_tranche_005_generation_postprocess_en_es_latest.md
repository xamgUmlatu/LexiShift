# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-13T05:09:55Z`
- Active generated items audited: `74`
- Families: `37`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 0 |
| Medium eval-overlap items | 0 |
| POS-weak items | 74 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 7 |
| Items with model POS-frame labels | 0 |
| Items with model topic-frame labels | 0 |
| High shadow-confusable items | 0 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 0 | n/a | n/a | 0 | 0 | 0 | 0 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 0 | n/a | n/a | 0 | 0 | 0 | 0 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 37 | n/a | n/a | 0 | 0 | 0 | 0 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 74 | n/a | n/a | 0 | 0 | 0 | 0 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

## Recommendations

- Prefer sentence-only evidence for the next generated batch because it preserves or improves the control without explanatory-note leakage.
- Use the conservative sentence-only view as the safety check before any paid scale-up; it removes high-overlap and weak-POS rows while keeping the denominator fixed.
- Add an admission or postprocess guard for target lemmas inside evidence_note, even though sentence-level target leakage was already blocked.

## Limitations

- `offline no-spend postprocess over already generated active-only rows`
- `heuristic POS and overlap labels are diagnostic, not gold labels`
- `note-only views are diagnostics and should not be promoted as runtime evidence`
- `same selected-family denominator is held across views for comparability`
- `this does not validate shadow or no-winner generation at scale`
