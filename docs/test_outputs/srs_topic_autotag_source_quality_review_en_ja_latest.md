# en-ja SRS Topic Autotag Source Quality Review

- Evidence artifact: `docs/test_outputs/srs_topic_autotag_evidence_en_ja_latest.json`
- Scope: all `73,752` corrected en-ja SRS candidates
- Candidate score range in this artifact: `0.000225` to `1.0`
- Purpose: judge whether each source is real topic evidence, weak review evidence, or noisy/fake topic data before using it for SRS preference admission.
- Identity note: this review uses the fixed JMDict matcher where kana-only
  entries preserve raw hiragana/katakana surface script and only normalize the
  reading slot. This prevents same-reading cross-script leaks such as
  `ちゃんと` inheriting `チャント` evidence or `デモ` inheriting `でも` evidence.

## Coverage Summary

| Source | Evidence rows | Unique lemma-reading pairs | Top-10k coverage | Topics | Quality read |
| --- | ---: | ---: | ---: | ---: | --- |
| `jmdict_field_direct` | 6,652 | 6,145 | 8.33% | 13 | Best precision. Real JMDict field labels, but often attached to a specialized secondary sense of an otherwise common word. |
| `jmdict_gloss_keyword` | 5,235 | 4,594 | 6.23% | 8 | Useful weak candidate source. Gloss keywords find real topic words but also many generic verbs and broad senses. |
| `jmdict_misc_review` | 1,667 | 1,646 | 2.23% | 3 | Real register evidence, not real topical preference evidence. Useful as `casual/slang` or `formal/literary`, not as a normal topic. |
| `english_wordnet_gloss_bridge` | 51,444 | 24,010 | 32.56% | 5 | High coverage but too noisy for direct topic tags. Many false positives from English polysemy. |
| All local sources | 64,998 | 30,843 | 41.82% | 16 | Coverage is dominated by the noisy WordNet bridge; high-confidence local topic coverage is much smaller. |

Unique pair coverage by current corrected score band:

| Source | 0.00-0.10 | 0.10-0.20 | 0.20-0.30 | 0.30-0.40 | 0.40-0.50 | 0.50-0.60 | 0.60-0.70 | 0.70-0.80 | 0.80-0.90 | 0.90-1.00 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All local sources | 236 | 797 | 1,586 | 2,899 | 4,273 | 4,471 | 3,480 | 4,335 | 5,118 | 3,648 |
| `jmdict_field_direct` | 23 | 114 | 218 | 484 | 741 | 786 | 725 | 788 | 792 | 1,474 |
| `jmdict_gloss_keyword` | 52 | 122 | 163 | 313 | 489 | 663 | 624 | 712 | 936 | 520 |
| `jmdict_misc_review` | 31 | 36 | 57 | 98 | 150 | 205 | 289 | 256 | 326 | 198 |
| `english_wordnet_gloss_bridge` | 202 | 733 | 1,499 | 2,654 | 3,699 | 3,606 | 2,474 | 3,187 | 3,675 | 2,281 |

## Source Samples And Assessment

### `jmdict_field_direct`

Representative good evidence:

| Topic | Sample rows | Read |
| --- | --- | --- |
| `science_math` / `computing_internet` | `ベクトル/べくとる`, `ダウンロード/だうんろーど`, `ゲート/げーと`, `培養/ばいよう` | Usually real topic evidence, now split between science/math and computing/internet. |
| `food_cooking` | `饂飩/うどん`, `クレープ/くれーぷ`, `チーズ/ちーず` | Strong evidence when the field is food/cooking and the gloss is actually the food item. |
| `games` | `フラッシュ/ふらっしゅ`, `ネーム/ねーむ`, `切り/きり` in go | Strong for game-specific senses; weaker for common verbs with a game sense. |
| `music_media_entertainment` | `オペラ/おぺら`, `バス/ばす`, `ベース/べーす` | Real, but some are specific musical senses rather than general entertainment vocabulary. |
| `medicine_health` | `感染/かんせん`, `ショック/しょっく`, `カテーテル/かてーてる` | Mostly good topic evidence. |

Important caveat examples:

| Topic | Sample rows | Concern |
| --- | --- | --- |
| `shopping_money` / `work_office` | `上げる/あげる`, `子/こ`, `鏡/かがみ`, `髭/ひげ` | The topic is real for a specialized sense, but the learner item is too broad or too ordinary to promote as finance/business vocabulary without sense gating. |
| `science_math` / `computing_internet` | `仕事/しごと` as physics “work”, `開く/ひらく` as computing/mathematics, `牛/うし` as astronomy mansion | Real JMDict fields, but not good standalone topic-admission evidence for the base word. |
| `food_cooking` | `どう/どう` as dough, `開く/ひらく` as cutting open fish, `白/しろ` as grilled intestine | Real fields but high risk of wrong learner expectation. |
| `sports_fitness` | `水/みず`, `本/ほん`, `開く/ひらく` | Real sports senses, but common base words should not be strongly topic-stretched. |

Assessment: this is the best source, but should be used as strong evidence only when the entry looks domain-specific enough. Common short words, broad verbs, counters, and everyday nouns need a secondary-sense guard.

### `jmdict_gloss_keyword`

Representative good evidence:

| Topic | Sample rows | Read |
| --- | --- | --- |
| `animals` | `魚/さかな` | Good when the gloss itself is the actual topic noun. |
| `anime_manga_pop_culture` | `漫画/まんが`, `アニメ/あにめ`, `アイドル/あいどる`, `コスプレ/こすぷれ` | Small but useful. |
| `food_cooking` | `飯/めし`, `チーズ/ちーず`, `ストレート/すとれーと` for liquor/tea/coffee | Mixed but often meaningful. |
| `medicine_health` | `診療/しんりょう`, `病院/びょういん` | Good for medical nouns; weaker for generic verbs. |
| `sports_fitness` | `スポーツ/すぽーつ`, `コート/こーと`, `ハンド/はんど` | Often good for concrete terms. |

Weak/noisy examples:

| Topic | Sample rows | Concern |
| --- | --- | --- |
| `food_cooking` | `作る/つくる`, `入る/はいる`, `出す/だす`, `探す/さがす` | Gloss mentions food-related action, but the lemma is a generic verb. |
| `travel_places_transport` | `行く/いく`, `作る/つくる`, `切る/きる`, `練る/ねる` | Mostly generic verbs or unrelated senses. |
| `animals` | `使う/つかう`, `取る/とる`, `開く/ひらく`, `声/こえ` | Topic appears in an example-like or secondary gloss, not a good learner-topic tag. |
| `plants_nature` | `開く/ひらく` from “root”, `立つ/たつ` with “tree/building” | Keyword matching can confuse mathematical/root or example context with nature. |

Assessment: useful as a review/candidate source and possibly weak support when combined with another source. It should not independently create strong topic-stretch eligibility for common verbs or broad words.

### `jmdict_misc_review`

Representative evidence:

| Topic/register | Sample rows | Read |
| --- | --- | --- |
| `casual_slang_register` | `米/こめ` online comment, `草/くさ` LOL, `ピザ/ぴざ` derogatory slang, `信者/しんじゃ` fanboy | Real register evidence. |
| `casual_slang_register` | `出来上がる/できあがる` drunk, `彼処/あそこ` euphemistic genitals, `僕/ぼく` colloquial “you” | Real but sense-specific. |
| `formal_professional_register` | `昨年/さくねん`, `値/あたい`, `怒る/いかる`, `こそ/こそ` | Real misc labels, but “formal/literary” should probably affect register/admission posture rather than topical preference. |

Assessment: not garbage, but it is not a topical source. Keep as a separate register dimension, not as normal topic coverage.

### `english_wordnet_gloss_bridge`

Representative false positives:

| Topic | Sample rows | Why it is not safe |
| --- | --- | --- |
| `animals` | `人/ひと` from “adult/human”, `ペン` from English “pen”, `規模/きぼ` from “scale” | English WordNet synsets create irrelevant topic matches. |
| `food_cooking` | `中/なか` from “center”, `所/ところ` from “point/side”, `基/もと` from “stock/ingredient” | English gloss polysemy overwhelms Japanese topic meaning. |
| `hobbies_crafts` | `先生/せんせい` from “master”, `大統領/だいとうりょう` from “big man/boss”, `道路/どうろ` from “highway” | WordNet hobby/craft links are mostly semantic drift. |
| `sports_fitness` | `はい/はい` from “pardon”, `我慢/がまん`, `移民/いみん`, `芝居/しばい` | Sports matches often come from unrelated English words or broad synsets. |
| `plants_nature` | `前/まえ` from “head”, `目/め` from “grain/pip”, `上/うえ` from “elder” | Polysemy again, not Japanese topic evidence. |

Assessment: reject as a direct topic source for now. It can only become useful after a redesign with strong guards, e.g. exact English lemma class constraints, topic whitelist per POS, stopword/polysemy filters, and support from another Japanese-side source.

## Coverage Gaps

Current high-confidence topic coverage is thin:

- Reliable JMDict field coverage is only about `8.3%` of the full corrected candidate universe.
- Gloss keyword adds about `6.2%`, but much of it must remain weak unless the word is concrete/domain-specific.
- Register labels cover about `2.2%`, but they do not solve ordinary topic preference coverage.
- The apparent `41.8%` all-source coverage is misleading because it is dominated by the noisy WordNet bridge.

Topic gaps visible in the source summary:

- `travel_places_transport` has almost no direct field coverage (`6` direct rows); most current rows come from weak gloss keywords.
- `anime_manga_pop_culture` is tiny (`10` rows total).
- `shopping_money`, `work_office`, `law_politics_civics`, `medicine_health`, `music_media_entertainment`, and `plants_nature` are present but sparse.
- Everyday user preference categories such as school, work, household, shopping, emotion, social life, internet/software, and entertainment fandom are not covered well by the current taxonomy/source mix.

## Current Recommendation

Use the sources in tiers:

1. `jmdict_field_direct`: promote as the main local topic evidence source, but add guards for common/generic words and secondary senses.
2. `jmdict_gloss_keyword`: keep as weak evidence. Allow it to support another source, or promote only concrete nouns/gairaigo/domain-specific entries.
3. `jmdict_misc_review`: keep, but treat as register evidence rather than topic evidence.
4. `english_wordnet_gloss_bridge`: do not use for direct topic admission. Archive behind a review-only flag or disable until redesigned.

Additional coverage ideas are still needed if the product needs broad topic preference behavior. The most promising next sources are Japanese Wikipedia/Wikidata category-derived entity topics from dumps or cached slow probes, curated public wordlists by domain, and corpus/context co-occurrence from our existing sentence/example resources.
