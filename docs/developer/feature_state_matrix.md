# Feature State Matrix

Status: active ledger
Role: Canonical current
Last updated: 2026-04-15
Source-of-truth: cross-cutting state ledger; runtime truth still lives in code, tests, and dated evidence artifacts.

Purpose:
- Keep feature state explicit for GenAI-driven development.
- Separate `implemented`, `default-on`, `verified`, and `planned` so current behavior is easy to recover.
- Give each feature a dated checkpoint plus evidence paths.

Use this file when:
- default behavior changes,
- benchmark policy or baseline assumptions change,
- a workstream moves from scaffolded to executable,
- code inspection finds a doc/code mismatch that should be tracked.

## Status Vocabulary

- `planned`: documented idea only.
- `scaffolded`: code/docs shape exists, but behavior is not yet fully executable.
- `implemented`: code path exists and is usable.
- `default-on`: implemented and enabled in normal/default behavior.
- `verified`: implementation has recent evidence (artifact, test, or direct code inspection).

## Date Fields

- `Last documented checkpoint`: most recent dated doc milestone or spec update.
- `Last verified`: most recent artifact date, test evidence, or dated code inspection.

## Rulegen Benchmark / Gate / Triage Loop

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-04-08`
- Last verified: `2026-04-08` pair-local dataset split tooling tests + `en-ja` preset audit on the pair-local dataset path
- Default behavior:
  - Required for rulegen scoring, candidate filtering, POS normalization, and LP tuning changes.
  - Canonical loop remains benchmark -> quality gate -> triage.
  - Pair-local benchmark datasets under `docs/test_inputs/rulegen_benchmark_cases/` are now the development edit surface for tuned pairs, while `docs/test_inputs/rulegen_benchmark_cases.json` remains the compatibility aggregate consumed by default CLI flows that do not opt into a pair-local dataset path.
  - Latest rulegen artifacts now have human-facing Markdown summaries for benchmark, gate, and triage surfaces.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `docs/developer/rulegen_test_pipeline.md`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_benchmark_case_sync.py`
  - `scripts/testing/rulegen_benchmark_bundle.py`
  - `scripts/testing/rulegen_benchmark_presets.py`
  - `scripts/testing/rulegen_benchmark_summary.py`
  - `scripts/testing/rulegen_quality_gate.py`
  - `scripts/testing/rulegen_quality_gate_summary.py`
  - `scripts/testing/rulegen_benchmark_triage.py`
  - `scripts/testing/rulegen_benchmark_triage_summary.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_summary_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_summary_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_summary_latest.md`
- Known gaps:
  - Current `docs/test_outputs/rulegen_quality_gate_latest.json` has FAIL findings for `en-es` quality floor and delta budget.
  - Recommended pairs (`en-ja`, `en-de`, `es-en`) are still advisory rather than hard-gated.
  - Cross-machine benchmark artifacts can preserve source-machine absolute dataset paths; the gate now falls back to the repo-local dataset copy when the original path is unavailable.
  - Artifact history and pair inference still depend on wrapper usage rather than a mandatory repo-wide gate.
  - Benchmark artifacts now mirror resolved resources under each pair as well as in the top-level `resources` block, they now carry SHA-256 resource checksums, they now record the effective per-target `word_package` snapshot used by the run, the benchmark CLI now supports named preset methodologies from `docs/test_inputs/rulegen_benchmark_presets.json`, and portable bundle export/replay now packages the exact dataset/resources/snapshots for cross-machine reruns; the remaining ergonomic gap is optional single-file archive/import support.

## Rulegen Benchmark Optimization Architecture

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-03-29` seventh `en-es` benchmark-expansion tranche (`100` cases), canonical refresh, and frozen profile-bank refresh on the `100`-case suite
- Last verified: `2026-03-29` canonical `en-es` benchmark/gate/triage refresh on the `100`-case suite, targeted benchmark test rerun, frozen profile-bank rerun, and pipeline/state/doc sync
- Default behavior:
  - Active direction remains a non-throwaway benchmark acceleration program that keeps the current canonical preset methodology while moving the implementation toward a `compile -> sweep -> materialize` architecture, a backend-neutral pair-resource contract, and later trait-aware profile analysis on top of the same benchmark substrate.
  - Already landed slices include timing/profiling instrumentation, pair-context caching, compute/materialization split, compiled `en-es` candidate/case/result tables, deferred case-payload materialization, a direct compiled non-variant `en-es` sweep path that can bypass adapter-generated `VocabRule`s, a compiled benchmark-only variant-row path so the canonical `var=on` half of the `en-es` matrix no longer has to use the live adapter loop, narrower overlay-demotion caching so score-table rebuilds do not recompute Kaikki policy rows for every score-weight-only config change, a backend-neutral persistent path-cache layer for translation-pack metadata plus benchmark resource checksums, and the Phase 5 serial-sweep preparation path that now prebuilds compiled `en-es` requests/configs/filter tables/score tables/compact selected-row tables before the remaining per-run case evaluation loop. The compiled score path now also uses `numpy` arrays plus an explicit config-matrix projection for batch score/ranking computation, offers a guarded local `torch` CUDA score backend behind `LEXISHIFT_RULEGEN_SCORE_BACKEND`, replaces string source-phrase tie-breakers with stable numeric phrase-order ids, and reuses equivalent selected-row tables across distinct configs by compiled row-selection signatures: accepted row groups, target-ranked row order, reverse-hygiene signals, and threshold pass/fail rows, rather than intermediate score-table object identity or raw confidence payloads.
  - The `en-es` benchmark surface now also exposes a wider Kaikki family/category control plane without changing canonical defaults: normalized family sets include `art_media`, `communication_network`, `computing`, `mechanics_tools`, `music`, `biology`, and `chemistry`, and non-default per-family demotion maps can now be swept explicitly through `--kaikki-policy-risk-family-demotion-sets` / `en_es_stage_a_family_followup_v2`.
  - Current architecture now also explicitly treats database-specific logic as a resource-layer concern: the benchmark workstream is moving toward backend-neutral translation-pack record/loader contracts, with FreeDict/Kaikki compatibility loaders as one current implementation rather than the architectural model.
  - Latest canonical `en-es` benchmark now lands at objective `131.180` with `Top1 89.00%`, `Top3 100.00%`, `ForbidAny 0.00%`, and `AvgRulesPerTarget 2.97`; the current actionable set is `11` review items with no hard fails.
  - The benchmark suite now spans `100` `en-es` cases. The seventh tranche (`banda`, `registro`, `patrón`, `trazo`, `tráfico`, `mando`) added three canonical passes plus three new review cases, which widened the ranking-pressure surface without introducing forbidden-side regressions.
  - A guarded local `torch`/CUDA score-backend smoke is also benchmark-equivalent on this PC, but it is slower on the real current sweep shape at about `0.71s` wall clock with `prepare_compiled_sweep_inputs` about `0.328s`, so GPU remains an explicit opt-in rather than default-on.
  - The latest artifact-resolved best run is now a `var=on` tied winner, and the canonical best objective still has `12` equivalent tied winners including the earlier `var=off` lane; this is currently a stable tie-order detail, not a quality change.
  - The current targeted extraction follow-up also adds a narrow noun-head recovery step for long noun-like gloss phrases, which fixed the `batería` hard fail on the canonical `64`-case benchmark surface without broadening general multiword admission; a later narrow nominal-compound follow-up now does the same kind of focused recovery for `móvil` on the `88`-case suite.
  - A second narrow follow-up now suppresses reverse-miss penalties only for heuristic `leading_alias` and `nominal_head` fragments when they do not already have a direct reverse hit; this lifts `cuadro` from hard FAIL to REVIEW on the canonical surface without changing ordinary comma-fragment behavior.
  - A third narrow follow-up now admits only recurrent exact reverse-attested two-word phrasal-verb candidates, which fixes `sacar` on the canonical surface with top3 `take out, withdraw, draw` without enabling broad multiword verb admission.
  - Later slices are still expected to be:
    - fuller compiled benchmark IR generalization across pairs/packs
    - vectorized CPU backend
    - optional GPU backend only after the sweep has been converted into a genuinely numeric feature-table problem
- Evidence:
  - `docs/developer/rulegen_test_pipeline.md`
  - `docs/developer/rulegen_benchmark_optimization_plan.md`
  - `core/lexishift_core/resources/path_cache.py`
  - `scripts/testing/rulegen_benchmark.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/resources/dict_loaders.py`
  - `core/lexishift_core/rulegen/generation.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/tests/rulegen/test_rulegen_en_es_compiled_resources.py`
- Known gaps:
  - Current full canonical sweep now batch-prepares compiled score inputs and selected-row tables, but case-summary reduction still executes one config at a time; the next major performance frontier is denser config-matrix evaluation over compiled candidate rows and later batch case-summary reduction.
  - The implementation is still pair-heavy in `en-es`, and the newly explicit backend-neutral resource contract is only the first slice, not the final generalized pack abstraction.
  - Current active `en-es` benchmark path still does not have a broadly profitable GPU-shaped workload because it lacks an active embedding/neural scoring backend and is still dominated by preprocessing, selection, and resource work even though the score projection path now has both numeric `numpy` and guarded optional `torch` implementations.

## Rulegen Auto Audit Wrapper

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-11`
- Last verified: `2026-03-11` CLI inspection
- Default behavior:
  - Optional wrapper for touched-pair rulegen audits.
  - Preserves the canonical benchmark -> quality gate -> triage sequence by calling `rulegen_pair_audit_cycle.py`.
  - Adds dated artifacts, `*_latest` alias updates, and run manifests.
- Evidence:
  - `docs/developer/ai_workflow.md`
  - `docs/developer/genai_workflow_architecture.md`
  - `scripts/testing/rulegen_auto_audit.py`
  - `scripts/testing/rulegen_pair_audit_cycle.py`
- Known gaps:
  - Pair inference is heuristic and should not replace explicit `--pairs` when the touched scope is ambiguous.
  - Wrapper coverage is currently specific to the rulegen quality loop and not yet mirrored for SRS quality work.

## SRS Quality Harness

- Status: `implemented`, `verified`, `default-on` = `yes` for SRS scheduler/admission/publication workflow
- Last documented checkpoint: `2026-03-21` FSRS scheduler migration and journey artifact refresh
- Last verified: `2026-03-21` synthetic harness run + summary artifact
- Default behavior:
  - Use the synthetic harness for SRS scheduler, admission refresh, helper publication, set execution, and runtime-serving workflow changes.
  - Review scheduling is now FSRS-based.
  - Current harness covers bootstrap/publication/runtime diagnostics for `en-ja` and `en-de`, plus an `en-ja` feedback-cycle pause/resume scenario.
  - Human-facing summary is available from the JSON artifact.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/testing/srs_quality_harness.py`
  - `scripts/testing/srs_quality_summary.py`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/srs_quality_summary_latest.md`
- Known gaps:
  - Coverage is synthetic and pair-limited; it does not yet grade pedagogical quality or real user data.
  - Current harness intentionally surfaces the due-aware publication mismatch as a warning, not a hard failure.
  - `es-en` / `en-es` SRS quality scenarios are not yet represented in the synthetic harness.

## Kaikki `en-es` Compatibility Dictionary Pipeline

- Status: `implemented`, `verified`; `default-on` = `yes` for forward `wiktionary-es-en.sqlite` when present and for the `en-es` reverse-check path when `wiktionary-en-es.sqlite` is present
- Last documented checkpoint: `2026-03-23` reverse-source evaluation + dedicated EN->ES converter/catalog path
- Last verified: `2026-03-23` targeted converter/helper/adapter tests plus rebuilt Kaikki forward artifact benchmark and Kaikki/Kaikki reverse-enabled `en-es` comparison lane
- Default behavior:
  - App language-pack catalog now includes a pair-specific `wiktionary-es-en` pack sourced from the English-edition Kaikki raw dump.
  - App language-pack catalog also includes a dedicated `wiktionary-en-es` Kaikki pack for EN->ES reverse-check evaluation.
  - Download flow now supports `download + convert + auto-link` for this pack, producing a compatibility SQLite artifact rather than exposing raw JSONL to runtime.
  - `en-es` pair resource resolution now prefers `wiktionary-es-en.sqlite` when present in the language-packs dir.
  - The normalized runtime contract stays aligned with the existing dictionary loader surface: `entries(headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord)`.
  - Converter preserves richer Kaikki metadata in auxiliary SQLite tables for later ranking/synonym work, and the reverse converter additionally preserves translation-box metadata in `translation_meta`.
- Evidence:
  - `docs/language_pairs/kaikki_en_es_integration_plan.md`
  - `docs/language_pairs/language_pack_urls.txt`
  - `docs/language_pairs/lp_resource_requirements.md`
  - `docs/language_pairs/data_source_licensing_and_distribution.md`
  - `apps/gui/src/language_packs_catalog.py`
  - `apps/gui/src/language_packs.py`
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/src/settings_language_packs_path_mixin.py`
  - `core/lexishift_core/resources/kaikki_sqlite.py`
  - `scripts/data/convert_kaikki_glosses_to_sqlite.py`
  - `scripts/data/convert_kaikki_es_en_to_sqlite.py`
  - `scripts/data/convert_kaikki_translations_to_sqlite.py`
  - `scripts/data/convert_kaikki_en_es_to_sqlite.py`
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/pos/normalization.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/tests/resources/test_kaikki_sqlite_conversion.py`
  - `core/tests/helper/test_lp_capabilities.py`
  - `core/tests/pos/test_pos_normalization.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_kaikki_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_kaikki_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_kaikki_bidir_reverse_latest.json`
- Known gaps:
  - `en-es` quality gate remains red in the current workspace even after the Kaikki forward ordering fix; further sense-policy and reverse-check work is still required.
  - The reverse Kaikki source decision is documented, the EN->ES converter exists, and the first reverse-enabled Kaikki/Kaikki lane improved `en-es` top1 to `81.25%`, but the remaining failure classes still need review before promoting the same artifact to the general `es-en` forward path.
  - Synonym extraction from Kaikki metadata is still deferred.
  - Bulk-rules GUI selection is not yet wired to use the new Kaikki pack id.

## Kaikki `en-ja` Rulegen Dictionary Flow

- Status: `implemented`, `verified`; `default-on` = `yes` for helper/runtime rulegen when `wiktionary-ja-en.sqlite` is installed, `no` for seed/bootstrap
- Last documented checkpoint: `2026-04-08` `en-ja` benchmark-suite expansion from a `143`-case core lane to a `161`-case core lane with a more discriminative ranking tranche centered on common but polysemous admissions such as `場合`, `国`, `気`, `話`, `全て`, `県`, `別`, and `他`
- Last verified: `2026-04-08` targeted adapter and benchmark dataset tests plus a local Kaikki-derived `wiktionary-ja-en.sqlite` benchmark/gate/triage refresh over the `161`-case core pair-local suite (`Top1 100.00%`, `Top3 100.00%`, `ForbidAny 0.00%`, triage `0`, pair-local quality floor pass, canonical `96`-config wall clock about `26s`). The canonical matrix still warns for low sensitivity (`56 / 96` configs tied on the top metric vector), but the broader supported-surface sweep is materially healthier than the older small-suite state: `168 / 864` configs are perfect and top-objective share is about `19.4%`, so the pair is clean on the current suite without yet being fully weight-constrained.
- Default behavior:
  - App language-pack catalog now includes a pair-specific `wiktionary-ja-en` pack sourced from the English-edition Kaikki raw dump.
  - Download flow now supports `download + convert + auto-link` for this pack, producing `wiktionary-ja-en.sqlite`.
  - `en-ja` helper/runtime rulegen now resolves a generic translation-dictionary slot and prefers `wiktionary-ja-en.sqlite` when present, with `JMdict_e` as fallback.
  - Bulk-rules GUI selection now exposes and prefers `wiktionary-ja-en` ahead of `jmdict-ja-en` for `en-ja` dictionary-backed generation.
  - Current Kaikki `en-ja` candidate handling now keeps reading-compatible Japanese-script variants, falls back from kanji targets to kana-backed Kaikki headwords when the pair word package provides the reading, joins split ruby segments into full readings for same-surface homographs, strips article/annotation noise from gloss phrases, splits safe comma / semicolon / `or` gloss lists, suppresses structural POS noise such as counter / character side-senses when lexical noun or verb senses exist, recovers a narrow set of safe single-word noun / verb heads from phrase glosses including phrase heads such as `presence of people -> presence`, `spicy hot -> spicy`, and qualifier/admin heads like `country in general -> country` or long prefecture descriptions -> `prefecture`, suppresses bad English expansion noise such as `ifs`, `entirelies`, and `etcs`, and applies narrow family-level competition demotions when event-noun, business, geopolitical, mental-state, communication-noun, totality-noun, occupational-title, spatial-noun, or method-suffix gloss families compete with misleading side meanings on the same target.
  - Default seed/bootstrap behavior remains JMDict-based; `JMdict_e` is still required for empty-store JA bootstrap/filtering.
  - The benchmark/audit path now preloads `en-ja` Kaikki translation gloss records once per sweep, isolates duplicate-surface reading cases during preloaded evaluation, supplements kana/romaji alias headwords only for truly missing targets such as `まだ -> 未だ`, and caches the derived reading/alias indices once per sweep so the canonical `96`-config matrix is back in the ~`20s` range instead of multi-minute regressions.
  - The current pair-local dataset is now split into a `161`-case core canonical lane plus a `2`-case rare-reading edge file. The core lane now includes both admission-derived common vocabulary and a newer discriminative ranking tranche with explicit forbidden-side-sense coverage for polysemous common targets; the edge file keeps intentionally recondite readings such as `大家:たいか` and `大人:たいじん` out of the default benchmark path.
  - The benchmark runner now isolates duplicate-surface `en-ja` cases by reading during preloaded sweeps, so same-surface pairs such as `空(から)` / `空(そら)` and `生(せい)` / `生(なま)` no longer collapse into one cached benchmark target.
  - Real helper bootstrap review now has a pair of local `en-ja` harvest artifacts from `80`-item installed-resource admission passes: the first pre-hardening review exposed high-frequency grammar items such as `ます`, `です`, `だ`, and `た`, plus orthographically bad standalone targets such as `為る` and `侭`; the follow-up post-hardening review confirms that the current JA bootstrap now blocks those auxiliaries/copulas, blocks `侭`, and normalizes `為る` to admitted surface `する`.
  - Default helper bootstrap roots now seed a narrow `stopwords-ja.json` asset alongside the older German asset, and JA bootstrap selection now layers three reviewed policies ahead of admission/publication:
    - exact JA stopword filtering for clear grammar-only spillover such as `ます`, `です`, `だ`, `た`, `ない`, `れる`, and `られる`
    - a tiny reviewed JA lexical exclusion list for bad standalone targets that are not clean stopword cases, currently `侭` / `まま`
    - a tiny reviewed JA orthographic normalization map for bad default source surfaces, currently `為る -> する`, preserving the original source surface in metadata and avoiding any broad kana-preference rule for ordinary kanji vocabulary
  - Tracked follow-up:
    - keep the current JA bootstrap hardening intentionally narrow until additional candidates are reviewed; the next explicit review bucket includes broader orthographic or ultra-abstract surfaces such as bare `為` and `訳`
    - if a trustworthy external compiled/preferred-orthography source for Japanese becomes available, evaluate it as a candidate replacement or supplement for the current tiny reviewed surface-normalization map rather than expanding toward a broad kana-preference heuristic
- Evidence:
  - `docs/language_pairs/language_pack_urls.txt`
  - `docs/language_pairs/lp_data_inventory_matrix.md`
  - `docs/language_pairs/lp_resource_requirements.md`
  - `docs/language_pairs/data_source_licensing_and_distribution.md`
  - `apps/gui/src/language_packs_catalog.py`
  - `apps/gui/src/language_packs.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/pairs/en_ja.py`
  - `scripts/data/convert_kaikki_glosses_to_sqlite.py`
  - `scripts/data/convert_kaikki_ja_en_to_sqlite.py`
  - `core/tests/dev/test_gui_import_contract.py`
  - `core/tests/pos/test_pos_normalization.py`
  - `core/tests/resources/test_dict_loaders_freedict_pos.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_en_ja_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_ja_latest.json`
  - `docs/test_outputs/experiments/en_ja_admission_harvest_review_20260408.json`
  - `docs/test_outputs/experiments/en_ja_admission_harvest_review_20260408.md`
  - `docs/test_outputs/experiments/en_ja_admission_harvest_postpolicy_review_20260408.json`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/srs_quality_summary_latest.md`
  - `core/tests/srs/test_srs_seed.py`
  - `core/tests/helper/test_helper_engine.py`
- Known gaps:
  - Seed/bootstrap still depends on `JMdict_e`; this is intentionally a mixed JMDict-seed plus Kaikki-rulegen rollout rather than a full source replacement.
  - Single-pair `en-ja` audits now downgrade missing required-pair coverage to advisory warnings, but the shared hard-gated policy set still only requires `en-es`.
  - The `en-ja` benchmark path is now fast enough for canonical sweeps through one-time preload, but it still uses the generic live adapter path rather than a compiled pair backend.
  - The current Kaikki `en-ja` ranking lift depends on narrow pair-specific gloss heuristics rather than a generalized multilingual Kaikki policy layer.
  - The canonical `121`-case core suite is clean again, but the broader `864`-config supported-surface sweep is still underconstrained: `168 / 864` configs are perfect, `semantic_demotion_scale=1.0` remains mandatory, and the weight space still needs more benchmark expansion to sharpen ordinary knob selection.
  - JA bootstrap hardening is intentionally narrow rather than comprehensive. It now blocks the reviewed auxiliary/copula and lexical-noise cases above, but broader grammar-heavy or ultra-abstract targets such as bare `為` and `訳` can still appear in admission reviews and will need separate policy decisions if we want to tighten the bootstrap frontier further.

## SRS Journey E2E Harness

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-03-21` FSRS-backed journey artifacts for deterministic, synthetic-real, and installed-resource `en-ja` + `en-es` lanes
- Last verified: `2026-03-21` deterministic `en-ja` + `en-es` core and edge journey harness runs, synthetic-resource real-publication lanes, installed-resource `en-ja` + `en-es` runs, Markdown summaries, and interactive HTML review artifacts
- Default behavior:
  - Deterministic `en-ja` and `en-es` core and edge journey lanes plus matching real-publication lanes are available as analysis-first SRS E2E harnesses, but they are not yet part of the required default SRS workflow loop in `AGENTS.md`.
  - The core lane captures item-level admitted `S`, due `D`, and published `P` sets across bootstrap, refresh, and fade/stick phases.
  - Journey JSON now includes bootstrap candidate audits, refresh candidate ranking audits, and richer per-item state fields such as confidence, due rank, and lexical previews for retroactive pedagogical review.
  - The edge lane captures duplicate-feedback and exposure-only behavior with the same item-level reporting contract.
  - The real-publication lane keeps deterministic clocks/resources, uses the actual seed-builder plus helper/rulegen publication path, and now holds complete due publication for the current `en-ja` and `en-es` scenarios.
  - Separate installed-resource review lanes now stage the user's local frequency/dictionary packs into an isolated temp helper root, assign cohorts from actual admitted lemmas, and surface real-data pedagogical flow without mutating the live helper state.
  - Interactive HTML playback artifacts now provide step-by-step review with phase controls, admission rationale tables, and a sticky profile-state panel.
  - Current contract mode defaults to observation: publication broader than the due subset is surfaced as a warning rather than a hard failure.
- Evidence:
  - `docs/srs/srs_journey_harness_workstream.md`
  - `scripts/testing/srs_journey_harness.py`
  - `scripts/testing/srs_journey_summary.py`
  - `scripts/testing/srs_journey_html.py`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.html`
- Known gaps:
  - `en-de` extension is still pending.
  - The deterministic and synthetic-resource real-publication lanes are still useful regression surfaces, but installed-resource review currently depends on local data-pack availability and is not yet part of the default required workflow loop.
  - The due-aware publication contract remains unresolved; the harness currently records the mismatch instead of enforcing it.

## Development Workflow Safeties

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-17` canonical-doc metadata enforcement + changed-scope doc-reference expansion + health warning-delta gating
- Last verified: `2026-03-21` local `check:state`, `check:report`, `check:summary`, `check:style:report`, `check:style:summary`, and `health:project:report`
- Default behavior:
  - `npm --prefix scripts run check` is the stable non-mutating repo safety command.
  - `npm --prefix scripts run check` now includes the strict Windows parity audit, so parity regressions fail the default local safety gate and pre-push hook.
  - `npm --prefix scripts run check` now includes strict repo-wide Ruff lint/format checks because the repo-wide style baseline is clean.
  - `npm --prefix scripts run check:changed` is the preferred branch-scope workflow command.
  - `npm --prefix scripts run check:changed` now records both total changed files and substantive changed files, and uses the substantive set when inferring heavier quality loops such as rulegen audit; Python uses AST comparison, JSON uses parsed equality, and Markdown/text uses whitespace-normalized comparison.
  - `npm --prefix scripts run check:docs` now validates top metadata (`Status`, `Role`, `Last updated`) plus referenced repo paths for canonical routing/policy docs.
  - `npm --prefix scripts run check:changed` now reruns the canonical doc integrity audit when canonical docs change or when referenced source files under `apps/`, `core/`, `scripts/`, `.github/`, or canonical root files change materially.
  - `npm --prefix scripts run health:project:changed` now blocks new/regressed warning debt alongside new/regressed violation debt.
  - `npm --prefix scripts run build` is the local build smoke for maintained build surfaces.
  - `npm --prefix scripts run build:report` is the full build contract and now verifies expected BetterDiscord / GUI artifacts in the report payload.
  - Hosted macOS `build:report` keeps the full GUI bundle validation path; hosted Windows `build:report` now uses the full GUI build plus artifact verification, while the strict Windows parity audit remains the dedicated Windows-specific validation gate.
  - Hosted CI now runs both the full macOS `build:report` path and the explicit Ubuntu `build:ci:report` partial path.
  - Python-backed npm workflow commands now resolve their interpreter through `scripts/dev/run_python.js` so `check` / `build` / audit entrypoints remain usable on Windows hosts.
  - `npm --prefix scripts run build:ci` / `build:ci:report` keep the same build workflow on unsupported hosts while recording explicit GUI-validation skips.
  - `npm --prefix scripts run check:style` is the standalone repo-wide style loop.
  - `npm --prefix scripts run check:style:report` and `check:style:summary` publish the current repo-wide Ruff style state as JSON and Markdown artifacts.
  - `npm --prefix scripts run check:state` audits the feature-state ledger for required fields, dated checkpoints, evidence paths, and transition-aware updates relative to `HEAD`.
  - `npm --prefix scripts run check:report`, `check:changed:report`, and `build:report` emit machine-readable JSON artifacts for automation.
  - Failed `check` / `build` commands now record stdout/stderr tail lines and missing-artifact details in the JSON reports so hosted CI failures remain inspectable from artifacts and summaries.
  - `npm --prefix scripts run check:summary` renders a Markdown summary from the latest workflow reports and now surfaces first-failure detail tails when present.
  - Hosted CI now lets report-producing steps continue long enough to upload summaries/artifacts, then fails the job via explicit JSON-based gate steps.
  - Hosted Ubuntu repo-safety now uses `npm --prefix scripts run check:report:ci`, which skips the redundant Windows parity audit; dedicated Windows parity/build jobs remain responsible for that surface.
  - Hosted repo-safety still renders the latest rulegen benchmark/gate/triage summaries, but the known-red rulegen artifact no longer blocks the generic repo-safety job.
  - `npm --prefix scripts run hooks:install` installs both `pre-commit` and `pre-push`; the pre-push hook mirrors `npm --prefix scripts run check`.
  - `pre-commit` now runs repo-wide Ruff lint and Ruff format before commit, while `pre-push` keeps the full repo-safety gate.
- Evidence:
  - `scripts/dev/feature_state_audit.py`
  - `scripts/dev/dev_workflow_check.py`
  - `scripts/dev/dev_workflow_changed_check.py`
  - `scripts/dev/dev_workflow_build.py`
  - `scripts/dev/dev_workflow_style_check.py`
  - `scripts/dev/dev_workflow_style_summary.py`
  - `scripts/dev/check_doc_references.py`
  - `scripts/dev/check_project_health.js`
  - `scripts/dev/project_health_rules.js`
  - `scripts/dev/ci_report_gate.py`
  - `scripts/dev/run_python.js`
  - `apps/betterdiscord-plugin/build_plugin.js`
  - `.pre-commit-config.yaml`
  - `.github/workflows/ci.yml`
  - `requirements-build.txt`
  - `scripts/package.json`
  - `docs/test_outputs/dev_workflow/feature_state_audit_latest.json`
  - `docs/test_outputs/dev_workflow/doc_references_latest.json`
  - `docs/test_outputs/dev_workflow/check_latest.json`
  - `docs/test_outputs/dev_workflow/check_changed_latest.json`
  - `docs/test_outputs/dev_workflow/build_latest.json`
  - `docs/test_outputs/dev_workflow/build_ci_latest.json`
  - `docs/test_outputs/dev_workflow/summary_latest.md`
  - `docs/test_outputs/dev_workflow/style_latest.json`
  - `docs/test_outputs/dev_workflow/style_summary_latest.md`
  - `docs/test_outputs/project_health/project_health_latest.json`
  - `docs/developer/documentation_governance.md`
  - `docs/developer/project_health_gate_structure.md`
  - `docs/developer/local_setup.md`
  - `docs/developer/build_and_release.md`
- Known gaps:
  - GUI packaging makes `build` materially slower than `check`.
  - Hosted build coverage is now macOS full, Windows full-build plus artifact verification with a separate strict parity gate, and Ubuntu CI-safe partial; Ubuntu remains the explicit non-GUI proof lane rather than full desktop packaging.
  - Canonical-doc metadata enforcement is currently limited to the canonical routing/policy layer, not every maintained doc in the repo.
  - Pre-commit and pre-push coverage are optional until contributors run `npm --prefix scripts run hooks:install`.
  - Branch-scope changed reports intentionally surface the whole branch delta, so long-running branches can report unrelated debt unless contributors use `check:changed:local` or `check:changed:staged`.

## GitHub Pages Docs Deployment

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-13`
- Last verified: `2026-03-13` local `bundle exec jekyll build --trace` + hosted `pages` / `pages-build-deployment` success on `302bba5`
- Default behavior:
  - Repo-owned Pages workflow now lives in `.github/workflows/pages.yml`.
  - Pull requests touching `docs/**` run a build-only Pages validation job.
  - Pushes to `main` touching `docs/**` build and deploy the site through GitHub Actions.
  - Local parity command is `cd docs && bundle exec jekyll build --trace`.
- Evidence:
  - `.github/workflows/pages.yml`
  - `docs/runbooks/github_pages_setup.md`
  - `docs/Gemfile`
  - `docs/Gemfile.lock`
  - `docs/_config.yml`
  - `docs/developer/local_setup.md`
  - `docs/test_outputs/dev_workflow/github_pages_workflow_verification_latest.md`
- Known gaps:
  - Current workflow validates Jekyll build/deploy only; it does not yet run link checking or browser-level UI smoke tests for docs JavaScript.

## Windows GUI Parity Audit

- Status: `implemented`, `verified`, `default-on`
- Last documented checkpoint: `2026-03-12`
- Last verified: `2026-03-12` parity audit rerun + repo-safety integration + changed-scope/CI workflow wiring review
- Default behavior:
  - `npm --prefix scripts run check` now runs the strict Windows parity audit as part of repo safety and pre-push.
  - `npm --prefix scripts run check:windows:parity` writes a machine-readable parity audit of Windows GUI/helper/build parity.
  - `npm --prefix scripts run check:windows:parity:summary` renders the current parity state into Markdown for human handoff.
  - Hosted CI now has a Windows full-build lane plus parity audit artifacts.
  - `npm --prefix scripts run check:changed` now runs the Windows parity audit automatically when parity-related files change.
  - Windows CI now uses the strict parity audit command so parity regressions fail the hosted workflow.
- Evidence:
  - `docs/developer/windows_gui_parity_workstream.md`
  - `scripts/dev/windows_parity_audit.py`
  - `scripts/dev/windows_parity_summary.py`
  - `apps/gui/src/frozen_layout.py`
  - `apps/gui/src/helper_installer.py`
  - `apps/gui/src/helper_ui.py`
  - `apps/gui/src/helper_tray.py`
  - `docs/architecture/native_messaging_design.md`
  - `docs/test_outputs/dev_workflow/windows_parity_latest.json`
  - `docs/test_outputs/dev_workflow/windows_parity_summary_latest.md`
  - `.github/workflows/ci.yml`
- Known gaps:
  - The parity audit is now a required workflow gate, but it is still not a complete release certification on its own.
  - Current browser coverage is limited to the supported GUI helper environments (`chrome`, `chromium`, `brave`).

## Feature-State Evidence Audit

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-12`
- Last verified: `2026-03-12` local audit run + repo safety/base-ref integration
- Default behavior:
  - `scripts/dev/feature_state_audit.py` validates that feature entries include status, dated checkpoints, default behavior bullets, evidence bullets, and known gaps.
  - Evidence paths in `docs/developer/feature_state_matrix.md` must resolve on disk.
  - Repo safety now runs this audit directly against `HEAD`, pre-commit runs it when the feature ledger changes, and changed-scope workflow checks run it against the branch base when the ledger is touched.
- Evidence:
  - `scripts/dev/feature_state_audit.py`
  - `core/tests/dev/test_feature_state_audit.py`
  - `scripts/dev/dev_workflow_check.py`
  - `.pre-commit-config.yaml`
  - `docs/test_outputs/dev_workflow/feature_state_audit_latest.json`
- Known gaps:
  - The audit enforces structure and evidence existence, not semantic correctness of every status claim.
  - It does not yet require every status transition to update its verification date in the same commit.

## Generic Gloss Demotion

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-02-27`
- Last verified: `2026-02-28` benchmark artifact review; `2026-03-21` code inspection after `en_ja` adapter/module rename
- Default behavior:
  - Active for current rulegen pairs through pair-specific demotion lists.
  - Tuned via `semantic_demotion_scale`.
- Evidence:
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/rulegen/rulegen_congruity_implementation_plan.md`
  - `core/lexishift_core/rulegen/semantic_demotion.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/pairs/en_ja.py`
- Known gaps:
  - Heuristic demotion is conservative and does not replace sense-level disambiguation.
  - Current `en-es:madre` failure shows generic demotion alone is not sufficient.

## Reverse-Check Scoring

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-26` exact-hit ambiguity + exact-hit specificity reverse signals with benchmark/probe harness exposure
- Last verified: `2026-03-26` targeted ranking/tuning/helper/harness tests, canonical `en-es` benchmark/gate/triage rerun over the expanded 48-config reverse sweep, reverse run-matrix refresh, and focused `cuadro` probe
- Default behavior:
  - Configurable and pair-aware for `en-es` and `es-en`.
  - Not yet promoted to default production tuning.
  - Reverse-check-specific evaluation now has a named `en-es` lane via `npm --prefix scripts run quality:rulegen:reverse:en-es`.
  - Parameter-set comparison is now tracked in `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`.
  - Reverse scoring now also supports:
    - an exact-hit ambiguity penalty keyed off `reverse_check_total`
    - an additive exact-hit specificity bonus keyed off `reverse_check_total`
  - both signals are harness-exposed, but both are still off in the current canonical best run.
- Evidence:
  - `docs/rulegen/reverse_check_scoring_phase1.md`
  - `docs/rulegen/reverse_check_rollout_matrix.md`
  - `docs/rulegen/reverse_check_en_es_case_review_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`
  - `core/lexishift_core/rulegen/ranking.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/tuning.py`
  - `scripts/testing/rulegen_benchmark.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_latest.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.md`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_off_latest.json`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_on_latest.json`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
  - `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
- Known gaps:
  - Only `en-es` and `es-en` are wired; `en-de` and `en-ja` have no reverse-check implementation.
  - No committed `es-en` benchmark/gate/triage artifact yet proves rollout maturity.
  - The canonical benchmark loop now sweeps both `rev=off` and `rev=on`, but `en-es` still remains red on top-1 accuracy and average-rule volume even after the latest extraction and phrase-policy follow-ups kept the best `rev=on` lane at the top.
  - The current `en-es` reverse-enabled best run now reaches `Top1 92.19%`, `Top3 100.00%`, and `ForbidAny 0.00%`; remaining work is now about lexical preference and ranking rather than reverse plumbing or slang leakage.
  - The new exact-hit ambiguity penalty and exact-hit specificity bonus are both implemented and harness-exposed, but neither beat the existing best lane yet; current `cuadro` behavior is still more sensitive to miss/far-penalty tradeoffs and score clamping than to these exact-hit refinements alone.
  - `cuadro` still exposes a non-separable failure class for reverse evidence alone, but the earlier `sacar` phrase-policy gap is now covered by a narrow recurrent exact reverse-attested phrasal-verb rule, and the `acabar` / `coger` vulgar-leakage issue is now covered by a narrow clean-competition suppression rule for explicit vulgar senses.
  - Current rollout is no longer scoring-only: it now includes a narrow strict candidate-blocking rule for explicit vulgar usage when clean competition exists, while broader blocking remains off.

## Kaikki Provenance / Competition Scoring

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-27` provenance scoring with second benchmark-expansion pass and live Kaikki demotion now winning
- Last verified: `2026-03-27` targeted `en-es` provenance/adapter/benchmark tests, canonical `en-es` benchmark/gate/triage rerun over the expanded 57-case / 144-config sweep, and probe-path verification
- Default behavior:
  - `en-es` Kaikki candidates now support a sweepable additive provenance penalty:
    - `late_sense_clean_earlier_competition_penalty`
  - the signal is off unless the selected config sets a nonzero penalty
  - the current canonical best run now selects:
    - `kprov=0.10`
  - the signal is powered only by existing metadata already carried on candidates:
    - `target_provenance`
    - `gloss_provenance`
    - `sense_provenance`
    - `kaikki_policy_shadow`
  - benchmark and probe seams both expose it:
    - benchmark label: `kprov`
    - probe flag: `--kaikki-policy-late-sense-penalty`
- Evidence:
  - `docs/language_pairs/kaikki_en_es_integration_plan.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_latest.json`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/en_es_support.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_probe_words.py`
  - `core/tests/rulegen/test_rulegen_en_es_kaikki_provenance.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `core/tests/dev/test_rulegen_benchmark.py`
- Known gaps:
  - only the smallest provenance signal is live so far; richer provenance/competition features are still pending
  - the current signal is now selected together with live Kaikki demotion, but it still does not solve `cuadro` or the remaining lexical-preference review cases
  - `en-de`, `en-ja`, and `es-en` do not yet have analogous provenance-scoring work
  - per-family Kaikki demotion strengths remain available, but the next nearby targeted rulegen candidate is lexical-preference / ranking work for `cuadro`, `red`, `derecho`, `cuenta`, and `señal`, not another short-phrase or slang-policy change

## Trait-Conditioned Rulegen Profiles

- Status: `scaffolded`; runtime routing not implemented or verified
- Last documented checkpoint: `2026-03-29` frozen profile-bank rerun on the `88`-case `en-es` suite after the fifth dataset-expansion tranche
- Last verified: `2026-03-29` canonical `en-es` benchmark refresh plus frozen profile-bank analysis on the `88`-case suite
- Default behavior:
  - No runtime profile routing exists yet.
  - Current rulegen still uses one selected configuration per run rather than choosing profiles from runtime-computable target traits.
  - The intended future direction is to route among a small bank of named profiles using a shared feature extractor and benchmark-backed trait analysis.
  - Benchmark case payloads now emit a hardened analysis-only `trait_summary` seam in the latest `en-es` artifacts.
  - The current payload is explicitly split into:
    - `router_input`
    - `result_shape`
    - `benchmark_only`
  - Current concrete offline profile candidates now exist on `en-es`:
    - canonical recall-oriented baseline
    - admission-tight precision profile
    - combined balanced profile
    - family-followup high-objective profile
  - Current evidence says those profiles materially change precision/recall shape and rule volume, but they still do not change the remaining review-boundary winners consistently enough to justify runtime routing.
  - The first frozen profile-bank comparison on the `71`-case suite found no top-1 winner differences, the rerun on the `77`-case suite found the first split, the `83`-case rerun kept that same pattern, and the current `94`-case rerun now finds:
    - `1` top-1 winner difference across the current four-profile bank
    - `0` cases with top-3 coverage differences
    - the current top-1-sensitive case is `móvil`, where canonical keeps `mobile phone` while the tighter profiles regress to bare `mobile`
  - The first post-`móvil` trait-region aggregation on top of that frozen bank found:
    - `admission-tight` and `family-followup` now tie as the best objective profiles across most regions
    - canonical still carries the only extra top-1 win because of `móvil`
    - those region-level wins therefore still mostly affect rule volume / breadth rather than broader top-1 identity changes
- Evidence:
  - `docs/rulegen/trait_conditioned_rulegen_profiles.md`
  - `docs/developer/rulegen_en_es_broad_sweep_runbook.md`
  - `docs/test_outputs/experiments/rulegen_en_es_profile_bank_analysis_20260329_100cases.json`
  - `docs/test_outputs/experiments/rulegen_en_es_profile_bank_comparison_20260329_100cases.md`
  - `docs/test_outputs/experiments/rulegen_en_es_dataset_expansion_tranche5_20260329.md`
  - `docs/test_outputs/experiments/rulegen_en_es_post_vulgarfix_frontier_summary_20260328.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/language_pairs/kaikki_en_es_integration_plan.md`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_benchmark_presets.py`
  - `scripts/testing/rulegen_benchmark_bundle.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/kaikki_views.py`
  - `core/lexishift_core/rulegen/ranking.py`
- Known gaps:
  - There is no runtime router yet; the new trait extractor contract is still only consumed by benchmark artifacts.
  - The current `trait_summary` payload is ready for offline profile-bank comparison, but not yet used by a live runtime decision path.
  - No profile bank or interpretable router is implemented.
  - The benchmark suite is broader now, but the next required step is still broader suite/profile evidence plus targeted lexical work rather than shipping any routing behavior.
  - The next recommended sequence is:
    - keep the `88`-case suite as the active profile-analysis baseline
    - aggregate frozen-bank results by `router_input` trait regions and inspect the `trama` split plus the new `navegador` top-3 sensitivity
    - only then revisit another suite-expansion tranche, embeddings, or other larger new signal families in the profile-analysis loop
  - Learner-stage-aware routing is only conceptual at this point and must stay separate from lexical trait inference.

## POS Normalization

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-02-23` phase-6 artifacts; `2026-03-11` code inspection
- Default behavior:
  - Seed extraction and word-package metadata carry raw and canonical POS.
  - Rulegen pair modules can consume normalized POS metadata.
- Evidence:
  - `docs/rulegen/pos_normalization_workstream.md`
  - `core/lexishift_core/pos/normalization.py`
  - `core/lexishift_core/srs/seed.py`
  - `core/lexishift_core/rulegen/pairs/pos_utils.py`
  - `docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json`
  - `docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json`
- Known gaps:
  - Unknown POS inventory remains for `freq-de-default.sqlite` and `freq-ja-bccwj.sqlite`.
  - POS metadata is stronger than current downstream decision usage for both rulegen ranking and SRS growth.

## SRS Set Planner Strategies

- Status:
  - `frequency_bootstrap`: `implemented`, `default-on`, `verified`
  - `profile_bootstrap`: `implemented`, `default-on`, `verified`
  - `profile_growth`: `implemented`, `verified`
  - `adaptive_refresh`: `scaffolded`
- Last documented checkpoint: `2026-04-15`
- Last verified: `2026-04-15` targeted profile-bootstrap/helper/audit tests, synthetic SRS quality harness, refreshed preference-sanity artifact, and refreshed live frontier topic coverage audit
- Default behavior:
  - Plain `frequency_bootstrap` remains the neutral executable baseline.
  - `profile_bootstrap` is now executable and default-on for the extension/options initialize flow that already requests it.
  - Current `profile_bootstrap` behavior keeps seed generation and hard pair-local gating neutral, normalizes raw planner context into explicit topic weights plus effective canonical topic-family matching weights, resolves `proficiency_estimate`, `challenge_target`, and `challenge_spread`, then reranks the admitted pool using those signals.
  - GUI frequency-pack builds now enrich `freq-ja-bccwj` and `freq-es-cde` with companion Kaikki/Wiktionary topic metadata when the matching local language-pack SQLite exists, storing the resulting topic hints in `frequency.sense_topics` for downstream admission matching.
  - Topic-affinity matching now expands conservative canonical topic families in the scorer and diagnostics, so source tags such as `pets`, `board-games`, `business`, and `streaming` can contribute to user-facing interests such as `animals`, `games`, `finance`, and `livestream` without replacing the neutral coverage baseline.
  - Topic-affinity now also applies a bounded topic-specificity dampener so mixed-domain/polysemous candidates keep some lift but no longer score like clean topical hits. Current diagnostics expose the effective specificity factor plus support-count and hint-count fields.
  - `profile_bootstrap` now also reports active-topic neutral-frontier support diagnostics for the current profile, including per-topic candidate count, support mass, example lemmas, and whether the topic currently has enough labeled support to justify scarcity calibration.
  - `profile_bootstrap_v3` now adds a bounded PoC `scarcity_bonus` scorer lane for sparse-but-real topical support. The bonus is gated by active-topic frontier support, remains secondary to the neutral coverage floor, and is explicitly documented as provisional tuning rather than final policy.
  - Bootstrap and refresh admission now use an explicit weighted-without-replacement selector over the scored frontier rather than a deterministic top-`N` cutoff. The scorer remains deterministic; the admission selector is the stochastic layer.
  - Options now also expose a non-mutating admission preview path that runs the same planner/bootstrap logic, keeps deterministic rerank diagnostics, and reuses the same weighted selector as live bootstrap before any `S` mutation or rulegen publish occurs.
  - Options now expose first-step editable admission signals for the selected profile/pair: `interests`, `proficiency.estimated_value`, and `difficulty_preferences.target_challenge_center`.
  - Those option values are stored under `srsProfiles.<profile_id>.srsSignalsByPair.<pair>` and blank values are pruned rather than persisted as empty placeholder objects.
  - Bootstrap diagnostics now expose the selection strategy, selector version, normalized context summary, policy summary, canonical topic-family matching sources, and per-item rerank explanations for the admitted preview.
  - Pair-local active inventory membership is now persisted separately in `srs_inventory.json`, and sampled rulegen/runtime publication read that manifest when present instead of implicitly treating every pair item in `srs_store.json` as active inventory.
  - `profile_growth` is now executable for the manual `objective="rebalance"` path only. It preserves protected learned items, can park low-commitment active items without deleting their history, can reactivate retained items, can admit new seed items when needed, and republishes pair-local rulegen from the resulting active inventory.
  - Options now expose preview-first manual rebalance controls for the selected pair: `Preview rebalance to current preferences` and `Apply rebalance…`.
- Evidence:
  - `docs/srs/srs_set_planning_technical.md`
  - `docs/srs/srs_profile_schema.md`
  - `docs/srs/srs_preference_update_and_rebalance_policy.md`
  - `docs/srs/srs_preference_signal_admission_design.md`
  - `docs/srs/srs_preference_signal_admission_v1_contract.md`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/srs/profile_bootstrap.py`
  - `core/lexishift_core/srs/selector.py`
  - `core/lexishift_core/frequency/sqlite.py`
  - `core/lexishift_core/srs/inventory.py`
  - `core/lexishift_core/srs/rebalance.py`
  - `core/lexishift_core/helper/rulegen.py`
  - `core/lexishift_core/helper/use_cases/admission_preview.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
  - `core/lexishift_core/helper/use_cases/rebalance_set.py`
  - `core/lexishift_core/helper/use_cases/refresh_set.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `scripts/helper/lexishift_native_host.py`
  - `scripts/helper/lexishift_helper.py`
  - `scripts/data/enrich_frequency_topics_from_sqlite.py`
  - `scripts/testing/srs_admission_preference_sanity.py`
  - `scripts/testing/srs_frequency_topic_coverage.py`
  - `apps/chrome-extension/options.html`
  - `apps/chrome-extension/options/controllers/srs/actions/admission_preview_workflow.js`
  - `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
  - `apps/chrome-extension/options/controllers/srs/actions/admission_preview_formatter.js`
  - `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
  - `apps/chrome-extension/options/core/settings/signals_methods.js`
  - `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
  - `apps/chrome-extension/options/core/helper/srs_set_methods.js`
  - `apps/gui/src/language_packs.py`
  - `apps/gui/src/language_packs_catalog.py`
  - `core/tests/srs/test_srs_inventory.py`
  - `core/tests/srs/test_profile_bootstrap.py`
  - `core/tests/srs/test_selector.py`
  - `core/tests/srs/test_srs_rebalance.py`
  - `core/tests/srs/test_srs_set_planner.py`
  - `core/tests/frequency/test_frequency_sqlite_converter.py`
  - `core/tests/dev/test_gui_import_contract.py`
  - `core/tests/helper/test_helper_rulegen.py`
  - `core/tests/helper/test_helper_engine.py`
  - `core/tests/dev/test_srs_admission_preference_sanity.py`
  - `core/tests/dev/test_srs_frequency_topic_coverage.py`
  - `docs/test_outputs/srs_admission_preference_sanity_latest.json`
  - `docs/test_outputs/srs_admission_interest_review_en_es_latest.md`
  - `docs/test_outputs/srs_admission_interest_review_en_es_metrics_latest.md`
  - `docs/test_outputs/srs_frequency_topic_coverage_latest.json`
  - `docs/test_outputs/srs_quality_latest.json`
- Known gaps:
  - `profile_growth` is only implemented for manual `objective="rebalance"`; continuous growth admission is still not executable.
  - Rebalance is intentionally manual and pair-local; there is still no automatic inventory mutation on every preference edit.
  - Topic-affinity lift is now backed by Kaikki-derived frequency-pack topic enrichment for local `ja` and `es` packs when companion SQLite sources exist, and the live audit now reports canonical topic coverage inside the top bootstrap frontier. Current `en-es` Monte Carlo review confirms the architecture and stochastic selector are working, but the final admission lift is still modest: `sports`, `music`, and `games` move in the right direction, `finance` is still noisy, and `animals` is still too sparse. Coefficient tuning remains explicit follow-up work rather than a blocker for the current merge checkpoint; `freq-en-coca` and broader classifier-derived topic coverage remain the main gaps.
  - Current challenge/proficiency fitting still uses a coarse bootstrap difficulty proxy derived from neutral admission weight, not a richer curriculum model.
  - Rebalance currently uses the same normalized preference signals as `profile_bootstrap`; feedback-window aggregation and empirical trend routing remain future work under `adaptive_refresh`.
  - Pair policy defaults are currently near-identical across active pairs.

## Due-Aware SRS Serving

- Status: `planned`; end-to-end implementation not verified
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Docs define due-set-driven serving.
  - Current helper publication and extension gate behavior appear to operate on admitted `S` items rather than a separately published due subset.
- Evidence:
  - `docs/srs/srs_hybrid_model_technical.md`
  - `core/lexishift_core/srs/scheduler.py`
  - `core/lexishift_core/helper/rulegen.py`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
- Known gaps:
  - No explicit due-state artifact or due-aware helper ruleset publish path is currently tracked here.
  - This item should remain `planned` until helper publication and runtime gating are verified against due-state behavior.

## Extension-Side Confidence Gating For Helper Rules

- Status: `planned` / `unverified`
- Last documented checkpoint: `2026-02-27` rulegen docs review
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Docs describe confidence-based runtime filtering.
  - Extension runtime path inspected on `2026-03-11` did not confirm a live helper-rule confidence filter.
- Evidence:
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/reference/glossary.md`
  - `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
- Known gaps:
  - Treat this as unresolved until a code path is identified and tested.
  - Do not mark confidence gating as shipped based on docs alone.

## GenAI Workflow Architecture

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-11`
- Last verified: `2026-03-12`
- Default behavior:
  - Use the rulegen quality loop already defined in `AGENTS.md` and `docs/developer/ai_workflow.md`.
  - Use `docs/developer/genai_workflow_architecture.md` for agent roles, instance splitting, and harness policy.
  - Use `scripts/testing/rulegen_auto_audit.py` for dated plus latest rulegen audit runs when a change-aware wrapper is helpful.
- Evidence:
  - `docs/developer/genai_workflow_architecture.md`
  - `scripts/testing/rulegen_auto_audit.py`
  - `scripts/testing/rulegen_pair_audit_cycle.py`
- Known gaps:
  - Feature-state discipline is stronger now, but status transitions are not yet enforced against commit-scoped artifact diffs.
  - Hosted CI still uses an explicit CI-safe build mode rather than full macOS GUI validation.

## Current State Mismatches To Preserve Explicitly

These are not accidental wording issues. Keep them explicit until code and docs converge.

1. Reverse-check is implemented but not yet default-on.
2. SRS docs define due-aware serving, but current end-to-end publish/gate behavior is not yet verified as due-aware.
3. Docs mention runtime confidence filtering, but extension-side helper-rule confidence gating is not yet verified in code.
