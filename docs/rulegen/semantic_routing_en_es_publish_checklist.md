# en-es Semantic Routing Publish Checklist

Status: active launch checklist
Role: Runbook / operational
Last updated: 2026-04-22
Last verified: 2026-04-22 capability-driven semantic-runtime contract sweep against helper diagnostics, extension runtime, options status UX, and current launch posture docs
Purpose: define the exact checklist for a controlled `en-es` browser-extension launch of semantic runtime veto without hard-coding the architecture to `en-es`
Source-of-truth: this checklist is the launch runbook; code truth still lives in runtime/helper code, `docs/developer/feature_state_matrix.md`, and generated test artifacts
Related docs:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`

## Scope

This checklist is for the first controlled `en-es` launch shape only:

- surface: browser extension
- rule origin: SRS-origin rules only
- semantic gate state: automatic when the selected pair/profile publication has active ready coverage
- artifact transport: local helper files plus extension cache fallback
- published `status=ready` rows: only the current helper-side `emitted_rule_siblings` PoC when real sibling senses are available in the active emitted ruleset or the broader initialize/refresh semantic-context pool
- runtime action: `replace` or keep original text

Not in scope for this checklist:

- cloud-hosted semantic artifacts
- BetterDiscord/chat runtime integration
- forcing semantic admission on profiles that still publish zero ready coverage
- multi-LP rollout policy
- broad shadow-mined blocker publication
- phrase-set publication
- `soft_affordance` rendering

## Current E2E Shape

When semantic admission is active today, the runtime path is:

1. helper publication writes SRS rules plus semantic inventory sidecar for a pair/profile
2. current `en-es` `status=ready` coverage comes from emitted-sibling competition sets built from the active emitted rules plus the broader helper-side initialize/refresh semantic-context pool
3. extension loads rules and semantic inventory from helper, with extension cache as fallback
4. extension finds normal trie matches first
5. only SRS matches that already carry `rule.metadata.semantic_admission` are semantically eligible
6. only `status=ready` matches are batched to helper `semantic_admit_batch`
7. non-ready matches stay on the configured fallback-policy path instead of calling helper semantic scoring
8. helper decision policy returns `replace`, `abstain`, or the reserved `soft_affordance`
9. extension renders only `replace`; all other outcomes keep the original source text

This checklist therefore validates a real helper/runtime gate on a narrow published ready subset.
It does not claim that broad shadow-mined blocker discovery is solved.

## Recommended Pilot Posture

Use this posture for the first real `en-es` pilot:

- `srsEnabled=true`
- semantic admission status resolves to `Automatic`

Reasoning:

- normal users no longer manage a semantic-admission toggle or fallback selector
- the runtime should enable helper-side semantic veto automatically only when the selected pair/profile publication has real ready coverage
- profiles without ready coverage should stay on standard SRS replacement behavior instead of exposing rollout controls in options

## Preconditions

Before enabling the pilot for any profile:

- the helper can publish an `en-es` ruleset containing nonzero `metadata.semantic_admission` coverage
- the helper can publish an `en-es` semantic inventory sidecar for the same profile
- the helper can publish a nonzero emitted-sibling `status=ready` subset for the pilot profile from the active rules plus the broader initialize/refresh semantic-context pool, or the launch owner explicitly accepts that the pilot is only exercising fallback behavior
- the extension can reach the helper/native-host on the target machine
- the active policy id and sidecar schema version are frozen for the pilot batch

## Release Validation

Run these checks before calling the path publishable:

```bash
python3 -m pytest \
  core/tests/rulegen/test_semantic_publication.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py \
  core/tests/helper/test_rulegen_outputs.py \
  core/tests/architecture/test_extension_structure.py \
  core/tests/dev/test_helper_translation_dict_entrypoints.py -q

python3 scripts/testing/semantic_shadow_experiment_matrix_en_es.py
python3 scripts/testing/semantic_shadow_experiment_compare_en_es.py
python3 scripts/dev/check_doc_references.py
```

If the extension options/runtime code changed, also syntax-check the touched files:

```bash
node --check apps/chrome-extension/options/core/ui_manager.js
node --check apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js
node --check apps/chrome-extension/content/runtime/settings_change_router.js
```

## Per-Profile Enable Checklist

For each pilot profile:

1. Open extension options and select the correct SRS profile.
2. Set source/target languages to `en` -> `es`.
3. Enable `SRS practice mode`.
4. Refresh or initialize the pair so helper artifacts are current.
5. Confirm the semantic-admission status row reads `Automatic`.
6. Run `SRS runtime diagnostics`.

The runtime diagnostics should show all of the following:

- `semantic_admission_enabled: true`
- `semantic_runtime_capability: active`
- `semantic_ready_rule_count: > 0`
- `semantic_inventory_loaded: true`
- `semantic_inventory_source: helper` or `helper-cache`
- nonzero eligible/policy counters once real browsing text is exercised
- no persistent helper error for semantic inventory or semantic admission

## Manual Smoke

Perform a live smoke on normal browsing text after diagnostics are healthy:

- browse ordinary English pages with known `en-es` SRS targets active
- confirm benign replacements still occur for clearly supported contexts
- confirm ambiguous contexts now stay original-text more often than legacy behavior
- confirm helper outage or sidecar absence causes abstain, not silent legacy replace, when pilot fallback is `abstain_on_unavailable`

Acceptable first-pilot posture:

- false abstains remain visible
- harmful replaces must stay low enough to justify the feature flag

## Rollback

Fast rollback:

- publish a pair/profile state whose semantic-admission status is no longer `Automatic`

Conservative rollback:

- keep semantic publication artifacts available
- accept standard SRS replacement behavior until ready coverage is restored

Artifact rollback:

- republish the prior SRS ruleset and semantic inventory for the affected profile/pair

## Known Limits At Publish Time

These limits should stay explicit during launch:

- published `en-es` competition sets are still the current conservative helper-side emitted-sibling PoC, not a solved fully-general miner or LP-parity-ready blocker inventory
- phrase-set publication is not populated yet, so phrase preemption does not rely on published phrase inventories
- `soft_affordance` exists in contracts and policy outputs, but the browser currently treats non-`replace` outcomes as keep-original
- extension launch readiness does not prove chat/plugin readiness
- transport is local/helper-first today; cloud packaging can be decided later without changing the runtime contract
