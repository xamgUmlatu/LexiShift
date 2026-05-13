# Semantic Pack Operator Smoke Runbook

Status: active runbook
Role: Runbook / operational
Last updated: 2026-05-14
Last verified: 2026-05-14 against the `en-es-active-only-combined-full-v1-tranche-009` default pack id, Advanced debug install flow wiring, helper/native-host install command, split-inline DOM semantic-context runtime fix, optimized semantic batching, tranche-009 automated install/page-scan evidence, tranche-005 operator checkpoint evidence, and tranche-003 hands-on operator smoke evidence
Purpose: give a tester a repeatable way to install and smoke-test the current semantic-veto pack without relying on chat history
Source-of-truth: operational runbook only; implementation truth lives in `core/lexishift_core/helper/use_cases/semantic_pack_install.py`, `scripts/helper/lexishift_native_host.py`, `apps/chrome-extension/options.html`, and the extension helper client
Related docs:
- `docs/developer/feature_state_matrix.md`
- `docs/developer/post_veto_productization_and_repo_posture_plan.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`

## Scope

This runbook is for the current private/operator semantic-veto smoke path:

- pair: `en-es`
- pack id: `en-es-active-only-combined-full-v1-tranche-009`
- runtime policy: `en_es_sentence_veto_v2`
- active-only floor: `min_active_score=0.015`
- install surface: extension Options -> Advanced debug tools -> semantic pack installer

This is not the normal end-user install flow and not a cloud distribution plan.
It is the controlled way to test the latest generated pack through the same
soft-assist smoke path.

## Current Approval Status

The tranche-009 pack is automated-clean and ready for operator smoke. It has
passed repaired admission, source packaging, isolated install, and automated
live-page scan, but it is not yet operator-approved.

Tranche-005 remains the latest operator-accepted product checkpoint. The latest
hands-on browser-extension smoke remains tranche-003. That hands-on approval was
recorded after the runtime began sending surrounding sentence/block context
instead of tiny split-inline text-node fragments, and after the semantic
admission batching speedup.

Rerun it when:

- testing on a new machine or browser profile,
- changing the helper/native-host install path,
- changing the selected SRS profile or helper data root,
- changing runtime policy,
- generating or installing a new semantic pack.

## What Success Means

A successful smoke means:

- the named pack installs for the selected profile,
- SRS runtime diagnostics show semantic admission is active for the profile,
- a normal browser page with current pack words produces semantic policy decisions,
- the page shows a useful mix of replacements and kept-original text,
- helper errors, inventory errors, and fallback decisions stay at zero for the smoke.

It does not mean:

- every occurrence should be replaced,
- `en-es` coverage is complete,
- harmful replacements are impossible,
- phrase/no-winner cases are solved.

The current product stance is soft assist: fewer obviously wrong replacements and more useful visible SRS replacements, not perfect semantic filtering.

## Data-Root Choice

There are two valid testing modes.

Use the default helper data folder for live extension smoke.
This is the simplest product-like path because the native host and browser runtime read the same helper-local files.
In Options, leave `Install to default helper data folder` checked.

Use a disposable data root only for isolated materialization tests, or when the native host is also launched with the same `LEXISHIFT_DATA_DIR`.
If the pack is installed into a temp root but the native host later serves runtime requests from the default root, live browser pages will not exercise the temp-root pack.

The current unreleased-product posture allows using the default helper folder with disposable test profiles.
That is usually better than a disconnected temp root for live browser review.

## Install Through Options

1. Load the unpacked extension from `apps/chrome-extension/`.
2. Open extension Options.
3. Select or create the SRS profile you want to test.
4. Set source/target to `en` -> `es`.
5. Enable SRS practice mode.
6. Open `Advanced debug tools`.
7. Leave `Semantic inventory path override` blank.
8. Leave `Semantic pack id` as `en-es-active-only-combined-full-v1-tranche-009`.
9. For live extension smoke, leave `Install to default helper data folder` checked.
10. Click `Install semantic pack...`.
11. Confirm the overwrite prompt.

Expected current install result:

- pack id: `en-es-active-only-combined-full-v1-tranche-009`
- profile id: the selected profile, usually `default`
- rules: `416`
- competition sets: `416`

The install route writes both:

- a pair-level semantic pack copy under the helper data root,
- profile-local runtime files under `srs/profiles/<profile-id>/`.

The options workflow also clears the extension helper cache for the pair/profile after a successful install.

## Verify Diagnostics

After install:

1. Click `SRS runtime diagnostics`.
2. Confirm semantic admission is active or automatic for `en-es`.
3. Confirm helper inventory source is `helper` or `helper-cache`.
4. Confirm ready semantic rule/competition-set counts are nonzero.
5. Confirm there is no helper, inventory, or manifest-family error.

For page-level smoke, open the page developer console.
With debug logs enabled, semantic summaries should look like normal LexiShift console objects and include:

- `decisionPolicyId: "en_es_sentence_veto_v2"`
- `ready: 1`
- `inventorySource: "helper"` or `"helper-cache"`
- nonzero `eligible` on pages that contain current pack words
- nonzero `policyReplaces` or `policyAbstains` once decisions occur
- `fallbackReplaces: 0`
- `fallbackAbstains: 0`
- empty `helperError` and `inventoryError`

If `eligible` stays `0`, the page likely does not contain current pack triggers.
That is not an install failure by itself.

## Smoke Pages

Use ordinary pages that contain words from the current pack.

Known useful pages from the tranche-009 automated scan and earlier tranche-003
smoke:

- `https://en.wikipedia.org/wiki/Dentist`
- `https://en.wikipedia.org/wiki/Bar_(establishment)`
- `https://en.wikipedia.org/wiki/Bar_(music)`
- `https://en.wikipedia.org/wiki/Offset_(computer_science)`
- `https://en.wikipedia.org/wiki/Carbon_offset`
- `https://en.wikipedia.org/wiki/Bridle`
- `https://en.wikipedia.org/wiki/Self-control`
- `https://en.wikipedia.org/wiki/Heart`
- `https://en.wikipedia.org/wiki/Brother`
- `https://en.wikipedia.org/wiki/Rebate_(marketing)`
- `https://en.wikipedia.org/wiki/Smile`
- `https://en.wikipedia.org/wiki/December`
- `https://en.wikipedia.org/wiki/Latin`

The first operator smoke also used:

- `https://en.wikipedia.org/wiki/Wikipedia:Acceptable_sources`

Useful current pack triggers include:

- `acceptable`
- `dentist`
- `health`
- `bar`
- `pub`
- `offset`
- `control`
- `heart`
- `brother`
- `rebate`
- `smile`
- `tax`
- `maybe`
- `more`
- `work`
- `light`
- `report`
- `jack`
- `japanese`
- `judge`
- `knock`
- `latin`
- `male`
- `measure`
- `regulation`

Do not treat the page list as a benchmark.
It is a product-feel smoke surface.

## How To Judge Behavior

When reviewing a page, classify observed behavior in plain product terms:

- good replace: the Spanish replacement reads like the intended source sense,
- acceptable abstain: the original English is kept where the model is unsure,
- false abstain: a good replacement was missed,
- harmful replace: the Spanish replacement is visibly the wrong sense or awkward enough to hurt the reading experience.

For the current soft-assist PoC:

- false abstains are acceptable,
- some harmful replacements are acceptable,
- repeated obvious harmful replacements on common pages should be written down as follow-up data or rulegen issues,
- one-off narrow mappings do not reopen the veto research loop by themselves.

## Common Failure Modes

### Install says the helper is unavailable

Run `Test helper connection`.
If the native host exits during startup, inspect:

```text
~/Library/Application Support/LexiShift/LexiShift/logs/native_host.log
```

### Install reports unknown command

The browser is using an older native host script.
Reload the unpacked extension and make sure the installed native-host manifest points at the current workspace helper script.

### Install succeeds but the page does not change

Check these first:

- the page was reloaded after install,
- SRS practice mode is enabled,
- source/target is `en` -> `es`,
- the selected profile matches the installed profile,
- diagnostics show semantic admission active,
- the page actually contains current pack triggers,
- a disposable `data_root` was not used without also launching the native host against that same root.

### All decisions abstain

This can be normal on a page with weak or mismatched context.
Try a known smoke page and inspect `policyAbstains`, `policyReplaces`, active score, and shadow score in the console summary before treating it as a regression.

## CLI Fallback

Use the CLI when debugging outside the extension.

Product-like default helper-root install:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id default \
  --pack-id en-es-active-only-combined-full-v1-tranche-009 \
  --allow-default-data-root
```

Disposable materialization check:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id default \
  --pack-id en-es-active-only-combined-full-v1-tranche-009 \
  --data-root /tmp/lexishift-semantic-pack-smoke
```

Dry-run preview:

```bash
python3 scripts/helper/lexishift_helper.py install_semantic_pack \
  --pair en-es \
  --profile-id default \
  --pack-id en-es-active-only-combined-full-v1-tranche-009 \
  --allow-default-data-root \
  --dry-run
```

Keep `--semantic-inventory` for one-off diagnostics only.
Normal product-shaped testing should use `--pack-id`.

## Rollback

For a disposable test profile, reset or replace the profile-local SRS publication files.

For the default helper root, the low-risk rollback is to reinstall the previous pack id or refresh the profile from normal SRS/rulegen publication.
The latest operator-accepted product checkpoint remains:

```text
en-es-active-only-combined-full-v1-tranche-005
```

The latest hands-on browser-extension smoke remains
`en-es-active-only-combined-full-v1-tranche-003`.

If the goal is only to stop semantic-veto behavior temporarily, disable SRS practice mode or test with a profile that has no semantic-ready publication.

## Evidence To Preserve

For each manual smoke, record:

- date,
- pack id,
- profile id,
- page URL,
- whether diagnostics were active,
- console summary fields for at least one page,
- a short human read of visible replacements and abstains.

Use this only as operator product-feel evidence.
Do not treat it as a benchmark metric unless the rows are later captured by a reproducible scan harness.
