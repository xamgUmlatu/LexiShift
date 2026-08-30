# Semantic Veto SRS Source Stack Audit (`en-es`)

Generated: `2026-06-07T19:13:39+00:00`

## Summary

- Status: `review`
- Recommended stack: `spalex_only_publishable_frontier_plus_optional_kaikki_enrichment_with_freq_es_cde_internal_benchmark`
- SPALEX clean distinct rows: `44853`
- Current CDE distinct rows: `1984`
- Combined distinct candidates: `45131`
- Current CDE rows missing from SPALEX: `278`

## Target Readiness

| Target | Reaches | CDE rows | SPALEX-added rows | Kaikki headwords | POS mapped | Explicit topics | Medicine signal | Reverse target |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2000 | True | 1984 | 16 | 1343 (67.2%) | 1999 (100.0%) | 195 (9.8%) | 48 (2.4%) | 1804 (90.2%) |
| 5000 | True | 1984 | 3016 | 4129 (82.6%) | 4732 (94.6%) | 683 (13.7%) | 118 (2.4%) | 4689 (93.8%) |
| 10000 | True | 1984 | 8016 | 7687 (76.9%) | 8236 (82.4%) | 1182 (11.8%) | 229 (2.3%) | 9201 (92.0%) |

## Findings

- `PASS` `SPALEX_REACHES_10K`: SPALEX has 44853 clean distinct spellings, enough for a 10k expansion frontier.
- `REVIEW` `SPALEX_NOT_STANDALONE_REPLACEMENT`: 278 current CDE lemmas are absent from SPALEX. Keep the CDE-seed union as an internal continuity benchmark, not as a publishable pack dependency.
- `REVIEW` `TOPIC_METADATA_REQUIRES_OVERLAY`: Explicit Kaikki topic coverage is useful but partial (1182 / 10000), so domain overlays and/or embedding-assisted tagging are still needed.
- `PASS` `MEDICINE_SEED_SIGNAL_EXISTS`: Kaikki provides an initial medicine/health signal for 229 / 10000 combined candidates.
- `REVIEW` `KAIKKI_LICENSE_AND_DUMP_PINNING_REQUIRED`: Kaikki enrichment remains promotion-review data until attribution, share-alike/GFDL posture, and dated dump identity are encoded in manifests.

## Source Roles

- `SPALEX`: use as the publishable candidate frontier source with frequency, Zipf, and prevalence signals.
- `freq-es-cde`: keep only as the current manual-supply/internal benchmark; do not make it a dependency of publishable SPALEX packs.
- `Kaikki/Wiktionary`: use as the POS/gloss/dictionary/topic enrichment layer, not as the primary ranking source.

## Recommended Next Steps

- Treat SPALEX as the leading publishable candidate-frontier source.
- Prototype `freq-es-spalex-v1` as SPALEX-only, with optional Kaikki POS/topic enrichment tracked as a review-gated component.
- Keep `freq-es-spalex-expanded-v1` as a CDE-seed union only for internal comparison against the current manual-supply baseline.
- Backfill POS/gloss/topic metadata from the installed Kaikki forward pack and keep missing Kaikki rows explicit.
- Add a narrow topic overlay for medicine/health before claiming interest-tailored admission quality.
- Encode SPALEX CC BY attribution and Kaikki review-required attribution/share-alike/dump-pin requirements in source manifests before promotion.
- Run a neutral vs medicine-weighted SRS admission probe after the provisional source pack exists.
