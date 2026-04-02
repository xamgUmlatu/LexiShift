# Data Source Normalization Architecture

Status: active planning doc with first executable slice
Role: architecture target / implementation plan
Purpose: define the final desired architecture for installed language/data packs so rulegen, helper, and benchmark code consume a normalized contract instead of provider-specific raw files.
Last updated: 2026-04-03
Last verified: 2026-04-03 helper/gui path and manifest slice
Source-of-truth: planning doc only; executable truth still lives in code, tests, and current pack/build flows.

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

- translation language packs now install under stable per-pack roots rather than flat shared filenames
- language-pack downloads now write manifest files that record the canonical runtime artifact path
- helper translation-dictionary resolution now checks manifest-backed installed packs before falling back to filename/path guessing
- current runtime artifacts are still mixed:
  - FreeDict translation packs still expose TEI as the canonical runtime artifact
  - Kaikki translation packs still expose compatibility SQLite as the canonical runtime artifact

## Phase B: FreeDict Build Normalization

Goals:

- add a FreeDict build pipeline to canonical SQLite
- stop treating extracted TEI directories as the runtime contract

Definition of done:

- `freedict-en-de`, `freedict-de-en`, `freedict-en-es`, and `freedict-es-en` install to compiled SQLite artifacts plus manifests
- temporary extracted source directories can be deleted after successful builds

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

## Questions / Remaining Decisions

No blocking architectural questions remain after the new product direction:

- prefer compiled canonical runtime artifacts, ideally SQLite
- delete dirty raw downloads/extraction directories after successful build

One non-blocking future choice remains:

- do we want an explicit developer-only raw-retention toggle for debugging rebuilds?

Recommendation:

- yes, but opt-in only and excluded from the normal runtime contract
