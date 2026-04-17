# SP2 Profile Schema Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted extension profile-schema contract tests plus doc/code inspection
Purpose: bound the first SP2 slice around SRS profile schema and sizing authority so later admission/publication reviews start from an explicit current executable contract
Source-of-truth: packet only; executable truth still lives in code, tests, docs, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `SP2`
- Slice: `SP2.1`
- Title: profile schema and sizing authority
- Pass type: verification-first with contract-tightening tests

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
- `apps/chrome-extension/options/core/helper/base_methods.js`
- `apps/chrome-extension/options/core/helper/srs_set_methods.js`
- `core/lexishift_core/srs/set_policy.py`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_profile_schema_contract.py`
- `core/tests/dev/test_extension_srs_action_workflows.py`
- `core/tests/srs/test_srs_set_policy.py`

Primary contract/docs surface:

- `docs/srs/srs_profile_schema.md`
- `docs/developer/project_integrity_stabilization_backlog.md`
- `docs/developer/feature_state_matrix.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether profile-driven admission strategies are fully executable today
- due-aware publication/runtime semantics
- preview/rebalance mutation guarantees beyond the profile-context and sizing contract they consume
- extension controller/UI wiring details beyond what is needed to confirm schema truth

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- later SRS slices depend on agreement about what the profile schema actually is today
- if docs overstate editable or executable signal fields, later correctness reviews can argue about behavior that is not actually reachable
- the main risk here is contract drift between docs, extension normalization, and helper request envelopes

## Contract Sketch

The intended current profile-schema contract is:

1. extension signal storage uses a fixed top-level `v1` allowlist
2. unknown top-level signal families are dropped before helper-facing profile context is composed
3. helper-facing `profile_context` uses normalized snake_case mirrors for the allowed signal families
4. sizing remains authoritative in the top-level helper request envelope, not in nested `profile_context.constraints` / `profile_context.sizing`
5. nested `constraints` / `sizing` inside `profile_context` are descriptive mirrors for planner cohesion and diagnostics, not execution authority

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Extension signal normalization keeps a fixed top-level allowlist and drops unknown families. | `signals_methods.js` | `core/tests/dev/test_extension_srs_profile_schema_contract.py` | `verified for this slice` |
| Helper-facing profile context uses snake_case mirrors of the allowed signal families. | `srs_profile_methods.js`, workflow formatting/tests | `core/tests/dev/test_extension_srs_action_workflows.py` | `verified for this slice` |
| Top-level helper request sizing remains authoritative even if nested `profile_context.sizing` disagrees. | `helper/base_methods.js`, `helper/srs_set_methods.js`, `srs/set_policy.py` | `core/tests/dev/test_extension_srs_profile_schema_contract.py`, `core/tests/srs/test_srs_set_policy.py` | `verified for this slice` |
| Current docs should keep unknown-family dropping and top-level sizing authority explicit enough for later SRS slices. | `docs/srs/srs_profile_schema.md` | doc/code inspection plus this slice packet | `verified for this slice` |

## Invariants

1. adding a new top-level signal family requires code changes, not only doc changes
2. unknown top-level signal families do not silently leak into helper-facing profile context
3. nested keys inside allowed families may survive as compatibility/data-ready payload, but top-level family membership remains fixed
4. helper request sizing is determined from top-level request fields, not nested `profile_context` mirrors
5. later SRS slices should treat `profile_context.sizing` / `constraints` as descriptive mirrors unless code changes make them authoritative

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Stored signals include unknown top-level family | family is dropped by extension normalization |
| Allowed signal families include nested data | allowed families survive normalization |
| Helper request carries mismatched top-level sizing and nested profile-context sizing | top-level request sizing remains authoritative |
| Planner context composition | allowed signal families are mirrored under normalized snake_case helper keys |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_extension_srs_profile_schema_contract.py -q`
  - `python3 -m pytest core/tests/dev/test_extension_srs_action_workflows.py -q`
  - `python3 -m pytest core/tests/srs/test_srs_set_policy.py -q`

## Planned Action For This Slice

1. verify the fixed signal-family allowlist directly instead of inferring it from docs
2. verify top-level sizing authority directly instead of inferring it from request examples
3. tighten the schema doc only if code inspection shows that the current wording is still overstating the executable contract

## Outcome

Result:

- no correctness defect found in the SP2.1 profile-schema seam
- the current local schema doc already carried the main allowlist-vs-sizing distinction, and this slice now pins those assumptions directly in targeted tests
- this gives later SP2 slices a cleaner foundation by reducing argument over which profile fields are actually current executable inputs
