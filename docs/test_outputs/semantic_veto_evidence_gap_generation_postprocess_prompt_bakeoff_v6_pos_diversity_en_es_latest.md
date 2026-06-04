# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T00:20:45Z`
- Active generated items audited: `47`
- Families: `24`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 1 |
| Medium eval-overlap items | 5 |
| POS-weak items | 1 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 47 |
| Items with model topic-frame labels | 47 |
| High shadow-confusable items | 0 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 47 | 0.6044 | 0.3333 | 4 | 32 | 12 | 3 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 47 | 0.6044 | 0.3333 | 4 | 32 | 12 | 3 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 47 | 0.6923 | 0.4375 | 1 | 27 | 19 | 2 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 47 | 0.4725 | 0.1042 | 5 | 43 | 1 | 4 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 46 | 0.5934 | 0.3125 | 4 | 33 | 11 | 3 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 46 | 0.6813 | 0.4167 | 1 | 28 | 18 | 2 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 46 | 0.6813 | 0.4167 | 1 | 28 | 18 | 2 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 47 | 0.6923 | 0.4375 | 1 | 27 | 19 | 2 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 45 | 0.6703 | 0.3958 | 1 | 29 | 17 | 2 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 24 | 0.5714 | 0.2083 | 1 | 38 | 8 | 2 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 47 | 0.6923 | 0.4375 | 1 | 27 | 19 | 2 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:control:gobernar:005`: The dashboard listed Control as an internal project code.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:govern:gobernar:005`: The dashboard listed Govern as an internal project code.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:control:gobernar:005`: The dashboard listed Control as an internal project code.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:govern:gobernar:005`: The dashboard listed Govern as an internal project code.

### `sentence_only_all`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:control:gobernar:005`: The dashboard listed Control as an internal project code.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:german:alem-n:003`: The dashboard listed German as an internal project code.
- `en-es:full-family-repaired-full:govern:gobernar:005`: The dashboard listed Govern as an internal project code.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:control:gobernar:005`: The dashboard listed Control as an internal project code.
- `en-es:full-family-repaired-full:begin:comenzar:003`: The dashboard listed Begin as an internal project code.
- `en-es:full-family-repaired-full:govern:gobernar:005`: The dashboard listed Govern as an internal project code.

### `no_high_eval_overlap_sentence_only`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `conservative_sentence_only`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

### `quality_top1_sentence_only`
- `en-es:full-family-repaired-full:break:quebrar:002`: A dry branch can break under sudden pressure.
- `en-es:full-family-repaired-full:smile:sonre-r:004`: She used a smile to thank the nurse.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:adjoining:vecino:001`: The adjoining farm belongs to a neighboring family.
- `en-es:full-family-repaired-full:acceptable:razonable:004`: The sample was acceptable for laboratory testing.

## Recommendations

- Treat evidence_note text as an active experimental variable; note-only evidence moved decisions, so sentence-only should be the safer promotion candidate.
- Do not promote raw evidence_note text without scrubbing; the note-only diagnostic widened harmful replacements.
- Prefer sentence-only evidence for the next generated batch because it preserves or improves the control without explanatory-note leakage.
- Use the conservative sentence-only view as the safety check before any paid scale-up; it removes high-overlap and weak-POS rows while keeping the denominator fixed.

## Limitations

- `offline no-spend postprocess over already generated active-only rows`
- `heuristic POS and overlap labels are diagnostic, not gold labels`
- `note-only views are diagnostics and should not be promoted as runtime evidence`
- `same selected-family denominator is held across views for comparability`
- `this does not validate shadow or no-winner generation at scale`
