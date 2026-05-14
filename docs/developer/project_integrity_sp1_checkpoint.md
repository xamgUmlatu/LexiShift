# SP1 Checkpoint

Status: active checkpoint
Role: Mixed
Last updated: 2026-04-18
Last verified: 2026-04-18 after `SP1.8` validation and commit
Purpose: summarize what the `SP1` secondary-pass track covered, what it fixed, what it verified, and what still remains before treating the track as effectively complete
Source-of-truth: checkpoint only; executable truth still lives in code, tests, per-slice packets, and the validation runs attached to those slices
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_sp1_resource_settings_packet.md`
- `project_integrity_sp1_panel_state_packet.md`
- `project_integrity_sp1_embedding_panel_packet.md`
- `project_integrity_sp1_translation_frequency_panel_packet.md`
- `project_integrity_sp1_secondary_language_resources_packet.md`
- `project_integrity_sp1_embedding_runtime_resolution_packet.md`
- `project_integrity_sp1_translation_runtime_resolution_packet.md`
- `project_integrity_sp1_frequency_runtime_resolution_packet.md`

## Scope

`SP1` was the resource-settings and round-trip correctness track from the secondary-pass plan.

Primary question:

"Can managed and manual resource configuration survive save/load/use/delete flows without identity drift?"

The track was meant to cover four broad areas:

1. settings serialization authority
2. managed-id vs manual-path separation
3. install/unlink/delete conversion lifecycle
4. panel-state/UI snapshot coherence after reload

By the end of this checkpoint, the track also explicitly covers the consumer side:

- embedding runtime resolution
- translation runtime resolution
- frequency runtime resolution

That matters because SP1 would have been incomplete if we only proved persistence while leaving actual runtime consumers on path-order assumptions.

## Slice Summary

| Slice | Packet | Outcome | Status |
|---|---|---|---|
| `SP1.1` | `project_integrity_sp1_resource_settings_packet.md` | Verified settings serialization/import-export/state-migration authority for the managed-id vs manual-path split. | `complete` |
| `SP1.2` | `project_integrity_sp1_panel_state_packet.md` | Fixed a real lifecycle defect: embedding delete now clears stale pair activation even when files are already missing. | `complete` |
| `SP1.3` | `project_integrity_sp1_embedding_panel_packet.md` | Verified the in-flight embedding panel-state split for seed/auto-link/activate behavior and downstream agreement. | `complete` |
| `SP1.4` | `project_integrity_sp1_translation_frequency_panel_packet.md` | Verified translation/frequency unlink/delete lifecycle parity and raised evidence to match the embedding seam. | `complete` |
| `SP1.5` | `project_integrity_sp1_secondary_language_resources_packet.md` | Verified the transitional compatibility contract for `wordnet-en` / `moby-en`, including legacy-field seeding and binding-map precedence. | `complete` |
| `SP1.6` | `project_integrity_sp1_embedding_runtime_resolution_packet.md` | Verified manifest-first embedding runtime resolution, configured fallback, and duplicate suppression. | `complete` |
| `SP1.7` | `project_integrity_sp1_translation_runtime_resolution_packet.md` | Found and fixed a real authority-order defect: managed translation artifacts now override stale same-key configured paths. | `complete` |
| `SP1.8` | `project_integrity_sp1_frequency_runtime_resolution_packet.md` | Verified managed-first frequency runtime resolution and configured fallback at both helper and SRS consumer layers. | `complete` |

## What SP1 Accomplished

At a practical level, `SP1` now gives us a much firmer contract for future resource and UX work:

1. Managed resource identity is now explicitly pack-id-first across persistence, panel state, and runtime consumers.
2. Manual/external paths are still supported, but their role is now clearer: compatibility/import surfaces, not the primary authority for managed installs.
3. Delete/unlink flows have direct lifecycle coverage instead of relying on happy-path assumptions.
4. Translation, frequency, and embedding consumers now all have explicit managed-vs-manual precedence evidence.
5. The remaining mixed secondary lexical surface is now documented as transitional rather than accidentally inconsistent.

In terms of actual defects found during `SP1`, two mattered:

1. `SP1.2`: embedding delete could leave stale pair-level activation behind when local files were already gone.
2. `SP1.7`: translation runtime resolution could let a stale same-key configured path override a managed installed artifact.

Both were fixed and verified during the track.

## Checklist Coverage

The original manual scenario checklist from the secondary-pass plan is now covered as follows:

| Checklist item | Covered by |
|---|---|
| Save managed translation/frequency/embedding selections and confirm ids survive without path drift. | `SP1.1`, `SP1.3`, state-migration and settings-persistence tests |
| Save a mixed managed/manual configuration and confirm the two modes remain distinguishable. | `SP1.1`, `SP1.2`, `SP1.4`, `SP1.5` |
| Unlink/delete installed packs and confirm stale UI/config state is gone. | `SP1.2`, `SP1.3`, `SP1.4` |
| Run serialize -> deserialize -> serialize style checks where practical. | `SP1.1` |
| Verify runtime consumers resolve the same resource identity the UI persisted. | `SP1.6`, `SP1.7`, `SP1.8` |

## Remaining Work

There is no obvious unresolved `SP1` seam left from the original track definition.

Said more plainly:

- the persistence side is covered
- the panel/delete/unlink side is covered
- the runtime consumer side is covered

So `SP1` is effectively complete enough to stop slicing and move to `SP2`.

## SP1-Adjacent Carry-Forward

One meaningful carry-forward remains nearby, but it is not a reason to keep `SP1` open:

- `N-004` in `project_integrity_secondary_pass_notes.md`:
  `wordnet-en` and `moby-en` still bridge the newer shared language-resource binding surface and the older dedicated `wordnet_dir` / `moby_path` fields.

That is real and worth keeping explicit, but it is better treated as:

- a later secondary lexical normalization decision,
- a doc/state reconciliation task,
- or a future resource-architecture pass,

not as an unfinished resource-integrity seam blocking the end of `SP1`.

## Recommended Status

Recommended interpretation after this checkpoint:

- `SP1`: `complete for the current secondary-pass purpose`
- next active track: `SP2`

If we want one more administrative closeout step, it should be a planning/state-doc update rather than another SP1 code seam.
