# N-015 Translation Gloss Locator Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 seam read plus targeted semantic-publication/doc contract review
Purpose: bound the semantic-publication locator naming cleanup so provider-neutral translation-pack language reaches the semantic pointer contract without broadening the surrounding runtime surface
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_e1_translation_heuristics_packet.md`
- `feature_state_matrix.md`
- `../rulegen/semantic_routing_data_contract.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`

## Slice

- Track: `N-015`
- Slice: `N-015`
- Title: provider-neutral translation-gloss locator naming
- Pass type: verification-first with bounded semantic-publication contract cleanup

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/lp_capabilities.py`
- `core/lexishift_core/rulegen/semantic_publication.py`
- `core/lexishift_core/rulegen/semantic_shadow_record_clusters.py`

Primary tests/evidence surface:

- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_rulegen_adapters.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/rulegen/test_semantic_shadow_record_clusters.py`

Primary contract/docs surface:

- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/rule_generation_technical.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- provider-local loader and pair-module names such as `load_freedict_gloss_records_ordered` or `freedict_*_path`
- translation-pack download, install, or manifest resolution behavior
- semantic-shadow policy quality, competition mining, or runtime veto thresholds
- JMDict or Wiktionary locator semantics beyond keeping their current behavior stable

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the old provider-shaped names leak into capability records and current-truth docs above the helper seam
- this is easy to miss because the runtime still works, but it keeps presenting FreeDict-specific vocabulary as if it were the generic translation contract
- the slice is still bounded because it is naming and pointer construction, not scoring, admission policy, or SRS scheduling

## Contract Sketch

The intended contract for this slice is:

1. semantic-publication capability records should describe translation-gloss locators using provider-neutral vocabulary
2. locator payloads should still carry the concrete provider identity separately
3. JMDict and Wiktionary locator kinds remain provider-specific where the locator truly depends on that source structure
4. helper/runtime/docs should agree on the same exported pointer-mode vocabulary
5. regenerated semantic ids may change for translation-gloss locators because locator kind participates in the stable key, and that churn is acceptable when the artifact family is regenerated together

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Pair capability records define the exported semantic pointer-mode vocabulary. | `resolve_pair_capability(...).semantic_publication` | `core/lexishift_core/helper/lp_capabilities.py`, semantic inventory tests/docs | `verified before edit` |
| Semantic admission and inventory builders emit locator records using the same vocabulary claimed in capability records. | `_build_locator(...)`, `_build_publication_capability_record(...)` | `core/tests/rulegen/test_semantic_publication.py`, `core/tests/helper/test_rulegen_outputs.py` | `contradicted before edit` |
| Current-truth docs still describe deterministic translation-gloss pointers using FreeDict-shaped naming. | semantic-routing docs and `feature_state_matrix.md` | repo docs | `contradicted before edit` |
| Shadow-side grouped translation records should emit the same generic translation-gloss locator shape as semantic publication. | `cluster_shadow_records(...)` | no dedicated seam-local test before this slice | `uncertain before edit` |

## Invariants

1. `en-es` and `en-de` still prefer `sense_provenance` before the translation-gloss fallback
2. `de-en` and `es-en` still derive deterministic active pointers from gloss order when that metadata exists
3. locator payloads keep provider identity explicit even after the mode/kind rename
4. non-translation locator kinds (`wiktionary_ordinal`, `jmdict_entry`, `opaque`) remain unchanged
5. helper publication, semantic inventory output, and current-truth docs use the same exported locator vocabulary

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| `en-es` / `en-de` provenance-rich result | inventory capability advertises `sense_provenance` plus `translation_gloss`, while emitted locator stays `wiktionary_ordinal` when richer provenance exists |
| `de-en` / `es-en` gloss-index result | semantic admission still produces stable ids and inventory senses, but locator kind is now `translation_gloss` |
| missing gloss-index metadata on translation-gloss pairs | `reason_code` uses the generic translation-gloss wording |
| shadow-record clustering from ordered translation records | clustered locator kind matches the semantic-publication translation-gloss contract |
| regenerated semantic inventory family | pointer ids rotate coherently within the regenerated family, with no cross-artifact mismatch inside a single run |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_rulegen_adapters.py core/tests/helper/test_rulegen_outputs.py core/tests/rulegen/test_semantic_shadow_record_clusters.py -q`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. rename semantic-publication capability modes and missing-locator reason codes from `freedict_gloss` to `translation_gloss`
2. update semantic-publication and shadow-record locator builders so emitted locator kinds match that generic contract while still carrying concrete provider identity
3. add seam-local regression coverage for the semantic-publication and shadow-record locator surfaces
4. update current-truth docs and resolve the `N-015` carry-forward note
