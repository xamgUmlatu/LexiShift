# Interest-Tailored SRS Data Acquisition Plan

Status: active data planning reference
Role: Planning / WIP
Last updated: 2026-05-17
Last verified: 2026-05-17 by current en-es source-readiness findings, SPALEX + Kaikki source-stack audit, provisional SPALEX pack build/audits, SRS profile/admission docs, and interest-tailored admission algorithm review
Purpose: enumerate the data needed to make interest-tailored SRS admission real, identify what is missing now, and define a practical acquisition strategy
Source-of-truth: data acquisition plan; current executable truth lives in SRS seed/admission code, installed pack manifests, generated source-readiness audits, and promoted source packs.

Related docs:
- `srs_interest_tailored_admission_algorithm.md`
- `srs_profile_schema.md`
- `srs_set_planning_technical.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../rulegen/semantic_veto_srs_corpus_candidate_readiness_runbook.md`
- `../test_outputs/semantic_veto_srs_source_stack_audit_en_es_latest.md`
- `../test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_spalex_latest.md`
- `../test_outputs/pack_lifecycle_audit_spalex_latest.md`
- `../test_outputs/semantic_veto_srs_zipf_bridge_en_es_spalex_latest.md`
- `../test_outputs/semantic_veto_srs_zipf_bridge_en_es_spalex_10k_full_rulegen_latest.md`
- `../test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_10k_latest.md`

## Data-First Goal

Before making interest-tailored admission a default product behavior, collect
and normalize the data that the model needs. The algorithm should not pretend
to personalize from empty metadata.

The first target is not perfect global coverage. The first target is a complete,
auditable `en-es` candidate corpus that supports:

1. a larger general Spanish SRS frontier,
2. POS/function-word controls,
3. topic/domain tags for high-value categories such as medicine and health,
4. non-beginner readiness signals,
5. rulegen coverage evidence,
6. feedback-ready user profile signals.

## Missing Data Summary

Current `en-es` state is useful but not enough for the target model.

| Data Class | Current State | Missing For Target Model |
| --- | --- | --- |
| General Spanish candidate size | Installed baseline has `2,000` rows and `1,984` distinct non-empty lemmas. SPALEX has `44,853` clean distinct spellings; CDE seed plus SPALEX expansion yields `45,131` distinct candidates. | A promoted, license-cleared 5k-10k+ candidate frontier. |
| Frequency/rank | Current pack has usable rank/frequency. SPALEX has full `freq`, `zipf`, `percent_total`, and `prevalence_total` coverage. | Merge policy between current baseline and expansion source; field-level provenance. |
| POS | Current baseline has 100% POS. In the CDE-seed plus SPALEX-expansion audit, CDE plus installed Kaikki maps POS for `9,435 / 10,000` combined candidates. The provisional full pack has POS rows for `33,968 / 45,131`. | Promotion-grade POS policy for ambiguous/function-heavy candidates and Spanish stopwords. |
| Topic/domain metadata | Current baseline has `0%`. Installed Kaikki gives explicit topic rows for `1,353 / 10,000` combined candidates. The provisional full pack has topic rows for `4,114 / 45,131`. | Topic taxonomy, topic/domain tags, scalar memberships, confidence, and source provenance. |
| Medical/health domain support | Installed Kaikki gives an initial medicine/health-like signal for `248 / 10,000` combined candidates. | Health/medicine/dentistry topic family, aliases, domain lexicon, and validation set. |
| Difficulty/readiness | Frequency rank can proxy difficulty. Profile schema supports proficiency/challenge fields. | CEFR/learner-level overlay or calibrated difficulty model for non-beginner users. |
| Rulegen coverage | Current denominator evidence exists for current baseline; expanded candidate full-rulegen coverage was not promoted. | Per-candidate rulegen coverage cache for expanded corpus. |
| Semantic-veto coverage | Current semantic-veto coverage is measured for current admitted families. | Expanded denominator and uncovered-family audit after candidate source selection. |
| Source/license provenance | Current source has pack metadata. SPALEX Figshare metadata reports `CC BY 4.0`; Kaikki/Wiktionary enrichment still needs attribution/share-alike/GFDL posture and dated dump pinning. | Promotion manifests with source hash, license, attribution, and redistribution notes. |
| User interest profile | Existing profile context supports interests/topic weights in principle. | Scalar UX-to-profile mapping, confidence, decay, and explicit/inferred source separation. |
| Feedback adaptation | SRS feedback and signal queues exist as product seams. | Aggregation policy that updates interests, difficulty, and source preferences gradually. |

## Candidate Data Needed

Every candidate lemma should eventually have:

- normalized lemma and display form,
- LP key,
- frequency/rank score,
- POS and POS confidence,
- stopword/function-word class,
- topic vector,
- topic confidence,
- difficulty estimate,
- source confidence,
- rulegen coverage status,
- semantic-veto coverage status when browser replacement is expected,
- field-level provenance,
- license/promotion state.

Rows may be incomplete during research, but promotion should make incompleteness
explicit. For example, `no_topic_metadata=true` is better than silently treating
missing topics as neutral evidence.

## User And Feedback Data Needed

For each profile, the target model needs:

- explicit interest choices,
- scalar topic weights,
- confidence per topic signal,
- proficiency estimate,
- target challenge center and spread,
- known words,
- blocked/suspended words,
- review outcomes,
- inferred reading-topic summaries,
- source preferences,
- topic and difficulty decay windows.

The UI can remain simple. Internally, the system should preserve whether a
signal came from:

- explicit setup,
- profile edit,
- reading behavior,
- SRS feedback,
- import/backfill,
- system default.

Explicit signals can start high-confidence. Inferred signals should start lower
and change gradually.

## How To Get The Data

### 1. General Candidate Frontier

Preferred sources:

- use SPALEX as the leading open candidate-frontier source when paired with the
  current `freq-es-cde` seed/baseline;
- recover or rebuild the referenced Spanish 20k source if license/provenance is
  acceptable;
- evaluate a license-cleared general frequency source;
- use temporary `wordfreq`-derived candidates only for research until
  attribution/sharealike obligations are fully documented;
- merge dictionary-derived lemma candidates only when rank/frequency backfill is
  available.

Output:

- `freq-es-spalex-expanded-v1.sqlite` or equivalent research pack,
- source manifest,
- overlap report against `freq-es-cde`,
- duplicate and normalization report.

Current practical source-stack finding:

- SPALEX is strong enough to lead the 10k expansion frontier, but it is not a
  standalone replacement for `freq-es-cde`: `278` current CDE lemmas are absent
  from SPALEX.
- The first practical stack should keep `freq-es-cde` as the seed/baseline, then
  add SPALEX-ranked rows with field-level provenance.
- Installed Kaikki covers `9,469 / 10,000` combined candidates as Spanish
  headwords and gives CDE plus Kaikki mapped POS for `9,435 / 10,000`.
- Explicit Kaikki topic coverage remains partial at `1,353 / 10,000`, so topic
  overlays and/or embedding-assisted tagging are still required before
  interest-tailored admission quality claims.

Current provisional pack result:

- `scripts/data/build_spalex_frequency_pack_en_es.py` builds a reversible
  `freq-es-spalex-expanded-v1` research pack from the current CDE seed, SPALEX
  additions, and installed Kaikki enrichment.
- The generated pack has `45,131` rows and `45,131` distinct lemmas.
- Source-readiness audit status is `ok`: it reaches 2k, 5k, and 10k, resolves
  rank through `id`, resolves runtime commonness through `pmw`, has `75.3%` POS
  row coverage, and has `9.1%` topic row coverage.
- Pack lifecycle audit status is `review` only because license review remains
  required; manifest, artifact, and provenance sidecars are present and valid.
- The SRS Zipf bridge accepts the pack and reports `45,131` full SRS-admissible
  targets with no issues in the diagnostic bridge run.
- The 10k full-rulegen bridge run produced `4,260` source-target families from
  `10,000` SRS target lemmas. The active-only planner reports `49 / 4,260`
  currently covered semantic-veto families, `4,211` uncovered families, and
  `3,690` unreviewed source-target rows. This shows the candidate is large
  enough for SRS expansion, while semantic-veto evidence expansion remains a
  separate tranche-review problem.

### 2. POS And Function-Word Controls

Preferred sources:

- current frequency POS where present,
- Wiktionary/Kaikki Spanish-headword POS backfill,
- installed dictionary resources,
- Spanish stopword/function-word lists after license review,
- conservative ambiguous-POS policy.

Output:

- POS coverage audit,
- ambiguous POS report,
- function-word exclusion/defaulting policy,
- per-row POS provenance.

### 3. Topic/Domain Tags

Preferred source order:

1. dictionary or sense-level topic labels when available;
2. curated domain lexicons for high-value categories;
3. source-page or corpus domain labels when available;
4. embedding-assisted inference over glosses/examples;
5. manual review for high-impact or high-ambiguity tags.

Do not rely on a single binary tag such as `medicine=true`. Store scalar
memberships:

```json
{
  "topics": {
    "health": 0.92,
    "medicine": 0.74,
    "dentistry": 0.30
  },
  "topic_confidence": 0.86,
  "topic_source": "wiktionary_topics_plus_embedding_inference_v1"
}
```

Initial taxonomy should be small and useful:

- health,
- medicine,
- travel,
- finance,
- games,
- daily_life,
- academic,
- technology,
- animals,
- media.

The taxonomy should support aliases and parent relationships. For example:

- `medical`, `medicine`, `clinical` -> `medicine`,
- `healthcare`, `health` -> `health`,
- `dentist`, `dentistry`, `dental` -> `dentistry`, parent `medicine`.

Output:

- topic taxonomy file,
- alias/parent map,
- topic overlay table,
- topic confidence report,
- holdout validation set.

### 4. Embedding-Assisted Tagging

Use embeddings as an assistive tagger, not the sole source of truth.

Embeddings are useful for:

- suggesting topic memberships for unlabeled lemmas,
- ranking candidate domain labels from gloss/example text,
- detecting likely aliases between topic labels,
- finding domain-near words missed by curated lexicons.

Embeddings are risky for:

- bare one-word lemmas with no gloss,
- polysemous words such as `operacion`, `consulta`, `virus`, or `presion`,
- high-stakes domain claims with no supporting source,
- categories whose meaning depends heavily on context.

Recommended inference input:

```text
lemma + POS + dictionary glosses + example sentences + source sense topics
```

Avoid relying on:

```text
lemma only
```

Recommended embedding workflow:

1. Define topic prototypes from curated labels and short descriptions.
2. Embed candidate gloss/example bundles.
3. Compute similarity to topic prototypes.
4. Convert similarities to scalar memberships.
5. Apply confidence thresholds.
6. Require agreement with dictionary/lexicon evidence for high-confidence tags
   when possible.
7. Store low-confidence tags as provisional, not promotion-grade evidence.

Output should preserve provenance:

```json
{
  "topic_source": "embedding_topic_inference_v1",
  "input_fields": ["lemma", "pos", "glosses", "examples"],
  "model": "recorded-model-id",
  "topic_scores": {"medicine": 0.71, "health": 0.64},
  "confidence": 0.58,
  "promotion_state": "provisional"
}
```

### 5. Difficulty And Non-Beginner Readiness

Preferred sources:

- frequency/rank proxy,
- CEFR or learner-level lists after license review,
- user self-report,
- placement/known-word checks,
- SRS review history,
- domain rarity or specialistness overlays.

Output:

- normalized `difficulty_estimate`,
- source provenance,
- beginner/intermediate/advanced test cohorts,
- admission probe proving advanced profiles are not forced through only basic
  vocabulary.

### 6. Rulegen And Semantic Compatibility

For every candidate frontier:

- run rulegen coverage against installed dictionary packs,
- record whether the lemma can produce usable replacement rules,
- separate SRS-only usefulness from browser-replacement usefulness,
- run semantic-veto denominator audits only after the candidate frontier is
  source-ready.

Output:

- per-candidate `rulegen_coverage`,
- expanded rulegen denominator,
- semantic-veto covered/uncovered family report,
- reason codes for unsupported rows.

### 7. Feedback-Based Improvement Cycle

Feedback should improve the profile gradually.

Signals:

- review outcomes update difficulty/proficiency fit,
- suspensions reduce future admission pressure for similar candidates,
- repeated reading-topic exposure nudges topic weights,
- ignored topics decay,
- successful reviews can increase readiness for harder words nearby,
- repeated failures can reduce challenge target or narrow difficulty spread.

Use smoothing, not hard jumps:

```text
new_weight = (1 - alpha) * old_weight + alpha * observed_signal
```

Confidence should accumulate separately:

```text
new_confidence = min(max_confidence, old_confidence + evidence_gain)
```

Decay should reduce stale inferred interests without touching explicit choices
unless the user changes them:

```text
inferred_weight = inferred_weight * exp(-days_since_signal / half_life)
```

The feedback loop is product-critical, but it should not be required before the
first data acquisition milestone. First prove the static data can support
interest-tailored admission; then let feedback make it smoother.

## Acquisition Sequence

1. Freeze current `freq-es-cde` as baseline.
2. Choose or recover a license-clear expanded Spanish candidate source.
3. Build a provisional expanded SQLite with rank/frequency and provenance.
4. Add POS backfill and Spanish stopword/function-word policy.
5. Create a small topic taxonomy and health/medicine overlay first.
6. Add embedding-assisted topic inference only after dictionary/gloss inputs are
   available.
7. Add difficulty proxy and any available learner-level overlay.
8. Run rulegen coverage over the expanded candidate frontier.
9. Run neutral vs medicine-weighted admission probes.
10. Run metadata-free-source probes to confirm missing topics stay neutral.
11. Document source/license/promote-or-hold decisions.
12. Only then consider default product wiring.

## First Concrete Data Milestone

The first milestone should produce an auditable `en-es` research dataset with:

- at least 5k distinct Spanish candidate lemmas,
- rank/frequency for every row,
- POS or conservative POS fallback for every admitted row,
- health/medicine topic tags for a meaningful subset,
- topic confidence and provenance,
- Spanish stopword/function-word filtering,
- rulegen coverage flags,
- neutral and medicine-weighted admission comparison artifacts.

This milestone is enough to prove whether the product idea works before trying
to solve every language pair and every domain.
