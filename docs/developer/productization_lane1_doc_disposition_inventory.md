# Productization Lane 1 Documentation Disposition Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 doc-reference check, state check, and diff hygiene after LP supersession review
Purpose: record the first Lane 1 inventory for redundant, stale, mixed-status, or weakly classified documentation before any broad archive or deletion pass
Source-of-truth: inventory only; current behavior still lives in source code, tests, generated evidence, `feature_state_matrix.md`, and canonical domain docs.
Related docs:
- `productization_closure_roadmap.md`
- `documentation_governance.md`
- `documentation_grooming_workstream.md`
- `project_integrity_stabilization_runbook.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`

## Slice Scope

Lane: Lane 1, redundant and stale documentation.

Slice: first repo-wide documentation disposition inventory.

This pass does not archive, delete, or rewrite domain docs. It identifies the
first cleanup queues so future passes can work deliberately.

Explicitly out of scope:

1. moving the `project_integrity_*_packet.md` files,
2. retiring old rulegen or semantic-veto docs,
3. changing canonical routing policy,
4. changing runtime behavior or generated evidence,
5. treating this inventory as implementation truth.

## Scan Method

The scan covered Markdown docs under `docs/`, excluding generated and build
output folders:

- excluded: `docs/test_outputs/`,
- excluded: `docs/_site/`,
- excluded: `docs/.jekyll-cache/`.

Commands used during the inventory:

```bash
find docs -path docs/_site -prune -o -path docs/.jekyll-cache -prune \
  -o -path docs/test_outputs -prune -o -name '*.md' -print | sort

rg -n "^Status:|^Role:|^Last updated:|^Last verified:|^Source-of-truth:|^Purpose:" \
  docs --glob '*.md' --glob '!_site/**' --glob '!test_outputs/**' \
  --glob '!.jekyll-cache/**'
```

Summary from the first scan:

| Metric | Count | Interpretation |
| --- | ---: | --- |
| Non-generated Markdown docs scanned | 194 | Broad enough for an inventory pass, not a full truth audit. |
| Docs under `docs/developer/` | 82 | Developer root is carrying many slice packets. |
| Docs under `docs/rulegen/` | 48 | Rulegen/semantic-veto has the densest planning and evidence-reference surface. |
| Docs missing `Role:` metadata | 55 | Metadata normalization is a safe first cleanup queue. |
| Docs with non-governance role labels | 82 | Many docs predate the exact role vocabulary in `documentation_governance.md`. |
| `project_integrity_*` packet docs with `Role: Packet / WIP` | 51 | Useful evidence packets, but not cleanly grouped or role-normalized. |
| Docs checked by `check_doc_references.py` in this checkout | 13 | The current automated gate covers routing/policy docs, not the full doc tree. |

## Disposition Labels

Use these labels in follow-up Lane 1 passes:

| Label | Meaning |
| --- | --- |
| Keep current | Canonical or operational doc that should remain in the normal routing path. |
| Normalize metadata | Useful doc with missing or non-standard metadata. |
| Group evidence | Evidence packet or checkpoint should remain available but move behind a clearer index or folder. |
| Archive review | Candidate for archive/demotion after surviving value is migrated. |
| Supersession review | Candidate overlaps with newer docs and needs an explicit winner/loser map. |
| Site-route review | GitHub Pages or handbook page that should not be treated as developer authority by default. |
| Defer | Not enough evidence to move or demote in this slice. |

No `Delete` label is assigned in this first inventory. Deletion needs a later
exact-reference search and value-migration check.

## Domain Disposition Inventory

| Area | Current Read | Initial Disposition | Next Action |
| --- | --- | --- | --- |
| Root routing docs | `docs/README.md` is canonical and already sends contributors to current developer and architecture hubs. `docs/TODOs.md` lacks `Role:` metadata. | Keep current / Normalize metadata | Preserve routing. Add standard metadata to `TODOs.md` in a small metadata-only pass. |
| Developer hub docs | `docs/developer/README.md`, `developer_reference.md`, `local_setup.md`, `documentation_governance.md`, and `feature_state_matrix.md` are the current routing/status layer. | Keep current | Do not broaden their scope during Lane 1. Link only inventories that are actively useful. |
| Developer project-integrity packets | 51 packet docs sit directly under `docs/developer/` with `Role: Packet / WIP`; most are slice evidence, not current authority. A packet index now groups them without moving files. | Group evidence partial | Use `project_integrity_packet_index.md` before any packet move, archive, or mass role relabel. Keep code/test evidence links intact. |
| Developer planning docs | Several useful plans used non-standard roles, such as `roadmap / sequencing`, `ordered implementation plan`, or `practical sweep execution guide`. Non-packet developer planning docs now use governance-approved roles. | Normalize metadata complete for non-packet docs | Later cleanup can review whether any planning docs should be superseded, but do not change behavior claims without code/test evidence. |
| Architecture docs | `docs/architecture/README.md` already classifies implemented, mixed, and planning docs. Planning docs include `sync_design.md`, `popup_modules_settings_implementation_plan.md`, and `design_diagram_workplan.md`. | Keep current / Normalize metadata | Start with metadata and route freshness, not content rewrites. |
| GUI docs | GUI docs now have governance metadata and a dedicated authority map at `docs/gui/README.md`. `gui_current_structure.md` remains a dated snapshot, not current structure authority. | Normalize metadata complete / Supersession review complete | Use `docs/gui/README.md` before editing individual GUI docs. Verify behavior against `apps/gui/src/` and `apps/gui/tests/` before promoting snapshot/workstream text. |
| SRS docs | SRS docs now have governance metadata and a dedicated authority map at `docs/srs/README.md`. Several docs remain intentionally `Mixed` because they contain both current implementation notes and target-state planning. | Normalize metadata complete / Supersession review complete | Use `docs/srs/README.md` before editing individual SRS docs. Do not promote roadmap/schema claims without feature-state, code, test, or SRS harness evidence. |
| Rulegen core docs | Core docs such as `rule_generation_technical.md`, `synonym_generation_technical.md`, POS workstream docs, and congruity plans predate the governance metadata model. Missing-role and non-packet non-standard role labels now carry governance-approved roles. | Normalize metadata complete for non-packet docs | Do not edit rulegen claims without the rulegen quality loop when behavior-facing. |
| Rulegen reverse-check dated docs | The 2026-03-13 reverse-check docs are valuable history but read like workstream snapshots tied to older artifacts. The three dated `en-es` review snapshots now live under `docs/archive/rulegen/`; active policy/status remains in the rollout matrix, phase-1 spec, LP support guide, and feature-state ledger. | Archive move complete for dated `en-es` snapshots | Keep `reverse_check_rollout_matrix.md` and `reverse_check_scoring_phase1.md` in active rulegen docs unless a later pass creates a stronger current rulegen reference. |
| Semantic routing and semantic-veto docs | Existing docs already include artifact authority, archive consolidation, local-output disposition, denominator current state, and expansion planning. Missing-role and non-packet non-standard role labels now identify planning, runbook, mixed-reference, ledger, and current-reference scope. | Supersession review / metadata complete for non-packet docs | Build a semantic docs authority map before editing individual files. Preserve current denominator and active-only product posture. |
| Language-pair docs | Resource requirements, inventory matrices, setup checklists, and workstream roadmaps now have metadata and a dedicated authority map at `docs/language_pairs/README.md`. | Normalize metadata complete for non-packet docs / Supersession review complete | Use `docs/language_pairs/README.md` before editing individual LP docs. Keep status-sensitive LP claims routed through feature-state, code, tests, and generated audits. |
| Reference docs | `reference/schema.md`, `glossary.md`, and `theme_schema.md` lack governance metadata but are linked from routing docs. | Normalize metadata | Add exact role/source-of-truth metadata before content changes. |
| Runbooks | Runbooks are operationally useful but mostly lack role/status metadata. | Normalize metadata | Add standard metadata and verification commands where obvious. |
| Handbook and getting-started pages | These are GitHub Pages/user-facing entrypoints with Jekyll front matter, not developer source-of-truth docs. They now carry hidden governance comments so source readers see authority boundaries without adding visible site clutter. | Site-route review complete | Keep them out of developer authority paths unless explicitly routed as user docs. Re-audit page content separately if UI/command claims become release-facing. |
| `docs/test_inputs/**/README.md` | Test-input READMEs are local dataset/schema guides, not user or architecture docs. | Normalize metadata complete for missing-role READMEs | Keep implemented/default-on/verified state outside these READMEs; use feature-state and generated artifacts for status. |
| `docs/semantic_routing_html/README.md` | Auxiliary local preview guide for semantic-routing HTML pages. | Normalize metadata complete | Keep it as a preview runbook; semantic runtime truth remains in code, tests, and canonical semantic-veto docs. |

## First Cleanup Queue

### L1-A: Metadata Normalization Packet

Goal:
- add standard `Status`, `Role`, `Last updated`, `Purpose`, and
  `Source-of-truth` metadata where the doc is still clearly useful.

Start with:

1. root-level `TODOs.md`,
2. `docs/reference/*.md`,
3. `docs/runbooks/*.md`,
4. `docs/gui/*.md`,
5. `docs/srs/*.md`.

Progress:

- `L1-A.1` completed metadata-only normalization for:
  - `docs/TODOs.md`,
  - `docs/reference/glossary.md`,
  - `docs/reference/schema.md`,
  - `docs/reference/theme_schema.md`,
  - `docs/runbooks/app_size_reduction.md`,
  - `docs/runbooks/cws_upload_gate.md`,
  - `docs/runbooks/github_pages_setup.md`,
  - `docs/runbooks/helper_tray_debug_summary.md`,
  - `docs/runbooks/cws_preflight_reports/README.md`.
- Dated CWS preflight report files under `docs/runbooks/cws_preflight_reports/`
  are generated evidence snapshots and may be ignored locally; normalize the
  tracked report index rather than hand-editing ignored generated reports.
- After `L1-A.1`, the scanned docs missing `Role:` metadata dropped from `55`
  to `46`; the remaining count still includes the ignored generated CWS
  preflight snapshot.
- `L1-A.2` completed domain-adjacent metadata normalization for:
  - `docs/gui/gui_app_fix_workstream.md`,
  - `docs/gui/gui_current_structure.md`,
  - `docs/gui/gui_ux_decisions.md`,
  - `docs/gui/profile_ruleset_refactor_notes.md`.
- GUI labels were applied conservatively: the older structure doc is a
  review-required snapshot, the UX decision log is decision rationale, and the
  workstream/refactor notes are planning surfaces rather than current runtime
  authority.
- After `L1-A.2`, the scanned docs missing `Role:` metadata dropped from `46`
  to `42`; the remaining count still includes the ignored generated CWS
  preflight snapshot.
- `L1-A.3` completed SRS metadata normalization for:
  - `docs/srs/srs_curriculum_notes.md`,
  - `docs/srs/srs_hybrid_model_technical.md`,
  - `docs/srs/srs_practice_layer_design.md`,
  - `docs/srs/srs_profile_schema.md`,
  - `docs/srs/srs_roadmap.md`,
  - `docs/srs/srs_schema.md`,
  - `docs/srs/srs_selector_technical.md`,
  - `docs/srs/srs_set_planning_technical.md`.
- SRS labels were applied conservatively after an SRS-adjacent doc/code/test
  read: schema, roadmap, practice, hybrid-model, profile-schema, and
  set-planning docs remain `Mixed`; selector and curriculum docs remain
  `Planning / WIP`.
- After `L1-A.3`, the scanned docs missing `Role:` metadata dropped from `42`
  to `34`; the remaining count still includes the ignored generated CWS
  preflight snapshot.

Validation:

```bash
python3 scripts/dev/check_doc_references.py
git diff --check
```

### L1-B: Developer Packet Grouping Plan

Goal:
- keep project-integrity packets available while making it obvious that they are
  slice evidence, not current runtime authority.

Required pre-move checks:

1. exact-reference search for each packet path,
2. decide whether to create a packet index before moving files,
3. update routing docs only after the target structure is clear,
4. run doc-reference checks after every move batch.

Do not start by moving all 51 packet files.

Progress:

- `L1-B.1` created `docs/developer/project_integrity_packet_index.md`.
- The index groups all `51` `project_integrity_*_packet.md` files by workstream
  family without moving, archiving, or relabeling the packet files.
- The index records cleanup rules for later packet moves:
  - exact-reference search before each move,
  - preserve cross-packet links,
  - migrate surviving current truth into canonical docs before demotion,
  - keep packet role normalization separate from file moves.
- `L1-B.2` completed exact-reference disposition prep for the B-packet group:
  - `project_integrity_b4_semantic_diagnostics_packet.md`,
  - `project_integrity_b5_en_es_poc_boundary_packet.md`,
  - `project_integrity_b6_semantic_roadmap_pruning_packet.md`.
- Result: keep the B packets in place for now. They are referenced by
  `project_integrity_g2_evidence_wording_packet.md` and
  `project_integrity_secondary_pass_notes.md`, so any future move should update
  those links in the same slice. The packet index records this boundary.
- `L1-B.3` completed exact-reference disposition prep for the D-packet group:
  - `project_integrity_d1_semantic_baseline_freeze_packet.md`,
  - `project_integrity_d2_admission_core_packet.md`,
  - `project_integrity_d3_active_inventory_packet.md`,
  - `project_integrity_d4_helper_preview_rebalance_packet.md`,
  - `project_integrity_d5_initialize_reconciliation_packet.md`,
  - `project_integrity_d6_refresh_reset_reconciliation_packet.md`,
  - `project_integrity_d7_runtime_diagnostics_packet.md`,
  - `project_integrity_d8_extension_ui_wiring_packet.md`.
- Result: keep the D packets together in place for now. Several are referenced
  by later SP/F/G packet evidence and secondary-pass notes, and splitting the
  group would make the sequential admission-port chain harder to follow. The
  packet index records the affected references.
- `L1-B.4` completed exact-reference disposition prep for the E data-source
  holdout packet group:
  - `project_integrity_e1_translation_heuristics_packet.md`,
  - `project_integrity_e1_translation_pack_holdout_packet.md`,
  - `project_integrity_e2_frequency_pack_holdout_packet.md`,
  - `project_integrity_e3_embedding_pack_holdout_packet.md`,
  - `project_integrity_e4_installed_manual_contract_packet.md`.
- Result: keep the E packets together in place for now. E1 links forward into
  N015 and back to the translation-pack holdout packet, so splitting low-ref
  E2-E4 from E1 would make the data-source holdout history harder to follow.
- `L1-B.5` completed exact-reference disposition prep for the F loader/workflow
  packet group:
  - `project_integrity_f11_dict_loader_split_packet.md`,
  - `project_integrity_f11_grouped_loader_convergence_packet.md`,
  - `project_integrity_f14_srs_action_workflow_split_packet.md`.
- Result: keep the F packets in place for now. F11 is referenced by
  secondary-pass notes, and F14 is referenced by later SP5 workflow packets.
- `L1-B.6` completed exact-reference disposition prep for the G/N governance
  and naming-normalization packet groups:
  - `project_integrity_g2_evidence_wording_packet.md`,
  - `project_integrity_n014_pair_config_translation_fields_packet.md`,
  - `project_integrity_n015_translation_gloss_locator_packet.md`.
- Result: keep these packets in place for now. G2 is the evidence-wording anchor
  for older packet groups, and N014/N015 are a sequential normalization pair
  linked from secondary-pass notes and E1 follow-up evidence.
- `L1-B.7` completed exact-reference disposition prep for the SP1 resource
  settings/runtime-resolution packet group.
- Result: keep SP1 packets in place with `project_integrity_sp1_checkpoint.md`
  as the current grouping layer. The checkpoint and secondary-pass notes
  reference most of this group directly, so a move should wait until the packet
  archive destination and checkpoint role are decided together.
- `L1-B.8` completed exact-reference disposition prep for the SP2 SRS
  policy/profile/observability packet group.
- Result: keep SP2 packets in place for now. They are still cited as evidence
  for due-aware serving, confidence gating, settings-save behavior, and active
  inventory observability boundaries in secondary-pass notes, feature-state
  entries, and adjacent packets.
- `L1-B.9` completed exact-reference disposition prep for SP3, SP5, SP6, and
  SP7 packet groups.
- Result: keep these SP packets in place for now. SP3 bridges semantic
  fallback/schema cleanup into later semantic evidence routing, SP5 feeds SP6
  and SP7 extension/share cleanup, SP6 bridges extension docs and feature-state
  refreshes, and SP7 resolves earlier Share Center/SRS quality artifact notes.
  Moving them safely requires a coordinated secondary-pass packet archive
  target, not one-off file moves.

### L1-C: Semantic/Rulegen Authority Map

Goal:
- prevent dense semantic-veto and rulegen planning docs from competing with
  current denominator, runtime, and expansion posture.

Start from:

1. `docs/rulegen/semantic_veto_artifact_authority_audit.md`,
2. `docs/rulegen/semantic_veto_archive_consolidation.md`,
3. `docs/rulegen/semantic_veto_denominator_current_state.md`,
4. `docs/rulegen/semantic_veto_srs_corpus_expansion_plan.md`,
5. `docs/developer/feature_state_matrix.md`.

Output:
- a map of current authority, historical support, planning, and generated
  evidence pointers.

Progress:

- `L1-C.1` added `docs/rulegen/semantic_rulegen_authority_map.md` as the
  current routing layer for semantic-veto, semantic-routing, and rulegen cleanup
  claims.
- Result: do not edit individual semantic/rulegen docs by "newest or most
  detailed wins." Route each claim by type:
  - current product status through `feature_state_matrix.md`,
  - current semantic-veto denominator through
    `semantic_veto_denominator_current_state.md`,
  - corpus-expansion planning through
    `semantic_veto_srs_corpus_expansion_plan.md`,
  - artifact classification through the artifact authority/reconciliation docs,
  - historical reverse-check lessons through the reverse-check docs until their
    surviving policy is captured in current rulegen references.
- `L1-C.2` linked the authority map from `docs/README.md` and
  `docs/developer/README.md`.

### L1-D: Dated Reverse-Check Archive Prep

Goal:
- keep the useful reverse-check lessons without leaving old dated docs as
  ambiguous current workstream surfaces.

Candidate docs:

1. `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`,
2. `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`,
3. `docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`,
4. `docs/rulegen/reverse_check_rollout_matrix.md`,
5. `docs/rulegen/reverse_check_scoring_phase1.md`.

Do not move the remaining current mixed references until their policy/status
claims are fully represented in the feature-state ledger and rulegen support
guide.

Progress:

- `L1-D.1` captured the surviving reverse-check policy/status in:
  - `docs/rulegen/reverse_check_scoring_phase1.md`,
  - `docs/rulegen/reverse_check_rollout_matrix.md`,
  - `docs/rulegen/rulegen_lp_support_guide.md`,
  - `docs/language_pairs/en_de_workstream_roadmap.md`,
  - `docs/rulegen/semantic_rulegen_authority_map.md`.
- `L1-D.2` moved the three dated `en-es` review snapshots into
  `docs/archive/rulegen/` and updated exact references.
- Result: the dated March 2026 `en-es` review docs are now historical evidence
  snapshots. Current reverse-check state remains in the rollout matrix,
  phase-1 spec, LP support guide, feature-state ledger, and current artifacts.

### L1-E: Site Docs Authority Note

Goal:
- distinguish GitHub Pages/user handbook files from developer truth surfaces.

Candidate docs:

1. `docs/index.md`,
2. `docs/handbook/*.md`,
3. `docs/getting-started/*.md`.

This is a site-routing pass, not a product behavior pass.

Progress:

- `L1-E.1` completed source-only governance comments for:
  - `docs/index.md`,
  - `docs/handbook/README.md`,
  - `docs/handbook/architecture.md`,
  - `docs/handbook/developer.md`,
  - `docs/handbook/diagrams.md`,
  - `docs/handbook/index.md`,
  - `docs/handbook/release.md`,
  - `docs/getting-started/README.md`,
  - `docs/getting-started/images/README.md`,
  - `docs/getting-started/index.md`.
- Site-doc labels distinguish Pages navigation and user-facing runbooks from
  developer implementation authority. Comments are hidden in rendered pages so
  they do not add public manual clutter.
- After `L1-E.1`, the scanned docs missing `Role:` metadata dropped from `34`
  to `24`; the remaining count still includes the ignored generated CWS
  preflight snapshot.

### L1-F: Language-Pair Metadata Packet

Goal:
- classify LP setup, resource, recovery, inventory, and POS docs without
  changing LP implementation status claims.

Progress:

- `L1-F.1` completed metadata normalization for:
  - `docs/language_pairs/dictionary_matrix_checklist.md`,
  - `docs/language_pairs/extension_lp_generalization_checklist.md`,
  - `docs/language_pairs/language_pair_setup_checklist.md`,
  - `docs/language_pairs/lp_data_inventory_matrix.md`,
  - `docs/language_pairs/lp_resource_requirements.md`,
  - `docs/language_pairs/pos_source_and_pipeline_reference.md`,
  - `docs/language_pairs/resource_recovery_playbook.md`.
- Labels were applied conservatively:
  - checklist and rollout docs remain planning/mixed surfaces,
  - `language_pair_setup_checklist.md` and `resource_recovery_playbook.md`
    are operational runbooks,
  - `pos_source_and_pipeline_reference.md` is the canonical POS reference,
  - LP requirement and inventory matrices remain mixed current-plus-target
    references.
- After `L1-F.1`, the scanned docs missing `Role:` metadata dropped from `24`
  to `17`; the remaining count still includes the ignored generated CWS
  preflight snapshot.

### L1-G: Auxiliary README Metadata Packet

Goal:
- normalize small README guides that are clearly supporting surfaces, not
  implementation authority.

Progress:

- `L1-G.1` completed metadata normalization for:
  - `docs/semantic_routing_html/README.md`,
  - `docs/test_inputs/rulegen_benchmark_cases/README.md`,
  - `docs/test_inputs/rulegen_lp_profiles/README.md`.
- Labels keep these READMEs scoped:
  - semantic routing HTML is a local preview runbook,
  - rulegen benchmark cases are the canonical dataset-label guide,
  - LP profiles are an operational guide for static profile contracts, not
    dynamic feature-state truth.
- After `L1-G.1`, the scanned docs missing `Role:` metadata dropped from `17`
  to `14`; the remaining count still includes the ignored generated CWS
  preflight snapshot.

### L1-H: Rulegen/Semantic Missing-Role Metadata Packet

Goal:
- classify the remaining substantive `docs/rulegen/` missing-role files without
  changing rulegen behavior claims, semantic policy, benchmark labels, or
  generated evidence.

Progress:

- `L1-H.1` completed metadata normalization for:
  - `docs/rulegen/rule_generation_technical.md`,
  - `docs/rulegen/synonym_generation_technical.md`,
  - `docs/rulegen/pos_normalization_workstream.md`,
  - `docs/rulegen/phase0_pos_baseline_findings.md`,
  - `docs/rulegen/rulegen_congruity_implementation_plan.md`,
  - `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`,
  - `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`,
  - `docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`,
  - `docs/rulegen/reverse_check_rollout_matrix.md`,
  - `docs/rulegen/reverse_check_scoring_phase1.md`,
  - `docs/rulegen/semantic_llm_generation_budget_reference.md`,
  - `docs/rulegen/semantic_veto_breadth_expansion_gate.md`,
  - `docs/rulegen/semantic_veto_current_wave6_rerun_chain.md`.
- Labels were applied conservatively:
  - core technical docs and rollout/scoring specs remain `Mixed`,
  - dated reverse-check review docs are `Archive / legacy` evidence snapshots,
  - the POS phase-0 baseline is `Generated evidence`,
  - semantic budget/gate docs remain planning surfaces,
  - the current wave6 rerun chain is an operational runbook and still not a
    runtime-policy promotion.
- After `L1-H.1`, the scanned docs missing `Role:` metadata dropped from `14`
  to `1`; the remaining item is the ignored generated CWS preflight snapshot
  under `docs/runbooks/cws_preflight_reports/`.

### L1-I: Non-Packet Role Normalization Packet

Goal:
- convert descriptive non-standard `Role:` labels to the governance-approved
  vocabulary without changing content, status claims, or implementation truth.

Progress:

- `L1-I.1` completed role normalization for the `31` non-packet docs that had
  non-standard role labels across developer planning docs, language-pair docs,
  semantic/rulegen docs, and `docs/test_inputs/semantic_routing/README.md`.
- Role mappings were conservative:
  - plans, roadmaps, research queues, and future-gate docs use
    `Planning / WIP`,
  - executable guides use `Runbook / operational`,
  - current-plus-target references use `Mixed`,
  - the semantic-veto assumption ledger uses `Draft decision log`,
  - current semantic denominator/archive-routing references use
    `Canonical current` only where the doc is a current routing or state
    reference rather than implementation truth.
- After `L1-I.1`, docs with non-standard `Role:` labels dropped from `82` to
  `51`; all remaining non-standard labels are `Role: Packet / WIP` in
  `docs/developer/project_integrity_*_packet.md` files.

### L1-J: SRS Supersession Review

Goal:
- keep SRS roadmap/schema/planning docs useful without letting mixed target-state
  text compete with current feature-state and harness truth.

Progress:

- `L1-J.1` added `docs/srs/README.md` as the SRS documentation authority map.
- Result: no SRS docs were archived in this slice.
- Current routing:
  - `docs/developer/feature_state_matrix.md` owns implemented/default-on/
    verified SRS status,
  - `docs/architecture/srs_lp_architecture.md` owns the LP/SRS capability
    contract,
  - `docs/srs/srs_roadmap.md` remains the mixed current snapshot and roadmap,
  - `docs/srs/srs_schema.md` and `docs/srs/srs_profile_schema.md` remain mixed
    schema references,
  - `docs/srs/srs_selector_technical.md` and
    `docs/srs/srs_curriculum_notes.md` remain planning-only surfaces.
- `L1-J.2` linked the SRS authority map from `docs/README.md`,
  `docs/developer/README.md`, and `docs/srs/srs_roadmap.md`.
- Productization boundary preserved:
  - due-aware serving is still planned end to end,
  - profile bootstrap/growth remain non-default or limited as documented in
    feature-state entries,
  - roadmap/schema text should not be treated as implementation proof.

### L1-K: GUI Supersession Review

Goal:
- keep GUI workstream, snapshot, and decision docs useful without letting older
  structure notes compete with source/test truth.

Progress:

- `L1-K.1` added `docs/gui/README.md` as the GUI documentation authority map.
- Result: no GUI docs were archived in this slice.
- Current routing:
  - `apps/gui/src/` and `apps/gui/tests/` own current GUI behavior,
  - `docs/gui/gui_current_structure.md` remains a dated snapshot after the
    Utility Dock/profile-ruleset work,
  - `docs/gui/gui_app_fix_workstream.md` remains planning/WIP history and a
    cleanup queue,
  - `docs/gui/gui_ux_decisions.md` remains decision rationale,
  - `docs/gui/profile_ruleset_refactor_notes.md` remains refactor planning
    context.
- `L1-K.2` linked the GUI authority map from `docs/README.md` and
  `docs/developer/README.md`, and added a routing note to
  `docs/gui/gui_current_structure.md`.
- Productization boundary preserved:
  - current GUI structure claims require source/test verification,
  - the February 2026 structure snapshot is not promoted as current
    architecture authority,
  - GUI packaging/platform claims stay routed through build/parity docs and
    feature-state entries.

### L1-L: Language-Pair Supersession Review

Goal:
- keep language-pair resource matrices, onboarding checklists, and workstream
  roadmaps useful without letting older checklist rows compete with current
  feature-state, code, test, and generated-audit truth.

Progress:

- `L1-L.1` added `docs/language_pairs/README.md` as the language-pair
  documentation authority map.
- Result: no language-pair docs were archived in this slice.
- Current routing:
  - `docs/developer/feature_state_matrix.md` owns implemented/default-on/
    verified LP status,
  - `docs/architecture/srs_lp_architecture.md` and
    `core/lexishift_core/helper/lp_capabilities.py` own the LP/SRS capability
    contract boundary,
  - `docs/rulegen/rulegen_lp_support_guide.md` owns the rulegen mechanism
    stack,
  - `docs/rulegen/lp_onboarding_operating_model.md` and
    `docs/rulegen/lp_onboarding_checklist_template.md` own the rulegen-specific
    onboarding golden path,
  - `docs/language_pairs/language_pair_setup_checklist.md` remains the
    cross-surface operational onboarding runbook,
  - `docs/language_pairs/lp_resource_requirements.md` and
    `docs/language_pairs/lp_data_inventory_matrix.md` remain mixed
    current-plus-target resource references,
  - `docs/language_pairs/dictionary_matrix_checklist.md` remains a planning
    checklist, not the current LP support matrix.
- Productization boundary preserved:
  - resource presence, wiring, coverage adequacy, SRS support, rulegen
    publication, and runtime serving remain separate status axes,
  - pair roadmaps and one-off research snapshots do not promote LP parity
    without current source/test/artifact evidence.

## Current Stop Conditions

Stop and ask for direction if a follow-up pass finds:

1. a doc that is stale but still the only source for an implemented behavior,
2. generated evidence cited as architecture authority with no owning doc,
3. an exact-reference search showing a proposed move would break scripts,
4. a metadata change that would imply a feature-state promotion,
5. a cleanup that touches rulegen scoring, SRS behavior, or semantic runtime
   policy.

## Immediate Recommendation

Lane 1 has completed the maintained-doc metadata sweep, the packet grouping
index, the semantic/rulegen authority map, the dated reverse-check archive move,
and the SRS, GUI, and language-pair supersession routing maps. The only
remaining non-standard role labels are the `51` project-integrity packet docs,
which are now grouped by `project_integrity_packet_index.md`.

The next broad move needs an explicit choice between:

1. continue Lane 1 by selecting a packet archive destination and moving packet
   groups behind that index,
2. switch to Lane 2 code-path cleanup now that the highest-risk doc routing
   ambiguity is lower.
