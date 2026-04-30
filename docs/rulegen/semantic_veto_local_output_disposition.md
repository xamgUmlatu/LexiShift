# Semantic Veto Local Output Disposition

Status: current reference
Role: Integrity audit snapshot
Last updated: 2026-05-01
Last verified: 2026-05-01 against `git status --short`,
`git ls-files --others --exclude-standard`, exact-reference searches, and JSON
parse checks for preserved draft inputs

## Purpose

This pass classifies the remaining dirty and untracked semantic-veto generated
outputs without letting local `latest` reports steer runtime or promotion
claims. It does not rerun semantic evidence and does not change the
browser/helper runtime path.

## Disposition Summary

Committed historical inputs:

- `14` previously untracked wave2 through wave5 draft datasets and queues under
  `docs/test_outputs/experiments/semantic_non_v10_wave_drafts/`.
- Reason: tracked historical reports, heldout case files, or harness defaults
  reference these files by path. Keeping the reports without the referenced
  inputs leaves historical evidence non-reproducible.
- Authority: historical or seed support only. These files do not steer the
  current candidate and do not promote any runtime policy.
- Manifest:
  `docs/test_inputs/semantic_veto_wave2_wave5_draft_input_manifest_en_es.json`.

Left unstaged as local generated-output churn:

- `12` tracked wave5 source-portfolio files:
  - `4` normalized-evidence JSON files under
    `docs/test_outputs/experiments/semantic_example_frame_batches/`
  - `8` source-admission sidecar JSON/Markdown reports under
    `docs/test_outputs/semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest_*`
- Reason: the sidecar report deltas are timestamp-only, while the normalized
  evidence diffs are large generated-output reordering/churn. Wave5 is
  historical seed context in this workstream, so this pass does not commit those
  local rerun artifacts.
- Future action: if wave5 is revisited, regenerate and commit the whole wave5
  source-portfolio cycle deliberately, with the archive ledger updated at the
  same time.

Left untracked as local-only wave6 comparator output:

- `14` untracked wave6 translation-sense and alternate-phrase comparator
  JSON/Markdown reports under `docs/test_outputs/`.
- Reason: exact-reference searches found no committed doc, registry, test, or
  script reference to these filenames. The selected wave6 evidence needed by
  current methodology wording was committed in the preceding methodology
  reconciliation pass.
- Future action: regenerate or commit these only if a future research task
  explicitly reopens the translation-sense or alternate-phrase comparator lane.

Out of semantic-veto scope:

- `6` generic repo-health, feature-state, rulegen benchmark, and benchmark
  triage outputs remain modified.
- Reason: they are not semantic-veto authority and should be handled by their
  owning project-health or rulegen audit flow.

## Preserved Research Boundary

The next semantic-veto research lane remains
`wave7_active_signal_and_rescue_split`. This disposition pass only makes local
artifact authority explicit. It does not advance wave7 remediation and does not
change the current research candidate.
