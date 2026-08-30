# en-ja SRS Topic Autotagging Sidecar

Status: active research sidecar
Role: Topic-coverage expansion / source-comparison workflow
Last updated: 2026-07-02
Purpose: make en-ja SRS topic coverage expansion manageable by generating comparable, source-provenance topic evidence and deterministic review samples instead of hand-tagging the vocabulary universe.

## Goal

The product goal is not to make every source label a user-facing topic. The goal is
to build a reusable evidence table:

```text
word item -> source-backed topic evidence -> reviewed topic overlay candidates
```

Each evidence row preserves:

- lemma and reading,
- current corrected difficulty score and band,
- admission/correction metadata,
- proposed product topic,
- source and source label,
- membership/confidence,
- match mode and ambiguity flags,
- license/review posture.

Runtime SRS admission should only consume a reviewed/exported overlay. This
sidecar is for discovering which source rules are precise enough.

## Implemented Files

- Policy data:
  `../test_inputs/srs_topic_autotag_policy_en_ja.json`
- Evidence generator:
  `../../scripts/testing/srs_topic_autotag_evidence_en_ja.py`
- Product-safe promotion exporter:
  `../../scripts/testing/srs_topic_autotag_promotion_overlay_en_ja.py`
- Auto evidence review labels:
  `../test_inputs/srs_topic_auto_review_labels_en_ja.json`
- Full auto evidence review ledger:
  `../../scripts/testing/srs_topic_auto_review_ledger_en_ja.py`
- Product-owned manual semantic lexicon matcher:
  `../../scripts/testing/srs_topic_manual_semantic_lexicon_en_ja.py`
- Wikidata claim probe:
  `../../scripts/testing/srs_topic_autotag_wikidata_claim_probe_en_ja.py`
- Wikidata claim chunk runner:
  `../../scripts/testing/srs_topic_autotag_wikidata_claim_probe_chunks_en_ja.py`
- NDL authority probe:
  `../../scripts/testing/srs_topic_autotag_ndl_authority_probe_en_ja.py`
- Focused tests:
  `../../core/tests/dev/test_srs_topic_autotag_evidence_en_ja.py`
  and
  `../../core/tests/dev/test_srs_topic_manual_semantic_lexicon_en_ja.py`
  and
  `../../core/tests/dev/test_srs_topic_autotag_promotion_overlay_en_ja.py`
- Current local artifact:
  `../test_outputs/srs_topic_autotag_evidence_en_ja_latest.md`
  and `.json`
- Current product-safe candidate overlay:
  `../test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.md`
  and `.json`
- Topic/proficiency sampling grid:
  `../test_inputs/srs_admission_topic_proficiency_grid_configs_en_ja.json`
- Randomized UX admission sampler:
  `../../scripts/testing/srs_admission_random_ux_sample_pack_en_ja.py`
- Current auto evidence review ledger:
  `../test_outputs/srs_topic_auto_review_ledger_en_ja_latest.md`
  and `.json`
- Current manual semantic lexicon evidence:
  `../test_outputs/srs_topic_manual_semantic_lexicon_en_ja_latest.md`
  and `.json`
- Current Wikidata claim probe artifact:
  `../test_outputs/srs_topic_autotag_wikidata_claim_probe_en_ja_latest.md`
  and `.json`

## Candidate Universe

The sidecar uses the packaged corrected en-ja difficulty CSV as its default
denominator:

```text
core/lexishift_core/resources/srs/en_ja/learner_difficulty_corrected.csv
```

This is intentional. Topic evidence needs to be reviewed in the same vocabulary
space the product will use, including score, band, `candidate_state`,
`admission_override`, and correction metadata.

## Source Adapters

### Product-Owned Manual Semantic Lexicon

Uses a checked-in, product-owned seed lexicon for obvious closed-set topics and
internal facets:

```text
docs/test_inputs/srs_topic_manual_semantic_lexicon_en_ja.json
```

This source is intentionally not a scraper and not an ontology. It is the
controlled fallback for high-confidence lists such as common foods, animals,
plants, sports, games, music/instruments, vehicles/transport, common regions,
body/health, science/math, civics, media forms, arts/literature forms, weather,
places/facilities, shopping/money, work/office, computing/internet,
cooking/dining, daily routines, emotions/social description, communication,
colors, calendar/time, family/people, school/classroom, household objects, and
basic measurements.

Important guard:

```text
entry with reading -> exact normalized reading required
entry without reading -> accepted only when the corrected ranking has one row for that lemma
unmatched or ambiguous entry -> artifact is review, not ok
```

The current artifact is clean:

- 30 collections
- 1,033 declared entries
- 1,033 matched entries
- 0 unmatched entries
- 845 product topic evidence rows
- 1,033 internal facet rows

Only collections with `promotion_eligible: true` and a `target_family` are
consumed by the product-safe promotion exporter. Facet-only collections remain
sidecar metadata and do not become user-facing topic rows.

Current promotion impact:

- `product_owned_manual_semantic_lexicon`: 839 overlay rows after dedupe against
  other promoted sources
- 770 runtime-effective rows under the current lemma-only runtime overlay
- 69 review-only rows, mostly because the lemma has multiple corrected readings
  and therefore needs a reading-specific runtime overlay contract before safe
  admission

Current granular facet additions beyond the first seed pass:

- `place_facility`
- `shopping_money`
- `work_office`
- `computing_internet`
- `cooking_dining`
- `daily_life_routines`
- `emotion_social`
- `communication_language`

The daily-life, emotion/social, and communication/language collections are
facet-only for now because they are high-value UX groupings but cut across the
current coarse topic families. Shopping/work and computing/science are promoted
as split child topics:

- `shopping_money` and `work_office` under the compatibility parent
  `finance_business`
- `computing_internet` and `science_math` under the compatibility parent
  `science_technology`

Places/facilities still promote under `travel_places_transport`, and
cooking/dining still promotes under `food_cooking`.

This is the safest current source for broad “big hitter” topic coverage because
the entries are curated directly against the corrected SRS candidate universe
and do not inherit web category/polysemy noise.

### JMDict Field Direct

Uses JMDict `<field>` labels mapped through the en-ja product taxonomy. This is
the strongest current local source.

Important guard:

```text
JMDict match = exact written surface + normalized reading
```

Kana-only JMDict entries match kana-only candidates by exact raw kana surface
plus normalized reading. The sidecar intentionally keeps hiragana and katakana
surfaces separate, so `ちゃんと` does not inherit evidence from `チャント`, and
`デモ` does not inherit evidence from `でも`.

### JMDict Misc Review

Uses review-only JMDict `<misc>` labels such as slang, Internet slang, and manga
slang. This is not a topic-default source; it is useful for register/pop-culture
candidate discovery.

### JMDict Gloss Keyword

Uses policy-owned English keyword rules over short JMDict glosses. This can find
food, animals, plants, games, medicine, sports, and travel candidates beyond
explicit fields, but it is candidate-generation only until sampled.

### English WordNet Gloss Bridge

Uses installed English WordNet lexname files and JMDict English gloss
intersections. This is useful as a comparison/control source, but the first run
showed it is too polysemy-heavy for direct promotion. Examples like `game`,
`set`, `head`, `stock`, `scale`, and `adult` create many false topical links.

Treat this source as:

```text
possible mining source -> heavy guards/review required
```

not as product-ready topic coverage.

### Japanese Wikipedia Dump Categories

Uses downloaded Japanese Wikipedia SQL metadata dumps:

- `page`
- `redirect`
- `categorylinks`
- `linktarget`

The adapter resolves exact candidate lemma titles, follows redirects, maps page
IDs to category titles, then applies the Japanese topic keyword policy. This is
repeatable and full-corpus friendly, but it is still review evidence: a
Wikipedia title does not prove the exact SRS reading, and page/category evidence
can point to media works, people, ambiguous terms, or adjacent concepts.

The adapter now applies a reading-identity gate before creating rows:

```text
surface-only Wikipedia evidence + multiple candidate readings -> reject
surface-only Wikipedia evidence + one candidate reading -> keep as weakly verified
kana-exact surface -> keep
```

This mitigates same-kanji/wrong-reading rows, but it does not solve page-sense
or adjacent-category contamination.

The current evidence generator also applies a conservative quality guard to
low-score Wikipedia rows:

```text
low-score Wikipedia category evidence -> require lemma/title corroboration
single-character topic labels -> require exact or explicit literal support
```

This blocks beginner-range false positives such as common words that are also
song/person/work titles, while keeping direct rows such as `食べる -> food`,
`旅行 -> travel`, and `漫画 -> manga`. Full-corpus samples still show
above-beginner work-title and broad-category leakage, so Wikipedia dump rows
remain review evidence rather than product-ready tags.

Important guard:

```text
Wikipedia title/category match = candidate-generation evidence, not product truth
```

Before repeated iteration, build a compact cache of page title -> resolved title
-> categories. Raw gzip SQL scans take several minutes.

### Kaikki / Wiktionary Topic Metadata

Uses downloaded Kaikki Japanese Wiktionary JSONL data. The adapter matches exact
candidate lemma surfaces and maps explicit sense `topics`/topic-like categories
through `kaikki_topic_mappings` in the policy file.

Before creating a row, the adapter extracts entry readings from `forms`/`ruby`
and `sounds`. When those readings exist, only the matching SRS reading is kept.
If no source reading is available, the row is kept only for kana-exact or
single-reading candidate surfaces.

This is materially better than WordNet gloss bridging because topic labels come
from lexical sense metadata. It is still sense-specific and can tag common base
words with narrow senses, so it remains candidate-generation evidence until
sampled and guarded.

The current evidence generator applies source-quality guards for common
low-score rows:

```text
late/narrow Kaikki sense on low-score word -> reject unless lemma is a literal topic word
low-score broad labels such as sciences/business/religion -> require a topic anchor
low-score name entries -> reject unless the lemma itself is a literal topic word
```

This removes failures such as `水 -> sumo`, `場所 -> sumo`, `戦争 -> card
games`, `ポケット -> business`, and `布団 -> religion`. It does not solve
same-surface multi-sense katakana items such as `バス`, where transport and
music senses have the same surface/reading.

### Online Adapters

The sidecar has opt-in online adapters for:

- Wikidata,
- Web NDL Authorities,
- Japanese Wikipedia categories.

These are build-time probes only. They are not runtime dependencies. NDL is
currently deferred from the product-safe export path until its metadata and
review policy are tighter.

The first small online smoke found current public endpoint friction:

- Wikidata SPARQL returned HTTP 429 rate limiting.
- Wikidata API fallback also hit HTTP 429 during the smoke.
- Web NDL Authorities exact-label SPARQL works, but only with the simple
  per-label query shape, not the batched `VALUES` shape.
- Japanese Wikipedia API can also rate-limit small bursts.

For serious use, prefer slower bounded probes, local cache files, or downloaded
dumps/exports where license posture allows it.

### NDL Authority Probe

The NDL authority probe is separate from the older generic `ndl_online` adapter.
It uses this safer shape:

```text
candidate lemma -> exact Web NDL Authorities label -> SKOS scheme/broader/related metadata
```

The probe caches exact-label results and writes resumable chunk artifacts. By
default, topic evidence is emitted only from `ndlsh` rows whose scheme is
`topicalTerms`. This is important because the same label can also appear as an
NDL name-authority row; for example, `桜` has a topical subject-heading row and
name-authority rows. Name-authority rows are kept out of topic evidence unless
`--include-non-topical-authorities` is explicitly set for research.

The current first smoke over known labels generated 4 topic rows:

- `野球 -> sports_fitness`
- `医学 -> medicine_health`
- `漫画 -> anime_manga_pop_culture`
- `将棋 -> games`

The smoke also caught a useful failure mode: related labels can contaminate
topic keyword matching. `漫画喫茶` contains `茶`, but that should not make
`漫画` a food/cooking word. The probe therefore uses exact labels, alternate
labels, and broader labels for keyword triggers; related labels are retained
only as review context.

Treat NDL as evidence-only for now. It is not consumed by the product-safe
promotion exporter.

### Wikidata Claim Probe

The Wikidata claim probe is separate from the older `wikidata_online` adapter.
The old adapter tried SPARQL first and fell back to description keywords. The
claim probe instead uses this shape:

```text
candidate lemma -> Japanese Wikipedia pageprops QID -> Wikidata EntityData claims -> nearest configured topic root
```

This matters because it tests structured ontology evidence rather than text
keyword evidence. The probe caches both page title -> QID and QID -> simplified
claims.

Current observations:

- The known-topic smoke mapped `寿司`, `野球`, `癌`, `桜`, `漫画`, and `将棋`
  correctly after adding narrower roots and preferring nearest matched roots.
- The first broader 80-label uncovered sample found 32 exact entities but only
  2 topic rows. After adding roots supported by inspected misses and explicitly
  rejecting Wikidata disambiguation pages, the same 80-label sample produced 8
  topic rows.
- The 8-row refined sample was all new relative to the current product-safe
  overlay: `アフタヌーン`, `詩`, `スケッチ`, `練り切り`, `犯人`, `台風`,
  `くり`, and `エミュレート`.
- A 250-label live sample is possible but still too slow/rate-sensitive for
  routine iteration through the public endpoints. Larger runs should use a local
  Wikidata dump/cache or a stricter ancestry frontier strategy.
- Many unmapped exact entities are not useful topic rows, including generic
  concepts and disambiguation pages.
- Some misses are promising root-expansion candidates, such as literature,
  weather/nature, sweets/food, software/technology, birds/animals, ships or
  transport, and document/legal-administrative classes.

The broad/live Wikidata probe remains evidence-only, but the product-safe
promotion exporter now consumes strict claim-probe rows from the current refined
artifact. A row is promotable only when it has an exact Japanese Wikipedia
pageprops QID, a structured Wikidata claim path from item to configured topic
root, source/unique reading identity, minimum confidence, and no disambiguation
signal. Generic Wikidata search rows are not auto-promoted.

The next Wikidata pass should focus on either a local/cache-backed larger run or
a manually reviewed promotion-candidate packet from the current refined rows.

## Commands

Local-only source comparison:

```bash
python3 scripts/testing/srs_topic_autotag_evidence_en_ja.py \
  --top-n 73752 \
  --sample-per-cell 4 \
  --max-sample-rows 240 \
  --max-sample-rows-per-source 80
```

Offline dump-source bakeoff:

```bash
python3 scripts/testing/srs_topic_autotag_evidence_en_ja.py \
  --top-n 73752 \
  --source jawikipedia_dump_category \
  --source kaikki_wiktionary_topic \
  --sample-per-cell 4 \
  --max-sample-rows 320 \
  --max-sample-rows-per-source 160 \
  --json-out docs/test_outputs/srs_topic_autotag_dump_source_bakeoff_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_dump_source_bakeoff_en_ja_latest.md
```

Small online smoke:

```bash
python3 scripts/testing/srs_topic_autotag_evidence_en_ja.py \
  --top-n 1000 \
  --source wikidata_online \
  --source ndl_online \
  --source jawikipedia_category_online \
  --enable-network \
  --online-limit 40 \
  --online-chunk-size 10 \
  --sleep-seconds 0.05 \
  --sample-per-cell 2 \
  --max-sample-rows 80 \
  --json-out docs/test_outputs/srs_topic_autotag_evidence_en_ja_online_probe_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_evidence_en_ja_online_probe_latest.md
```

Focused tests:

```bash
python3 -m unittest core.tests.dev.test_srs_topic_autotag_evidence_en_ja
python3 -m unittest core.tests.dev.test_srs_topic_autotag_promotion_overlay_en_ja
```

Product-safe promotion overlay:

```bash
python3 scripts/testing/srs_topic_autotag_promotion_overlay_en_ja.py \
  --overlay-json-out docs/test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.json \
  --json-out docs/test_outputs/srs_topic_autotag_promotion_overlay_report_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.md
```

Wikidata claim probe:

```bash
python3 scripts/testing/srs_topic_autotag_wikidata_claim_probe_en_ja.py \
  --max-labels 80 \
  --max-entity-requests 1600 \
  --sleep-seconds 0.25 \
  --json-out docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_en_ja_latest.md
```

Known-topic Wikidata smoke:

```bash
python3 scripts/testing/srs_topic_autotag_wikidata_claim_probe_en_ja.py \
  --max-labels 6 \
  --lemma 寿司 \
  --lemma 野球 \
  --lemma 癌 \
  --lemma 桜 \
  --lemma 漫画 \
  --lemma 将棋 \
  --max-entity-requests 350 \
  --json-out docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_known_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_known_en_ja_latest.md
```

Resumable full Wikidata claim pass:

```bash
python3 scripts/testing/srs_topic_autotag_wikidata_claim_probe_chunks_en_ja.py \
  --chunk-size 250 \
  --sleep-seconds 0.35 \
  --retry-after-seconds 45 \
  --max-entity-requests-per-chunk 3000 \
  --fail-on-incomplete
```

The chunk runner writes per-chunk artifacts under
`docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_chunks_en_ja/` and a
merged evidence artifact at
`docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_full_en_ja_latest.json`
plus `.md`. Re-running the same command skips completed chunks and resumes
incomplete/missing chunks. If a chunk hits public-endpoint rate limiting or the
per-chunk entity budget, the command stops and can be rerun later.

The full runner includes already-covered lemmas by default. This is intentional:
the goal is to find all safe Wikidata rows, including additional topics for
words that already have one topic from Kaikki, Japanese Wikipedia, or reviewed
JMDict evidence. Use `--exclude-covered` only for a cheaper uncovered-only pass.

After the full pass is complete, regenerate the product-safe promotion overlay
from the full Wikidata artifact:

```bash
python3 scripts/testing/srs_topic_autotag_promotion_overlay_en_ja.py \
  --wikidata-evidence-json docs/test_outputs/srs_topic_autotag_wikidata_claim_probe_full_en_ja_latest.json \
  --overlay-json-out docs/test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.json \
  --json-out docs/test_outputs/srs_topic_autotag_promotion_overlay_report_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.md
```

NDL authority smoke:

```bash
python3 scripts/testing/srs_topic_autotag_ndl_authority_probe_en_ja.py \
  --chunk-size 20 \
  --force \
  --lemma 野球 \
  --lemma 医学 \
  --lemma 漫画 \
  --lemma 台風 \
  --lemma 将棋 \
  --lemma 桜 \
  --lemma 寿司 \
  --lemma 犯人 \
  --sleep-seconds 0.05 \
  --json-out docs/test_outputs/srs_topic_autotag_ndl_authority_probe_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_topic_autotag_ndl_authority_probe_en_ja_latest.md
```

Resumable NDL authority pass:

```bash
python3 scripts/testing/srs_topic_autotag_ndl_authority_probe_en_ja.py \
  --chunk-size 250 \
  --sleep-seconds 0.2 \
  --fail-on-incomplete
```

The NDL runner writes per-chunk artifacts under
`docs/test_outputs/srs_topic_autotag_ndl_authority_probe_chunks_en_ja/`, a
cache at `docs/test_outputs/srs_topic_autotag_ndl_authority_probe_cache_en_ja.json`,
and a merged evidence artifact at
`docs/test_outputs/srs_topic_autotag_ndl_authority_probe_en_ja_latest.json`
plus `.md`. Re-running skips complete chunks unless `--force` is passed.

## First Local Run

The first local top-10k run produced:

| Source | Evidence Rows | Lemmas | Early Read |
| --- | ---: | ---: | --- |
| JMDict field direct | 1,157 | 947 | Best immediate candidate for promotion review. |
| JMDict gloss keyword | 824 | 699 | Plausible mining source; needs sampled precision review. |
| JMDict misc review | 247 | 241 | Useful for register and manga/slang discovery, not topic default. |
| English WordNet gloss bridge | 16,228 | 5,430 | Too noisy unguarded; useful mostly as a negative/control source. |

The most important result is structural: exact JMDict item matching removes the
same-reading false-positive family that hurt earlier topic experiments. The
guarded dump-source pass adds useful topic evidence, but the product-safe export
only promotes reviewed JMDict overlay rows plus strict Kaikki/Wiktionary and
Japanese Wikipedia rows, plus strict Wikidata claim-probe rows from the refined
artifact. It does not promote raw WordNet bridge rows, raw JMDict field rows
that have not already passed review, generic Wikidata search rows, NDL probe
rows, or broad dump evidence that only works as mining data.

Auto rows from Kaikki/Wiktionary, Japanese Wikipedia, and Wikidata are now
blocked from runtime by default. The review-label file can mark a row
`accept_runtime`, but even accepted rows must still pass the existing runtime
identity guards. Reject labels remove rows from the product-safe overlay while
preserving them in the full review ledger for audit.

Current product-safe candidate overlay:

| Metric | Count |
| --- | ---: |
| Overlay rows | 3,955 |
| Runtime-effective rows under membership >= 1.0 | 778 |
| Review-only rows kept below runtime threshold | 3,177 |
| Auto reject labels applied | 144 |
| Auto review ledger rows | 5,197 |

Rows below membership `1.0` are retained as review evidence only. The current
runtime overlay contract is lemma-only, so multi-reading lemma rows stay
review-only until runtime supports reading-specific topic overlays.

Runtime safety pass on 2026-07-02 reviewed the runtime-effective overlay rows
and the current preference/product acceptance mover samples. One clear
product-facing overlap was fixed: `コンピューター`, `インターネット`, and
`プログラム` were removed from `science_math_core` because they are already
covered by `computing_internet`. After regeneration, both sample packs still
pass and no unreviewed auto topic rows surface in the product acceptance review
pack. Remaining runtime rows are judged product-safe, with some intentionally
broad entries in anime/pop culture, hobbies, computing, and places/facilities.

Full off-diagonal topic/proficiency sampling on 2026-07-02 used
`docs/test_inputs/srs_admission_topic_proficiency_grid_configs_en_ja.json`.
The grid produced:

- `95` scenarios
- `84` pass findings
- `13` warn findings
- `0` fail findings
- `77` / `90` topic scenarios with topic movers
- `0` surfaced untrusted auto-topic rows in the grid review pack

The warnings are source-depth warnings, not precision failures: several
advanced-tail `p85` scenarios have no admitted topic movers because the
runtime-effective topic rows for shallow or sparse topics are mostly below the
advanced readiness window. The main affected topics are animals, food/cooking,
law/politics, medicine/health, music/media, science/math, shopping/money,
sports/fitness, travel/places, and work/office. This means the current behavior
backs off to neutral advanced admission instead of forcing weak topic matches.

The first grid run exposed a separate corrected-difficulty lookup bug:
display-only rows such as `段々 -> だんだん`, `御飯 -> ご飯`, and
`今日は -> こんにちは` could appear under the display form with no corrected
match and therefore fall back to frequency difficulty. The runtime corrected
difficulty index now supports exact and unique `display_form` matches. After
that fix, the grid has `0` admitted rows using the `1_minus_base_weight`
fallback and the advanced neutral samples no longer contain obvious early
display-only words at the top.

Randomized product-profile UX sampling is available through:

```bash
python3 scripts/testing/srs_admission_random_ux_sample_pack_en_ja.py \
  --draw-count 3 \
  --preview-count 40 \
  --json-out docs/test_outputs/srs_admission_random_ux_sample_pack_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_admission_random_ux_sample_pack_en_ja_latest.md
```

This sampler keeps the deterministic acceptance/grid artifacts separate. It
uses a true-random root seed by default, records all per-draw seeds for replay,
and samples a smaller preview from each profile-shaped active set. The artifact
keeps word-level metadata needed for qualitative UX review: corrected
difficulty, difficulty minus proficiency, topic affinity, proficiency fit,
readiness window, rank delta, correction/admission state, and topic/non-topic
leniency summaries.

The latest full run used the 30-scenario product-acceptance config with 3
draws and 40 words per draw:

- `30` scenarios
- `90` total random draws
- `31` pass findings
- `0` warnings/failures
- all `19` topic scenarios had topic movers
- root random seed: `7396708340892770270`
- random surfaced-auto review pack row count: `0`

This run gives a better UX feel than the deterministic grid. Higher-coverage
topics such as computing/internet, anime/manga/pop-culture, games,
hobbies/crafts, and mixed professional/entertainment profiles produced strong
topic share. Sparse or naturally shallow topics still had lower topic share,
which is expected and preferable to forcing bad topic matches.

## Explicit Admission Closure

Status: accepted with caveats for explicit en-ja configuration admission.

Latest acceptance artifacts after the hard admission-suitability selector gate:

- Preference sample pack:
  `../test_outputs/srs_admission_preference_sample_pack_en_ja_latest.md`
  - `PASS`, `18` scenarios, `14 / 14` topic scenarios with movers
  - findings: `20` pass, `0` warn, `0` fail
- Product acceptance pack:
  `../test_outputs/srs_admission_product_acceptance_en_ja_latest.md`
  - `PASS`, `30` scenarios, `19 / 19` topic scenarios with movers
  - findings: `32` pass, `0` warn, `0` fail
- Topic/proficiency grid:
  `../test_outputs/srs_admission_topic_proficiency_grid_en_ja_latest.md`
  - `WARN`, `95` scenarios, `77 / 90` topic scenarios with movers
  - findings: `84` pass, `13` warn, `0` fail
  - warnings are only "overlay present but no admitted topic movers" for sparse
    advanced-topic profiles such as `animals_p85`, `food_cooking_p85`,
    `law_politics_civics_p85`, `science_math_p85`, and similar p85/shallow
    cases.
- Random UX sample pack:
  `../test_outputs/srs_admission_random_ux_sample_pack_en_ja_latest.md`
  - `PASS`, `30` scenarios, `90` draws, `19 / 19` topic scenarios with movers
  - findings: `31` pass, `0` warn, `0` fail

All surfaced-auto review packs currently have row count `0`:

- product acceptance:
  `../test_outputs/srs_topic_surfaced_auto_review_pack_en_ja_latest.md`
- topic/proficiency grid:
  `../test_outputs/srs_topic_surfaced_auto_review_pack_grid_en_ja_latest.md`
- randomized UX:
  `../test_outputs/srs_topic_surfaced_auto_review_pack_random_ux_en_ja_latest.md`

Product interpretation:

- The explicit shape `proficiency_estimate: 0.00..1.00` plus optional
  `topic_weights` is product-plausible.
- Topic coverage is safe but incomplete. Sparse topics are allowed to fall back
  to neutral admission rather than forcing weak matches.
- Runtime-effective topic overlay rows are precision-first and only reviewed
  rows are allowed to affect product samples.
- Candidate rows with `admission_suitability=0.0` are now a hard selection
  block in the shared selector. They remain visible in diagnostic ranking
  previews, but cannot be selected into an active/admission set by top-n,
  reserved-topic-lane, or weighted selection.
- No-enabled-rule protection remains a lifecycle/rulegen viability layer:
  after rulegen output is available, active items without an enabled runtime
  rule are reconciled out with reason `no_enabled_rules`. Initial bootstrap and
  manual refresh now have bounded refill passes that block the failed lemmas,
  select replacement candidates within the original active/budget target, rerun
  rulegen, and keep only candidates that survive the same enabled-rule check.
  Rebalance still uses reconciliation only.

## Recommended Next Review

1. Keep the explicit configuration packs as the acceptance baseline.
2. Treat new topic evidence as coverage expansion only; promote rows only after
   source-specific review and rerun the same acceptance packs.
3. Harden admission viability next:
   - keep zero-suitability as a selector-level block;
   - keep no-enabled-rule reconciliation in mutation paths;
   - keep initial-bootstrap and manual-refresh no-rule refill enabled;
   - consider whether rebalance should also backfill when rulegen
     viability removes selected active items.
4. Add implicit browsing/reading trends only as a capped personalization signal
   over the accepted explicit admission path.

For the current branch, the product-safe promotion overlay is ready for
explicit sample testing. A systematic off-diagonal grid is available at
`docs/test_inputs/srs_admission_topic_proficiency_grid_configs_en_ja.json`.
It covers 5 shared proficiency levels (`p10`, `p25`, `p45`, `p65`, `p85`) for
each of the 16 runtime-effective topic families, plus neutral controls and
mixed-profile stress cases. This is intentionally broader than the
product-acceptance matrix: it tests happy paths and awkward cases, including
hard topics for beginners and shallow topics for advanced learners.

Run it with explicit outputs so it does not overwrite the smaller product
acceptance artifact:

```bash
python3 scripts/testing/srs_admission_preference_sample_pack_en_ja.py \
  --config-json docs/test_inputs/srs_admission_topic_proficiency_grid_configs_en_ja.json \
  --json-out docs/test_outputs/srs_admission_topic_proficiency_grid_en_ja_latest.json \
  --markdown-out docs/test_outputs/srs_admission_topic_proficiency_grid_en_ja_latest.md
```

The next untested-topic work should start from one of two paths:

1. sample profile/admission behavior with the product-safe overlay explicitly
   selected, or
2. test unpromoted sources as mining inputs only, then add guards before they
   can enter the promotion exporter.
