# Data Source Normalization Execution Order

Status: active execution roadmap
Role: ordered implementation plan
Purpose: turn the normalization architecture target into an explicit, resumable sequence of remaining work.
Last updated: 2026-04-03
Last verified: 2026-04-03 code/doc review after FreeDict SQLite install normalization, German frequency whitelist migration, synonym-loader migration, manifest-backed translation pack refs, helper debug/journey-installed translation-pack seam cleanup, the first frequency pack-ref/runtime-diagnostics seam slice, the first embedding pack-id activation/runtime-resolution slice, the internal helper translation-dictionary seam cleanup, benchmark split cleanup, generic helper alias removal, the synonym translation-pack seam cleanup, and the settings UI installed-vs-manual resource classification pass
Source-of-truth: planning/execution guide only; runtime truth still lives in code, tests, and `feature_state_matrix.md`.

## Compatibility Policy

For the rest of this workstream, compatibility is intentionally narrow.

What can change aggressively now:

- app-managed GUI surfaces
- helper/native-host payloads used only by this unreleased app stack
- internal helper/runtime naming
- benchmark/probe/help-text surfaces that are only developer tooling

What may still keep compatibility shims for a while:

- manual external imports
- explicit developer/debug paths
- tests that intentionally exercise raw-format coverage
- provider-specific converter/build tooling

Practical rule:

- if a surface is part of the unreleased app/runtime/tooling contract, prefer rename/remove over preserving old `freedict_*` or TEI-first behavior
- if a surface is explicitly about manual imports, raw-format tests, or provider-specific conversion, compatibility is still reasonable

## End State

We are done when all of these are true:

1. Every app-managed pack family installs under a stable pack-id root.
2. Every app-managed pack family writes `manifest.json`.
3. Every app-managed pack family finishes in a canonical SQLite runtime artifact.
4. Raw downloads and extraction trees are deleted by default after successful build.
5. Helper/runtime/settings/benchmark resolve managed packs by pack identity and manifest, not by guessed filenames.
6. Runtime consumers use shared normalized loaders/views instead of provider-native TEI/XML/raw-vector parsing.
7. Raw TEI and raw embedding/vector files remain only as explicit manual import or debug compatibility paths.

## Permanent Family Matrix

This matrix is the canonical remaining-work board for the normalization program.

| Family | Representative packs | Normalized managed form | Primary UX/runtime endpoints | Current state | Remaining target |
|---|---|---|---|---|---|
| Translation dictionaries | `freedict-de-en`, `freedict-en-de`, `freedict-es-en`, `freedict-en-es`, `wiktionary-es-en`, `wiktionary-en-es` | Pack root + `manifest.json` + compiled SQLite + translation-pack ref | settings pack manager, helper rulegen, runtime diagnostics, benchmark, bulk-rule translation expansion, SRS harness fixtures | Mostly normalized | managed installs now converge on `main.sqlite`; remaining work is provider-shaped generic naming cleanup and making manifest-first resolution dominant everywhere |
| Frequency packs | `freq-en-coca`, `freq-ja-bccwj`, `freq-de-default`, `freq-es-cde` | Pack root + `manifest.json` + SQLite + frequency-pack ref | settings pack manager, SRS growth/admission, helper/runtime diagnostics | Mostly normalized | converge artifact naming to `main.sqlite`, tighten canonical schema, finish pack-id/manifests as the primary contract |
| Embedding packs | `embed-en-cc`, `embed-de-cc`, `embed-ja-cc`, `embed-es-cc`, `embed-xling-*` | Pack root + `manifest.json` + SQLite + embedding-pack ref | settings pack manager, replacement filter, embedding-backed synonym behavior | Mostly normalized for app-managed installs | app-managed installs now converge on `main.sqlite`; remaining work is to keep raw `.vec/.bin` strictly in manual import/debug territory |
| Secondary lexical packs | `wordnet-en`, `moby-en`, `openthesaurus-de`, `odenet-de`, `jp-wordnet`, `jp-wordnet-sqlite`, `jmdict-ja-en`, `cc-cedict-zh-en` | Mixed/raw today | settings pack manager, bulk add rules, some SRS/rulegen support for `jmdict` | Not normalized as a family | decision pending; either normalize into the same managed-pack model or explicitly demote to manual/legacy import status |

## UX Endpoint Matrix

| Endpoint | Source families used | Current contract | Desired end state |
|---|---|---|---|
| Settings pack manager | translation, frequency, embeddings, secondary lexical packs | managed installs already build/manifest for translation/frequency/embeddings; secondary packs still mixed | every app-managed pack downloads, fully converts, writes manifest, and removes obsolete raw data by default |
| Helper rulegen / native host / runtime diagnostics | translation, frequency, `jmdict` where needed | translation/frequency mostly pack-ref aware; some provider-specific internals remain below the seam | pack-id/manifests are primary identity everywhere generic |
| SRS growth / admission | frequency, `jmdict` where required | frequency mostly normalized, `jmdict` still special/raw | same pack-root + manifest + canonical artifact model for all product-critical managed sources |
| Replacement filter | embeddings | managed embeddings already resolve by pack id first | pack-id-first only for managed paths; raw vector files only through explicit import/debug paths |
| Bulk add rules / synonym expansion | secondary lexical packs + translation packs | mixed; translation side cleaner, secondary packs still mixed/raw | either normalize all retained packs or explicitly classify them as manual/legacy |
| Benchmark / developer tooling | translation primarily | mostly normalized; generic naming cleanup largely done | pack ids/manifests/checksums as the default identity surface |

## Decision Policy For Secondary Lexical Families

We are intentionally not forcing a yes/no product decision yet for secondary lexical packs.

Current policy:

- keep them available while the testing architecture improves
- include them in future evaluation/sweep work where useful
- use slice-based evidence to decide whether they deserve first-class normalization

Decision gate:

1. Add or expose evaluation slices that can reveal semantic/word-group wins.
2. Test whether a secondary source improves accuracy or pedagogical quality on those slices.
3. If it shows real value, normalize it into the same managed-pack model.
4. If it does not, keep it only as a manual/debug/legacy import path, not as a core managed runtime contract.

So for now:

- `translation`, `frequency`, and `embeddings` are mandatory normalization targets
- `secondary lexical packs` are experimental candidates for promotion

## Permanent Implementation Board

Status markers:

- `[x]` done enough for the current architecture
- `[~]` partially complete / transitional
- `[ ]` remaining

| Board item | Status | Notes |
|---|---|---|
| Managed translation installs build to SQLite and write manifests | `[x]` | FreeDict and Kaikki app-managed translation packs now land as manifest-backed SQLite artifacts |
| Managed frequency installs build to SQLite and write manifests | `[x]` | install/resolution path is normalized enough to use as the default |
| Managed embedding installs build to SQLite and write manifests | `[x]` | app-managed embeddings now convert as part of install |
| Raw download/extraction cleanup for managed installs | `[x]` | default direction is now delete-after-success for the main managed families |
| Generic helper translation naming cleanup | `[x]` | app-managed helper/native-host/runtime seam now prefers `translation_dict_*` |
| Generic benchmark/probe naming cleanup | `[x]` | benchmark split landed; generic translation naming is now the normal tooling contract |
| Adapter request contract uses generic translation-path fields | `[x]` | generic request seam no longer carries `freedict_*` aliases |
| Synonym translation-pack seam uses generic directional fields | `[x]` | runtime seam no longer uses FreeDict-shaped field names there |
| Managed translation settings persist by pack identity rather than stale raw paths | `[~]` | normalized translation packs now persist as managed pack ids, manual entries now serialize under explicit `language_pack_paths`, and the settings UI now labels managed artifacts as installed vs manual external paths; secondary language-pack flows still keep path-shaped state |
| Managed frequency settings/runtime fully pack-id-first | `[~]` | managed frequency packs now persist as pack ids, manual entries now serialize under explicit `frequency_pack_paths`, and SRS runtime resolves managed ids first; remaining work is mostly schema/diagnostic cleanup |
| Managed embedding settings/runtime fully pack-id-first | `[x]` | app-managed embedding activation is pack-id-first, old managed embedding paths now migrate out on load, and manual path storage remains separate for import/debug use |
| Converge managed translation artifact naming to `main.sqlite` | `[x]` | app-managed translation installs now land on `main.sqlite`; legacy `<pack_id>.sqlite` names remain fallback for older/manual paths |
| Converge managed frequency artifact naming to `main.sqlite` | `[x]` | app-managed frequency installs now land on `main.sqlite`; legacy `freq-*.sqlite` names remain fallback for older/manual paths |
| Converge managed embedding artifact naming to `main.sqlite` | `[x]` | app-managed embedding installs already land on `main.sqlite`; manual raw/vector paths remain explicit compatibility inputs |
| Remove remaining app-managed obsolete field names | `[~]` | most generic seams are done; settings now serialize explicit `*_pack_paths`, and remaining hits are increasingly provider-specific or tooling-local |
| Reclassify raw TEI/raw vector paths as import/debug only | `[~]` | settings UI now distinguishes installed artifacts from manual/import paths for translation, frequency, and embeddings, but enforcement and wording are not yet uniform across every secondary/manual surface |
| Secondary lexical family promotion decision | `[ ]` | depends on future slice-based evaluation results |

## Current Achieved State

Already landed:

- manifest-backed install roots for translation packs
- manifest-backed install roots for frequency packs
- manifest-backed install roots for app-managed embedding packs
- app-managed FreeDict translation packs now build to SQLite
- helper default translation resolution now prefers FreeDict SQLite artifact names
- German frequency whitelist/build now prefers normalized FreeDict artifacts
- synonym generation now reads FreeDict through the shared translation-pack loader
- bulk-rules GUI FreeDict selection now resolves managed SQLite artifacts or legacy SQLite files, and no longer treats extracted TEI directories as a normal managed path
- synthetic SRS quality/journey harness fixtures now default to SQLite translation resources instead of raw TEI
- translation pack refs now honor managed manifests when present instead of relying only on filename/provider inference
- helper rulegen debug payloads now report translation pack id/provider/source-profile fields through the shared translation-pack seam
- installed-resource journey staging now preserves manifest-backed translation pack roots instead of flattening them into loose artifact files
- helper/runtime now expose a first frequency pack-ref seam so diagnostics and pair-resource resolution can report pack identity, provider, and POS source profile instead of only a raw SQLite path
- managed translation settings now split normalized app-owned translation packs into `managed_language_pack_ids` plus manual `language_pack_paths`, and app-state loading migrates old saved managed artifact paths into that shape
- managed frequency settings now split app-owned frequency packs into `managed_frequency_pack_ids` plus manual `frequency_pack_paths`, and app-state loading migrates old saved managed artifact paths into that shape
- the settings dialog plus cancel/save sync path now stop re-saving managed translation/frequency artifact paths when those installs are already represented by pack id
- the bulk-rules translation path now rebuilds managed translation pack paths from stored pack ids, while SRS growth rebuilds managed default frequency artifacts from stored pack ids before falling back to manual paths
- app-managed translation installs now converge on `language_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `<pack_id>.sqlite` filenames for older local installs
- app-managed frequency installs now converge on `frequency_packs/<pack_id>/main.sqlite`, while panel/runtime resolution still accepts legacy `freq-*.sqlite` filenames for older local installs
- managed embedding activation can now be persisted by pack id per pair while runtime resolves those pack ids back through manifest-backed SQLite artifacts
- app-state load/update now migrates old saved managed embedding artifact paths into pack-id-first per-pair activation and strips those app-owned paths from the manual embedding maps
- the settings panel now omits redundant managed embedding artifact paths from saved settings when those installs are already represented by pack id + manifest-backed resolution
- settings serialization now writes explicit `language_pack_paths`, `frequency_pack_paths`, and `embedding_pack_paths` keys instead of the older generic `*_packs` path maps
- the settings UI now labels app-owned resolved resources as `Installed`, external/manual translation-frequency-embedding paths as `Manual`, and active embedding rows as either `Active (Installed)` or `Active (Manual)` so the managed-vs-import boundary is explicit in normal use
- helper CLI/native-host entrypoints and internal helper use cases now prefer generic `translation_dict_path` naming, and runtime/helper diagnostics no longer emit `freedict_de_en_*` as part of the app-managed generic contract

Still intentionally transitional:

- some GUI/runtime/benchmark/help-text paths still mention TEI compatibility inputs even though the default managed path is SQLite-first
- translation packs still preserve legacy `<pack_id>.sqlite` artifact names as fallback paths during migration
- frequency packs still preserve legacy `freq-*.sqlite` artifact names
- embeddings still preserve raw/manual path maps for compatibility and manual imports, but managed app-owned embedding paths no longer need to be persisted alongside pack-id activation
- benchmark/help-text surfaces still contain some legacy filename/provider heuristics, especially the oversized `rulegen_benchmark.py` hotspot

## Board-Driven Execution Rule

When choosing the next task, prefer this order:

1. close `[~]` items for mandatory families (`translation`, `frequency`, `embeddings`)
2. finish settings/runtime pack-id-first cleanup before doing cosmetic naming convergence
3. converge active managed artifact names to `main.sqlite` only after manifest-first resolution is stable
4. treat `secondary lexical packs` as evidence-driven candidates, not automatic promotion targets

## Execution Order

## Phase 1: App-Managed Translation Surface Cleanup

Goal:
- remove FreeDict-era naming and TEI-first assumptions from unreleased app/helper/tooling surfaces

Why this is first:
- this is now mostly naming and contract cleanup, not risky storage work
- the app is not released, so we should remove obsolete names instead of preserving them
- `de-en` and related LP work should not keep building on TEI-first seams

Concrete work:

1. GUI/helper breaking cleanup
   - remove or narrow remaining TEI/directory compatibility logic in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/main_bulk_rules_mixin.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/helper_daemon.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/dialogs_code.py`
   - rename app-facing labels/settings so generic surfaces say `translation dictionary` / `translation pack`, not `freedict`
   - do not preserve app-only legacy naming just for compatibility

2. Helper/native-host/CLI breaking cleanup
   - update:
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/helper/lexishift_helper.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/helper/lexishift_native_host.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/engine.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/rulegen.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/pair_resources.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/initialize_set.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/refresh_set.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
   - make generic request/response fields primary and remove old `freedict_*` names where the caller is only our own app/tooling
   - keep manual-path compatibility only where a raw provider file is still an explicit supported import path

3. Synthetic harness/resource fixture cleanup
   - move the remaining synthetic translation fixtures toward SQLite-first defaults in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/srs_quality_harness_support.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/srs_journey_harness_support.py`
   - keep TEI fixture helpers only when a test explicitly needs raw-format coverage
   - current checkpoint: both the quality harness and the journey harness are now SQLite-first by default, and the journey resource-writing logic has been split into a dedicated helper so the scenario-support file stays below the project-health ceiling

4. Benchmark/probe/help-text cleanup
   - update developer tooling so SQLite is presented as the normal managed artifact
   - keep TEI mentioned only as an explicit manual/debug input
   - main hotspot:
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/rulegen_benchmark.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/rulegen_probe_words.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/apps/chrome-extension/options/controllers/srs/actions/formatters.js`

Definition of done:

- unreleased app/helper/tooling surfaces no longer present `freedict_*` as the primary generic contract
- managed translation packs are no longer treated as extracted TEI directories in normal runtime flows
- TEI survives only as a manual-import/debug/provider-specific path
- test fixtures default to SQLite unless they are explicitly TEI-coverage tests

## Phase 2: Translation Internal Convergence

Goal:
- finish the generic/internal translation seam so generic layers stop carrying provider-shaped assumptions

Concrete work:

1. Normalize generic helper/core names
   - retire transitional aliases like `requires_freedict_de_en_for_rulegen` where they are only internal
   - keep provider-specific naming only in provider-specific modules

2. Narrow translation-pack heuristics
   - reduce filename-guessing in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/lp_capabilities.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/translation_packs.py`
   - manifest-first should be the real path; filename guessing becomes fallback for manual/import cases only

3. Decide whether pair-local config names stay provider-specific
   - likely yes for now in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/rulegen/pairs/en_de.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/rulegen/pairs/de_en.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/rulegen/pairs/es_en.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/rulegen/pairs/en_es.py`
   - generic layers should be normalized first; pair-local provider names are lower priority unless they start causing confusion

Definition of done:

- generic layers are provider-neutral
- provider-specific naming remains only where it is actually describing a provider-specific implementation

## Phase 3: Frequency Finalization

Goal:
- make frequency packs match the same final contract as translation packs, not just “SQLite somewhere on disk”

Concrete work:

1. Canonicalize artifact contract
   - decide and migrate from legacy `freq-*.sqlite` filenames toward canonical `main.sqlite`
   - do this only after manifest-backed resolution is fully stable

2. Tighten the canonical SQLite schema
   - converge on stable columns like:
     - `lemma`
     - `lemma_lc`
     - `rank`
     - `pmw`
     - `pos`
   - keep fallback column handling until all managed packs use the canonical schema

3. Remove path-first frequency assumptions
   - helper/runtime/settings should prefer frequency pack identity + manifest, not direct file paths
   - keep explicit file overrides only as compatibility/dev tooling

Definition of done:

- managed frequency packs resolve as pack refs first
- managed frequency runtime does not depend on pack-specific legacy filenames
- the migration no longer needs special-case schema fallbacks for current managed packs

## Phase 4: Embedding Finalization

Goal:
- finish the storage-to-runtime migration for embeddings so SQLite is not only the install artifact, but also the normal runtime contract

Concrete work:

1. Move settings/runtime from artifact paths to pack identity
   - current managed installs already end in SQLite
   - current verified progress:
     - managed embedding installs already end in manifest-backed SQLite
     - per-pair managed activation can now be persisted by pack id
     - replacement-filter runtime now resolves those pack ids back to manifest-backed SQLite artifacts
   - remaining work is replacing the remaining direct artifact-path settings/maps for managed embeddings while keeping manual raw-file import compatibility

2. Separate managed installs from manual imports
   - app-managed embeddings:
     - pack root
     - manifest
     - canonical SQLite
   - manual raw `.vec/.bin` imports:
     - explicit compatibility/import path only

3. UI/diagnostic polish
   - make “conversion is part of install” explicit
   - keep clear failure/reporting for conversion failures

Definition of done:

- app-managed embedding runtime no longer depends on raw `.vec/.bin`
- settings/diagnostics identify managed embeddings by pack id + manifest-backed artifact
- raw vector support is clearly a compatibility/import path, not the normal app-managed contract

## Phase 5: Unified Pack Refs Across Families

Goal:
- stop passing loose paths around as the primary generic resource contract

Concrete work:

1. Add family-equivalent pack refs for:
   - translation
   - frequency
   - embeddings

2. Make helper/runtime/benchmark diagnostics report:
   - pack id
   - provider
   - canonical artifact path
   - checksum/version when available

3. Make generic resolution functions manifest-driven first
   - filename guessing should become compatibility fallback, not the main resolution path

Definition of done:

- generic layers work with pack refs and manifests first
- raw path guessing only exists as compatibility fallback

## Phase 6: Final Cleanup And Convergence

Goal:
- remove transitional assumptions once the pack-ref and consumer migrations are complete

Concrete work:

1. Remove obsolete filename/path heuristics where safe
2. Reduce TEI/raw-vector compatibility to explicit manual-import/debug code paths
3. Converge compiled artifact names to `main.sqlite` once all managed consumers are manifest-driven
4. Make benchmark/resource artifacts prefer pack ids/manifests/checksums as the primary identity surface

Definition of done:

- no normal managed runtime flow depends on raw provider files
- generic code does not need provider-specific filename heuristics to function
- managed pack storage and runtime contracts are structurally consistent across translation, frequency, and embeddings

## Best Immediate Next Steps

If continuing now, the highest-value order is:

1. Phase 1 app-managed translation surface cleanup
   - `apps/gui/src/main_bulk_rules_mixin.py`
   - `apps/gui/src/helper_daemon.py`
   - `scripts/helper/lexishift_helper.py`
   - `scripts/helper/lexishift_native_host.py`
   - `scripts/testing/rulegen_benchmark.py`
   - `scripts/testing/rulegen_probe_words.py`

2. Phase 2 translation internal convergence
   - `core/lexishift_core/helper/engine.py`
   - `core/lexishift_core/helper/rulegen.py`
   - `core/lexishift_core/helper/lp_capabilities.py`
   - `core/lexishift_core/helper/pair_resources.py`

3. Phase 3 frequency/runtime cleanup
   - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/main_srs_mixin.py`
   - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
   - continue replacing path-first frequency resolution/reporting and artifact-specific assumptions with manifest-backed pack refs

4. Phase 4 embedding seam migration
   - move the remaining managed embedding settings/maps from path-first persistence to pack-id-first persistence

I would not jump to `main.sqlite` renaming across families before the remaining runtime consumers and harnesses stop assuming specific legacy filenames.

## Relationship To `de-en`

This normalization path remains upstream of deeper `de-en` quality work.

The safe sequence is:

1. finish the remaining translation-consumer normalization
2. keep `de-en` on the normalized translation-pack contract
3. only then spend more effort on `de-en` benchmark growth and tuning
