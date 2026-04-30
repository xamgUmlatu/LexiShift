# Semantic Veto Assumption Ledger

Status: current reference
Role: Reconciliation ledger
Last updated: 2026-05-01
Scope: current `wave6_auth_frame_raw_sentence_surface_pos_rescue` candidate only

This ledger records the assumptions behind the current semantic-veto candidate.
It is not a runtime-policy change and not promotion evidence by itself. Rows
marked tested are tested only against the evidence named in the row; rows marked
untested must become queued tests before they can support promotion.

## Current Candidate Boundary

- Candidate: `wave6_auth_frame_raw_sentence_surface_pos_rescue`
- Production status: `research_only`
- Runtime policy change: `none`
- Current active/shadow evidence: `38` cases, `0` harmful replacements, `0`
  false abstains.
- Current phrase/no-winner evidence before rescue replay: `16` cases, `2`
  harmful replacements.
- Current scorer-backed rescue validation: `54` cases, `0` harmful
  replacements, `0` false abstains, `3` active rescues.
- Next required breadth gate: `wave7_source_class_breadth_v1`

## Assumption Rows

| Assumption | Status | Evidence Link | Current Read | Required Action |
| --- | --- | --- | --- | --- |
| Raw-sentence context is the right context view for this lane. | tested_current_suite | `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md`; `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md`; `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md` | Raw-sentence context passes the current active/shadow suite at `0` harmful and `0` false abstains, but it does not by itself protect phrase/no-winner rows before rescue. | Retest raw-sentence context in `wave7_source_class_breadth_v1`; do not treat it as universally better than windowed or masked views. |
| The phrase-prototype margin of `0.02` is the right active/shadow and phrase/no-winner balance point. | tested_current_suite | `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md`; `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md`; `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md` | The margin participates in the passing current policy shape, but the unrescued phrase suite still has `2` harmful replacements. | Keep the margin tied to the named validation artifacts; sweep or confirm it again on fresh wave7 suites before promotion. |
| Source-triggered authorization frames are a real semantic-class signal, not a browser-case template. | tested_current_suite | `docs/test_outputs/semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.md`; `docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.md`; `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.md`; `source_trigger_overfit_audit` in `docs/test_inputs/semantic_veto_system_registry_en_es.json` | The adapter emitted `5` rows for one permission-like sense, with matched source-trigger text and no target-in-source flag in the rendered audit. The targeted overfit action also records `0` heldout sentence or Spanish target-lemma violations across `54` heldout sentences. | Preserve source-trigger checks for any new class detector. Do not generalize authorization-frame success to other semantic classes without class-specific source triggers. |
| The recommended rescue gates are sufficient for this current wave6 suite. | tested_current_suite | `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md`; `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md` | The recommended policy `m=0;p=0.02;rescue_active=0.52;noun_lead=none;modifier_lead=0.02` is scorer-backed offline at `0` harmful and `0` false abstains over `54` cases. | Keep the gates research-only until runtime implementation work and broader scorer-backed validation exist. |
| Current wave6 breadth is enough for promotion-like confidence. | rejected | `docs/rulegen/semantic_veto_breadth_expansion_gate.md`; `docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.md` | Failure-class mining still marks promotion blocked by insufficient breadth, and the breadth gate says wave7 is definition-only until executed. | Run `wave7_source_class_breadth_v1` before further promotion claims or threshold tuning. |
| The current candidate has already changed runtime behavior. | rejected | `docs/test_inputs/semantic_veto_system_registry_en_es.json`; `docs/rulegen/semantic_veto_reconciliation_workstream.md`; `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`; `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py` | The registry current candidate still says `runtime_policy_change: none`, and the reconciliation workstream keeps runtime behavior separate from research candidates. | Any runtime change needs a separate implementation pass plus runtime-path tests. |
| Phrase/no-winner behavior can be summarized inside active/shadow metrics. | rejected | `docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md`; `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md`; `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md` | The phrase/no-winner suite is the visible source of the original `low` and `bear` harms. Rescue validation closes that current-suite issue, but it does not erase the separate guardrail. | Keep phrase/no-winner validation and active/shadow validation separate in every candidate summary. |
| New semantic-class detectors can be added by analogy with authorization frames alone. | untested | `docs/rulegen/semantic_veto_breadth_expansion_gate.md`; `docs/test_outputs/semantic_authorization_frame_evidence_non_v10_wave6_wiktextract_supported_latest.md` | Authorization frames are source-triggered only for one permission-like family in wave6. The breadth gate requires at least `3` non-authorization semantic-class buckets from source-detectable signals. | For wave7, add class detectors only when gloss, translation-sense, or source example text fires the detector without browser heldout text or Spanish target lemmas. |

## Action Hooks

- `assumption_ledger_seed`: done when this ledger is registered and the registry
  summary is regenerated cleanly.
- `archive_consolidation`: next pass. Demote or label old artifacts only after
  their surviving lesson is represented in the registry, this ledger, or the
  workstream.
- `breadth_expansion_gate`: remains the next substantive evidence-producing
  task before runtime promotion or broader confidence claims.
