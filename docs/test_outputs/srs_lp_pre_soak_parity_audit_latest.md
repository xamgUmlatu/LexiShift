# SRS LP Pre-Soak Parity Audit

- Generated: 2026-07-04
- Scope: SRS difficulty ranking, topic preference coverage, browsing-interest mining, admission refresh, profile/journey/runtime harnesses, and Options topic exposure for `en-ja`, `en-es`, and `en-de`.
- Explicitly out of scope: full rulegen benchmark quality, semantic-veto product-scope quality, and non-SRS replacement quality except where they affect SRS admission or publication.
- Worktree note: this audit includes the current parity fixes, including English-source mining for `en-es`/`en-de`, casefolded aggregate lookup for German target lemmas, and an explicit strict-MVP topic allowlist for `en-es`.

## Executive Summary

`en-ja` is the only pair with a product-reviewed learner difficulty ranking. `en-es` and `en-de` currently use the generic frequency-proxy difficulty fallback. That is the largest product-quality gap.

`en-es` is much closer than `en-de` on topic/product scaffolding: it has a topic taxonomy, release-readiness artifacts, beta preflight, and journey harnesses. The artifacts still say limited depth and manual beta signoff are required. `en-de` has synthetic SRS harness coverage and now runtime browsing-mining smoke coverage, but lacks pair-specific topic taxonomy, topic release review, and journey harness coverage.

The safest path is:

1. Land the current browsing-mining parity infra fixes.
2. Add a cheap difficulty sample review for `en-es` and `en-de` instead of attempting full en-ja-style calibration immediately.
3. Make remaining topic exposure pair-safe: `en-es` should stay on its strict-MVP 10-topic picker; `en-de` should either receive an explicit minimal taxonomy/review artifact or have unsupported topic UX clearly disabled.
4. Add/align harness coverage so the pre-soak evidence for each LP is explicit rather than inferred from another pair.

## Readiness Matrix

| Area | `en-ja` | `en-es` | `en-de` | Audit judgment |
| --- | --- | --- | --- | --- |
| Learner difficulty ranking | Packaged corrected CSV plus exact/manual overlay. | Generic `1 - base_weight` frequency proxy only. | Generic `1 - base_weight` frequency proxy only. | Biggest gap for the other LPs. |
| Difficulty review artifacts | Extensive calibration, holdout, full-range sample, first-N review, manual correction artifacts. | No comparable SRS learner-difficulty workstream found. | No comparable SRS learner-difficulty workstream found. | Need at least sample review before soak. |
| Topic taxonomy | `srs_topic_preference_taxonomy_en_ja.json`; broad source-readiness work. | `srs_topic_preference_taxonomy_en_es.json`; status `planning`, but release-readiness artifact classifies strict MVP topics. | No `srs_topic_preference_taxonomy_en_de.json`. | `en-es` partial; `en-de` missing. |
| Topic autotag policy | `srs_topic_autotag_policy_en_ja.json`. | Missing. | Missing. | Do not imply en-ja-style autotag coverage outside `en-ja`. |
| Options topic picker | Static picker exposes 10 chips; en-ja support set is broader than visible picker. | Static picker exposes the same 10 chips; explicit strict-MVP support set now prevents accidental future topic exposure. | Static picker exposes 10 chips; explicit support set disables `animals` and `food_cooking`, and includes `travel_places_transport` even though no travel chip is visible. | `en-de` topic UX needs product review; `en-es` picker is now pair-safe for the current strict MVP set. |
| Topic release evidence | Deep current en-ja topic review and overlays. | `srs_topic_release_readiness_en_es_latest.md`: status `ok`, but limited depth; strict MVP exposure is 10 topics. | None found. | `en-es` can be limited beta after manual signoff; `en-de` cannot claim topic parity. |
| Beta preflight | Not the limiting pair for this audit. | `srs_beta_preflight_en_es_latest.md`: status `REVIEW`; automated checks pass but manual beta signoff pending. | None found. | `en-es` still requires manual beta signoff. |
| SRS quality harness | Covered. | Not in `SUPPORTED_SYNTHETIC_PAIRS`. | Covered. | Add en-es or explicitly route to journey harness evidence. |
| SRS journey harness | Fixture and latest artifacts exist. | Fixture and latest artifacts exist; current summaries are WARN, not FAIL. | No pair fixture found. | `en-de` needs fixture or equivalent smoke before soak. |
| Browsing mining runtime smoke | Current local smoke passes. | Current local smoke passes after local source-mining parity change. | Current local smoke passes after local source-mining parity and casefold lookup changes. | Infra is now close; keep tests committed. |
| Saved-page browsing configs | Exists for en-ja. | Missing. | Missing. | Runtime smoke covers the core path, but saved-page review tooling is not pair-parity. |

## Evidence Notes

- Difficulty code is pair-specific: `estimate_learner_difficulty()` checks for `pair == "en-ja"` and otherwise returns the frequency proxy.
- Packaged SRS difficulty resources only exist under `core/lexishift_core/resources/srs/en_ja/`.
- Profile bootstrap uses `frequency_difficulty = 1.0 - source_commonness`, so non-en-ja difficulty is only as good as the base candidate weight/commonness source.
- Current topic input files found:
  - `docs/test_inputs/srs_topic_preference_taxonomy_en_ja.json`
  - `docs/test_inputs/srs_topic_preference_taxonomy_en_es.json`
  - `docs/test_inputs/srs_topic_autotag_policy_en_ja.json`
  - `docs/test_inputs/srs_browsing_admission_saved_page_admission_configs_en_ja.json`
- No matching en-de taxonomy, en-es/en-de autotag policy, or en-es/en-de saved-page config was found.
- `scripts/testing/srs_quality_harness.py` currently supports `en-ja` and `en-de`.
- `scripts/testing/srs_journey_harness_support.py` currently has pair fixtures for `en-ja` and `en-es`.
- Existing en-es beta preflight says automated checks are clean but manual signoff remains pending.

## Must Fix Before Multi-LP Soak

1. Commit/land the current parity fixes.
   - Reason: without these changes, source browsing mining was effectively en-ja-only, German target aggregate lookup could miss casefolded terms like lowercase store keys versus titlecase candidate lemmas, and en-es topic support depended on the current static picker staying narrow forever.

2. Decide `en-de` topic exposure policy.
   - Option A: keep only a very small explicit en-de topic picker until taxonomy/review exists.
   - Option B: hide or disable topic preferences for en-de in the SRS setup flow.
   - Option C: create a minimal en-de taxonomy/release-readiness artifact and sample it.
   - Recommended for speed: Option A or B before tester soak, then Option C after.

3. Generate current-ranking samples for `en-es` and `en-de`.
   - This is not a full calibration workstream. It is a sanity review of frequency-proxy ranking by proficiency band so we know whether the first user experience is acceptable.
   - Minimum useful output: 20-40 random candidates per broad band, plus first 100-200 admission candidates for a normal beginner profile.

4. Give en-es a current explicit SRS pre-soak evidence path.
   - Either add en-es to the core SRS quality harness or document/run the en-es journey harness as the canonical equivalent.
   - Current en-es journey artifacts are WARN due publication-scope behavior, not FAIL, but that warning should be consciously accepted or resolved.

5. Add an en-de journey fixture or equivalent profile bootstrap smoke.
   - en-de has core SRS quality harness coverage, but lacks the journey/profile UX evidence en-es has.

## Should Fix Soon

1. Add pair-specific topic release/readiness artifacts for en-de.
2. Add saved-page browsing/admission configs or explicitly declare runtime smoke as the pair-generic replacement for en-es/en-de.
3. Add a compact difficulty correction layer for the most obvious first-200 failures in en-es/en-de after sample review.
4. Add a report that compares topic-match share in sampled admission for the 10 visible topic chips, per LP.

## Not Required Before Soak

1. Full en-ja-style difficulty sweeps/calibration for en-es and en-de.
2. Deep topic expansion for en-de.
3. Contextual English disambiguation beyond current conservative source mining.
4. Broad target-language page mining without reliable reading/lemma disambiguation.

## Recommended Next Work

The next practical slice should be a pair-parity hardening slice:

1. Decide and implement conservative en-de topic exposure.
2. Add or run generated sample packs for en-es/en-de difficulty/admission bands.
3. Add the missing harness bridge: en-es core SRS quality inclusion or en-es journey-as-canonical documentation; en-de journey/profile smoke.
4. Rerun SRS quality, runtime smoke for all three pairs, and targeted tests for the changed modules.

Expected outcome: we will know which LPs are safe for tester soak as-is, which are safe only with topics disabled/limited, and whether the frequency-proxy difficulty ranking is visibly acceptable for en-es/en-de beginners.
