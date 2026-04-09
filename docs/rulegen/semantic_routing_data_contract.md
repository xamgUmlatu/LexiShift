# Semantic Routing Data Contract

Status: planning slice
Role: Planning / WIP
Last updated: 2026-04-10
Last verified: 2026-04-10 code-path inspection across rulegen emission, helper publication, ruleset serialization, and extension runtime consumption
Purpose: define the best long-term data-flow shape for semantic routing so LP support stays symmetric and runtime integration does not depend on benchmark-only candidate metadata
Source-of-truth: planning doc only; current implemented truth still lives in code, `docs/reference/schema.md`, and `docs/developer/feature_state_matrix.md`
Planning schemas:
- `docs/test_inputs/semantic_routing/semantic_admission.schema.json`
- `docs/test_inputs/semantic_routing/semantic_inventory.schema.json`
Related planning doc:
- `docs/rulegen/semantic_routing_publication_contract.md`
Verification:
- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/persistence/storage.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
- `docs/reference/schema.md`

## Goal

Semantic routing will only be stable if the repo communicates the right data in the right layer.

The design target is:

- keep the runtime-facing schema symmetric across LPs,
- avoid pair-specific one-off payloads,
- avoid shoving heavy benchmark/debug provenance into every emitted rule,
- and make the future runtime admission layer possible without re-deriving core sense identity from scratch on every page apply.

## Current End-To-End Data Flow

Today the main flow is:

1. SRS store selects target lemmas.
2. Rulegen pair adapters build `RuleCandidate` objects.
3. Pair adapters may attach rich candidate metadata.
4. `materialize_vocab_rule(...)` converts each candidate into `VocabRule`.
5. Ruleset JSON is written by helper publication.
6. Extension loads rules, gates by SRS, builds trie, and applies replacements.
7. DOM spans keep a compact dataset payload for UI and feedback.

## Current Data Layers

### 1. Candidate metadata during rulegen

This is the richest layer.

Examples:
- `en-es` and `en-de` can attach:
  - `dictionary_record`
  - `dictionary_record_views`
  - `gloss_provenance`
  - `sense_provenance`
  - `target_provenance`
  - shadow-risk metadata
- `en-ja`, `de-en`, and `es-en` currently carry much less:
  - gloss order
  - reverse-check fields
  - POS
  - script/word-package metadata where applicable

Important: this is benchmark/ranking-time data, not automatically runtime-visible data.

### 2. Emitted ruleset metadata

This is the runtime contract today.

Persisted rule metadata currently includes:
- `language_pair`
- `confidence`
- `word_package`
- `script_forms`
- `morphology`
- `pos`
- narrow `rulegen` ids only

It does not currently preserve rich candidate provenance such as:
- `sense_provenance`
- `target_provenance`
- `gloss_provenance`
- raw dictionary record views

### 3. Snapshot output

The helper snapshot is a compact lemma -> source preview.

It is good for:
- summary UI
- quick diagnostics

It is not a semantic-routing inventory.

### 4. Extension runtime payload

The extension mainly consumes:
- rules
- `metadata.language_pair`
- `metadata.word_package`
- `metadata.script_forms`
- `metadata.morphology`
- `metadata.description`

Span datasets currently carry compact UI fields such as:
- original text
- replacement
- display replacement
- language pair
- source
- word package
- origin

This is intentionally compact and should stay compact.

## Critical Current Gap

The repo currently loses semantic identity between:

- candidate generation
- and emitted runtime rules

That means:
- some LPs can reason about sense identity during benchmark/ranking,
- and the repo now has a shared emitted-rule pointer shape,
- but runtime still does not receive a fully ready competition/shadow contract.

This is why semantic routing is still only partially implemented as a runtime publication seam rather than a real admission layer.

## Design Principle

Do not make the runtime ruleset carry every debug field.

Instead, split the future semantic-routing contract into three layers:

1. `rule-level admission pointer`
2. `semantic inventory sidecar`
3. `runtime decision record`

That gives us:
- small rulesets,
- rich offline provenance where needed,
- LP symmetry,
- and good runtime observability.

## Recommended Future Contract

### Layer A. Rule-Level Admission Pointer

Each emitted rule should optionally carry a small LP-agnostic semantic-routing block.

Recommended location:
- `rule.metadata.semantic_admission`

This should be small and runtime-safe.

Recommended shape:

```json
{
  "schema_version": 1,
  "status": "ready",
  "trigger_id": "en-es:trigger:ball",
  "sense_id": "en-es:wiktionary_es_en:pelota:sense:20:0",
  "competition_set_id": "en-es:ball:pelota:v1",
  "phrase_set_id": "en-es:ball:v1"
}
```

If the LP cannot populate it yet:

```json
{
  "schema_version": 1,
  "status": "unavailable",
  "reason_code": "missing_sense_locator"
}
```

This is the most important parity rule:

- every LP should emit the same top-level semantic-admission shape,
- even if some LPs only emit `status=unavailable` at first.

That avoids a short-term architecture where `en-es` gets a bespoke runtime contract and other LPs lag behind structurally.

### Layer B. Semantic Inventory Sidecar

Heavy semantic data should live outside the ruleset in a new published sidecar.

Recommended artifact:
- per pair/profile semantic inventory JSON written alongside ruleset + snapshot
- future helper-path naming target: `srs/profiles/<profile_id>/srs_semantic_inventory_<pair>.json`

Recommended responsibilities:
- define triggers
- define sense records
- define competition sets
- define phrase-hazard sets
- keep rich provenance/evidence views available for backend scoring and diagnostics

Recommended top-level shape:

```json
{
  "schema_version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "generated_at": "2026-04-10T12:00:00Z",
  "triggers": {},
  "senses": {},
  "competition_sets": {},
  "phrase_sets": {}
}
```

Recommended helper/runtime linkage:
- ruleset stays the hot path artifact at `srs_ruleset_<pair>.json`
- snapshot stays the compact preview artifact at `srs_rulegen_snapshot_<pair>.json`
- semantic inventory becomes the heavy semantic sidecar at `srs_semantic_inventory_<pair>.json`
- `rule.metadata.semantic_admission` only stores ids that resolve inside the sidecar for the same `pair/profile_id`

Example sidecar fragment:

```json
{
  "schema_version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "generated_at": "2026-04-10T12:00:00Z",
  "triggers": {
    "en-es:trigger:ball": {
      "trigger_id": "en-es:trigger:ball",
      "source_phrase": "ball",
      "normalized_source_phrase": "ball",
      "token_count": 1
    }
  },
  "senses": {
    "en-es:wiktionary:pelota:20:0": {
      "sense_id": "en-es:wiktionary:pelota:20:0",
      "trigger_id": "en-es:trigger:ball",
      "status": "ready",
      "target_lemma": "pelota",
      "sense_label": "object, generally spherical, used for playing games",
      "canonical_pos": "noun",
      "provider": "wiktionary_es_en",
      "locator": {
        "provider": "wiktionary_es_en",
        "locator_kind": "wiktionary_ordinal",
        "entry_ord": 20,
        "sense_ord": 0
      },
      "evidence_views": {
        "all_evidence_text": "object, generally spherical, used for playing games | (a round or ellipsoidal object)"
      }
    }
  },
  "competition_sets": {
    "en-es:ball:pelota:v1": {
      "competition_set_id": "en-es:ball:pelota:v1",
      "trigger_id": "en-es:trigger:ball",
      "status": "ready",
      "active_sense_id": "en-es:wiktionary:pelota:20:0",
      "shadow_sense_ids": [
        "en-es:wiktionary:baile:11:0",
        "en-es:wiktionary:bola_mala:2:0"
      ],
      "selection_mode": "mixed",
      "selection_policy_version": "v1"
    }
  },
  "phrase_sets": {}
}
```

Recommended record responsibilities:

- `triggers`
  - normalized source trigger family
  - token count
  - canonical source text

- `senses`
  - stable `sense_id`
  - LP/provider
  - target lemma
  - POS
  - short debug label
  - structured locator
  - source-derived evidence views

- `competition_sets`
  - which trigger is being judged
  - active sense
  - promoted shadows
  - shadow-selection policy version

- `phrase_sets`
  - phrase/idiom blockers that should preempt semantic scoring

### Layer C. Runtime Decision Record

Runtime should not write giant payloads into DOM spans.
It should instead emit a compact structured decision record for diagnostics/logging.

Recommended content:
- `trigger_id`
- `sense_id`
- `competition_set_id`
- selected context view id
- policy id
- active score
- top shadow score
- final outcome:
  - `replace`
  - `soft`
  - `abstain`
- reason codes

Recommended location:
- runtime diagnostics / helper debug channel
- not as full DOM dataset payload

The DOM span itself should stay lightweight.

## Why This Split Is Better

### Why not put everything in the ruleset?

Because:
- rulesets are hot runtime data,
- heavy provenance is repetitive,
- raw record views would bloat size,
- and pair-local debug fields do not belong in the permanent hot path.

### Why not only keep a sidecar and no rule pointer?

Because runtime needs a fast way to know:
- whether a rule is semantic-routing-ready,
- which sense it claims,
- and which competition set to consult.

Without a per-rule pointer, runtime would have to rediscover identity from replacement text and source phrase, which is brittle.

### Why not put semantic-routing data on DOM spans?

Because spans are a UI/result surface, not the canonical source of truth.

Spans should only carry:
- UI display data,
- feedback identity data,
- and maybe a compact decision id or outcome label later.

They should not become the main transport layer for heavy semantic evidence.

## Recommended Cross-LP Symmetry Rules

### Rule 1. Shared top-level contract

Every LP should use the same top-level field names:
- `semantic_admission`
- `status`
- `sense_id`
- `competition_set_id`
- `phrase_set_id`

### Rule 2. Pair-local locator stays nested

If LPs need different locator details, keep them inside sidecar sense records.

Example:
- `en-es` may use `entry_ord/sense_ord/gloss_ord`
- `en-ja` may use JMDict entry/sense references
- another LP may use a hashed dictionary key

That asymmetry is acceptable inside the nested `locator`.
It should not leak into the shared rule-level contract.

### Rule 3. Status parity beats capability parity

Not every LP needs full semantic-routing support immediately.
But every LP should have the same contract shape.

So parity should mean:
- same fields,
- same meanings,
- same failure modes,

not:
- every LP already populates every field.

### Rule 4. Heavy evidence belongs in inventory, not rule metadata

This keeps:
- ruleset payloads lean,
- runtime loading simple,
- and debug richness available without shipping it everywhere.

## What We Should Not Do

Avoid these short-term shapes:

- add `en-es`-only top-level runtime fields like `sense_provenance` directly to rule metadata while other LPs have nothing comparable
- make runtime reconstruct active sense solely from `replacement + source_phrase`
- store the entire shadow/evidence bundle in every rule row
- put benchmark-only provenance objects directly into DOM span datasets
- make phrase preemption and semantic competition share one untyped blob

## Immediate Engineering Direction

The next engineering-safe direction is:

1. add a planning-level schema for `metadata.semantic_admission`
2. define a new semantic inventory sidecar artifact
3. map current LPs into capability tiers
4. preserve a stable rule-level pointer even when the LP can only emit `status=unavailable`

Recommended LP capability tiers for this work:

- `tier_a`: `en-es`, `en-de`
  - already have candidate-side provenance worth serializing

- `tier_b`: `en-ja`
  - likely needs explicit JMDict sense locator support before it can emit `ready`

- `tier_c`: `de-en`, `es-en`
  - can likely emit the shared contract early, but initially with weaker or unavailable sense identity

## First Concrete Steps

1. Extend the planning schema with `metadata.semantic_admission` as a future rule field.
2. Define `sense_id`, `trigger_id`, and `competition_set_id` string conventions.
3. Define a semantic inventory sidecar schema.
4. Audit `en-es` and `en-de` candidate provenance into that sidecar shape.
5. Define what `en-ja`, `de-en`, and `es-en` need to emit at least `status=unavailable` symmetrically.
6. Only after that, decide which LPs can emit `status=ready`.
