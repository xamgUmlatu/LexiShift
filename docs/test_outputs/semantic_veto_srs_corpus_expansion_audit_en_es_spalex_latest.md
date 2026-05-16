# en-es SRS Corpus Expansion Audit

- Status: `ok`
- Decision: `srs_corpus_expansion_candidates_audited`
- Generated: `2026-05-16T18:40:40.905394+00:00`
- Candidate DBs: `1`
- Current candidate unique lemmas: `45131`
- Largest candidate unique lemmas: `45131`
- Candidate reaching 5k: `True`
- Candidate reaching 10k: `True`

## Why This Exists

Compare possible Spanish learner-corpus/frequency-pack sources before expanding SRS admission, rulegen denominator, or semantic-veto generation.

This is a source-readiness audit. It does not change SRS admission, rulegen, semantic-veto evidence, runtime policy, or paid generation.

## Candidate Summary

| Candidate | Status | Unique Lemmas | Rows | Rank | Frequency | POS Share | Topic Share | Issues |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| `current_bridge_frequency_db` | `ok` | 45131 | 45131 | `id` | `pmw` | 75.3% | 9.1% | `none` |

## Target Readiness

| Candidate | Target | Reaches Target | Shortfall | Available Share |
| --- | ---: | --- | ---: | ---: |
| `current_bridge_frequency_db` | 2000 | `True` | 0 | 100.0% |
| `current_bridge_frequency_db` | 5000 | `True` | 0 | 100.0% |
| `current_bridge_frequency_db` | 10000 | `True` | 0 | 100.0% |

## Candidate Source Research Matrix

| Source Family | What It Could Improve | Main Risk | First Check |
| --- | --- | --- | --- |
| Recovered or rebuilt Spanish 20k frequency list | Fastest path if it preserves the current pack's ordering semantics. | May still lack topic/domain metadata and license/provenance clarity. | Confirm provenance, row count, POS coverage, and pack schema. |
| General frequency corpus | Broad 5k-10k coverage for ordinary browsing and SRS. | Frequency alone may overvalue function words or weak learner targets. | Measure lemma/POS quality and compare overlap with current 2k. |
| Learner-level or CEFR-style list | Better alignment with staged learner progression. | May be smaller, licensed restrictively, or missing frequency values. | Check level coverage and mergeability with frequency ranks. |
| Dictionary-derived lemma expansion | Large coverage without waiting for a frequency source. | No natural ranking; may admit obscure or awkward lemmas. | Require rank backfill, POS validation, and exclusion filters. |
| Domain/topic overlays | Makes user preference SRS useful for medicine, law, travel, etc. | Domain value is high but general-frequency comparability is weak. | Keep source/domain tags and blend as an overlay, not a replacement. |
| Hybrid base-frequency plus overlays | Most product-aligned path: general coverage plus user-specific depth. | Merge policy can hide provenance and duplicate lemmas if not audited. | Version the merged pack and audit per-source contribution. |

## Recommended Next Steps

1. Keep the current 2k frequency pack frozen as the baseline denominator.
2. Recover or recreate the apparent Spanish 20k source before choosing a new corpus source.
3. Run this audit on every candidate SQLite pack and compare row count, unique lemmas, POS coverage, and topic/domain coverage.
4. After selecting a candidate source, rerun the SRS Zipf bridge with full rulegen and then refresh the semantic-veto denominator audit.
