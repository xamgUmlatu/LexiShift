# Semantic Routing Data Contract

Status: active mixed contract
Role: Mixed
Last updated: 2026-04-21
Last verified: 2026-04-21 semantic schema-reference reconciliation against the shipped publication/runtime seam plus stable schema/test references
Purpose: describe the current semantic-routing data layers and the remaining target contract so LP support stays symmetric without confusing shipped pointer seams for full runtime-readiness
Source-of-truth: mixed as-is + target contract; current implemented truth still lives in code, tests, `docs/reference/schema.md`, and `docs/developer/feature_state_matrix.md`
Current schema references:
- `docs/test_inputs/semantic_routing/semantic_admission.schema.json`
- `docs/test_inputs/semantic_routing/semantic_inventory.schema.json`
- `docs/test_inputs/semantic_routing/semantic_admit_batch_request.schema.json`
- `docs/test_inputs/semantic_routing/semantic_admit_batch_response.schema.json`
Remaining planning schemas:
- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`
Related docs:
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
Verification:
- `core/lexishift_core/persistence/storage.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/rulegen/semantic_publication.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
- `core/lexishift_core/helper/use_cases/semantic_admission.py`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
- `core/tests/rulegen/test_rulegen_adapters.py`
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
- `docs/reference/schema.md`

## Goal

Semantic routing will only be stable if the repo communicates the right data in the right layer.

The design target is:

- keep the runtime-facing schema symmetric across LPs,
- avoid pair-specific one-off payloads,
- avoid shoving heavy benchmark/debug provenance into every emitted rule,
- and make the future runtime admission layer possible without re-deriving core sense identity from scratch on every page apply.

## How To Read This Doc

- Treat `Current End-To-End Data Flow`, `Current Data Layers`, and `Current LP Pointer Strength` as the current data contract.
- Treat `Recommended Future Contract` as the target shape that later work should continue converging toward.
- Treat rollout sequencing as owned by `docs/rulegen/semantic_routing_implementation_roadmap.md` and first-launch operation as owned by `docs/rulegen/semantic_routing_en_es_publish_checklist.md`.
- Treat this doc as a data-layer map, not as proof that semantic runtime readiness is solved.

## Current End-To-End Data Flow

Today the main flow is:

1. SRS store selects target lemmas.
2. Rulegen pair adapters build `RuleCandidate` objects.
3. Pair adapters may attach rich candidate metadata.
4. Pair publication helpers annotate results with `metadata.semantic_admission` when semantic-routing publication is enabled.
5. Helper publication writes ruleset JSON, snapshot JSON, and an optional semantic inventory sidecar.
6. Extension loads rules, gates by SRS, builds trie, and applies replacements.
7. Runtime semantic admission, when enabled, resolves inventory and decision records from helper/helper-cache without expanding the ruleset into full provenance payloads.
8. DOM spans keep a compact dataset payload for UI and feedback.

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
- optional `semantic_admission`

It does not currently preserve rich candidate provenance such as:
- `sense_provenance`
- `target_provenance`
- `gloss_provenance`
- raw dictionary record views

What is true today is narrower but real:

- emitted rules can now carry a stable active pointer through `metadata.semantic_admission`
- that pointer is LP-symmetric at the top level (`schema_version`, `status`, `trigger_id`, `sense_id`, `competition_set_id`, optional `phrase_set_id`)
- pointer strength still differs by pair, and most LPs still emit `status=unavailable`

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

## Current LP Pointer Strength

Current emitted-rule pointer strength by active rulegen LP:

| LP / pair | Current emitted pointer strength | Current competition publication state |
|---|---|---|
| `en-es` | strongest current active pointer; uses `sense_provenance` first with `translation_gloss` fallback | narrow batch-local `status=ready` PoC for emitted siblings in the same batch; not broad shadow-mined blocker publication or LP-parity readiness |
| `en-de` | same general pointer strategy as `en-es`: `sense_provenance` first with `translation_gloss` fallback | currently stays `status=unavailable` because shadow promotion is not solved |
| `en-ja` | stable `jmdict_entry`-backed active pointer derived from target forms | currently stays `status=unavailable` |
| `de-en` | stable `translation_gloss`-backed active pointer from deterministic gloss order (currently FreeDict-backed) | currently stays `status=unavailable` |
| `es-en` | stable `translation_gloss`-backed active pointer from deterministic gloss order (currently FreeDict-backed) | currently stays `status=unavailable` |

So the current answer to "does runtime get no semantic identity at all?" is now:

- no

The current answer to "does runtime get a fully ready competition/shadow contract by default?" is still:

- also no

## Critical Current Gap

The repo no longer drops semantic identity completely between candidate generation and emitted runtime rules.

What it still does not carry by default is the full runtime-ready competition contract.

That means:

- some LPs can reason about rich sense identity during benchmark/ranking,
- all current rulegen LPs can now emit a shared active-pointer block in `metadata.semantic_admission`,
- helper publication can now emit a semantic inventory sidecar that resolves those ids,
- but runtime still does not receive a fully ready competition/shadow contract by default.

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

The sections below are still the shared target shape for LP-symmetric semantic routing, but they are no longer purely aspirational.
Layer A pointer fields, Layer B semantic inventory sidecars, and the Layer C helper/runtime batch seam are now all implemented in the shipped helper/browser-extension path.
What remains future-facing is rollout breadth, LP parity, and broader runtime readiness, not invention of a separate payload shape.

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
  "reason_code": "missing_source_sense_locator"
}
```

This is the most important parity rule:

- every LP should emit the same top-level semantic-admission shape,
- even if some LPs only emit `status=unavailable` at first.

That avoids a short-term architecture where `en-es` gets a bespoke runtime contract and other LPs lag behind structurally.

### Layer B. Semantic Inventory Sidecar

Heavy semantic data now lives outside the ruleset in a published sidecar, and later work should keep converging on that shape instead of pushing more provenance into the ruleset itself.

Current artifact:
- per pair/profile semantic inventory JSON written alongside ruleset + snapshot
- current helper path: `srs/profiles/<profile_id>/srs_semantic_inventory_<pair>.json`

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
  "capability": {
    "pointer_modes": [
      "sense_provenance",
      "translation_gloss"
    ],
    "default_unavailable_reason_code": "missing_source_sense_locator",
    "competition_mode": "emitted_rule_siblings",
    "competition_reason_code": "missing_shadow_selection",
    "phrase_mode": "not_published",
    "phrase_reason_code": "missing_phrase_inventory"
  },
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
  "capability": {
    "pointer_modes": [
      "sense_provenance",
      "translation_gloss"
    ],
    "default_unavailable_reason_code": "missing_source_sense_locator",
    "competition_mode": "emitted_rule_siblings",
    "competition_reason_code": "missing_shadow_selection",
    "phrase_mode": "not_published",
    "phrase_reason_code": "missing_phrase_inventory"
  },
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
      "selection_mode": "automatic",
      "selection_policy_version": "en_es_emitted_rule_siblings_v1"
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

- `capability`
  - which locator modes this pair can currently emit
  - which unavailable reason should be expected when locator derivation fails
  - whether competition publication is still absent or using a limited PoC mode
  - whether phrase publication is still intentionally absent

- `phrase_sets`
  - phrase/idiom blockers that should preempt semantic scoring

### Layer C. Runtime Admission Request / Response

Runtime should not discover semantic competitors on its own.
It should send a compact, concrete request to the helper-side decision engine.
The browser extension semantic-admission path now uses this helper/runtime seam directly, while still batching only `status=ready` eligible matches and resolving non-ready eligible rows locally through fallback.

Current request responsibilities:

- identify pair and profile
- identify offset semantics explicitly
- state the configured `fallback_policy`
- optionally request a specific `decision_policy_id`
- send the matched source phrase and local context text
- send the already-emitted `semantic_admission` pointer from the matched rule

Current schema reference:

- `docs/test_inputs/semantic_routing/semantic_admit_batch_request.schema.json`

Current request fragment:

```json
{
  "schema_version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "offset_encoding": "utf16_code_unit",
  "decision_policy_id": "en_es_sentence_veto_v1",
  "fallback_policy": "abstain_on_unavailable",
  "surface_kind": "browser_page",
  "matches": [
    {
      "match_id": "node17:ball:0",
      "source_phrase": "ball",
      "context_text": "The child kicked the ball into the street.",
      "match_start": 17,
      "match_end": 21,
      "semantic_admission": {
        "schema_version": 1,
        "status": "ready",
        "trigger_id": "en-es:trigger:ball",
        "sense_id": "en-es:wiktionary:pelota:20:0",
        "competition_set_id": "en-es:ball:pelota:v1",
        "phrase_set_id": "en-es:ball:v1"
      }
    }
  ]
}
```

Current response responsibilities:

- return the resolved `decision_policy_id`
- echo the active `fallback_policy`
- return the final user-facing outcome for each match:
  - `replace`
  - `soft_affordance`
  - `abstain`
- state whether that outcome came from:
  - the semantic decision policy
  - or the configured fallback policy
- expose compact diagnostics such as:
  - `selection_policy_version`
  - selected `context_view_id`
  - `active_score`
  - `top_shadow_score`
  - `score_margin`
  - `reason_codes`

Current schema reference:

- `docs/test_inputs/semantic_routing/semantic_admit_batch_response.schema.json`

Current response fragment:

```json
{
  "schema_version": 1,
  "pair": "en-es",
  "profile_id": "default",
  "decision_policy_id": "en_es_sentence_veto_v1",
  "fallback_policy": "abstain_on_unavailable",
  "decisions": [
    {
      "match_id": "node17:ball:0",
      "decision": "replace",
      "decision_source": "policy",
      "reason_codes": [
        "active_margin_clear"
      ],
      "trigger_id": "en-es:trigger:ball",
      "sense_id": "en-es:wiktionary:pelota:20:0",
      "competition_set_id": "en-es:ball:pelota:v1",
      "phrase_set_id": "en-es:ball:v1",
      "selection_policy_version": "en_es_shadow_selection_v1",
      "context_view_id": "masked_sentence",
      "active_score": 0.63,
      "top_shadow_score": 0.31,
      "score_margin": 0.32
    }
  ]
}
```

This version split is intentional:

- `schema_version` governs payload shape
- `selection_policy_version` governs offline blocker publication
- `decision_policy_id` governs runtime semantic scoring
- `fallback_policy` governs what happens when semantic readiness is missing or unusable

The offset rule is also intentional:

- request offsets are currently frozen as `utf16_code_unit`
- that matches the browser/plugin runtime surfaces that produce the request
- helper-side implementations must therefore treat offsets as transport values, not assume Python code-point indexing by default

### Layer D. Runtime Decision Record

The response itself is the canonical structured decision record.
Runtime may derive a smaller local diagnostics record from it, but should not invent a separate semantic truth surface.

Recommended location:

- helper debug channel
- runtime diagnostics
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
  - already have candidate-side source-sense provenance worth serializing

- `tier_b`: `en-ja`
  - can now emit stable `jmdict_entry` locators, but still lacks source-sense provenance and shadow publication

- `tier_c`: `de-en`, `es-en`
  - can now emit stable `translation_gloss` locators, but still rely on deterministic gloss slots rather than richer source-sense provenance

## First Concrete Steps

1. Extend the planning schema with `metadata.semantic_admission` as a future rule field.
2. Define `sense_id`, `trigger_id`, and `competition_set_id` string conventions.
3. Define a semantic inventory sidecar schema.
4. Audit `en-es` and `en-de` candidate provenance into that sidecar shape.
5. Keep weaker LPs on the same contract while making their locator tiers explicit in the sidecar capability summary.
6. Only after that, decide which LPs can emit `status=ready`.
