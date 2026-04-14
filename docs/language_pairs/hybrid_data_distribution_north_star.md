# Hybrid Data Distribution North Star

Status: active plan
Role: Planning / WIP
Last updated: 2026-04-15
Last verified: 2026-04-15 repo-doc review against current LP licensing register, pack inventory matrix, helper/rulegen target loading, semantic publication flow, and publication manifest behavior
Purpose: define the long-term data-distribution posture for LexiShift so the project can eventually combine hosted open data with local restricted data without weakening rulegen quality or violating distribution policy
Source-of-truth: planning doc only; current implemented truth still lives in helper pack resolution, local helper publication, and the data-source licensing register
Related docs:
- `docs/language_pairs/data_source_licensing_and_distribution.md`
- `docs/language_pairs/lp_data_inventory_matrix.md`
- `docs/language_pairs/language_pack_urls.txt`
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`

## Current Product Posture

Current `v1` posture should stay explicit:

- all data is local
- all compile inputs are local
- all emitted runtime artifacts are local
- there is no cloud-hosted semantic or rulegen data requirement

That posture is acceptable for `v1`.

It is also the safest posture while:

- pack licensing remains mixed
- publication legality of compiled derivatives is not fully settled
- and cloud shard/update behavior is still unimplemented

## Problem The North Star Solves

Long term, LexiShift wants both:

- full rulegen / veto quality
- and smaller client-side downloads

Those goals are compatible only if the project separates:

1. build-time source inputs
2. runtime-delivered compiled outputs
3. distribution legality of each source lane

The browser or plugin should never need to know which upstream raw source produced a rule.
That decision belongs upstream in the compile pipeline.

## Core North-Star Principle

LexiShift should eventually support a hybrid source model:

- hosted/open source lanes
- local/manual-supply source lanes
- one compile step that can merge both
- runtime artifacts derived from that compile

The merge point should be helper/rulegen compile time, not browser runtime.

This lets LexiShift:

- preserve full compile quality when local restricted packs are available
- keep runtime small
- and avoid shipping raw corpora to every client

## Distribution Classes

The repo should eventually treat every input pack as belonging to a distribution class.

Minimum intended classes:

- `public_hostable`
  - source or converted artifact may be auto-downloaded or hosted by LexiShift if obligations are satisfied
- `manual_supply_only`
  - source or converted artifact must remain user-supplied/local until policy owner review settles redistribution

Optional future refinement:

- `local_generated_from_manual_supply`
  - converted local derivative remains local-only even if the conversion format is standardized

This classification is separate from:

- pack kind (`translation`, `frequency`, `embedding`, etc.)
- quality
- or whether the pack is currently integrated

## Compile Modes

To keep legality explicit, the build system should eventually expose two compile modes.

### 1. `public_hostable`

Use only source packs whose distribution class permits hosted or auto-downloaded publication.

Outputs from this mode may be:

- hosted by LexiShift
- cached remotely
- shared across users
- or pre-fetched as baseline artifacts

### 2. `local_augmented`

Allow the compile to additionally use manual-supply or otherwise local-only packs.

Outputs from this mode may improve quality, but they should remain:

- local to the user/device/profile
- not uploaded
- not shared as public cloud artifacts

This is the main asymmetry:

- hosted baseline can be broad but legally clean
- local augmentation can be stronger but must inherit local-only restrictions

## Inheritance Rule

Every compiled artifact should inherit the most restrictive distribution class of any source pack that materially contributed to it.

That rule should be treated as non-optional.

In practice:

- if a compiled ruleset uses only `public_hostable` packs, it may remain `public_hostable`
- if it uses even one `manual_supply_only` pack, the compiled artifact should become `local_only`

This avoids the most dangerous failure mode:

- accidentally publishing a derived artifact that was improved by a restricted local pack

## Where The Merge Should Happen

The intended future merge order is:

1. resolve target set `S`
2. resolve available pack lanes
3. filter lanes by compile mode
4. run rulegen and semantic compile using the permitted lanes
5. emit generation-aligned runtime artifacts

The browser runtime should only consume:

- ruleset
- snapshot
- semantic inventory

It should never need raw:

- frequency packs
- translation dictionaries
- Kaikki dumps
- or embeddings

## Artifact Classes

The repo should eventually distinguish three artifact classes.

### 1. Raw source packs

Examples:

- frequency databases
- FreeDict TEI or compatibility SQLite
- Kaikki-derived compatibility SQLite
- embeddings

These are governed directly by source licensing and pack-specific policy.

### 2. Converted local packs

Examples:

- normalized SQLite produced from a raw archive

These should not automatically be treated as more redistributable than the source they came from.

### 3. Compiled runtime outputs

Examples:

- `srs_ruleset_<pair>.json`
- `srs_rulegen_snapshot_<pair>.json`
- `srs_semantic_inventory_<pair>.json`

These are the only artifacts runtime needs.

Their distribution class should be computed from source provenance, not guessed from file type.

## Current Implication For `v1`

This north star does not change `v1`.

Current intended `v1` posture remains:

- fully local compilation
- fully local publication
- no cloud-hosted runtime bundle requirement
- no need yet to split hosted baseline from local augmentation

That is acceptable because:

- the product is unreleased
- the data-source policy matrix is still mixed
- and the repo should not rush cloud distribution before legality and provenance rules are enforced

## What Must Exist Before Hybrid Distribution

The following should exist before LexiShift attempts hosted/open plus local/manual hybrid delivery.

### 1. Pack-level policy metadata

Installed pack manifests should eventually record at least:

- `license_id`
- `distribution_class`
- `obligation_flags`
- `evidence_url`
- `verified_status`

### 2. Compile provenance

Publication manifests should eventually record:

- exact source pack ids used
- compile mode
- resulting artifact distribution class

### 3. Enforcement

The compile pipeline should refuse to mark an artifact as hostable if any contributing pack is local-only.

### 4. Runtime scope metadata

Hosted runtime bundles should later say whether they are:

- pair-global baseline
- profile-scoped closure
- or some future shard form

This avoids ambiguity about whether a missing record means:

- not needed for this bundle
- or publication corruption

## Recommended Future Product Shape

The most plausible long-term product shape is:

1. LexiShift can provide a hosted, legally clean baseline bundle built only from `public_hostable` inputs.
2. Advanced users can add local packs for higher quality.
3. Helper compile merges those local packs into a better local-only build.
4. Runtime uses the resulting compiled bundle without caring which upstream lanes produced it.

That gives the project the desired combination:

- smaller default downloads
- good baseline quality
- stronger local quality when the user opts in
- and clear legal boundaries

## Decision Summary

Current decision:

- document the hybrid model as the north star
- keep `v1` entirely local
- do not force cloud architecture now
- and do not publish derived artifacts across mixed-license inputs until provenance-driven distribution enforcement exists
