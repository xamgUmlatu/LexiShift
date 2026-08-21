# en-es Learner Difficulty Residual Signal Plan

Status: diagnostic handoff
Last updated: 2026-07-05

Purpose: break the remaining `en-es` learner-difficulty misses into explicit
component problems, then map each problem to signals we can test without
changing production ranking behavior.

## Current Anchor

The current working comparison point is documented in:

- `scripts/testing/srs_learner_difficulty_residual_patterns_en_es.py`
- `docs/test_outputs/srs_learner_difficulty_residual_patterns_en_es_latest.md`

That sidecar treats `learner_source_zipf_medium` as the fixed baseline and
`spalex_blend__lsb_w090_c022__cog_l__no_guard` as the current sweep-selected
candidate. It is diagnostic-only: runtime behavior and production ranking are
not changed.

## Component Problem Routes

| Route | Representative rows | What is wrong structurally | Signal needed |
| --- | --- | --- | --- |
| `source_void_too_hard` | `cachar`, `chipirón`, `desenfocar`, `guiri` | The broad learner source is absent, so the model has no positive evidence to distinguish useful tail words from obscure tail words. | Independent positive evidence: multi-domain frequency, subtitle/spoken frequency, domain list presence, or safer learner-source expansion. |
| `spoken_regional_commonness_gap` | `cachar`, `chingar`, `huevón`, `guiri`, `pedorro` | Some regional/colloquial words are common enough for learners or real media, but SPALEX plus learner lists leave them too late. | Spoken or social/web frequency, plus precise region/register tags so this does not become a broad regional rescue. |
| `vulgar_register_policy_split` | `chingar`, `huevón`, `pedorro`; counterexamples `culero`, `cerote` | Scalar difficulty and product admission policy diverge. A vulgar word can be easy/common while still needing admission/display policy. | Separate difficulty score from restriction/presentation flags; do not force vulgarity to mean high scalar difficulty. |
| `domain_concrete_register_gap` | `chipirón`, `telele`, `adulatorio`, `amputar`, `rótula` | Specific concrete/domain words are not all equally obscure; SPALEX tail rank alone over-raises some usable items. | Domain/topic presence, broad web/subtitle frequency, and possibly dictionary topic/category evidence. |
| `transparent_cognate_morphology_gap` | `desenfocar`, `reexaminar`, `adulatorio`, `presidenta`, `amputar` | English speakers can often infer transparent morphology or cognates, but the current rescue is too limited. | Prefix/suffix/morphology features, translation alignment, English-frequency-weighted cognate transparency. |
| `learner_cognate_over_rescue` | `parte`, `moraleja`, `par` | Learner or cognate evidence sometimes over-lowers short, polysemous, or domain-specific rows. | Dampener based on shortness, ambiguity, dictionary sense breadth, function/common-word collision, and low semantic specificity. |
| `marked_regional_counterexample_keep_current_shape` | `palta`, `culero`, `chucha`, `cerote`, `desmazalado` | Many marked/regional rows are already acceptable; any new route needs a guard set. | Route-specific counterexample review before promotion. |

The important modeling point is that these are not one problem. A single
"marked/regional" scalar cannot fix them, because some marked rows should move
down, some should stay high, and some need product policy rather than scalar
difficulty changes.

## Existing Signal To Expose More Precisely

The local `wiktionary-es-en` SQLite pack already has richer data than the
current scalar model exposes:

- `sense_glosses.tags_json` can contain country tags such as `Mexico`, `Chile`,
  `Peru`, `Spain`, and broader labels such as `Latin-America`.
- `sense_glosses.tags_json` also contains register labels such as
  `colloquial`, `slang`, `vulgar`, `archaic`, `dated`, `rare`, `uncommon`,
  `derogatory`, and `offensive`.
- `sense_glosses.categories_json` mirrors many of those labels as categories,
  for example `Mexican Spanish`, `Spanish vulgarities`, or
  `Spanish colloquialisms`.
- `sense_glosses.topics_json` can expose domain topics such as `botany`,
  `medicine`, `anatomy`, `law`, `physics`, or `finance`.

This should be the first no-new-license signal expansion. The model should not
use a broad boolean. It should expose reviewable subfeatures such as:

- `region_tag_count`
- `region_breadth_score`
- `has_latin_america_or_broad_region`
- `register_colloquial_score`
- `register_vulgar_score`
- `register_rare_dated_score`
- `domain_topic_count`
- `sensitive_policy_flag`

These features let us test targeted formulas while preserving counterexamples.

Implementation note: the current diagnostic palette/probe now exposes the
structured Kaikki subfeatures as additive fields and components:

- `dict_region_tag_count_score`
- `dict_domain_topic_count_score`
- `dict_register_colloquial_score`
- `dict_register_sensitive_score`
- `dict_register_rare_dated_score`
- `regional_colloquial_gate`
- `tail_domain_specificity`
- `tail_rare_dated_register`

The first sweep that included these components still selected the same
`no_guard` candidate as the best stable model. That does not make the
components useless; it means they should be treated as route diagnostics or
gates for stronger positive evidence, not as a broad global penalty.

## Unsupported-Ease Absence Gate Checkpoint

The next broad-shape experiment ported the `en-ja` exact-support idea into an
`en-es`-appropriate absence gate. Instead of treating broad-source absence as a
global penalty, the probe now exposes:

- `native_easy_support`: whether SPALEX already says the word is easy;
- `positive_ease_support`: broad learner-source presence, learner-source
  confidence/count, cognate transparency, native commonness, and normal
  dictionary presence;
- `unsupported_ease50` / `unsupported_ease65`: rows that look easy by SPALEX
  but lack broad learner-source or other positive ease support;
- gated variants such as `unsupported_ease_content`,
  `unsupported_ease_marked`, `unsupported_ease_usage`, and
  `unsupported_ease_structural`;
- floor variants such as `unsupported_ease_usage_floor060` so the sweep can
  raise only implausibly-easy unsupported rows.

This is mathematically different from the earlier tail absence checks because
it asks: "does the current model think this row belongs in the easy/mid range
without any independent ease support?" The answer is exposed as a component,
then weight and cap are swept.

The result was informative but not promotable. The expanded sweep still
selected `spalex_blend__lsb_w090_c022__cog_l__no_guard` as the best stable
candidate. `ue_marked_l` and `ue_usage_l` landed very close to the top, but
they did not improve calibration or holdout balanced score over `no_guard`.
Qualitatively:

- content/POS-gated absence was too broad and raised names, months, countries,
  and function-like rows;
- marked/domain-gated absence was narrower but still let dictionary domain and
  markedness metadata pull up names or country/topic rows;
- usage-only absence excluded domain-topic evidence, but dictionary markedness
  itself remained too broad for a clean global scalar correction.

The conclusion is not that absence is useless. It is that absence mainly
identifies review routes. The remaining large misses are mostly useful tail
words that need independent positive evidence, not an additional absence-based
penalty.

## External Signal Candidates

| Candidate | What it gives | Why it may help | Main concern |
| --- | --- | --- | --- |
| `wordfreq` Spanish Zipf | Multi-domain word frequency through roughly 2021; Spanish has broad source coverage. | Good first sidecar for independent commonness, especially because it mixes web/social/subtitles/books/news instead of only SPALEX. | Data redistribution/licensing needs review before product bundling; it is rounded/binned frequency, not a pedagogical source. |
| LexComSpaL2 | Direct Spanish L2 lexical-complexity judgments on a 0-1 scale for 2,240 in-context target words. | Closest current open signal to learner difficulty itself; especially useful as a counterweight when SPALEX puts transparent/common learner words too late. | Token-level and domain-limited. Broad rescue over-pulls early product-priority words, so only narrowed/capped sidecar shapes should be considered. |
| `hermitdave/FrequencyWords` `es_full` | Raw OpenSubtitles surface counts with deep tail coverage. | Strong for colloquial/spoken rows that written-frequency sources miss. It found many residual probe words. | Subtitle translation bias; content is CC BY-SA; surface counts are not lemma-safe. |
| `orgtre/top-open-subtitles-sentences` | Cleaned top OpenSubtitles words/sentences and original-language-only variant. | Useful sanity check for spoken subtitle commonness. | Top-word lists stop at 30k; original-language-only Spanish is sparse; translation bias remains. |
| `doozan/spanish_data` `frequency.csv` | Lemma-like frequency rows plus form breakdowns derived from subtitle data. | Morphology aggregation could help verbs such as `amputar` or `abalanzar`. | Not independent of subtitle frequency, and some lemma/form merges look unsafe, so it should be diagnostic-only until audited. |
| Corpus del Español / WordFrequency.info | Lemma/frequency and dialect/genre resources. | Probably strong for real Spanish frequency/dialect questions. | Access/licensing/manual-supply constraints; not a low-friction product source yet. |
| Sketch Engine / esTenTen | Huge web corpus, regional varieties possible. | Strong theoretical fit for modern/domain/regional commonness. | Commercial/tool access; not an immediate open sidecar. |
| Leipzig/Wortschatz | Downloadable corpora can be CC BY; query service has stricter terms. | Could be useful if a Spanish downloadable corpus is located. | Not clearly available through the same simple managed path as existing English/German packs. |

## Probe Findings So Far

Installed `wordfreq` gives useful but incomplete separation:

| Lemma | `wordfreq` Zipf | Interpretation |
| --- | ---: | --- |
| `parte` | 6.00 | Correctly very common; over-rescue risk is not frequency absence. |
| `par` | 5.07 | Correctly common, but still polysemous/short and needs dampening. |
| `presidenta` | 4.40 | Strong evidence that the current score is too high. |
| `chingar` | 3.30 | Spoken/vulgar commonness exists. |
| `chucha` | 3.31 | Good counterexample for vulgar-policy split. |
| `culero` | 3.30 | Good counterexample for vulgar-policy split. |
| `palta` | 2.88 | Regionally common enough to avoid a blanket regional penalty. |
| `huevón` | 2.77 | Spoken/regional row with real commonness support. |
| `pedorro` | 2.73 | Spoken/register row with support. |
| `amputar` | 2.53 | Transparent/domain verb with some support. |
| `guiri` | 2.38 | Some support, but still not enough alone. |
| `cachar` | 2.28 | Some support, but weaker than desired. |
| `reexaminar` | 2.17 | Morphology/cognate rescue probably matters more than frequency. |
| `chipirón` | 1.47 | Frequency does not support a large downshift by itself. |
| `telele` | 1.55 | Frequency does not support a large downshift by itself. |
| `adulatorio` | 0.00 | Confirms it is not a commonness rescue candidate. |

LexComSpaL2 now gives a direct learner-complexity lane:

- local source files live under `data/external/lexcomspal2/`;
- the formula probe loads `LexComSpaL2_all.tsv` when present;
- coverage is narrow (`905 / 44,853` probe rows in the latest run), but the
  rows are high-value because they are actual L2 difficulty judgments;
- broad LexCom rescue was too aggressive and over-lowered early words such as
  `vida`, `tiempo`, `país`, `año`, and `parte`;
- the retained sweep shapes therefore test micro rescue and
  `lexcom_rescue_after030` / `lexcom_rescue_after040` instead of a flat global
  rescue.

Latest side-source sweep result:

| Candidate family | Calibration balanced | Holdout balanced | Calibration MAE | Holdout MAE | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| no side source: `spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard` | 0.897895 | 0.897837 | 0.067568 | 0.078253 | Previous stable shape. |
| narrowed LexCom: `spalex_blend__lsb_w090_c022__cog_l__lex_mid_l__lex_caution_l` | 0.898393 | 0.898364 | 0.066575 | 0.076830 | Small but real improvement; keep diagnostic pending qualitative review. |
| broad LexCom rescue | higher balanced in one run | mixed | worse MAE/residuals | mixed | Rejected as too aggressive because it over-pulled early product-priority rows. |

Subtitle-derived sources give a different view:

- `FrequencyWords` `es_full` finds many deep-tail residuals that top-30k lists
  miss, including `huevón`, `pedorro`, `cachar`, `guiri`, `mocasín`, and
  `amputar`.
- `doozan/spanish_data` lemma aggregation finds `chingar`, `huevón`,
  `mocasín`, `amputar`, `parte`, `par`, `moraleja`, `abalanzar`, `vallar`,
  and `rótula`, but its form breakdown can show unsafe merges. For example,
  the `vallar` row includes forms that are probably not clean evidence for the
  lemma.

## Recommended Next Experiments

1. Expose precise Kaikki region/register/domain features in the formula probe.
   This is the safest because it uses data we already ingest. This is now
   implemented in the diagnostic sidecars.
2. Keep diagnostic-only `wordfreq` and LexComSpaL2 side-source lanes in the
   probe/sweep. Gate them to route-specific or post-early-range shapes, and
   let weight zero remain a valid sweep outcome.
3. Test a spoken/subtitle commonness lane only as a sidecar. Prefer
   `FrequencyWords es_full` over top-30k OpenSubtitles lists for diagnostic
   coverage, but do not promote it without license and counterexample review.
4. Test a cognate/morphology rescue refinement separately from regional/spoken
   fixes. These are mathematically different routes.
5. Add a dampener for short/polysemous over-rescued rows and verify against
   `parte`, `par`, and `moraleja` before broad promotion.

## Non-Goals

- Do not treat all marked/regional words as easier.
- Do not treat all vulgar words as harder.
- Do not use product restriction policy as scalar difficulty.
- Do not promote external corpus data until licensing/provenance and
  counterexample review are explicit.
