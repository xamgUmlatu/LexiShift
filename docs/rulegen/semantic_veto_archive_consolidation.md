# Semantic Veto Archive Consolidation

Status: current reference
Role: Archive and supersession ledger
Last updated: 2026-05-01
Scope: semantic-veto research artifacts that remain useful but should not steer
the current candidate directly

This ledger preserves older semantic-veto findings without letting old
`latest` reports compete with the current source of truth. It does not delete
artifacts. It classifies them so future work can cite the surviving lesson
without reviving an outdated promotion claim.

## Current Steering Set

Use these artifacts first for current semantic-veto decisions:

- `docs/rulegen/semantic_veto_reconciliation_workstream.md`
- `docs/test_inputs/semantic_veto_system_registry_en_es.json`
- `docs/test_outputs/semantic_veto_system_registry_latest.md`
- `docs/rulegen/semantic_veto_assumption_ledger.md`
- `docs/rulegen/semantic_veto_current_wave6_rerun_chain.md`
- `docs/rulegen/semantic_veto_breadth_expansion_gate.md`

The current candidate remains
`wave6_auth_frame_raw_sentence_surface_pos_rescue`, with no runtime policy
change. Older artifacts below are context, controls, or superseded failure
baselines unless the registry names them as current candidate inputs.

## Archive Rows

| Artifact | Registry State | Surviving Lesson | Why It No Longer Steers |
| --- | --- | --- | --- |
| `docs/test_outputs/semantic_source_reference_lane_latest.md` | historical_reference | Freezing a lane manifest plus source-cycle, active/shadow, phrase, and admitted-evidence checks is the right reproducibility pattern. | It describes an older masked-sentence source-reference lane, not the current wave6 auth-frame raw-sentence rescue candidate and not runtime behavior. |
| `docs/test_outputs/semantic_source_admission_cycle_wordnet_active_related_plant_cell_depth3_heldout_v2_policy_latest.md` | historical_reference | WordNet active-related rows plus staged source admission were useful for source-cycle validation. | Its `promotion_candidate` wording is offline source-lane terminology and has been superseded for current steering by the wave6 candidate registry rows. |
| `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave5_portfolio_latest.md` | historical_reference | Wave5 proved the value of materialized portfolios, phrase-gap tracking, and breadth-gap accounting before broader claims. | It is a seed-pass portfolio read; wave6 and the breadth gate now carry the current source-support and breadth questions. |
| `docs/test_outputs/semantic_source_non_v10_wave6_wiktextract_supported_heldout_margin005_validation_latest.md` | superseded | The first wave6 supported-source heldout exposed concrete blockers and failure traces. | It predates raw-sentence context, authorization-frame evidence, and scorer-backed rescue validation, so its metrics are a failure baseline rather than the current candidate read. |
| `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_wiktextract_supported_latest.md` | superseded | The original wave6 blockers (`leave`, `piece`, `bear`, `fair`) shaped the later auth-frame, raw-sentence, and rescue-gate work. | The current blocker posture now comes from `auth_frame_failure_mining` plus the breadth expansion gate. |
| `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave32_anypos_unsupported_latest.md` | historical_reference | Forward-only upper-bound sweeps expose source-support ceilings and acquisition targets. | Unsupported upper-bound completion is not source-supported promotion evidence and must route through source-support conversion before current-candidate claims. |
| `docs/test_inputs/semantic_veto_wave2_wave5_draft_input_manifest_en_es.json` | historical_reference | These input files keep older tracked wave2-wave5 reports, heldout cases, and harness defaults reproducible. | They are seed/history support inputs only; current candidate steering uses the registry's wave6 and wave7 rows. |

## Retained Current References

These docs still matter, but they are no longer the first place to decide the
current candidate:

- `docs/rulegen/semantic_decision_rule_comparison_plan.md`: methodology for
  isolating context, scorer, aggregation, final rule, and phrase handling.
- `docs/rulegen/semantic_source_admission_program.md`: source-admission history,
  operating constraints, and older source-lane lessons.
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`: research-lane
  state ledger for decision experiments.

When these docs use older "current best" or `promotion_candidate` language,
interpret it within the local section date and artifact family. Current system
truth comes from the reconciliation registry and rendered summary.

## Follow-Up Queue

- Keep adding historical or superseded rows when a future pass finds old
  `latest` artifacts cited as current authority.
- Do not delete generated reports until their surviving lesson is represented
  in this ledger, the system registry, or the workstream.
- If a historical artifact becomes part of a new candidate again, promote it
  through the registry with fresh validation rather than relying on the old
  `latest` filename.
