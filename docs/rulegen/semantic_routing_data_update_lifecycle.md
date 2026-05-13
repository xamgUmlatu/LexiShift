# Semantic Routing Data Update Lifecycle

Status: active plan
Role: Planning / operational
Last updated: 2026-05-12
Last verified: 2026-05-13 helper CLI/native-host semantic-pack installer tests, named-pack resolver tests, default tranche-004 dev pack, and disposable product-root install smoke
Purpose: define the update process for semantic-routing data so LexiShift can add mined, manual, and later LLM-derived evidence without creating awkward runtime coupling, redundant storage, or unsafe publication flow
Source-of-truth: planning doc only; current implemented truth still lives in helper publication/runtime code and the semantic-routing contracts
Related docs:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/rulegen/semantic_feedback_promotion_flow.md`
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
- `docs/rulegen/semantic_pack_operator_smoke_runbook.md`

Routing note:

- this document does not redefine the current helper publication/runtime contract
- it also does not replace the first-launch `en-es` runbook
- use it when the question is how mined, reviewed, manual, or later LLM-derived semantic data should be stored, promoted, and republished over time

## Current Scope Assumptions

This proposal is deliberately grounded in the current project reality:

- the product is still unreleased
- semantic-routing data is still local/helper-first
- there is no cloud sync requirement yet
- there is no need yet for background auto-update behavior

That does not remove the need for an update model.

The risk is the opposite:

- if mined data, reviewed data, and later LLM data start landing ad hoc,
- we will create duplicated artifacts,
- unclear provenance,
- and a runtime path that becomes harder to migrate later.

The goal of this document is to prevent that while the system is still small.

## Core Rule

Semantic-routing data updates should always happen in two different layers:

1. source-of-truth data update
2. runtime artifact publication

Those layers must not be collapsed.

Source-of-truth data is where we ingest:

- mined lexical evidence
- reviewed corrections
- synthetic or LLM proposals
- future example and cue packs

Runtime artifact publication is where we emit only the narrow contract runtime actually consumes:

- `rule.metadata.semantic_admission`
- ruleset
- snapshot
- semantic inventory sidecar

This is the most important discipline in the whole lifecycle.

## Design Rules

### 1. Never edit published runtime artifacts by hand

The files runtime consumes are outputs, not authoring surfaces.

Do not directly patch:

- `srs_ruleset_<pair>.json`
- `srs_rulegen_snapshot_<pair>.json`
- `srs_semantic_inventory_<pair>.json`

Those should always be regenerated from upstream source-of-truth data.

### 2. Keep raw evidence append-only

Raw source batches should be treated as append-only records with explicit provenance.

Corrections should happen by:

- adding review decisions
- adding normalized overrides
- or publishing a new compiled generation

not by mutating old raw batch content until its origin becomes ambiguous.

### 3. Runtime should only consume compiled generations

LLM output must never go straight to runtime.

The allowed path is:

1. ingest raw/silver rows
2. normalize and dedupe them into the canonical evidence layer
3. compile a generation
4. validate the generation
5. publish the generation
6. let helper/runtime consume only the published generation

### 4. Publish the full artifact family atomically

Ruleset, snapshot, and semantic inventory form one publication family.

They should be:

- built from the same generation
- promoted together
- rolled back together
- deleted together on reset

Do not allow mixed generations across those files.

### 5. Add one release identity beyond the existing semantic version axes

The current contracts already separate:

- `schema_version`
- `selection_policy_version`
- `decision_policy_id`
- `fallback_policy`

That is correct and should stay.

The update process still needs one more identity:

- `generation_id`

`generation_id` answers a different question:

- which exact compiled build is live right now?

It should not replace the existing semantic version fields.
It should sit alongside them.

### 6. Avoid heavy per-profile duplication

Today the local helper materializes artifacts per `pair/profile_id`, which is fine.

If cloud-backed data arrives later, the heavy semantic content should not be duplicated per profile by default.

The recommended future split is:

- pair-global semantic core
- profile-local publication overlay
- helper-local materialized runtime files

This preserves the current runtime contract while avoiding cloud-side waste.

### 7. Keep provenance explicit all the way through

Every upstream row should keep enough provenance to answer:

- where it came from
- whether it was mined, manual, or LLM-generated
- whether it is reviewed
- what model/prompt produced it if synthetic
- what normalization or dedupe step transformed it

If a compiled blocker set improves metrics, we should be able to trace why.

### 8. Keep family-level queue state separate from raw batches

Raw batches are not enough to manage iterative LLM augmentation well.

If the project intends to:

- spend one bounded budget tranche now
- and potentially add more semantic data later

then the repo also needs a family-level queue memory layer.

That queue memory should answer:

- which semantic families have already been attempted
- which generation kind was attempted for each family
- which batch attempted it
- whether the family still looks unresolved
- and whether the current likely diagnosis is data-related or non-data-related

Without that layer, later batch waves will drift toward redundant regeneration.

### 9. Treat user feedback as weak evidence, not direct semantic truth

If future user reporting is added for semantic failures, those reports should enter the system as weak evidence.

The safe default is:

- ingest the report as a raw event with provenance
- keep local safety action as a separate override path
- but require review-gated promotion before shared semantic truth changes

This applies even when the report is attached to one exact fired rule.

Per-rule event granularity is useful for diagnostics and later clustering.
It is not enough reason to bypass review.

### 10. Keep local user overrides separate from shared semantic truth

Users may eventually need the ability to locally suppress or remove a bad rule.

That is a valid safety mechanism, but it should not mutate:

- shared source-of-truth evidence
- compiled semantic generations
- or published pair-global semantic artifacts

Instead, local suppression should live in a profile-local or helper-local override layer.

That preserves two important properties:

- the user gets immediate protection
- the shared semantic pipeline stays auditable and reviewable

Current planning anchor:

- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`

## Proposed Data Layers

The clean update lifecycle has eight layers if the family queue memory step is counted separately.

### Layer 0. Approval and source registry

Purpose:

- declare which source families are allowed into the offline stack

Current repo anchor:

- `docs/test_inputs/semantic_shadow_source_registry.json`

This layer answers:

- is a source family approved at all?
- is it intended for coverage, discrimination, cue generation, or silver proposals?

### Layer 0.5. Family inventory and queue state

Purpose:

- remember which semantic competition families deserve attention and which have already been attempted

This layer should track:

- family identity
- likely root-cause bucket
- queue status
- prior generation attempts
- and current recommended action

This is the layer that makes later additive LLM waves practical instead of redundant.

Current planning anchor:

- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

### Layer 1. Raw source batches

Purpose:

- store newly ingested records exactly enough that provenance is preserved

Examples:

- mined dictionary exports
- reviewed patch rows
- LLM shadow proposal batches
- LLM anchor/cue proposal batches
- future user semantic-report event batches

Required fields conceptually:

- `batch_id`
- `source_family`
- `pair`
- `source_type`
- `ingested_at`
- `provenance`
- `review_state`

LLM batches should also carry:

- `model_id`
- `prompt_version`
- `temperature`
- `cost_metadata`

Paid LLM generation runs should preserve a durable run directory before any row
is normalized or admitted. The recommended local product path is:

```text
<lexishift_data_root>/language_packs/<pair>/semantic_generation_runs/<run-id>
```

That directory should contain the run manifest, exact request queue, append-only
journal, raw-response JSONL, failure JSONL, final raw bundle, and final generated
responses. Raw paid outputs are source material. If later normalization,
postprocessing, scoring, or publication fails, the project should be able to
rebuild from that run directory without paying for the same completed requests
again.

Current repo anchor for the first LLM lane:

- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
  - raw batch envelope for offline LLM shadow, bridge, and cue proposals before any canonical normalization
- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
  - raw event envelope for future semantic user reports before any aggregation or promotion

### Layer 2. Normalized canonical evidence

Purpose:

- convert heterogeneous source rows into one stable internal evidence model

This is where we:

- dedupe equivalent senses
- reconcile trigger spelling variants
- normalize POS
- attach stable sense locators where possible
- tag rows as runtime-publishable or not

This layer should still be richer than runtime.
It is the build input, not the served package.

Current repo anchors for the first normalized lane:

- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`
  - canonical offline evidence shape after raw rows are normalized
- `core/lexishift_core/rulegen/semantic_evidence.py`
  - deterministic batch normalizer for the current LLM intake seam

### Layer 3. Compiled semantic generation

Purpose:

- build one immutable semantic-routing generation from the canonical evidence layer

Each generation should have:

- `generation_id`
- build timestamp
- pair scope
- input batch references
- normalization version
- selection policy version
- validation summary

The output of this layer is the first thing that should be treated as releasable.

### Layer 4. Publication family

Purpose:

- produce the exact runtime-facing files for one `pair/profile_id`

Current runtime-facing family:

- ruleset
- snapshot
- semantic inventory

Today those are written locally through helper publication.
That should remain the only thing runtime reads.

### Layer 5. Release manifest

Purpose:

- say which compiled generation is active

For the current local-only world, this can stay implicit.

For any future remote or cloud-backed world, make it explicit.

Recommended manifest identity:

- channel name such as `dev`, `pilot`, or `stable`
- target `generation_id`
- artifact hashes
- publication timestamp

### Layer 6. Helper-local materialization

Purpose:

- place the active generation onto the current helper paths runtime already expects

This final materialization step is what keeps runtime simple.

The browser/helper runtime should not care whether the upstream source was:

- mined locally
- reviewed manually
- downloaded from cloud
- or enriched by LLM

It should only care that the local helper paths contain one valid aligned publication family.

Current local materializer:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id <profile-id> \
  --pack-id <stable-pack-id> \
  --data-root <disposable-or-product-data-root>
```

`--semantic-inventory` is now an optional developer override, not the normal
product-shaped route. When it is omitted, the helper resolves the requested
`pack_id` in this order:

1. an already-installed local pack copy under
   `<data-root>/language_packs/<pair>/semantic_packs/<pack-id>/semantic_inventory.json`
2. an explicit semantic-pack catalog file from `LEXISHIFT_SEMANTIC_PACK_CATALOG`
3. the current repo dev-pack path for named development packs, including the
   current default `en-es-active-only-combined-full-v1-tranche-004`

That keeps tests and first product checks honest: the UI/backend contract is
"install this named pack into this profile/data root", while file paths remain
available for diagnostics, replay, and one-off source debugging.

The same materializer is also exposed through the native-host command
`install_semantic_pack`. Its payload uses the same fields as the CLI:

```json
{
  "type": "install_semantic_pack",
  "payload": {
    "pair": "en-es",
    "profile_id": "<profile-id>",
    "pack_id": "<stable-pack-id>",
    "data_root": "<disposable-or-product-data-root>"
  }
}
```

`semantic_inventory_path` may still be supplied in that payload as an explicit
override. It should not be required by normal product testing.

The command intentionally requires `--data-root` on the CLI or
`payload.data_root` through native host unless the corresponding
`allow_default_data_root` flag is passed. That keeps the first product checks in
a disposable root such as:

```text
docs/test_outputs/experiments/semantic_veto_source_packaging/<pack-id>-product-install-data-root
```

It writes two layers:

- pair-level pack copy:
  `<data-root>/language_packs/<pair>/semantic_packs/<pack-id>/`
- profile-local runtime publication family:
  `<data-root>/srs/profiles/<profile-id>/srs_ruleset_<pair>.json`,
  `srs_rulegen_snapshot_<pair>.json`,
  `srs_semantic_inventory_<pair>.json`, and
  `srs_publication_manifest_<pair>.json`

The command also supports `--dry-run`, which validates and reports the target
paths without writing profile artifacts.

The browser extension options page exposes the same route under Advanced debug
tools. That UI installs by semantic `pack_id`, accepts a local compiled inventory
path only as an override, and still requires either a disposable data root or an
explicit opt-in to the default helper data root. It is for product validation and
local release testing, not a final end-user pack download flow.

Use `docs/rulegen/semantic_pack_operator_smoke_runbook.md` for the current
operator-facing install and browser-smoke steps. In particular, live extension
smoke should either target the helper's default data root or run the native host
with the same `LEXISHIFT_DATA_DIR` used during installation; otherwise a
disposable materialization root will not be the root used by later page-runtime
requests.

## Recommended Identity Model

Keep these identities separate:

- `schema_version`
  - payload shape
- `selection_policy_version`
  - offline blocker-selection logic
- `decision_policy_id`
  - runtime semantic decision logic
- `fallback_policy`
  - runtime behavior when semantic readiness fails
- `generation_id`
  - one exact compiled build

The operational mistake to avoid is using one field to mean all five.

## Proposed Update Flow For The Current Local-Only Project

This is the recommended near-term process while everything is still local.

1. Add or ingest new source batches.
2. Normalize them into the canonical evidence layer.
3. Compile a new `generation_id`.
4. Run schema validation, referential-integrity checks, and benchmark/veto checks.
5. If the generation passes, materialize the publication family to helper-local files.
6. Replace the old local files atomically.
7. Keep the previous generation available as last-known-good rollback.

Even without cloud, this is worth following because it prevents:

- silent mixed-generation files
- direct edits to local runtime artifacts
- and loss of provenance once LLM data starts landing

## Proposed Update Flow If Cloud Is Added Later

If cloud-backed delivery arrives, keep the runtime contract unchanged and add only one extra distribution layer.

Recommended flow:

1. Build a new immutable `generation_id`.
2. Upload immutable artifacts under that generation id.
3. Publish or update a small channel manifest that points to the generation.
4. Helper sync reads the manifest.
5. Helper downloads the full generation and verifies hashes.
6. Helper materializes the local runtime family on existing helper paths.
7. Runtime keeps reading the same local files as today.

This avoids transport-specific runtime logic.

## Recommended Future Split To Avoid Redundancy

If cloud distribution is introduced, do not store the heaviest semantic package separately for every profile unless profile semantics truly differ.

Recommended future split:

- pair-global semantic core
  - triggers
  - senses
  - competition sets
  - phrase sets
  - heavy provenance/evidence bundles if retained at build time
- profile-local overlay
  - ruleset
  - snapshot
  - profile-specific readiness or selection toggles if they ever exist
  - future local user suppressions or deny overrides
- helper-local materialized sidecar
  - current runtime-facing semantic inventory shape

This means:

- cloud storage avoids duplicate pair data across many profiles
- helper composes what runtime already expects
- browser/runtime code does not need to change just because storage topology changed

## LLM-Specific Rules

LLM augmentation fits this lifecycle well, but only under strict rules.

### Allowed role

LLM data may help:

- propose missing shadow candidates
- propose bridge candidates
- propose anchors or cue drafts
- produce review packets or silver labels

### Forbidden role

LLM data should not:

- write runtime sidecars directly
- bypass normalization
- bypass evaluation
- silently replace reviewed source-of-truth rows

### Required metadata

Every LLM-derived row should keep:

- `source_type=llm`
- `model_id`
- `prompt_version`
- `batch_id`
- `review_state`
- `promotion_state`

This is what lets us later ask whether the gain came from:

- the model itself
- the prompt
- the downstream filter
- or manual review

## User-Feedback-Specific Rules

Future user feedback also fits this lifecycle, but under a different discipline.

### Allowed role

User feedback may help:

- identify locally unsafe rules
- prioritize families for manual review
- prioritize families for later LLM generation
- reveal recurring topic, phrase, or policy-failure clusters

### Forbidden role

Raw user feedback should not:

- directly rewrite the canonical semantic evidence layer
- directly publish new blocker sets
- or silently become a shared global truth source

### Required metadata

Every future semantic report event should keep enough context to answer:

- which exact rule fired
- which semantic family it belonged to
- which generation and policy produced it
- which report type the user chose
- and whether the resulting action was only local or later promoted

Primary planning anchors:

- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/rulegen/semantic_feedback_promotion_flow.md`

## Error-Prevention Rules

These rules matter more than convenience.

Always require:

- schema validation for published payloads
- referential integrity between `semantic_admission` ids and inventory ids
- one generation id across ruleset/snapshot/inventory
- explicit deletion of stale aligned artifacts on reset
- last-known-good rollback pointer
- source provenance on every upstream batch

Never allow:

- manual edits to published runtime files
- partial promotion of one file from a new generation
- live runtime reads from raw source batches
- LLM data without provenance or review state

## Suggested First Implementation Slices

This proposal does not require immediate cloud work.

The first useful low-risk steps are:

1. introduce `generation_id` in the offline build/publication lifecycle
2. write a small build manifest for each compiled semantic generation
3. keep current helper-local publication paths as the only runtime-facing files
4. add referential-integrity validation as a first-class publication gate
5. treat LLM augmentation as a new Layer 1 source family, not a runtime shortcut

## Practical Takeaway

The intended operating model is:

- ingest broadly
- normalize once
- compile immutably
- validate aggressively
- publish narrowly
- materialize locally

That process is already compatible with the current unreleased local-helper setup.
It also gives us a clean upgrade path if cloud-hosted semantic packages are introduced later.
