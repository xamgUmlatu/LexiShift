# Feature State Matrix

Status: active ledger
Role: Canonical current
Last updated: 2026-07-02
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
- Last documented checkpoint: `2026-06-09` dedicated advisory latest lanes now include `en-ja`; the quality gate now scopes saturation checks to the requested pair and reports a non-strict one-run saturation warning for fixed reference lanes instead of a hard saturation failure.
- Last verified: `2026-06-09` dedicated `npm --prefix scripts run quality:rulegen:en-ja` refresh, en-ja summary rendering, LP profile/conformance checks, and focused saturation validator coverage; earlier `2026-04-04` focused dataset-loader/gate/bundle tests plus local `en-de` benchmark/gate/triage refresh on the directory-backed dataset
- Default behavior:
  - Required for rulegen scoring, candidate filtering, POS normalization, and LP tuning changes.
  - Canonical loop remains benchmark -> quality gate -> triage.
  - Benchmark case source-of-truth is now the LP-specific directory `docs/test_inputs/rulegen_benchmark_cases/`; benchmark tooling merges those files on load.
  - Latest rulegen artifacts now have human-facing Markdown summaries for benchmark, gate, and triage surfaces.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `docs/developer/rulegen_test_pipeline.md`
  - `scripts/package.json`
  - `scripts/testing/rulegen_benchmark.py`
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
  - `en-de` now has a named advisory latest lane, but it is still separate from the canonical strict `en-es` lane and not yet part of `required_benchmark_pairs`.
  - Cross-machine benchmark artifacts can preserve source-machine absolute dataset paths; the gate now falls back to the repo-local dataset copy when the original path is unavailable.
  - Artifact history and pair inference still depend on wrapper usage rather than a mandatory repo-wide gate.
  - Benchmark artifacts now mirror resolved resources under each pair as well as in the top-level `resources` block, they now carry SHA-256 resource checksums, they now record the effective per-target `word_package` snapshot used by the run, the benchmark CLI now supports named preset methodologies from `docs/test_inputs/rulegen_benchmark_presets.json`, and portable bundle export/replay now packages the exact dataset/resources/snapshots for cross-machine reruns; the remaining ergonomic gap is optional single-file archive/import support.
  - Fixed one-config advisory lanes can now pass quality-floor checks while still warning that sweep saturation cannot be evaluated; use broad presets when parameter-sensitivity evidence matters.

## Rulegen Benchmark Optimization Architecture

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-03-28` the compiled `en-es` sweep path now includes `numpy` config-matrix score projection, a guarded optional `torch` CUDA score backend, compact selected-row preparation, backend-neutral preload caches, and a separate black-box pipeline contract doc for the full benchmark/render/gate/triage loop
- Last verified: `2026-03-28` focused unit coverage, latest warm-cache canonical `en-es` sweep smoke, guarded `torch`/CUDA equivalence smoke, and pipeline/state sync
- Default behavior:
  - Active direction remains a non-throwaway benchmark acceleration program that keeps the current canonical preset methodology while moving the implementation toward a `compile -> sweep -> materialize` architecture, a backend-neutral pair-resource contract, and later trait-aware profile analysis on top of the same benchmark substrate.
  - Already landed slices include timing/profiling instrumentation, pair-context caching, compute/materialization split, compiled `en-es` candidate/case/result tables, deferred case-payload materialization, a direct compiled non-variant `en-es` sweep path that can bypass adapter-generated `VocabRule`s, a compiled benchmark-only variant-row path so the canonical `var=on` half of the `en-es` matrix no longer has to use the live adapter loop, narrower overlay-demotion caching so score-table rebuilds do not recompute Kaikki policy rows for every score-weight-only config change, a backend-neutral persistent path-cache layer for translation-pack metadata plus benchmark resource checksums, and the Phase 5 serial-sweep preparation path that now prebuilds compiled `en-es` requests/configs/filter tables/score tables/compact selected-row tables before the remaining per-run case evaluation loop. The compiled score path now also uses `numpy` arrays plus an explicit config-matrix projection for batch score/ranking computation, offers a guarded local `torch` CUDA score backend behind `LEXISHIFT_RULEGEN_SCORE_BACKEND`, replaces string source-phrase tie-breakers with stable numeric phrase-order ids, and reuses equivalent selected-row tables across distinct configs by compiled row-selection signatures: accepted row groups, target-ranked row order, reverse-hygiene signals, and threshold pass/fail rows, rather than intermediate score-table object identity or raw confidence payloads.
  - Current architecture now also explicitly treats database-specific logic as a resource-layer concern: the benchmark workstream is moving toward backend-neutral translation-pack record/loader contracts, with FreeDict/Kaikki compatibility loaders as one current implementation rather than the architectural model.
  - Latest warm-cache canonical `en-es` benchmark smoke on this PC stays exact at objective `129.474` with total wall clock about `0.50s`; `preload_translation_gloss_records` is about `0.223s`, compiled sweep-input preparation is about `0.174s`, and the remaining per-config `run_config` loop is about `0.012s` total across the 144-config serial sweep.
  - A guarded local `torch`/CUDA score-backend smoke is also benchmark-equivalent on this PC, but it is slower on the real current sweep shape at about `0.71s` wall clock with `prepare_compiled_sweep_inputs` about `0.328s`, so GPU remains an explicit opt-in rather than default-on.
  - The latest artifact-resolved best run is now a `var=on` tied winner, but the canonical best objective still has `12` equivalent tied winners including the earlier `var=off` lane; this is currently a stable tie-order detail, not a quality change.
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
  - `en-de` now has a compiled resource context (`EnDeCompiledResources`), candidate-row IR, and a first reusable prepared score-table plus selected-row sweep path for non-variant runs, but it still lacks the fuller `en-es` compiled filter/score-table stack and broader compiled sweep reuse.
  - Current active `en-es` benchmark path still does not have a broadly profitable GPU-shaped workload because it lacks an active embedding/neural scoring backend and is still dominated by preprocessing, selection, and resource work even though the score projection path now has both numeric `numpy` and guarded optional `torch` implementations.

## Rulegen LP Onboarding Scaffold

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-04-04` rulegen LP onboarding now has a machine-readable profile contract, profile validator, a profile-to-repo conformance audit, checklist/operating-model docs, and a template-driven scaffold that can render benchmark/profile stubs plus optional roadmap, pair-module, adapter-contract starter-test, integration-handoff, and benchmark-preset-starter files for a new pair
- Last verified: `2026-04-04` focused scaffold tests, `check:lp-profiles`, `check:docs`, and `check:state`
- Default behavior:
  - LP onboarding now has a documented operating model in `docs/rulegen/lp_onboarding_operating_model.md` and a reusable checklist in `docs/rulegen/lp_onboarding_checklist_template.md`.
  - Machine-readable pair contracts now live under `docs/test_inputs/rulegen_lp_profiles/` and are validated by `npm --prefix scripts run check:lp-profiles`.
  - Repo alignment for those profiles is now validated separately by `npm --prefix scripts run check:lp-conformance`, which audits pair-derived path conventions, preset pair wiring, latest benchmark artifact pair presence, wrapper-command pair mentions, pair-module symbol naming, pair exports in `rulegen/pairs/__init__.py`, adapter registration in `rulegen/adapters.py`, and capability-mode registration in `helper/lp_capabilities.py`.
  - `npm --prefix scripts run scaffold:rulegen:lp -- ...` now acts as a thin scaffold orchestrator:
    - schema-driven JSON for LP profiles and benchmark case stubs
    - template-driven text/code rendering for roadmaps, pair-module stubs, adapter-contract starter tests, integration-handoff docs for central wiring follow-ups, and benchmark-preset starter snippets
  - The scaffold deliberately does not invent LP-specific normalization rules, family mappings, benchmark expectations, ranking decisions, adapter registration, or quality claims.
- Evidence:
  - `docs/rulegen/lp_onboarding_operating_model.md`
  - `docs/rulegen/lp_onboarding_checklist_template.md`
  - `docs/test_inputs/rulegen_lp_profiles/README.md`
  - `docs/test_inputs/rulegen_lp_profiles/profile.schema.json`
  - `scripts/dev/check_rulegen_lp_profiles.py`
  - `scripts/dev/check_rulegen_lp_conformance.py`
  - `scripts/dev/scaffold_rulegen_lp.py`
  - `scripts/dev/templates/rulegen_lp/workstream_roadmap.md.tmpl`
  - `scripts/dev/templates/rulegen_lp/pair_module.py.tmpl`
  - `scripts/dev/templates/rulegen_lp/pair_test.py.tmpl`
  - `scripts/dev/templates/rulegen_lp/integration_handoff.md.tmpl`
  - `scripts/dev/templates/rulegen_lp/benchmark_preset_starter.md.tmpl`
  - `core/tests/dev/test_scaffold_rulegen_lp.py`
  - `scripts/package.json`
- Known gaps:
  - The scaffold still does not wire adapter registration, benchmark presets, pair exports, or central routing updates for a new pair; it now generates those follow-ups as an explicit handoff instead of editing central files automatically.
  - LP-specific benchmark cases, normalization profiles, metadata-family mappings, and ranking decisions remain manual by design.
  - The scaffold is currently a generator plus templates, not yet a full profile-driven code registry updater.
  - The conformance audit currently enforces benchmark/preset conventions plus central pair export/adapter/capability registration for profiled pairs, but it still does not inspect benchmark summary commands, package-level convenience scripts, or pair-specific roadmap freshness.

## Data Source Normalization Architecture

- Status: `implemented`, `verified`; `default-on` = `partial` for manifest-backed translation-pack, frequency-pack, and app-managed embedding-pack installs plus helper default-pack discovery
- Last documented checkpoint: `2026-06-10` manual-supply frequency-source setup now has a GUI baseline: supported source-file builders can open the provider/license page, detect expected source files in Downloads, import provider-native sources into managed `main.sqlite` packs, and write manifest/provenance sidecars. Earlier `2026-06-09` resource catalog entries carry source/license/distribution metadata, Learning Languages exposes source/license details and semantic-pack setup state, and `en-ja` has an explicit source-stack setup path using quality-preferred BCCWJ plus JMDict.
- Last verified: `2026-06-10` targeted GUI tests for frequency-source import and Learning Languages resource-card manual-source candidate import plus i18n JSON validation; earlier `2026-06-09` targeted source-stack test and local pair-resource-plan/i18n JSON smoke for `en-ja`; earlier `2026-06-08` targeted source-stack, semantic-pack install, learning-pair setup, POS overlay catalog/source-license plumbing, generated notices, and locale validation; earlier `2026-04-21` targeted bulk-rules, panel-state, dialog-persistence, and persistence helper tests plus state/doc safety checks
- Default behavior:
  - Target architecture is now explicit:
    - installed packs should resolve by manifest-backed pack identity rather than flat filenames
    - canonical runtime artifacts should prefer compiled SQLite
    - provider-native raw archives/extraction trees should be treated as build inputs rather than runtime contracts
    - raw download/extraction artifacts should be deleted after successful build unless a developer-only retention mode is explicitly enabled
    - any new data-source onboarding should follow that model by default rather than inventing a new install/runtime shape
  - First executable slices are now live for translation, frequency, and app-managed embedding packs:
    - GUI language-pack downloads install into stable per-pack roots under `language_packs/<pack_id>/`
    - app-managed language-pack installs now write `manifest.json`
    - app-managed FreeDict language-pack installs now compile provider TEI sources to canonical SQLite artifacts before completion
    - helper translation-dictionary resolution now prefers manifest-backed installed pack artifacts and FreeDict SQLite filenames before falling back to TEI/path guessing
    - the German frequency whitelist/build path now resolves FreeDict through the same normalized translation-pack artifact contract and shared translation headword loader
    - the GUI bulk-rules FreeDict path now resolves managed SQLite artifacts first, falls back to legacy SQLite files when needed, and no longer treats extracted TEI directories as a normal managed input
    - the synthetic SRS quality/journey harness helpers now emit SQLite translation resources by default
    - the journey harness resource-writing logic now lives in a dedicated helper module so fixture-format changes no longer grow the main scenario-support file
    - shared translation pack refs now honor managed manifests when present instead of relying only on filename/provider inference
    - helper rulegen debug payloads now report translation pack id/provider/source-profile fields through the shared translation-pack seam
    - installed-resource journey staging now preserves manifest-backed translation pack roots instead of flattening them into loose artifact files
    - GUI frequency-pack downloads now install into stable per-pack roots under `frequency_packs/<pack_id>/`
    - app-managed frequency-pack installs now write `manifest.json`
    - helper default frequency resolution now prefers manifest-backed installed pack artifacts before falling back to legacy flat filenames
    - helper/runtime now expose a first frequency pack-ref seam so pair-resource resolution, runtime diagnostics, and benchmark resource payloads can report frequency pack id, provider, and POS source profile instead of only a raw SQLite path
    - LP source-stack defaults now live in `core/lexishift_core/helper/source_stacks.py`; helper runtime diagnostics expose the full `source_stack`, required missing resources, and recommended missing enrichment, while the GUI learning-pair setup cards derive installable frequency, language, POS-overlay, and semantic-pack resources from that same registry
    - GUI SRS growth and the POS normalization probe now share a configured frequency-pack resolver from the helper layer instead of each carrying their own managed-id/manual-path/fallback path logic
    - app-managed translation installs now converge on `language_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `<pack_id>.sqlite` filenames for older local installs
    - app-managed frequency installs now converge on `frequency_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `freq-*.sqlite` filenames for older local installs
    - GUI embedding-pack downloads now install into stable per-pack roots under `embedding_packs/<pack_id>/`
    - app-managed embedding-pack downloads now normalize to SQLite and write `manifest.json` only after successful conversion
    - successful app-managed embedding conversion now treats SQLite as the canonical installed artifact and cleans up the raw downloaded vector file
    - managed embedding activation can now be persisted by pack id per pair, and the replacement-filter runtime resolves those pack ids back through manifest-backed SQLite artifacts
    - app-state load/update now migrates old saved managed embedding artifact paths into pack-id-first per-pair activation and strips those app-owned paths from the manual embedding maps
    - the settings panel now strips managed installed embedding artifacts from seed/auto-link state and keeps managed activation under per-pair embedding pack ids instead of rehydrating those artifacts into the manual path map
    - managed translation settings now persist normalized app-owned translation packs by pack id while the saved manual `language_pack_paths` map omits those managed artifact paths
    - managed frequency settings now persist app-owned frequency packs by pack id while the saved manual `frequency_pack_paths` map omits those managed artifact paths
    - app-state load/update now migrates old saved managed translation/frequency artifact paths into that split representation
    - the settings panel now keeps managed translation/frequency ids in dedicated in-memory sets instead of reconstructing those ids from unified path maps on save
    - the mixed language-pack settings surface now keeps explicit `LanguageResourceBinding` records for managed translation packs plus secondary/manual entries, and dialog persistence can derive managed ids plus manual paths from those bindings
    - `wordnet-en` and `moby-en` remain explicit compatibility exceptions inside that mixed surface: persisted `wordnet_dir` / `moby_path` are still mirrored for compatibility, but bulk-rules runtime consumers now resolve them from the shared binding-map-first effective-path helper before falling back to those legacy aliases
    - the language-pack table, delete flow, and auto-link path now consume those `LanguageResourceBinding` records directly, and the language-pack tab now explicitly states that app-managed packs are the default while manual selection is a temporary compatibility path
    - bulk-rules translation loading and source-stat reporting now use a shared configured language-pack resolver to rebuild managed translation artifacts from stored pack ids before falling back to manual path maps, while SRS growth rebuilds managed default frequency artifacts from stored pack ids before falling back to manual paths
    - the settings panel now omits redundant managed embedding artifact paths from saved settings when those installs are already represented by pack id + manifest-backed resolution
    - settings serialization now writes explicit `language_pack_paths`, `frequency_pack_paths`, and `embedding_pack_paths` keys instead of the older generic `*_packs` path maps
    - the settings UI now labels app-owned resolved resources as installed artifacts and external/manual paths as manual inputs, with embedding activation explicitly distinguishing active installed vs active manual rows
    - the resource workspace intro plus the frequency and embedding tab copy now explicitly describe installed packs as the default path and manual paths as compatibility/import surfaces
    - helper CLI/native-host execution entrypoints now accept `frequency_pack_path` as the preferred frequency override field while retaining `set_source_db` as a compatibility alias, and preview/rebalance payloads expose frequency pack path/id/provider/POS-profile fields alongside the legacy execution field
    - Spanish-target SRS seed/admission paths can now auto-discover an installed `pos-es-ud-ancora-v1` POS overlay under `pos_packs/`, fill missing/unmapped SPALEX POS from UD AnCora word-form UPOS, and expose `pos_overlay_*` diagnostics separately from the frequency-pack source
    - the learning-pair resource setup surface now includes `en-de` via the source-stack registry (`freq-de-default`, `freedict-de-en`, `freedict-en-de`) and keeps existing pair cards in creation order while focus/status labels change
    - the learning-pair resource setup surface now also includes `en-ja` via the source-stack registry with `freq-ja-bccwj` as the quality-preferred/manual target-frequency source and `jmdict-ja-en` as the auto-download rulegen/semantic-locator source; source-frequency prior and JP WordNet remain documented as non-blocking experiments/enrichment rather than required setup resources
    - Learning Languages now shows semantic/veto reference-pack state: `en-es` can install `en-es-active-only-combined-full-v1-tranche-011` as a pair-level semantic pack copy for later SRS rule-publication enrichment, while `en-de` shows a non-blocking pending row because no default semantic reference pack is declared yet
    - detailed resource tables and Learning Languages resource slots now expose a non-blocking Source & license details action showing provider, source URL, license link, distribution mode, local installed path when present, and the generated notices path
    - manual-supply frequency resources with supported source-file builders now route through explicit user-local acquisition: the setup UI opens the provider/license page, detects expected Downloads-folder source filenames, offers an import action from the pair card, confirms source rights, and converts/links into the managed pack layout with manifest/provenance sidecars
    - `scripts/data/generate_third_party_data_notices.py` renders `docs/language_pairs/THIRD_PARTY_DATA_NOTICES.md` from the same resource catalog metadata used by GUI install/setup flows
  - Current runtime contract is still transitional rather than final:
    - FreeDict and Kaikki translation packs now expose SQLite as the canonical app-managed runtime artifact, but manual TEI files, older extracted directories, and legacy `<pack_id>.sqlite` filenames remain compatibility inputs during migration
    - normalized translation/frequency settings are now pack-id-first for the mandatory managed families, while `wordnet-en` / `moby-en` remain explicit compatibility aliases inside the secondary language-pack family until any later promotion decision is made
    - frequency packs already expose SQLite, and new app-managed installs now use `main.sqlite`, but legacy `freq-*.sqlite` names still remain valid fallback paths during migration
    - embedding runtime still accepts raw `.vec/.bin` paths as a compatibility path for manually supplied external files
    - managed embedding settings/runtime are now pack-id-first for app-owned installs, while manual raw/vector and external SQLite paths remain separate compatibility/import inputs
    - POS overlays have a helper/runtime resolver and builder for Spanish, and `pos-es-ud-ancora-v1` is now a first-class recommended learning-pair setup resource that auto-downloads UD AnCora sources into `pos_packs/<pack_id>/main.sqlite`; broader POS-overlay table views and non-Spanish overlay catalogs remain future work
    - semantic-pack setup is now visible in Learning Languages, but runtime semantic accuracy remains dependent on a subsequent SRS rule publication/refresh that attaches the installed reference evidence to eligible rules
    - broad manual file-path selection is not a promoted product feature; it is a transitional compatibility surface and likely phase-out candidate unless a concrete use case survives
- Evidence:
  - `docs/developer/data_source_normalization_architecture.md`
  - `docs/developer/language_pair_generalization_roadmap.md`
  - `docs/language_pairs/de_en_workstream_roadmap.md`
  - `apps/gui/src/language_packs_catalog.py`
  - `apps/gui/src/language_packs.py`
  - `apps/gui/src/settings_pair_resource_plan.py`
  - `apps/gui/src/settings_language_packs_path_mixin.py`
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/src/settings_language_packs_table_mixin.py`
  - `apps/gui/src/settings_language_packs_pair_setup_mixin.py`
  - `apps/gui/src/settings_language_packs_support.py`
  - `scripts/data/generate_third_party_data_notices.py`
  - `docs/language_pairs/THIRD_PARTY_DATA_NOTICES.md`
  - `core/lexishift_core/helper/translation_packs.py`
  - `core/lexishift_core/helper/frequency_packs.py`
  - `core/lexishift_core/helper/embedding_packs.py`
  - `core/lexishift_core/helper/pair_resources.py`
  - `core/lexishift_core/helper/source_stacks.py`
  - `core/lexishift_core/helper/installed_packs.py`
  - `core/lexishift_core/resources/installed_packs.py`
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `core/lexishift_core/helper/use_cases/semantic_pack_install.py`
  - `apps/gui/src/main_srs_mixin.py`
  - `apps/gui/src/main_replacement_filter_mixin.py`
  - `apps/gui/src/dialogs.py`
  - `core/lexishift_core/persistence/settings.py`
  - `apps/gui/src/main_bulk_rules_mixin.py`
  - `core/lexishift_core/resources/freedict_sqlite.py`
  - `core/lexishift_core/resources/synonyms.py`
  - `core/lexishift_core/frequency/de/build_support.py`
  - `core/lexishift_core/frequency/de/pipeline.py`
  - `apps/gui/src/main_bulk_rules_mixin.py`
  - `scripts/testing/srs_quality_harness_support.py`
  - `scripts/testing/srs_journey_harness_support.py`
  - `scripts/testing/synthetic_translation_fixture_support.py`
  - `scripts/data/convert_embeddings.py`
  - `scripts/data/convert_freedict_tei_to_sqlite.py`
  - `core/tests/helper/test_installed_packs.py`
  - `core/tests/helper/test_lp_capabilities.py`
  - `core/tests/helper/test_frequency_packs.py`
  - `core/tests/dev/test_pos_normalization_probe.py`
  - `core/tests/helper/test_pair_resources.py`
  - `core/tests/helper/test_helper_engine.py`
  - `apps/gui/tests/test_main_settings_resource_persistence.py`
  - `apps/gui/tests/test_main_embedding_pack_resolution.py`
  - `apps/gui/tests/test_language_pack_panel_state_mixin.py`
  - `apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py`
  - `apps/gui/tests/test_language_pack_path_mixin.py`
  - `apps/gui/tests/test_state_resource_settings_migration.py`
  - `core/tests/helper/test_embedding_packs.py`
  - `core/tests/dev/test_srs_harness_resource_normalization.py`
  - `core/tests/frequency/test_de_build_support.py`
  - `core/tests/resources/test_dict_loaders_freedict_pos.py`
  - `core/tests/resources/test_synonyms_translation_packs.py`
- Known gaps:
  - Installed-pack resolution is only partially manifest-driven today; generic helper/runtime resolution and GUI auto-link use it for translation and frequency defaults, shared translation/frequency pack refs now honor manifests, and benchmark resource payloads now carry translation and source-frequency pack identity directly, but probe flows still include some legacy path assumptions.
  - FreeDict packs are still effectively runtime-addressed through TEI-compatible paths in some probe/tooling flows even though app-managed installs now build to SQLite and the main helper/GUI/harness consumers now prefer SQLite-first paths.
  - Managed embedding activation no longer needs persisted app-owned artifact paths, and the settings panel now strips managed installed artifacts from seed/auto-link state; remaining temporary embedding path handling is mostly limited to in-flight download/conversion/manual-link flows.
  - Manual external embedding files still bypass the managed-pack manifest layout by design during migration.
  - `wordnet-en` / `moby-en` are still not promoted into the same normalized managed-pack model as translation/frequency/embeddings; they remain explicit compatibility exceptions until the broader secondary lexical family decision is made.
  - Frequency packs still preserve their legacy `freq-*.sqlite` artifact names as fallback paths during migration.
  - Translation consumers still include TEI-compatible assumptions in some probe/tooling paths, but the shared loader-backed or SQLite-first consumers now include rulegen pairs, helper/runtime diagnostics, benchmark resource payloads, the German frequency whitelist, synonym generation, the bulk-rules GUI path, and the synthetic SRS quality/journey harnesses plus installed journey staging.

## `de-en` Baseline Rulegen Enablement

- Status: `implemented`, `verified`; `default-on` = `yes` for helper/rulegen capability when `freedict-en-de` is present
- Last documented checkpoint: `2026-04-03` `de-en` helper defaults now prefer manifest-backed app-managed translation artifacts, with legacy `freedict-en-de.sqlite` and TEI inputs retained only as fallback compatibility paths
- Last verified: `2026-04-03` targeted helper/capability/adapter tests and doc sync
- Default behavior:
  - `de-en` now has a real rulegen mode (`de_en`) and participates in the generalized translation-dictionary helper seam.
  - Default `de-en` forward resolution now prefers manifest-backed app-managed translation artifacts and otherwise falls back to legacy `freedict-en-de.sqlite` / TEI compatibility inputs when needed, with normalized translation-pack identity available in helper/resource resolution.
  - The first `de-en` pair implementation is intentionally simple: FreeDict forward candidate extraction, generic scoring, German source-side stopword filtering, and no reverse-check path yet.
- Evidence:
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/rulegen/pairs/de_en.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/tests/helper/test_lp_capabilities.py`
  - `core/tests/helper/test_pair_resources.py`
  - `core/tests/helper/test_translation_packs.py`
  - `core/tests/helper/test_helper_engine.py`
  - `core/tests/helper/test_helper_daemon.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `docs/language_pairs/de_en_workstream_roadmap.md`
- Known gaps:
  - `de-en` still has no benchmark dataset or quality frontier; this slice is enablement, not tuning.
  - `de-en` still has no reverse-check implementation.
  - Helper CLI override naming still reflects legacy FreeDict terminology even though the generalized translation-dictionary seam is active underneath.

## `en-de` Advisory Quality Lane

- Status: `implemented`, `verified`; `default-on` = `no` for the repo-wide hard gate
- Last documented checkpoint: `2026-06-09` `en-de` now uses `freq-en-leipzig-default` as the default English source-frequency prior, and the canonical advisory preset is retuned around the accepted top3-first configuration.
- Last verified: `2026-06-09` focused source-frequency/default-resolution tests, SRS quality harness, LP conformance checks, resource integrity audit, and dedicated `npm --prefix scripts run quality:rulegen:en-de` refresh
- Default behavior:
  - `en-de` now has a first-class advisory benchmark/gate/triage surface separate from the canonical strict `en-es` lane.
  - The dedicated `en-de` gate now runs in pair-scoped mode, so it no longer reports missing required/recommended-pair or no-delta-overlap noise from unrelated benchmark lanes.
  - The lane now uses a named preset:
    - `en_de_canonical_matrix`
  - `en-de` now has a default-on English source-frequency prior in the
    canonical advisory lane and helper rulegen publication path when the pack
    is installed:
    - default pack: `freq-en-leipzig-default/main.sqlite`
    - fallback compatibility pack: `freq-en-coca.sqlite`
    - benchmark/config label: `sfreq=on/off`
    - benchmark CLI surface: `--source-frequency-prior-values`, `--source-frequency-db-en-de`
    - probe CLI surface: `--enable-source-frequency-prior`, `--source-frequency-db-en-de`
  - `en-de` now also has an experimental default-off reverse-check bridge:
    - benchmark/config labels: `rev`, `xamb`, `xspec`
    - benchmark uses the existing reverse English->German resource resolution when `rev=on`
    - probe flags: `--reverse-check-enabled`, `--translation-dict-en-de-reverse`
  - `en-de` now also consumes the existing Kaikki policy surface when the translation source is a Wiktionary/Kaikki-style SQLite:
    - benchmark/config labels: `kdem`, `kfam`, `kprov`
    - probe flags: `--kaikki-policy-live-demotion`, `--kaikki-policy-late-sense-penalty`
    - provider/profile inference now follows the translation-pack identity instead of hardcoding FreeDict POS normalization
  - `en-de` now also has experimental default-off Kaikki sense-shaping / competition seams:
    - same-sense representative selection surfaced as `srep`
    - sense-level defaultness competition surfaced as `sdcmp`
    - probe flags: `--sense-representative-penalty`, `--sense-defaultness-competition-penalty`
  - The app-managed translation catalog now includes:
    - `wiktionary-de-en`
    - build wrapper: `scripts/data/convert_kaikki_de_en_to_sqlite.py`
    - converter path: `scripts/data/convert_kaikki_glosses_to_sqlite.py`
  - Dedicated outputs now live at:
    - `docs/test_outputs/rulegen_benchmark_en_de_latest.json`
    - `docs/test_outputs/rulegen_benchmark_en_de_latest.md`
    - `docs/test_outputs/rulegen_benchmark_en_de_latest.html`
    - `docs/test_outputs/rulegen_quality_gate_en_de_latest.json`
    - `docs/test_outputs/rulegen_benchmark_triage_en_de_latest.json`
    - `docs/test_outputs/rulegen_benchmark_triage_en_de_latest.md`
    - `docs/test_outputs/rulegen_benchmark_en_de_summary_latest.md`
    - `docs/test_outputs/rulegen_quality_gate_en_de_summary_latest.md`
    - `docs/test_outputs/rulegen_benchmark_triage_en_de_summary_latest.md`
  - The current lane intentionally stays advisory:
    - no reverse-check in the canonical advisory latest lane
    - no promoted `en-de` Kaikki default source path yet
    - current scoped quality is product-accepted for beta/advisory use
    - no promoted `en-de` machine delta baseline yet
    - severity-aware forbidden-any cleanup comes before pair-specific frontier work
- Evidence:
  - `docs/language_pairs/en_de_workstream_roadmap.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/package.json`
  - `docs/test_inputs/rulegen_benchmark_presets.json`
  - `docs/test_outputs/rulegen_benchmark_en_de_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_en_de_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_de_latest.json`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_en_de_source_freq_experiment_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_de_source_freq_experiment_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_summary_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_en_de_kaikki_tuning_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_de_kaikki_tuning_latest.json`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `apps/gui/src/language_packs_catalog.py`
  - `core/lexishift_core/frequency/en/pipeline.py`
  - `core/lexishift_core/helper/source_stacks.py`
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `scripts/data/convert_kaikki_de_en_to_sqlite.py`
  - `scripts/testing/rulegen_probe_words.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `core/tests/dev/test_rulegen_probe_words.py`
  - `core/tests/resources/test_kaikki_sqlite_conversion.py`
- Known gaps:
  - `en-de` remains advisory and is still not part of `required_benchmark_pairs`.
  - The benchmark case set is now broader at `58` targets, and the current `en-de` latest run passes the scoped advisory quality floor with `86.21%` top1, `100.00%` top3, `0.00%` forbidden-top1, `15.52%` forbidden-any, and `2.29` average rules per target.
  - The current `en-de` latest triage surface still has `12` actionable items (`9` FAIL, `3` REVIEW). These are now forbidden-any or top1-order issues rather than forbidden-top1 issues; examples include `Schule -> pod`, `Zeit -> spell/most`, `Fenster -> box`, `Tag -> tag`, and `Stimme -> part`.
  - The dedicated `en-de` gate is pair-scoped, passing, and product-accepted for beta/advisory use. Delta checks still warn until an `en-de` machine baseline is promoted:
    - `DELTA_SCOPE_BASELINE_MISSING`
  - `en-de` now has default-off reverse-check plumbing and probe support, but the first focused Kaikki reverse experiment did not beat `rev=off` (`93.10%` top1 / `96.55%` top3 -> `91.38%` / `96.55%` with the tested reverse setting).
  - The Leipzig source-frequency prior plus top3-first preset is sufficient for the scoped advisory floor, but not enough to call `en-de` hard-gated or semantically parity-ready:
    - current canonical config: `md=3 mr=none srep=on thr=0.500 sfreq=on sdef=0.80 var=off pos=on rev=off w_pos=0.000`
    - remaining cleanup is mainly severity/defaultness work around broad third-slot candidates and top1 order
  - `wiktionary-de-en` download/build support now exists, and the local Kaikki tuning lane is strong (`93.10%` top1 / `96.55%` top3), but it is still a local advisory comparison rather than a promoted default source path or accepted scoped baseline.
  - The current best local Kaikki `en-de` config still leaves the richer parity signals off:
    - `rev=off`
    - `kdem=off`
    - `kprov=off`
  - Same-sense representative selection is now a real frontier mover in local Kaikki runs, but the first sense-level defaultness penalty (`sdcmp`) proved too blunt to help.
  - `en-de` now has a compiled resource context, candidate-row IR, and live/compiled prepared score-table plus selected-row sweep coverage, but it still lacks the fuller `en-es` prepared benchmark stack and the richer `en-es`-style provenance competition layer.
  - Practical initialize/refresh work for the German-target lane is no longer blocked on a missing German frequency resource in the current source-stack path; `freq-de-default` is installable/valid in the latest local smoke. The remaining `en-de` gap is quality maturity, not basic resource availability.

## `en-ja` Advisory Quality Lane

- Status: `implemented`, `verified`; `default-on` = `no` for the repo-wide hard gate
- Last documented checkpoint: `2026-06-10` `en-ja` now has an expanded 33-case benchmark set, machine-readable LP profile, named canonical advisory preset, dedicated npm wrapper, latest benchmark/gate/triage artifacts, pair-scoped quality-gate evidence, a 95-case semantic-veto breadth-stress lane, explicit non-default helper policy `en_ja_sentence_veto_breadth_v1`, JMDict/BCCWJ topic-source readiness evidence, a user-approved topic precision packet, and an approved non-default strong-label topic-overlay path for helper admission previews.
- Last verified: `2026-06-10` dedicated `npm --prefix scripts run quality:rulegen:en-ja` refresh and summary rendering on the expanded case set; SRS/runtime smoke via `quality:srs:harness`, `quality:srs:journey`, `quality:srs:journey:real`, `quality:srs:journey:installed`, targeted SRS/extension/helper semantic policy contract tests, en-ja semantic-veto breadth harness/sweep/product-quality artifacts, `npm --prefix scripts run quality:srs:topic:en-ja`, `quality:srs:topic:en-ja:review`, `quality:srs:topic:en-ja:overlay`, focused en-ja topic-overlay helper preview coverage, and Options en-ja topic allowlist contract coverage; earlier `2026-06-09` LP profile/conformance checks, focused rulegen benchmark/preset/gate tests, and source-stack/resource-plan validation
- Default behavior:
  - `en-ja` now has a first-class advisory benchmark/gate/triage surface separate from the canonical strict `en-es` lane.
  - Current promotion decision: keep `en-ja` advisory/non-default for this stage.
    Do not add a machine delta baseline, `required_benchmark_pairs`, or default
    runtime semantic policy until product/default enablement needs that stronger
    contract.
  - The lane uses a named preset:
    - `en_ja_canonical_matrix`
  - The current reference config is:
    - `max_definitions=2`
    - `max_rules=none`
    - `exact_gloss_demotion=on`
    - `source_frequency_prior=off`
    - `variants=off`
    - `pos=on`
    - `reverse=off`
  - The source posture is explicit:
    - `jmdict-ja-en` is the JMDict-backed translation/rulegen/semantic-locator source.
    - `freq-ja-bccwj` is the quality-preferred/manual target-frequency source for SRS/admission and target word-package context, not an active source-frequency ranking prior in the current rulegen lane.
  - Current SRS/runtime smoke is non-failing:
    - `docs/test_outputs/srs_quality_latest.json` reports `PASS` with `pass=22`, `warn=0`, `fail=0`
    - en-ja deterministic, real-publication, and installed-data journey lanes complete with `fail=0`; their only journey warning is the known admitted-set publication broader than due-subset observation
    - installed-data journey resolves real BCCWJ/JMDict candidates and Japanese script-form word packages without mutating the live helper state
  - Current semantic-veto breadth evidence is non-failing for the initial product target:
    - `docs/test_outputs/semantic_routing_sentence_veto_en_ja_breadth_latest.json` reports `95` cases, `96.8%` decision accuracy, `100.0%` replace precision, `92.1%` replace recall, `0` harmful replacements, and `3` false abstains
    - `docs/test_outputs/semantic_routing_sentence_veto_sweep_en_ja_breadth_latest.json` sweeps `10240` lexical rows including `family_all` and `active_only` phrase-guard POS scopes; the best objective and zero-harmful frontier now agree on the active-only phrase-scope candidate
    - `docs/test_outputs/semantic_veto_product_quality_en_ja_latest.json` meets the mirrored `en-es` initial product thresholds with `92.1%` positive allow, `100.0%` negative abstain, and utility above lexical allow-all
    - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py` registers explicit, non-default helper policy `en_ja_sentence_veto_breadth_v1` with the accepted active-only phrase-guard POS scope
  - Current topic-source readiness is measured but not promoted:
    - `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.json` reports `9,258` candidate-like BCCWJ rows in the top `10k` frontier, `8,403` with any JMDict match, `8,363` with strong exact/alias JMDict matches, `1,910` with trusted topic fields, and `866` with trusted topic fields plus strong matching
    - the audit keeps exact/alias evidence separate from reading-only evidence so same-reading homographs do not inflate strong topic counts
    - `12 / 16` product-taxonomy families have strong candidate rows; anime/manga, hobbies/crafts, and register/style families remain source-thin or review-only backlog surfaces
    - `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.json` samples `144` rows across all `116` family/match/source-label cells and applies `144` user-approved labels: `8` strong accepts, `57` light accepts, `63` wrong-topic rejects, and `16` secondary/obscure rejects
    - `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.json` builds a user-approved, non-default `65` row overlay candidate; only the `8` strong labels are runtime-effective under the current `profile_injection_min_membership=1.0` policy, while `57` light labels remain lower-membership evidence for later scalar-topic work
    - `core/tests/helper/test_helper_engine.py` verifies that ordinary helper preview resolution can load the `en-ja` overlay and move a matched medicine/health candidate into the admitted preview
    - `apps/chrome-extension/options/core/srs_topic_support.js` gates `en-ja`
      topic chips to the approved strong-label families:
      `finance_business`, `games`, `law_politics_civics`, `medicine_health`,
      `science_technology`, and `sports_fitness`
    - this proves source supply, reviewed-label integration, and some admission movement, but it is still not broad topic recall proof, ordinary installed Options-flow proof, or default topic-admission parity
  - Dedicated outputs now live at:
    - `docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
    - `docs/test_outputs/rulegen_benchmark_en_ja_latest.md`
    - `docs/test_outputs/rulegen_benchmark_en_ja_latest.html`
    - `docs/test_outputs/rulegen_quality_gate_en_ja_latest.json`
    - `docs/test_outputs/rulegen_benchmark_triage_en_ja_latest.json`
    - `docs/test_outputs/rulegen_benchmark_triage_en_ja_latest.md`
    - `docs/test_outputs/rulegen_benchmark_en_ja_summary_latest.md`
    - `docs/test_outputs/rulegen_quality_gate_en_ja_summary_latest.md`
    - `docs/test_outputs/rulegen_benchmark_triage_en_ja_summary_latest.md`
    - `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.json`
    - `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.md`
    - `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.json`
    - `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.md`
    - `docs/test_outputs/srs_jmdict_topic_overlay_en_ja_latest.json`
    - `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.json`
    - `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.md`
- Evidence:
  - `docs/test_inputs/rulegen_lp_profiles/en_ja.json`
  - `docs/test_inputs/rulegen_benchmark_presets.json`
  - `docs/test_inputs/rulegen_benchmark_cases/en_ja.json`
  - `scripts/package.json`
  - `core/lexishift_core/rulegen/pairs/en_ja.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/helper/source_stacks.py`
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_en_ja_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_ja_latest.json`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/srs_quality_summary_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.json`
  - `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_breadth_v1.json`
  - `docs/test_inputs/semantic_veto_product_quality_policy_en_ja.json`
  - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
  - `docs/test_outputs/semantic_routing_sentence_veto_en_ja_breadth_latest.json`
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_en_ja_breadth_latest.json`
  - `docs/test_outputs/semantic_veto_product_quality_en_ja_latest.json`
  - `docs/test_inputs/srs_topic_preference_taxonomy_en_ja.json`
  - `docs/test_inputs/srs_jmdict_topic_review_labels_en_ja.json`
  - `scripts/testing/srs_jmdict_topic_source_readiness_en_ja.py`
  - `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.json`
  - `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.md`
  - `scripts/testing/srs_jmdict_topic_review_packet_en_ja.py`
  - `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.json`
  - `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.md`
  - `scripts/testing/srs_jmdict_topic_overlay_poc_en_ja.py`
  - `docs/test_outputs/srs_jmdict_topic_overlay_en_ja_latest.json`
  - `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.json`
  - `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.md`
  - `core/tests/helper/test_helper_engine.py`
  - `apps/chrome-extension/options/core/srs_topic_support.js`
  - `core/tests/dev/test_extension_srs_settings_contract.py`
- Known gaps:
  - `en-ja` remains advisory and is still not part of `required_benchmark_pairs`.
  - The benchmark case set is now expanded to `33` targets; current scoped advisory quality passes with `96.97%` top1, `100.00%` top3, `0.00%` forbidden-top1, `3.03%` forbidden-any, and `1.76` average rules per target.
  - The current scoped gate has no failure findings, but still warns until an `en-ja` machine baseline and broader sensitivity sweep are promoted:
    - `DELTA_SCOPE_BASELINE_MISSING`
    - `SATURATION_SINGLE_RUN_WARN`
    - These are accepted advisory-lane warnings for this stage, not active
      blockers. The repo should keep using `npm --prefix scripts run
      quality:rulegen:en-ja` for en-ja work and shared rulegen regression checks
      instead of hard-gating the pair globally.
  - The current latest triage has one accepted nonblocking known failure:
    `世界` top1 is `society`, while `sphere` remains a forbidden-any third-slot
    candidate under the JMDict gloss ordering. Keep `sphere` forbidden because
    the sense is obscure and should not be silently product-accepted for
    teaching; do not weaken the case just to clear the advisory lane.
  - The current benchmark machinery does not yet make BCCWJ an active candidate-ordering prior; it relies on JMDict gloss order plus exact generic-gloss demotion and target word-package context.
  - The semantic-veto breadth-stress lane passes the mirrored initial product thresholds, but it is not enough for parity/default-on:
    - only curated stress rows are measured so far
    - no representative browsing lane has been measured
    - `en_ja_sentence_veto_breadth_v1` is explicit-callable but not the default `en-ja` semantic decision policy by current promotion decision
    - current zero-harmful breadth behavior depends on active-only phrase-guard POS scope plus the idiom-tail phrase signal for `ball is in your court`
  - Runtime/SRS smoke is accepted for this onboarding stage, but `en-ja` is still not promoted into the repo-wide required rulegen pair list or any public default-on rollout policy.
  - Topic-source readiness is no longer unknown for `en-ja`: BCCWJ/JMDict plus
    `srs_topic_preference_taxonomy_en_ja_v1` provide real source supply for
    selected families. Topic-aware SRS admission is partially evidenced by a
    user-approved non-default overlay and focused helper preview coverage, but
    still unresolved for full product parity because light labels are not yet a
    product scalar-membership contract and broad visible preference movement
    comparable to the `en-es` topic MVP has not been proven through the ordinary
    installed Options/helper/runtime flow. Follow
    `docs/srs/srs_topic_signal_lp_generalization_runbook.md` before claiming
    profile-personalized admission parity.

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

- Status: `implemented`, `verified`, `default-on` = `yes` for SRS scheduler/admission/publication/runtime-serving workflow
- Last documented checkpoint: `2026-06-10` synthetic SRS harness refresh remains clean across `en-ja` and `en-de`, with bootstrap/publication/runtime diagnostics, due-aware runtime metadata, feedback-cycle pause/resume, and encounter-watch coverage all non-failing.
- Last verified: `2026-06-10` `npm --prefix scripts run quality:srs:harness`, `quality:srs:summary`, focused en-ja LP E2E publication test, and targeted SRS quality/journey tests
- Default behavior:
  - Use the synthetic harness for SRS scheduler, admission refresh, helper publication, set execution, and runtime-serving workflow changes.
  - Review scheduling is now FSRS-based.
  - Current harness covers bootstrap/publication/runtime diagnostics for `en-ja` and `en-de`, plus an `en-ja` feedback-cycle pause/resume scenario.
  - The feedback-cycle scenario now checks helper SRS due metadata and runtime due-active counts, so broad publication can pass only when runtime serving remains due-aware.
  - The feedback-cycle scenario now records initial, before-refresh, and after-refresh store snapshots, including scheduler fields, selected lemmas, and separate feedback vs refresh deltas.
  - The encounter-watch scenario verifies age-aware dashboard diagnostics for fresh unseen, stale unseen, legacy age-unknown, reviewed, and no-enabled-rule active items.
  - The committed `latest` JSON artifact is publication-normalized for review stability; raw in-memory harness details remain available before publication.
  - Human-facing summary is available from the JSON artifact and includes an Encounter Watch section.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/testing/srs_quality_harness.py`
  - `scripts/testing/srs_quality_harness_support.py`
  - `scripts/testing/srs_quality_summary.py`
  - `core/tests/dev/test_srs_quality_harness.py`
  - `core/tests/dev/test_srs_quality_summary.py`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/srs_quality_summary_latest.md`
- Known gaps:
  - Coverage is synthetic and pair-limited; it does not yet grade pedagogical quality or real user data.
  - The harness verifies runtime due-aware serving through metadata; it does not require or prove a dedicated due-only publication artifact.
  - `es-en` / `en-es` SRS quality scenarios are not yet represented in the synthetic harness.

## Testing Artifact Provenance / Freshness

- Status: `implemented`, `verified`; `default-on` = `partial` for the en-ja SRS learner-difficulty research chain
- Last documented checkpoint: `2026-06-17` generated SRS learner-difficulty research artifacts now have a standardized provenance contract and a reusable freshness checker; missing provenance is treated as stale.
- Last verified: `2026-06-17` focused artifact-provenance unit coverage plus live acronym-audit freshness smoke.
- Default behavior:
  - Do not trust `*_latest` by filename alone.
  - Use live producer/consumer code as source of truth, then regenerate or run `scripts/testing/check_artifact_freshness.py` before using an existing artifact for a tuning decision.
  - Generated artifacts under `docs/test_outputs/` are recursively checked when they are inputs to another generated artifact, so a downstream report cannot silently rely on an unprovenanced upstream matrix/search output.
- Evidence:
  - `docs/developer/testing_artifact_provenance.md`
  - `scripts/testing/artifact_provenance.py`
  - `scripts/testing/check_artifact_freshness.py`
  - `scripts/testing/srs_ja_acronym_signal_audit_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_signal_sweep_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_piecewise_search_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_model_family_search_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_model_family_meta_search_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_model_tree_search_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_curve_search_en_ja.py`
  - `scripts/testing/srs_learner_difficulty_tail_partition_search_en_ja.py`
  - `core/tests/dev/test_artifact_provenance.py`
- Known gaps:
  - Coverage is not repo-wide yet; older rulegen/semantic artifacts may still lack this generated-artifact provenance block.
  - Large external installed-resource files may be tracked by size/mtime instead of SHA-256 when they exceed the configured hash threshold.

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

## SRS Journey E2E Harness

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-06-10` en-ja deterministic, real-publication, and installed-resource journey artifacts were refreshed for onboarding smoke, and installed-resource staging now preserves installed POS-overlay packs so Spanish SPALEX journeys exercise the same UD AnCora enrichment available to helper seed/admission paths.
- Last verified: `2026-06-10` `quality:srs:journey`, `quality:srs:journey:real`, `quality:srs:journey:installed`, journey summaries/HTML renderers, targeted journey tests, installed-support test, and extension SRS/settings/runtime contract tests
- Default behavior:
  - Deterministic `en-ja` and `en-es` core and edge journey lanes plus matching real-publication lanes are available as analysis-first SRS E2E harnesses, but they are not yet part of the required default SRS workflow loop in `AGENTS.md`.
  - The core lane captures item-level admitted `S`, due `D`, and published `P` sets across bootstrap, refresh, and fade/stick phases.
  - Journey JSON now includes bootstrap candidate audits, refresh candidate ranking audits, and richer per-item state fields such as confidence, due rank, and lexical previews for retroactive pedagogical review.
  - The edge lane captures duplicate-feedback and exposure-only behavior with the same item-level reporting contract.
  - The real-publication lane keeps deterministic clocks/resources, uses the actual seed-builder plus helper/rulegen publication path, and now holds complete due publication for the current `en-ja` and `en-es` scenarios.
  - Separate installed-resource review lanes now stage the user's local frequency/dictionary packs into an isolated temp helper root, assign cohorts from actual admitted lemmas, and surface real-data pedagogical flow without mutating the live helper state.
  - Installed-resource staging preserves manifest-backed POS-overlay packs as well as frequency, language, reverse-language, and stopword resources, so `en-es` SPALEX installed journeys use `pos-es-ud-ancora-v1` when present.
  - The `en-es` profile-preference lane proves that `profile_bootstrap` can promote a tagged topic candidate into the initial active set, while the same scenario still grows, pauses, and resumes through feedback refresh.
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
  - `docs/test_outputs/srs_journey/srs_journey_en_es_profile_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_profile_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_profile_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_installed_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.html`
- Known gaps:
  - `en-de` extension is still pending.
  - The deterministic and synthetic-resource real-publication lanes are still useful regression surfaces, but installed-resource review currently depends on local data-pack availability and is not yet part of the default required workflow loop.
  - The journey harness artifacts are not the current due-aware runtime serving authority; use the SRS quality harness for the Lane 5 helper-metadata/runtime-gate contract.
  - Current `en-ja` journey smoke by itself does not establish topic-aware
    admission parity. Use the pair-local source-readiness, user-approved overlay,
    and focused helper preview evidence as the backend gate, then run the
    ordinary installed Options/helper/runtime flow before any profile-topic
    parity claim.

## en-es SRS Beta Preflight

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-05-27` read-only en-es SRS beta preflight now
  composes strict-MVP topic-picker checks, taxonomy visibility validation, latest
  SRS quality evidence, en-es profile-preference and installed-resource journey
  evidence, and explicit manual beta signoff checks.
- Last verified: `2026-05-27` preflight script/report generation, focused
  preflight tests, rerun en-es profile and installed journey artifacts plus
  summaries, doc-reference check, state audit, diff check, and changed-file gate.
- Default behavior:
  - The preflight is read-only. It does not install packs, mutate helper state,
    delete SRS stories, or mark beta signoff complete.
  - The generated status is expected to remain `REVIEW` until a human completes
    the fresh extension/helper smoke checklist.
  - Automated checks require the options-page topic picker to match
    `mvp_picker_visibility=strict_mvp_visible`, require beta/hidden/register/
    legal-gated families to stay out of the ordinary picker, require locale
    coverage for visible chips, and require latest SRS quality/journey artifacts
    to have no failing findings.
  - Current en-es journey warnings are surfaced rather than hidden. Publication
    broader than due is an observation-mode warning, while the installed-resource
    `movimiento` due-not-published warning remains a review item for manual beta
    smoke because it is a rulegen/data coverage symptom, not a picker/admission
    selector failure.
- Evidence:
  - `docs/runbooks/srs_beta_preflight_en_es.md`
  - `scripts/testing/srs_beta_preflight_en_es.py`
  - `docs/test_outputs/srs_beta_preflight_en_es_latest.json`
  - `docs/test_outputs/srs_beta_preflight_en_es_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_profile_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_profile_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md`
  - `core/tests/dev/test_srs_beta_preflight_en_es.py`
- Known gaps:
  - Manual fresh-install/helper connection, runtime replacement, feedback,
    automatic refresh, discard, and reset smoke still require human beta signoff.
  - The preflight does not replace Chrome Web Store packaging preflight, full
    repo safety checks, or build validation.
  - It reports latest local installed-resource evidence; a tester machine can
    still differ if required packs are missing or manually installed differently.

## Development Workflow Safeties

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-04-19` Ruff fallback resolution + explicit unavailable reporting for workflow style checks
- Last verified: `2026-04-19` targeted dev-workflow unit tests + wrapper-driven `check:style` report + `check:changed:local`; `2026-05-15` Lane 3 L3-F packaging/platform parity truth pass, Windows parity audit, parity summary render, focused workflow/build/parity tests, doc-reference check, state check, and diff hygiene
- Default behavior:
  - `npm --prefix scripts run check` is the stable non-mutating repo safety command.
  - `npm --prefix scripts run check` now includes the strict Windows parity audit, so parity regressions fail the default local safety gate and pre-push hook.
  - `npm --prefix scripts run check` now includes strict repo-wide Ruff lint/format checks because the repo-wide style baseline is clean.
  - Workflow Ruff checks now try the selected Python's `-m ruff` entrypoint first and fall back to a `ruff` executable on `PATH`; advisory commands report `unavailable` instead of fake style debt when neither invocation exists, while strict variants still fail.
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
  - `scripts/dev/ruff_support.py`
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
- Last verified: `2026-03-12` parity audit rerun + repo-safety integration + changed-scope/CI workflow wiring review; `2026-05-15` Lane 3 L3-F parity audit rerun, parity summary render, focused Windows parity tests, doc-reference check, state check, and diff hygiene
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

## Browser Helper Connection Management

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-06-01` browser-connections manager kept the narrowed one-click prod rows and browser+extension-ID unpacked-dev flow, workspace-host installs switched to a pinned-interpreter wrapper, native-host startup failures write deterministic local logs, resource-settings launches now carry a startup session into GUI startup telemetry, the packaged GUI now uses the canonical PyInstaller onedir EXE/COLLECT payload split, transport/browser failures expose stable helper-facing error codes, options-side helper flows localize timeout/browser-blocked cases alongside helper-missing/host-exited cases, and saved bundled/workspace connections auto-repair a narrow set of deterministic stale manifest/host states on startup or when `Connections...` opens
- Last verified: `2026-06-01` targeted native-host resource-settings telemetry tests, GUI startup logger tests, packaged startup measurement script tests, GUI build-spec tests, native-host startup-log coverage, installed-bundle rebuild/validation, installed-bundle startup measurements, extension helper transport/localization contracts from the existing evidence set, and changed-scope repo safety
- Default behavior:
  - The GUI app now routes helper install/repair through a Browser Connections manager in the app menu and SRS settings instead of the older single environment prompt.
  - Fixed-ID production browsers keep a one-click connect/repair path.
  - Unpacked development extensions are managed separately through a narrow dialog that captures only browser + unpacked extension ID; the app uses the current workspace helper automatically for that browser.
  - Workspace-host installs now target a generated wrapper script that pins the repo interpreter, so browser launches from Finder/GUI shells do not depend on whichever `python3` happens to be on `PATH`.
  - Saved bundled/workspace browser connections now auto-repair a narrow set of deterministic stale states on startup and when `Connections...` opens: unreadable manifests, missing host paths, missing expected origins, stale bundled copies, and pre-wrapper/stale workspace-wrapper states.
  - Native-host startup/import failures now append a traceback to `logs/native_host.log` under the LexiShift data root, so browser-side `Native host has exited` failures have a deterministic local log instead of only a transient browser transport error.
  - Native-host resource-settings requests now log a startup session, activation timing, launch resolution, command class, `Popen` timing, and total native-host handoff timing; cold GUI launches receive the same session through `LEXISHIFT_STARTUP_SESSION_ID`.
  - GUI startup timing records now include session id, PID, parent PID, argv mode, launch source, launch mode, resource pair, UTC timestamps, and request-to-checkpoint timing when the GUI was launched by the native host.
  - The packaged GUI uses PyInstaller onedir bundles with `EXE(..., exclude_binaries=True)` and `COLLECT`-owned binaries/zipfiles/datas, so installed main/helper app size and warm relaunch latency are no longer dominated by duplicated executable payloads.
  - Native-messaging manifests now merge all allowed origins for the same browser into one manifest instead of assuming only one extension ID.
  - Same-browser prod and unpacked-dev entries still share one host path; the GUI only surfaces that as a targeted warning when an unpacked-dev change would switch a configured browser to the workspace host.
  - Helper install inspection now distinguishes `Configured`, `Needs repair`, and `Not configured`, including stale bundled-helper copies and legacy direct-script workspace manifests.
  - Manifest path, host path, and reveal actions are available only through an explicit technical-details toggle rather than the default card surface.
  - Background/bridge transport layers now classify common browser transport failures with stable codes, and options-side helper status/test/open flows localize timeout, browser-blocked native messaging, helper-missing, and host-exited cases instead of surfacing raw browser strings by default.
- Evidence:
  - `docs/architecture/native_messaging_design.md`
  - `apps/gui/src/helper_installer.py`
  - `apps/gui/src/helper_ui.py`
  - `apps/gui/src/main_menu_mixin.py`
  - `apps/gui/src/main_runtime.py`
  - `apps/gui/src/startup_logging.py`
  - `apps/gui/packaging/pyinstaller.spec`
  - `scripts/build/gui_app.py`
  - `apps/gui/src/dialogs.py`
  - `apps/gui/src/helper_connections_dialog.py`
  - `core/lexishift_core/helper/gui_startup_telemetry.py`
  - `scripts/helper/lexishift_native_host.py`
  - `scripts/dev/packaged_gui_startup_measure.py`
  - `apps/chrome-extension/background.js`
  - `apps/chrome-extension/shared/helper/helper_transport_extension.js`
  - `apps/chrome-extension/options/core/helper/base_methods.js`
  - `core/tests/dev/test_helper_installer_native_messaging.py`
  - `core/tests/dev/test_helper_browser_connections.py`
  - `core/tests/dev/test_extension_helper_error_localization_contract.py`
  - `core/tests/dev/test_native_host_startup_logging.py`
  - `core/tests/dev/test_native_host_resource_settings.py`
  - `core/tests/dev/test_packaged_gui_startup_measure.py`
  - `core/tests/dev/test_gui_app_build.py`
  - `apps/gui/tests/test_main_runtime_startup_logging.py`
  - `docs/test_outputs/dev_workflow/gui_startup_performance_open_latest.json`
  - `docs/test_outputs/dev_workflow/gui_startup_performance_activation_latest.json`
  - `docs/test_outputs/dev_workflow/gui_startup_performance_bundle_id_latest.json`
  - `docs/test_outputs/dev_workflow/gui_startup_performance_direct_latest.json`
- Known gaps:
  - Native messaging still uses one host manifest per browser name, so same-browser prod and unpacked-dev origins still share one host path.
  - Fixed-ID production rows only work in builds where `apps/gui/resources/helper_extension_ids.json` contains real non-placeholder production IDs.
  - The desktop app can verify manifest/origin/host freshness, but it still cannot prove that the browser extension is currently installed and active.
  - First launch immediately after reinstall/rebuild can still be materially slower than warm relaunch on the local machine; release signing/notarization and tester-machine measurements still need confirmation.

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

## Exact Gloss Demotion Overrides

- Status: `implemented`, `default-off`, `verified`
- Last documented checkpoint: `2026-04-04`
- Last verified: `2026-04-04` code inspection and canonical `en-es` / `en-de` benchmark artifact refresh
- Default behavior:
  - Disabled for helper defaults and canonical benchmark lanes.
  - Available only when `enable_exact_gloss_demotions` is explicitly enabled.
  - `semantic_demotion_scale` only modulates this override layer when enabled.
- Evidence:
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/rulegen/rulegen_congruity_implementation_plan.md`
  - `docs/rulegen/rulegen_lp_support_guide.md`
  - `core/lexishift_core/rulegen/semantic_demotion.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/pairs/en_ja.py`
  - `docs/test_outputs/rulegen_benchmark_summary_latest.md`
  - `docs/test_outputs/rulegen_benchmark_en_de_summary_latest.md`
- Known gaps:
  - The override map is exact phrase-level and should not be treated as a substitute for generalizable ranking signals.
  - Current `en-es` and `en-de` quality gaps still require richer ranking/source mechanisms.

## Reverse-Check Scoring

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-04-04` `en-de` now also wires reverse resource resolution, metadata emission, ranking consumption, and probe surface, with the first focused Kaikki reverse experiment recorded separately
- Last verified: `2026-05-16` root-dated rulegen evidence relocation moved the dated `en-es` reverse-check artifacts under `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/` and refreshed reverse-check routing without rerunning benchmark artifacts
- Default behavior:
  - Configurable and pair-aware for `en-es`, `es-en`, and `en-de`.
  - Not yet promoted to default production tuning.
  - Reverse-check-specific evaluation now has a named `en-es` lane via `npm --prefix scripts run quality:rulegen:reverse:en-es`.
  - Parameter-set comparison is now tracked in `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`.
  - `en-de` reverse-check is now available to the benchmark/probe seams, but remains off in the canonical advisory lane and off in the current best Kaikki lane.
  - Reverse scoring now also supports:
    - an exact-hit ambiguity penalty keyed off `reverse_check_total`
    - an additive exact-hit specificity bonus keyed off `reverse_check_total`
  - both signals are harness-exposed, but both are still off in the current canonical best run.
- Evidence:
  - `docs/rulegen/reverse_check_scoring_phase1.md`
  - `docs/rulegen/reverse_check_rollout_matrix.md`
  - `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`
  - `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
  - `docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`
  - `core/lexishift_core/rulegen/ranking.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/rulegen/tuning.py`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_probe_words.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_latest.md`
  - `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.md`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_off_latest.json`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_on_latest.json`
  - `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
  - `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `core/tests/dev/test_rulegen_probe_words.py`
- Known gaps:
  - `en-ja` still has no reverse-check implementation, and `en-de` has only a first local reverse experiment rather than a promoted pair lane.
  - No committed `es-en` benchmark/gate/triage artifact yet proves rollout maturity.
  - The first focused `en-de` Kaikki reverse experiment did not beat `rev=off`; the tested `rev=on` setting dropped top1 from `93.10%` to `91.38%` while leaving top3 flat at `96.55%`.
  - The canonical benchmark loop now sweeps both `rev=off` and `rev=on`, but `en-es` still remains red on top-1 accuracy and average-rule volume even after the repaired verb reverse normalization restored the best `rev=on` lane.
  - The current `en-es` reverse-enabled best run lifts `top3` to `98.25%`, but `top1` is still capped at `91.23%`; remaining work is now more about lexical choice than reverse plumbing.
  - The new exact-hit ambiguity penalty and exact-hit specificity bonus are both implemented and harness-exposed, but neither beat the existing best lane yet; current `cuadro` behavior is still more sensitive to miss/far-penalty tradeoffs and score clamping than to these exact-hit refinements alone.
  - `cuadro` still exposes a non-separable failure class for reverse evidence alone, and `sacar` still needs phrase-policy work when the benchmark is judged on top-1 quality rather than only top-3 recall.
  - Current rollout is scoring-only, not strict candidate blocking.

## Kaikki Provenance / Competition Scoring

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-27` provenance scoring with second benchmark-expansion pass and live Kaikki demotion now winning
- Last verified: `2026-04-04` targeted `en-es` provenance coverage plus new `en-de` adapter/probe tests and canonical `en-de` benchmark/gate/triage rerun
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
  - the current signal is now selected together with live Kaikki demotion, but it still does not solve `cuadro` or the new slang-side failures
  - `en-de` now has default-off Kaikki-policy scaffolding plus a strong local Kaikki advisory lane when a Wiktionary/Kaikki source is supplied, but there is still no promoted default source path or richer `en-es`-style provenance competition layer
  - `en-ja` and `es-en` do not yet have analogous provenance-scoring work
  - per-family Kaikki demotion strengths, gloss-decay shape exposure, and lexical short-phrase policy are still the next nearby sweep candidates

## Trait-Conditioned Rulegen Profiles

- Status: `planned`; runtime routing not implemented or verified
- Last documented checkpoint: `2026-04-11`
- Last verified: `2026-04-11` semantic-shadow feature-vector extraction/tests plus refreshed semantic-shadow matrix/compare artifacts
- Default behavior:
  - No runtime profile routing exists yet.
  - Current rulegen still uses one selected configuration per run rather than choosing profiles from runtime-computable target traits.
  - The intended future direction is to route among a small bank of named profiles using a shared feature extractor and benchmark-backed trait analysis.
- Evidence:
  - `docs/rulegen/trait_conditioned_rulegen_profiles.md`
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/language_pairs/kaikki_en_es_integration_plan.md`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_benchmark_presets.py`
  - `scripts/testing/rulegen_benchmark_bundle.py`
  - `scripts/testing/semantic_shadow_experiment_matrix_en_es.py`
  - `scripts/testing/semantic_shadow_experiment_compare_en_es.py`
  - `core/lexishift_core/rulegen/semantic_shadow_feature_vector.py`
  - `core/lexishift_core/rulegen/semantic_shadow_evaluation.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/kaikki_views.py`
  - `core/lexishift_core/rulegen/ranking.py`
- Known gaps:
  - There is no shared runtime trait extractor for the general rulegen benchmark yet; the new shared feature-vector surface currently exists only for the semantic-shadow veto analysis path.
  - The main rulegen benchmark artifacts still do not yet emit per-case feature vectors.
  - No profile bank or interpretable router is implemented.
  - Current dataset size is still better suited to coarse directional experiments than fine-grained routed-policy learning.
  - Learner-stage-aware routing is only conceptual at this point and must stay separate from lexical trait inference.

## Semantic Routing Runtime Admission Layer

- Status: `implemented`, `default-on-when-capable`, `verified`
- Last documented checkpoint: `2026-06-08` Learning Languages now exposes semantic/veto reference-pack status and a pair-level install/copy path for the current `en-es` reference pack while keeping `en-de` semantic reference coverage explicitly pending.
- Last verified: `2026-06-08` targeted semantic-pack install, source-stack, and GUI learning-pair setup tests; `2026-05-15` Lane 5 L5-E semantic inventory exception containment validation with focused semantic gate/runtime tests; `2026-05-16` routing-only evidence sync for semantic-shadow review queue path; `2026-06-06` route-only evidence sync from getting-started page to guide page
- Default behavior:
  - Semantic admission is no longer a normal user preference. The browser runtime auto-uses helper-side semantic admission only when the current pair/profile publication is actually capable of real semantic decisioning.
  - If a pair/profile has semantic metadata but no ready subset yet, LexiShift stays on standard SRS replacement behavior instead of asking the user to choose a fallback posture.
  - The repo now has passive semantic-routing publication scaffolding:
    - `metadata.semantic_admission` can be emitted on rules
    - helper publication can write a semantic inventory sidecar
    - helper publication now also writes a generation-aligned publication manifest for the ruleset/snapshot/semantic-inventory family
    - helper/native-host can now serve that semantic inventory as a first-class artifact
    - helper CLI/native-host can now materialize a compiled semantic pack into a profile-local publication family and pair-level pack copy, or copy only the pair-level pack for later rulegen enrichment, while requiring an explicit data root unless the caller explicitly opts into the platform default; the installer can resolve a named pack id from an installed pack copy, `LEXISHIFT_SEMANTIC_PACK_CATALOG`, or the current repo dev pack before falling back to a developer inventory-path override; the shared extension helper client and Advanced debug options flow now expose a named `installSemanticPack` route
    - pair capabilities can declare a default local semantic reference pack; normal SRS rulegen publication then uses an installed copy only as evidence enrichment for already-published source/replacement families, so a generated semantic pack can close ready-pointer gaps without widening or replacing the current Vocabulary Practice ruleset
    - GUI Learning Languages now uses the same source-stack/catalog model to show semantic pack state: `en-es` has an installable pair-level reference copy path, and `en-de` has an explicit non-blocking pending row because no comparable semantic reference pack is declared yet
    - extension helper cache/runtime can now persist and resolve semantic inventory in parallel with ruleset/snapshot
    - helper source-of-truth diagnostics can inspect pointer coverage, sidecar coverage, publication generation ids, and recomputed manifest-family state from the live helper artifacts
    - extension options/runtime diagnostics can surface best-effort cache counts plus cached snapshot/semantic generation ids and simple alignment, helper semantic capability/reason state, runtime semantic capability/pointer/ready counts, live semantic gate enablement, helper vs helper-cache source/error, aggregate ready/replace/abstain/soft-affordance counts, aggregate semantic fallback `reason_codes`, semantic helper batch/latency metrics, semantic scan scheduler metrics, DOM context-cache reuse metrics, and the last resolved `decision_policy_id` from the shipped runtime path
    - helper/native-host can now also answer `semantic_admit_batch` using a named shared policy registry, and the extension runtime can call that service when semantic admission is active
  - The shipped runtime gate is still intentionally conservative:
    - only SRS-origin rules that already carry `metadata.semantic_admission` are eligible
    - runtime activation now depends on computed capability (`active`, `published_unready`, `unavailable`, `error`) rather than a visible toggle
    - the shipped runtime defaults to `abstain_on_unavailable` for ready-rule inventory/helper failure cases, so unavailable semantic scoring fails closed instead of silently allowing replacement
    - thrown semantic inventory-resolution and helper decision-service exceptions are contained inside the semantic gate and become existing fail-closed fallback reason codes instead of rejecting the page scan
    - `legacy_on_unavailable` remains an accepted explicit compatibility policy, but it is not the default runtime/profile posture
    - `selection_mode=active_only` is now an explicit ready competition-set shape for active-only cue evidence with no shadows; for `en-es`, active-only inventories auto-select `en_es_sentence_veto_v2` when the request does not provide a decision-policy override, while ordinary `automatic`, `manual`, and `mixed` ready competition sets still require real shadow senses
    - the schema still reserves `soft_affordance` as a future optional non-replace outcome, but current DOM behavior only acts on `replace` and otherwise keeps the original text
  - The browser extension options page now exposes a read-only semantic-admission status row:
    - `Automatic`
    - `Not yet available`
    - `Unavailable`
    - `Needs repair`
  - Current implemented E2E is now explicit:
    - offline helper artifacts stay local
    - extension loads ruleset plus semantic inventory from helper/cache
    - lexical trie matching happens first
    - semantic admission activates only when the current enabled SRS rules have nonzero `status=ready` coverage and semantic inventory resolves cleanly
    - eligible matches are counted, but only `status=ready` eligible matches are batched to helper `semantic_admit_batch`
    - fallback decisions now roll up reason-code counts such as `semantic_status_pending`, `semantic_inventory_unavailable`, and `decision_service_error` into runtime diagnostics without changing replacement behavior
    - ready semantic helper requests use bounded block/sentence-window DOM context when inline markup splits the visible sentence across text nodes, with scan-local context-buffer reuse for small complete blocks, same-context helper-call coalescing, pair/profile inventory-resolution reuse across serial admissions, explicit `fit_scope=per_match` batching across different context strings, and two-phase semantic preflight for budgeted scans so TF-IDF-style scoring keeps one-match semantics while native helper calls are reduced; the default semantic scan node batch is now `96` with no helper flush delay, based on the live Castle first-visible/throughput tuning; replacement edits remain scoped to the original text node and final page-budget enforcement remains ordered
    - non-ready eligible matches still resolve locally through the shipped internal legacy fallback posture
    - runtime replaces only `replace` decisions and keeps the original otherwise
  - `en-es` now has a narrow publication PoC:
    - if real sibling senses for the same trigger are present either in the active emitted ruleset or in the broader initialize/refresh semantic-context pool, `metadata.semantic_admission.status` can be promoted to `ready` for the active rules without widening the visible SRS ruleset
    - the semantic inventory then publishes `competition_sets` with `selection_mode=automatic` and `selection_policy_version=en_es_emitted_rule_siblings_v1`
    - active-only generated cue rows can be tested through an isolated helper fixture using `selection_mode=active_only` and a generation-aligned ruleset/snapshot/semantic-inventory/manifest family
  - That PoC is intentionally limited to emitted siblings reachable from helper-side initialize/refresh context; it is not broad shadow mining, phrase-preemption publication, or LP-parity runtime readiness.
  - `en-es` now also has a research-only shadow inventory path:
    - `scripts/testing/semantic_shadow_inventory_en_es.py` mines sibling candidates from reviewed benchmark trigger phrases plus installed translation packs
    - `scripts/testing/semantic_shadow_inventory_triage_en_es.py` scores the resulting preview into `benchmark_aligned`, `same_pos_only`, and `no_promotion` buckets
    - `scripts/testing/semantic_shadow_policy_compare_en_es.py` compares named promotion policies (`same_pos_lenient_v1`, `benchmark_backed_v1`, `cross_checked_v1`, `cross_checked_backoff_missing_active_v1`)
    - `scripts/testing/semantic_shadow_policy_gap_queue_en_es.py` isolates the small set of rows that the stricter policy still drops
    - `scripts/testing/semantic_shadow_review_queue_en_es.py` builds the focused provisional keep-row queue consumed by the review-packet generator
    - `scripts/testing/semantic_shadow_review_packet_en_es.py` combines the policy snapshot, provisional keep rows, and provisional drop rows into one adjudication packet
    - `scripts/testing/semantic_shadow_gold_proxy_en_es.py` grades the current policies against a reviewed-trigger-overlap gold proxy derived directly from `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
    - `scripts/testing/semantic_shadow_coverage_gap_en_es.py` explains the strict-policy underblocked rows by comparing them against current inventory and rulegen benchmark source lists
    - `scripts/testing/semantic_shadow_seed_compare_en_es.py` holds the miner and strict promotion policy fixed while swapping only the seed trigger source (`benchmark_reviewed`, `rulegen_top3_sources`, `rulegen_all_sources`)
    - `scripts/testing/semantic_shadow_forward_seed_sweep_en_es.py` sweeps the new source-only forward-gloss trigger-length knob on top of the strict seed compare
    - `scripts/testing/semantic_shadow_support_score_sweep_en_es.py` now sweeps a small explicit support score over threshold and `max_promoted_shadows`, rather than adding more named promotion branches
    - `scripts/testing/semantic_shadow_trigger_support_sweep_en_es.py` now sweeps a compact trigger-support score before mining, while keeping the downstream shadow support policy fixed
    - the latest artifacts confirm that candidate mining works broadly enough to study, and the safer provisional runtime shape is now effectively the strict `cross_checked_v1` family: after active-side bundled-trigger matching was fixed, `cross_checked_backoff_missing_active_v1` no longer widens the promoted set and `coger / catch -> vista` falls out of the review queue
    - the new gold-proxy artifact gives the first explicit lower-bound grading surface for automation quality, without claiming sentence-level semantic-veto readiness
    - the latest miner improvement supplements reverse-headword candidates with benchmark-target forward-gloss matches for the same English trigger, which recovers real misses like `sacar/remove`, `malla/net`, and `cuadro/table`
    - current lower-bound read from that proxy:
      - `cross_checked_v1` / `cross_checked_backoff_missing_active_v1`: `64.3%` candidate precision, `90.0%` candidate recall, `90.0%` gold-trigger hit rate, `3.6%` overblocking rate
      - candidate-pool recall is now `90.0%`, which means the remaining bottleneck is concentrated in harder semantic-bridge cases like `cargo/job`, not simple reverse-pack asymmetry
    - the newest gap audit confirms that remaining bottleneck explicitly:
      - only `trabajo / job -> cargo` remains underblocked on the overlap proxy
      - current classification is `semantic_bridge_needed`, not `rulegen_source_gap`
    - the newest de-coupling compare makes the current benchmark dependence explicit:
      - `benchmark_reviewed`: `64.3%` precision / `90.0%` recall / `3.6%` overblocking
      - `rulegen_top3_sources`: `36.4%` precision / `40.0%` recall / `5.1%` overblocking
      - `rulegen_all_sources`: `33.3%` precision / `40.0%` recall / `5.8%` overblocking
      - interpretation: current shadow mining is not relying on manual per-target hacks, but it still depends materially on reviewed-trigger seeding; the next work is better automatic trigger seeding, not a looser blocker policy
    - the newest source-only augmentation lane closes much of the recall gap without adding manual data:
      - `rulegen_top3_plus_forward_gloss` / `rulegen_all_plus_forward_gloss` now reach `80.0%` candidate recall and `80.0%` gold-trigger hit rate on the lower-bound proxy, but only at `32.0%` precision with `9.4%` overblocking
      - the numeric forward-seed sweep shows the current best source-only setting is `forward_seed_max_words=1`; allowing longer phrase fragments does not improve recall on the current proxy and only worsens overblocking
    - the new support-score sweep provides the first compact numeric promotion surface:
      - for the reviewed-trigger control, the support score now exposes a real numeric safety/coverage ladder:
        - `min_score=3`, `max_promoted=1`: `20.0%` precision / `90.0%` recall / `26.1%` overblocking
        - `min_score=5`, `max_promoted=1`: `100.0%` precision / `80.0%` recall / `0.0%` overblocking
      - for the best current source-only lane, `min_score=5` and `max_promoted=2` improves the old strict baseline materially without adding manual data:
        - `rulegen_top3_plus_forward_gloss` / `rulegen_all_plus_forward_gloss`: `47.1%` precision / `80.0%` recall / `5.1%` overblocking
        - prior `cross_checked_v1` baseline on that lane: `32.0%` precision / `80.0%` recall / `9.4%` overblocking
      - interpretation: support-scored promotion is now a real numeric control surface for safety vs coverage, and a better next control surface than inventing more branchy named policies
    - the refreshed trigger-support sweep clarifies where earlier automatic-seed noise lives:
      - on `rulegen_top3_plus_forward_gloss`, `min_trigger_score=3` only helps relative to a much noisier downstream threshold (`shadow min=4`, `max_promoted=2`):
        - precision `8.0% -> 13.6%`
        - recall stays `80.0%`
        - overblocking `43.5% -> 23.9%`
      - on `rulegen_all_plus_forward_gloss`, the same trigger filter is too destructive:
        - precision `8.0% -> 14.3%`
        - recall `80.0% -> 20.0%`
        - inventory coverage `90.0% -> 50.0%`
      - interpretation: trigger filtering remains an upstream cleanup knob, but it is no longer the best frontier; higher downstream support thresholds still dominate it on the current miner
    - the new lexical-frequency sweep shows that a soft Spanish target-frequency prior does not currently improve the best lexical baseline:
      - `scripts/testing/semantic_shadow_frequency_sweep_en_es.py` keeps the current best source-only lane fixed and only adds a representative bonus for the most frequent shadow targets within each trigger bucket
      - best current source-only row remains unchanged at `47.1%` precision / `80.0%` recall / `5.1%` overblocking
      - higher frequency bonuses actively hurt precision and overblocking
      - the follow-on active-vs-shadow frequency-similarity sweep also leaves the best row unchanged:
        - best source-only setting still keeps `sim_weight=0.0`
        - positive similarity weights are effectively inert on the current reviewed overlap proxy
      - interpretation: target-side frequency is still worth preserving as optional metadata, but the current `freq-es-cde` pack does not justify making either raw frequency or frequency-band similarity a default blocker-selection signal
    - the new representative-pruning sweep shows that one obvious condensation idea is not the current bottleneck:
      - `scripts/testing/semantic_shadow_representative_pruning_sweep_en_es.py` collapses same-POS shadow candidates that share the same normalized `sense_label`, then keeps the highest-scoring representative from each cluster
      - on the current reviewed overlap proxy, that leaves the best rows unchanged:
        - reviewed control still prefers `off` at the current best `100.0%` precision / `80.0%` recall operating point
        - best source-only row also still prefers pruning `off`, staying at `47.1%` precision / `80.0%` recall / `5.1%` overblocking
      - interpretation: redundant same-sense variants exist in the raw inventory, but the present support threshold is already filtering most of them before they affect the reviewed denominator
    - the new lower-bound veto-proxy comparison is the first direct `curated_shadows` vs `auto_shadows` product-shape check:
      - `scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py` converts the reviewed overlap rows into proxy `allow` / `abstain` decisions and compares `curated_shadows`, `reviewed_auto_shadows`, `auto_shadows`, and `no_shadows`
      - current `en-es` read:
        - `curated_shadows`: `100.0%` abstain recall / `0.0%` harmful allow / `0.0%` overblocking
        - `reviewed_auto_shadows`: `80.0%` abstain recall / `20.0%` harmful allow / `0.0%` overblocking
        - `auto_shadows`: `80.0%` abstain recall / `20.0%` harmful allow / `5.1%` overblocking
        - `no_shadows`: `0.0%` abstain recall / `100.0%` harmful allow / `0.0%` overblocking
      - interpretation: the current source-only shadow lane already recovers most of the lower-bound veto benefit over `no_shadows`, and the remaining gap is concentrated in the unresolved `job` family rather than a broad collapse of blocker discovery
    - the first target-card embedding bridge has now been swept explicitly:
      - `scripts/testing/semantic_shadow_embedding_bridge_sweep_en_es.py` augments the current inventories with sentence-transformer nearest neighbors over source-derived target cards, but only as a backoff candidate source
      - it can recover `trabajo / job -> cargo` at the lower support threshold (`min_score=4`), raising source-only recall from `80.0%` to `90.0%`
      - that gain is not currently worth the noise:
        - `rulegen_top3_plus_forward_gloss` baseline best lexical row stays `47.1%` precision / `80.0%` recall / `5.1%` overblocking
        - best embedding-bridge row falls to `11.8%` precision / `90.0%` recall / `35.5%` overblocking
      - at the safer lexical threshold (`min_score=5`), the bridge does not improve recall, because the remaining `cargo / job -> trabajo` miss still has no active-side support
      - interpretation: nearest-neighbor target cards are useful as a research recall probe, but not yet a publishable improvement over the lexical baseline
    - the matrix harness now exposes explicit source toggles for the newly approved source families:
      - `semantic_bridge_include_aux_text`
      - `semantic_bridge_include_examples`
    - the matrix and compare runners now also accept explicit translation-pack overrides:
      - `--translation-dict`
      - `--reverse-translation-dict`
      - intended use: replay rebuilt or temporary source artifacts without overwriting installed packs
    - current local `en-es` read on those rows stays flat versus the lexical control even after refreshing the forward source artifact:
      - `promotion_semantic_bridge_aux_text_on` matches `source_only_borrowed`
      - `promotion_semantic_bridge_aux_text_examples_on` also leaves veto metrics flat, while lowering gold precision from `78.6%` to `75.9%`
      - the installed `wiktionary-es-en.sqlite` forward pack is older than the new example-preserving schema and exposes `0 / 453` benchmark-target forward records with examples
      - rebuilding the same forward pack from the local `raw-wiktextract-data.jsonl.gz` raises that benchmark-target availability to `132 / 453` records across `45` targets
      - interpretation: forward example absence was a stale-pack issue, not a source-limitation issue, but the current examples bridge still adds mostly extra candidate mass rather than the missing blockers we need
	  - The next broadening step is now explicit rather than ad hoc:
	    - `docs/rulegen/semantic_shadow_source_intake_plan.md` defines the operating model for source-heavy experimentation
	    - `docs/test_inputs/semantic_shadow_source_registry.json` tracks current and proposed source families together with approval state, role, and runtime-publishability
	    - the intended discipline is broad offline ingestion plus narrow runtime publication, with one coverage-heavy and one discrimination-heavy source family approved at a time
	  - The intended future direction is a conservative admission layer that can choose among:
	    - hard replace
	    - soft affordance / annotation
	    - abstain
	  - The governing product preference for that future layer is explicit:
	    - false abstain is cheaper than harmful replacement
	  - The repo now also has a research-only sentence-level runtime-veto harness:
	    - `scripts/testing/semantic_routing_sentence_veto_harness.py` evaluates one fixed active-vs-shadow scorer configuration over a curated sentence dataset
	    - `scripts/testing/semantic_routing_sentence_veto_sweep.py` sweeps scorer family, context view, evidence view, and threshold ladders over that same fixed dataset
	    - the current `en-es` fixed-shadow evaluation dataset lives at `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
	    - the current first `en-ja` fixed-shadow breadth evaluation dataset lives at `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_breadth_v1.json`
	    - this harness explicitly measures runtime-scoring quality separately from upstream shadow-mining quality
	    - the default sweep stays on the cheap lexical scorer family, while `sentence_transformer_cosine` is available as an explicit heavier model-choice lane
	    - the shipped ordinary `en-es` helper runtime now defaults to the deployable lexical gate via `en_es_sentence_veto_v2` (`tfidf_cosine + masked_sentence + all_evidence_text + min_active=0.015 + min_margin=0.00`); the heavier `en_es_sentence_veto_v3` sentence-transformer lane remains explicit because it requires model/dependency availability
	  - First current lexical result on that harness:
	    - the original higher threshold ladder (`min_active >= 0.25`) collapses to total abstention
	    - once the sweep includes `min_active_score=0.00` and `0.05`, the best zero-harmful lexical control row was `tfidf_cosine + masked_sentence + all_evidence_text + min_active=0.05 + min_margin=0.00`; the current active-only product-smoke posture deliberately lowers that floor to `0.015` to reduce false abstains after live-page review accepted some harmful-replace risk
	    - on the expanded `v10` dataset, that row reaches `73.7%` decision accuracy with `0.0%` harmful replace, `100.0%` replace precision, and `34.2%` replace recall on the current 95-case curated dataset
	  - First current model-choice result on that harness:
	    - the shipped `v3` sentence-transformer default is still the bounded runtime experiment, but the active `v10` evaluation slice still does not show a clean hard-replace story
	    - on `v10`, the same `masked_sentence + all_evidence_text + noun_family_frame_guard + sense_label_near_tie_active_rescue + min_active=0.00 + min_margin=0.00` row reaches `89.5%` decision accuracy with `1.8%` harmful replace, `96.7%` replace precision, `76.3%` replace recall, `88.2%` winner accuracy, and `100.0%` shadow-winner accuracy
	    - the current hard errors on the fixed-shadow `v10` slice are:
	      - harmful replace: `en-es:sentence-veto:play:005`
	      - false abstains: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:check:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`, `en-es:sentence-veto:report:001`, `en-es:sentence-veto:report:002`
	    - the corrected zero-noise soft ladder has collapsed on `v10`:
	      - best zero-noise row is `soft:a=0.60:m=0.00`
	      - it adds `0` soft true positives and `0` soft false positives
	    - the widened rescue overlay also remains non-clean on `v10`, because the same `play:005` row remains harmful
	    - first English-centric challenger `sentence-transformers/all-MiniLM-L6-v2` remains worse as a gate than the multilingual default lane
	    - `report` does not reopen the phrase-leak seam on the current strong runtime row; `report back` is already safely abstained, while `report:001` and `report:002` widen the held-out weak-active-support residue
	    - the current testing-only phrase-leak probe now isolates a stronger bounded candidate:
	      - active-sense noun phrase guarding on mixed noun/verb families
	      - it removes `play:005` on both the hard row and the widened overlay
	      - it now also cleanly phrase-preempts `watch:005`, `check:005`, `order:005`, `trip:005`, and `report:005`
	      - it preserves the existing rescue wins
	      - the held-out review is now more precise:
	        - the active-sense hard lane removes the harmful replace ceiling without improving the conservative hard corridor
	        - the active-sense overlay removes the harmful replace ceiling without giving back the current overlay corridor
	      - so the active-sense overlay is now the preferred bounded experiment, but this is still an evaluation/reference candidate rather than a shipped policy change
	    - current runtime-eval frontier is therefore no longer phrase-leak diagnosis by itself; it is frozen-queue cue-data preparation:
	      - keep the hard reference and accepted active-sense overlay fixed
	      - treat `play` as the phrase-risk negative control
	      - treat `check:002`, `order:002`, `trip:002`, `report:001`, and `report:002` as the current held-out weak-active-support residue
	      - the new `example_sentence_bank` feasibility pilot shows no queued-family example rows on the current installed packs
	      - the new reverse-aux-text pilot now lands that last cheap control:
	        - `reverse_aux_plus_all_evidence` improves the frozen queue-slice point read without widening the current harmful count
	      - the new prompt-spec plus smoke harness now freeze the first wording bundle too:
	        - proxy `gpt-5.4-mini`
	        - target `gpt-5.4`
	        - `6` concrete request rows across the `2` active cue slots
	      - after the first live proxy review, the frozen prompt contract was simplified:
	        - the model now emits only `evidence_text`
	        - optional `confidence` remains allowed
	        - the runner synthesizes all fixed ids and sense metadata into the stored intake row
	      - that keeps prompt output cheaper and less fragile while preserving the same stored provenance
	      - the simplified `semantic_prompt_bakeoff_v2` contract has now also passed a real live proxy run:
	        - `6 / 6` accepted and normalized
	        - input tokens dropped from `3414` to `2545`
	        - output tokens dropped from `1137` to `222`
	        - the cross-POS slot shifted from broad noun-gloss cues toward determiner/preposition/document framing
	      - the same simplified contract has now also passed a real live `gpt-5.4` target run:
	        - `6 / 6` accepted and normalized
	        - token volume stayed close to proxy (`2545` input, `231` output)
	        - the frame-sensitive cross-POS behavior persisted on the target model
	      - so the main remaining acceptance gate is no longer prompt confirmation:
	        - it is downstream effect on the fixed-shadow runtime slice
	      - that downstream bakeoff is now also landed:
	        - `scripts/testing/semantic_llm_prompt_downstream_en_es.py`
	        - `docs/test_outputs/semantic_llm_prompt_downstream_latest.md`
	      - current downstream read is negative for tranche promotion:
	        - the intended safe additive lane, `llm_cue_plus_all_evidence`, stays flat on both the hard reference and the active-sense overlay
	        - on the hard row it remains `77.5%` decision accuracy / `50.0%` replace recall / `1` harmful / `8` false abstains
	        - on the active-sense overlay it remains `80.0%` / `50.0%` / `0` / `8`
	        - it fixes `drink:002`, but introduces `drink:001`, so there is no net false-abstain gain
	      - the frozen reverse-aux control still wins:
	        - hard row `82.5%` / `62.5%` / `1` / `6`
	        - active-sense overlay `85.0%` / `62.5%` / `0` / `6`
	      - the stronger LLM diagnostic insertions do show signal, but not safely:
	        - `llm_cue_plus_sense_label` and `llm_cue_plus_gloss` both reach `62.5%` replace recall
	        - but both widen harmful replace from `1` to `3`
	      - current conclusion:
	        - keep the simplified `semantic_prompt_bakeoff_v2` output contract as the incumbent storage shape
	        - keep the accepted `gpt-5.4` cue tranche in analysis-only status
	        - do not approve broader cue-generation spend until a new prompt shape beats both the hard baseline and the reverse-aux control downstream
	      - that next prompt shape is now prepared as a bounded challenger matrix rather than just a note:
	        - prompt version `semantic_prompt_bakeoff_v3`
	        - `4` active cue slots and `12` proxy requests on the same frozen `v10` queue
	        - incumbent slots:
	          - `cue_contrastive_general_v1`
	          - `cue_cross_pos_frame_v1`
	        - overlap challengers:
	          - `cue_contrastive_overlap_v1`
	          - `cue_cross_pos_overlap_v1`
	        - next paid decision is therefore narrow:
	          - cheap proxy comparison first
	          - then another target-model pass only for slots that beat the incumbents
	      - that cheap proxy comparison has now also run:
	        - `12 / 12` requests accepted and normalized
	        - token volume stayed small enough for a bounded screening pass (`5370` input / `414` output)
	        - the overlap challengers are the first prompt variants that visibly move toward literal overlap-bearing evidence:
	          - `soil, water, leaves, roots, sunlight`
	          - `your online order for delivery`
	          - `annual report with findings, results, and recommendations`
	        - the incumbent slots remain readable, but still rely more on meta-language like `preceded by a determiner`
	      - the narrowed overlap target confirmation has now also run:
	        - only `cue_contrastive_overlap_v1` and `cue_cross_pos_overlap_v1` were carried forward
	        - `6 / 6` requests accepted and normalized on `gpt-5.4`
	        - token usage stayed bounded (`2825` input / `179` output)
	        - target outputs preserved the intended literal-overlap shape:
	          - `green leaves, roots in soil`
	          - `write a check to pay the rent`
	          - `the final report on findings and results`
	      - the refreshed downstream acceptance read is still negative for promotion:
	        - `Hard LLM cue plus all evidence` regresses the hard lane to `72.5%` decision accuracy / `50.0%` replace recall / `3` harmful / `8` false abstains
	        - the active-sense overlay remains flat at `80.0%` / `50.0%` / `0` / `8`
	        - the only fixed false abstain in the safe additive lane is `order:002`, while `drink:001` is introduced
	        - stronger LLM-only diagnostic lanes show recall but widen harmful replace to `5`
	        - `reverse_aux_plus_all_evidence` remains the better control at `82.5%` / `62.5%` / `1` / `6` on the hard row and `85.0%` / `62.5%` / `0` / `6` on the active-sense overlay
	      - current conclusion:
	        - both accepted target cue tranches remain analysis-only
	        - do not approve broader cue-generation spend from the current prompt matrix
	        - stop prompt-only iteration until a downstream insertion, source-data, or evaluation-lane change explains how the next spend can beat both the frozen hard reference and the reverse-aux control
	      - the new no-spend failure diagnostic now preserves that explanation:
	        - `scripts/testing/semantic_llm_prompt_failure_diagnostic_en_es.py`
	        - `docs/test_outputs/semantic_llm_prompt_failure_diagnostic_latest.md`
	        - reverse-aux remains the current control at `82.5%` accuracy / `62.5%` replace recall / `1` harmful / `6` false abstains
	        - active-only reverse-aux drops to `80.0%` / `56.2%` / `1` / `7`, so shadow-side auxiliary evidence is material
	        - `llm_cue_plus_all_evidence` stays worse at `72.5%` / `50.0%` / `3` / `8`
	        - reverse-aux plus LLM cue is identical to reverse-aux alone, so the accepted LLM cue text adds no incremental downstream value once source-derived active/shadow evidence is present
	        - LLM rescue-only probes also fail to beat the reverse-aux control
	      - the new no-spend source/insertion probe now makes the next source shape explicit:
	        - `scripts/testing/semantic_llm_source_insertion_probe_en_es.py`
	        - `docs/test_outputs/semantic_llm_source_insertion_probe_latest.md`
	        - full symmetric reverse-aux remains the only winning no-spend lane at `82.5%` / `62.5%` / `1` / `6`
	        - active-only reverse-aux is weaker at `80.0%` / `56.2%` / `1` / `7`
	        - shadow-only reverse-aux is weaker and less safe at `77.5%` / `56.2%` / `2` / `7`
	        - active LLM cues plus reverse-shadow calibration are still unsafe/weak at `72.5%` / `56.2%` / `4` / `7`
	        - hard reviewed example frames remove all false abstains but reopen phrase leaks at `92.5%` / `100.0%` / `3` / `0`
	        - active-guard reviewed example frames reach `100.0%` / `100.0%` / `0` / `0` as an internal non-runtime upper bound
	      - the new no-spend prototype-admission probe keeps the UX binary while testing a more fundamental internal scorer shape:
	        - `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`
	        - `docs/test_outputs/semantic_llm_prototype_admission_probe_latest.md`
	        - `docs/test_outputs/semantic_llm_prototype_admission_probe_expanded_latest.md`
	        - active/shadow/phrase-control reviewed examples are scored as competing prototypes, then reduced to `replace` or `abstain`
	        - the frozen queue clears at `100.0%` / `100.0%` / `0` / `0`
	        - active/shadow prototypes plus active-sense phrase guarding still leak `ball:005` and `match:005` on the expanded full-`v10` read at `97.9%` / `100.0%` / `2` / `0`
	        - adding phrase-control examples as abstain prototypes clears the expanded full-`v10` oracle read at `100.0%` / `100.0%` / `0` / `0`
	        - the canonical intake/evidence schema path now accepts `relation_type=phrase_control_example`, the `phrase_containment` role, and explicit `llm` / `external` / `internal` source types, with normalization still forcing `runtime_publishable=false`
	        - the no-spend example-frame contract gate now makes both the positive fixture and old active-only failure explicit:
	          - `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py`
	          - `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py`
	          - `scripts/testing/semantic_llm_example_frame_contract_en_es.py`
	          - `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py`
	          - `scripts/testing/semantic_llm_example_frame_generation_run_en_es.py`
	          - `scripts/testing/semantic_example_frame_batch_merge_en_es.py`
	          - `scripts/testing/semantic_llm_example_frame_generation_quality_gate_en_es.py`
	          - `docs/test_outputs/semantic_llm_example_frame_contract_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_contract_required_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_contract_expanded_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_contract_overlap_latest.md`
	          - `docs/test_outputs/semantic_reverse_aux_example_frame_contract_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_generation_run_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_generation_contract_latest.md`
	          - `docs/test_outputs/semantic_llm_example_frame_generation_quality_gate_latest.md`
	          - the reviewed frozen fixture is contract-complete at `8 / 8` families and the full-`v10` fixture is contract-complete at `19 / 19` families
	          - the current overlap target batch remains a negative read with `0 / 6` complete families because all six families lack shadow and phrase-control example rows
	          - the real external reverse-aux batch remains a negative required-family read with `0 / 8` complete families: active aux exists for all six target families, shadow aux exists for four, and phrase-control rows are absent
	          - the missing-row generation plan is no-spend and exact: `1` active example for `play`, `2` shadow examples for `plant`/`check`, and `8` phrase-control examples, with prompt input limited to trigger text, active/shadow sense labels and glosses, and queue role/archetype/notes rather than reviewed case sentences or translation targets
	          - the live missing-row generation run accepted and normalized `11 / 11` rows, and the merged batch is structurally complete at `8 / 8` required families with `24` rows
	          - the generated batch remains analysis-only because the quality gate rejects it: best containment-aware prototype config is `67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains
	          - the phrase-control ablation now separates the failure modes: broad semantic phrase prototypes put phrase-overreach pressure on `12` active false-abstain rows and directly add `2` incremental false abstains beyond the active-guard baseline, while containment-gated phrase evidence creates `0` incremental false-abstains and `2` correct containment hits
	          - the residual remediation planner now converts those containment-aware failures into `8` no-spend requests: `7` active examples for the `11` false-abstain cases and `1` shadow example for the `2` harmful `report` cases
	          - the residual source lane is now executed and filtered:
	            - `scripts/testing/semantic_llm_example_frame_leakage_audit_en_es.py`
	            - `docs/test_outputs/semantic_llm_example_frame_remediation_run_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_leakage_audit_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_run_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_leakage_audit_latest.md`
	            - the first residual pass accepted `8 / 8` rows and the second replayed/rekeyed pass accepted `6 / 6`; benchmark-leakage admission filtered out one `plant` row from each pass before merge
	          - the prototype probe now has a surface-POS guard:
	            - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_prototype_admission_probe_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_quality_gate_latest.md`
	            - the best generated-source config is now `prototype_reviewed_examples_surface_pos_rescue_guard`
	            - it keeps the UX binary and phrase-control containment-only, then uses local surface syntax to rescue noun-frame active cases and preempt verb-frame shadow cases
	            - it clears the prototype-quality gate at `95.0%` accuracy / `87.5%` recall / `0` harmful / `2` false abstains with `8 / 8` required families complete
	          - the post-promotion-candidate plant source check is negative:
	            - `docs/test_outputs/semantic_llm_example_frame_balanced_remediation_generalization_probe_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_plan_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_leakage_audit_latest.md`
	            - `docs/test_outputs/semantic_llm_example_frame_plant_remediation_v2_leakage_audit_latest.md`
	            - the full-`v10` generalization read keeps the surface-POS guard at `0` harmful replacements, but recall outside the frozen queue is source-coverage-limited
	            - the remediation planner now tracks the current best remediation guard and reduces the next source plan to `1` active `plant` request
	            - both bounded live plant attempts were structurally accepted but rejected by canonical benchmark-leakage admission, so the quality-gate numbers do not improve beyond the prior `95.0%` / `87.5%` / `0` / `2`
	        - the prototype-admission probe now consumes the normalized reviewed evidence batches directly, not only the sentence-veto dataset oracle path
	        - the prototype-admission probe also consumes the normalized reverse-aux evidence batch as a real external-source comparison and currently reads `67.5%` accuracy / `50.0%` recall / `5` harmful / `8` false abstains
	      - next technical direction:
	        - source/insertion work before any further prompt spend
	        - prioritize competition-symmetric active/shadow example-frame sets rather than missing-row-only fills
	        - keep phrase-control examples as a first-class source requirement, but treat generated phrase examples as local containment patterns or separately gated abstain evidence rather than broad semantic competitors
	        - rerun the failure diagnostic, source/insertion probe, and prototype-admission probe as no-spend gates before reopening paid generation
	      - the live prompt runner now exists too:
	        - `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`
	        - it preserves immutable raw response bundles plus raw and normalized batch artifacts under `docs/test_outputs/experiments/semantic_llm_prompt_batches/`
	      - the repo now also has a no-spend preflight surface:
	        - `scripts/testing/semantic_llm_prompt_preflight_en_es.py`
	        - `docs/test_outputs/semantic_llm_prompt_preflight_latest.md`
	        - narrowed preflight command examples now preserve selected `--request-id` filters instead of relying only on request-count guards
	      - the repo now also has a no-spend cost-estimate surface:
	        - `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py`
	        - `docs/test_outputs/semantic_llm_prompt_cost_estimate_latest.md`
	      - the same runner now also has a no-spend replay rehearsal path:
	        - `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`
	        - `docs/test_outputs/semantic_llm_prompt_replay_latest.md`
	      - the live runner now requires explicit `--execute-live`
	      - live spend is now also fail-closed on:
	        - exact selected-request-count declaration
	        - explicit pricing inputs
	        - explicit estimated cost ceiling
	      - live execution is now also resume-safe by explicit operator choice:
	        - each paid run is keyed by `--run-id`
	        - completed per-request outcomes are appended to a journal under `docs/test_outputs/experiments/semantic_llm_prompt_batches/`
	        - reruns without `--resume` are rejected over an existing journal
	        - `--resume` reuses completed outcomes but refuses ambiguous started-without-outcome requests
	      - the preflight artifact now prints a spend-capped live command template rather than an uncapped one
	      - so prompt bakeoff work is now a real preserved execution surface, not just a plan
	      - the replay rehearsal has already proven the core plumbing:
	        - one accepted request survives into raw, intake, and normalized artifacts
	        - one malformed request stays raw-only and is rejected
	        - one forced API failure is counted separately without corrupting the batch
	      - the current remaining blocker is downstream acceptance, not runner/quota plumbing:
	        - the Codex command shell still does not inherit `OPENAI_API_KEY` automatically, but the preflight artifact keeps the sourced-shell + repo-venv path explicit
	        - the sourced-shell + repo-venv live path is now proven on both proxy and target batches
	        - latest target-overlap preflight volume was `3155` heuristic input tokens and `540` heuristic expected output tokens
	        - actual target-overlap usage was `2825` input tokens and `179` output tokens
  - Before any rollout, the project still needs:
    - active-sense provenance carried from rulegen into runtime-consumable metadata
    - automatic sibling-shadow candidate mining and a small promotion policy
    - phrase/idiom preemption as a separate lane from semantic veto
    - runtime observability for why a replacement applied or abstained
- Evidence:
  - `docs/developer/productization_lane3_feature_state_truth_inventory.md`
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
  - `docs/rulegen/semantic_shadow_source_intake_plan.md`
  - `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md`
  - `docs/rulegen/semantic_routing_publication_contract.md`
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/architecture/extension_system_map.md`
  - `docs/guide/index.md`
  - `docs/srs/srs_roadmap.md`
  - `core/lexishift_core/replacement/core.py`
  - `core/lexishift_core/persistence/storage.py`
  - `core/lexishift_core/helper/paths.py`
  - `core/lexishift_core/helper/rulegen_outputs.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `core/lexishift_core/helper/use_cases/semantic_admission.py`
  - `core/lexishift_core/rulegen/semantic_publication.py`
  - `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py`
  - `scripts/testing/semantic_llm_prompt_preflight_en_es.py`
  - `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py`
  - `scripts/testing/semantic_llm_prompt_downstream_en_es.py`
  - `scripts/testing/semantic_llm_prompt_failure_diagnostic_en_es.py`
  - `scripts/testing/semantic_llm_source_insertion_probe_en_es.py`
  - `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`
  - `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py`
  - `scripts/testing/semantic_llm_example_frame_contract_en_es.py`
  - `core/lexishift_core/rulegen/semantic_evidence.py`
  - `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
  - `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`
  - `core/lexishift_core/rulegen/semantic_shadow_inventory.py`
  - `core/lexishift_core/rulegen/semantic_shadow_frequency.py`
  - `core/lexishift_core/rulegen/semantic_shadow_embedding_bridge.py`
  - `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
  - `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
  - `core/lexishift_core/rulegen/semantic_shadow_evaluation.py`
  - `core/lexishift_core/rulegen/semantic_shadow_representative_pruning.py`
  - `apps/chrome-extension/manifest.json`
  - `apps/chrome-extension/content/processing/replacement_semantic_debug.js`
  - `apps/chrome-extension/content/processing/replacement_semantic_override.js`
  - `apps/chrome-extension/content/processing/replacements.js`
  - `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`
  - `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
  - `apps/chrome-extension/content/runtime/dom_scan/semantic_context.js`
  - `apps/chrome-extension/content/runtime/dom_scan/semantic_node_scheduler.js`
  - `apps/chrome-extension/content/runtime/dom_scan/semantic_performance_metrics.js`
  - `apps/chrome-extension/content/runtime/semantic/semantic_gate_batch.js`
  - `apps/chrome-extension/content/runtime/semantic/semantic_gate_summary.js`
  - `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
  - `apps/chrome-extension/content/runtime/semantic/semantic_request_context.js`
  - `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
  - `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
  - `apps/chrome-extension/content/runtime/apply_runtime_actions.js`
  - `apps/chrome-extension/content/runtime/apply_settings_pipeline.js`
  - `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
  - `apps/chrome-extension/shared/settings/settings_defaults.js`
  - `apps/chrome-extension/shared/srs/srs_runtime_diagnostics.js`
  - `apps/chrome-extension/options.html`
  - `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
  - `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
  - `apps/chrome-extension/content_script.js`
  - `core/tests/helper/test_helper_engine.py`
  - `core/tests/dev/test_extension_helper_rule_confidence_contract.py`
  - `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py`
  - `core/tests/dev/test_extension_srs_action_formatters.py`
  - `core/tests/dev/test_extension_srs_settings_contract.py`
  - `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
  - `core/tests/dev/test_extension_text_node_processor_context_contract.py`
  - `core/tests/rulegen/test_semantic_shadow_frequency.py`
  - `core/tests/rulegen/test_semantic_shadow_embedding_bridge.py`
  - `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
  - `core/tests/rulegen/test_semantic_routing_runtime_scoring.py`
  - `core/tests/rulegen/test_semantic_publication.py`
  - `core/tests/rulegen/test_semantic_shadow_inventory.py`
  - `core/tests/architecture/test_extension_structure.py`
  - `core/tests/rulegen/test_semantic_shadow_evaluation.py`
  - `scripts/testing/semantic_routing_sentence_veto_harness.py`
  - `scripts/testing/semantic_routing_sentence_veto_sweep.py`
  - `scripts/testing/semantic_routing_sentence_veto_support.py`
  - `scripts/testing/semantic_shadow_inventory_en_es.py`
  - `scripts/testing/semantic_shadow_inventory_triage_en_es.py`
  - `scripts/testing/semantic_shadow_policy_compare_en_es.py`
  - `scripts/testing/semantic_shadow_policy_gap_queue_en_es.py`
  - `scripts/testing/semantic_shadow_review_queue_en_es.py`
  - `scripts/testing/semantic_shadow_review_packet_en_es.py`
  - `scripts/testing/semantic_shadow_gold_proxy_en_es.py`
  - `scripts/testing/semantic_shadow_coverage_gap_en_es.py`
  - `scripts/testing/semantic_shadow_seed_compare_en_es.py`
  - `scripts/testing/semantic_shadow_embedding_bridge_sweep_en_es.py`
  - `scripts/testing/semantic_shadow_frequency_sweep_en_es.py`
  - `scripts/testing/semantic_shadow_representative_pruning_sweep_en_es.py`
  - `scripts/testing/semantic_shadow_veto_proxy_compare_en_es.py`
  - `scripts/testing/semantic_shadow_forward_seed_sweep_en_es.py`
  - `scripts/testing/semantic_shadow_experiment_matrix_en_es.py`
  - `docs/test_inputs/semantic_shadow_source_registry.json`
  - `docs/test_outputs/semantic_shadow_inventory_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_inventory_triage_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_policy_compare_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_policy_gap_queue_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_review_packet_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_coverage_gap_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_seed_compare_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_forward_seed_sweep_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_frequency_sweep_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_representative_pruning_sweep_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_experiment_matrix_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_veto_proxy_compare_en_es_latest.md`
  - `docs/test_outputs/semantic_routing_sentence_veto_latest.md`
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_latest.md`
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_latest.md`
  - `docs/test_outputs/semantic_routing_sentence_veto_sweep_sentence_transformer_all_minilm_l6_latest.md`
  - `docs/test_outputs/semantic_llm_prompt_downstream_latest.md`
  - `docs/test_outputs/semantic_llm_prompt_failure_diagnostic_latest.md`
  - `docs/test_outputs/semantic_llm_source_insertion_probe_latest.md`
  - `docs/test_outputs/semantic_llm_prototype_admission_probe_latest.md`
  - `docs/test_outputs/semantic_llm_prototype_admission_probe_expanded_latest.md`
  - `docs/test_outputs/semantic_llm_reviewed_example_frame_batch_latest.md`
  - `docs/test_outputs/semantic_llm_reviewed_example_frame_batch_expanded_latest.md`
  - `docs/test_outputs/semantic_llm_example_frame_contract_latest.md`
  - `docs/test_outputs/semantic_llm_example_frame_contract_expanded_latest.md`
  - `docs/test_outputs/semantic_llm_example_frame_contract_overlap_latest.md`
- Known gaps:
  - No LP default path emits a fully mined competition/shadow set yet.
  - All current rulegen LPs can now emit stable active-pointer ids in `metadata.semantic_admission`, but pointer strength differs by locator mode:
    - `en-es` / `en-de`: source-sense provenance first, with translation-gloss fallback
    - `de-en` / `es-en`: deterministic translation-gloss locator (currently FreeDict-backed)
    - `en-ja`: deterministic JMDict entry locator
  - `en-es` can now emit `status=ready` in the explicit helper-side broader-context `emitted_rule_siblings` PoC mode, but that is still narrower than true shadow promotion and should not be read as end-to-end runtime readiness or LP parity.
  - Helper publication can now generate a semantic inventory sidecar with pair capability summary, and `en-es` can publish ready competition sets in that helper-side broader-context PoC, but current default output still does not include mined shadow sets or phrase-preemption inventory.
  - The first live `en-es` shadow inventory artifact proves that broad sibling mining is feasible, but its current promoted-shadow preview is still too noisy to serve as a runtime blocker set.
  - The new sentence-level runtime-veto harness is still intentionally small and curated:
    - only `en-es` is covered today
    - only 8 ambiguity families / 40 rows are labeled
    - thresholds from that dataset are not production-safe defaults
    - current lexical best row is still dominated by false abstains, so model-choice and evidence-view work remain open
    - the latest `v2` model shortlist shows that better winner ranking does not automatically translate into a better replace gate
  - The first triage artifact shows that the stricter preview can eliminate zero-signal rows, but the remaining top-1 promotions are still mostly justified only by `same_pos_as_active`, not by clearly benchmark-aligned competition evidence.
  - The first policy-comparison artifact makes the current algorithm tradeoff concrete:
    - `same_pos_lenient_v1` is broad but noisy
    - `benchmark_backed_v1` and especially `cross_checked_v1` are much cleaner, but probably too narrow to serve as the final default without more shadow evidence
  - The newest active-trigger refinement made the provisional policy safer:
    - bundled forward glosses can now supply active evidence for bare triggers like `take` and `catch`
    - benchmark-only shadows are no longer rescued when the active side is completely empty
    - `cross_checked_backoff_missing_active_v1` now converges to the same promoted set as `cross_checked_v1` on the latest `en-es` artifacts
  - There is no phrase-preemption lane separated from semantic-veto serving.
  - Two additional precision ideas now have negative `en-es` results on the current reviewed overlap proxy:
    - active-vs-shadow frequency-band similarity leaves the best row unchanged, with the sweep preferring `frequency_similarity_weight=0.0`
    - same-sense representative pruning by normalized `sense_label` plus POS also leaves the best row unchanged, with the sweep preferring pruning `off`
  - Runtime decision policy now exists for helper-side semantic scoring and fallback outcomes, but rendered soft-affordance UX is still not productized:
    - current browser DOM behavior applies only `replace`
    - `abstain` and `soft_affordance` both keep the original text today
    - future work still needs a visible soft-affordance interaction and rollout policy
  - Current encouraging semantic-routing benchmark results from prototype work should not be read as proof of fully automatic end-to-end sense discovery or runtime readiness.

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
  - `profile_bootstrap`: `implemented`, `verified`; `default-on` = `no`
  - `profile_growth`: `implemented`, `default-on` for refresh, `verified`
  - `adaptive_refresh`: `scaffolded`
- Last documented checkpoint: `2026-07-03` `profile_bootstrap_policy_v5` now treats corrected learner difficulty as the main scalar admission authority: source commonness is a small tie-breaker, challenge fit remains computed but unweighted in the default one-slider profile path, proficiency/readiness fit is dominant, and topic affinity plus bounded scarcity remain topic-UX helpers. `2026-06-11` seed-frontier cache lifecycle now includes explicit status/prepare APIs, single-flight locking, stale-cache cleanup, native-host/CLI entrypoints, and desktop resource-flow background warmup after relevant pack download/link/import. Full-frontier SRS bootstrap/admission now omits `bootstrap_top_n` by default and helper-driven initialize, preview, refresh, rebalance, and rulegen-job flows cache source-normalized seed rows under `srs/cache/seed_frontiers/` without caching profile scores. `2026-06-02` Options admission preview remains read-only but now returns a seed-controlled sampled subset from the planned active pool instead of the deterministic prefix, so repeated user-facing samples can vary while advanced diagnostics retain the full planned pool and seed. `2026-05-27` refresh admission defaults to `profile_growth`, which reuses the profile-bootstrap utility model for ongoing growth while preserving refresh capacity, due-pressure, retention, POS, and lifecycle gates. `profile_bootstrap` still uses a capped `reserved_topic_lane` selector by default when requested, options initialize/admission preview request it with current profile context, the preference sanity report includes a deterministic strength/proficiency matrix, and the en-es calibration report compares ranked, full-pool weighted, top-k weighted, and reserved topic-lane admission shapes with expected-vs-observed reserved-lane topic counts. Refresh payloads now report realized preferred-topic share for selected new admissions, and the preference product-loop test derives expected post-feedback topic share from topic strength, the capped topic lane, and remaining eligible topic capacity, including sparse medicine/technology cases. Automatic post-feedback refresh now triggers the same `profile_growth` refresh path only after helper-persisted feedback thresholds are met, and extension retry-only feedback flushes do not run the refresh check. The en-es topic taxonomy now records `mvp_picker_visibility`, the options-page topic chips exactly mirror `strict_mvp_visible`, and the dev admission lab surfaces beta/hidden/register visibility metadata without removing diagnostic scenarios.
- Last verified: `2026-07-03` en-ja product admission artifacts (`srs_admission_product_acceptance_en_ja_latest`: `PASS`, `srs_admission_random_ux_sample_pack_en_ja_latest`: `PASS`) show all `19` topic scenarios with movers, zero sampled `restricted_admission` rows, zero neutral non-topic rows more than `0.10` above proficiency, and surfaced-auto topic review `row_count=0`; focused profile-bootstrap/selector tests passed and SRS quality harness passed (`pass=22 warn=0 fail=0`). Earlier `2026-07-02` coverage included en-ja explicit admission artifacts (`srs_admission_preference_sample_pack_en_ja_latest`: `PASS`, `srs_admission_topic_proficiency_grid_en_ja_latest`: `WARN` with only sparse-topic no-mover warnings), hard admission-suitability selector tests, focused initial-bootstrap and refresh no-rule refill tests, and SRS quality harness. Earlier `2026-06-11` coverage included focused seed-cache lifecycle/use-case tests (`21 passed`) plus syntax/style checks for the helper/native-host/GUI cache-prep entrypoints, focused SRS/helper/options contract test set (`177 passed`), en-ja learner-difficulty audit regeneration (`72,758` deduped unique lemmas), local installed en-ja seed-cache timing probe (`10.379s` first full-frontier seed build, `2.497s` repeat cache hit, same `78,316` raw normalized seed rows), and local installed en-ja profile-bootstrap timing probe (`17.201s` first initialization, `8.326s` repeat cached initialization, same `72,758` selected unique count). Earlier `2026-06-02` coverage included focused helper admission-preview tests covering weighted and reserved-topic seeded preview sampling, plus state and changed-file gates. Earlier `2026-05-27` coverage included focused profile-growth refresh/helper/native-host/options tests, preference-shaped product-loop tests with derived strong/weaker/sparse post-feedback topic-share assertions, automatic refresh policy/state tests, extension feedback-sync auto-refresh contract tests, content-runtime/background bridge auto-refresh contract tests, options SRS bridge contract tests, profile-bootstrap reserved-topic-lane selector/helper/options tests, strict-MVP options topic-picker contract tests, taxonomy visibility validation, preference sanity artifact generation, en-es admission calibration artifact generation, SRS quality harness, doc-reference check, state audit, diff check, and changed-file gate.
- Default behavior:
  - No-strategy helper bootstrap execution remains frequency bootstrap.
  - Options initialize and admission preview request `profile_bootstrap`, which applies implemented normalization, scoring, diagnostics, a proficiency readiness multiplier, corrected-difficulty-first utility weights, and capped reserved topic-lane selection over the frequency seed frontier before initial active selection.
  - Actual selector admission now treats `admission_suitability=0.0` as hard
    ineligible while leaving those rows visible in ranking diagnostics. Low
    nonzero suitability remains a soft multiplier.
  - Initial bootstrap and manual refresh reconcile active items without enabled
    generated rules, then run bounded refill passes that block
    discarded/no-rule lemmas plus still-active lemmas, select replacement
    candidates within the original active/budget target, rerun rulegen, and
    report the result through `rule_availability_refill`. Rebalance still
    reconciles no-rule active items without refill.
  - Bootstrap/admission uses all available seed rows by default when
    `bootstrap_top_n` is omitted/null. Helper-driven flows use the
    source-normalized seed-frontier cache as a latency optimization; cache
    misses, stale keys, and corrupt files rebuild the same configured frontier.
    Cache status/prepare routes and desktop resource-flow warmup are
    profile-independent and do not change admission scoring.
  - Options admission preview sends a fresh seed per sample request and displays
    a sampled subset of the planned active pool; it does not initialize,
    persist, or publish SRS words.
  - The ordinary options-page topic picker exposes only en-es taxonomy families
    marked `mvp_picker_visibility=strict_mvp_visible`; beta, hidden,
    legal-gated, and register families stay out of that picker while remaining
    available to diagnostics and the advanced manual-tag field.
  - The local SRS admission lab may create a temporary EN-ES Zipf-bridge augmented frequency DB from committed test artifacts plus installed Kaikki POS data; this is dev-lab-only and does not install, mutate, or promote a production frequency pack.
  - The local SRS admission lab still lists all taxonomy families for internal
    sampling, but now labels strict-MVP, beta-hidden, source-hidden,
    register-hidden, and legal-gated visibility so diagnostic controls cannot be
    mistaken for tester-facing picker scope.
  - The calibration report is preview-only, but the reserved topic-lane row now
    exercises the real profile-bootstrap selection policy and reports expected
    topic count/status from lane cap plus source capacity. Full-pool weighted
    sampling remains too diffuse as a direct topic-preference policy.
  - `profile_growth` is executable for refresh/growth admission into `S`; it
    transforms the seed frontier through profile-aware scoring, applies the
    capped reserved topic-lane selector where relevant, and then uses the
    existing refresh admission gates before persistence/publication. When
    profile-growth diagnostics are active, refresh output includes
    `selected_preferred_topic` with selected count, preferred-topic count,
    realized share, and preferred-topic lemmas.
  - Automatic post-feedback refresh is implemented as a trigger layer for
    `profile_growth`: the extension runs a best-effort `srs_auto_refresh`
    check after one or more feedback items successfully sync to the helper,
    and the helper persists per-profile/pair attempt state before running the
    normal refresh path. Retry-only feedback flushes do not run the refresh
    check. Content-runtime bridge contract coverage now verifies that synced
    feedback routes through `record_feedback`, then `srs_auto_refresh`, to the
    background native-messaging bridge with the expected profile-growth payload.
    Options bridge contract coverage verifies SRS initialize, plan, preview,
    and refresh actions route through the same background native-messaging
    bridge with the expected profile-aware payloads.
  - `profile_growth` remains executable for the dedicated rebalance
    preview/apply lane.
  - `adaptive_refresh` still falls back to planning-only behavior.
- Evidence:
  - `docs/srs/srs_set_planning_technical.md`
  - `core/lexishift_core/srs/admission_features.py`
  - `core/lexishift_core/srs/profile_bootstrap.py`
  - `core/lexishift_core/srs/profile_bootstrap_support.py`
  - `core/lexishift_core/srs/seed_cache.py`
  - `core/lexishift_core/helper/use_cases/admission_preview.py`
  - `core/lexishift_core/helper/use_cases/seed_cache.py`
  - `core/lexishift_core/helper/use_cases/refresh_set.py`
  - `core/lexishift_core/helper/use_cases/auto_refresh_set.py`
  - `core/lexishift_core/srs/auto_refresh.py`
  - `core/lexishift_core/srs/growth.py`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/srs/selector.py`
  - `docs/test_inputs/srs_topic_preference_taxonomy_en_es.json`
  - `apps/chrome-extension/options.html`
  - `scripts/dev/srs_admission_lab_server.py`
  - `scripts/dev/srs_admission_lab_static.html`
  - `core/lexishift_core/helper/use_cases/rebalance_set.py`
  - `core/tests/srs/test_profile_bootstrap.py`
  - `core/tests/srs/test_selector.py`
  - `core/tests/dev/test_srs_admission_lab_server.py`
  - `core/tests/srs/test_srs_set_planner.py`
  - `core/tests/srs/test_srs_growth.py`
  - `core/tests/srs/test_srs_auto_refresh.py`
  - `core/tests/srs/test_srs_preference_product_loop.py`
  - `core/tests/dev/test_extension_feedback_auto_refresh_bridge_contract.py`
  - `core/tests/dev/test_extension_options_srs_bridge_contract.py`
  - `core/tests/dev/test_extension_srs_settings_contract.py`
  - `core/tests/helper/test_helper_auto_refresh_set.py`
  - `core/tests/dev/test_extension_helper_feedback_sync_auto_refresh.py`
  - `core/tests/helper/test_helper_engine.py`
  - `core/tests/dev/test_srs_planner_strategy_contract.py`
  - `core/tests/dev/test_helper_translation_dict_entrypoints.py`
  - `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py`
  - `core/tests/dev/test_srs_admission_preference_sanity.py`
  - `core/tests/dev/test_srs_admission_calibration_report_en_es.py`
  - `core/tests/dev/test_srs_topic_preference_taxonomy_en_es.py`
  - `core/tests/dev/test_srs_frequency_topic_coverage.py`
  - `scripts/testing/srs_admission_preference_sanity.py`
  - `scripts/testing/srs_admission_calibration_report_en_es.py`
  - `docs/test_outputs/srs_admission_calibration_en_es_latest.md`
  - `scripts/testing/srs_frequency_topic_coverage.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
- Known gaps:
  - `profile_growth` uses explicit profile signals supplied at refresh time; it
    does not yet auto-recalibrate proficiency from conquered words.
  - Pair policy defaults are currently near-identical across active pairs.
  - `core/lexishift_core/srs/profile_bootstrap.py` remains a structural hotspot and should be split in a later health pass rather than folded into admission-contract edits.

## Browsing-Based SRS Admission

- Status: `scaffolded`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-07-03` reading-aware browsing aggregates
  now use a target-key structure carrying lemma, optional reading, confidence,
  and observation-source metadata while preserving the opt-in, preview-only
  behavior. Earlier `2026-05-31` active-rotation release now parks mature
  review words out of full active inventories before refresh capacity is
  calculated, and reset treats the helper signal queue as story-scoped
  lifecycle state; pair reset removes that pair's feedback/exposure events and
  all-story reset removes the queue file. This extends the `2026-05-27` SRS
  lifecycle, active-budget, stale-unseen capacity, and manual refresh
  diagnostics update:
  browsing signal aggregation has an opt-in helper dev ingest path, persisted
  profile-scoped aggregate store, and hidden dev extension packet builder for
  replacement exposures; refresh admission also respects active suppression
  entries before admitting new lemmas; refresh responses include preview-only
  browsing diagnostics without changing actual neutral admission selection;
  `Balanced` preview can now realize one browsing slot for small budgets when
  fractional signal pressure is high enough; helper/native-host can now write
  durable `user_blocked` suppression entries and mark existing SRS items
  `discarded` for future discard/block flows; non-active lifecycle states are
  now excluded from active inventory, due selection, growth capacity, and
  rulegen publication; refresh capacity now uses the pair's resolved active
  inventory after automatic active-rotation release rather than the smaller
  due-only subset or every lifecycle-active store row; options refresh output
  now surfaces active budget, stale-unseen capacity pressure, selected lemmas,
  and preview-only browsing comparison diagnostics for manual SRS testing
- Last verified: `2026-07-03` backend plus gradient-verified browsing packs
  for `en-ja` and `en-es`; the en-ja implicit sample pack has `7` scenarios
  passing, the en-ja signal-gradient pack has `36` scenarios passing, alongside
  Unicode/en-ja browsing-signal core tests, focused helper/native-host browsing
  ingest tests, and SRS quality harness
  (`pass=22 warn=0 fail=0`). Earlier `2026-05-31` active-rotation release,
  inventory-scoped capacity, helper refresh parking, product-loop regression,
  and reset signal-queue cleanup tests extend
  lifecycle marker, inventory-scoped active-budget, automatic active-rotation
  release, stale-unseen capacity,
  manual refresh diagnostics,
  and active-inventory
  filtering tests, lifecycle-aware scheduler/growth/rulegen tests, admission
  suppression writer tests, reset suppression-metadata tests, fractional
  browsing-budget tests, SRS quality harness with seeded non-empty browsing
  preview, refresh-path browsing preview tests, refresh-suppression lifecycle
  guard tests, active-capacity refresh tests, extension packet-builder and
  offline helper/core research probe tests, focused helper/native-host browsing
  ingest tests, refreshed admission-lifecycle audit, and regenerated backend
  simulation artifact
- Default behavior:
  - No live browser capture is wired by default; the extension packet builder
    only runs when hidden setting `srsBrowsingAdmissionSignalsEnabled` is true.
  - No browsing signal changes actual SRS admission refresh yet.
  - Manual refresh admission now filters active admission-suppression entries;
    this guards future browsing boost from re-admitting suppressed lemmas.
  - Manual refresh capacity is capped by the pair's resolved active inventory
    after automatic active-rotation release, not by every lifecycle-active store
    row and not only by currently due items. Due count remains a pressure signal
    that can pause admission when reviews are overloaded.
  - Automatic active-rotation release runs during refresh only when the active
    inventory is already at or above the active-size target. It parks mature
    review items with at least four reviews and a next due date at least seven
    days in the future by removing them from active inventory while preserving
    their SRS store rows, history, lifecycle state, and future due date.
  - The `srs_admission_suppress` helper/native-host route can write durable
    `user_blocked` suppression; when a matching SRS item already exists, it marks
    that item `lifecycle_state=discarded` and removes it from active inventory.
    The options dashboard now uses this route for confirmed learner discard.
  - `SrsItem` lifecycle markers currently support `active`, `discarded`, and
    `cleared`; non-active lifecycle states are filtered out of active-inventory
    fallback, stale-inventory resolution, scheduler due selection, refresh
    growth admission, and helper rulegen publication.
  - `srs_reset` clears matching signal-queue feedback/exposure events and
    suppression metadata by default. A backend `preserve_lifecycle_metadata`
    flag exists for a future confirmation UX that keeps durable discard/block
    metadata, but signal-queue events are story lifecycle data and are still
    reset.
  - The SRS feedback popup remains a review-feedback surface only; it does not
    expose a cooldown action.
  - Manual refresh responses include preview-only browsing admission diagnostics
    for the same candidate pool and budget; the diagnostics do not affect the
    persisted refresh selection.
  - Options refresh output displays active count, due count, capacity budget,
    active zero-exposure/zero-feedback counts, stale-unseen active capacity,
    final admission budget, selected lemmas, and neutral vs `Balanced`/`Strong`
    browsing preview selections when available.
  - The preview uses fractional small-budget realization so `Balanced` can show
    one browsing lane when signal pressure is meaningful, while actual persisted
    admission remains neutral.
  - The helper ingest path requires explicit opt-in and stores bounded target-key
    aggregates only. Aggregates can carry `target_lemma`, `target_reading`,
    per-channel counts, observation-source metadata, and reading confidence, but
    URLs, raw page text, HTML, and context text are ignored.
  - The extension packet builder currently captures replacement exposures only,
    not arbitrary page words. It sanitizes observations before queueing helper
    packets.
  - The current simulation accepts an explicit pair and uses helper-persisted
    synthetic packets to prove capping, pruning, suppression, neutral/off
    baseline preservation, and monotonic `Off` / `Balanced` / `Strong`
    browsing-share behavior without mutating SRS items. The default fixture now
    exercises `en-ja` Unicode target lemmas, with an `en-es` comparison artifact
    retained for the older research lane.
  - The en-ja implicit browsing sample pack now runs profile-shaped preview
    scenarios over the real en-ja seed frontier: no-history neutral, explicit
    topic only, implicit history only, agreeing explicit+implicit history,
    conflicting explicit+implicit history, and blocked-lemma guards. It uses
    already-resolved target lemma aggregates only and remains preview-only.
  - The en-ja signal-gradient pack now verifies count sensitivity over the same
    preview path: weak single signals do not affect `Balanced`, multiple
    target-side signals reserve slots earlier, replacement-exposure signals are
    weaker, and lane counts remain monotonic as aggregate counts rise.
  - Topic preference, browsing admission, review scheduling, and page
    replacement are documented as separate product decisions; known/learned
    words must not become permanent unlimited page replacements by default.
- Evidence:
  - `docs/srs/srs_admission_lifecycle_current_state.md`
  - `docs/srs/srs_browsing_based_admission_plan.md`
  - `core/lexishift_core/srs/browsing_admission.py`
  - `core/lexishift_core/srs/admission_refresh.py`
  - `core/lexishift_core/srs/active_rotation.py`
  - `core/lexishift_core/srs/growth.py`
  - `core/lexishift_core/srs/scheduler.py`
  - `core/lexishift_core/srs/store.py`
  - `core/lexishift_core/srs/inventory.py`
  - `core/lexishift_core/srs/store_ops.py`
  - `core/lexishift_core/srs/admission_suppression.py`
  - `core/lexishift_core/helper/use_cases/admission_suppression.py`
  - `core/lexishift_core/helper/use_cases/reset.py`
  - `core/lexishift_core/helper/use_cases/browsing_admission.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
  - `core/lexishift_core/helper/use_cases/refresh_set.py`
  - `apps/chrome-extension/options/controllers/srs/actions/refresh_result_formatter.js`
  - `apps/chrome-extension/options/controllers/srs/actions/formatters.js`
  - `core/lexishift_core/helper/rulegen.py`
  - `core/lexishift_core/helper/paths.py`
  - `scripts/helper/lexishift_native_host.py`
  - `scripts/helper/lexishift_helper.py`
  - `apps/chrome-extension/shared/helper/helper_client.js`
  - `apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js`
  - `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
  - `scripts/testing/srs_browsing_admission_backend_simulation.py`
  - `scripts/testing/srs_browsing_admission_implicit_sample_pack_en_ja.py`
  - `scripts/testing/srs_browsing_admission_signal_gradient_en_ja.py`
  - `scripts/testing/srs_browsing_admission_research_en_es.py`
  - `docs/test_inputs/srs_browsing_admission_implicit_configs_en_ja.json`
  - `docs/test_inputs/srs_browsing_admission_signal_gradient_en_ja.json`
  - `docs/test_outputs/srs_browsing_admission_backend_simulation_latest.md`
  - `docs/test_outputs/srs_browsing_admission_backend_simulation_en_ja_latest.md`
  - `docs/test_outputs/srs_browsing_admission_backend_simulation_en_es_latest.md`
  - `docs/test_outputs/srs_browsing_admission_implicit_sample_pack_en_ja_latest.md`
  - `docs/test_outputs/srs_browsing_admission_signal_gradient_en_ja_latest.md`
  - `docs/test_outputs/srs_browsing_admission_research_en_es_latest.md`
  - `core/tests/srs/test_srs_admission_refresh.py`
  - `core/tests/srs/test_srs_active_rotation.py`
  - `core/tests/srs/test_srs_browsing_admission.py`
  - `core/tests/srs/test_srs_preference_product_loop.py`
  - `core/tests/srs/test_srs_growth.py`
  - `core/tests/srs/test_srs_scheduler.py`
  - `core/tests/srs/test_srs_store.py`
  - `core/tests/srs/test_srs_inventory.py`
  - `core/tests/srs/test_srs_store_ops.py`
  - `core/tests/helper/test_helper_admission_suppression.py`
  - `core/tests/helper/test_helper_browsing_admission.py`
  - `core/tests/helper/test_helper_engine.py`
  - `core/tests/helper/test_helper_rulegen.py`
  - `core/tests/dev/test_srs_browsing_admission_backend_simulation.py`
  - `core/tests/dev/test_extension_srs_action_workflows.py`
  - `core/tests/dev/test_helper_browsing_admission_entrypoints.py`
  - `core/tests/dev/test_extension_browsing_admission_signals.py`
  - `core/tests/dev/test_srs_browsing_admission_implicit_sample_pack_en_ja.py`
  - `core/tests/dev/test_srs_browsing_admission_signal_gradient_en_ja.py`
  - `core/tests/dev/test_srs_browsing_admission_research_en_es.py`
- Known gaps:
  - Broad live page-word capture remains unwired; only LexiShift replacement
    exposure batches can currently become dev browsing signals.
  - Browsing aggregates are not yet consumed by production admission refresh.
  - User-facing settings and reset/clear controls for browsing admission signals
    remain planned.
  - A strict calendar-day quota ledger for repeated manual refreshes remains
    planned if `max_new_items_per_day` must mean more than a per-refresh cap.
  - Restore/release/mastered lifecycle controls remain planned.

## SRS Admitted Words Dashboard

- Status: `implemented`, `default-on`, `verified` for visibility plus
  local dashboard search/filter/sort/pagination, read-only published-rule
  summaries, capped on-demand rule details, and confirmed durable dashboard
  discard; restore/mastery/release controls remain `planned`
- Last documented checkpoint: `2026-06-02` learner-facing dashboard wording pass
  keeps the stable `queued` machine state but shows it as `Upcoming`, renames
  replacement observability to `Page replacement`, removes raw item ids from the
  normal advanced row view, and moves read-only row details away from a separate
  `View`/rule-details action into row interaction; extends the `2026-05-31`
  active-rotation capacity release and `2026-05-27` admitted-words dashboard replacement
  eligibility projection, bridge/control polish, options UI, local review
  controls, published-rule summaries/details, first durable lifecycle action,
  profile-bootstrap bridge coverage, and encounter-watch visibility:
  helper/native-host can list pair/profile SRS items, summarize active/queued/
  due/removed states, surface active zero-exposure/zero-feedback watch counts,
  project which active rows are currently eligible for page replacement,
  persist `admitted_at` for newly admitted items, and expose scheduler/lifecycle
  details behind an advanced toggle in options; the dashboard can locally
  search/filter/sort already-loaded
  words with page-size controls, first/previous/next/last pagination, refresh
  metadata, disabled-state-aware clear filters, and Escape-to-clear search; rows
  show read-only published-rule counts/source previews and can load capped
  read-only rule details on demand; eligible rows can confirm Discard, which
  reuses `srs_admission_suppress` with `reason=user_blocked`; focused helper
  coverage now verifies profile-bootstrap initialization through rule publication
  and dashboard listing
- Last verified: `2026-06-02` learner-facing dashboard wording and row-detail
  interaction tests, helper label tests, architecture script-order test, JS
  syntax checks, locale JSON parse checks, state audit, doc-reference check,
  and diff check; extends the `2026-05-31` active-rotation release helper,
  inventory-scoped admission capacity, helper refresh integration, and
  product-loop regression tests plus the `2026-05-27` admitted-at dashboard
  encounter diagnostics, replacement-eligibility dashboard projection,
  bridge/meta-control, rule-summary/detail, search/filter/sort/pagination,
  confirmed discard route, stale-unseen encounter-watch counters/rendering, and
  profile-bootstrap initialize-to-dashboard bridge tests; focused helper
  endpoint, native-host route, helper client/manager route, resource-budget
  audit, suppression writer tests, SRS quality harness encounter-watch scenario,
  changed-file gate, doc-reference check, state audit, and diff check remain
  part of the broader dashboard evidence chain
- Default behavior:
  - The options page exposes a Learning words dashboard for the selected
    profile and language pair.
  - Refresh words calls `srs_items_list`; the listing route is read-only and
    does not admit, schedule, publish, discard, clear, or restore items.
  - The default dashboard shows learner-facing counts and rows; advanced fields
    are hidden behind a toggle.
  - Search, status filter, sort, clear-filter, page-size, and pagination
    controls reshape only the already-loaded dashboard payload. They do not call
    helper routes, mutate SRS state, or change admission/serving order.
  - Changing search, status, sort, page size, or clearing filters resets the
    dashboard to page 1.
  - The dashboard shows refresh metadata for the already-loaded payload,
    including loaded/viewed counts, active-inventory source, and published
    ruleset state. The refresh timestamp is anchored to the helper result, not
    local filter renders. Clear filters is disabled until search/status/sort
    are adjusted, and Escape clears the current search.
  - The dashboard exposes first-order encounter-watch visibility through an
    `Unseen` summary card, an `Encounter watch` metadata row, and compact row
    notes for active words with zero exposure plus zero feedback, stale-unseen
    age, unknown admission age, or no enabled published rules. Newly admitted
    SRS items persist `admitted_at`; legacy rows without it are treated as age
    unknown. These are diagnostics only and do not clear, release, or park
    words.
  - The dashboard exposes a read-only `Replacing` summary card, metadata count,
    and per-row `Replacing` label derived from active inventory, due state, and
    enabled published-rule availability. This is observability only; runtime
    replacement decisions still live in the extension runtime gate.
  - Each row can show read-only published-rule count plus a capped source-phrase
    preview from the current helper-published ruleset artifact. Missing or
    unreadable rulesets do not block item listing.
  - Profile-bootstrap initialization, helper-published rule outputs, active
    inventory, and dashboard list summaries share the same pair/profile helper
    state.
  - Rows with published rules can load capped read-only details for that lemma
    on demand through `srs_item_rule_details`; the normal list payload remains
    compact.
  - Active status uses the same active-inventory resolver as helper SRS serving;
    queued admitted words remain visible but not active, and are labeled
    `Upcoming` in learner-facing UI.
  - Dashboard replacement observability is labeled `Page replacement` in the
    user-facing UI. Internal payload fields named `serving` remain unchanged.
  - Published rule details open from the row rather than a competing normal
    `View` action; Discard remains the only explicit row mutation.
  - The normal advanced row view omits raw item ids. Raw ids remain developer
    diagnostics, not learner-facing advanced information.
  - When refresh finds the active inventory at or above the active-size target,
    lifecycle-active review words with at least four reviews and a next due date
    at least seven days in the future are automatically parked out of active
    inventory before capacity is calculated. Their SRS store rows and history
    are preserved, so this is not discard, deletion, or mastered lifecycle UX.
  - Eligible words expose a confirmed Discard action. It durably blocks refresh
    re-admission, marks existing SRS items `discarded`, and removes active
    inventory membership through the existing helper suppression route.
  - Restore/mastered/release actions remain planned and must not be inferred
    from dashboard discard.
- Evidence:
  - `docs/srs/srs_admitted_words_dashboard_plan.md`
  - `docs/srs/srs_admission_lifecycle_current_state.md`
  - `docs/srs/srs_schema.md`
  - `scripts/testing/srs_resource_budget_audit.py`
  - `scripts/testing/srs_resource_budget_audit_render.py`
  - `scripts/testing/srs_resource_budget_audit_time.py`
  - `core/lexishift_core/srs/store.py`
  - `core/lexishift_core/srs/store_ops.py`
  - `core/lexishift_core/srs/growth.py`
  - `core/lexishift_core/srs/admission_refresh.py`
  - `core/lexishift_core/srs/active_rotation.py`
  - `core/lexishift_core/helper/rulegen.py`
  - `core/lexishift_core/helper/use_cases/srs_items.py`
  - `core/lexishift_core/helper/engine.py`
  - `scripts/helper/lexishift_native_host.py`
  - `scripts/helper/lexishift_helper.py`
  - `apps/chrome-extension/options.html`
  - `apps/chrome-extension/options.css`
  - `apps/chrome-extension/options/core/ui_manager.js`
  - `apps/chrome-extension/options/core/bootstrap/controller_graph_elements.js`
  - `apps/chrome-extension/shared/helper/helper_client.js`
  - `apps/chrome-extension/options/controllers/srs/actions_controller.js`
  - `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
  - `apps/chrome-extension/options/core/helper/srs_set_methods.js`
  - `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_model.js`
  - `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_formatting.js`
  - `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_renderer.js`
  - `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_rule_details.js`
  - `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_workflow.js`
  - `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
  - `core/tests/srs/test_srs_store.py`
  - `core/tests/srs/test_srs_store_ops.py`
  - `core/tests/srs/test_srs_growth.py`
  - `core/tests/srs/test_srs_admission_refresh.py`
  - `core/tests/srs/test_srs_active_rotation.py`
  - `core/tests/srs/test_srs_preference_product_loop.py`
  - `core/tests/helper/test_helper_srs_items.py`
  - `core/tests/helper/test_helper_admission_suppression.py`
  - `core/tests/dev/test_srs_resource_budget_audit.py`
  - `core/tests/dev/test_helper_browsing_admission_entrypoints.py`
  - `core/tests/dev/test_extension_helper_status_profile_contract.py`
  - `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py`
- Known gaps:
  - Dashboard virtualization is not implemented.
  - Deep per-word semantic metadata inspection and morphology variant inspection
    are not implemented.
  - User actions for restore, clear, release, and mastered-state management are
    not implemented; current automatic parking is backend active-inventory
    capacity management only.
  - The extension feedback popup remains review-feedback only.

## SRS Word Info API And Quick Definition Popup

- Status: `implemented`, `default-on`, `verified` for the shared read-only
  word-info API, selected-profile Vocabulary Library page with active-pair
  selection, and built-in `quick-definition` popup module; cross-profile library enumeration and completed/
  mastered lifecycle UX remain planned.
- Last documented checkpoint: `2026-06-02` selected-profile Vocabulary Library
  page with active-pair selection and selected-profile theme application extends the source-resolution and enriched popup checkpoint:
  helper/core can read a profile/pair/lemma
  word-info payload, native host exposes `word_info_lookup`, the extension
  helper client exposes `lookupWordInfo`, Options exposes a
  `HelperManager.lookupWordInfo` convenience through the shared API wrapper,
  content/options load `shared/helper/word_info_api.js`, and the content popup
  registers `quick-definition` ahead of script/history modules; Options links
  to `learning_dashboard.html`, whose page controller resolves the active
  profile, lists active pairs for that profile, lists admitted words for the
  selected pair, applies the selected profile's Options background/card-theme
  preferences, loads current-page definition previews, opens a detail panel,
  and reuses confirmed discard as its only mutation.
- Last verified: `2026-06-02` dedicated Vocabulary Library page pair-selector/theme-loading tests plus
  focused helper word-info tests, native-host route tests, helper-client/API
  contract tests, quick-definition popup render and registry tests, extension
  structure tests, JS syntax checks, and Python compile checks
- Default behavior:
  - The route is read-only and does not admit, refresh, schedule, publish,
    discard, or otherwise mutate SRS state.
  - The helper returns compact learner-facing word info: normalized pair/profile
    fields, target display/lemma, POS where known, local glosses with optional
    safe sense details/examples, source phrase summaries, compact SRS
    presence/state, deterministic external dictionary links, and sanitized
    diagnostics.
  - Compact gloss selection prefers unrestricted senses and the first dictionary
    POS group; restricted usage senses such as slang/vulgar/obsolete/derogatory
    entries are fallback-only when no unrestricted sense is available.
  - Installed local lexical resources are the canonical gloss source. For
    `en-es`, the route resolves Spanish-to-English translation/gloss packs
    through existing pair-resource capability/default-pack logic rather than
    extension-side filenames or paths. Manifestless `language_packs/<pack-id>/main.sqlite`
    pack roots are recognized so local `wiktionary-es-en` installs keep the
    intended Wiktionary-first priority over FreeDict fallback.
  - The extension API wrapper normalizes camelCase/snake_case request fields,
    caches successful lookups for the current JS runtime session, and delegates
    native messaging to `HelperClient.lookupWordInfo`.
  - The content singleton is configured with the current helper client.
    `quick-definition` receives the shared `LexiShift.wordInfoApi` capability
    through the popup descriptor context and does not call native messaging or
    local storage directly.
  - `quick-definition` is default-on for all target languages through the popup
    module registry, renders first in the popup module stack, shows an immediate
    loading state, and then renders target display, POS when known, up to five
    local glosses with compact details/examples when available, and
    deterministic external dictionary links.
  - `quick-definition` degrades to localized fallback text when the helper is
    unavailable, the request is invalid, or installed definition data is
    missing.
  - Options code can call `HelperManager.lookupWordInfo(...)`.
  - The active Vocabulary Practice card links directly to a dedicated
    Vocabulary Library page instead of rendering an embedded dashboard. The page
    is scoped to the selected/current profile, lets the learner select among
    that profile's active language pairs, uses the existing read-only
    `srs_items_list` route, reuses local dashboard search/status/sort semantics,
    applies the selected profile's Options background/card-theme preferences,
    and loads definition/gloss previews only for the current page, capped at 25
    rows per render.
  - The Vocabulary Library detail panel shows local definition/glosses,
    external dictionary links, page-replacement source phrases, and advanced
    scheduler/page-replacement details behind an Advanced toggle.
  - The Vocabulary Library reuses confirmed dashboard discard as its only
    mutation; it does not implement restore, completed/mastered state, or
    cross-profile enumeration.
  - Local filesystem paths are intentionally excluded from learner-facing
    payloads and diagnostics.
- Evidence:
  - `docs/srs/srs_vocabulary_library_and_word_info_plan.md`
  - `docs/architecture/popup_modules_pattern.md`
  - `core/lexishift_core/helper/use_cases/word_info.py`
  - `core/lexishift_core/helper/engine.py`
  - `scripts/helper/lexishift_native_host.py`
  - `apps/chrome-extension/shared/helper/helper_client.js`
  - `apps/chrome-extension/shared/helper/word_info_api.js`
  - `apps/chrome-extension/content/ui/popup_modules/quick_definition_module.js`
  - `apps/chrome-extension/content/ui/ui.js`
  - `apps/chrome-extension/shared/srs/popup_modules_registry.js`
  - `apps/chrome-extension/options/core/helper/srs_set_methods.js`
  - `apps/chrome-extension/content_script.js`
  - `apps/chrome-extension/manifest.json`
  - `apps/chrome-extension/options.html`
  - `apps/chrome-extension/learning_dashboard.html`
  - `apps/chrome-extension/learning_dashboard.css`
  - `apps/chrome-extension/learning_dashboard_model.js`
  - `apps/chrome-extension/learning_dashboard_view.js`
  - `apps/chrome-extension/learning_dashboard_table.js`
  - `apps/chrome-extension/learning_dashboard_theme.js`
  - `apps/chrome-extension/learning_dashboard.js`
  - `core/tests/helper/test_helper_word_info.py`
  - `core/tests/dev/test_helper_browsing_admission_entrypoints.py`
  - `core/tests/dev/test_extension_helper_status_profile_contract.py`
  - `core/tests/dev/test_extension_quick_definition_popup_module.py`
  - `core/tests/dev/test_extension_learning_dashboard_page.py`
  - `core/tests/architecture/test_extension_structure.py`
- Known gaps:
  - Cross-profile Vocabulary Library enumeration is not implemented.
  - Completed/mastered lifecycle UX is not implemented in the Vocabulary
    Library.
  - Batch lookup for a page of library rows is not implemented.
  - The normalized public popup module API remains target architecture; the
    current module uses the existing internal popup descriptor/context pattern.
  - JMDict and future-pair provider behavior has a generic path but only
    `en-es` translation-pack lookup has focused production-style coverage in
    this slice.

## Vocabulary Practice Options UX

- Status: `implemented`, `default-on`, `verified` for the selected-story shell,
  direct Vocabulary Library entry, sampling curtain, switch styling, proficiency slider presentation,
  lazy status output, guided new-story initialization modal, and helper-backed
  missing-language-data setup recovery, delete-story state cleanup, and
  existing-GUI resource-settings deep-link activation; full multi-story
  enumeration remains `planned`
- Last documented checkpoint: `2026-06-02` Options now links directly to the
  dedicated Vocabulary Library instead of embedding the admitted-words
  dashboard, the dedicated page lets the selected profile switch among active
  language pairs while applying the same selected-profile background/card-theme
  preferences as Options, and learning-word review feedback plus automatic
  new-word refresh are implicit always-on defaults rather than learner-facing
  toggles. Manual-ruleset replacement feedback is an internal compatibility
  flag and remains off/not exposed for MVP.
  `2026-06-02` learner-facing naming now presents the
  SRS-backed learning surface as `Vocabulary Practice`, uses `practice`/
  `learning words` copy in setup, dashboard, preference-save, discard, and
  delete paths, localizes the updated extension/GUI strings across English,
  Japanese, Chinese, and German, and keeps internal `srs_*`/story identifiers as
  implementation details for APIs, storage, diagnostics, and tests. This naming
  pass extends the `2026-05-31` delete-story state cleanup and the
  `2026-05-28` resource-readiness setup recovery,
  generic installed-data hint removal, visible SRS enable-switch removal,
  story-scoped delete-story copy, active story preference-save/restore,
  flattened Advanced cleanup, theme-aware practice surfaces, and
  section-order polish extend the
  guided-flow checkpoint: controls are grouped under a selected profile/pair
  story block, that block is collapsed by default to a pair summary plus
  right-aligned active badge, the visible next-word controls are grouped into
  clearer subsections without repeated explanatory copy or a redundant heading,
  topic controls render
  as a contained probability-priority chip panel, the proficiency estimate is a
  slider that preserves the unset stored state until the user changes it and
  shows the previous saved value with a restore action,
  active-size copy now uses learner-facing practice wording, active-story
  candidate search depth is hidden as a backing control while the setup flow
  still keeps it under advanced starting-size controls,
  source/target pair controls and the legacy initialize button remain as hidden
  backing DOM anchors rather than visible active-story controls,
  sampling now sits next to admission settings, the Vocabulary Library entry follows
  sampling, sampling curtains use compact title/subtitle/action
  summaries, tentative free-form topic tags and advanced challenge tuning are
  hidden, new-word preference edits require an explicit Save preferences action,
  helper/semantic technical status is not shown inside the active story surface,
  empty status panels appear only after content is written,
  display controls are reduced to an inline highlight-color control plus sound
  toggle in the normal story surface, the collapsed
  `Advanced` section contains only same-level user-tunable new-word timing
  thresholds plus the story-scoped delete action, the visible SRS enable switch
  and generic installed-data hint are removed because the guided initialization
  flow is the learner-facing enable/readiness path, manual active-word
  update/learning-word refresh actions are no longer shown in the ordinary story
  surface, guided setup now turns missing language-data preflight failures into
  an inline resource-readiness panel with learner-facing resource labels that can
  open the GUI Resource settings tab through the native helper with the
  pair added/focused in the persistent Learning Languages resource view and
  retry the same setup check; the Learning Languages pair cards promote
  app-managed downloads, hide per-resource manual file selection from the
  learner-facing path, include the required Kaikki/Wiktionary `wiktionary-es-en`
  resource and the CC BY `freq-es-spalex-v1` frequency resource for en-es, show
  catalog sizes and per-resource progress, keep license-restricted
  `freq-es-cde` available only as a legacy/manual import path with
  rights-confirmed local source import for `spanish_lemmas20k.txt`, expose per-resource
  file-location reveal and uninstall actions for installed data, and confirm
  before removing a pair card from the Learning Languages list when any
  required resources for that pair are installed; Learning Languages pair and
  required-resource labels now resolve through the GUI locale catalog instead
  of hardcoded English plan labels, and GUI confirmation dialogs now route
  standard buttons such as Yes/No/Cancel/Close through the app locale catalog
  instead of relying on Qt's untranslated standard-button text; Resource
  settings tabs now keep their tab/canvas backdrops transparent to preserve the
  loaded GUI theme, and the shared Settings tab container explicitly paints the
  active theme's panel gradient before drawing any optional background image so
  transparent Resource tabs do not fall through to the Qt scroll viewport/default
  palette; section text hierarchy, buttons, cards, and tables style through
  active theme tokens with contrast-safe foreground fallback instead of
  inheriting dark Qt defaults, floating Resource-settings titles and
  descriptions are contrasted against the settings canvas/background token
  rather than a panel token and use slightly larger text hierarchy for image or
  dark backdrops, Learning Languages pair/resource-slot boxes use translucent
  theme-tinted frames so the corrected backdrop remains visible while the
  resource hierarchy stays readable, detailed resource tables use a theme-schema
  `surface_opacities.table` value with a 0.90 default so table surfaces preserve
  backdrop visibility without losing dense-row readability, and those tables use
  content-width columns with horizontal scrolling below their natural width
  while distributing surplus width into useful text columns instead of leaving a
  blank viewport gutter, and table-cell action buttons use a compact
  theme-aware cell-control style so Download/Select/Delete actions fit cleanly
  inside rows without looking like oversized form buttons; combo-box dropdown
  lists now own and style their actual popup `QListView` plus view/viewport
  palette through the active theme tokens, and the popup list view is frameless
  with zero margins/spacing so dark native popup slivers do not show above or
  below language-pair/theme selectors; Vocabulary Practice
  cards, topic
  panels, curtains, and the Vocabulary Library entry use the same card-theme CSS variable
  path as the rest of Options, the dedicated Vocabulary Library applies the
  selected profile's page background and card-theme preferences, and the
  start-new-story block opens a guided modal that defaults missing proficiency
  to an explicit beginner value, inherits the active profile without exposing a
  profile picker or profile-selection copy, starts each fresh setup opening
  with no topic chips selected,
  lets sampling persist draft preferences without activating the story, renders
  preview results as learner-facing word/topic cards with sanitized technical
  details behind a local Advanced disclosure, and reserves story activation for
  the initialize workflow. Successful delete-story handling now also clears the
  selected
  profile/pair story profile and signals, publishes runtime
  `srsEnabled: false`, reloads the active profile, and hides the current story
  card when the loaded profile is inactive so the deleted story does not
  reappear after refresh. Repeated resource-settings deep-link opens now try the
  GUI single-instance activation channel first, so an already-running app is
  raised and moved to the pair-focused Resource settings state instead of
  spawning another instance; if no GUI is running, the native helper now
  prefers the installed macOS `LexiShift.app` bundle before falling back to the
  source `main.py` development entrypoint, macOS fallback launch no longer
  requests `open -n`, and the resource catalog now carries byte-exact download
  totals for known large/Spanish resources so progress can remain determinate
  even when a server omits `Content-Length`. Options startup now applies the
  selected profile's card-theme and page backdrop immediately after synced
  settings load, before i18n/profile/helper refresh work, so profile visuals no
  longer wait behind the full background preview/status and page initialization
  path; the page-background manager also skips duplicate backdrop/image/position
  DOM writes so late background sync does not repaint the same already-applied
  visual state.
- Last verified: `2026-06-02` focused Vocabulary Library pair-selector/theme-loading/direct-link/implicit-feedback-auto-refresh tests plus
  resource-plan/manual-frequency-policy/native-app-launch checks now extend the
  setup-flow profile inheritance, clean-topic setup opening, sanitized preview
  diagnostics, preview-renderer update, and focused
  delete-story/resource-readiness/preference-save/bridge tests covering
  controller-graph construction order, collapsed selected-story markup,
  hidden active-story word-pool backing controls, initialization-only
  starting-word controls, hidden backing source/target/initialize controls,
  polished direct-library/sampling/inline display-feedback/Advanced markup and ordering,
  previous-proficiency restore binding, beginner-default setup proficiency,
  hidden inherited setup profile with no visible setup profile-selection copy,
  clean setup topic defaults,
  non-activating setup sampling, learner-facing sample preview cards with
  locally toggled advanced diagnostics and no printed local source paths,
	  Vocabulary Practice theme-token CSS contract,
  explicit preference-save controls, right-aligned active-story badge,
  generalized empty preview hiding,
  lazy rulegen status output, hidden SRS enable backing control, removed
  generic installed-data copy,
  story-scoped delete-story copy, switch-styled visible toggles, hidden
  experimental topic tags, hidden advanced challenge tuning, proficiency slider
  markup, active-story technical-status removal, missing-resource setup panel
  markup/controller behavior, native-host pair-aware resource-settings launch
  routing, existing-GUI local activation, installed macOS app launch preference,
  macOS non-`-n` fallback launch,
  GUI resource-tab activation routing, persistent Learning Languages pair card,
  learner-facing Learning Languages card localization,
  per-resource installed-data file-location reveal, required `wiktionary-es-en`
  and `freq-es-spalex-v1` pair resource plan coverage, SPALEX frequency
  download/import catalog coverage, built-in `freq-es-cde` legacy manual-import block,
  downloadable resource progress suppression before download start, downloadable
  resource detail routing, removed pair-card Add manually affordance,
  Learning Languages resource uninstall buttons and installed-resource remove
  confirmation,
  localized Learning Languages pair/resource labels plus recursive GUI i18n
  catalog-shape coverage and localized QMessageBox standard-button coverage,
  resource-tab theme-preserving transparent-canvas, contrast fallback, and
  table sizing coverage plus settings Resource intro-label readability and
  Settings tab-container base-paint coverage plus translucent Learning
  Languages card-frame coverage, resource-table opacity schema/default coverage,
  content-width horizontal-scroll table coverage, responsive surplus-width table
  coverage, compact table-cell action-button coverage, and combo-box popup
  view/palette/frame theme-style coverage,
  persisted selected-pair story deletion,
  inactive-profile current-card hiding, and delete-workflow UI reload after
  helper reset; download-total fallback/catalog tests; raw-source
  `freq-es-cde` managed-import/default-picker/rights-confirmation tests; extension
  structure/i18n checks, doc-reference check, state audit, changed-file gate,
  and diff check pass.
- Default behavior:
  - The Options page still operates on the selected profile and selected
    source/target language pair; it does not yet enumerate every persisted SRS
    profile/pair store.
  - The selected profile/pair practice controls render inside a practice-shaped block
    that is collapsed by default to the language-pair summary and active-pair
    badge; expanding it reveals grouped settings, a direct Vocabulary Library entry, sampling, and
    maintenance for the same visible journey. Inner practice surfaces, topic
    panels, and curtains use the Options card-theme CSS
    variable path instead of fixed beige surfaces.
  - The active story does not repeat a generic explanatory sentence above its
    controls; the summary row carries the pair identity and active badge.
  - The main Vocabulary Practice shell does not show generic installed-data copy; language-data
    readiness messaging should appear in setup, diagnostics, and actionable
    error/status states.
  - If setup sampling or initialization is blocked because required
    language-data resources are missing, the guided modal shows a
    language-data panel with learner-facing missing resource labels, offers to
    open the LexiShift GUI Resource settings tab via the native helper with the
    pair added/focused in the persistent Learning Languages view, and keeps the
    learner in the same setup flow for retry. That view offers app-managed
    dictionary downloads for `wiktionary-es-en` / `freedict-es-en`, the
    app-managed `freq-es-spalex-v1` Spanish frequency download/build path,
    byte-exact catalog download sizes and per-resource determinate progress
    when either the response or catalog has a known total, and offers
    file-location reveal for installed resources. License-restricted legacy
    frequency resources such as `freq-es-cde` remain available in the detailed
    resource tabs for compatibility/manual import, but are not the promoted
    en-es required resource. For `freq-es-cde`,
    selecting a licensed `spanish_lemmas20k.txt` source confirms local-use rights,
    keeps the Import action disabled until the local-use confirmation checkbox
    is checked, starts the file picker in the user's Downloads folder and
    preselects the expected source filename when present,
    stages a temporary copy, converts it into the managed
    `frequency_packs/freq-es-cde/main.sqlite` artifact, writes manifest and
    provenance sidecars, deletes the staged copy, and leaves the user's original
    file untouched. Manual external SQLite path selection also remains available
    in the detailed resource tabs for compatibility. When the GUI is already running,
    the native helper sends the
    pair-focused Resource settings activation message to that process instead
    of launching a second GUI instance; if no GUI is listening, it prefers
    launching the installed macOS `LexiShift.app` bundle before falling back to
    the source development entrypoint. The extension does not download or import packs directly;
    GUI resource management remains the app-owned source of truth for MVP.
  - Source/target language and legacy initialize controls are retained only as
    hidden backing controls for the current controller path; users change
    source/target language through the guided new-story modal instead of editing
    an already-created active story in place. The setup flow inherits the active
    profile through a hidden backing value and does not expose profile selection
    or profile-selection copy as a learner-facing step; setup persistence does
    not change the selected profile from modal state.
  - The legacy SRS enable checkbox is retained only as a hidden backing control;
    users enable a story by completing guided initialization, not by toggling a
    standalone switch.
  - Topic preferences are visible as probability-priority chips without an
    always-visible caveat in the active-story card; the one-time setup flow can
    still show pair-coverage context.
  - Admission sampling renders one helper preview payload into two local views:
    a simple learner-facing list of sampled words with topic/general badges, and
    an Advanced details disclosure containing sanitized diagnostic text. Opening
    or closing the disclosure does not re-run sampling, and local source paths
    are not printed.
  - Free-form advanced tags stay present in the DOM for compatibility but hidden
    from the main MVP surface.
  - The proficiency estimate is presented as a slider with a current value and an
    explicit Save preferences action; the saved value appears as a Previous
    setting row with a restore action, and if no stored estimate exists, the
    slider remains visually neutral while the runtime save/preview path treats it
    as unset until the user moves it.
  - The active story surface exposes a learner-facing active-practice size
    control by default. Vocabulary search range remains a hidden backing value
    for the current controller path and is only visible in the new-story setup
    flow under advanced starting-size controls. Starting-word count is hidden
    from already-created stories and remains visible only in the initialization
    flow.
  - Advanced challenge tuning remains in the DOM for compatibility but is hidden
    from the active-story beta surface.
  - Helper and sentence-fit technical status are not shown inside the active
    practice surface; runtime diagnostics remain in the bottom Advanced debug tools area.
  - The admitted-words embedded dashboard is no longer a learner-facing Options
    surface. The story card links directly to the dedicated Vocabulary Library,
    which is ordered directly after new-word sampling and can switch among the
    selected profile's active language pairs while rendering with that selected
    profile's Options page background and card-theme preferences.
  - New-word sampling remains non-mutating and is hidden until the sampling
    curtain is opened from its summary panel.
  - Display controls include only word highlight color and feedback sound in an
    inline row. Learning-word review buttons and automatic new-word addition
    after feedback are always-on MVP defaults, and manual-ruleset replacement
    feedback remains off/reserved, so none of those three flags are exposed as
    learner-facing toggles.
  - The collapsed active-practice `Advanced` section exposes new-word timing
	    thresholds as same-level controls, followed by `Delete Vocabulary Practice`. The
    delete action uses the existing helper reset route but is presented and
    confirmed as deleting only the selected profile/language-pair story. On
    helper reset success, Options removes the selected pair's persisted SRS
    profile and signal state for the selected profile, publishes runtime
    `srsEnabled: false`, reloads the active profile, and hides the active-story
    card so the deleted story stays gone after refresh. Active-word update
    preview/apply and manual
    learning-word refresh remain backend/dev workflows, but they are not
    promoted in the ordinary learner Options surface.
  - Helper-backed initialize/refresh status output stays hidden until a message
    is available.
  - The guided new-story modal uses the same underlying Options controls and
    helper workflows as the existing page path; it does not introduce a second
    SRS initialization implementation.
  - Modal sampling is non-mutating with respect to SRS admission and persists
    visible preference settings before calling the existing admission preview.
  - Modal initialization enables SRS for the selected story, persists visible
    settings, then calls the existing helper-backed initialize path.
  - Browsing-based admission still has no promoted user-facing opt-in in this
    story surface. The current implementation keeps the hidden
    `srsBrowsingAdmissionSignalsEnabled` flag default-off until production
    admission actually consumes browsing aggregates.
- Evidence:
  - `docs/srs/srs_story_based_options_flow_plan.md`
  - `apps/chrome-extension/options.html`
  - `apps/chrome-extension/options.css`
  - `apps/chrome-extension/options/controllers/srs/story_flow_controller.js`
  - `apps/chrome-extension/options/controllers/srs/story_flow_resource_check.js`
  - `apps/chrome-extension/options/controllers/srs/story_flow_utils.js`
  - `apps/chrome-extension/options/controllers/srs/actions/delete_story_state.js`
  - `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
  - `apps/chrome-extension/options/controllers/srs/actions/shared.js`
  - `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
  - `apps/chrome-extension/options/core/ui_manager.js`
  - `apps/chrome-extension/options/core/helper/base_methods.js`
  - `apps/chrome-extension/shared/helper/helper_client.js`
  - `scripts/helper/lexishift_native_host.py`
  - `core/lexishift_core/helper/gui_app_launch.py`
  - `apps/gui/src/main_runtime.py`
  - `apps/gui/src/main.py`
  - `apps/gui/src/settings_pair_resource_plan.py`
  - `apps/gui/src/settings_language_packs_pair_setup_mixin.py`
  - `core/tests/dev/test_extension_srs_settings_contract.py`
  - `core/tests/dev/test_extension_options_srs_bridge_contract.py`
  - `core/tests/dev/test_native_host_resource_settings.py`
  - `apps/gui/tests/test_pair_resource_plan.py`
  - `apps/gui/tests/test_main_runtime_activation.py`
  - `apps/gui/tests/test_settings_resources_tab.py`
  - `apps/gui/tests/test_main_settings_resource_persistence.py`
- Known gaps:
  - The Options page does not yet enumerate all persisted SRS profile/pair
    stores as separate story blocks.
  - The guided modal is a first beta implementation; it is not yet a full
    multi-step wizard with separate pages or richer pair capability warnings.
  - The technical size labels, advanced preview details, and diagnostic outputs
    have not had their focused product-copy pass.

## Pair-Local Active Inventory

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-04-19` active-inventory observability truth pass
- Last verified: `2026-04-19` targeted inventory-resolution tests plus current-truth doc sync
- Default behavior:
  - Each profile can persist pair-local `active_item_ids` plus `last_initialized_at`, `last_refreshed_at`, and `last_rebalanced_at`.
  - Inventory resolution is intentionally forgiving rather than fully authoritative:
    - if the inventory file is missing or the pair has no entry, active ids fall back to store-derived membership
    - if stored active ids are stale, missing ids are dropped during resolution instead of failing helper/runtime flows
  - Helper initialize/refresh/rebalance/rulegen flows can backfill inventory metadata from store-derived membership when needed.
  - Runtime diagnostics surfaces the current inventory view explicitly through `inventory_source`, the timestamp fields, and `inventory_store_missing_item_ids_count`.
- Evidence:
  - `docs/developer/srs_admission_selective_port_sequence.md`
  - `core/lexishift_core/srs/inventory.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
  - `core/lexishift_core/helper/use_cases/refresh_set.py`
  - `core/lexishift_core/helper/use_cases/rebalance_set.py`
  - `core/lexishift_core/helper/use_cases/rulegen_job.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `core/tests/srs/test_srs_inventory.py`
  - `core/tests/helper/test_helper_engine.py`
- Known gaps:
  - There is still no dedicated drift-repair artifact or hard failure signal for stale inventory state; observability relies on diagnostics plus write-path backfill.
  - Inventory should not be treated as stricter authority than the store until a stronger repair/reporting model is intentionally added.

## Due-Aware SRS Serving

- Status: `implemented`, `default-on when capable`, `verified`
- Last documented checkpoint: `2026-06-07` standard page replacement density restored to permissive defaults for en-es-style browsing density
- Last verified: `2026-06-07` settings-default contract, DOM scan runtime contract,
  replacement-selection contract, SRS resource-budget audit, SRS quality
  harness, and changed-scope state audit
- Default behavior:
  - Scheduler code builds a due queue from `next_due`.
  - Helper rulegen annotates matching SRS rules with `metadata.rulegen.srs`
    due-state metadata plus scheduler load fields when available.
  - Helper publication paths may still publish the active/admitted inventory for the pair, not a separately materialized due subset.
  - The extension SRS gate filters future-due helper SRS rules when due metadata is present.
  - When page budgets, one-per-block, or non-adjacent load constraints are
    active, extension replacement selection prefers new, learning, or
    lower-stability due SRS items over mature or future-due SRS rows inside the
    limited replacement slots.
  - Standard extension page-density defaults are explicit and permissive:
    `maxReplacementsPerPage = 0`, `maxReplacementsPerLemmaPerPage = 0`,
    `allowAdjacentReplacements = true`, and `maxOnePerTextBlock = false`.
  - Metadata-free cached helper rules remain active as a legacy compatibility fallback until regenerated.
- Evidence:
  - `docs/developer/productization_lane5_runtime_seam_inventory.md`
  - `docs/srs/srs_hybrid_model_technical.md`
  - `core/lexishift_core/srs/scheduler.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
  - `core/lexishift_core/helper/use_cases/refresh_set.py`
  - `core/lexishift_core/helper/rulegen.py`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
  - `scripts/testing/srs_quality_harness.py`
  - `core/tests/helper/test_helper_rulegen.py`
  - `core/tests/dev/test_extension_settings_defaults_contract.py`
  - `core/tests/dev/test_extension_replacements_contract.py`
  - `core/tests/dev/test_extension_srs_runtime_gate_contract.py`
  - `core/tests/dev/test_srs_quality_harness.py`
  - `docs/test_outputs/srs_quality_latest.json`
- Known gaps:
  - No dedicated due-only helper ruleset publication artifact is currently tracked here.
  - Legacy metadata-free cached helper rules are intentionally permissive until the helper ruleset is regenerated.
  - Browser/native E2E coverage for automatic feedback-triggered refresh remains
    open beyond helper policy/state tests.
  - `0` remains available as an explicit unlimited override for page and
    per-lemma replacement caps.
  - No durable mastered/released flag is fully implemented yet.
  - Synthetic harness coverage remains pair-limited.

## Extension-Side Confidence Gating For Helper Rules

- Status: `planned`; live helper-rule runtime gating not implemented
- Last documented checkpoint: `2026-04-18` confidence-gating packet and current-truth doc correction
- Last verified: `2026-04-18` targeted runtime contract test plus code-path audit
- Default behavior:
  - Helper rulegen supports generation-time `confidence_threshold` filtering before rules are emitted.
  - Current extension helper-rule runtime path does not inspect `rule.confidence` or apply a live helper-rule confidence threshold before SRS gating.
  - Extension selector utilities can still use item confidence for scoring in other contexts; that is not the helper-rule activation gate.
- Evidence:
  - `docs/developer/project_integrity_sp2_confidence_gating_packet.md`
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/reference/glossary.md`
  - `core/lexishift_core/rulegen/generation.py`
  - `core/lexishift_core/helper/use_cases/rulegen_job.py`
  - `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
  - `apps/chrome-extension/shared/srs/srs_selector.js`
  - `core/tests/dev/test_extension_helper_rule_confidence_contract.py`
- Known gaps:
  - Treat runtime confidence gating as unresolved until a real settings surface, runtime code path, and tests exist for helper-published rules.
  - Do not mark confidence gating as shipped based on docs alone.

## Extension Controller / Runtime Workflow Contracts

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-04-21` SP5/SP6 controller-runtime truth plus the SP7 Share Center compatibility-copy follow-up now keep the post-split options bootstrap, Share Center forwarding bridge, SRS maintenance workflows, and DOM-scan budget/order seams explicit in both architecture docs and operator-facing export copy
- Last verified: `2026-04-21` targeted Node-backed extension workflow tests, Share Center copy contract checks, structure checks, and state/doc safety checks
- Default behavior:
  - The options app bootstrap remains a hard dependency seam: `options.html` script order matters, `options.js` fails fast when required bootstrap/controller modules are missing, and successful startup still binds events before page init.
  - Share Center owns the grouped file-export/file-import UX, but it is still a compatibility bridge over the legacy share backend rather than a second share-schema authority.
  - Current Share Center compatibility mappings stay explicit:
    - `Full profile` export forwards to legacy `profile`
    - `Profile settings` export forwards to legacy `srs`
    - export-modal and target-hint copy now say those are the existing profile / SRS settings formats rather than implying a narrower new schema
    - import only triggers a hard reload when the imported scope mutates broader runtime state; ruleset/modules-only imports resync without reload
  - SRS maintenance workflows forward the active planning/profile context into initialize/refresh/reset helper calls, keep reset double-confirmed, and only mark ruleset freshness when the returned action result actually warrants it.
  - Content full-scan runtime seeds page-budget state from existing replacement spans, then deterministically redistributes node order by page/profile only when page-level budgets are active.
- Evidence:
  - `docs/developer/project_integrity_sp6_feature_state_refresh_packet.md`
  - `docs/architecture/options_controllers_architecture.md`
  - `docs/architecture/extension_system_map.md`
  - `docs/architecture/chrome_extension_technical.md`
  - `apps/chrome-extension/options.js`
  - `apps/chrome-extension/options/controllers/rules/share_center/workflows.js`
  - `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
  - `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
  - `core/tests/architecture/test_extension_structure.py`
  - `core/tests/dev/test_extension_options_bootstrap_contract.py`
  - `core/tests/dev/test_extension_share_center_workflow_contract.py`
  - `core/tests/dev/test_extension_share_center_copy_contract.py`
  - `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py`
  - `core/tests/dev/test_extension_dom_scan_runtime_contract.py`
- Known gaps:
  - Share Center copy now states the compatibility formats explicitly, but if product wants truly narrower `Profile settings` or `Full profile` exports later, that still needs an explicit new schema/version rather than a silent contract change.
  - This seam is now directly protected at the controller/runtime-contract level, but it is still not the same thing as a full browser E2E proof for storage mutation, native-helper latency, or rendered-page UX.

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
2. SRS serving is now due-aware at the runtime gate when helper due metadata is present, but helper publication still uses the broader active/admitted inventory rather than a dedicated due-only artifact.
3. Docs mention runtime confidence filtering, but the live helper-rule runtime still has no confidence gate after emission.
