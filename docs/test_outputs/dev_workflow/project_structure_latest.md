# Project Structure Inventory

Status: generated evidence
Role: Generated evidence
Last updated: 2026-05-15
Purpose: enumerate repository paths and surface structure-review candidates without approving cleanup actions.

This report is read-only evidence. Candidate rows are triage signals, not deletion approval.

## Summary

| Metric | Count |
| --- | ---: |
| `path_count` | 4193 |
| `file_count` | 3910 |
| `directory_count` | 283 |
| `tracked_file_count` | 3884 |
| `untracked_file_count` | 0 |
| `candidate_path_count` | 2447 |
| `duplicate_filename_group_count` | 24 |
| `duplicate_stem_group_count` | 50 |
| `unreferenced_script_candidate_count` | 3 |

## Ignored During Enumeration

Ignored directory names:

- `.bundle`
- `.git`
- `.idea`
- `.jekyll-cache`
- `.mypy_cache`
- `.pytest_cache`
- `.ruff_cache`
- `.sass-cache`
- `.venv`
- `.vscode`
- `__pycache__`
- `env`
- `node_modules`
- `venv`

Ignored relative prefixes:

- `apps/gui/dist`
- `docs/_site`
- `docs/vendor/bundle`
- `packaging/build`
- `packaging/output`

Ignored file names:

- `.DS_Store`
- `.DS_Store?`
- `Thumbs.db`
- `desktop.ini`

## Family Counts

| Family | Paths | Files | Dirs | Bytes |
| --- | ---: | ---: | ---: | ---: |
| `docs_test_outputs` | 2571 | 2413 | 158 | 724930443 |
| `core_tests` | 319 | 307 | 12 | 2710541 |
| `scripts_testing` | 316 | 315 | 1 | 5338898 |
| `app_chrome-extension` | 204 | 161 | 43 | 1369764 |
| `core_runtime` | 152 | 138 | 14 | 1525534 |
| `app_gui` | 115 | 105 | 10 | 175131342 |
| `docs_test_inputs` | 111 | 105 | 6 | 4414512 |
| `docs_developer` | 92 | 91 | 1 | 1275833 |
| `docs_rulegen` | 50 | 49 | 1 | 1299910 |
| `scripts_dev` | 39 | 36 | 3 | 306122 |
| `app_tests` | 33 | 32 | 1 | 147000 |
| `docs_asset` | 22 | 16 | 6 | 216854 |
| `docs_architecture` | 21 | 19 | 2 | 125360 |
| `app_betterdiscord-plugin` | 16 | 14 | 2 | 58698 |
| `docs_language_pairs` | 16 | 15 | 1 | 205945 |
| `scripts_data` | 13 | 12 | 1 | 27095 |
| `docs_srs` | 12 | 11 | 1 | 89275 |
| `docs_runbooks` | 9 | 7 | 2 | 16222 |
| `root_config` | 9 | 9 | 0 | 15238 |
| `scripts` | 9 | 9 | 0 | 35773 |
| `scripts_build` | 8 | 7 | 1 | 38742 |
| `scripts_helper` | 8 | 6 | 2 | 65814 |
| `docs_handbook` | 7 | 6 | 1 | 12748 |
| `docs_root` | 7 | 7 | 0 | 32424 |
| `root_directory` | 7 | 0 | 7 | 0 |
| `docs_archive` | 6 | 4 | 2 | 18224 |
| `docs_gui` | 6 | 5 | 1 | 30976 |
| `docs_getting-started` | 5 | 3 | 2 | 38836 |
| `docs_reference` | 4 | 3 | 1 | 26927 |
| `ci_workflow` | 3 | 2 | 1 | 16177 |
| `app_generated_bundle` | 1 | 1 | 0 | 58377 |
| `data_artifact` | 1 | 1 | 0 | 26648 |
| `diagram` | 1 | 1 | 0 | 1190 |

## Candidate Signal Counts

| Signal | Paths |
| --- | ---: |
| `generated_evidence_output` | 2326 |
| `duplicate_stem` | 1812 |
| `generated_latest_alias` | 1610 |
| `duplicate_filename` | 147 |
| `legacy_or_temporary_name` | 14 |
| `archive_tree` | 5 |
| `unreferenced_script_candidate` | 3 |

## Top Directories

| Path | Paths | Files | Dirs |
| --- | ---: | ---: | ---: |
| `docs/test_outputs` | 2571 | 2413 | 158 |
| `core/tests` | 319 | 307 | 12 |
| `scripts/testing` | 316 | 315 | 1 |
| `apps/chrome-extension` | 204 | 161 | 43 |
| `core/lexishift_core` | 152 | 138 | 14 |
| `apps/gui` | 148 | 137 | 11 |
| `docs/test_inputs` | 111 | 105 | 6 |
| `docs/developer` | 92 | 91 | 1 |
| `docs/rulegen` | 50 | 49 | 1 |
| `scripts/dev` | 39 | 36 | 3 |
| `docs/architecture` | 21 | 19 | 2 |
| `apps/betterdiscord-plugin` | 17 | 15 | 2 |
| `docs/language_pairs` | 16 | 15 | 1 |
| `docs/assets` | 14 | 10 | 4 |
| `scripts/data` | 13 | 12 | 1 |
| `docs/srs` | 12 | 11 | 1 |
| `docs/runbooks` | 9 | 7 | 2 |
| `docs/semantic_routing_html` | 8 | 6 | 2 |
| `scripts/build` | 8 | 7 | 1 |
| `scripts/helper` | 8 | 6 | 2 |
| `docs/handbook` | 7 | 6 | 1 |
| `docs/archive` | 6 | 4 | 2 |
| `docs/gui` | 6 | 5 | 1 |
| `docs/getting-started` | 5 | 3 | 2 |
| `docs/reference` | 4 | 3 | 1 |
| `.github/workflows` | 3 | 2 | 1 |
| `data/TestVocabPool.json` | 1 | 1 | 0 |
| `diagrams/lexishift_flow.mmd` | 1 | 1 | 0 |
| `docs/Gemfile` | 1 | 1 | 0 |
| `docs/Gemfile.lock` | 1 | 1 | 0 |
| `docs/README.md` | 1 | 1 | 0 |
| `docs/TODOs.md` | 1 | 1 | 0 |
| `docs/_config.yml` | 1 | 1 | 0 |
| `docs/index.md` | 1 | 1 | 0 |
| `docs/pack_source_manifest.json` | 1 | 1 | 0 |
| `scripts/README.md` | 1 | 1 | 0 |
| `scripts/backup_profiles_suisui_takeya.sh` | 1 | 1 | 0 |
| `scripts/build_gui_fast_incremental.sh` | 1 | 1 | 0 |
| `scripts/default.profraw` | 1 | 1 | 0 |
| `scripts/package.json` | 1 | 1 | 0 |

## Generated Output Accumulation

| Path | Files | Bytes |
| --- | ---: | ---: |
| `docs/test_outputs/experiments` | 740 | 134988020 |
| `docs/test_outputs/srs_journey` | 24 | 4014369 |
| `docs/test_outputs/dev_workflow` | 14 | 2621010 |
| `docs/test_outputs/ja_en` | 8 | 23864 |
| `docs/test_outputs/phase6_pos_inventory` | 8 | 326878 |
| `docs/test_outputs/licensing_header_audit` | 4 | 589151 |
| `docs/test_outputs/project_health` | 3 | 156089 |
| `docs/test_outputs/phase0_pos_baseline` | 2 | 296613 |
| `docs/test_outputs/baselines` | 1 | 901 |
| `docs/test_outputs/resource_integrity_audit` | 1 | 8898 |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.html` | 1 | 92093 |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | 1 | 190979 |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.md` | 1 | 8739 |
| `docs/test_outputs/rulegen_benchmark_all_pairs_summary_2026-03-21.md` | 1 | 1024 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_family_expansion_latest.json` | 1 | 63891 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_family_expansion_latest.md` | 1 | 1147 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_family_expansion_summary_latest.md` | 1 | 680 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json` | 1 | 58176 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.md` | 1 | 674 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_summary_latest.md` | 1 | 672 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.html` | 1 | 57812 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.json` | 1 | 10819736 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.md` | 1 | 2477 |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_summary_latest.md` | 1 | 714 |
| `docs/test_outputs/rulegen_benchmark_en_de_latest.html` | 1 | 82447 |
| `docs/test_outputs/rulegen_benchmark_en_de_latest.json` | 1 | 151507 |
| `docs/test_outputs/rulegen_benchmark_en_de_latest.md` | 1 | 5024 |
| `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.html` | 1 | 79055 |
| `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.json` | 1 | 224622 |
| `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.md` | 1 | 2258 |
| `docs/test_outputs/rulegen_benchmark_en_de_summary_latest.md` | 1 | 665 |
| `docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.html` | 1 | 52091 |
| `docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.json` | 1 | 41982 |
| `docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.md` | 1 | 1235 |
| `docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.html` | 1 | 11997 |
| `docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.json` | 1 | 336139 |
| `docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.md` | 1 | 2463 |
| `docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.html` | 1 | 58595 |
| `docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.json` | 1 | 201277 |
| `docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.md` | 1 | 715 |

## Duplicate Filenames

| Key | Count | Sample Paths |
| --- | ---: | --- |
| `srs_publication_manifest_en-es.json` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` |
| `srs_rulegen_snapshot_en-es.json` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` |
| `srs_ruleset_en-es.json` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` |
| `srs_semantic_inventory_en-es.json` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` |
| `stopwords-de.json` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/stopwords/stopwords-de.json` |
| `manifest.json` | 14 | `apps/chrome-extension/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/manifest.json` |
| `semantic_inventory.json` | 13 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-006/semantic_inventory.json` |
| `utils.js` | 4 | `apps/chrome-extension/content/ui/utils.js`<br>`apps/chrome-extension/options/controllers/profile/background/utils.js`<br>`apps/chrome-extension/options/controllers/rules/share_center/utils.js`<br>`apps/chrome-extension/options/controllers/ui/target_language_modal/utils.js` |
| `base_methods.js` | 3 | `apps/chrome-extension/options/core/helper/base_methods.js`<br>`apps/chrome-extension/options/core/rules_manager/base_methods.js`<br>`apps/chrome-extension/options/core/settings/base_methods.js` |
| `index.md` | 3 | `docs/getting-started/index.md`<br>`docs/handbook/index.md`<br>`docs/index.md` |
| `samples.json` | 3 | `docs/test_outputs/ja_en/samples_20260203_013949/samples.json`<br>`docs/test_outputs/ja_en/samples_20260203_014029/samples.json`<br>`docs/test_outputs/ja_en/samples_20260203_014116/samples.json` |
| `samples.tsv` | 3 | `docs/test_outputs/ja_en/samples_20260203_013949/samples.tsv`<br>`docs/test_outputs/ja_en/samples_20260203_014029/samples.tsv`<br>`docs/test_outputs/ja_en/samples_20260203_014116/samples.tsv` |
| `.gitignore` | 2 | `.gitignore`<br>`docs/runbooks/cws_preflight_reports/.gitignore` |
| `actions_controller.js` | 2 | `apps/chrome-extension/options/controllers/helper/actions_controller.js`<br>`apps/chrome-extension/options/controllers/srs/actions_controller.js` |
| `cjk_codec.js` | 2 | `apps/betterdiscord-plugin/src/cjk_codec.js`<br>`apps/chrome-extension/options/vendor/cjk_codec.js` |
| `core.py` | 2 | `core/lexishift_core/frequency/core.py`<br>`core/lexishift_core/replacement/core.py` |
| `en_de.json` | 2 | `docs/test_inputs/rulegen_benchmark_cases/en_de.json`<br>`docs/test_inputs/rulegen_lp_profiles/en_de.json` |
| `en_es.json` | 2 | `docs/test_inputs/rulegen_benchmark_cases/en_es.json`<br>`docs/test_inputs/rulegen_lp_profiles/en_es.json` |
| `latest.json` | 2 | `docs/test_outputs/licensing_header_audit/latest.json`<br>`docs/test_outputs/resource_integrity_audit/latest.json` |
| `lzstring.js` | 2 | `apps/betterdiscord-plugin/src/lzstring.js`<br>`apps/chrome-extension/options/vendor/lzstring.js` |
| `pipeline.py` | 2 | `core/lexishift_core/frequency/de/pipeline.py`<br>`core/lexishift_core/replacement/pipeline.py` |
| `srs_selector_test_dataset.json` | 2 | `apps/chrome-extension/shared/srs/srs_selector_test_dataset.json`<br>`docs/srs/srs_selector_test_dataset.json` |
| `ui.js` | 2 | `apps/betterdiscord-plugin/src/ui.js`<br>`apps/chrome-extension/content/ui/ui.js` |
| `workflows.js` | 2 | `apps/chrome-extension/options/controllers/rules/share_center/workflows.js`<br>`apps/chrome-extension/options/controllers/srs/actions/workflows.js` |

## Duplicate Stems

| Key | Count | Sample Paths |
| --- | ---: | --- |
| `srs_publication_manifest_en-es` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` |
| `srs_rulegen_snapshot_en-es` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` |
| `srs_ruleset_en-es` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` |
| `srs_semantic_inventory_en-es` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` |
| `stopwords-de` | 16 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/stopwords/stopwords-de.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/stopwords/stopwords-de.json` |
| `manifest` | 14 | `apps/chrome-extension/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/manifest.json` |
| `semantic_inventory` | 13 | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-006/semantic_inventory.json` |
| `samples` | 6 | `docs/test_outputs/ja_en/samples_20260203_013949/samples.json`<br>`docs/test_outputs/ja_en/samples_20260203_013949/samples.tsv`<br>`docs/test_outputs/ja_en/samples_20260203_014029/samples.json`<br>`docs/test_outputs/ja_en/samples_20260203_014029/samples.tsv`<br>`docs/test_outputs/ja_en/samples_20260203_014116/samples.json`<br>`docs/test_outputs/ja_en/samples_20260203_014116/samples.tsv` |
| `utils` | 5 | `apps/chrome-extension/content/ui/utils.js`<br>`apps/chrome-extension/options/controllers/profile/background/utils.js`<br>`apps/chrome-extension/options/controllers/rules/share_center/utils.js`<br>`apps/chrome-extension/options/controllers/ui/target_language_modal/utils.js`<br>`core/lexishift_core/rulegen/utils.py` |
| `base_methods` | 3 | `apps/chrome-extension/options/core/helper/base_methods.js`<br>`apps/chrome-extension/options/core/rules_manager/base_methods.js`<br>`apps/chrome-extension/options/core/settings/base_methods.js` |
| `en_de` | 3 | `core/lexishift_core/rulegen/pairs/en_de.py`<br>`docs/test_inputs/rulegen_benchmark_cases/en_de.json`<br>`docs/test_inputs/rulegen_lp_profiles/en_de.json` |
| `en_es` | 3 | `core/lexishift_core/rulegen/pairs/en_es.py`<br>`docs/test_inputs/rulegen_benchmark_cases/en_es.json`<br>`docs/test_inputs/rulegen_lp_profiles/en_es.json` |
| `options` | 3 | `apps/chrome-extension/options.css`<br>`apps/chrome-extension/options.html`<br>`apps/chrome-extension/options.js` |
| `rulegen_benchmark_all_pairs_2026-03-21` | 3 | `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.html`<br>`docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json`<br>`docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.md` |
| `rulegen_benchmark_en_de_kaikki_tuning_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.md` |
| `rulegen_benchmark_en_de_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_de_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_de_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_de_latest.md` |
| `rulegen_benchmark_en_de_source_freq_experiment_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.md` |
| `rulegen_benchmark_en_es_en_ja_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_en_ja_latest.md` |
| `rulegen_benchmark_en_es_expanded_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_expanded_latest.md` |
| `rulegen_benchmark_en_es_freedict_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_freedict_latest.md` |
| `rulegen_benchmark_en_es_kaikki_bidir_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_latest.md` |
| `rulegen_benchmark_en_es_kaikki_bidir_reverse_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_reverse_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_reverse_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_bidir_reverse_latest.md` |
| `rulegen_benchmark_en_es_kaikki_freedict_reverse_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_freedict_reverse_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_freedict_reverse_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_freedict_reverse_latest.md` |
| `rulegen_benchmark_en_es_kaikki_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_latest.md` |
| `rulegen_benchmark_en_es_kaikki_noreverse_current_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_noreverse_current_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_noreverse_current_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_noreverse_current_latest.md` |
| `rulegen_benchmark_en_es_kaikki_policy_experiment_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_experiment_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_experiment_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_experiment_latest.md` |
| `rulegen_benchmark_en_es_kaikki_policy_scale_experiment_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_scale_experiment_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_scale_experiment_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_kaikki_policy_scale_experiment_latest.md` |
| `rulegen_benchmark_en_es_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_latest.md` |
| `rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_ambiguity_experiment_latest.md` |
| `rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.md` |
| `rulegen_benchmark_en_es_reverse_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.md` |
| `rulegen_benchmark_en_es_reverse_recheck_latest` | 3 | `docs/test_outputs/rulegen_benchmark_en_es_reverse_recheck_latest.html`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_recheck_latest.json`<br>`docs/test_outputs/rulegen_benchmark_en_es_reverse_recheck_latest.md` |
| `rulegen_benchmark_expanded_smoke` | 3 | `docs/test_outputs/rulegen_benchmark_expanded_smoke.html`<br>`docs/test_outputs/rulegen_benchmark_expanded_smoke.json`<br>`docs/test_outputs/rulegen_benchmark_expanded_smoke.md` |
| `rulegen_benchmark_latest` | 3 | `docs/test_outputs/rulegen_benchmark_latest.html`<br>`docs/test_outputs/rulegen_benchmark_latest.json`<br>`docs/test_outputs/rulegen_benchmark_latest.md` |
| `rulegen_benchmark_polysemic_demotion_latest` | 3 | `docs/test_outputs/rulegen_benchmark_polysemic_demotion_latest.html`<br>`docs/test_outputs/rulegen_benchmark_polysemic_demotion_latest.json`<br>`docs/test_outputs/rulegen_benchmark_polysemic_demotion_latest.md` |
| `srs_journey_en_es_edge_latest` | 3 | `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.html`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.json`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.md` |
| `srs_journey_en_es_installed_latest` | 3 | `docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.html`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.json`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_installed_latest.md` |
| `srs_journey_en_es_latest` | 3 | `docs/test_outputs/srs_journey/srs_journey_en_es_latest.html`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_latest.json`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_latest.md` |
| `srs_journey_en_es_real_latest` | 3 | `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.html`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.json`<br>`docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.md` |
| `srs_journey_en_ja_edge_latest` | 3 | `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.html`<br>`docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.json`<br>`docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.md` |

## Unreferenced Script Candidates

| Path | Family | Exact refs | Stem refs | Package script |
| --- | --- | ---: | ---: | --- |
| `scripts/dev/srs_selector_demo.py` | `scripts_dev` | 0 | 0 | False |
| `scripts/dev/test_embeddings.py` | `scripts_dev` | 0 | 0 | False |
| `scripts/testing/semantic_shadow_review_queue_en_es.py` | `scripts_testing` | 0 | 0 | False |

## Candidate Path Sample

| Path | Family | Signals |
| --- | --- | --- |
| `.gitignore` | `root_config` | duplicate_filename, duplicate_stem |
| `apps/betterdiscord-plugin/src/cjk_codec.js` | `app_betterdiscord-plugin` | duplicate_filename, duplicate_stem |
| `apps/betterdiscord-plugin/src/lzstring.js` | `app_betterdiscord-plugin` | duplicate_filename, duplicate_stem |
| `apps/betterdiscord-plugin/src/ui.js` | `app_betterdiscord-plugin` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/content/ui/ui.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/content/ui/utils.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/manifest.json` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/helper/actions_controller.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/profile/background/utils.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/rules/share_center/utils.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/rules/share_center/workflows.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/srs/actions/workflows.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/srs/actions_controller.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/controllers/ui/target_language_modal/utils.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/core/helper/base_methods.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/core/rules_manager/base_methods.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/core/settings/base_methods.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/vendor/cjk_codec.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/options/vendor/lzstring.js` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `apps/chrome-extension/shared/srs/srs_selector_test_dataset.json` | `app_chrome-extension` | duplicate_filename, duplicate_stem |
| `core/lexishift_core/frequency/core.py` | `core_runtime` | duplicate_filename, duplicate_stem |
| `core/lexishift_core/frequency/de/pipeline.py` | `core_runtime` | duplicate_filename, duplicate_stem |
| `core/lexishift_core/replacement/core.py` | `core_runtime` | duplicate_filename, duplicate_stem |
| `core/lexishift_core/replacement/pipeline.py` | `core_runtime` | duplicate_filename, duplicate_stem |
| `docs/runbooks/cws_preflight_reports/.gitignore` | `docs_runbooks` | duplicate_filename, duplicate_stem |
| `docs/srs/srs_selector_test_dataset.json` | `docs_srs` | duplicate_filename, duplicate_stem |
| `docs/test_inputs/rulegen_benchmark_cases/en_de.json` | `docs_test_inputs` | duplicate_filename, duplicate_stem |
| `docs/test_inputs/rulegen_benchmark_cases/en_es.json` | `docs_test_inputs` | duplicate_filename, duplicate_stem |
| `docs/test_inputs/rulegen_lp_profiles/en_de.json` | `docs_test_inputs` | duplicate_filename, duplicate_stem |
| `docs/test_inputs/rulegen_lp_profiles/en_es.json` | `docs_test_inputs` | duplicate_filename, duplicate_stem |
| `docs/test_outputs/ja_en/samples_20260203_013949/samples.tsv` | `docs_test_outputs` | duplicate_filename, duplicate_stem |
| `docs/test_outputs/ja_en/samples_20260203_014029/samples.tsv` | `docs_test_outputs` | duplicate_filename, duplicate_stem |
| `docs/test_outputs/ja_en/samples_20260203_014116/samples.tsv` | `docs_test_outputs` | duplicate_filename, duplicate_stem |
| `docs/getting-started/index.md` | `docs_getting-started` | duplicate_filename |
| `docs/handbook/index.md` | `docs_handbook` | duplicate_filename |
| `docs/index.md` | `docs_root` | duplicate_filename |
| `apps/betterdiscord-plugin/src/state.js` | `app_betterdiscord-plugin` | duplicate_stem |
| `apps/chrome-extension/options.css` | `app_chrome-extension` | duplicate_stem |
| `apps/chrome-extension/options.html` | `app_chrome-extension` | duplicate_stem |
| `apps/chrome-extension/options.js` | `app_chrome-extension` | duplicate_stem |
| `apps/chrome-extension/options/controllers/rules/share_center/status.js` | `app_chrome-extension` | duplicate_stem |
| `apps/gui/build/pyinstaller/PYZ-00.pyz` | `app_gui` | duplicate_stem |
| `apps/gui/build/pyinstaller/PYZ-00.toc` | `app_gui` | duplicate_stem |
| `apps/gui/build/pyinstaller/PYZ-01.pyz` | `app_gui` | duplicate_stem |
| `apps/gui/build/pyinstaller/PYZ-01.toc` | `app_gui` | duplicate_stem |
| `apps/gui/resources/ttbn.icns` | `app_gui` | duplicate_stem |
| `apps/gui/resources/ttbn.ico` | `app_gui` | duplicate_stem |
| `apps/gui/src/pack_source_manifest.py` | `app_gui` | duplicate_stem |
| `apps/gui/src/state.py` | `app_gui` | duplicate_stem |
| `core/lexishift_core/helper/status.py` | `core_runtime` | duplicate_stem |
| `core/lexishift_core/rulegen/pairs/en_de.py` | `core_runtime` | duplicate_stem |
| `core/lexishift_core/rulegen/pairs/en_es.py` | `core_runtime` | duplicate_stem |
| `core/lexishift_core/rulegen/pairs/en_ja.py` | `core_runtime` | duplicate_stem |
| `core/lexishift_core/rulegen/pairs/es_en.py` | `core_runtime` | duplicate_stem |
| `core/lexishift_core/rulegen/utils.py` | `core_runtime` | duplicate_stem |
| `docs/Gemfile` | `docs_root` | duplicate_stem |
| `docs/Gemfile.lock` | `docs_root` | duplicate_stem |
| `docs/architecture/diagrams/DG-01_data_ownership_storage_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/architecture/diagrams/DG-02_settings_propagation_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/architecture/diagrams/DG-03_rule_resolution_dom_pipeline_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/architecture/diagrams/DG-04_feedback_eventual_sync_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/architecture/diagrams/DG-05_srs_init_refresh_control_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/architecture/diagrams/DG-06_helper_availability_state_as_is.mmd` | `docs_architecture` | duplicate_stem |
| `docs/assets/diagrams/DG-01_data_ownership_storage_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/assets/diagrams/DG-02_settings_propagation_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/assets/diagrams/DG-03_rule_resolution_dom_pipeline_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/assets/diagrams/DG-04_feedback_eventual_sync_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/assets/diagrams/DG-05_srs_init_refresh_control_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/assets/diagrams/DG-06_helper_availability_state_as_is.svg` | `docs_asset` | duplicate_stem |
| `docs/pack_source_manifest.json` | `docs_root` | duplicate_stem |
| `docs/semantic_routing_html/assets/veto_e2e.mjs` | `docs_asset` | duplicate_stem |
| `docs/semantic_routing_html/veto_e2e.html` | `docs_asset` | duplicate_stem |
| `docs/test_inputs/rulegen_benchmark_cases/en_ja.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/rulegen_benchmark_cases/es_en.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/rulegen_benchmark_presets.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_decision_rule_matrix_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_active_only_live_page_scan_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_evidence_gap_active_only_poc_requests_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_evidence_gap_control_pilot_plan_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_formula_shape_bakeoff_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_inputs/semantic_veto_sampling_expansion_design_en_es.json` | `docs_test_inputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-002-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-003-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-004-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-005-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-006-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-007-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-008-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-009-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-010-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-en-es-active-only-full-v1-tranche-011-approved_raw_responses.jsonl` | `docs_test_outputs` | duplicate_stem |
| `scripts/testing/rulegen_benchmark_presets.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_decision_rule_matrix_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_shadow_experiment_matrix_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_active_only_live_page_scan_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_evidence_gap_active_only_poc_requests_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_evidence_gap_control_pilot_plan_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_formula_shape_bakeoff_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.py` | `scripts_testing` | duplicate_stem |
| `scripts/testing/semantic_veto_sampling_expansion_design_en_es.py` | `scripts_testing` | duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-001/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-001-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-002/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-002-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-003/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-003-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-004/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-004-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-005/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-005-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-006/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-006/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_ruleset_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/profiles/default/srs_semantic_inventory_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-006-product-install-data-root/srs/stopwords/stopwords-de.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-007/manifest.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-007/semantic_inventory.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
| `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-007-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs_test_outputs` | generated_evidence_output, duplicate_filename, duplicate_stem |
