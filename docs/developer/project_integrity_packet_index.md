# Project Integrity Packet Index

Status: active grouping index
Role: Planning / WIP
Last updated: 2026-05-14
Last verified: 2026-05-14 Lane 1 packet exact-reference searches through SP7; packet contents not re-audited
Purpose: group the project-integrity packet docs so they can remain discoverable as evidence snapshots without being mistaken for current source-of-truth docs
Source-of-truth: grouping index only; current behavior truth still lives in code, tests, generated evidence, `feature_state_matrix.md`, and the canonical domain docs.

## Scope

This index covers the `51` `docs/developer/project_integrity_*_packet.md`
files that currently carry `Role: Packet / WIP`.

This pass does not:

1. move packet files,
2. relabel packet files,
3. archive packet files,
4. change any packet status claim,
5. replace exact packet evidence with this index.

The packet files are still the detailed evidence snapshots. This index is only
the grouping layer needed before later archive, move, or role-normalization
work.

## Cleanup Rules

Before any later move or archive pass:

1. run exact-reference searches for every proposed file move,
2. preserve cross-packet links or update them in the same slice,
3. migrate surviving current-truth claims into canonical docs before demoting a
   packet,
4. leave generated artifacts as evidence, not architecture authority,
5. keep packet relabeling separate from packet file moves.

Recommended role target after grouping:

- keep packet contents as historical slice evidence,
- convert `Role: Packet / WIP` to `Role: Archive / legacy` only after a packet's
  current value has been routed into a maintained doc,
- use `Role: Mixed` only for packets that remain a current operational
  checkpoint after re-audit.

## Packet Groups

### B: Semantic Baseline And Publication Boundary

These packets record early semantic publication/runtime readiness boundaries.

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_b4_semantic_diagnostics_packet.md` | active packet | Semantic diagnostics contract evidence. |
| `project_integrity_b5_en_es_poc_boundary_packet.md` | active packet | `en-es` publication PoC boundary evidence. |
| `project_integrity_b6_semantic_roadmap_pruning_packet.md` | active packet | Semantic roadmap/doc pruning evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_g2_evidence_wording_packet.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - this index.
- Current recommendation: keep in place until the broader semantic evidence
  routing/archive pass decides whether the B packets should become
  `Archive / legacy` or stay as indexed packet evidence.
- Reason: the B packets are still cited as evidence for later `G2` false-green
  cleanup and secondary-pass notes, so a file move would create link churn with
  little immediate product value.

### D: Semantic Admission And SRS Reconciliation

These packets record the semantic-admission and SRS reconciliation track.

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_d1_semantic_baseline_freeze_packet.md` | active packet | Baseline freeze evidence. |
| `project_integrity_d2_admission_core_packet.md` | active packet | Admission core evidence. |
| `project_integrity_d3_active_inventory_packet.md` | active packet | Active inventory persistence evidence. |
| `project_integrity_d4_helper_preview_rebalance_packet.md` | active packet | Helper preview/rebalance evidence. |
| `project_integrity_d5_initialize_reconciliation_packet.md` | active packet | Initialize reconciliation evidence. |
| `project_integrity_d6_refresh_reset_reconciliation_packet.md` | active packet | Refresh/reset reconciliation evidence. |
| `project_integrity_d7_runtime_diagnostics_packet.md` | active packet | Runtime diagnostics evidence. |
| `project_integrity_d8_extension_ui_wiring_packet.md` | active packet | Extension/UI admission wiring evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_g2_evidence_wording_packet.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - `project_integrity_sp2_inventory_observability_packet.md`,
  - `project_integrity_sp3_publication_family_packet.md`,
  - `project_integrity_f14_srs_action_workflow_split_packet.md`,
  - `project_integrity_sp5_srs_action_transitions_packet.md`,
  - this index.
- Current recommendation: keep the D packets together in place until the SRS
  admission/semantic-admission current truth has a single maintained routing
  note.
- Reason: D packets are a sequential admission-port chain. Moving only the
  lower-reference files would make the chain harder to follow, while moving the
  whole group would require coordinated updates to later SP/F/G packet evidence
  links.

### E: Data-Source Holdouts And Installed/Manual Contracts

These packets record data-source holdout checks and installed-vs-manual seams.

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_e1_translation_heuristics_packet.md` | active packet | Translation heuristic follow-up evidence. |
| `project_integrity_e1_translation_pack_holdout_packet.md` | active packet | Translation-pack holdout evidence. |
| `project_integrity_e2_frequency_pack_holdout_packet.md` | active packet | Frequency-pack holdout evidence. |
| `project_integrity_e3_embedding_pack_holdout_packet.md` | active packet | Embedding-pack holdout evidence. |
| `project_integrity_e4_installed_manual_contract_packet.md` | active packet | Installed-vs-manual contract evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_e1_translation_heuristics_packet.md`,
  - `project_integrity_n015_translation_gloss_locator_packet.md`,
  - this index.
- Current recommendation: keep the E packets in place until the broader
  data-source normalization and pack-lifecycle cleanup pass decides whether
  holdout packets should become archived evidence.
- Reason: most of the group is low-reference, but E1 has follow-up links into
  translation heuristic and locator-normalization evidence. Keeping the group
  together avoids splitting the data-source holdout history across locations.

### F: Loader And Workflow Splits

These packets record loader convergence and action-workflow splits.

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_f11_dict_loader_split_packet.md` | active packet | Dictionary loader split evidence. |
| `project_integrity_f11_grouped_loader_convergence_packet.md` | active packet | Grouped loader convergence evidence. |
| `project_integrity_f14_srs_action_workflow_split_packet.md` | active packet | SRS action workflow split evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_f11_grouped_loader_convergence_packet.md`,
  - `project_integrity_sp5_options_bootstrap_packet.md`,
  - `project_integrity_sp5_srs_action_transitions_packet.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - this index.
- Current recommendation: keep the F packets in place until loader/workflow
  consolidation evidence is routed through a maintained current doc or archived
  as a group.
- Reason: F11 has a direct resolved-note trail in secondary-pass notes, and F14
  is a dependency marker for later SP5 extension workflow packets.

### G: Evidence Wording And Governance

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_g2_evidence_wording_packet.md` | active packet | Evidence wording and false-green cleanup evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this packet without updating references in:
  - the B-packet disposition notes above,
  - the D-packet disposition notes above,
  - `project_integrity_secondary_pass_notes.md`,
  - this index.
- Current recommendation: keep in place until the broader packet archive pass
  has a stable destination for evidence-hygiene packets.
- Reason: G2 is the current evidence-wording cleanup anchor for multiple older
  packet groups. Moving it before the larger packet archive decision would add
  churn to the very references that explain why the older packets are evidence
  snapshots.

### N: Data-Source Naming And Locator Normalization

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_n014_pair_config_translation_fields_packet.md` | active packet | Pair-config translation field naming evidence. |
| `project_integrity_n015_translation_gloss_locator_packet.md` | active packet | Translation-gloss locator naming evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_n014_pair_config_translation_fields_packet.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - this index.
- Current recommendation: keep the N packets in place until provider-shaped
  naming history is either summarized in the data-source normalization docs or
  archived with adjacent E packet evidence.
- Reason: N014 and N015 are a small sequential normalization pair, and N015 also
  bridges back to the E1 translation heuristic cleanup.

### SP1: Resource Settings And Runtime Resolution

These packets record secondary-pass resource panel and runtime-resolution work.
The related non-packet checkpoint is `project_integrity_sp1_checkpoint.md`.

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp1_data_source_download_packet.md` | planned packet | Data-source download lifecycle planning. |
| `project_integrity_sp1_embedding_panel_packet.md` | active packet | Embedding panel-state evidence. |
| `project_integrity_sp1_embedding_runtime_resolution_packet.md` | active packet | Embedding runtime resolution evidence. |
| `project_integrity_sp1_frequency_runtime_resolution_packet.md` | active packet | Frequency runtime resolution evidence. |
| `project_integrity_sp1_panel_state_packet.md` | active packet | Panel-state lifecycle evidence. |
| `project_integrity_sp1_resource_settings_packet.md` | active packet | Resource settings evidence. |
| `project_integrity_sp1_secondary_language_resources_packet.md` | active packet | Secondary language-resource evidence. |
| `project_integrity_sp1_secondary_lexical_runtime_packet.md` | active packet | Secondary lexical runtime evidence. |
| `project_integrity_sp1_translation_frequency_panel_packet.md` | active packet | Translation/frequency panel evidence. |
| `project_integrity_sp1_translation_runtime_resolution_packet.md` | active packet | Translation runtime resolution evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_sp1_checkpoint.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - `data_source_normalization_architecture.md`,
  - this index.
- Current recommendation: keep the SP1 packets in place with
  `project_integrity_sp1_checkpoint.md` as the current grouping/summary layer.
- Reason: SP1 already has a non-packet checkpoint that references nearly every
  SP1 packet. Moving the packet files without deciding whether the checkpoint
  becomes the long-term index would create avoidable link churn.

### SP2: SRS Policy, Profile, And Observability

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp2_confidence_gating_packet.md` | active packet | Confidence gating evidence. |
| `project_integrity_sp2_due_aware_serving_packet.md` | active packet | Due-aware serving boundary evidence. |
| `project_integrity_sp2_extension_srs_settings_packet.md` | active packet | Extension SRS settings evidence. |
| `project_integrity_sp2_inventory_observability_packet.md` | active packet | Inventory observability evidence. |
| `project_integrity_sp2_planner_strategy_packet.md` | active packet | Planner strategy evidence. |
| `project_integrity_sp2_profile_schema_packet.md` | active packet | Profile schema evidence. |
| `project_integrity_sp2_settings_save_failure_packet.md` | active packet | Settings-save failure evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_secondary_pass_notes.md`,
  - `feature_state_matrix.md`,
  - `project_integrity_sp2_settings_save_failure_packet.md`,
  - the D-packet disposition notes above,
  - this index.
- Current recommendation: keep the SP2 packets together in place until SRS
  policy/profile/observability truth is routed through maintained SRS docs and
  feature-state entries.
- Reason: SP2 packets are still cited as the evidence trail for due-aware
  serving, confidence gating, settings-save behavior, and active-inventory
  observability boundaries.

### SP3: Semantic Publication And Schema Boundaries

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp3_fallback_gating_packet.md` | active packet | Fallback/gating evidence. |
| `project_integrity_sp3_publication_family_packet.md` | active packet | Publication-family coherence evidence. |
| `project_integrity_sp3_schema_reference_packet.md` | active packet | Schema-reference reconciliation evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_secondary_pass_notes.md`,
  - `project_integrity_sp3_schema_reference_packet.md`,
  - `project_integrity_sp6_semantic_evidence_routing_packet.md`,
  - the D-packet disposition notes above,
  - this index.
- Current recommendation: keep the SP3 packets in place until semantic
  publication/schema current truth is fully routed through the maintained
  semantic contract docs.
- Reason: SP3 is the bridge between semantic fallback/gating evidence and later
  schema/reference cleanup, so moving it before semantic authority mapping would
  obscure why older semantic docs were reclassified.

### SP5: Extension Workflow Surfaces

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp5_dom_scan_packet.md` | active packet | DOM scan evidence. |
| `project_integrity_sp5_options_bootstrap_packet.md` | active packet | Options bootstrap evidence. |
| `project_integrity_sp5_share_import_packet.md` | active packet | Share/import evidence. |
| `project_integrity_sp5_srs_action_transitions_packet.md` | active packet | SRS action transition evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_sp6_extension_doc_metadata_packet.md`,
  - `project_integrity_sp6_feature_state_refresh_packet.md`,
  - `project_integrity_sp7_share_center_compatibility_copy_packet.md`,
  - `project_integrity_secondary_pass_notes.md`,
  - the F-packet disposition notes above,
  - this index.
- Current recommendation: keep the SP5 packets in place until extension workflow
  current truth is consolidated through architecture docs and feature-state
  entries.
- Reason: SP5 packets are dependency markers for later SP6 and SP7 cleanup.
  Moving them now would require coordinated updates across extension-doc and
  Share Center evidence chains.

### SP6: Extension Docs And Semantic Evidence Routing

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp6_extension_doc_metadata_packet.md` | active packet | Extension doc metadata evidence. |
| `project_integrity_sp6_feature_state_refresh_packet.md` | active packet | Feature-state refresh evidence. |
| `project_integrity_sp6_semantic_evidence_routing_packet.md` | active packet | Semantic evidence routing evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_secondary_pass_notes.md`,
  - `feature_state_matrix.md`,
  - `project_integrity_sp6_extension_doc_metadata_packet.md`,
  - this index.
- Current recommendation: keep the SP6 packets in place until the extension doc
  metadata refresh and semantic evidence-routing cleanup are either reflected in
  maintained architecture docs or archived as a coordinated SP6 group.
- Reason: SP6 is the main bridge from SP5 implementation evidence into current
  architecture/feature-state cleanup.

### SP7: Share-Center Copy And SRS Quality Artifacts

| Packet | Current Status | Note |
| --- | --- | --- |
| `project_integrity_sp7_share_center_compatibility_copy_packet.md` | active packet | Share Center compatibility-copy evidence. |
| `project_integrity_sp7_srs_quality_artifact_packet.md` | active packet | SRS quality artifact normalization evidence. |

Disposition prep:

- Exact-reference search completed: 2026-05-14.
- Do not move this group without updating references in:
  - `project_integrity_secondary_pass_notes.md`,
  - `project_integrity_sp7_share_center_compatibility_copy_packet.md`,
  - this index.
- Current recommendation: keep the SP7 packets in place until Share Center copy
  and SRS quality artifact-normalization truth are either reflected in maintained
  docs or archived with the wider secondary-pass packet set.
- Reason: SP7 resolves notes raised by earlier SP5/SP6 work, so it should not be
  separated from the secondary-pass evidence chain before a broader archive
  destination is chosen.

## Next Cleanup Slice

Recommended next step:

1. exact-reference search for one packet group,
2. decide whether that group should stay in place with normalized roles or move
   under a packet/evidence folder,
3. update this index and all affected links in the same slice,
4. run `python3 scripts/dev/check_doc_references.py` and `git diff --check`.
