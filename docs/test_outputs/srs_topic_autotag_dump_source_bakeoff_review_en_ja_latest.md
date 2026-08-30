# en-ja SRS Topic Dump Source Bakeoff Review

- Evidence artifact: `docs/test_outputs/srs_topic_autotag_dump_source_bakeoff_en_ja_latest.json`
- Scope: all `73,752` corrected en-ja SRS candidates
- Sources tested: `jawikipedia_dump_category`, `kaikki_wiktionary_topic`
- Posture: source-quality bakeoff only; no runtime topic admission is changed.

## Coverage After Precision Guards

| Source | Evidence rows | Unique lemma-reading pairs | Full-corpus coverage | Topics | Unique pairs beyond existing non-WordNet sources |
| --- | ---: | ---: | ---: | ---: | ---: |
| `jawikipedia_dump_category` | 6,289 | 5,736 | 7.78% | 8 | 3,695 |
| `kaikki_wiktionary_topic` | 10,319 | 4,505 | 6.11% | 13 | 2,591 |
| Combined dump sources | 16,608 | 9,597 | 13.01% | 13 | 6,033 |

Existing local non-WordNet sources covered `11,343` unique lemma-reading pairs.
Adding the guarded dump sources raises combined local non-WordNet coverage to
`17,376 / 73,752`, or `23.56%`.

The current run includes reading-identity gates plus source-quality guards.

Reading gate counts:

- `jawikipedia_dump_category`: `accepted_kana_exact_surface=11,928`,
  `accepted_unique_surface_reading=22,134`,
  `rejected_ambiguous_surface_only=2,178`.
- `kaikki_wiktionary_topic`: `accepted_exact_source_reading=45,068`,
  `accepted_unique_surface_reading=4,100`,
  `rejected_ambiguous_surface_only=1,379`,
  `rejected_conflicting_source_reading=8,731`.

Quality guard rejections:

- `jawikipedia_dump_category:low_score_uncorroborated_category=197`
- `kaikki_wiktionary_topic:low_score_nonprimary_sense=349`
- `kaikki_wiktionary_topic:weak_broad_label_without_topic_anchor=146`
- `kaikki_wiktionary_topic:generic_nonprimary_sense=68`
- `kaikki_wiktionary_topic:generic_broad_single_source_sense=17`
- `kaikki_wiktionary_topic:low_score_name_entry=15`
- `kaikki_wiktionary_topic:generic_short_for_or_redirect_sense=8`

## What Improved

The guard pass removed the most dangerous beginner-range failures:

- Same-surface multi-reading evidence is rejected unless the source proves the
  reading or the corrected candidate universe has only one reading.
- Kaikki/Wiktionary late, narrow senses no longer tag common low-score words
  unless the lemma itself is a literal topic word.
- Kaikki broad labels such as `business`, `sciences`, `engineering`, `media`,
  and `religion` now need a gloss/category anchor for low-score rows.
- Wikipedia low-score category evidence now needs topic corroboration from the
  lemma/title, with stricter handling for single-character labels such as `茶`.

Examples fixed in the smoke/sample pass:

- `水 -> sumo`, `山 -> mahjong`, `戦争 -> card games`
- `場所 -> sumo`, `フォーク -> baseball ellipsis`, `パン -> Pan/mythology`
- `大勢 -> sports`, `例えば -> anime/plants`, `茶色 -> food`
- `ポケット -> business`, `身体 -> sciences`, `布団 -> religion`

## Source Read

### Japanese Wikipedia Categories

This source is useful but not product-ready as a direct topic table.

Good patterns:

- Beginner and concrete lexical topic rows now look much cleaner:
  `食べる`, `飲む`, `料理`, `野菜`, `風邪`, `薬`, `花`, `駅`, `旅行`,
  `ホテル`, `スポーツ`, `テニス`, `漫画`.
- It still contributes broad coverage in sparse bands, especially foods,
  plants/nature, animals, medicine, sports, travel, and pop culture.

Remaining failure patterns:

- Above the low-score guard, category evidence still contains work-title,
  person, broad-concept, and adjacent-category rows. Examples from the full
  sample include anime/media-title leakage and broad animal/biology category
  leakage.
- A page title can match a vocabulary item while representing a song, manga,
  person, sports player, or named work rather than the lexical item.
- Category keywords can be contextually related but not useful for learner topic
  preference. This is most visible for broad labels such as `動物`, `漫画`,
  `アニメ`, and `スポーツ`.

Recommendation:

- Keep as review/candidate-generation evidence.
- Do not promote all Wikipedia rows directly.
- Next product-grade filter should create a stricter `promotion_ready` stratum:
  likely title/literal/corroborated rows only, plus hand-reviewed category
  whitelists/blacklists for person pages, work titles, and broad academic
  categories.

### Kaikki / Wiktionary Japanese

This source is now closer to usable, but still sense-specific.

Good patterns:

- Explicit sense topics are much better than English WordNet gloss bridging.
- Entry readings from `forms`/`ruby`/`sounds` materially reduce wrong-reading
  rows.
- The new sense guards remove the worst low-score narrow-sense pollution while
  preserving literal topic words such as `漫画`, `旅行`, `法律`, `科学`, and
  anchored rows such as `売り場` and `エンジニア`.

Remaining failure patterns:

- Some same-surface katakana items are genuinely multi-sense, e.g. `バス` can
  be transport or music/bass. The source can prove the surface/reading, but not
  which product sense the SRS card will emphasize.
- Some direct narrow-topic labels are defensible but may still be too broad for
  personalization, e.g. `少女 -> anime/comics`, `駄目 -> Go`, or `ベース ->
  games`.
- Duplicate capitalization/source-label variants still inflate evidence rows;
  the final product overlay should dedupe to item-topic pairs.

Recommendation:

- Keep as the stronger of the two new dump sources.
- Promote only item-topic pairs that survive a final item-topic dedupe and
  sample review by topic family.

## Current Conclusion

The cleanup was meaningful, but the combined dump artifact is still not an
automatic product topic table.

The current best interpretation is:

```text
dump evidence -> guarded review candidates -> stricter promotion_ready overlay
```

This is enough to continue toward topic coverage expansion, but the next step
should be a promotion-layer review rather than more raw source downloading.
The likely product path is to keep high-precision local sources, guarded Kaikki
rows, and only a strict subset of Wikipedia rows, then sample the resulting
admission output under user preference profiles.
