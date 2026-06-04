# Semantic Veto SRS Source Stack Audit (`en-es`)

Generated: `2026-05-16T18:29:52+00:00`

## Summary

- Status: `review`
- Recommended stack: `freq-es-cde_seed_plus_spalex_expansion_plus_kaikki_enrichment`
- SPALEX clean distinct rows: `44853`
- Current CDE distinct rows: `1984`
- Combined distinct candidates: `45131`
- Current CDE rows missing from SPALEX: `278`

## Target Readiness

| Target | Reaches | CDE rows | SPALEX-added rows | Kaikki headwords | POS mapped | Explicit topics | Medicine signal | Reverse target |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2000 | True | 1984 | 16 | 1906 (95.3%) | 1999 (100.0%) | 236 (11.8%) | 60 (3.0%) | 1804 (90.2%) |
| 5000 | True | 1984 | 3016 | 4796 (95.9%) | 4842 (96.8%) | 733 (14.7%) | 130 (2.6%) | 4689 (93.8%) |
| 10000 | True | 1984 | 8016 | 9469 (94.7%) | 9435 (94.3%) | 1353 (13.5%) | 248 (2.5%) | 9201 (92.0%) |

## Findings

- `PASS` `SPALEX_REACHES_10K`: SPALEX has 44853 clean distinct spellings, enough for a 10k expansion frontier.
- `REVIEW` `SPALEX_NOT_STANDALONE_REPLACEMENT`: 278 current CDE lemmas are absent from SPALEX, so the first stack should retain CDE as a seed/baseline.
- `PASS` `KAIKKI_COVERS_COMBINED_10K`: Installed Kaikki covers 9469 / 10000 combined candidates as headwords.
- `PASS` `POS_BACKFILL_COVERS_COMBINED_10K`: CDE plus Kaikki POS maps 9435 / 10000 combined candidates.
- `REVIEW` `TOPIC_METADATA_REQUIRES_OVERLAY`: Explicit Kaikki topic coverage is useful but partial (1353 / 10000), so domain overlays and/or embedding-assisted tagging are still needed.
- `PASS` `MEDICINE_SEED_SIGNAL_EXISTS`: Kaikki provides an initial medicine/health signal for 248 / 10000 combined candidates.
- `REVIEW` `KAIKKI_LICENSE_AND_DUMP_PINNING_REQUIRED`: Kaikki enrichment remains promotion-review data until attribution, share-alike/GFDL posture, and dated dump identity are encoded in manifests.

## Source Roles

- `freq-es-cde`: keep as the current seed/baseline, especially because SPALEX does not cover every short/function-heavy current row.
- `SPALEX`: use as the candidate frontier expansion source with frequency, Zipf, and prevalence signals.
- `Kaikki/Wiktionary`: use as the POS/gloss/dictionary/topic enrichment layer, not as the primary ranking source.

## Recommended Next Steps

- Treat SPALEX as the leading open candidate-frontier source, but not as a standalone replacement for `freq-es-cde`.
- Prototype `freq-es-spalex-expanded-v1.sqlite` as a union: current CDE seed rows first, then SPALEX-ranked additions with field-level provenance.
- Backfill POS/gloss/topic metadata from the installed Kaikki forward pack and keep missing Kaikki rows explicit.
- Add a narrow topic overlay for medicine/health before claiming interest-tailored admission quality.
- Encode SPALEX CC BY attribution and Kaikki review-required attribution/share-alike/dump-pin requirements in source manifests before promotion.
- Run a neutral vs medicine-weighted SRS admission probe after the provisional source pack exists.
