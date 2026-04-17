# Project Integrity Secondary Pass Notes

Status: active notes
Role: Planning / WIP
Last updated: 2026-04-17
Last verified: 2026-04-17 ledger expanded with taxonomy guidance so repeated finding classes are easier to spot
Purpose: capture interesting observations discovered during the secondary pass that are not fixed or fully resolved in the current slice
Source-of-truth: notes ledger only; entries are reminders and hypotheses, not verified product truth unless promoted into code, tests, `feature_state_matrix.md`, or another canonical doc
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_stabilization_runbook.md`
- `feature_state_matrix.md`

## How To Use This Ledger

Add an entry when:

- the observation is relevant to integrity/correctness,
- it is not the immediate slice being executed,
- and it would be easy to forget if it only lived in chat history.

Each entry should be specific enough that a later pass can pick it up without re-discovering it from scratch.

Recommended status values:

- `carry-forward`: worth reviewing in a later slice
- `promoted`: moved into a canonical doc/backlog item/test task
- `resolved`: addressed directly in code/docs/tests
- `dismissed`: reviewed later and determined not to require action

Recommended category values:

- `contract mismatch`
- `persistence drift`
- `lifecycle bug`
- `negative-path gap`
- `docs/state drift`
- `false-green evidence`
- `tooling noise`

## Entries

| ID | Date | Found during | Category | Observation | Why it matters | Suspected scope | Status | Next action | Promotion target |
|---|---|---|---|---|---|---|---|---|---|
| `N-001` | 2026-04-17 | SRS quality harness refresh | `contract mismatch` | Due-aware publication still reports a warning: published ruleset covers more items than the due subset in at least one synthetic scenario. | This may be an intentional publication/runtime contract, an under-documented behavior, or a real correctness gap. | `SP2` SRS publication/runtime semantics | `carry-forward` | Decide during `SP2` whether this is expected, doc-only, or a bug; attach the answer to the harness evidence. | `feature_state_matrix.md`, SRS docs, or targeted SRS tests |
| `N-002` | 2026-04-17 | `npm --prefix scripts run check:changed` | `tooling noise` | The repo-safety loop still reports `changed_style_status: advisory-fail` locally because `.venv/bin/python` cannot import `ruff`. | This reduces signal quality and makes it easier to ignore meaningful validation output. | `SP7` tooling reliability | `carry-forward` | Decide whether the right fix is local environment setup, script hardening, or explicit workflow guidance. | local setup docs or repo-safety tooling |
| `N-003` | 2026-04-17 | Secondary-pass planning | `docs/state drift` | The stabilization backlog's structural-health snapshot still reflects the earlier near-limit state and clean-worktree checkpoint, not the current branch after the recent splits and generated evidence refreshes. | Planning docs can become misleading if the snapshot looks current after the branch reality has changed. | `SP6` backlog reconciliation | `carry-forward` | Refresh the snapshot once the next documentation/state reconciliation slice is ready. | `project_integrity_stabilization_backlog.md` |
| `N-004` | 2026-04-18 | `SP1.5` secondary resource compatibility review | `contract mismatch` | `wordnet-en` and `moby-en` now participate in the shared language-resource binding/manual-path map in the settings panel, but downstream consumers still rely on the dedicated `wordnet_dir` and `moby_path` fields rather than a fully uniform secondary-pack contract. | Future normalization or UX refactors can update one representation and accidentally leave the other behind unless this exception stays explicit. | later secondary lexical normalization and runtime-consumer reconciliation | `carry-forward` | When the secondary lexical family decision is made, decide whether these two sources become normal managed/manual pack entries everywhere or remain documented permanent exceptions. | `data_source_normalization_execution_order.md`, `feature_state_matrix.md`, or a later SP1/SP5 packet |
