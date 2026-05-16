# en-es Spanish Expansion Source Probe - 2026-05-16

Status: research checkpoint
Role: Decision support / no-download candidate probe
Last updated: 2026-05-16
Last verified: 2026-05-16 with source-readiness audit, POS backfill audit, and SRS Zipf bridge candidate frequency override
Related docs:
- `semantic_veto_srs_corpus_expansion_plan.md`
- `semantic_veto_srs_corpus_candidate_readiness_runbook.md`
- `semantic_veto_denominator_current_state.md`

## Purpose

This checkpoint pivots the en-es expansion work away from additional
provenance-policy seams and back to the product question:

> What Spanish source can actually move SRS admission beyond the current 2k
> sample while preserving enough quality evidence to rerun rulegen and the
> semantic-veto denominator?

No external dataset was downloaded for this probe.

## Current Baseline Finding

The current installed Spanish frequency pack remains the frozen comparison
baseline:

- installed pack: `freq-es-cde.sqlite`,
- rows: `2,000`,
- distinct non-empty lemmas: `1,984`,
- rank/order column: `id`,
- frequency column: `freq`,
- POS coverage: `100%`,
- topic/domain coverage: `0%`.

Local search did not find a hidden `spanish_lemmas20k.txt` source file in the
repo or LexiShift application-support data root. The catalog/runbook notes
identify the current CDE/wordfrequency artifact as a sample-sized file, about
2,000 rows, every 10th rank from a larger 20k list.

Interpretation: the current ceiling is not just an audit artifact. The app is
really operating from a sample-sized Spanish frequency source.

## No-Download Candidate Probe

The global Python environment on this machine already has `wordfreq` installed
as version `3.1.1`; the repo `.venv` does not. I used that existing local
package to create a temporary SQLite candidate at:

```text
/tmp/lexishift_wordfreq_es_10k.sqlite
```

Temporary build shape:

```text
source_provider = wordfreq
source_version = 3.1.1
source_profile = wordfreq_es_best_10k
build_command = python wordfreq top_n_list(es, 10000, wordlist=best)
license_status = requires_attribution_sharealike_review
```

This candidate is not installed, not committed as data, and not promoted. It is
only a shape/readiness probe.

## License Posture

The locally installed `wordfreq 3.1.1` package metadata reports Apache-2.0 for
the package itself, but its own metadata also says the included data files may be
redistributed under Creative Commons Attribution-ShareAlike 4.0. It also records
source-specific acknowledgement/attribution requirements for Google Books
Ngrams, OPUS/OpenSubtitles, and SUBTLEX-derived data.

Interpretation: this is acceptable for local diagnostic testing, but not yet a
promotion-grade source license decision. A shipped or app-managed `wordfreq`
derived pack would need explicit attribution/sharealike handling in pack
metadata, docs, and any distribution bundle.

## Source-Readiness Result

Command:

```bash
python3 scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py \
  --candidate-db /tmp/lexishift_wordfreq_es_10k.sqlite \
  --json-out /tmp/lexishift_wordfreq_es_10k_audit.json \
  --markdown-out /tmp/lexishift_wordfreq_es_10k_audit.md
```

Result:

| Metric | Value |
| --- | ---: |
| Rows | `10,000` |
| Distinct non-empty lemmas | `10,000` |
| Reaches 5k | `true` |
| Reaches 10k | `true` |
| Rank column | `id` |
| Frequency column | `freq` |
| POS coverage | `0%` |
| Topic/domain coverage | `0%` |

Issues:

- `missing_or_empty_pos_column`
- `missing_or_empty_topic_domain_metadata`

Interpretation: a 10k Spanish source is locally testable and clears the raw
size/rank/frequency ceiling, but it is not promotion-ready because POS and
topic/domain metadata are absent and source/license policy is not reviewed.

## POS Backfill Probe

Because the candidate frequency DB has no POS column, I tested whether the
already-installed Spanish-headword lexical resources can backfill POS without
installing or mutating the candidate.

Command:

```bash
python3 scripts/testing/semantic_veto_srs_candidate_pos_backfill_audit_en_es.py \
  --candidate-db /tmp/lexishift_wordfreq_es_10k.sqlite \
  --json-out /tmp/lexishift_wordfreq_es_10k_pos_backfill_audit.json \
  --markdown-out /tmp/lexishift_wordfreq_es_10k_pos_backfill_audit.md
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate unique lemmas | `10,000` |
| Lemmas with any external POS | `5,497` |
| Lemmas with mapped POS | `5,036` |
| Lemmas with confident weighted lexical bucket | `4,122` |
| Ambiguous raw POS lemmas | `1,101` |
| Wiktionary ES-EN candidate hits | `5,497` |
| FreeDict ES-EN candidate hits | `0` |

Rank-band signal:

| Candidate Band | Any POS | Mapped POS | Confident Weighted Bucket | Ambiguous Raw POS |
| ---: | ---: | ---: | ---: | ---: |
| Top 100 | `78%` | `77%` | `18%` | `42%` |
| Top 500 | `72%` | `70%` | `35%` | `29%` |
| Top 1,000 | `72%` | `69%` | `44%` | `24%` |
| Top 2,000 | `69%` | `65%` | `47%` | `19%` |
| Top 5,000 | `62%` | `57%` | `45%` | `14%` |
| Top 10,000 | `55%` | `50%` | `41%` | `11%` |

Filter scenario signal:

| Scenario | Kept | Top 100 | Top 500 | Top 1,000 |
| --- | ---: | ---: | ---: | ---: |
| All candidate rows | `10,000` | `100` | `500` | `1,000` |
| Surface-clean rows | `9,981` | `98` | `491` | `989` |
| Mapped POS | `5,036` | `77` | `348` | `685` |
| Mapped POS, non-ambiguous, surface-clean | `3,936` | `35` | `203` | `445` |
| Confident weighted bucket | `4,122` | `18` | `175` | `436` |

Interpretation: installed Wiktionary ES-EN gives enough exact-headword POS
signal to make a 5k shortlist plausible, but not enough to claim 10k POS-ready
coverage. The confident weighted-bucket count is below 5k because ambiguous POS
rows are treated conservatively. The installed FreeDict ES-EN SQLite exists but
has no usable POS rows in this local pack. The top-rank bands are especially
ambiguous, which suggests this `wordfreq` candidate includes common function
words, forms, and numerals that need explicit filtering or defaulting policy
before promotion. Basic numeric/surface filtering barely changes the candidate;
the real quality decision is how strict to be about POS ambiguity and function
word/defaulting policy.

## Baseline Overlap

Quick overlap against the current installed `freq-es-cde.sqlite` baseline:

| Comparison | Count |
| --- | ---: |
| Current unique lemmas | `1,984` |
| Candidate unique lemmas | `10,000` |
| Current lemmas also in candidate | `509` |
| Current overlap share | `25.7%` |
| Candidate lemmas not in current baseline | `9,491` |
| Candidate top-2k lemmas not in current baseline | `1,861` |

Interpretation: the candidate is not a continuity-preserving replacement for
the CDE sample. It would be a substantially different Spanish source, which may
be good for broad coverage but requires explicit product/source review.

## SRS Bridge Candidate Override Result

The SRS Zipf bridge now accepts a candidate frequency DB without installing it:

```bash
python3 scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py \
  --frequency-db /tmp/lexishift_wordfreq_es_10k.sqlite \
  --full-srs-top-n 10000 \
  --json-out /tmp/lexishift_wordfreq_es_10k_bridge.json \
  --markdown-out /tmp/lexishift_wordfreq_es_10k_bridge.md
```

Result:

| Metric | Value |
| --- | ---: |
| Full SRS-admissible target count | `10,000` |
| Full target very-common/common count | `7,247` |
| Full target very-common/common share | `72.5%` |
| Full source-target pairs | `0` |
| Full source mapping status | `skipped` |

This run did not include full rulegen. That is intentional: the candidate is
not source-ready enough yet to justify an expensive full downstream denominator
refresh.

## Decision Implications

1. The raw Spanish corpus-size ceiling is solvable.
2. The next real blocker is not another provenance seam; it is candidate source
   quality:
   - POS tagging/backfill,
   - source/license review,
   - stopword/noise filtering,
   - continuity decision versus the current CDE sample,
   - then full rulegen and denominator yield.
3. Topic/domain metadata remains a separate overlay track. Missing topic/domain
   tags should not block a 5k-10k general-frequency candidate, but it must block
   any claim of topic-personalized SRS coverage.
4. The SRS bridge can now evaluate a candidate before install/promotion, so the
   next iteration can compare multiple candidate SQLite files without touching
   `freq-es-cde`.

## Recommended Next Work

Preferred next slice:

1. Choose one candidate strategy for a real comparison pack:
   - local/manual `wordfreq` candidate with explicit source/license review,
   - a recovered/manual CDE 20k source if the user can supply it under license,
   - a licensing-safe corpus pipeline,
   - or a hybrid frequency plus overlay candidate.
2. Add or choose a POS backfill path for that candidate before full rulegen.
3. Use the POS backfill audit to decide whether the target is a safe 5k
   shortlist, a 10k candidate needing more metadata, or not worth promoting.
4. Run source-readiness and SRS bridge on the candidate with candidate-specific
   artifact filenames.
5. Only then run full rulegen and denominator audit.

Do not overwrite `freq-es-cde`. Do not launch paid generation yet.
