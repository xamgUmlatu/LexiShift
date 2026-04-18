# Project Integrity Secondary Pass Notes

Status: active notes
Role: Planning / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 E4 installed/manual contract checkpoint
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
| `N-001` | 2026-04-17 | SRS quality harness refresh | `contract mismatch` | Due-aware publication still reports a warning: published ruleset covers more items than the due subset in at least one synthetic scenario. | This mattered because the system had a due queue and due-aware design docs, but helper publication/runtime gating still operated on the broader admitted inventory. | `SP2` SRS publication/runtime semantics | `promoted` | `SP2.4` promoted this into explicit current truth: due-aware serving remains planned, while the harness keeps broader-than-due publication as a warning instead of a pass claim. | `feature_state_matrix.md`, `project_integrity_sp2_due_aware_serving_packet.md`, SRS practice docs |
| `N-002` | 2026-04-17 | `npm --prefix scripts run check:changed` | `tooling noise` | The repo-safety loop still reports `changed_style_status: advisory-fail` locally because `.venv/bin/python` cannot import `ruff`. | This reduces signal quality and makes it easier to ignore meaningful validation output. | `SP7` tooling reliability | `carry-forward` | Decide whether the right fix is local environment setup, script hardening, or explicit workflow guidance. | local setup docs or repo-safety tooling |
| `N-003` | 2026-04-17 | Secondary-pass planning | `docs/state drift` | The stabilization backlog's structural-health snapshot still reflects the earlier near-limit state and clean-worktree checkpoint, not the current branch after the recent splits and generated evidence refreshes. | Planning docs can become misleading if the snapshot looks current after the branch reality has changed. | `SP6` backlog reconciliation | `carry-forward` | Refresh the snapshot once the next documentation/state reconciliation slice is ready. | `project_integrity_stabilization_backlog.md` |
| `N-004` | 2026-04-18 | `SP1.5` secondary resource compatibility review | `contract mismatch` | `wordnet-en` and `moby-en` now participate in the shared language-resource binding/manual-path map in the settings panel, but downstream consumers still rely on the dedicated `wordnet_dir` and `moby_path` fields rather than a fully uniform secondary-pack contract. | Future normalization or UX refactors can update one representation and accidentally leave the other behind unless this exception stays explicit. | later secondary lexical normalization and runtime-consumer reconciliation | `carry-forward` | When the secondary lexical family decision is made, decide whether these two sources become normal managed/manual pack entries everywhere or remain documented permanent exceptions. | `data_source_normalization_execution_order.md`, `feature_state_matrix.md`, or a later SP1/SP5 packet |
| `N-005` | 2026-04-18 | `SP2.2` extension SRS settings contract audit | `negative-path gap` | `saveSrsSettings()` currently performs profile persistence, runtime publish, and signal persistence as separate writes with no local compensation or partial-save recovery. A late failure can therefore leave runtime/profile fields updated while the signal payload remains stale. | This is hard to notice on the happy path today, but it becomes more important as more profile fields or UX controls are added to the save flow. | later SRS save lifecycle / failure-handling review | `carry-forward` | Decide in a later SP2 lifecycle slice whether the save path should become transactional, reordered, or more explicit about partial-write failure handling before broadening the editable signal surface. | later SP2 packet or `feature_state_matrix.md` if current truth needs to mention partial-save behavior |
| `N-006` | 2026-04-18 | `D3` active inventory persistence audit | `negative-path gap` | Explicit active inventory resolution is intentionally forgiving: missing inventory falls back to store-derived membership and stale inventory ids are silently dropped during resolution. Current observability mainly comes from runtime diagnostics and write-path backfill rather than a dedicated drift-repair signal. | This matters because later lifecycle or UX work can accidentally treat inventory as fully authoritative when the current model is closer to a soft cache with selective self-healing behavior. | later inventory lifecycle / observability review across D6-D7 and SP2 | `carry-forward` | Decide in a later lifecycle slice whether stronger repair/reporting semantics are needed or whether the forgiving model should simply stay explicit in canonical docs and diagnostics. | later D6/D7 packet, `feature_state_matrix.md`, or SRS runtime docs if current truth needs stronger visibility |
| `N-007` | 2026-04-18 | D7-D8 synthesis checkpoint | `false-green evidence` | Two recent seams showed the same pattern: present-tense validation claims were stronger than the committed direct evidence behind them. D7 needed explicit LP E2E assertions for manifest-family coherence, and D8 found a runbook note already citing `core/tests/dev/test_extension_srs_action_workflows.py` before that test existed in-tree. | This matters because seam docs and checkpoint notes can look fully verified while still relying on implicit coverage or local-only test state. | `G2` evidence hygiene and future seam checkpoint notes | `carry-forward` | When a seam doc cites a validation bundle, prefer committed seam-local tests or assertions over implied coverage, and audit older checkpoint docs for similar doc-ahead-of-evidence cases during `G2`. | `project_integrity_secondary_pass_plan.md`, later `G2` packet, or checkpoint docs that still cite implicit coverage |
| `N-008` | 2026-04-18 | `E1.1` translation-pack tooling holdout audit | `contract mismatch` | `rulegen_probe_words.py` still presents a more path-shaped developer surface than the benchmark/runtime seams: its CLI/help/output remain centered on resolved raw dictionary paths, while the downstream pair configs still use provider-shaped field names such as `freedict_*` below the current split. | This matters because later UX or docs work could mistake those local probe/adaptor names for the real managed-pack contract even though runtime and benchmark artifacts are already more manifest/pack-id oriented. | later `E4` UI-contract cleanup plus `F7` / `F11` structural follow-through | `carry-forward` | When the probe split resumes, decide whether the script should surface pack-id/provider metadata directly or explicitly keep the path-oriented view as a manual/debug layer only. | `project_integrity_e1_translation_pack_holdout_packet.md`, `data_source_normalization_execution_order.md`, or a later `E4`/`F7` packet |
| `N-009` | 2026-04-18 | `E2.1` frequency-pack tooling and diagnostics audit | `contract mismatch` | Helper CLI/native-host execution APIs still use the path-first `set_source_db` field name even though settings persistence and runtime diagnostics now expose frequency-pack identity separately. | This matters because later docs or UI cleanup can over-read `set_source_db` as the canonical managed frequency contract when it is really an execution-layer file override. | later `E4` installed-vs-manual cleanup plus possible helper API cleanup in `F12` | `carry-forward` | Decide later whether execution surfaces should gain pack-id-aware overrides or whether `set_source_db` should remain explicitly documented as a manual/debug compatibility input only. | `project_integrity_e2_frequency_pack_holdout_packet.md`, `feature_state_matrix.md`, or a later `E4`/`F12` packet |
| `N-010` | 2026-04-18 | `E4.1` installed/manual contract cleanup | `contract mismatch` | The extension-side SRS action formatters still print raw `set_source_db` lines in preflight and diagnostics output without the same explicit “installed packs by default / manual override” framing now used in helper CLI copy and settings surfaces. | This matters because operator-facing diagnostics can still read as path-first even though the underlying settings/runtime contract is pack-first for managed installs. | later extension diagnostics wording follow-through, likely alongside `F14` controller cleanup | `carry-forward` | When the SRS action formatter/controller files settle, decide whether to relabel the line, annotate it as a manual override, or pair it with the pack-identity fields already available in diagnostics. | later `E4`/`F14` packet, extension diagnostics copy, or `feature_state_matrix.md` if current truth needs stronger wording |
