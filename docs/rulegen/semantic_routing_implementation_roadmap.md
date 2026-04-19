# Semantic Routing Implementation Roadmap

Status: planning slice
Role: Planning / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 doc-routing review against the current contract, launch, and research-plan docs plus stable semantic publication/runtime references
Purpose: sequence the work required to turn semantic-routing publication scaffolding plus research harnesses into a real runtime admission layer, while keeping the architecture LP-symmetric and transport-agnostic
Source-of-truth: planning doc only; current implemented truth still lives in code, `docs/developer/feature_state_matrix.md`, and the linked planning docs
Related planning docs:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
Related runbooks:
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
Verification:
- `core/lexishift_core/rulegen/semantic_publication.py`
- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/engine.py`
- `scripts/helper/lexishift_native_host.py`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`

## Document map

Use the semantic-routing docs in this order:

1. `docs/rulegen/semantic_routing_publication_contract.md`
   - current emitted-rule pointer, sidecar, manifest, and helper diagnostics contract
2. `docs/rulegen/semantic_routing_runtime_readiness.md`
   - current shipped browser-runtime seam and the remaining readiness boundary
3. `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
   - operational runbook for the first controlled `en-es` launch only
4. this roadmap
   - near-term implementation ladder from the current emitted-sibling PoC to a broader launchable system
5. `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
   - post-PoC evidence plan for proving blocker generation beyond the emitted-sibling slice
6. `docs/rulegen/semantic_shadow_testing_architecture.md`
   - research harness architecture and experiment workflow, not the current launch contract
7. `docs/rulegen/semantic_routing_data_update_lifecycle.md`
   - future data-promotion/update lifecycle once broader semantic evidence starts landing

Do not mix those roles.
Current contract truth, launch steps, and research evidence should not be reconstructed by averaging multiple docs together.

## Goal

Ship semantic veto as a real end-to-end runtime feature.

The first production target is `en-es`.
The architecture target is all LPs.

That means:

- `en-es` may be the first pair with a real runtime semantic gate,
- but the contracts, publication surfaces, and runtime seams must not become `en-es`-specific,
- and the research harnesses must remain first-class rather than getting replaced by opaque production logic.

## Design Rules

These rules should stay fixed throughout the roadmap.

### 1. Freeze interfaces now, defer transport decisions

We do not need to decide yet whether semantic packages are:

- helper-local files,
- downloaded assets,
- packaged resources,
- or cloud-backed caches.

We do need to decide now:

- the runtime request/response contract,
- the semantic package contract,
- the fallback behavior when data is unavailable,
- and the versioning story for future algorithm updates.

### 2. Keep runtime thin and decision logic centralized

The browser/plugin should:

- find concrete matches in flowing text,
- extract local context,
- call a semantic admission service,
- render or abstain,
- and log diagnostics.

The helper/backend should own:

- semantic inventory loading,
- phrase-preemption logic,
- active-vs-shadow scoring,
- near-tie rescue logic,
- and policy versioning.

This keeps:

- one production decision engine,
- one benchmark target for the harnesses,
- and one place to update the algorithm later.

### 3. Broad ingest, narrow publish

Research and build pipelines may use:

- raw dictionaries,
- frequency packs,
- Wiktionary/Kaikki dumps,
- example banks,
- bridge signals,
- and later silver/LLM sources.

Runtime should consume only a distilled semantic package:

- compact rule pointer,
- semantic inventory sidecar,
- explicit policy ids and readiness states.

### 4. Separate four kinds of versioning

Do not collapse these into one opaque version field:

- `schema_version`
- `selection_policy_version`
- `decision_policy_id`
- `fallback_policy`

That separation is what allows:

- new runtime policies without rebuilding every inventory,
- new shadow-mining policies without changing browser contracts,
- and LP-specific readiness without LP-specific payload shapes.

### 5. Keep all LPs on one emitted shape

Every LP should aim to emit the same top-level rule metadata seam:

- `rule.metadata.semantic_admission`

Even when the only truthful payload is:

```json
{
  "schema_version": 1,
  "status": "unavailable",
  "reason_code": "missing_source_sense_locator"
}
```

This avoids a short-term architecture where `en-es` gets a bespoke runtime contract and every other LP later has to be migrated.

### 6. Preserve harnesses as production-adjacent tools

The current harnesses should survive and keep testing the same logic used in production:

- shadow mining and promotion harnesses remain the offline blocker-generation test bed,
- sentence-veto harnesses remain the runtime-decision test bed,
- runtime diagnostics remain the live observability surface.

The goal is:

- shared policy code,
- different callers.

## Target End-To-End Shape

The intended final flow is:

1. offline rulegen/publication emits rules plus semantic package
2. runtime loads rules plus semantic package metadata
3. runtime finds concrete source-phrase matches in a text node or message
4. runtime batches semantic-admission checks for eligible matches
5. helper decision engine returns:
   - `replace`
   - `abstain`
   - later, optional `soft_affordance`
6. runtime renders spans only for admitted matches
7. runtime diagnostics record:
   - why a match was admitted,
   - why it abstained,
   - and whether a fallback path was used

The current runtime seam for this is match-time filtering, not active-rule resolution.
In repo terms, that means semantic gating belongs downstream of trie matching and upstream of span creation.

## Starting Point

This roadmap assumes the current-truth docs above are read first and intentionally does not restate their full checkpoints.

Current ownership:

- `docs/rulegen/semantic_routing_publication_contract.md` owns the current emitted pointer, semantic inventory, manifest, diagnostics, and reset family
- `docs/rulegen/semantic_routing_runtime_readiness.md` owns the shipped browser-runtime seam and the remaining readiness boundary
- `docs/developer/feature_state_matrix.md` owns the implemented/default-off/verified status snapshot
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md` owns the first controlled `en-es` launch procedure and fallback posture

Planning summary this roadmap builds on:

- `metadata.semantic_admission` pointer scaffolding is real
- helper publication can write semantic inventory plus a generation-aligned publication manifest
- browser runtime can load semantic inventory from helper/cache and call `semantic_admit_batch` for ready rows when enabled
- current `en-es` ready coverage is still only the batch-local emitted-sibling PoC
- broader shadow-mined blocker publication, phrase publication, and multi-LP rollout remain later tracks

This roadmap therefore focuses on phase order and design rules rather than re-documenting the current contract or launch checklist in full.

## Roadmap Phases

### Phase 1. Freeze contracts and policy boundaries

Objective:

- make the serving boundary explicit before implementation drifts into pair-specific or transport-specific shortcuts

Deliverables:

- final `semantic_admission` schema rules for runtime use
- final semantic inventory sidecar contract for runtime use
- semantic admission request/response schema for runtime calls
- explicit version split:
  - `schema_version`
  - `selection_policy_version`
  - `decision_policy_id`
  - `fallback_policy`
- explicit rollout policy states:
  - `legacy_on_unavailable`
  - `abstain_on_unavailable`
  - later `soft_affordance_on_unavailable`

Implementation notes:

- keep this LP-symmetric
- keep source-specific provenance out of runtime payloads
- keep unknown fields ignorable so future upgrades are additive

Acceptance:

- the same request/response contract can serve `en-es` now and other LPs later
- the contract does not require any runtime knowledge of raw dictionary record shapes
- transport can remain undecided

### Phase 2. Productize semantic package publication and serving

Objective:

- make the semantic package a first-class published artifact instead of a research sidecar that only diagnostics understand

Deliverables:

- helper request for `get_semantic_inventory`
- extension/helper-client method parallel to `getRuleset()` and `getSnapshot()`
- helper cache path for semantic inventory
- generation-aligned loading of:
  - ruleset
  - snapshot
  - semantic inventory
- clearer capability/readiness metadata in the published inventory
- explicit `phrase_sets` status even when the set is empty or unavailable

Implementation seams:

- `core/lexishift_core/helper/engine.py`
- `scripts/helper/lexishift_native_host.py`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`

Acceptance:

- runtime can fetch semantic inventory for a pair/profile without reading raw source corpora
- semantic inventory cache invalidation follows the same generation lifecycle as ruleset publication
- helper diagnostics can show whether the runtime semantic package is actually loadable

### Phase 3. Land a production semantic-admission service in the helper

Objective:

- move the best current runtime algorithm out of research harness-only code paths and into a callable production decision engine

Deliverables:

- helper request for batched semantic admission, for example `semantic_admit_batch`
- production policy registry, starting with `en_es_sentence_veto_v1`
- shared Python decision engine that uses:
  - phrase/frame guard
  - primary scorer
  - margin logic
  - narrow active rescue
- reason-code output for every abstain or replace decision
- policy metadata returned in every decision result

Required discipline:

- production decision code must call the same underlying scoring/policy code that the harness can evaluate
- no browser-only reimplementation of the algorithm

Suggested shape:

- request contains:
  - pair
  - profile_id
  - context text
  - match offsets or matched source phrase
  - rule pointer ids from `semantic_admission`
- response contains:
  - `decision`
  - `decision_policy_id`
  - `reason_codes`
  - compact score summary for diagnostics

Acceptance:

- the sentence-veto harness can replay the same policy id used by production
- policy behavior is versioned and attributable in artifacts and logs
- adding a new policy does not require changing the browser contract

### Phase 4. Wire semantic gating into extension/plugin runtime

Objective:

- make runtime semantic admission a real part of the replacement path while preserving the existing deterministic replacement core

Deliverables:

- runtime semantic package loader/cache
- per-text-node or per-message batching of semantic checks
- match filtering before span creation
- runtime handling of:
  - `ready`
  - `unavailable`
  - `not_applicable`
  - missing or stale package
- production gating flag so semantic admission can be enabled per pair/profile

Why the seam matters:

- semantic gating should happen after trie matches are known
- semantic gating should happen before DOM spans are created
- semantic gating should not mutate active-rule resolution itself

Implementation seams:

- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
- likely new `apps/chrome-extension/content/runtime/semantic/*` modules

Acceptance:

- disabling semantic routing restores today’s runtime behavior
- enabling semantic routing only changes eligible matches, not unrelated DOM scanning behavior
- the same architecture can be reused by the BetterDiscord runtime surface

### Phase 5. Add production observability and failure accounting

Objective:

- make runtime semantic behavior debuggable and safe to iterate on

Deliverables:

- counters for:
  - semantic-ready matches
  - semantic replaces
  - semantic abstains
  - phrase-preempted matches
  - rescue-triggered matches
  - fallback-path matches
- per-decision reason-code summaries in runtime diagnostics
- optional sampled decision logs for debugging
- clear distinction between:
  - missing readiness
  - policy abstain
  - package load failure
  - policy execution failure

Acceptance:

- a developer can answer why a visible word was replaced or not replaced
- future algorithm changes can be judged against live diagnostics instead of anecdote

### Phase 6. Launch `en-es` as the first production pair

Objective:

- turn the current narrow `en-es` path into the first real controlled launch without letting the PoC define the long-term architecture

Operational owner:

- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`

Phase discipline:

- use the checklist for fallback posture, validation commands, per-profile enable steps, and explicit launch out-of-scope limits
- keep the exact published-ready boundary aligned with the current contract docs rather than restating it here
- keep broader shadow-mined blocker publication and multi-LP rollout on separate tracks even if the first `en-es` pilot succeeds

Acceptance:

- launch-readiness questions can be answered from the checklist plus current-truth contract docs instead of research notes or duplicated roadmap prose

### Phase 7. Generalize the framework to other LPs

Objective:

- make new LP support a publication and policy problem, not a browser-architecture rewrite

LP maturity ladder:

### Tier 0. Pointer-only

- LP emits `semantic_admission` with `status=unavailable`
- runtime contract already stays compatible

### Tier 1. Published inventory

- LP can publish triggers and senses
- competition sets may still be unavailable
- runtime can inspect readiness accurately

### Tier 2. Pilot runtime semantic veto

- LP can publish a conservative ready subset
- helper can serve a pair-specific decision policy
- runtime can gate those ready rows only

### Tier 3. Production semantic veto

- LP has enough publication coverage and testing evidence for broader use

Cross-LP requirements:

- same top-level rule pointer shape
- same semantic inventory shape
- same runtime request/response shape
- pair capability flags decide readiness, not browser-side pair branching
- pair-specific mining/promotion remains offline
- pair-specific decision policy remains helper-side

Initial follow-on LP candidates:

- `en-de`
- `de-en`
- `en-ja`
- `es-en`

Expected asymmetry:

- some LPs may sit at Tier 0 or Tier 1 for a long time
- that is acceptable as long as the shared contracts do not fork

### Phase 8. Decide transport and package distribution later

Objective:

- choose the best delivery model after the package contract is stable

Options that should remain open:

- helper-local file publication only
- packaged local assets
- online package download and local cache
- cloud sync for profile/pair assets

Explicit non-goal for now:

- do not let transport choice reshape the runtime decision contract

Acceptance:

- changing the delivery mechanism does not require changing:
  - rule payloads
  - semantic inventory shape
  - decision request/response contract
  - harness evaluation logic

## Testing And Verification Ladder

These lanes should exist simultaneously.

### 1. Publication correctness

- rule metadata roundtrip tests
- semantic inventory publication tests
- helper diagnostics tests

### 2. Decision-policy correctness

- targeted unit tests for phrase guards, rescue logic, and scorer behavior
- curated sentence-veto harness
- policy sweeps against fixed competition sets

### 3. Runtime integration correctness

- extension/plugin tests for:
  - package load
  - unavailable readiness
  - abstain path
  - replace path
  - diagnostics

### 4. Product-shape confidence

- lower-bound veto proxy for blocker-generation quality
- sentence-veto benchmark for runtime-decision quality
- live runtime diagnostics for actual user-facing behavior

## Decisions We Do Not Need Now

These should stay explicitly deferred:

- final cloud/package transport mechanism
- final UI for soft affordance
- broad multi-pair rollout timing
- heavier model optimization beyond the first stable production policy
- source-heavy experimentation for every future LP before the first `en-es` launch

## Recommended Next Implementation Moves

In order:

1. freeze the semantic admission request/response contract
2. add helper-side `get_semantic_inventory`
3. add helper-side `semantic_admit_batch`
4. promote the current best `en-es` decision logic into a named production policy
5. wire runtime gating at match time
6. add semantic runtime diagnostics
7. launch `en-es` in a conservative rollout mode

That sequence gives the project:

- one real shipped pair,
- one stable cross-LP architecture,
- and a future-proof place to keep improving the algorithm without redoing the E2E.
