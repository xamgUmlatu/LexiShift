# Kaikki `en-es` Integration Plan

Status: draft implementation contract
Role: working design note
Last updated: 2026-03-26
Source-of-truth: current implementation still lives in code; this note records the intended contract for the first Kaikki-backed `en-es` rollout.

## Scope

- First target:
  - Replace `freedict-es-en` as the primary dictionary resource for `en-es` rulegen.
- First non-goals:
  - Do not add synonym runtime support yet.
  - Do not add a generic multi-purpose Wiktionary runtime loader.
  - Do not switch `es-en` in the same slice unless the reverse-check path is explicitly revisited.

## Source Decision

- Use the English-edition Kaikki raw dump as the source feed.
- Do not use Spanish-edition raw data for the first `en-es` rollout.

Reasoning:

- The English-edition dump exposes Spanish entries with English glosses, which matches the current `en-es` rulegen requirement: Spanish target headword -> English source-side gloss candidates.
- This keeps the replacement semantically aligned with the current `spa-eng.tei` role, while also preserving richer Wiktionary metadata for later ranking and filtering work.

## Resource Modeling Decision

- Model the first Kaikki resource as a pair-specific translation pack in the app.
- Do not model the first rollout as a generic `multi -> multi` runtime dictionary pack.

Implementation consequence:

- App-facing pack id should be specific to the runtime use case, e.g. `wiktionary-es-en`.
- The source URL may still be a multi-language Kaikki dump, but the post-conversion artifact must be pair-specific.

## Runtime Contract Decision

- The Kaikki converter must emit the same normalized SQLite surface that current FreeDict-backed rulegen already consumes.
- Existing runtime loaders and rulegen code should continue to work against the normalized `entries` table without requiring a new raw-data code path.

Required normalized table:

- `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`
- `meta(key, value)`

Required behavior:

- Preserve ordered gloss candidates for each headword.
- Preserve raw POS in the same `pos` field used by the current FreeDict SQLite path.
- Keep the SQLite file directly consumable by current dictionary loaders.

## Metadata Preservation Decision

- Do not discard Kaikki-only metadata during conversion.
- Preserve richer metadata in auxiliary tables and/or metadata JSON, while keeping the normalized `entries` contract stable.

First-slice auxiliary metadata priorities:

- record-level language and POS
- sense glosses and raw glosses
- sense tags/topics/categories
- entry forms
- entry sounds
- entry synonyms
- etymology text

## Extraction Decision

- For the first `en-es` converter, extract Spanish headwords from English-edition records where `lang_code == "es"`.
- Build translation candidates from English glosses in `senses[].glosses`.
- Do not build the first `en-es` resource from English translation boxes pointing to Spanish words.

Reasoning:

- Using Spanish entries with English glosses matches the current FreeDict `spa-eng` orientation.
- This is the cleanest drop-in replacement for `en-es` rulegen.

## Filtering Decision

- The first converter must exclude obvious non-lemma / inflection-only sense noise from the normalized `entries` output.
- Filtering should be conservative and explicitly documented.

First-slice exclusion targets:

- `form-of`
- `alt-of`
- inflection-only glosses such as `inflection of ...`

Note:

- Richer morphology-aware handling is a later improvement; the first slice only needs to stop obvious rulegen pollution.

## Download / Conversion Decision

- The app should support Kaikki via `download + convert + auto-link`.
- The converter must accept `.jsonl.gz` directly and stream it line-by-line.
- Avoid requiring a fully expanded intermediate raw file for normal app usage.

Implementation consequence:

- This flow should behave more like the existing frequency/embedding conversion flows than the existing FreeDict `download-as-is` flow.

## POS Normalization Decision

- Kaikki/Wiktionary should get its own explicit POS source profile.
- Do not keep treating Kaikki POS as `freedict` metadata by accident.

First-slice expectation:

- Common English POS tags from Kaikki such as `noun`, `verb`, `adj`, `adjective`, `adverb` should normalize through an explicit `wiktionary`/`kaikki` profile.

## Default Resolution Decision

- For `en-es`, pair resource resolution should prefer the Kaikki-derived SQLite artifact when present.
- FreeDict should remain as a fallback path during the transition.

## Reverse Source Evaluation Decision

- For the `en-es` reverse-check dictionary, use the English-edition Kaikki dump as the canonical
  source for a dedicated `wiktionary-en-es.sqlite` artifact.
- Do not build the reverse dictionary by mechanically inverting `wiktionary-es-en.sqlite`.
- Do not use Spanish-edition Kaikki as the first canonical reverse source.

Reasoning:

- English-edition Kaikki exposes English headwords with Spanish entries in `translations[]`, plus
  English-side senses and translation tags. This is the cleanest fit for `English source candidate
  -> Spanish reverse targets`.
- Spanish-edition Kaikki does expose English translations from Spanish entries, but that would
  still force the runtime artifact to be derived from Spanish-headword records rather than native
  English-headword translation boxes.
- Spot evaluation showed English-edition records like `mother`, `until`, `hello`, and `table`
  carry usable Spanish translation rows with sense text and regional tags, while sampled
  Spanish-edition English records were primarily definition-oriented and often had empty
  `translations[]`.

Implementation consequence:

- The reverse-check path should get its own pair-specific pack id, `wiktionary-en-es`.
- The converter should emit the same normalized `entries` contract as the forward Kaikki artifact,
  while preserving reverse-specific translation metadata in auxiliary tables.

## Verification Decision

- Because this touches `en-es` rulegen resource behavior, the canonical benchmark -> quality gate -> triage loop remains required.
- Targeted tests are required for:
  - converter schema/output
  - loader compatibility
  - POS normalization
  - `en-es` regression coverage for known gaps such as `movimiento`

## Current Measured Status

- Current comparable `en-es` benchmark lanes on the Kaikki artifacts are:
  - forward Kaikki, no reverse-check: `Top1 75.00%`, `Top3 85.42%`, `ForbidTop1 0.00%`
  - forward Kaikki + FreeDict reverse-check: `Top1 79.17%`, `Top3 85.42%`, `ForbidTop1 0.00%`
  - forward Kaikki + Kaikki reverse-check: `Top1 79.17%`, `Top3 85.42%`, `ForbidTop1 0.00%`
- Current conclusion:
  - reverse-check is helping
  - the current reverse signal is not the main remaining blocker
  - the dominant remaining blocker is forward-side sense policy for Kaikki-backed `en-es`

Observed reverse-check wins:

- `cargo`: reverse-check moves top1 from `debit` to `charge`
- `cuenta`: reverse-check moves top1 from `operation` to `account`
- `sacar`: reverse-check moves top1 from `take` to `draw`, but the case still needs review

Observed remaining failure classes:

- function-word / grammar-heavy targets:
  - `ese -> hello`
  - `hasta -> even`
  - `según -> no_rules_emitted`
- noisy sense selection:
  - `presentar -> table`
  - `plaza -> position` or `bullring`
  - `parte -> side` / `behalf`

## Diagnosed Failure Mechanism

The current `ese` failure is not a Kaikki conversion-order bug.

Verified Kaikki forward ordering for `ese`:

1. noun: `The name of the Latin script letter S/s.`
2. determiner: `that`
3. interjection: `hello`

Current runtime behavior:

- the noun gloss is dropped by the single-word filter because it is multiword
- the determiner gloss `that` is dropped by the generic English stopword filter
- the interjection gloss `hello` survives, so it becomes top1

Implication:

- current `en-es` filtering is too generic for function-word / grammar-adjacent targets
- current rulegen is not yet making use of Kaikki’s richer sense metadata even though the converter preserves it

## Metadata Availability Decision

Kaikki already preserves the metadata needed for the next rulegen slice.

Forward artifact (`wiktionary-es-en.sqlite`) already preserves:

- `entry_meta.pos`
- `entry_meta.pos_title`
- `entry_meta.tags_json`
- `entry_meta.categories_json`
- `sense_glosses.tags_json`
- `sense_glosses.topics_json`
- `sense_glosses.categories_json`
- `sense_glosses.form_of_json`
- `sense_glosses.alt_of_json`

Reverse artifact (`wiktionary-en-es.sqlite`) already preserves:

- normalized `entries`
- `translation_meta.sense_text`
- `translation_meta.english_text`
- `translation_meta.tags_json`

Current gap:

- runtime loader / candidate source still treats the Kaikki artifact mostly like FreeDict-compatible `translation + pos`
- richer Kaikki qualifiers such as `Mexico`, `informal`, `demonstrative`, and translation-box sense text are not yet consumed by production `en-es` rulegen

## SRS Scope Decision

- LexiShift SRS should remain vocabulary-first, not grammar-first.
- Very grammar-heavy targets may be filtered, deprioritized, or excluded from the admission/publication path.
- This should not be used as an excuse to leave rulegen in a broken state for such targets while they are still present in data, tests, or existing sets.

Practical interpretation:

- fix `en-es` rulegen first so absurd outputs like `ese -> hello` do not win
- then evaluate an admission-side policy for grammar-heavy targets such as:
  - determiners
  - conjunctions
  - prepositions
  - particles
  - pronouns used primarily as grammar carriers rather than lexical vocabulary

## Completed Slice: Function-Word Repair

The function-word / grammar-adjacent repair slice is now implemented.

Implemented changes:

- POS-aware stopword bypass for grammatical senses in `en-es`
- POS-aware short multiword support for grammatical senses
- interjection-shadow suppression for cases like `ese`
- first-pass Kaikki register/region demotion support
- Kaikki auxiliary metadata plumbing into runtime candidates

Observed benchmark outcomes after this slice:

- `ese -> that`
- `hasta -> until`
- `según -> according to`
- these cases no longer appear in the current triage set

This slice should be treated as complete and stable unless later tuning regresses it.

## Remaining Failure Analysis

The remaining `en-es` problems are now mostly lexical candidate-shaping and lexical polysemy, not function-word handling.

Direct raw Kaikki examples from the English-edition dump:

- `ocurrir`
  - first sense: `to happen, to occur`
  - second sense: `to come up with`
  - implication: this is not a source-coverage failure; current rulegen is losing the first sense structurally
- `presentar`
  - early broad senses: `to present, to submit`, `to introduce`, `to show`
  - later niche/domain senses: `to file` (law), `to table` (government)
  - implication: broad earlier senses are being lost while the later narrow sense `table` survives
- `plaza`
  - early broad sense: `plaza, town square`
  - later senses: `position`, `bullring`, `mall`
  - implication: unsplit broad lexical glosses are being lost; later single-token survivors win
- `parte`
  - early broad sense: `part; section; portion; share; piece; bit; cut; proportion`
  - later senses: `side`, `party`, `behalf`
  - implication: semicolon-delimited broad lexical senses are being lost while narrower late senses survive
- `cuadro`
  - early senses: `square`, `rectangle`, `picture`, `frame`
  - later senses: `chart`, `graph`, organizational senses, ellipsis senses
  - implication: this is partly candidate-shaping and partly lexical ranking / benchmark-label review

## Next Phased Plan

The next work should be sequenced deliberately. Do not bundle all remaining ideas into one large tuning pass.

### Phase A. Dictionary Entry Format Investigation And Robust Normalization

Priority:

- highest

Goal:

- build a formally robust solution for the variety of Kaikki/Wiktionary gloss-list formats instead of adding ad hoc word-specific fixes

Why this is first:

- `ocurrir`, `presentar`, `plaza`, and `parte` all show that broad early senses exist in Kaikki
- those senses are currently being lost because the current gloss sanitization and split logic is too narrow
- no amount of scoring or reverse-check tuning can fix candidates that never survive extraction

Scope of investigation:

- inventory the real gloss formats currently seen in Kaikki `en-es` for high-value Spanish entries
- classify the structural patterns, especially:
  - repeated infinitive lists such as `to happen, to occur`
  - comma-separated lexical alias lists such as `plaza, town square`
  - semicolon-delimited lexical lists such as `part; section; portion; share`
  - mixed parenthetical glosses such as `to introduce (someone), to acquaint`
  - domain-marked glosses that should stay grouped instead of being split too aggressively
- document which patterns should:
  - stay intact
  - split into multiple candidates
  - split only under specific POS or punctuation conditions

Design constraints:

- preserve raw Kaikki sense order
- preserve a stable sub-order within a split gloss
- preserve sense metadata on every emitted fragment
- avoid exploding candidate count through naive splitting
- avoid breaking the already-repaired function-word behavior

Expected implementation direction:

- replace the current narrow split heuristic in `_expand_en_es_gloss_variants()` with a more formal normalizer/splitter
- keep fragment generation deterministic and testable
- add focused fixtures for each known gloss-structure class before broad benchmark reruns

Expected case impact:

- `ocurrir` should emit `happen` and/or `occur`
- `presentar` should retain broad candidates such as `present`, `submit`, `introduce`
- `plaza` should retain `plaza` and/or `town square`
- `parte` should retain `part`, `section`, `portion`, `share`, `piece`

Acceptance criteria for Phase A:

- no-rule failure for `ocurrir` is eliminated
- broad early lexical candidates appear in probe output for `presentar`, `plaza`, and `parte`
- function-word fixes for `ese`, `hasta`, and `según` remain intact

Phase A implementation status:

- implemented

Observed raw-format findings from the bounded Kaikki investigation:

- sampled first `25,000` Spanish records from the English-edition raw dump
- observed counts in that bounded sample:
  - comma-bearing glosses: `6,372`
  - parenthetical + comma glosses: `2,042`
  - verb comma lists beginning with `to `: `1,785`
  - semicolon-bearing glosses: `1,321`
- representative observed patterns:
  - verb lists: `to happen, to occur`, `to generate, to create, to produce, to cause`
  - lexical alias lists: `plaza, town square`, `foot, base`, `free, without charge`
  - semicolon lexical lists: `part; section; portion; share`
  - mixed parenthetical lists: `to introduce (someone), to acquaint`

Implemented Phase A behavior:

- top-level delimiter splitting now respects parentheses/brackets/braces
- semicolon-delimited gloss lists are recovered as ordered fragment candidates
- comma-delimited verb gloss lists are recovered when they behave like real infinitive lists
- short lexical alias lists are recovered without enabling uncontrolled comma splitting
- inline parenthetical gloss annotations are stripped before shape filtering
- fragment-level metadata is preserved on emitted candidate records for later diagnostics/ranking work

Observed benchmark outcomes after Phase A:

- canonical `en-es` benchmark improved to:
  - `Top1 89.58%`
  - `Top3 93.75%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
- triage count dropped from `9` to `5`

Observed case outcomes after Phase A:

- fixed:
  - `ocurrir -> happen / occur`
  - `presentar -> present / submit / introduce`
  - `plaza -> plaza`
  - `parte -> part / section / portion`
- preserved from previous slice:
  - `ese -> that`
  - `hasta -> until`
  - `según -> according to`
- still remaining:
  - `cuadro -> square / rectangle / frame`
  - `cuenta -> count / tally / operation`
  - `sacar -> take / withdraw / expel`
  - review-class cases such as `derecho` and `red`

Conclusion after Phase A:

- structural candidate recovery is now materially improved and should be treated as implemented
- the next blocker is no longer “Kaikki lacks the word” or “the gloss format prevented emission”
- the next blocker is ranking among surviving lexical candidates, which is the start of Phase B / Phase C territory

### Phase B. Earlier-Sense-Skipped Suspicion Signal

Priority:

- medium, after Phase A

Goal:

- demote late survivors when earlier broader senses existed but were structurally lost or suppressed

Motivation:

- this captures the general failure shape behind `ese`
- it is also relevant for lexical cases where a later narrow sense wins only because earlier broad senses were not preserved cleanly

Expected direction:

- record whether earlier senses were skipped for structural reasons
- treat a surviving late sense as suspicious when:
  - all earlier senses were skipped or collapsed away
  - the surviving sense is materially later in sense order
  - the surviving sense is tagged as informal, region-limited, interjectional, or otherwise specialized

This should remain a second-pass ranking signal, not a substitute for Phase A candidate recovery.

Phase B architecture status:

- objective provenance plumbing is now implemented
- ranking/demotion behavior for this phase is still intentionally deferred

Implemented objective data-flow:

- every generated `en-es` candidate now carries:
  - raw dictionary metadata under `dictionary_record`
  - normalized Kaikki helper views under `dictionary_record_views.kaikki`
  - fragment-level gloss provenance under `gloss_provenance`
  - sense-level provenance under `sense_provenance`
  - target-level inventory/provenance under `target_provenance`
- gloss provenance now preserves:
  - raw gloss text
  - exact split-fragment source text
  - emitted fragment text before later candidate normalizers
  - fragment index/count/strategy/separator
  - normalization operations such as inline-annotation stripping
- target provenance now preserves objective inventory facts such as:
  - current sense ordinal/position
  - current sense candidate count
  - earlier sense count
  - surviving sense ordinals
  - surviving normalized dictionary POS canonicals

Important boundary:

- this slice does not yet assign suspicion penalties
- it only makes the necessary evidence available so a later ranking slice can do so explicitly and testably

Observed validation after landing this architecture:

- canonical `en-es` benchmark remained at:
  - `Top1 89.58%`
  - `Top3 93.75%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
- triage count remained `5`
- interpretation:
  - Phase B architecture is compatible with current behavior
  - any later movement in ranking can be attributed to the future policy layer rather than hidden data-flow changes

### Phase C. Kaikki Metadata-Aware Lexical Sense-Risk Demotion

Priority:

- medium/high, but explicitly deferred until after Phase A

Goal:

- use Kaikki topics/categories/tags to demote specialized domain senses when a broader everyday sense exists

Examples:

- `presentar -> table` should be demoted because it is government-specific
- `plaza -> bullring` should be demoted because it is entertainment/lifestyle-specific
- legal or technical side senses should not outrank broad everyday senses without strong support

Important decision:

- this is a real improvement path, but it is more difficult than the structural candidate-recovery work
- it should therefore remain a deliberate later slice, not be mixed into the Phase A investigation

Phase C architecture status:

- metadata normalization plumbing is now implemented
- shadow policy scaffolding is now implemented
- actual metadata-driven lexical demotion is still intentionally deferred

Implemented objective data-flow:

- Kaikki candidate metadata now exposes a normalized helper view with:
  - `marker_fields`
  - `prefixed_marker_fields`
  - `combined_markers`
  - `combined_prefixed_markers`
  - `text_fields`
  - `relation_fields`
  - `combined_relations`
  - `family_fields`
  - `combined_families`
- this keeps raw source metadata available while also exposing normalized views for later rulegen needs
- the view is designed so later ranking code can choose between:
  - raw strings
  - canonical normalized markers
  - coarse prefixed marker families
  - relation/text views
- every generated `en-es` candidate now also carries `kaikki_policy_shadow`, which records:
  - configured risky families for the current run
  - matched family hits for the candidate
  - whether competition was evaluated against same-canonical or all-target candidates
  - whether a cleaner competing candidate exists
  - whether the current candidate would be demoted if live policy were enabled
  - the exact reason trail for that shadow decision

Important boundary:

- Phase C scoring has not started yet
- current rulegen still does not demote lexical senses based on topics/categories/tags beyond the earlier targeted function-word/register fixes
- the purpose of this slice is to prevent future Phase C logic from needing another loader/candidate-schema refactor first
- the shadow object is the intended switch-point for later experiments:
  - enable or disable family groups
  - enable or disable live demotion
  - compare families/weights in benchmark sweeps without changing candidate extraction again

Observed validation after landing this shadow-policy scaffolding:

- canonical `en-es` benchmark remained at:
  - `Top1 89.58%`
  - `Top3 93.75%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
- triage count remained `5`
- interpretation:
  - family normalization and competition tracing are available for inspection now
  - any later metric movement can be attributed to explicit live-policy choices rather than hidden metadata-plumbing changes

First bounded harness experiment after wiring live-policy controls:

- benchmark harness now supports:
  - `--kaikki-policy-live-demotion-values`
  - `--kaikki-policy-risk-family-sets`
- bounded `en-es` matrix:
  - live demotion: `off/on`
  - family sets:
    - `math_geometry + government_law + hunting_fishing_tools + register_region + abbreviation_ellipsis_formof`
    - `math_geometry + government_law + hunting_fishing_tools`
- best observed run:
  - `Top1 89.58%`
  - `Top3 95.83%`
  - `ForbidTop1 0.00%`
  - `ForbidAny 0.00%`
- interpretation:
  - the first live policy path is already moving recall in the right direction
  - the smaller lexical family set performed identically to the broader set in this bounded run
  - the next useful question is not whether the harness can move the metric, but which case-level effects are worth keeping

Reverse exact-hit ambiguity signal:

- objective motivation:
  - `cuadro -> square` still showed `reverse=hit@0/22`, which means the exact reverse hit is real but highly ambiguous
  - the previous reverse scorer could see `reverse_check_total`, but only reverse-definition hygiene used it directly; ranking itself did not
- implemented signal:
  - reverse-check scoring now supports:
    - `exact_hit_ambiguity_threshold`
    - `exact_hit_ambiguity_penalty`
  - benchmark and probe harnesses now expose the same knobs
- validation outcome:
  - canonical `en-es` benchmark stayed unchanged with the default `xamb=off` lane:
    - `Top1 89.58%`
    - `Top3 97.92%`
  - first bounded reverse ambiguity experiment also kept the best run at `xamb=off`
- direct probe outcome for `cuadro`:
  - with `reverse_far_hit_penalty=0.2` and `reverse_miss_penalty=0.0`, turning on `xamb=12:0.80` reduced `square` from rank `1.0000` to `0.5333`
  - this confirmed the signal is wired correctly
  - but it did not change the capped top-5, because `rectangle` and the art/data senses are currently driven more by miss/far penalty settings than by exact-hit ambiguity alone
- current interpretation:
  - the exact-hit ambiguity signal is now available for later tuning and combination tests
  - it is not sufficient by itself to solve `cuadro`
  - the next meaningful quality gains are still likely to come from lexical-sense policy and/or short phrase policy, with reverse ambiguity acting as a supporting signal rather than a standalone fix

Reverse exact-hit specificity bonus:

- objective motivation:
  - not all `rank=0` reverse hits are equally informative
  - a candidate with `hit@0/1` should be able to receive more additive support than one with `hit@0/22`
  - this is the positive mirror of the ambiguity penalty and is strictly additive, so it can be swept without changing extraction or filter behavior
- implemented signal:
  - reverse-check scoring now also supports:
    - `exact_hit_specificity_bonus`
  - the bonus is scaled smoothly by reverse fanout:
    - effective bonus = `exact_hit_specificity_bonus / reverse_check_total`
  - benchmark and probe harnesses now expose the same knob
- validation outcome:
  - canonical `en-es` benchmark now sweeps `xspec` values `0.0`, `0.1`, and `0.2`
  - current best run still remains:
    - `rev=on`
    - `xamb=off`
    - `xspec=off`
  - summary metrics stayed unchanged at:
    - `Top1 89.58%`
    - `Top3 97.92%`
    - `ForbidTop1 0.00%`
- direct probe outcome for `cuadro`:
  - `xspec=0.2` did not change the uncapped or capped ordering
  - `square` stayed at rank `1.0000`
  - this is expected under the current scorer because the leading exact-hit candidate is already score-clamped at `1.0`
- current interpretation:
  - the exact-hit specificity bonus is implemented, harness-exposed, and available for later sweeps
  - under the current reverse match bonus and clamp behavior, it is mostly a neutral supporting signal rather than an immediate mover
  - if later sweeps continue to show saturation, the next related design question is whether reverse specificity should act earlier in scoring or under lower reverse match bonuses, not whether the current plumbing is present

### Phase D. Admission-Side Grammar Filtering

Priority:

- later, after rulegen correctness

Goal:

- decide whether grammar-heavy targets should remain in the main vocabulary-first SRS lane

Current decision:

- do not use admission filtering as a substitute for fixing rulegen
- revisit after the rulegen path is behaviorally sound

## Acceptance Criteria For The Current Planning Sequence

Phase-by-phase expectations:

- Phase A must focus completely on robust dictionary-entry-format handling
- Phase B must only follow once candidate recovery is verified
- Phase C is documented and deferred, not mixed into Phase A
- Phase D remains an admission-policy follow-up, not an immediate rulegen shortcut

Shared regression expectations:

- keep reverse-check improvements for `cargo` and `cuenta`
- keep the function-word repairs for `ese`, `hasta`, and `según`
- do not reintroduce the old FreeDict-style coverage hole for common words such as `movimiento`, `área`, `presentar`, `crear`
- do not increase forbidden-top1 rate from the current `0.00%`

Validation loop after each implemented phase:

- rerun the canonical `en-es` benchmark
- rerun the quality gate
- rerun benchmark triage
- run targeted tests for the touched rulegen/filter/loader modules

## Benchmark Artifact Ergonomics And Portability

Current benchmark artifact shape:

- resolved resource paths already exist in the top-level benchmark JSON under:
  - `resources[pair].translation_dict_path`
  - `resources[pair].reverse_translation_dict_path`
- `best_run` does not currently repeat that resource block
- this is intentional in the current implementation because all runs for a given pair share the same resource set during one benchmark invocation

Current limitation:

- the current shape is compact, but slightly awkward for downstream analysis because a consumer inspecting only `pairs[pair].best_run` does not see the resolved resources immediately
- the current artifact also records local absolute paths and the active `data_root`, which is useful for traceability but not yet sufficient for machine-to-machine reproducibility

Updated benchmark artifact decision:

- keep the canonical top-level `resources` block
- pair-local `resources` is now also mirrored under `pairs[pair]` as an ergonomics improvement
- do not duplicate the same resource payload into every individual run

Current reproducibility gap:

- benchmark runs currently depend on:
  - the resolved translation dictionary resources
  - the local `data_root`
  - the current SRS store for target `word_package` hints
- that means a copied git checkout is not yet a fully portable experiment environment by itself

Required portability work before the large PC-side sweep:

1. portable experiment bundle
- portable bundle export/replay is now implemented in `scripts/testing/rulegen_benchmark_bundle.py`
- the bundle now exports:
  - the exact SQLite/TEI resources used by the benchmark
  - the copied benchmark dataset
  - the copied source benchmark JSON
  - the frozen per-pair `word_package` snapshots
  - preset metadata and commit metadata
- the bundle can be validated and replayed on another machine without reading the live local SRS store
- the benchmark runner now supports `--word-package-snapshot-json` so bundle replay uses frozen input state instead of live helper state

2. benchmark input freezing
- resource checksums are now recorded in benchmark artifacts alongside resolved paths
- the exact per-target `word_package` snapshot used by the run is now recorded under each pair in the benchmark artifact
- avoid silently depending on whatever happens to be in the receiving machine's live SRS store

3. sweep preset portability
- named sweep presets now live in `docs/test_inputs/rulegen_benchmark_presets.json`
- current named methodologies include:
  - `en_es_canonical_matrix`
  - `en_es_policy_hypothesis_matrix`
- use the same preset names/files on both development machines so experiment intent stays stable

4. artifact ergonomics
- mirror `resources` under `pairs[pair]`
- make it easier to compare best-run results without separately looking up the top-level resource table

Current recommendation:

- the repo plus exported bundle is now good enough for the large PC-side broad sweep
- use the bundle `validate` and `run` flow on the receiving machine so the sweep stays tied to the frozen resource and `word_package` state
- keep the benchmark preset name in the source artifact so the methodology remains explicit

Implemented low-friction cleanup:

- benchmark JSON now mirrors pair-local `resources` under `pairs[pair]`
- benchmark JSON now also records SHA-256 checksums for the resolved dictionary resources
- benchmark JSON now records a per-pair `word_package_snapshot`, including explicit `null` entries for targets that had no package input
- benchmark CLI now supports `--preset`, `--preset-file`, and `--list-presets`, and records the selected preset in the `sweep` block when used
- benchmark bundle export/replay now exists in `scripts/testing/rulegen_benchmark_bundle.py`, and replayed the current canonical `en-es` lane successfully from frozen bundle inputs
- this does not change scoring behavior
- it improves artifact readability immediately
- it helps formalize benchmark methodology before the larger cross-machine sweep

## Deferred Work

- synonym extraction/runtime wiring
- generic multi-pair Kaikki pack generation and cataloging
- trait-conditioned rulegen profile routing driven by runtime-computable target/candidate features rather than manual tags:
  - planning spec: `docs/rulegen/trait_conditioned_rulegen_profiles.md`
- optional bundle archive/import ergonomics if we later want single-file transfer instead of directory transfer
