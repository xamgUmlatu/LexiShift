# Semantic Veto Artifact Authority Audit

Status: current reference
Role: Integrity audit snapshot
Last updated: 2026-05-01
Last verified: 2026-05-01 against `git status --short`,
`semantic_veto_system_registry_en_es.json`,
`semantic_veto_system_registry_latest.md`, and dirty semantic-veto doc diffs

## Purpose

This audit keeps semantic-veto research artifacts from becoming accidental
runtime or architecture authority. It does not promote a semantic veto policy,
rerun semantic evidence, or change the browser/helper runtime path.

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

The registry currently has `27` primary artifact paths containing `latest`.
None of those primary `latest` paths are marked as runtime truth.

State split:

- `21` are `generated_evidence`
- `4` are `historical_reference`
- `2` are `superseded`

Component split:

- `11` are `source_admission`
- `6` are `candidate_wave6`
- `6` are `historical_or_seed`
- `4` are `diagnostics`

Current interpretation: the registry is not treating `latest` reports as
runtime authority. The next risk is dirty local output drift, not registry
state collapse.

## Dirty Worktree Findings

Tracked methodology / ledger changes:

- `docs/rulegen/semantic_decision_rule_comparison_plan.md`
- `docs/rulegen/semantic_sentence_veto_algorithm.md`
- `docs/rulegen/semantic_source_admission_program.md`
- `docs/test_inputs/semantic_decision_research_lanes_en_es.json`
- `docs/test_outputs/semantic_decision_research_lanes_latest.json`
- `docs/test_outputs/semantic_decision_research_lanes_latest.md`

Classification: these are current-reference or current-research surfaces, but
the dirty changes are not yet authoritative. They appear to add wave6 source and
guard findings plus reconciliation links. Review them as a separate
methodology-doc reconciliation pass before treating their wording as canonical.

Tracked generated-output changes:

- wave5 source-portfolio normalized evidence under
  `docs/test_outputs/experiments/semantic_example_frame_batches/`
- wave5 source-admission sidecar reports under `docs/test_outputs/`
- generic `project_health`, `feature_state`, rulegen benchmark, and benchmark
  triage outputs

Classification: these dirty files are local generated output state. Within this
semantic-veto workstream, the wave5 source-portfolio lane remains historical
context unless a later audit registers more of those sidecars explicitly. The
generic project-health and rulegen benchmark outputs are outside semantic-veto
artifact authority and should not steer this workstream.

Untracked local generated outputs:

- wave2 through wave5 non-v10 draft datasets and queues under
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/`
- wave6 translation-sense, alternate-phrase, surface-POS, margin, heldout, and
  rescue sweep outputs under `docs/test_outputs/`

Classification: these are local experiment outputs, not current authority.
They need a disposition pass before they are committed, archived, regenerated,
or ignored.

## Preserved Research Lane

The wave7 research lane remains queued as
`wave7_active_signal_and_rescue_split`. It starts from the phrase-control
triage artifacts and should not be advanced during integrity-audit passes unless
the user explicitly switches to research remediation.

## Follow-Up Audit Order

1. `semantic_methodology_doc_dirty_state_reconcile`: review dirty methodology
   docs and the decision research lane ledger, then decide what becomes
   current reference versus what stays research-only.
2. `local_semantic_latest_output_disposition`: classify dirty and untracked
   generated semantic outputs as commit, archive, regenerate, or out-of-scope
   local output.
