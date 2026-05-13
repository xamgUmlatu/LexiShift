# Post-Veto Productization And Repo Posture Plan

Status: active planning
Role: Planning / WIP
Last updated: 2026-05-14
Last verified: 2026-05-14 doc-routing slice against `feature_state_matrix.md`, semantic-veto registry summary, tranche-011 automated follow-through artifacts, tranche-005 operator product checkpoint, split-inline DOM semantic-context runtime fix, optimized semantic batching, tranche-003 hands-on operator smoke evidence, and the semantic-pack operator smoke runbook
Purpose: organize the work after the first successful semantic-veto product smoke, without reopening open-ended veto research by default
Source-of-truth: planning document only; current implementation truth lives in source code, `docs/developer/feature_state_matrix.md`, and the semantic-veto registry artifacts

## Current Checkpoint

The semantic-veto workstream has reached a real product-smoke checkpoint:

- `en-es-active-only-combined-full-v1-tranche-011` is the latest automated-clean generated-data pack.
- The pack has `455` source-target families, `922` normalized evidence rows, and installs as `455` helper rules.
- Installed competition sets are `432` active-only and `23` shadowed/mixed.
- The extension Advanced debug install flow can install the named pack without pasting an inventory file path.
- Live browser smoke accepted the tranche-003 pack with the `en_es_sentence_veto_v2` active-only policy and `min_active_score=0.015` as useful soft-assist behavior after the runtime began using surrounding sentence/block context for split-inline DOM text and after semantic batching was optimized.
- Tranche-005 remains the latest operator-accepted product checkpoint.
- Tranche-003 remains the latest formally recorded hands-on browser-extension smoke.
- Tranche-011 has passed paid generation, admission, postprocess, source packaging, isolated pack install, and automated live-page scan. It is automated-clean and ready for an operator checkpoint if desired.
- The active-only SRS-derived generation queue is now exhausted under the current reviewed 570-family denominator: `455` families are covered and the remaining `115` are excluded from active-only generation as weak or non-visible source-target rows.

This is not full `en-es` semantic coverage, and it is not a near-zero-harmful replacement guarantee.
It is a bounded soft-assist feature checkpoint: many good replacements become visible, some bad replacements are still expected, and false abstains remain acceptable if the browsing experience still improves.

## Product Boundary

The current product stance is:

- semantic veto is a helper-backed runtime enhancement for SRS-origin browser replacements,
- the user either sees the replacement or keeps the original text,
- active-only cue evidence is the only paid data shape currently proven through generation, admission, packaging, install, and live smoke,
- generated shadows and phrase/no-winner controls remain later lanes, used only when active-only evidence leaves clear harmful replacement classes,
- narrow rulegen mappings such as `tax -> imponer` are accepted for this PoC rather than turning this phase back into broad rulegen repair.

The current non-goals are:

- no broad new decision-algorithm research unless live testing exposes a severe, repeated failure class,
- no full-budget generation without source-target review and spend guards,
- no cloud distribution decision before local profile installation and artifact versioning are clean,
- no public-facing claim that semantic veto is complete across all `en-es`.

## Workstream Principles

1. Stabilize what works before expanding it.
2. Keep debug/operator install paths separate from the normal user product path until they are deliberately promoted.
3. Treat generated reports as evidence, not source-of-truth planning by themselves.
4. Continue paid generation only in resumable, reviewed tranches.
5. Keep project presentation modest: demonstrate the actual local-first product, not an overclaimed research result.

## Roadmap

### 1. Checkpoint Stabilization

Goal: make the current state easy to recover, explain, and verify.

Work:

- keep `feature_state_matrix.md` aligned with the current pack, runtime policy, and known gaps,
- keep the semantic-veto registry summary clean,
- preserve the tranche-011 pack artifacts and install path,
- avoid touching unrelated untracked research files unless explicitly routed,
- document any broad repo-safety blocker separately from semantic-veto success.

Exit criteria:

- canonical docs say the same thing as the installed pack and current helper/runtime code,
- a future agent can identify the current pack, policy id, coverage count, and install route without reading chat history,
- doc-reference and state checks are clean or have clearly separated unrelated failures.

### 2. Product Install And Testing Flow

Goal: make product-shaped testing repeatable without developer-only path guessing.

Work:

- keep named semantic-pack installation as the default test flow,
- use `docs/rulegen/semantic_pack_operator_smoke_runbook.md` as the tester runbook for installing the pack, reloading the extension, and choosing test pages,
- use `docs/rulegen/semantic_veto_active_only_tranche_runbook.md` for tranche-003 and later generated-data follow-through,
- verify diagnostics expose enough information to distinguish replace, abstain, helper error, inventory error, fallback, and policy id,
- decide whether the current Advanced debug install path is sufficient for the private PoC or whether a first-class local semantic-pack installer is needed.

Exit criteria:

- a tester can install the current pack into a disposable profile or explicit data root,
- the extension can be reloaded and exercised without manual inventory-path edits,
- observed behavior can be diagnosed from existing logs and diagnostics.

### 3. Guarded Data Generation Follow-Through

Goal: expand coverage only through the process that has already worked.

Work:

- refresh the SRS-derived `en-es` source-target denominator,
- review the next source-target tranche before spending,
- generate active-only cue rows with explicit request count, run id, pricing inputs, and cost ceiling,
- run admission, postprocess, source packaging, pack build, isolated install, live-page scan, and registry summary after each tranche,
- stop or redirect if a tranche shows systematic data-quality or product-feel regression.

Exit criteria:

- each paid tranche is independently resumable and auditable,
- coverage remains explainable from the current `455 / 570` automated-clean family checkpoint with no hidden data mutation,
- the next tranche is never treated as approved until source-target review and no-spend request planning pass.

Deferred TODO:

- Research broader `en-es` SRS-corpus expansion after the current semantic-veto
  tranche path is stable. The current `1,984` Spanish target denominator comes
  from the installed `freq-es-cde` sample frequency pack, which contains `2,000`
  rows, not from a final product decision to cap Spanish SRS at about two
  thousand words. Future work should compare licensing-safe broader Spanish
  frequency resources, POS/rank quality, integration with SRS admission and
  rulegen, and the resulting semantic-veto evidence-generation cost before
  changing the current active-only tranche plan.

### 4. Repo Presentation And Employer-Facing Posture

Goal: make the project legible as a serious local-first language-learning system.

Work:

- update public-facing README and developer routing only after current truth is stable,
- emphasize the working product surfaces: desktop GUI, Chrome extension, helper, SRS, rulegen, local data packs, and semantic-veto PoC,
- add a concise demo/testing story rather than forcing readers through research artifacts,
- keep research depth available through docs, but route casual readers to product and architecture first,
- avoid presenting semantic veto as solved language-wide.

Exit criteria:

- a new reader can understand what LexiShift does in under a minute,
- an interviewer can find system architecture, test strategy, and a credible advanced feature without reading generated artifacts,
- deeper semantic-veto research remains discoverable but does not dominate the repo entrypoint.

### 5. Release Hygiene

Goal: ensure the repo can support credible packaging and continued work.

Work:

- separate semantic-veto-specific validation from broad existing repo debt,
- triage the full-repo pre-push mypy failures that currently block ordinary pushes without `SKIP=repo-safety-check`,
- run build/package checks when packaging surfaces change,
- keep default local safety loops documented and runnable.

Exit criteria:

- normal commits and pushes do not require bypassing unrelated broad failures,
- known build/test debts are explicit and owned,
- release-facing docs match the actual supported app surfaces.

## Immediate Next Slices

1. Record an operator checkpoint for tranche-011 if desired.
2. Treat the active-only generation lane as complete under the current 570-family denominator unless the SRS corpus or source-target review policy changes.
3. Product install polish and public README posture remain separate slices after the generated-data checkpoint is safe.

## Verification

For doc-only updates in this workstream:

```bash
python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

For semantic-pack install/runtime changes, add the focused tests listed in `docs/developer/feature_state_matrix.md` under the Semantic Routing Runtime Admission Layer.
