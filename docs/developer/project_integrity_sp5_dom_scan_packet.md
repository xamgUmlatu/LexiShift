# SP5 DOM Scan Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted DOM scan runtime contract tests plus structure/doc checks
Purpose: bound the final `SP5` slice around DOM scan ordering and page-budget behavior so the content-runtime seam has direct executable evidence for deterministic scan distribution, budget seeding, and manifest-order dependencies
Source-of-truth: packet only; executable truth still lives in the content runtime scan modules, structure tests, and current extension architecture docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `../architecture/extension_system_map.md`
- `../architecture/chrome_extension_technical.md`

## Slice

- Track: `SP5`
- Slice: DOM scan ordering and scan-budget behavior
- Title: content scan-order and budget-state contract
- Pass type: verification-first slice with narrow doc/test correction

## Exact Seam

Primary code surface:

- `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
- `apps/chrome-extension/content/runtime/dom_scan/scan_order.js`
- `apps/chrome-extension/content/runtime/dom_scan/page_budget_tracker.js`
- `apps/chrome-extension/content/processing/replacement_selection.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/manifest.json`

Primary docs/evidence surface:

- `core/tests/dev/test_extension_dom_scan_runtime_contract.py`
- `core/tests/architecture/test_extension_structure.py`
- `docs/architecture/extension_system_map.md`
- `docs/architecture/chrome_extension_technical.md`

## Explicitly Out Of Scope

This slice does not directly review:

- tokenization or trie-match correctness
- semantic admission gating behavior inside scan results
- popup rendering or feedback lifecycle after spans are created
- helper/runtime rule resolution already covered in earlier slices
- broader content-script composition beyond the scan-order and page-budget seam

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `low`
- priority: `high`

Reasoning:

- DOM scan order and budget usage directly shape what the user sees on the page, but regressions here can still look superficially "fine" if some replacements happen
- a stale manifest-order test and stale docs can miss a live dependency even when the runtime still works locally
- the content scan seam had no direct Node-backed contract test before this slice

## Contract Sketch

The intended current contract is:

1. `scan_order.js` only reorders nodes when page-level budgets are active
2. the full-scan reorder is deterministic for the same page/profile seed and can vary across profile/page seeds
3. `page_budget_tracker.js` seeds page budget usage from already-rendered `.lexishift-replacement` spans and increments usage as new replacements are applied
4. `dom_scan_runtime.js` builds page budget state before reordering nodes and before per-node processing in a full scan
5. the manifest-order test and current architecture docs must list `scan_order.js` as a first-class dependency before `dom_scan_runtime.js`

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Scan reordering is disabled when page budgets are off and deterministic when budgets are on. | `scan_order.js` | new Node-backed DOM-scan contract test | `verified for this slice` |
| Page budget state seeds from existing replacement spans and updates usage incrementally. | `page_budget_tracker.js` | new Node-backed DOM-scan contract test | `verified for this slice` |
| Full-scan runtime builds budget state before node reorder and processes the reordered node list. | `dom_scan_runtime.js` | new Node-backed DOM-scan contract test | `verified for this slice` |
| Manifest-order structure checks include the full DOM scan helper stack. | `manifest.json`, structure test | updated structure test | `fixed and verified in this slice` |
| Current extension docs describe `scan_order.js` and the active scan-order behavior. | extension architecture docs | doc update plus doc-reference check | `fixed in this slice` |

## Invariants

1. page-budget enforcement must not silently depend on raw DOM order alone when distribution is enabled
2. full-scan ordering must be deterministic for the same page/profile context
3. existing replacement spans must count against page budgets during later full scans or rescans
4. manifest-order tests and docs must describe every live DOM scan dependency that `dom_scan_runtime.js` requires

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Budgets disabled | node order remains unchanged |
| Budgets enabled | node order is deterministic and redistributed |
| Existing page replacements | seeded budget counts reflect already-rendered spans |
| New replacement accounting | budget state increments on newly applied replacements |
| Full scan | runtime builds budget state, reorders nodes, then processes them |
| Manifest order | `scan_order.js` loads before `dom_scan_runtime.js` |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_dom_scan_runtime_contract.py core/tests/architecture/test_extension_structure.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. add direct Node-backed coverage for scan-order distribution and budget seeding
2. repair the static manifest-order assertion so it includes `scan_order.js`
3. correct the current extension docs so the DOM scan seam matches the executable runtime

## Outcome

Result:

- the DOM scan seam now has direct executable evidence for the scan-order and page-budget contract rather than only code inspection plus partial manifest-order checks
- the static structure test now guards the full DOM scan helper stack that the runtime depends on
- the current extension docs no longer omit the deterministic scan-order module and behavior
