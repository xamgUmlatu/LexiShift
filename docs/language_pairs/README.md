# Language-Pair Documentation Authority Map

Status: active LP docs routing
Role: Canonical current
Last updated: 2026-05-17
Last verified: 2026-05-17 SRS topic-signal LP generalization runbook routing update; routing only, LP capability/status claims not re-audited
Purpose: route language-pair, resource, and onboarding claims without treating older checklist or roadmap snapshots as current implementation truth
Source-of-truth: routing guide only; executable truth lives in LP capability/resource code, rulegen/SRS code, GUI pack registration, tests, generated audits, and `docs/developer/feature_state_matrix.md`.

Use this file before editing language-pair docs. It identifies which document
owns which claim type and which docs are planning or historical context.

## Current Authority By Claim Type

| Claim type | Start here | Authority boundary |
| --- | --- | --- |
| Implemented/default-on/verified LP status | `../developer/feature_state_matrix.md` | Status claims need code, test, or generated artifact evidence. Do not infer status from checklist completion. |
| LP/SRS capability contract | `../architecture/srs_lp_architecture.md` and `../../core/lexishift_core/helper/lp_capabilities.py` | Architecture describes the contract; source code owns runtime behavior. |
| Pair resource resolution | `../../core/lexishift_core/helper/pair_resources.py`, `../../apps/gui/src/language_packs.py`, and `lp_resource_requirements.md` | Matrices are human-facing references; code and audits own executable truth. |
| Rulegen LP mechanism stack | `../rulegen/rulegen_lp_support_guide.md` | Mechanism/status updates that touch rulegen behavior need the rulegen quality loop. |
| Rulegen LP onboarding process | `../rulegen/lp_onboarding_operating_model.md` and `../rulegen/lp_onboarding_checklist_template.md` | These are the rulegen-specific golden path and reusable checklist. |
| End-to-end LP onboarding checklist | `language_pair_setup_checklist.md` | Operational runbook for GUI, extension, helper, core rulegen, and SRS wiring. |
| Resource requirements and gaps | `lp_resource_requirements.md` | Mixed current-plus-target matrix; verify status-sensitive claims against code and audits. |
| Resource inventory | `lp_data_inventory_matrix.md` | Mixed inventory matrix; use generated resource/POS audits for current local machine state. |
| POS source and pipeline behavior | `pos_source_and_pipeline_reference.md` and `../rulegen/pos_normalization_workstream.md` | POS policy and raw-tag claims should stay tied to provider/profile code and probe artifacts. |
| SRS topic-signal data acquisition and cross-LP lessons | `../srs/srs_topic_signal_lp_generalization_runbook.md`, `../srs/srs_interest_tailored_data_acquisition_plan.md`, and `../srs/srs_topic_preference_decision_matrix_en_es.md` | General method and en-es worked example only; do not use as proof that another LP has promoted topic overlays. |
| Licensing and distribution posture | `data_source_licensing_and_distribution.md` and `hybrid_data_distribution_north_star.md` | Legal/distribution posture remains review-required where the underlying doc says so. |
| Resource recovery | `resource_recovery_playbook.md` | Operational recovery runbook for invalid/unlinked packs. |
| Extension/helper LP rollout | `extension_lp_generalization_checklist.md`, `../architecture/srs_lp_architecture.md`, and `../developer/feature_state_matrix.md` | Checklist rows are not proof of default-on shipped behavior. |
| Pair-specific roadmaps | `de_en_workstream_roadmap.md`, `en_de_workstream_roadmap.md`, and pair-specific integration plans such as `kaikki_en_es_integration_plan.md` | Treat as planning or mixed references unless the doc metadata and feature-state evidence say otherwise. |
| Older capability checklists | `dictionary_matrix_checklist.md` | Planning checklist; current requirement/inventory rows belong in `lp_resource_requirements.md` and `lp_data_inventory_matrix.md`. |

## Supersession Decisions

No language-pair docs are archived in this Lane 1 pass.

- `language_pair_setup_checklist.md` remains the cross-surface operational
  onboarding runbook. Rulegen-specific mature-pair work routes through
  `../rulegen/lp_onboarding_operating_model.md` and
  `../rulegen/lp_onboarding_checklist_template.md`.
- `dictionary_matrix_checklist.md` remains a planning checklist. Do not treat
  it as the current LP support matrix; status-sensitive rows should be captured
  in `lp_resource_requirements.md`, `lp_data_inventory_matrix.md`, or
  `../developer/feature_state_matrix.md`.
- Pair-specific workstream roadmaps remain planning or mixed references. They
  can explain intent and history, but they do not promote a pair without current
  source/test/artifact evidence.
- SRS topic-signal lessons should route through
  `../srs/srs_topic_signal_lp_generalization_runbook.md` before they are copied
  into pair-specific roadmaps. The en-es animals/plants packet is a worked
  example, not a cross-LP status claim.
- One-off research snapshots under this folder should stay snapshot-only until
  explicitly promoted into the authority map, feature-state ledger, or another
  canonical current doc.

## Productization Boundaries

- LP parity is directional. Spell out `source->target` when a pair naming claim
  could be misread.
- "Resource exists" is weaker than "resource is wired", and both are weaker
  than "resource is coverage-adequate for production publication".
- SRS initialize/refresh support, rulegen publication, runtime serving, and
  extension/helper UI wiring are separate status axes.
- Generated audits are evidence snapshots, not architecture authority. Promote
  stable lessons into the owning doc before using them as current product truth.
