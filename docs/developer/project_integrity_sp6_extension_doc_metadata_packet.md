# SP6 Extension Doc Metadata Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 extension architecture doc metadata refresh plus doc-safety checks
Purpose: bound the next SP6 seam around extension architecture doc metadata so header dates and authority labels now match the body truth already refreshed during SP5 and SP6.1
Source-of-truth: packet only; canonical architecture truth still lives in the extension architecture docs, the state ledger, and the direct SP5/SP6 evidence
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `../architecture/options_controllers_architecture.md`
- `../architecture/extension_system_map.md`
- `../architecture/chrome_extension_technical.md`
- `project_integrity_sp5_options_bootstrap_packet.md`
- `project_integrity_sp5_share_import_packet.md`
- `project_integrity_sp5_dom_scan_packet.md`
- `project_integrity_sp6_feature_state_refresh_packet.md`

## Slice

- Track: `SP6`
- Slice: stale present-tense claims in seam docs
- Title: extension architecture metadata refresh
- Pass type: narrow doc-metadata correction

## Exact Seam

Primary contract/docs surface:

- `docs/architecture/options_controllers_architecture.md`
- `docs/architecture/extension_system_map.md`
- `docs/architecture/chrome_extension_technical.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

Supporting evidence surface:

- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_sp5_options_bootstrap_packet.md`
- `docs/developer/project_integrity_sp5_share_import_packet.md`
- `docs/developer/project_integrity_sp5_dom_scan_packet.md`
- `docs/developer/project_integrity_sp6_feature_state_refresh_packet.md`

## Explicitly Out Of Scope

This slice does not directly review:

- new runtime or controller behavior
- additional present-tense wording beyond the header metadata/authority labels
- feature-state ledger structure
- broader evidence-path hygiene across other architecture or planning docs

## Risk Score

- likelihood: `low`
- blast radius: `low`
- observability: `high`
- priority: `medium`

Reasoning:

- the body content in these docs was already brought current by earlier slices, but the stale header dates could make readers discount that truth
- the risk is not hidden product breakage; it is preventable trust erosion in the docs that later cleanup work will rely on

## Contract Sketch

The intended current SP6 seam-doc metadata contract is:

1. header metadata should not make freshly corrected current-truth docs look stale
2. authority labels should be re-checked when metadata is touched, but changed only if the body truth actually moved
3. the mixed/current distinction should stay explicit:
   - `options_controllers_architecture.md` and `extension_system_map.md` remain canonical current references
   - `chrome_extension_technical.md` remains a mixed reference because it still intentionally includes rollout/gap-tracking sections

## Claim-To-Evidence Map

| Claim | Owning docs/evidence | Evidence surface | Current status |
|---|---|---|---|
| The extension architecture docs contain April 21 current-truth body updates from SP5/SP6.1. | extension architecture docs plus SP5/SP6 packets | direct doc inspection | `verified before this slice` |
| The stale `Last updated: 2026-03-21` headers were metadata drift rather than proof that the body truth was still March-only. | targeted docs plus `N-020` | direct header/body comparison | `verified before this slice` |
| The canonical-current labels on the two architecture maps are still correct. | `options_controllers_architecture.md`, `extension_system_map.md` | direct doc inspection | `confirmed in this slice` |
| The mixed label on `chrome_extension_technical.md` is still correct because rollout/gap-tracking sections remain intentionally mixed. | `chrome_extension_technical.md` | direct doc inspection | `confirmed in this slice` |
| The note is now resolved instead of left as open drift. | `project_integrity_secondary_pass_notes.md` | direct doc update in this slice | `fixed in this slice` |

## Invariants

1. doc metadata should support the current authority routing, not undermine it
2. keep mixed/current labels tied to actual body scope, not to whether a file was recently edited
3. do not widen a metadata correction into another behavior audit

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Reader checks extension architecture docs after SP5/SP6 | header dates no longer imply the files are older than the body truth |
| Reader compares architecture docs with `feature_state_matrix.md` | authority surfaces no longer look artificially out of sync by date alone |
| Reader asks whether `chrome_extension_technical.md` should now be canonical current | packet records that the mixed label was reviewed and intentionally retained |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. update the stale `Last updated` metadata on the three targeted extension docs
2. explicitly re-check the current-vs-mixed labels instead of assuming they should change
3. resolve `N-020` now that the metadata/header drift is closed

## Outcome

Result:

- the extension architecture docs no longer look artificially stale relative to the SP5/SP6 body updates they already contain
- the authority labels were reviewed and left intentionally unchanged, which keeps the mixed/current routing explicit instead of making a cosmetic label flip
- `N-020` is now resolved without broadening the pass into another runtime or architecture rewrite
