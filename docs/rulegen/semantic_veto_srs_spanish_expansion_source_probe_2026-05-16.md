# en-es Spanish Expansion Source Probe - 2026-05-16

Status: research checkpoint
Role: Decision support / no-download candidate probe
Last updated: 2026-05-16
Last verified: 2026-05-16 with source-readiness audit and SRS Zipf bridge candidate frequency override
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
license_status = requires_review
```

This candidate is not installed, not committed as data, and not promoted. It is
only a shape/readiness probe.

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
3. Run source-readiness and SRS bridge on the candidate with candidate-specific
   artifact filenames.
4. Only then run full rulegen and denominator audit.

Do not overwrite `freq-es-cde`. Do not launch paid generation yet.
