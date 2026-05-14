# Semantic Veto Artifact Authority Audit

Status: current reference
Role: Mixed
Last updated: 2026-05-01
Last verified: 2026-05-01 against `git status --short`,
`semantic_veto_system_registry_en_es.json`,
`semantic_veto_system_registry_latest.md`, dirty semantic-veto doc diffs, and
`semantic_decision_research_lanes_latest.md`, and
`semantic_veto_local_output_disposition.md`

## Purpose

This audit keeps semantic-veto research artifacts from becoming accidental
runtime or architecture authority. It does not promote a semantic veto policy,
rerun semantic evidence, or change the browser/helper runtime path.

## Subsequent Pass Status

`semantic_methodology_doc_dirty_state_reconcile` accepted the intended
methodology-doc and decision-lane ledger updates as research-only/current
reference material. The accepted wording adds reconciliation links, records the
wave6 source/guard finding, and keeps the strongest auth-frame/rescue candidate
explicitly non-promotable until broader heldout and rulegen quality evidence
exist.

The selected wave6 evidence files referenced by that methodology wording are
now committed as generated evidence. Other dirty or untracked semantic output
files remain non-authoritative until
`local_semantic_latest_output_disposition`.

`local_semantic_latest_output_disposition` committed referenced wave2 through
wave5 draft input files as historical/seed support and left the remaining
semantic generated-output churn local-only. See
`docs/rulegen/semantic_veto_local_output_disposition.md`.

## Authority Rules

- Runtime truth comes from code, runtime tests, manifests, and helper inventory
  publication paths.
- Registry `current_reference` docs coordinate work; they are not generated
  evidence.
- Registry `generated_evidence` rows can support a claim only through their
  owning doc and action item.
- `latest` filenames are never authority by name alone.
- Dirty or untracked local generated outputs are non-authoritative until a pass
  explicitly classifies, regenerates, commits, or leaves them out of scope.
- Research remediation remains separate from integrity auditing.

## Registry Snapshot

The registry currently has `28` primary artifact paths containing `latest`.
None of those primary `latest` paths are marked as runtime truth.

State split:

- `22` are `generated_evidence`
- `4` are `historical_reference`
- `2` are `superseded`

Component split:

- `11` are `source_admission`
- `6` are `candidate_wave6`
- `6` are `historical_or_seed`
- `4` are `diagnostics`
- `1` is `decision_research`

Current interpretation: the registry is not treating `latest` reports as
runtime authority. The next risk is dirty local output drift, not registry
state collapse.

## Dirty Worktree Findings

Tracked methodology / ledger changes reviewed by
`semantic_methodology_doc_dirty_state_reconcile`:

- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/rulegen/semantic_sentence_veto_algorithm.md`
- `docs/rulegen/semantic_source_admission_program.md`
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- `docs/test_outputs/semantic_decision_research_lanes_latest.json`
- `docs/test_outputs/semantic_decision_research_lanes_latest.md`

Classification: the intended changes are current-reference or current-research
surfaces after reconciliation. They add wave6 source and guard findings plus
reconciliation links, but they remain research-only and do not alter runtime
policy.

Tracked generated-output changes reviewed by
`local_semantic_latest_output_disposition`:

- wave5 source-portfolio normalized evidence under
  `docs/test_outputs/experiments/semantic_example_frame_batches/`
- wave5 source-admission sidecar reports under `docs/test_outputs/`
- generic `project_health`, `feature_state`, rulegen benchmark, and benchmark
  triage outputs

Classification: these dirty files remain local generated output state. Within
this semantic-veto workstream, the wave5 source-portfolio lane remains
historical context. The sidecar deltas are timestamp-only and the normalized
evidence deltas are large generated-output churn, so this pass leaves them
unstaged. The generic project-health and rulegen benchmark outputs are outside
semantic-veto artifact authority and should not steer this workstream.

Untracked local generated outputs reviewed by
`local_semantic_latest_output_disposition`:

- wave2 through wave5 non-v10 draft datasets and queues under
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/`
- wave6 translation-sense, alternate-phrase, surface-POS, margin, heldout, and
  rescue sweep outputs under `docs/test_outputs/`

Classification: wave2 through wave5 draft inputs referenced by tracked reports,
heldout cases, or harness defaults were committed as historical/seed support.
Their manifest is
`docs/test_inputs/semantic_veto_wave2_wave5_draft_input_manifest_en_es.json`.
Unreferenced wave6 comparator outputs remain local-only and non-authoritative.

## Preserved Research Lane

The wave7 research lane remains queued as
`wave7_active_signal_and_rescue_split`. It starts from the phrase-control
triage artifacts and should not be advanced during integrity-audit passes unless
the user explicitly switches to research remediation.

## Follow-Up Audit Order

The integrity audit lane has no remaining queued disposition pass. Future work
should either execute the parked research lane,
`wave7_active_signal_and_rescue_split`, or open a new reconciliation pass if
runtime policy, harness coverage, or artifact authority changes.
