# Data Source Normalization Architecture

Status: active planning doc with first executable slice
Role: architecture target / implementation plan
Purpose: define the final desired architecture for installed language/data packs so rulegen, helper, and benchmark code consume a normalized contract instead of provider-specific raw files.
Last updated: 2026-04-03
Last verified: 2026-04-03 helper/gui path and manifest slice plus manifest-backed translation pack refs, helper/journey-installed translation-pack seam cleanup, the first frequency pack-ref/runtime-diagnostics seam, the first embedding pack-id activation/runtime-resolution seam, and the internal helper translation-dictionary seam cleanup
Source-of-truth: planning doc only; executable truth still lives in code, tests, and current pack/build flows.

Execution-order companion:
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/data_source_normalization_execution_order.md`

## Why This Workstream Exists

Current pack handling is inconsistent across providers:

- FreeDict packs are installed as extracted source directories and current pair code may read TEI directly.
- Kaikki packs already build a compatibility SQLite artifact.
- Helper/runtime resolution still contains filename/path assumptions that leak provider storage details upward.

That is good enough for incremental pair work, but it is not the final architecture we want.

The desired end state is:

1. provider-specific raw downloads are treated as build inputs
2. runtime consumes normalized installed pack manifests plus compiled artifacts
3. the canonical compiled artifact is a small, queryable, provider-agnostic format, preferably SQLite
4. dirty download archives and extraction directories are deleted after a successful build unless an explicit developer-retention mode is enabled

In short:

- normalize at the contract level
- compile to a canonical runtime artifact
- stop exposing raw provider layout to helper/rulegen/benchmark code

## Compatibility Boundary

For this repo, compatibility should now be treated as a scoped engineering choice, not a default obligation.

Because the app/runtime stack is not released, we do not need to preserve old app-managed naming or old app-managed TEI-first behavior just to avoid churn.

That means:

- GUI/helper/native-host/developer-tooling surfaces owned by this repo can be renamed or cleaned up directly
- `freedict_*` fields should stop being the primary generic contract on app-managed surfaces
- app-managed flows should stop advertising TEI as a normal runtime artifact

Compatibility is still reasonable only for:

- manual external imports
- explicit developer/debug paths
- provider-specific converter/build tooling
- tests that intentionally verify raw-format coverage

So the final architecture is not just “support both forever.” It is:

- aggressive cleanup for app-managed surfaces
- explicit compatibility islands for manual/debug/provider-specific workflows

## Onboarding Rule

This is not only a cleanup plan for current packs.
It is the required architecture for all future data-source onboarding.

Any new language/data pack added to the app or helper should:

1. install under a stable pack-id root
2. write a manifest that declares the canonical runtime artifact
3. produce or adopt one canonical compiled runtime artifact, preferably SQLite
4. treat provider-native raw downloads/extractions as build inputs, not runtime contracts
5. delete dirty raw downloads/extractions after successful build by default

New onboarding should not introduce fresh flat-file runtime contracts or provider-specific path guessing into helper, rulegen, benchmark, or diagnostics layers.

## Core Architectural Decision

The final architecture should standardize on a universal logical API and a preferred compiled storage format.

Logical API:

- every translation pack resolves to the same normalized pack contract
- every provider exposes the same normalized lexical-record view, even if some fields are sparse

Preferred storage:

- SQLite is the default compiled runtime artifact whenever the source is not already in an equally practical structured format
- raw archives and temporary extraction trees are build-time implementation details, not runtime inputs

This means:

- rulegen should ask for a normalized translation pack, not for `eng-deu.tei`
- benchmark should ask for pack identity, capabilities, and checksums, not infer provider by filename
- pair modules should consume normalized record views, not provider-native TEI/XML/JSONL formats directly

## Final Target Model

## 1. Pack Catalog Spec

The pack catalog should remain the source of truth for:

- pack id
- provider
- source/direction
- raw download URL/version
- license/distribution posture
- required raw files, if any
- build pipeline id
- expected compiled artifacts

This is an extension of the current catalog, not a replacement for it.

## 2. Installed Pack Directory

Each installed pack should live in its own stable directory, for example:

`$DATA_ROOT/language_packs/<pack_id>/`

That directory should contain:

- `manifest.json`
- `artifacts/`
- optional `build_logs/`
- optional `raw/` only when raw retention is explicitly enabled

Runtime should not depend on flat filenames in the top-level `language_packs/` directory.

## 3. Pack Manifest

Each installed pack should have a manifest that records:

- pack id
- provider
- pair/direction
- source download metadata
- build pipeline version
- build timestamp
- checksums
- compiled artifact list
- metadata capabilities
- POS source profile

This manifest should let helper/runtime/benchmark discover pack identity without guessing from filenames.

## 4. Compiled Artifact Layer

Compiled artifacts are the canonical runtime inputs.

Preferred default:

- `main.sqlite`

Possible future secondary artifacts:

- auxiliary sqlite indexes
- compact JSON summaries
- cache tables for reverse aliases, phrase fragments, or POS inventories

The runtime should not care whether `main.sqlite` came from:

- FreeDict TEI
- Kaikki raw dump
- JMDict XML
- CEDICT text

If a provider already ships something we consider equivalent to the canonical artifact, we can treat that as the compiled artifact directly.

## 5. Normalized Pack Ref

`TranslationPackRef` should evolve into a richer installed-pack reference that includes:

- pack id
- provider
- pair
- direction
- manifest path
- canonical artifact path
- checksum
- POS source profile
- metadata capability flags

The important change is that the canonical runtime reference should point at the pack and its compiled artifact, not at a guessed raw file path.

## 6. Normalized Lexical View

This is the real normalization boundary.

Every translation pack should expose the same logical record shape, such as:

- headword / lemma
- normalized headword
- translation / gloss / candidate text
- normalized candidate text
- rank / order
- POS
- sense/entry/gloss ordinals
- tags / topics / categories / register / region
- provenance

Not every provider needs to fill every field, but the shape should be stable.

Pair code should consume this normalized lexical view, not provider-native storage.

## 7. Pair Compiler

Pair-local rulegen modules should be responsible for:

- pair-specific candidate extraction
- pair-specific normalization policy
- pair-specific scoring signals
- pair-specific metadata views

They should not be responsible for:

- finding provider-native files
- parsing TEI/XML/JSONL directly
- inferring provider identity from paths

## 8. Generic Runtime And Benchmark Layers

Helper, runtime diagnostics, rulegen adapters, and benchmark should consume:

- normalized pack refs
- normalized lexical views
- compiled pair context / benchmark IR

They should not contain provider-specific path heuristics except inside the resource/build layer.

## Preferred Storage Policy

Default policy:

- compile installed packs to SQLite
- keep the compiled artifact and manifest
- delete raw archives and dirty extraction directories after a successful build

Rationale:

- faster runtime access
- consistent loader contract
- simpler portability
- fewer path/layout edge cases
- smaller semantic surface area in helper/rulegen/benchmark code

Non-goal:

- keeping raw provider trees around as the normal runtime contract

Allowed exception:

- an explicit developer/debug retention mode may keep `raw/` for inspection or rebuild debugging

That debug mode should be opt-in and should not shape the runtime architecture.

## Provider-Specific Implications

## FreeDict

Desired final behavior:

- download archive
- extract only as a temporary build step
- compile TEI into canonical SQLite
- record manifest/checksums/provenance
- delete archive and temporary extraction tree

Runtime should consume the compiled SQLite, not `*.tei` directly.

## Kaikki

Kaikki is already directionally closer to the final model:

- raw download
- build to pair-specific SQLite
- runtime consumes SQLite

The remaining work is mainly to move it under the same manifest/pack-ref/normalized-view contract as other providers.

## JMDict / Other Sources

Same principle:

- provider-specific raw artifact may differ
- canonical installed runtime contract should still be manifest + compiled artifact + normalized lexical view

## Migration Plan

## Phase A: Manifest-Centered Installed Pack Layout

Goals:

- move from flat-file/path-guessing toward pack-id-based resolution
- give each installed pack a stable directory and manifest

Definition of done:

- runtime can resolve installed translation packs by pack id
- manifest exists even if the pack still references legacy raw artifacts during migration

Current verified progress:

- app-managed language-pack downloads now install under stable per-pack roots rather than flat shared filenames
- app-managed language-pack downloads now write manifest files that record the canonical runtime artifact path
- helper translation-dictionary resolution now checks manifest-backed installed packs before falling back to filename/path guessing
- shared translation pack refs now honor managed manifests when present instead of relying only on filename/provider inference
- helper rulegen debug payloads now report translation pack id/provider/source-profile fields through the shared translation-pack seam
- helper CLI/native-host entrypoints and the internal helper use-case seam now prefer generic `translation_dict_path` naming, and app-managed helper/runtime diagnostics no longer expose `freedict_de_en_*` keys as part of the generic contract
- installed-resource journey staging now preserves manifest-backed translation pack roots instead of flattening them into loose artifact files
- current runtime artifacts are still mixed:
  - app-managed FreeDict translation packs now build to canonical SQLite artifacts while manual TEI files and older extracted directories remain compatibility inputs
  - Kaikki translation packs still expose compatibility SQLite as the canonical runtime artifact

Current non-coverage:

- helper/rulegen resource resolution is still only partially manifest-aware outside translation defaults, the first frequency pack-ref/runtime-diagnostics seam, and the first embedding pack-id activation/runtime-resolution seam
- embedding runtime and settings still preserve raw-file compatibility for manually supplied external files during migration
- frequency packs still keep pack-specific SQLite filenames during migration rather than a fully unified `main.sqlite` contract

## Normalized Runtime Format By Pack Family

This section records the preferred final runtime artifact for each major pack family.
The intent is to prevent future onboarding from drifting into ad hoc storage formats.

### Translation Packs

Preferred runtime artifact:

- `main.sqlite`

Rationale:

- translation packs need indexed headword/candidate lookup
- pair modules should not parse provider-native TEI/XML/JSONL directly
- a canonical SQLite contract makes forward/reverse resource handling symmetric

Migration note:

- Kaikki is already close because it builds to SQLite today
- FreeDict app-managed installs now have a TEI-to-SQLite normalization step; remaining work is benchmark/help-text cleanup plus a small set of residual compatibility-heavy consumer seams rather than the main helper/journey runtime path

### Frequency Packs

Preferred runtime artifact:

- `main.sqlite`

Current reality:

- frequency is already directionally correct
- app-managed installs already convert raw source files to SQLite
- runtime already consumes SQLite through `SqliteFrequencyStore`

What still needs normalization:

- stable pack-id root plus `manifest.json`
- one canonical artifact filename/layout
- tighter semantic schema so runtime does not rely on broad column-name fallback forever

Target canonical schema:

- `frequency(lemma, lemma_lc, rank, pmw, pos, ...)`
- `meta(key, value)`

Compatibility rule during migration:

- source-specific extra columns may still be preserved
- runtime should gradually move toward canonical column names, with fallback logic retained only as a migration bridge

### Embedding Packs

Preferred runtime artifact:

- `main.sqlite`

Current reality:

- raw `.vec` / `.bin` files are still treated as acceptable runtime inputs
- SQLite conversion exists, but it is not the mandatory app-managed end state yet

What should change:

- app-managed embedding downloads should always end in SQLite
- raw vectors should become build/import inputs only
- runtime should prefer manifest-backed SQLite artifacts by default

Target canonical schema:

- `vectors(word, word_lc, dim, norm, lsh_sig, vector)`
- `meta(key, value)`

Why SQLite remains the right target for now:

- exact lookup is the primary active runtime need
- optional approximate-neighbor narrowing already exists via `lsh_sig`
- introducing a separate ANN service or custom binary index would add operational complexity before embeddings are even a primary scorer

## Phase B: FreeDict Build Normalization

Goals:

- add a FreeDict build pipeline to canonical SQLite
- stop treating extracted TEI directories as the runtime contract

Definition of done:

- `freedict-en-de`, `freedict-de-en`, `freedict-en-es`, and `freedict-es-en` install to compiled SQLite artifacts plus manifests
- temporary extracted source directories can be deleted after successful builds

Current verified progress:

- the FreeDict app catalog now declares managed TEI-to-SQLite builds for `freedict-de-en`, `freedict-en-de`, `freedict-es-en`, and `freedict-en-es`
- app-managed translation installs now auto-link manifest-backed SQLite artifacts instead of extracted TEI directories
- helper default translation-dictionary discovery now prefers FreeDict SQLite artifact names before TEI compatibility filenames
- the German frequency whitelist/build path now prefers manifest-backed FreeDict SQLite artifacts and shared translation-pack headword loaders instead of TEI-only parsing
- the synonym generator now reads FreeDict packs through the shared translation-pack loader, so app-managed SQLite artifacts work there without a separate TEI parser
- the GUI bulk-rules FreeDict path now resolves managed SQLite artifacts first and only falls back to TEI-compatible directory contents for legacy/manual inputs
- the synthetic SRS quality and journey harness fixtures now emit SQLite translation resources by default instead of raw TEI
- the journey harness resource-writing layer now lives in a dedicated helper module so storage-format normalization no longer expands the already-large scenario-support file
- shared translation pack refs now honor managed manifests when present instead of relying only on filename/provider inference
- helper rulegen debug payloads now report translation pack id/provider/source-profile fields through the shared translation-pack seam
- helper CLI/native-host entrypoints and the internal helper use-case seam now prefer generic `translation_dict_path` naming, and app-managed helper/runtime diagnostics no longer expose `freedict_de_en_*` keys as part of the generic contract
- installed-resource journey staging now preserves manifest-backed translation pack roots instead of flattening them into loose artifact files

## Phase B2: Apply The Same Model To Other Pack Families

Goals:

- migrate frequency packs to the same manifest-backed compiled-artifact model
- migrate embedding packs/converters to the same manifest-backed compiled-artifact model
- make new monolingual/synonym source onboarding follow this contract immediately instead of creating new one-off install shapes

Definition of done:

- pack install behavior is structurally consistent across translation, frequency, and embedding families
- new data-source onboarding has one explicit checklist instead of source-family-specific storage improvisation

Detailed execution plan:

1. Frequency normalization
   - install under `frequency_packs/<pack_id>/`
   - write `manifest.json`
   - keep the current SQLite writer and current pack-specific SQLite filenames during the first migration slice
   - begin tightening toward canonical columns like `lemma_lc`, `rank`, and `pmw`
   - migrate runtime/settings resolution to manifest-backed pack refs before removing filename assumptions or renaming artifacts to `main.sqlite`
   - current verified progress:
     - managed frequency installs now use stable pack roots plus manifests
     - helper default frequency discovery now prefers manifest-backed artifacts
     - helper/runtime now expose a first frequency pack-ref seam so diagnostics and pair-resource resolution can report pack id, provider, and POS source profile

2. Embedding normalization
   - install under `embedding_packs/<pack_id>/`
   - write `manifest.json`
   - make app-managed installs run conversion automatically so the completed state is always SQLite
   - retain raw downloads only in explicit debug/import modes
   - migrate runtime/settings resolution to manifest-backed pack refs and make raw `.vec/.bin` loading a compatibility path rather than the default app-managed contract
   - current verified progress:
     - app-managed embedding installs already complete as manifest-backed SQLite artifacts
     - per-pair managed embedding activation can now be persisted by pack id instead of only by raw artifact path
     - replacement-filter runtime can now resolve managed embedding pack ids back through manifest-backed SQLite artifacts while still honoring legacy/manual path entries
     - settings persistence now omits redundant managed embedding artifact paths when those installs are already represented by pack id + manifest-backed resolution

3. Shared seam cleanup
   - add installed-pack helpers for frequency and embedding families, not only translation
   - make diagnostics report pack id, provider, artifact path, and checksum from manifests
   - move helper/runtime/resource resolution toward pack refs instead of loose file paths
   - preserve compatibility wrappers until all active callers use manifests

## Phase C: Unified Pack Ref And Resolver

Goals:

- make helper/runtime/benchmark resolve pack refs from manifests
- remove filename/path guessing from generic layers

Definition of done:

- `default_translation_dictionary_path(...)` and similar helpers become compatibility wrappers around manifest-driven pack resolution

## Phase D: Normalized Lexical View Loaders

Goals:

- provider-specific parsers/loaders feed a shared normalized lexical-record interface

Definition of done:

- pair modules consume normalized lexical views rather than raw TEI/JSONL/XML files

## Phase E: Pair Migration

Recommended order:

1. migrate `de-en` first
2. keep `en-es` on the same normalized pack contract while preserving current advanced logic
3. widen to other cross-lingual and later monolingual pairs

## Phase F: Cleanup

Goals:

- remove obsolete flat-file assumptions
- remove provider-specific naming leaks from generic code
- make benchmark/resource artifacts report pack ids and manifest-backed metadata as the primary identity

## Immediate Practical Implication For `de-en`

Today, `de-en` still reads FreeDict TEI directly.
That is acceptable only as a temporary proof-LP step.

The next normalization milestone should therefore be:

- compile `freedict-en-de` into canonical SQLite
- resolve it through a manifest-backed pack ref
- make `de-en` consume the normalized compiled artifact instead of `eng-deu.tei`

That work should happen before deeper `de-en` rulegen quality tuning.

## Expected User Experience Changes

Most of the final behavior should feel cleaner, not stranger, but two families differ in how much user-visible change to expect.

### Translation Packs

Expected user experience:

- mostly unchanged once manifests are in place
- downloads still appear as one install action
- runtime should become more reliable because helper no longer depends on filename guessing

### Frequency Packs

Expected user experience:

- almost no intentional behavioral change
- they already convert to SQLite during install
- the main visible change should be more stable pack directories and clearer installed-pack identity

### Embedding Packs

Expected user experience:

- this is the family most likely to feel different
- today, users can keep a raw vector file around and convert later
- under the normalized model, app-managed installs should finish in a converted SQLite state automatically

Likely visible differences:

- install may take longer before the UI reports completion because conversion becomes part of installation
- disk usage may spike temporarily during conversion
- the "use" path should become simpler because there is one canonical artifact instead of raw-file-or-sqlite ambiguity

## Regression And Compatibility Risks

The main risks are operational and compatibility-related, not conceptual.

### Low-risk area: Frequency

Why low-risk:

- runtime already expects SQLite
- install already converts to SQLite
- the migration is mostly about manifest/layout/schema tightening

Primary regression risks:

- pack path migration bugs during delete/validate/status checks
- schema-tightening mistakes if fallback resolution is removed too early

Mitigation:

- keep current column fallback logic until all managed frequency packs write the canonical schema
- add manifest-aware tests for download, validate, delete, and runtime lookup

### Medium-risk area: Translation

Why medium-risk:

- Kaikki is already close
- FreeDict still has a real loader migration ahead from TEI to SQLite

Primary regression risks:

- loss of provider-specific metadata during TEI normalization
- pair modules assuming raw provider quirks that are not preserved in the normalized loader

Mitigation:

- preserve provenance and source-order metadata in the normalized SQLite
- migrate one pair at a time, with `de-en` as the first proof

### Highest user-experience risk: Embeddings

Why highest:

- the current app/runtime still tolerates raw `.vec/.bin` as an active path
- automatic conversion changes the timing and completion semantics of install

Primary regression risks:

- longer install times being perceived as failed or stuck downloads
- conversion failures surfacing later than today if status reporting is poor
- existing settings or runtime code still looking for raw files instead of manifest-backed SQLite

Mitigation:

- make conversion progress explicit in the UI
- keep raw-file import as a compatibility path for manually supplied external files
- treat app-managed packs and external/manual files as separate contracts
- do not remove raw runtime fallback until manifest-backed SQLite resolution is fully wired through settings and runtime

## Questions / Remaining Decisions

No blocking architectural questions remain after the new product direction:

- prefer compiled canonical runtime artifacts, ideally SQLite
- delete dirty raw downloads/extraction directories after successful build

One non-blocking future choice remains:

- do we want an explicit developer-only raw-retention toggle for debugging rebuilds?

Recommendation:

- yes, but opt-in only and excluded from the normal runtime contract
