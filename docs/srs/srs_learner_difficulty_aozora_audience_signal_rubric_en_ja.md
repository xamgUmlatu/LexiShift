# Aozora Work-Audience Signal Rubric for en-ja Difficulty

Status: research rubric for sidecar experiments
Last updated: 2026-06-24

This document records how Aozora/Yozora/Bungo/NDL work-level metadata should be
interpreted before we turn it into word-level learner-difficulty features. The
goal is to avoid collapsing noisy work metadata into one premature "work
difficulty" score.

## Research Inputs

- Aozora/Yozora NDC semantics:
  - Yozora says Aozora works are classified by 3-digit NDC, and child books use
    a leading `K`.
  - Yozora also notes classification is done after a work is published/read, so
    absence of classification is not negative evidence.
  - Source: https://yozora.main.jp/about.html
- Aozora NDC database history:
  - Aozora's own "soramoyou" notes that book cards and CSV data use values such
    as `NDC 911 914` and `NDC K913`.
  - Source: https://www.aozora.gr.jp/soramoyou/soramoyou2012.html
- NDC semantics:
  - NDC is a subject/classification system, not a learner level system.
  - Source: https://www.jla.or.jp/ndc/
- NDL Search API:
  - NDL Search exposes Search APIs via SRU/OpenSearch/OpenURL and metadata via
    OAI-PMH.
  - NDL's API specification says API metadata follows DC-NDL, and OpenSearch can
    filter NDC by prefix.
  - NDL API terms require care around application, provider permissions, credit,
    and large/continuous access.
  - Sources:
    - https://ndlsearch.ndl.go.jp/help/api
    - https://ndlsearch.ndl.go.jp/help/api/specifications
- Bungo Search for Kids:
  - The for-Kids pages explicitly list Aozora child-literature works and expose
    reading-time bucket, character count, popularity, and excerpt.
  - This is useful as third-party inclusion evidence, but not an official Aozora
    or NDL classification source.
  - Source: https://search.bungo.app/juvenile/authors/all/categories/all/books
- Aozora morphology aggregate:
  - The local `freq-ja-aozora-word` pack is a research sidecar built from
    `青空文庫形態素解析データ集`.
  - Source/license pages:
    - https://aozora-word.hahasoha.net/
    - https://aozora-word.hahasoha.net/license.html

## Local Landscape Snapshot

Snapshot source:
`$DATA_ROOT/frequency_packs/freq-ja-aozora-word/main.sqlite`.

Work profile rows:

| Metric | Value |
| --- | ---: |
| Total works | 11,176 |
| K-NDC child/youth works | 918 |

Orthography and local accessibility:

| Orthography | Works | Mean accessibility percentile |
| --- | ---: | ---: |
| 新字新仮名 | 6,705 | 0.699 |
| 新字旧仮名 | 3,167 | 0.258 |
| 旧字旧仮名 | 1,280 | 0.064 |
| 旧字新仮名 | 17 | 0.225 |
| その他 | 7 | 0.043 |

K-NDC works by existing local accessibility band:

| Band | K-NDC works | Non-K works | K share |
| --- | ---: | ---: | ---: |
| accessible | 521 | 2,273 | 18.6% |
| mixed | 118 | 3,794 | 3.0% |
| hard | 156 | 2,637 | 5.6% |
| very_hard | 123 | 1,554 | 7.3% |

K-NDC split by orthography:

| Orthography | K works | Mean accessibility percentile |
| --- | ---: | ---: |
| 新字新仮名 | 535 | 0.960 |
| 新字旧仮名 | 290 | 0.338 |
| 旧字旧仮名 | 86 | 0.087 |
| 旧字新仮名 | 5 | 0.385 |
| その他 | 2 | 0.134 |

Important implication: `K` is a strong audience signal, but not a guaranteed
easy-language signal. It becomes much more useful when combined with modern
orthography and local accessibility. Old-kana K works such as old children's
texts are still useful evidence of child audience, but should not strongly lower
word difficulty by themselves.

Top K-NDC groups:

| NDC | Works | Mean accessibility percentile | Interpretation |
| --- | ---: | ---: | --- |
| `NDC K913` | 694 | 0.743 | Child/youth fiction; often useful for easier exposure when modern. |
| `NDC K911` | 126 | 0.227 | Child/youth poetry; often linguistically harder or old-form-heavy. |
| `NDC K933` | 17 | 0.975 | Translated English fiction; often modern/easy in this corpus. |
| `NDC K953` | 13 | 0.923 | Translated French fiction; often modern/easy in this corpus. |
| `NDC K943` | 11 | 0.946 | Translated German fiction; often modern/easy in this corpus. |

Local metadata keyword counts are much weaker than K-NDC because the local
tables contain title/author/NDC/orthography, not full card fields. Examples:

| Keyword | Local metadata matches | K-NDC matches |
| --- | ---: | ---: |
| `少年` | 37 | 19 |
| `少女` | 14 | 2 |
| `童話` | 8 | 2 |
| `子供` | 27 | 7 |
| `こども` | 33 | 9 |
| `赤い鳥` | 1 | 1 |

This means keyword evidence must be field-aware. `少年` in a title is not the
same as `少年` in an NDL subject, publication series, publisher, or Aozora work
field.

## Source Confidence Rubric

Do not use a single flat keyword rule. Use source, match quality, and field.

| Evidence | Direction | Suggested confidence | Notes |
| --- | --- | ---: | --- |
| Aozora/Yozora exact K-NDC on same Aozora work | child/youth audience | high | Strongest compact audience signal. Does not alone mean easy vocabulary. |
| Yozora page links exact Aozora card | child/youth audience | high | Independent confirmation of the K-NDC classification page. |
| Bungo for Kids listing exact match | child/youth audience | high | Inclusion evidence from a child-literature index. |
| NDL exact/card-linked record with K-NDC or juvenile/school subject | child/youth audience | medium-high | Useful when exact/card-linked; weaker if broad title only. |
| Aozora card work fields contain `童話`, `児童`, `赤い鳥`, etc. | child/youth or publication context | medium | Ignore author biography/person fields for work audience. |
| NDL publisher/series/title contains `少年`, `少女`, `児童`, `教科書`, etc. | youth/school context | medium | Requires relevant work match. |
| Wikipedia/Wikidata category/description hints | topical/audience hint | low | Useful only as weak supporting evidence. |
| Bungo direct detail page without listing match | length/popularity only | low for audience | Detail pages give read-time/PV/length, not proof of child audience. |
| Title-only keyword hit | weak lexical context | very low | Often describes subject matter, not audience. |

Use noisy-or composition rather than summing raw counts:

```text
combined_confidence = 1 - product(1 - source_confidence_i)
```

This lets multiple independent weak sources accumulate without letting duplicate
records from one provider dominate.

## Work Axes

The next code layer should compute reusable axes, not final difficulty.

### `work_child_or_school_audience`

What it means: evidence that the work was written for, classified as, or indexed
with child/school/youth context.

Inputs:

- K-NDC from Aozora/Yozora.
- Bungo for Kids listing exact match.
- NDL exact/card-linked K-NDC, juvenile subject, school subject, publisher, or
  series cues.
- Aozora card work-field cues.
- Low-confidence Wikipedia/Wikidata hints.

Do not let this directly imply an easy word score.

### `work_accessible_language`

What it means: the actual token profile of the work appears relatively easy
inside the Aozora morphology universe.

Inputs:

- Existing `work_profile.accessibility_percentile`.
- Common/mid/tail/rare unique shares.
- Modern orthography.

This is already available locally and is more directly lexical than audience
metadata.

### `work_old_or_literary_risk`

What it means: exposure from this work may reflect old orthography, old kana,
poetry, literary style, or text-form artifacts that should not lower a word too
aggressively.

Inputs:

- `旧字旧仮名`, `新字旧仮名`, `旧字新仮名`.
- Low accessibility percentile.
- K-NDC poetry patterns such as `K911`.
- High rare-unique share.

### `work_general_exposure`

What it means: the work is visible/popular in the sidecar ecosystem.

Inputs:

- Aozora work token count and dispersion.
- Bungo popularity PV.
- NDL result count only if exact/card-linked and source is trusted.

This is weaker than BCCWJ/Tubelex for general word frequency. It should mostly
serve as an upper-tail tiebreaker.

## Word-Level Aggregation Contract

For a vocabulary item, aggregate over the Aozora works where the token appears.
Use token exposure, confidence, and coverage.

```text
weighted_axis_mean(axis) =
  sum(token_count_in_work * work_axis_value * work_axis_confidence)
  / sum(token_count_in_work * work_axis_confidence)

axis_coverage =
  sum(token_count_in_work for works with usable axis evidence)
  / sum(token_count_in_work across all Aozora works)
```

Initial word features should include:

- `aozora_child_accessible_exposure`
- `aozora_child_old_or_hard_exposure`
- `aozora_modern_accessible_exposure`
- `aozora_old_literary_exposure`
- `aozora_audience_signal_coverage`
- `aozora_audience_signal_confidence`
- `aozora_bungo_child_listing_exposure`
- `aozora_ndl_child_or_school_exposure`

The scorer should later be free to sweep whether these features matter only
above a difficulty gate, only as a cap/floor, or as a small residual adjustment.
The aggregation layer should not bake in that model decision.

## Guardrails For First Implementation

1. Preserve raw provider evidence and fetch provenance.
2. Compute work axes separately from word-level aggregates.
3. Keep `audience`, `accessibility`, and `old/literary risk` as separate axes.
4. Do not treat `K-NDC` or `Bungo for Kids` as "easy" without accessibility and
   orthography context.
5. Do not let broad title-only NDL/Wikipedia matches move scores.
6. Do not count author biography/person fields as work-audience evidence.
7. Store `value`, `coverage`, `confidence`, and `evidence_json` for every
   aggregate.
8. Keep all new features sidecar-only until a review pack shows explanatory
   value on known failures and controls.

## What Comes Next

The next necessary code step is a local, repeatable aggregation pass:

```text
work_audience_feature/provider rows
  -> work_audience_axis_score
  -> token_audience_feature
  -> qualitative review pack
  -> optional scorer sweep
```

The first review pack should compare known advanced/tail failures and controls
using the new features before any model formula uses them.

## First Aggregation Implementation

Implemented:
`scripts/testing/build_aozora_lexical_context_features_ja.py`.

The first implementation prioritizes the lexical work-profile signal because it
is already available for the whole Aozora morphology pack and is more directly
connected to word difficulty than metadata tags alone.

Input:

- Required: `$DATA_ROOT/frequency_packs/freq-ja-aozora-word/main.sqlite`.
- Optional: work-audience metadata SQLite from
  `scripts/testing/fetch_aozora_work_audience_metadata_ja.py --output-sqlite`.

Output tables:

- `work_audience_axis_score`
  - Work-level axes from existing `work_profile`.
  - Includes accessibility percentile, modern orthography, old-orthography
    risk, K-NDC child/youth signal, K911 poetry risk, lexical rarity risk, and
    combined child-accessible or child-old/hard priors.
  - If an optional rich audience DB is supplied, selected works also get
    external child/school and warning/adultish axes.
- `token_audience_summary`
  - One wide row per Aozora token row for review/debugging.
  - Includes token count, work count, rank, pmw, accessibility-weighted mean,
    accessible-work exposure, hard-work exposure, modern/old orthography
    exposure, child/youth exposure, modern-child exposure, old-literary risk
    context, and confidence.
- `token_audience_feature`
  - Normalized long-form feature rows for later sweeps.

Important limitation:

- The current Aozora `main.sqlite` does not contain a per-token/per-work bridge.
  Therefore token-level features currently use the existing broad
  `token_context_profile` aggregates.
- Rich provider metadata can already be stored as work-axis evidence, but it
  cannot be precisely re-aggregated to arbitrary token features until a future
  rebuild stores token-by-work counts or another token-work bridge.

This is intentional for now: it lets us test the more promising lexical-context
signal immediately without rerunning the full morphology build, while keeping the
schema ready for richer work-axis aggregation later.
