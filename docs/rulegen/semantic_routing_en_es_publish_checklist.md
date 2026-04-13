# en-es Semantic Routing Publish Checklist

Status: active launch checklist
Role: Runbook / operational
Last updated: 2026-04-13
Last verified: 2026-04-13 repo-doc/runtime-path inspection plus semantic-shadow experiment artifacts
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
- semantic gate state: opt-in, default-off
- artifact transport: local helper files plus extension cache fallback
- runtime action: `replace` or keep original text

Not in scope for this checklist:

- cloud-hosted semantic artifacts
- BetterDiscord/chat runtime integration
- default-on rollout
- multi-LP rollout policy
- phrase-set publication
- `soft_affordance` rendering

## Current E2E Shape

When semantic admission is enabled today, the runtime path is:

1. helper publication writes SRS rules plus semantic inventory sidecar for a pair/profile
2. extension loads rules and semantic inventory from helper, with extension cache as fallback
3. extension finds normal trie matches first
4. only SRS matches that already carry `rule.metadata.semantic_admission` are eligible for semantic admission
5. extension batches eligible matches to helper `semantic_admit_batch`
6. helper decision policy returns `replace`, `abstain`, or the reserved `soft_affordance`
7. extension renders only `replace`; all other outcomes keep the original source text

## Recommended Pilot Posture

Use this posture for the first real `en-es` pilot:

- `srsEnabled=true`
- `srsSemanticAdmissionEnabled=true`
- `srsSemanticAdmissionFallbackPolicy=abstain_on_unavailable`

Reasoning:

- `default-off` keeps current shipped behavior stable for everyone else
- `abstain_on_unavailable` matches the product preference for false abstains over harmful replaces
- rollback stays one setting flip away

## Preconditions

Before enabling the pilot for any profile:

- the helper can publish an `en-es` ruleset containing nonzero `metadata.semantic_admission` coverage
- the helper can publish an `en-es` semantic inventory sidecar for the same profile
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
4. Enable `Semantic admission (experimental)`.
5. Set fallback policy to `Abstain`.
6. Refresh or initialize the pair so helper artifacts are current.
7. Run `SRS runtime diagnostics`.

The runtime diagnostics should show all of the following:

- `semantic_admission_enabled: true`
- `semantic_fallback_policy: abstain_on_unavailable`
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

- set `srsSemanticAdmissionEnabled=false`

Conservative rollback:

- keep semantic admission enabled
- switch `srsSemanticAdmissionFallbackPolicy=legacy_on_unavailable`

Artifact rollback:

- republish the prior SRS ruleset and semantic inventory for the affected profile/pair

## Known Limits At Publish Time

These limits should stay explicit during launch:

- published `en-es` competition sets are still the current conservative PoC, not a solved fully-general miner
- phrase-set publication is not populated yet, so phrase preemption does not rely on published phrase inventories
- `soft_affordance` exists in contracts and policy outputs, but the browser currently treats non-`replace` outcomes as keep-original
- extension launch readiness does not prove chat/plugin readiness
- transport is local/helper-first today; cloud packaging can be decided later without changing the runtime contract
