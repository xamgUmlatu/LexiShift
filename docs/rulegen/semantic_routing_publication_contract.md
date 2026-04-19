# Semantic Routing Publication Contract

Status: active mixed contract
Role: Mixed
Last updated: 2026-04-16
Last verified: 2026-04-16 code-path inspection plus targeted helper publication/diagnostics/reset tests
Purpose: define the current semantic-routing emitted-rule and helper publication contract, while keeping the remaining target shape explicit for later rollout work
Source-of-truth: mixed as-is + target contract; current implemented truth still lives in code, tests, `docs/reference/schema.md`, and `docs/developer/feature_state_matrix.md`
Planning schemas:
- `docs/test_inputs/semantic_routing/semantic_admission.schema.json`
- `docs/test_inputs/semantic_routing/semantic_inventory.schema.json`
Verification:
- `core/lexishift_core/replacement/core.py`
- `core/lexishift_core/persistence/storage.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/paths.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/helper/use_cases/reset.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/rulegen/test_semantic_publication.py`
- `docs/reference/schema.md`

## Purpose

This document answers one practical engineering question:

- once semantic-routing ids exist, how should they be emitted, published, and inspected in repo terms?

It does not re-argue the overall architecture.
That lives in:

- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`

This document narrows the problem to:

1. current `RuleMetadata` pointer shape
2. current helper publication artifacts
3. current helper diagnostics visibility
4. parity rules and remaining target behavior for all LPs

Sequencing for landing those pieces now lives in:

- `docs/rulegen/semantic_routing_implementation_roadmap.md`

## Current Verified Seam

Today:

- `RuleMetadata` has an optional `semantic_admission` field.
- ruleset persistence roundtrips both `metadata.rulegen` and `metadata.semantic_admission`.
- `HelperPaths` now exposes pair/profile-scoped paths for:
  - `srs_ruleset_<pair>.json`
  - `srs_rulegen_snapshot_<pair>.json`
  - `srs_semantic_inventory_<pair>.json`
  - `srs_publication_manifest_<pair>.json`
- helper publication always writes:
  - `srs_ruleset_<pair>.json`
  - `srs_rulegen_snapshot_<pair>.json`
- helper publication writes `srs_semantic_inventory_<pair>.json` when semantic inventory is provided, and removes a stale sidecar when it is omitted on a later publication run
- helper publication now stamps a shared `generation_id` into snapshot and semantic inventory, then writes a publication manifest for the whole artifact family
- helper publication validates the publication family before writing:
  - ready pointers require semantic inventory publication
  - ready pointers must resolve to trigger/sense/competition-set records in the sidecar
  - snapshot and semantic inventory must agree with the requested pair/profile/generation
- helper source-of-truth diagnostics inspect:
  - store
  - ruleset
  - snapshot
  - semantic inventory
  - publication manifest
- helper reset treats semantic inventory and publication manifest as part of the same pair/profile publication family and removes them alongside ruleset/snapshot cleanup

So the implementation seam is already real:

- keep the rule metadata and sidecar contract stable
- keep the publication family generation-aligned
- keep diagnostics and reset behavior aligned with that family
- fill readiness gaps LP by LP without inventing LP-specific publication shapes

## Rule-Level Admission Pointer

The current rule-level pointer lives at:

- `rule.metadata.semantic_admission`

The rule payload stays intentionally small.
It should carry only ids and readiness state, not heavy evidence.

### Current `RuleMetadata` seam

Current dataclass seam:

```python
@dataclass(frozen=True)
class RuleMetadata:
    ...
    rulegen: Optional[Mapping[str, object]] = None
    semantic_admission: Optional[Mapping[str, object]] = None
```

Current supported JSON shape example:

```json
{
  "source_phrase": "ball",
  "replacement": "pelota",
  "metadata": {
    "language_pair": "en-es",
    "confidence": 0.82,
    "word_package": {
      "version": 1,
      "language_tag": "es",
      "surface": "pelota",
      "reading": "pelota",
      "script_forms": {
        "latin": "pelota"
      },
      "source": {
        "provider": "wiktionary_es_en"
      }
    },
    "semantic_admission": {
      "schema_version": 1,
      "status": "ready",
      "trigger_id": "en-es:trigger:ball",
      "sense_id": "en-es:wiktionary:pelota:20:0",
      "competition_set_id": "en-es:ball:pelota:v1",
      "phrase_set_id": "en-es:ball:v1"
    }
  }
}
```

If the LP cannot yet emit a runtime-usable sense pointer:

```json
{
  "semantic_admission": {
    "schema_version": 1,
    "status": "unavailable",
    "reason_code": "missing_source_sense_locator"
  }
}
```

### What must not go into `semantic_admission`

Do not store these in rule metadata:

- raw dictionary record views
- full shadow lists
- full evidence text bundles
- benchmark-only annotations
- pair-specific locator internals beyond ids

Those belong in the semantic inventory sidecar.

## Current Helper Publication Contract

Helper publication now manages one pair/profile publication family with three primary artifacts plus one manifest:

1. ruleset
2. snapshot
3. semantic inventory
4. publication manifest

Current helper filenames:

- `srs_ruleset_<pair>.json`
- `srs_rulegen_snapshot_<pair>.json`
- `srs_semantic_inventory_<pair>.json`
- `srs_publication_manifest_<pair>.json`

Current locations:

- `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`
- `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
- `srs/profiles/<profile_id>/srs_semantic_inventory_<pair>.json`
- `srs/profiles/<profile_id>/srs_publication_manifest_<pair>.json`

### Current `HelperPaths` seam

Current path helpers:

```python
def semantic_inventory_path(self, pair: str, profile_id: str | None = None) -> Path:
    safe_pair = pair.replace("/", "-").replace(":", "-")
    return self.profile_srs_dir(profile_id) / f"srs_semantic_inventory_{safe_pair}.json"

def publication_manifest_path(self, pair: str, profile_id: str | None = None) -> Path:
    safe_pair = pair.replace("/", "-").replace(":", "-")
    return self.profile_srs_dir(profile_id) / f"srs_publication_manifest_{safe_pair}.json"
```

### Current `write_rulegen_outputs(...)` contract

Current signature:

```python
def write_rulegen_outputs(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str = "default",
    rules: Sequence[VocabRule],
    snapshot: Mapping[str, object],
    semantic_inventory: Mapping[str, object] | None = None,
) -> None:
    ...
```

Publication rules:

- always publish ruleset
- always publish snapshot
- always publish a publication manifest for the family
- publish semantic inventory when it is provided for the pair/profile
- if semantic inventory is omitted, remove any stale prior semantic sidecar before writing the new manifest
- snapshot and semantic inventory inherit one shared family `generated_at`
- snapshot and semantic inventory receive one shared `generation_id`
- the manifest records:
  - `generated_at`
  - `published_at`
  - `generation_id`
  - per-artifact `path`, `exists`, `sha1`, and `bytes`
  - validation state for the family
- reject invalid publication families before writing any artifact
- do not force runtime to infer semantic availability by the presence or absence of the sidecar alone

That last point matters.
The source of truth for a rule stays:

- `metadata.semantic_admission.status`

The sidecar is the resolution target for ids, not the only readiness signal.

## Current Diagnostics Contract

The shipped diagnostics seam is now split across three concrete layers:

- helper source-of-truth diagnostics from `get_srs_runtime_diagnostics(...)`
- extension-cache diagnostics from the options-page `SRS runtime diagnostics` action
- current tab/runtime last-state diagnostics persisted through `srsRuntimeLastState`

That split matters because only the helper payload is authoritative for publication-family alignment.
The cache layer is best-effort local state.
The last-reported runtime state is the live browser apply view.

Current helper semantic-inventory diagnostics:

- `semantic_inventory_path`
- `semantic_inventory_exists`
- `semantic_inventory_schema_version`
- `semantic_inventory_generation_id`
- `semantic_inventory_pointer_modes`
- `semantic_inventory_default_unavailable_reason_code`
- `semantic_inventory_error`
- `semantic_inventory_trigger_count`
- `semantic_inventory_sense_count`
- `semantic_inventory_competition_set_count`
- `semantic_inventory_phrase_set_count`
- `snapshot_generation_id`
- `ruleset_rules_with_semantic_admission`
- `ruleset_rules_semantic_ready`
- `ruleset_rules_semantic_unavailable`
- `ruleset_rules_semantic_not_applicable`

Current helper publication-manifest diagnostics:

- `publication_manifest_path`
- `publication_manifest_exists`
- `publication_manifest_generation_id`
- `publication_manifest_family_valid`
- `publication_manifest_error_count`
- `publication_manifest_errors`

Current extension-cache diagnostics:

- `cache.ruleset_exists`
- `cache.ruleset_rules_count`
- `cache.snapshot_exists`
- `cache.snapshot_target_count`
- `cache.semantic_inventory_exists`
- `cache.semantic_inventory_competition_set_count`
- `cache.semantic_inventory_phrase_set_count`

Current tab/runtime last-state diagnostics:

- `semantic_admission_enabled`
- `semantic_fallback_policy`
- `semantic_inventory_loaded`
- `semantic_inventory_source`
- `semantic_inventory_error`
- `semantic_matches_eligible`
- `semantic_matches_ready`
- `semantic_policy_replaces`
- `semantic_policy_abstains`
- `semantic_fallback_replaces`
- `semantic_fallback_abstains`

Current join-point limits:

- helper diagnostics are the only shipped surface that can verify `generation_id` alignment and manifest-family validity
- extension cache currently tracks artifact presence/counts only; it does not persist manifest validation or publication generation ids
- current tab/runtime last state keeps aggregate semantic counters, not the full per-decision record stream

This gives the repo a current sanity loop:

- do rules carry the pointer?
- does the sidecar exist?
- is the snapshot/sidecar generation-aligned?
- does the manifest think the family is coherent?

## Current Reset / Lifecycle Rules

When helper resets pair/profile artifacts, it now treats semantic inventory and publication manifest as part of the same publication family.

Current reset behavior:

- deleting `srs_ruleset_<pair>.json` should also delete `srs_semantic_inventory_<pair>.json`
- deleting a pair/profile publication family also deletes `srs_publication_manifest_<pair>.json`
- all-pairs reset removes every `srs_semantic_inventory_*.json` and `srs_publication_manifest_*.json` under the profile SRS directory
- semantic inventory and manifest should be regenerated whenever ruleset/snapshot are regenerated for the same pair/profile

The intent is simple:

- ruleset, snapshot, semantic inventory, and manifest should stay generation-aligned

## Cross-LP Parity Rules

### Rule 1. One published shape for all LPs

Every LP should aim at the same emitted rule shape:

- `metadata.semantic_admission`

Even if the payload is only:

```json
{
  "schema_version": 1,
  "status": "unavailable",
  "reason_code": "missing_source_sense_locator"
}
```

### Rule 2. One sidecar shape for all LPs

Every LP should aim at the same sidecar top-level structure:

- `triggers`
- `senses`
- `competition_sets`
- `phrase_sets`

LP-specific locator details stay nested in:

- `senses.<sense_id>.locator`

### Rule 3. Capability differences should show up as status, not schema drift

Good:

- `en-es` emits a `sense_provenance`-backed pointer
- `en-es` can publish a limited `emitted_rule_siblings` competition set when real sibling senses are present in the same emitted batch
- `de-en` emits a `translation_gloss`-backed pointer (currently FreeDict-backed)
- `en-ja` emits a `jmdict_entry`-backed pointer

Bad:

- `en-es` uses `semantic_admission`
- `en-ja` invents a different top-level field

## Rollout Sequence

The lowest-risk order remains:

1. planning docs and schemas
2. `semantic_admission` in `RuleMetadata`
3. storage roundtrip support for `metadata.semantic_admission`
4. `HelperPaths.semantic_inventory_path(...)`
5. helper publication for the sidecar
6. helper publication diagnostics plus joined options/runtime visibility for pointer + sidecar coverage
7. generation-aligned publication manifest plus reset cleanup
8. narrow `status=ready` rollout for the strongest LPs only

Current checkpoint:

- steps `1` through `7` are now landed
- step `8` is landed only as a narrow `en-es` emitted-sibling publication PoC, not as broad shadow-mined runtime readiness

## Current Acceptance Bar

The current implementation now satisfies the first publication-contract bar:

- emitted rules roundtrip `metadata.semantic_admission` losslessly
- helper publication can write and overwrite the semantic inventory sidecar
- helper publication rejects invalid ready-pointer families before writing
- helper publication now stamps a shared `generation_id` across snapshot, semantic inventory, and manifest
- reset/delete lifecycle removes stale sidecars and publication manifests
- helper source-of-truth diagnostics can see pointer coverage, sidecar presence, publication generation ids, and manifest family state
- joined options/runtime diagnostics can also surface extension-cache presence plus live semantic gate source/error and aggregate decision counts
- LPs without full support can still emit the shared pointer shape with `status=unavailable`

What this does not yet prove:

- broad publishable shadow-mined competition sets
- phrase-preemption publication
- production-ready semantic scoring defaults
