# en-es Learner Signal Source Matrix

Status: active source audit for first learner-difficulty formula work
Last updated: 2026-07-05
Purpose: track the signal sources available for `en-es` learner-difficulty
ranking before adding manual correction rows.

## Policy

This workstream should follow the `en-ja` sequence, but not copy its source
assumptions. The first `en-es` pass should:

- expose every already-wired product signal that can plausibly help ordering;
- keep formula experiments separate from manual corrections;
- avoid treating dictionary metadata as difficulty truth before precision
  checks;
- keep topic preference/admission signals separate from the base proficiency
  ladder unless a formula experiment explicitly tests the interaction.

## Current Product-Usable Source Lanes

| Source | Product lane | Current use | Signal candidates | Notes |
| --- | --- | --- | --- | --- |
| SPALEX frequency pack (`freq-es-spalex-v1`) | `auto-download` / app-managed local build | Default `en-es` SRS candidate frequency source. | rank/commonness (`id`, `pmw`), SPALEX source rank/frequency, Zipf, total prevalence, total percent, source-family metadata | Strongest current native-exposure signal. It gives ordering/commonness, not learner curriculum level. |
| UD AnCora POS overlay (`pos-es-ud-ancora-v1`) | `auto-download` / app-managed local build | Optional POS enrichment over SPALEX forms. | UPOS-derived raw POS, canonical POS, POS bucket, overlay confidence/counts, source-provider metadata | SPALEX itself has no POS. The overlay is keyed by Spanish word form, not lemma, to avoid false joins for forms such as `una`. |
| Kaikki/Wiktionary ES->EN (`wiktionary-es-en`) | app-managed local build; license obligations tracked separately | Primary dictionary/rulegen source and optional metadata source. | dictionary POS, entry count, sense/gloss/translation counts, sense topics, tags, categories, form-of/alt-of counts, forms/sounds/synonyms/etymology presence | Useful for ambiguity, register/domain, and candidate-quality experiments. Tags/categories must stay reviewable because they can be noisy. |
| FreeDict ES->EN (`freedict-es-en`) | app-managed local build | Fallback dictionary source for rulegen. | headword coverage, translation count, POS when present | Useful as coverage backup, but not currently the preferred difficulty signal. |
| SRS candidate classifier | built-in | Seed/admission candidate state and suitability. | candidate state, presentation mode, problem class, classification confidence/reasons, admission suitability | Product policy signal. Good for filtering or gating, not a scalar difficulty truth by itself. |
| Topic overlays / profile topics | built-in + generated local overlays | Topic preference and admission prioritization. | sense/profile topics, topic source, product topic families | Important for personalized admission. Use carefully in base difficulty because topic salience is not the same as proficiency. |
| Internal Spanish form analyzer | built-in diagnostic | Weak orthographic/form metadata for formula sweeps. | character length, token count, diacritics, Spanish-specific letters, punctuation/hyphen/space/digit flags, suffix-like cues (`-mente`, `-ción`, infinitives, participles, gerunds) | Weak supporting signal. Best as an interaction or tie-breaker after frequency/POS/dictionary evidence. |

## Current Diagnostic Learner/Core Source Overlay

| Source | License / lane | Current use | Signal candidates | Notes |
| --- | --- | --- | --- | --- |
| Wiktionary Spanish1000 subtitle list | Wiktionary CC BY-SA/GFDL terms; sidecar diagnostic | Parsed by `srs_learner_difficulty_learner_source_audit_en_es.py` into a lemma-keyed overlay. | top-1000 subtitle rank, surface hit, lemma hit, weak learner-core score/confidence | This is not CEFR or curriculum data. It is a separate spoken/subtitle-core perspective that helps pull obvious core words down when SPALEX Zipf places them late. |
| `lsspkk/espanjapeli` Spanish words | MIT; sidecar diagnostic | Parsed from `svelte/src/lib/data/words.ts`. | beginner-list presence, optional CEFR/frequency fields where the source supplies them | Small and not authoritative, but product-plausible as weak beginner/core evidence. |
| `pretzelai/openlingo` A1 Spanish lesson | MIT; sidecar diagnostic | Parsed from the A1 Spanish lesson markdown. | A1 lesson vocabulary presence | Very small source. Useful as a sanity signal only, not broad coverage. |
| `pretzelai/openlingo` Spanish dictionary | MIT; sidecar diagnostic | Parsed from `words/spanish.json`. | CEFR-like level, source word-frequency rank, flashcard suitability, example sentence/translation presence | Broadest current learner/pedagogical source for en-es. It is product-usable diagnostic evidence, but not an official CEFR/DELE specification. |
| LexComSpaL2 | ODC-BY 1.0; sidecar diagnostic | Loaded from `data/external/lexcomspal2/LexComSpaL2_all.tsv` when present. | token-level Spanish L2 lexical complexity (`overall`, `PL1`, `PL2`, `PL3`), corpus domain, row count | Direct learner-complexity evidence. Coverage is narrow and domain-limited, so the formula probe exposes it as capped rescue/caution evidence rather than replacing the ranking target. |

The generated overlay artifact is:

- `scripts/testing/srs_learner_difficulty_learner_source_audit_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_learner_source_audit_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_learner_source_audit_en_es_latest.md`

The current full-corpus overlay covers `12,877 / 44,853` candidate rows. The
OpenLingo dictionary supplies most of that coverage (`12,795` matched rows).
This changes the overlay from a narrow beginner/core rescue into a broad
learner-source lane. It should still be bounded and tested against SPALEX
rather than treated as official CEFR truth.

Absence semantics are explicit in the current palette/probe:

- absence from tiny lesson/list sources is not evidence;
- absence from the broad OpenLingo dictionary is exposed as a testable feature;
- no fixed model currently turns broad-source absence into a penalty by itself;
- the shape sweep can test tail-gated absence guards such as
  `learner_broad_absence_tail65`;
- the probe also exposes en-ja-inspired "unsupported easy row" components such
  as `positive_ease_support`, `unsupported_ease65`,
  `unsupported_ease_usage`, and `unsupported_ease_usage_floor060`, where broad
  learner-source absence only matters when the row otherwise looks too easy
  and lacks independent ease support.

## Deferred Or Research-Needed Inputs

| Source type | Current lane | Reason |
| --- | --- | --- |
| Authoritative CEFR / DELE / school-level Spanish vocabulary lists | `research-needed` | Would be the closest `en-es` analogue to JLPT/lesson sources. This pass did not find a product-safe authoritative open list. |
| Textbook or graded-reader vocabulary | `research-needed` | Pedagogically valuable, but copyright/licensing varies. |
| Subtitle/web/book corpora beyond SPALEX | `research-needed` | Could improve register or modern-use ordering, but requires provenance, license, and fit checks. |
| Spanish learner dictionaries or platform levels | `research-needed` | Potentially strong learner-order signal, usually constrained by terms or unclear bulk-use rights. |
| CodingFriends basic vocabulary word lists | `not-ingested` | Beginner vocabulary shape is useful, but the source is CC BY-NC 4.0 and therefore not product-safe without a separate licensing decision. |
| ArtCC FreeLingo Spanish vocabulary sets | `not-ingested` | Rich CEFR-like sets exist, but the repo is AGPL-3.0 and should not be copied into product data without an explicit licensing decision. |
| `gamescomputersplay/vocabulary-test` Spanish levels | `not-ingested` | The project describes Spanish levels as frequency-ranked chunks, so this does not add independent learner-level evidence over frequency. |

## Sweep Readiness

The first formula-sweep-ready signal set should use only already-wired lanes:

1. SPALEX rank/commonness, Zipf, prevalence, and percent fields.
2. Effective POS from frequency rows and/or the UD AnCora overlay.
3. Candidate state, problem class, presentation mode, and admission suitability.
4. Kaikki/Wiktionary dictionary metadata: entry/sense/gloss counts, POS values,
   topics, tags, categories, and form-of/alt-of flags.
5. Existing topic hints as optional admission/preference interactions.
6. Internal Spanish form features as weak complexity/interactions.

Formula sweeps should report:

- calibration accuracy once reviewed `en-es` labels exist;
- monotonicity of sampled difficulty bands;
- beginner/core retention without manual corrections;
- false promotion of grammar/function/noisy dictionary rows;
- coverage by source family, POS bucket, topic, and dictionary metadata.

## Diagnostic Artifact

The current signal-palette sidecar is:

- `scripts/testing/srs_learner_difficulty_signal_palette_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_signal_palette_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_signal_palette_en_es_latest.md`

It is deliberately read-only. It builds `en-es` seeds through the same
`build_seed_candidates` path used by SRS admission, then inspects the raw
frequency SQLite and optional Kaikki/Wiktionary auxiliary tables to show which
signals are actually available.

The current cross-language transfer audit is:

- `docs/srs/srs_learner_difficulty_en_ja_to_en_es_transfer_audit.md`

It translates mature `en-ja` model roles into `en-es` sweep candidates and
separates directly transferable ideas from Japanese-specific mechanisms that
should not be ported.

The first formula-shape probe sidecar is:

- `scripts/testing/srs_learner_difficulty_formula_probe_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_formula_probe_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_formula_probe_en_es_latest.md`

It materializes the transferable signal families as isolated candidate
rankings: SPALEX frequency bases, bounded POS/function guards, dictionary
markedness/ambiguity/form guards, and English-Spanish cognate/transparency
rescue using Wiktionary translations plus local English frequency. It also
includes bounded learner-source rescue variants when the learner-source overlay
artifact is present. The current probe also exposes optional side-source lanes:
`wordfreq` Spanish Zipf commonness and LexComSpaL2 learner-complexity
rescue/caution components when those local dependencies are available. It is
still diagnostic-only: no production ranking, runtime behavior, or manual
correction layer is changed.

The first calibration review-pack sidecar is:

- `scripts/testing/srs_learner_difficulty_calibration_review_pack_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_latest.md`
- balanced JSON output:
  `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.json`
- balanced Markdown output:
  `docs/test_outputs/srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.md`

It samples formula-probe rows across base difficulty bands and targeted
diagnostic strata, then emits editable label stubs plus a fixed
calibration/holdout split. It is the first artifact intended for human
`en-es` difficulty labeling, but it still does not add labels or alter runtime
behavior. The `diagnostic` selection profile keeps stress-test coverage; the
`balanced` profile is the preferred first labeling pack because it limits
pure grammar anchors, adds low-rank content vocabulary, and keeps explicit
absolute-tail anchors.

The first promoted reviewed label inputs are:

- calibration:
  `docs/test_inputs/srs_learner_difficulty_calibration_en_es.json`
- holdout:
  `docs/test_inputs/srs_learner_difficulty_holdout_en_es.json`

They preserve the balanced review pack's preassigned split: 100 calibration
rows and 50 holdout rows. Numeric learner-difficulty labels are kept separate
from `review_treatment` and policy flags so sweeps can score ranking accuracy
without confusing admission restrictions with scalar difficulty.

The first labeled formula-evaluation sidecar is:

- `scripts/testing/srs_learner_difficulty_formula_eval_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_formula_eval_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_formula_eval_en_es_latest.md`

It scores the current formula-probe variants against the promoted calibration
and holdout labels. Primary metrics exclude `deprioritized_vocab` rows; the
artifact also reports all-numeric metrics so restriction policy remains visible.

The first scalar/shape sweep sidecar is:

- `scripts/testing/srs_learner_difficulty_formula_sweep_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_formula_sweep_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_formula_sweep_en_es_latest.md`

It recombines already-materialized formula-probe components across SPALEX
base choice, learner-source rescue strength/cap, cognate rescue, capped
POS/dictionary guards, tail-gated broad-source absence, and unsupported-ease
absence gates. This sweep is still diagnostic-only. With the OpenLingo Spanish
dictionary included, the fixed `learner_source_zipf_medium` variant improves to
roughly `0.880` calibration / `0.890` holdout balanced score. The side-source
sweep currently reaches roughly `0.898` / `0.898` without side-source evidence
and roughly `0.898` / `0.898` with a narrowed LexComSpaL2 correction. The
LexCom shape slightly improves stable holdout/MAE versus the no-side-source
stable candidate, but the effect is small and should remain diagnostic until
qualitative review. A broader LexCom rescue over-pulled early product-priority
words, so the retained sweep shapes gate LexCom rescue after the very early
range. Tail-gated broad-source absence and unsupported-ease absence variants
did not win this pass, which suggests absence is useful to expose but not yet a
primary global correction.

The residual-pattern handoff sidecar is:

- `scripts/testing/srs_learner_difficulty_residual_patterns_en_es.py`
- default JSON output:
  `docs/test_outputs/srs_learner_difficulty_residual_patterns_en_es_latest.json`
- default Markdown output:
  `docs/test_outputs/srs_learner_difficulty_residual_patterns_en_es_latest.md`

It treats `learner_source_zipf_medium` as the fixed baseline and the current
stable sweep candidate as the working comparison point. The current candidate
is `spalex_blend__lsb_w090_c022__cog_l__lex_mid_l__lex_caution_l`. The report
groups remaining reviewed-label residuals by computable tags so the next phase
can target specific failure families instead of continuing broad shape search.
In the current run, most residuals are still too-hard rows that are absent from
the broad learner source; the smaller too-easy cluster is mostly over-rescued
learner-source/cognate rows.

The component-problem route handoff is:

- `docs/srs/srs_learner_difficulty_en_es_residual_signal_plan.md`

It splits the residual queue into explicit source-void, spoken/regional,
vulgar-policy, domain/register, transparent-cognate, over-rescue, and
counterexample-guard routes. This is the current bridge between broad formula
sweeps and targeted signal experiments.

## Current Interpretation

Compared with `en-ja`, `en-es` starts with fewer pedagogical anchors and much
less target-script burden. The current likely hierarchy is:

1. SPALEX commonness/native exposure as the base ordering signal.
2. Broad learner-source evidence as bounded pedagogical ceilings/anchors,
   especially from OpenLingo's CEFR-like dictionary plus smaller core/lesson
   sources.
3. Explicit absence semantics: most missing sources mean nothing; broad-source
   absence is only a tail-gated or unsupported-easy-row experimental signal.
4. POS and candidate classification to protect the SRS ladder from function
   words, proper-like rows, and low-suitability candidates.
5. Dictionary metadata to detect ambiguity, marked/register/domain cues, and
   form-of/alt-of noise.
   The diagnostic palette/probe now separates broad dictionary markedness into
   region count, colloquial/slang, sensitive/vulgar, rare/dated, and domain
   topic components so absence-of-learner-source can be tested against more
   precise positive/negative evidence. The usage-only unsupported-ease variant
   deliberately excludes domain-topic evidence, but the latest sweep still did
   not promote it globally.
6. Spanish form features only as weak shape/interaction signals.
7. Manual corrections only after formula work has exposed the remaining
   systematic failures.
