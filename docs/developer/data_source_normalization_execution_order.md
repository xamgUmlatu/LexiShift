# Data Source Normalization Execution Order

Status: active execution roadmap
Role: ordered implementation plan
Purpose: turn the normalization architecture target into an explicit, resumable sequence of remaining work.
Last updated: 2026-04-03
Last verified: 2026-04-03 code/doc review after FreeDict SQLite install normalization, German frequency whitelist migration, synonym-loader migration, the first frequency pack-ref/runtime-diagnostics seam slice, and the first embedding pack-id activation/runtime-resolution slice
Source-of-truth: planning/execution guide only; runtime truth still lives in code, tests, and `feature_state_matrix.md`.

## End State

We are done when all of these are true:

1. Every app-managed pack family installs under a stable pack-id root.
2. Every app-managed pack family writes `manifest.json`.
3. Every app-managed pack family finishes in a canonical SQLite runtime artifact.
4. Raw downloads and extraction trees are deleted by default after successful build.
5. Helper/runtime/settings/benchmark resolve managed packs by pack identity and manifest, not by guessed filenames.
6. Runtime consumers use shared normalized loaders/views instead of provider-native TEI/XML/raw-vector parsing.
7. Raw TEI and raw embedding/vector files remain only as explicit manual import or debug compatibility paths.

## Current Achieved State

Already landed:

- manifest-backed install roots for translation packs
- manifest-backed install roots for frequency packs
- manifest-backed install roots for app-managed embedding packs
- app-managed FreeDict translation packs now build to SQLite
- helper default translation resolution now prefers FreeDict SQLite artifact names
- German frequency whitelist/build now prefers normalized FreeDict artifacts
- synonym generation now reads FreeDict through the shared translation-pack loader
- bulk-rules GUI FreeDict selection now resolves managed SQLite artifacts before TEI-compatible directory fallbacks
- synthetic SRS quality/journey harness fixtures now default to SQLite translation resources instead of raw TEI
- helper/runtime now expose a first frequency pack-ref seam so diagnostics and pair-resource resolution can report pack identity, provider, and POS source profile instead of only a raw SQLite path
- managed embedding activation can now be persisted by pack id per pair while runtime resolves those pack ids back through manifest-backed SQLite artifacts

Still intentionally transitional:

- some GUI/runtime/harness paths still mention TEI compatibility inputs even though the default managed path is SQLite-first
- frequency packs still preserve legacy `freq-*.sqlite` artifact names
- embeddings still preserve direct artifact-path maps for compatibility and manual imports even though managed pair activation can now use pack ids
- generic helper/resource reporting still contains filename/provider heuristics

## Execution Order

## Phase 1: Translation Consumer Cleanup

Goal:
- make managed translation packs behave like SQLite-first resources everywhere that matters at runtime

Why this is first:
- translation packs are the noisiest remaining source of TEI-specific assumptions
- `de-en` and related LP work should not keep building on TEI-first seams

Concrete work:

1. GUI compatibility cleanup
   - remove or narrow remaining TEI/directory compatibility logic in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/main_bulk_rules_mixin.py`
   - keep directory fallback only where manual legacy packs are intentionally still supported

2. Synthetic harness/resource fixture cleanup
   - move the remaining synthetic translation fixtures toward SQLite-first defaults in:
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/srs_quality_harness_support.py`
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/srs_journey_harness_support.py`
   - keep TEI fixture helpers only when a test explicitly needs raw-format coverage
   - current checkpoint: both the quality harness and the journey harness are now SQLite-first by default, and the journey resource-writing logic has been split into a dedicated helper so the scenario-support file stays below the project-health ceiling

3. Generic helper/diagnostic naming cleanup
   - remove generic logic that infers provider semantics from `.tei` or `freedict` filename patterns where a manifest-backed pack id is available
   - main hotspot:
     - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/rulegen_job.py`

4. Benchmark/help-text compatibility cleanup
   - update user-facing help text and comments so SQLite is presented as the normal managed artifact
   - keep TEI mentioned only as compatibility input
   - main hotspot:
     - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/rulegen_benchmark.py`

Definition of done:

- managed translation packs are no longer treated as extracted TEI directories in normal runtime flows
- TEI survives only as a compatibility/manual-import path
- test fixtures default to SQLite unless they are explicitly TEI-coverage tests

## Phase 2: Frequency Finalization

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

## Phase 3: Embedding Finalization

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

## Phase 4: Unified Pack Refs Across Families

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

## Phase 5: Legacy Cleanup And Convergence

Goal:
- remove transitional assumptions once the pack-ref and consumer migrations are complete

Concrete work:

1. Remove obsolete filename/path heuristics where safe
2. Reduce TEI/raw-vector compatibility to explicit manual-import/debug code paths
3. Optionally converge compiled artifact names to `main.sqlite`
4. Make benchmark/resource artifacts prefer pack ids/manifests/checksums as the primary identity surface

Definition of done:

- no normal managed runtime flow depends on raw provider files
- generic code does not need provider-specific filename heuristics to function
- managed pack storage and runtime contracts are structurally consistent across translation, frequency, and embeddings

## Best Immediate Next Steps

If continuing now, the highest-value order is:

1. Phase 2 frequency/runtime cleanup
   - `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/main_srs_mixin.py`
   - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
   - continue replacing path-first frequency resolution/reporting with manifest-backed pack refs

2. Phase 3 embedding seam migration
   - move the remaining managed embedding settings/maps from path-first persistence to pack-id-first persistence

3. Phase 1 residual translation cleanup
   - `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/use_cases/rulegen_job.py`
   - `/Users/takeyayuki/Documents/projects/LexiShift/scripts/testing/rulegen_benchmark.py`
   - remove the remaining TEI-compatible language in generic helper/benchmark seams once pack-ref reporting is stable

I would not jump to `main.sqlite` renaming across families before the remaining runtime consumers and harnesses stop assuming specific legacy filenames.

## Relationship To `de-en`

This normalization path remains upstream of deeper `de-en` quality work.

The safe sequence is:

1. finish the remaining translation-consumer normalization
2. keep `de-en` on the normalized translation-pack contract
3. only then spend more effort on `de-en` benchmark growth and tuning
