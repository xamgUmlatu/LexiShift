# Semantic Routing Publication Contract

Status: planning slice
Role: Planning / WIP
Last updated: 2026-04-10
Last verified: 2026-04-10 code-path inspection across `RuleMetadata`, storage roundtrip, helper output publication, helper paths, and runtime diagnostics
Purpose: define the future emitted-rule shape and helper publication contract for semantic routing so implementation work lands on a shared LP-symmetric path
Source-of-truth: planning doc only; current implemented truth still lives in code, `docs/reference/schema.md`, and `docs/developer/feature_state_matrix.md`
Planning schemas:
- `docs/test_inputs/semantic_routing/semantic_admission.schema.json`
- `docs/test_inputs/semantic_routing/semantic_inventory.schema.json`
Verification:
- `core/lexishift_core/replacement/core.py`
- `core/lexishift_core/persistence/storage.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/paths.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `docs/reference/schema.md`

## Purpose

This document answers one practical engineering question:

- once semantic-routing ids exist, how should they be emitted, published, and inspected in repo terms?

It does not re-argue the overall architecture.
That lives in:

- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`

This document narrows the problem to:

1. future `RuleMetadata` shape
2. helper publication artifacts
3. helper diagnostics visibility
4. parity rules for all LPs

## Current Verified Seam

Today:

- `RuleMetadata` has an optional `semantic_admission` field.
- ruleset persistence roundtrips both `metadata.rulegen` and `metadata.semantic_admission`.
- helper publication writes:
  - `srs_ruleset_<pair>.json`
  - `srs_rulegen_snapshot_<pair>.json`
- helper publication can also write:
  - `srs_semantic_inventory_<pair>.json`
- helper runtime diagnostics inspects:
  - store
  - ruleset
  - snapshot
  - semantic inventory

So the implementation seam is real and small:

- keep the rule metadata/sidecar contract stable
- expand the default producers
- and start filling readiness gaps LP by LP

## Future Emitted Rule Shape

The future rule-level pointer should live at:

- `rule.metadata.semantic_admission`

The rule payload stays intentionally small.
It should carry only ids and readiness state, not heavy evidence.

### Planned `RuleMetadata` extension

Future dataclass intent:

```python
@dataclass(frozen=True)
class RuleMetadata:
    ...
    rulegen: Optional[Mapping[str, object]] = None
    semantic_admission: Optional[Mapping[str, object]] = None
```

Future JSON example:

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

## Future Helper Publication Contract

Helper publication should eventually manage three paired artifacts per `pair/profile_id`:

1. ruleset
2. snapshot
3. semantic inventory

Recommended helper filenames:

- `srs_ruleset_<pair>.json`
- `srs_rulegen_snapshot_<pair>.json`
- `srs_semantic_inventory_<pair>.json`

Recommended locations:

- `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`
- `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
- `srs/profiles/<profile_id>/srs_semantic_inventory_<pair>.json`

### Future `HelperPaths` addition

Recommended future path helper:

```python
def semantic_inventory_path(self, pair: str, profile_id: str | None = None) -> Path:
    safe_pair = pair.replace("/", "-").replace(":", "-")
    return self.profile_srs_dir(profile_id) / f"srs_semantic_inventory_{safe_pair}.json"
```

### Future `write_rulegen_outputs(...)` contract

Recommended future signature:

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
- publish semantic inventory when semantic-routing publication is enabled for the pair/profile
- if semantic-routing publication is enabled, prefer writing a real sidecar even when many records are `status=unavailable`
- do not force runtime to infer semantic availability by the presence or absence of the sidecar alone

That last point matters.
The source of truth for a rule stays:

- `metadata.semantic_admission.status`

The sidecar is the resolution target for ids, not the only readiness signal.

## Future Diagnostics Contract

Helper/runtime diagnostics should learn the third artifact explicitly.

Recommended additions to `get_srs_runtime_diagnostics(...)`:

- `semantic_inventory_path`
- `semantic_inventory_exists`
- `semantic_inventory_schema_version`
- `semantic_inventory_pointer_modes`
- `semantic_inventory_default_unavailable_reason_code`
- `semantic_inventory_error`
- `semantic_inventory_trigger_count`
- `semantic_inventory_sense_count`
- `semantic_inventory_competition_set_count`
- `semantic_inventory_phrase_set_count`
- `ruleset_rules_with_semantic_admission`
- `ruleset_rules_semantic_ready`
- `ruleset_rules_semantic_unavailable`
- `ruleset_rules_semantic_not_applicable`

This gives the repo an immediate sanity loop:

- do rules carry the pointer?
- does the sidecar exist?
- do the ids resolve to a coherent inventory?

## Future Reset / Lifecycle Rules

When helper resets pair/profile artifacts, it should treat semantic inventory as part of the same publication family.

Recommended future reset behavior:

- deleting `srs_ruleset_<pair>.json` should also delete `srs_semantic_inventory_<pair>.json`
- deleting `srs_rulegen_snapshot_<pair>.json` should not be the only semantic-routing cleanup path
- semantic inventory should be regenerated whenever ruleset/snapshot are regenerated for the same pair/profile

The intent is simple:

- ruleset, snapshot, and semantic inventory should stay generation-aligned

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
- `de-en` emits a `freedict_gloss`-backed pointer
- `en-ja` emits a `jmdict_entry`-backed pointer

Bad:

- `en-es` uses `semantic_admission`
- `en-ja` invents a different top-level field

## Rollout Sequence

The lowest-risk engineering order is:

1. add planning docs and schemas
2. add `semantic_admission` to `RuleMetadata`
3. add storage roundtrip support for `metadata.semantic_admission`
4. add `HelperPaths.semantic_inventory_path(...)`
5. teach helper publication to write the sidecar
6. teach runtime diagnostics to report pointer + sidecar coverage
7. only then start emitting `status=ready` for the strongest LPs
8. keep any first `status=ready` rollout narrow and explicit about its shadow-selection mode

## Minimum Acceptance Bar For First Implementation

The first implementation pass should be considered correct only if:

- emitted rules roundtrip `metadata.semantic_admission` losslessly
- helper publication can write and overwrite the semantic inventory sidecar
- reset/delete lifecycle removes stale sidecars
- runtime diagnostics can see both the pointer coverage and sidecar presence
- LPs without full support still emit the shared pointer shape with `status=unavailable`

That gives us a real end-to-end contract without prematurely claiming semantic scoring is production-ready.
