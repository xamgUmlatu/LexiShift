# SP2 Confidence Gating Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted runtime contract test plus helper/runtime/doc inspection
Purpose: bound the SP2.5 slice around helper-rule confidence gating so the current contract stays explicit: confidence thresholding exists during rule generation, but the live extension helper-rule activation path still does not gate on confidence
Source-of-truth: packet only; executable truth still lives in code, tests, docs, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `ai_workflow.md`
- `genai_workflow_architecture.md`
- `../rulegen/rule_generation_technical.md`
- `../reference/glossary.md`

## Slice

- Track: `SP2`
- Slice: `SP2.5`
- Title: helper-rule confidence gating
- Pass type: verification-first with runtime contract pinning and narrow state/doc correction

## Exact Seam

Primary code surface:

- `core/lexishift_core/rulegen/generation.py`
- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/use_cases/rulegen_job.py`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/shared/srs/srs_gate.js`
- `apps/chrome-extension/shared/srs/srs_selector.js`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_helper_rule_confidence_contract.py`
- `core/tests/helper/test_helper_rulegen.py`
- `core/tests/helper/test_helper_engine.py`

Primary contract/docs surface:

- `docs/rulegen/rule_generation_technical.md`
- `docs/reference/glossary.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/ai_workflow.md`
- `docs/developer/genai_workflow_architecture.md`

## Explicitly Out Of Scope

This slice does not directly review:

- confidence-scoring quality or threshold tuning by pair
- future UX for a pair-aware confidence slider
- SRS selector weighting quality outside the helper-rule activation path
- semantic-routing runtime gating

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- confidence exists in multiple layers, so it is easy to infer a live runtime gate from field presence alone
- docs that overstate this seam can mislead later UX/settings work into assuming a shipped feature already exists
- the mismatch is subtle because generation-time thresholding is real, while runtime helper-rule gating is not

## Contract Sketch

The intended current confidence-gating contract is:

1. rule generation computes rule confidence and applies `confidence_threshold` before rules are emitted
2. helper rulegen jobs resolve and pass that threshold through the current tuning/config surface
3. once helper rules are emitted and handed to extension runtime, `active_rules_runtime.js` and `srs_gate.js` do not inspect `rule.confidence` or prune helper rules by confidence
4. `shared/srs/srs_selector.js` does use confidence as a scoring input for selector-style calculations, but that is a separate utility and not the helper-rule activation gate
5. current truth should therefore remain:
   - helper-rule confidence gating at runtime is still planned
   - live helper-rule confidence filtering is not part of the current extension activation path

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Rule generation applies `confidence_threshold` before emitting rules. | `generation.py`, helper rulegen wiring | `core/tests/helper/test_helper_rulegen.py`, `docs/rulegen/rule_generation_technical.md` | `verified for this slice` |
| Helper rulegen jobs carry the threshold through resolved tuning/config. | `helper/rulegen.py`, `helper/use_cases/rulegen_job.py`, helper engine | `core/tests/helper/test_helper_engine.py`, `core/tests/helper/test_helper_rulegen.py` | `verified for this slice` |
| Extension helper-rule activation does not inspect confidence once rules are emitted. | `active_rules_runtime.js`, `srs_gate.js` | `core/tests/dev/test_extension_helper_rule_confidence_contract.py` | `verified for this slice` |
| Extension selector utilities that reference confidence are not proof of helper-rule runtime gating. | `shared/srs/srs_selector.js` | direct code inspection plus this packet/doc correction | `verified for this slice` |

## Invariants

1. generation-time thresholding and live runtime activation must be described as separate contracts
2. the presence of `metadata.confidence` on emitted rules must not be treated as proof of a live runtime helper-rule filter
3. selector/scoring utilities that read confidence must not be cited as evidence for helper-rule activation gating
4. docs/state should keep runtime confidence gating `planned` until a real settings surface, runtime code path, and tests exist
5. runtime contract tests should be able to show that low-confidence helper rules remain active once already emitted

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Rulegen emits rules with a threshold | low-confidence candidates are filtered before emission |
| Helper runtime receives low- and high-confidence helper rules | both stay eligible if already emitted and enabled |
| Extension SRS gate runs on helper rules | gate behavior keys off origin/published ruleset, not confidence |
| Extension selector code references confidence | treat it as separate selector weighting, not runtime helper-rule activation |
| Current-truth docs/state | feature stays planned until a real live gate exists |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_extension_helper_rule_confidence_contract.py -q`
  - `python3 -m pytest core/tests/helper/test_helper_rulegen.py -q -k confidence`
- state/doc integrity:
  - `npm --prefix scripts run check:state`
  - `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. verify generation-time thresholding vs live runtime activation as separate seams
2. add a direct extension runtime contract test so the absence of a live confidence gate is no longer only an inspection claim
3. narrow the state ledger and nearest current-truth docs so they describe the real contract explicitly

## Outcome

Result:

- no hidden live helper-rule confidence gate was found in the extension activation path
- current behavior is internally consistent once separated correctly:
  - rulegen can filter by `confidence_threshold` before emission
  - helper jobs preserve that thresholding contract
  - emitted helper rules then flow through extension activation without confidence-based pruning
  - selector utilities can reference confidence in other contexts, but that is not the helper-rule gate
- this slice therefore promotes the stronger current truth: runtime confidence gating remains planned rather than merely "not yet verified"
