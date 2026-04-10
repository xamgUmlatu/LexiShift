# Feature State Matrix

Status: active ledger
Role: Canonical current
Last updated: 2026-04-10
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
- Last documented checkpoint: `2026-04-04` benchmark case authoring now uses LP-specific source files under `docs/test_inputs/rulegen_benchmark_cases/`, the benchmark/gate loader now accepts either a single JSON file or that directory directly, pair-scoped dataset validation now stays local to the selected LP, and bundle export now materializes a merged dataset JSON for replay
- Last verified: `2026-04-04` focused dataset-loader/gate/bundle tests plus local `en-de` benchmark/gate/triage refresh on the directory-backed dataset
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
- Last documented checkpoint: `2026-04-03` FreeDict app-managed translation packs now build to canonical SQLite, translation pack refs honor managed manifests, helper rulegen debug and installed journey staging both use the normalized translation-pack seam, helper/runtime expose a first frequency pack-ref seam, app-state normalization migrates old managed embedding paths into pack-id-first per-pair activation, the settings UI now makes the installed-vs-manual resource boundary explicit, the settings panel now keeps managed translation/frequency ids separate from manual path maps internally, and the mixed language-pack surface now uses an explicit language-resource binding layer that now also drives the table/delete/autolink seam directly
- Last verified: `2026-04-03` targeted helper/resource/frequency/synonym/SRS-harness/journey-installed tests plus GUI/core compile verification for FreeDict SQLite conversion, manifest-backed translation resolution, translation-pack ref resolution, helper debug translation-pack diagnostics, journey installed-pack staging, German frequency whitelist discovery, synonym loading through shared translation-pack loaders, SQLite-first synthetic quality/journey harness resources, frequency manifests, frequency pack-ref/runtime-diagnostics reporting, the shared configured frequency-pack resolver now used by GUI SRS growth and the POS probe, app-managed embedding conversion/manifests, embedding pack-id activation/runtime resolution, managed-embedding settings persistence cleanup, embedding path-migration tests, helper/native-host/internal translation-dictionary seam cleanup, settings/state migration tests for managed translation/frequency/embedding pack ids, settings-panel managed/manual state-split coverage for translation/frequency, language-resource binding coverage for the mixed language-pack surface, direct binding-driven language-pack table coverage, `main.sqlite` convergence for managed translation and frequency installs with legacy fallback coverage, settings-table installed/manual status coverage, and an SRS quality harness refresh
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
    - helper/runtime now expose a first frequency pack-ref seam so pair-resource resolution and runtime diagnostics can report frequency pack id, provider, and POS source profile instead of only a raw SQLite path
    - GUI SRS growth and the POS normalization probe now share a configured frequency-pack resolver from the helper layer instead of each carrying their own managed-id/manual-path/fallback path logic
    - app-managed translation installs now converge on `language_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `<pack_id>.sqlite` filenames for older local installs
    - app-managed frequency installs now converge on `frequency_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `freq-*.sqlite` filenames for older local installs
    - GUI embedding-pack downloads now install into stable per-pack roots under `embedding_packs/<pack_id>/`
    - app-managed embedding-pack downloads now normalize to SQLite and write `manifest.json` only after successful conversion
    - successful app-managed embedding conversion now treats SQLite as the canonical installed artifact and cleans up the raw downloaded vector file
    - managed embedding activation can now be persisted by pack id per pair, and the replacement-filter runtime resolves those pack ids back through manifest-backed SQLite artifacts
    - app-state load/update now migrates old saved managed embedding artifact paths into pack-id-first per-pair activation and strips those app-owned paths from the manual embedding maps
    - managed translation settings now persist normalized app-owned translation packs by pack id while the saved manual `language_pack_paths` map omits those managed artifact paths
    - managed frequency settings now persist app-owned frequency packs by pack id while the saved manual `frequency_pack_paths` map omits those managed artifact paths
    - app-state load/update now migrates old saved managed translation/frequency artifact paths into that split representation
    - the settings panel now keeps managed translation/frequency ids in dedicated in-memory sets instead of reconstructing those ids from unified path maps on save
    - the mixed language-pack settings surface now keeps explicit `LanguageResourceBinding` records for managed translation packs plus secondary/manual entries, and dialog persistence can derive managed ids plus manual paths from those bindings
    - the language-pack table, delete flow, and auto-link path now consume those `LanguageResourceBinding` records directly, and the language-pack tab now explicitly states that app-managed packs are the default while manual selection is a temporary compatibility path
    - bulk-rules translation loading and source-stat reporting now use a shared configured language-pack resolver to rebuild managed translation artifacts from stored pack ids before falling back to manual path maps, while SRS growth rebuilds managed default frequency artifacts from stored pack ids before falling back to manual paths
    - the settings panel now omits redundant managed embedding artifact paths from saved settings when those installs are already represented by pack id + manifest-backed resolution
    - settings serialization now writes explicit `language_pack_paths`, `frequency_pack_paths`, and `embedding_pack_paths` keys instead of the older generic `*_packs` path maps
    - the settings UI now labels app-owned resolved resources as installed artifacts and external/manual paths as manual inputs, with embedding activation explicitly distinguishing active installed vs active manual rows
  - Current runtime contract is still transitional rather than final:
    - FreeDict and Kaikki translation packs now expose SQLite as the canonical app-managed runtime artifact, but manual TEI files, older extracted directories, and legacy `<pack_id>.sqlite` filenames remain compatibility inputs during migration
    - normalized translation/frequency settings are now pack-id-first for the mandatory managed families, but secondary language-pack families still keep path-shaped settings until their promotion decision is made
    - frequency packs already expose SQLite, and new app-managed installs now use `main.sqlite`, but legacy `freq-*.sqlite` names still remain valid fallback paths during migration
    - embedding runtime still accepts raw `.vec/.bin` paths as a compatibility path for manually supplied external files
    - managed embedding settings/runtime are now pack-id-first for app-owned installs, while manual raw/vector and external SQLite paths remain separate compatibility/import inputs
    - broad manual file-path selection is not a promoted product feature; it is a transitional compatibility surface and likely phase-out candidate unless a concrete use case survives
- Evidence:
  - `docs/developer/data_source_normalization_architecture.md`
  - `docs/developer/language_pair_generalization_roadmap.md`
  - `docs/language_pairs/de_en_workstream_roadmap.md`
  - `apps/gui/src/language_packs_catalog.py`
  - `apps/gui/src/language_packs.py`
  - `apps/gui/src/settings_language_packs_path_mixin.py`
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/src/settings_language_packs_support.py`
  - `core/lexishift_core/helper/translation_packs.py`
  - `core/lexishift_core/helper/frequency_packs.py`
  - `core/lexishift_core/helper/embedding_packs.py`
  - `core/lexishift_core/helper/pair_resources.py`
  - `core/lexishift_core/helper/installed_packs.py`
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `apps/gui/src/main_srs_mixin.py`
  - `apps/gui/src/main_replacement_filter_mixin.py`
  - `apps/gui/src/dialogs.py`
  - `core/lexishift_core/persistence/settings.py`
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
  - `apps/gui/tests/test_language_pack_path_mixin.py`
  - `apps/gui/tests/test_state_resource_settings_migration.py`
  - `core/tests/helper/test_embedding_packs.py`
  - `core/tests/dev/test_srs_harness_resource_normalization.py`
  - `core/tests/frequency/test_de_build_support.py`
  - `core/tests/resources/test_dict_loaders_freedict_pos.py`
  - `core/tests/resources/test_synonyms_translation_packs.py`
- Known gaps:
  - Installed-pack resolution is only partially manifest-driven today; generic helper/runtime resolution and GUI auto-link use it for translation and frequency defaults, shared translation pack refs now honor manifests, but broader benchmark/probe consumers still include legacy path assumptions.
  - FreeDict packs are still effectively runtime-addressed through TEI-compatible paths in some benchmark/tooling flows even though app-managed installs now build to SQLite and the main helper/GUI/harness consumers now prefer SQLite-first paths.
  - Managed embedding activation no longer needs persisted app-owned artifact paths, but parts of the settings UI still build temporary path maps internally before splitting managed ids back out on save.
  - Manual external embedding files still bypass the managed-pack manifest layout by design during migration.
  - Frequency packs still preserve their legacy `freq-*.sqlite` artifact names as fallback paths during migration.
  - Translation consumers still include TEI-compatible assumptions in some benchmark/tooling paths, but the shared loader-backed or SQLite-first consumers now include rulegen pairs, helper/runtime diagnostics, the German frequency whitelist, synonym generation, the bulk-rules GUI path, and the synthetic SRS quality/journey harnesses plus installed journey staging.

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
- Last documented checkpoint: `2026-04-04` `en-de` now has a real Kaikki tuning lane, same-sense representative selection, German register/family enrichment, and an experimental sense-level defaultness penalty in addition to the earlier source-frequency, reverse-check, and Kaikki-policy scaffolding
- Last verified: `2026-04-10` feature-state evidence sync against the clean branch after preserving the separate `en-de` benchmark WIP branch
- Default behavior:
  - `en-de` now has a first-class advisory benchmark/gate/triage surface separate from the canonical strict `en-es` lane.
  - The dedicated `en-de` gate now runs in pair-scoped mode, so it no longer reports missing required/recommended-pair or no-delta-overlap noise from unrelated benchmark lanes.
  - The lane now uses a named preset:
    - `en_de_canonical_matrix`
  - `en-de` now also has an experimental default-off source-frequency prior:
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
  - The current lane intentionally stays baseline:
    - no reverse-check in the canonical advisory latest lane
    - no promoted `en-de` Kaikki default source path yet
    - dataset-expansion and lexical-choice cleanup come before pair-specific frontier work
- Evidence:
  - `docs/language_pairs/en_de_workstream_roadmap.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/package.json`
  - `docs/test_inputs/rulegen_benchmark_presets.json`
  - `docs/test_outputs/rulegen_benchmark_en_de_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_en_de_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_de_latest.json`
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
  - `scripts/data/convert_kaikki_de_en_to_sqlite.py`
  - `scripts/testing/rulegen_probe_words.py`
  - `core/tests/rulegen/test_rulegen_adapters.py`
  - `core/tests/dev/test_rulegen_probe_words.py`
  - `core/tests/resources/test_kaikki_sqlite_conversion.py`
- Known gaps:
  - `en-de` remains advisory and is still not part of `required_benchmark_pairs`.
  - The benchmark case set is now broader at `58` targets, but the current `en-de` latest run is still well below the configured top-1 floor (`65.52%` top1, `93.10%` top3).
  - The current `en-de` latest triage surface is still heavy at `21` actionable items (`16` FAIL, `5` REVIEW), including hard junk-gloss failures such as `Zeit -> spell`, `Sprache -> diction`, `Fenster -> box`, and `Tag -> tag`.
  - The dedicated `en-de` gate is now pair-scoped, but delta checks still warn until an `en-de` baseline is accepted:
    - `DELTA_SCOPE_BASELINE_MISSING`
  - `en-de` now has default-off reverse-check plumbing and probe support, but the first focused Kaikki reverse experiment did not beat `rev=off` (`93.10%` top1 / `96.55%` top3 -> `91.38%` / `96.55%` with the tested reverse setting).
  - The new source-frequency prior is measurable but not sufficient on its own:
    - focused experiment improved `top3` (`93.10%` -> `98.28%`) without moving `top1` (`65.52%`)
    - the mechanism currently helps expected answers re-enter top3 (`Grund`, `Straße`, `Zug`) more than it fixes junk top1 defaults
  - `wiktionary-de-en` download/build support now exists, and the local Kaikki tuning lane is strong (`93.10%` top1 / `96.55%` top3), but it is still a local advisory comparison rather than a promoted default source path or accepted scoped baseline.
  - The current best local Kaikki `en-de` config still leaves the richer parity signals off:
    - `rev=off`
    - `kdem=off`
    - `kprov=off`
  - Same-sense representative selection is now a real frontier mover in local Kaikki runs, but the first sense-level defaultness penalty (`sdcmp`) proved too blunt to help.
  - `en-de` now has a compiled resource context, candidate-row IR, and live/compiled prepared score-table plus selected-row sweep coverage, but it still lacks the fuller `en-es` prepared benchmark stack and the richer `en-es`-style provenance competition layer.
  - Practical initialize/refresh work for the German-target lane still needs the missing `freq-de-default.sqlite` resource even though the benchmark lane itself can run.

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
- Last verified: `2026-04-10` feature-state evidence sync against the clean branch after preserving the separate `en-de` benchmark WIP branch
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
  - `docs/rulegen/reverse_check_en_es_case_review_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`
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
- Last documented checkpoint: `2026-03-26`
- Last verified: `2026-03-26` planning review against current benchmark and Kaikki architecture
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
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/kaikki_views.py`
  - `core/lexishift_core/rulegen/ranking.py`
- Known gaps:
  - There is no shared runtime trait extractor yet.
  - Benchmark artifacts do not yet emit per-case feature vectors.
  - No profile bank or interpretable router is implemented.
  - Current dataset size is still better suited to coarse directional experiments than fine-grained routed-policy learning.
  - Learner-stage-aware routing is only conceptual at this point and must stay separate from lexical trait inference.

## Semantic Routing Runtime Admission Layer

- Status: `planned`; publication/payload scaffolding is implemented, `en-es` has a narrow competition-set publication PoC, and there are now research-only `en-es` shadow inventory, triage, and policy-comparison artifacts, but no LP emits a live semantic-routing admission policy by default
- Last documented checkpoint: `2026-04-10` added a reviewed-trigger-overlap gold-proxy grader for `en-es` auto shadow promotion
- Last verified: `2026-04-10` targeted `semantic_shadow_inventory` / `semantic_shadow_evaluation` tests plus refreshed `en-es` shadow inventory/policy-comparison/review-queue/gap-queue/review-packet/gold-proxy artifacts and doc/state sync
- Default behavior:
  - No semantic-routing admission layer is active in the browser runtime today.
  - Current runtime replacement behavior is still driven by rule emission plus existing SRS gating, not by sentence-level sense competition.
  - The repo now has passive semantic-routing publication scaffolding:
    - `metadata.semantic_admission` can be emitted on rules
    - helper publication can write a semantic inventory sidecar
    - runtime diagnostics can inspect both pointer coverage and sidecar coverage
  - That scaffolding does not mean semantic routing is active.
  - `en-es` now has a narrow publication PoC:
    - if real sibling senses for the same trigger are present in the same emitted result batch, `metadata.semantic_admission.status` can be promoted to `ready`
    - the semantic inventory then publishes `competition_sets` with `selection_mode=automatic` and `selection_policy_version=en_es_emitted_rule_siblings_v1`
  - That PoC is intentionally limited to emitted siblings already present in the batch; it is not full shadow mining.
  - `en-es` now also has a research-only shadow inventory path:
    - `scripts/testing/semantic_shadow_inventory_en_es.py` mines sibling candidates from reviewed benchmark trigger phrases plus installed translation packs
    - `scripts/testing/semantic_shadow_inventory_triage_en_es.py` scores the resulting preview into `benchmark_aligned`, `same_pos_only`, and `no_promotion` buckets
    - `scripts/testing/semantic_shadow_policy_compare_en_es.py` compares named promotion policies (`same_pos_lenient_v1`, `benchmark_backed_v1`, `cross_checked_v1`, `cross_checked_backoff_missing_active_v1`)
    - `scripts/testing/semantic_shadow_policy_gap_queue_en_es.py` isolates the small set of rows that the stricter policy still drops
    - `scripts/testing/semantic_shadow_review_packet_en_es.py` combines the policy snapshot, provisional keep rows, and provisional drop rows into one adjudication packet
    - `scripts/testing/semantic_shadow_gold_proxy_en_es.py` grades the current policies against a reviewed-trigger-overlap gold proxy derived directly from `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
    - the latest artifacts confirm that candidate mining works broadly enough to study, and the safer provisional runtime shape is now effectively the strict `cross_checked_v1` family: after active-side bundled-trigger matching was fixed, `cross_checked_backoff_missing_active_v1` no longer widens the promoted set and `coger / catch -> vista` falls out of the review queue
    - the new gold-proxy artifact gives the first explicit lower-bound grading surface for automation quality, without claiming sentence-level semantic-veto readiness
    - current lower-bound read from that proxy:
      - `cross_checked_v1` / `cross_checked_backoff_missing_active_v1`: `54.5%` candidate precision, `60.0%` candidate recall, `60.0%` gold-trigger hit rate, `3.6%` overblocking rate
      - candidate-pool recall is also `60.0%`, which means mining coverage is now at least as important as promotion strictness
  - The intended future direction is a conservative admission layer that can choose among:
    - hard replace
    - soft affordance / annotation
    - abstain
  - The governing product preference for that future layer is explicit:
    - false abstain is cheaper than harmful replacement
  - Before any rollout, the project still needs:
    - active-sense provenance carried from rulegen into runtime-consumable metadata
    - automatic sibling-shadow candidate mining and a small promotion policy
    - phrase/idiom preemption as a separate lane from semantic veto
    - runtime observability for why a replacement applied or abstained
- Evidence:
  - `docs/rulegen/semantic_routing_runtime_readiness.md`
  - `docs/rulegen/semantic_routing_publication_contract.md`
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/architecture/extension_system_map.md`
  - `docs/getting-started/index.md`
  - `docs/srs/srs_roadmap.md`
  - `core/lexishift_core/replacement/core.py`
  - `core/lexishift_core/persistence/storage.py`
  - `core/lexishift_core/helper/paths.py`
  - `core/lexishift_core/helper/rulegen_outputs.py`
  - `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
  - `core/lexishift_core/rulegen/semantic_publication.py`
  - `core/lexishift_core/rulegen/semantic_shadow_inventory.py`
  - `core/lexishift_core/rulegen/semantic_shadow_evaluation.py`
  - `core/tests/rulegen/test_semantic_publication.py`
  - `core/tests/rulegen/test_semantic_shadow_inventory.py`
  - `core/tests/rulegen/test_semantic_shadow_evaluation.py`
  - `scripts/testing/semantic_shadow_inventory_en_es.py`
  - `scripts/testing/semantic_shadow_inventory_triage_en_es.py`
  - `scripts/testing/semantic_shadow_policy_compare_en_es.py`
  - `scripts/testing/semantic_shadow_policy_gap_queue_en_es.py`
  - `scripts/testing/semantic_shadow_review_packet_en_es.py`
  - `scripts/testing/semantic_shadow_gold_proxy_en_es.py`
  - `docs/test_outputs/semantic_shadow_inventory_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_inventory_triage_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_policy_compare_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_policy_gap_queue_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_review_packet_en_es_latest.md`
  - `docs/test_outputs/semantic_shadow_gold_proxy_en_es_latest.md`
- Known gaps:
  - No LP default path emits a fully mined competition/shadow set yet.
  - All current rulegen LPs can now emit stable active-pointer ids in `metadata.semantic_admission`, but pointer strength differs by locator mode:
    - `en-es` / `en-de`: source-sense provenance first, with FreeDict gloss fallback
    - `de-en` / `es-en`: deterministic FreeDict gloss-slot locator
    - `en-ja`: deterministic JMDict entry locator
  - `en-es` can now emit `status=ready` in the explicit `emitted_rule_siblings` PoC mode, but that is still narrower than true shadow promotion and should not be read as end-to-end runtime readiness.
  - Helper publication can now generate a semantic inventory sidecar with pair capability summary, and `en-es` can publish ready competition sets in the emitted-sibling PoC, but current default output still does not include mined shadow sets or phrase-preemption inventory.
  - The first live `en-es` shadow inventory artifact proves that broad sibling mining is feasible, but its current promoted-shadow preview is still too noisy to serve as a runtime blocker set.
  - The first triage artifact shows that the stricter preview can eliminate zero-signal rows, but the remaining top-1 promotions are still mostly justified only by `same_pos_as_active`, not by clearly benchmark-aligned competition evidence.
  - The first policy-comparison artifact makes the current algorithm tradeoff concrete:
    - `same_pos_lenient_v1` is broad but noisy
    - `benchmark_backed_v1` and especially `cross_checked_v1` are much cleaner, but probably too narrow to serve as the final default without more shadow evidence
  - The newest active-trigger refinement made the provisional policy safer:
    - bundled forward glosses can now supply active evidence for bare triggers like `take` and `catch`
    - benchmark-only shadows are no longer rescued when the active side is completely empty
    - `cross_checked_backoff_missing_active_v1` now converges to the same promoted set as `cross_checked_v1` on the latest `en-es` artifacts
  - There is no phrase-preemption lane separated from semantic-veto serving.
  - There is no runtime decision policy yet for hard replace vs soft affordance vs abstain.
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
  - `profile_bootstrap`: `scaffolded`
  - `profile_growth`: `scaffolded`
  - `adaptive_refresh`: `scaffolded`
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Executable behavior remains frequency bootstrap.
  - Profile-aware strategies still fall back to planning-only or frequency-bootstrap execution.
- Evidence:
  - `docs/srs/srs_set_planning_technical.md`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
- Known gaps:
  - Planner diagnostics are ahead of executable strategy diversity.
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
4. Planner docs describe multiple strategies, but executable behavior is still dominated by frequency bootstrap.
