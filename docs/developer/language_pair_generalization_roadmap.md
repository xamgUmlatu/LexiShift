# Language Pair Generalization Roadmap

Status: active planning doc
Role: roadmap / sequencing
Purpose: Define the recommended order for generalizing the current `en-es`-optimized rulegen and benchmark stack so it can support additional language pairs and additional data-source families without duplicating pair-specific infrastructure.
Last updated: 2026-04-03
Last verified: 2026-04-03
Source-of-truth: planning doc only; executable truth still lives in code, tests, and the current pair/resource capability docs.

## Scope

This roadmap is about the next architectural workstream after the current `en-es` optimization and sweep work:

- make the benchmark/resource contract pair-agnostic
- make the translation-pack/resource layer provider-agnostic
- preserve the current `en-es` compiled benchmark path as the reference implementation
- identify the first concrete LP that should land once the abstraction boundary is clean enough

This roadmap now assumes a broader normalization rule:

- the same manifest-backed installed-pack model should be applied to existing pack families over time
- any new data-source onboarding should follow that model from the start rather than introducing fresh flat-file runtime contracts

This doc is not a promise to make every LP production-ready immediately.
It is the sequencing plan for reaching that point without creating throwaway pair-specific code.

Related:

- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/data_source_normalization_architecture.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/rulegen_benchmark_optimization_plan.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/rulegen_test_pipeline.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/de_en_workstream_roadmap.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/extension_lp_generalization_checklist.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/lp_resource_requirements.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/core/lexishift_core/helper/lp_capabilities.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/language_packs_catalog.py`

## Current Baseline

Current executable rulegen adapters:

- `en-ja`
- `en-de`
- `en-es`
- `es-en`

Current pair/data observations:

- `en-es` is now the most advanced optimization target and the current benchmark reference lane.
- The benchmark optimization work has already moved toward a backend-neutral pair-resource contract, but current implementation is still materially pair-heavy in `en-es`.
- Pair capability and source resolution still need continued generalization, but the canonical pair-capability dictionary requirement field is now the generic `requires_translation_dictionary_for_rulegen`, not a provider-shaped alias.
- GUI language-pack endpoints already exist for a wider source set than the currently optimized pair uses:
  - `freedict-de-en`
  - `freedict-en-de`
  - `freedict-es-en`
  - `freedict-en-es`
  - `wiktionary-es-en`
  - `wiktionary-en-es`
  - `wordnet-en`
  - `moby-en`
  - `odenet-de`
  - `openthesaurus-de`
  - `jp-wordnet`
  - `jp-wordnet-sqlite`
  - `jmdict-ja-en`

Current missing/blocked LPs are therefore not all blocked by raw endpoint availability.
Many are blocked by:

- pair-specific adapter gaps
- helper/runtime generalization gaps
- missing frequency packs
- missing monolingual synonym pipelines

## High-Level Goal

The goal is not only "support more pairs."

The real goal is:

1. one generic benchmark/resource contract
2. one generic pair compile boundary
3. pair-specific rulegen logic plugged into that boundary
4. provider-specific loaders hidden below that boundary
5. later multi-pack and agreement experiments using the same contract

If that is done well, adding a new LP should become mostly:

- add capabilities
- add or link resources
- add one pair adapter or pair profile
- run the benchmark and SRS quality loops

instead of requiring a new end-to-end architecture slice every time.

The first concrete proof-LP execution plan now lives in:

- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/de_en_workstream_roadmap.md`

## Ordering Principles

1. generalize interfaces before adding many new LPs
2. remove legacy source-specific naming from generic paths
3. keep benchmark semantics stable while generalizing contracts
4. prove the generalized contract on one additional LP before widening further
5. do not mix monolingual and cross-lingual generalization in the first slice unless the contract truly supports both

## Phase 1: Clean Up Generic Resource Naming

Status:

- should start soon

Why first:

- current generic code and artifacts still use names like `freedict_path` for non-FreeDict reality
- that makes the architecture harder to reason about and harder to extend cleanly

Concrete targets:

- remove FreeDict-specific names from generic benchmark/resource surfaces
- replace generic "freedict" language with "translation dictionary" or "translation pack" where behavior is actually provider-neutral
- keep provider identity explicit as metadata, not hidden in field names

Examples to clean:

- pair capability booleans that still need to stay role-based and provider-neutral
- artifact/resource fields that imply one provider family
- helper naming that leaks old implementation detail into generic code paths

Definition of done:

- generic surfaces describe role, not current provider
- provider/source family remains available as explicit metadata
- `en-es` behavior does not change

## Phase 2: Define A Normalized Translation-Pack Contract

Status:

- started

Goal:

- make the benchmark, helper, and adapter layers consume the same normalized forward/reverse dictionary contract regardless of underlying storage format

The contract should cover:

- forward translation pack
- reverse translation pack
- provider identity
- storage/path/checksum metadata
- POS source/profile
- preserved auxiliary metadata availability
- compile-time record access

The contract should not assume:

- SQLite only
- FreeDict only
- Kaikki only
- one pack per provider family

This is the key architectural seam that lets future sources such as:

- TEI-derived compatibility SQLite
- Kaikki-derived SQLite
- native SQLite synonym packs
- later CEDICT or other dictionary families

feed the same benchmark and rulegen substrate.

The explicit final-storage direction is now documented separately:

- normalize installed packs around manifest-backed canonical compiled artifacts
- prefer SQLite for the canonical runtime artifact
- treat raw provider downloads/extractions as build inputs, not runtime contracts
- delete dirty raw download/extraction artifacts after a successful build unless a developer-only retention mode is enabled

See:

- `/Users/takeyayuki/Documents/projects/LexiShift/docs/developer/data_source_normalization_architecture.md`

Definition of done:

- benchmark input resolution uses normalized translation-pack objects
- pair adapters accept normalized translation-pack resources
- storage/provider specifics are below the loader/resource boundary

Current verified progress:

- helper/runtime resolution already prefers generic `translation_dict_path`
- adapter requests and helper job configs now accept generic `translation_dict_path`
- helper-to-adapter rulegen calls can now carry normalized `TranslationPackRef` objects
- helper resource resolution and runtime diagnostics now resolve/report normalized translation-pack identity
- legacy `freedict_*` fields remain as compatibility aliases while pair-local configs are still being normalized
- translation language packs now also install under stable per-pack roots with `manifest.json`, and helper translation-dictionary resolution can read those manifests before falling back to filename guessing

## Phase 3: Generalize The Compiled Pair Boundary

Status:

- should happen while Phase 2 is landing

Goal:

- turn the current `en-es` compiled benchmark path into a reusable pair-compile pattern rather than a special one-off acceleration path

Target shape:

- resolve inputs
- load normalized resources
- compile pair context / benchmark IR
- sweep configs
- materialize artifacts

Pair-specific code should live in:

- candidate extraction
- signal projection
- ranking semantics
- optional pair-local metadata views

Pair-specific code should not leak into:

- generic sweep orchestration
- artifact shape
- resource identity
- cache storage model

Definition of done:

- `en-es` remains the reference implementation
- the benchmark engine can describe a generic compile/sweep/materialize flow for any pair
- adding a new pair does not require another benchmark-engine fork

## Phase 4: Generalize Pair Capability And LP Readiness

Status:

- should start once the resource contract is clear

Goal:

- make helper/runtime readiness checks reflect LP/resource reality cleanly

Current issues to resolve:

- capability flags still reflect old provider assumptions
- some LP readiness is documented but not encoded cleanly
- missing-resource errors are still more implementation-shaped than LP-shaped

Concrete work:

- replace provider-specific booleans with capability/resource-role fields
- make pair requirements explicit:
  - forward dictionary required or not
  - reverse dictionary optional/required
  - frequency pack required
  - stopwords optional
  - seed validation source
- keep GUI/helper readiness aligned with the same source of truth

Definition of done:

- helper, extension, and benchmark code all speak the same LP requirement model
- missing-resource messages are pair-specific and source-role-specific

## Phase 5: Land The First Additional LP On The Clean Contract

This is the point where it becomes easiest to stop abstracting and add one concrete LP.

Recommended first LP:

- `de-en`

Why `de-en` is the best first concrete target:

- it is cross-lingual like the current optimized workstream
- it already has a GUI-downloadable dictionary endpoint: `freedict-en-de`
- it can reuse the existing English frequency pack: `freq-en-coca`
- the current blocker is mainly adapter/helper generalization, not missing raw endpoint discovery
- it is explicitly called out in the current checklist as "data mostly available, adapter still missing"

Why not another pair first:

- `en-de` still needs a practical real German frequency setup for full usability
- `de-de` is still blocked by a real German frequency pack plus monolingual pipeline work
- `en-en` has sources available, but monolingual synonym-rulegen is a distinct pipeline family and should not be the first proof target if the immediate goal is to generalize the current translation-pair architecture
- `en-zh` is still blocked by missing Chinese frequency infrastructure and adapter work

Definition of done for this phase:

- `de-en` has a real adapter
- helper/runtime readiness resolves correctly
- benchmark and rulegen run through the generalized contract
- no regression to `en-es` or `en-ja`

## Phase 6: Add The First Missing Data-Source Pack That Unlocks Multiple LPs

This is the first "just add the missing data source" moment.

Recommended first missing data-source addition:

- German frequency pack completion and app-facing pipeline polish

Why this is the best first missing data-source lane:

- it unlocks practical `en-de`
- it is also a blocker for `de-de`
- the build path already exists and is documented
- this is a more leveraged addition than adding a one-off niche dictionary endpoint

Concrete targets:

- make `freq-de-default.sqlite` a first-class, reproducible pack workflow
- keep or improve app-button wiring for German frequency generation/install
- add stopword readiness where appropriate

This is the moment to tell the user "it is now easiest to just land a concrete missing data-source lane."

## Phase 7: Broaden To Monolingual LPs

Only after the translation-pair generalization is proven.

Recommended order:

1. `en-en`
2. `ja-ja`
3. `de-de`
4. `es-es`

Reasoning:

- `en-en` has the cleanest source availability: WordNet + Moby + English frequency already exist
- `ja-ja` also has source availability, but the monolingual Japanese semantics deserve a more careful adapter
- `de-de` depends on the German frequency lane becoming real
- `es-es` still needs concrete monolingual source selection

This phase should reuse the same benchmark/resource contract, but it will need a different rule source family:

- synonym dictionary rather than translation dictionary

So the generalized contract should be broad enough to support:

- translation pack lanes
- synonym pack lanes

without making the first translation-focused slice too abstract too early.

## Phase 8: Only Then Widen Multi-Source And Agreement Work

Not a first generalization step.

This should come after the basic pair/resource contract is stable.

Later work here includes:

- multi-pack agreement scoring
- multiple forward sources in one LP lane
- multiple reverse sources in one LP lane
- later trait-conditioned routing informed by source family and target traits

## Recommended Immediate Work Queue

This is the concrete order I would follow from the current codebase:

1. generic naming cleanup for translation resources and capability flags
2. normalized translation-pack contract at benchmark/helper/adapter boundary
3. generic compiled pair-context boundary cleanup
4. pair capability / LP readiness model cleanup
5. implement `de-en` on the cleaned contract
6. land/polish German frequency pack workflow
7. only then widen to monolingual LPs such as `en-en`

## When To Tell The User "Now Is The Time To Add A Specific Language"

There are two decision points:

1. First concrete LP moment:
- when Phases 1 through 4 are clean enough
- then `de-en` becomes the right first concrete LP to land

2. First concrete missing data-source moment:
- once the translation contract is stable enough that new LP work is no longer architecture-blocked
- then German frequency is the best missing data-source lane to add next

So the short version is:

- first concrete LP: `de-en`
- first concrete missing data-source lane: German frequency / stopword readiness

## Non-Goals For The First Generalization Slice

Do not do these first:

- full all-pair quality optimization
- generic monolingual + cross-lingual unification in one single hard switch
- embedding-led generalization
- multi-source agreement implementation
- trait-conditioned runtime routing
- broad GPU generalization

Those all benefit from the cleaner pair/resource contract, but they are later work.

## Success Criteria

This workstream is going well if:

- `en-es` remains stable and benchmark-equivalent
- generic resource fields no longer pretend everything is FreeDict-shaped
- benchmark and helper code can talk about normalized pair resources cleanly
- `de-en` becomes a straightforward next LP instead of a bespoke engineering project
- adding a new pack/provider starts to look like data plumbing plus adapter logic, not whole-pipeline surgery
