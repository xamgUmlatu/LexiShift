# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess

- Status: `ok`
- Decision: `generated_evidence_postprocess_ready_for_interpretation`
- Generated: `2026-05-09T22:52:38Z`
- Active generated items audited: `32`
- Families: `16`

## Audit Counts

| Count | Value |
| --- | ---: |
| High eval-overlap items | 0 |
| Medium eval-overlap items | 8 |
| POS-weak items | 4 |
| Definition-like sentence items | 0 |
| Target lemma in evidence note | 0 |
| Items with model POS-frame labels | 0 |
| Items with model topic-frame labels | 0 |
| High shadow-confusable items | 0 |

## View Bakeoff

| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `all_sentence_plus_note` | 32 | 0.6825 | 0.4375 | 2 | 18 | 11 | 3 | control: current scoring appends generated sentence plus evidence_note |
| `sentence_plus_scrubbed_note` | 32 | 0.6825 | 0.4375 | 2 | 18 | 11 | 3 | mechanically remove target lemmas and meta labels from evidence_note |
| `sentence_only_all` | 32 | 0.7143 | 0.5000 | 2 | 16 | 12 | 2 | use generated browser sentences only, dropping explanatory notes |
| `note_only_diagnostic` | 32 | 0.5079 | 0.0625 | 1 | 30 | 0 | 3 | diagnostic: evidence_note only, to see whether notes are driving lift |
| `no_high_eval_overlap_sentence_plus_note` | 32 | 0.6825 | 0.4375 | 2 | 18 | 11 | 3 | drop generated rows with high lexical overlap against frozen eval cases |
| `no_high_eval_overlap_sentence_only` | 32 | 0.7143 | 0.5000 | 2 | 16 | 12 | 2 | drop high eval-overlap rows and use sentence-only evidence |
| `pos_anchored_sentence_only` | 28 | 0.7143 | 0.4688 | 1 | 17 | 11 | 1 | keep rows whose generated source usage mechanically matches expected POS |
| `no_definition_like_sentence_only` | 32 | 0.7143 | 0.5000 | 2 | 16 | 12 | 2 | drop definition-like generated browser sentences and use sentence-only evidence |
| `conservative_sentence_only` | 28 | 0.7143 | 0.4688 | 1 | 17 | 11 | 1 | sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability |
| `quality_top1_sentence_only` | 16 | 0.6508 | 0.3125 | 0 | 22 | 6 | 0 | keep one highest-quality sentence-only row per family |
| `quality_top2_sentence_only` | 32 | 0.7143 | 0.5000 | 2 | 16 | 12 | 2 | keep up to two highest-quality sentence-only rows per family after audit scoring |

## Regressions By View

### `all_sentence_plus_note`
- `en-es:full-family-repaired-full:continue:durar:001`: The drought may continue for months.
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `sentence_plus_scrubbed_note`
- `en-es:full-family-repaired-full:continue:durar:001`: The drought may continue for months.
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `sentence_only_all`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `note_only_diagnostic`
- `en-es:full-family-repaired-full:continue:durar:001`: The drought may continue for months.
- `en-es:full-family-repaired-full:billow:oleaje:004`: The curtain started to billow in the wind.
- `en-es:full-family-repaired-full:pair:par:001`: She bought a pair of gloves at the market.

### `no_high_eval_overlap_sentence_plus_note`
- `en-es:full-family-repaired-full:continue:durar:001`: The drought may continue for months.
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `no_high_eval_overlap_sentence_only`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `pos_anchored_sentence_only`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.

### `no_definition_like_sentence_only`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

### `conservative_sentence_only`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.

### `quality_top2_sentence_only`
- `en-es:full-family-repaired-full:billow:oleaje:003`: Smoke began to billow from the warehouse.
- `en-es:full-family-repaired-full:snore:roncar:003`: A loud snore came from the next room.

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
