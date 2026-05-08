# Semantic Routing Schema References

Status: mixed current plus offline-intake staging
Role: schema reference for shipped semantic-routing seams plus planning/research semantic-routing surfaces

This directory is mixed on purpose.

- Some schema files now describe shipped semantic-routing seams:
  - emitted rule pointers under `rule.metadata.semantic_admission`
  - helper-published semantic inventory sidecars
  - helper/runtime `semantic_admit_batch` request and response payloads used by the browser extension semantic-admission path
- Other schema files still describe planning or research surfaces, so future implementation can converge on one LP-symmetric data shape instead of inventing pair-specific payloads ad hoc.

Files:
- `semantic_admission.schema.json`
  - current per-rule pointer contract stored under `rule.metadata.semantic_admission`
  - broad runtime readiness still depends on LP-specific publication support and launch posture
- `semantic_inventory.schema.json`
  - current semantic inventory sidecar contract published alongside ruleset/snapshot for semantic routing
  - helper artifact naming is `srs_semantic_inventory_<pair>_<profile>.json`
  - includes optional pair capability summary for active-pointer modes and default unavailable reasons
- `semantic_llm_intake_batch.schema.json`
  - offline Layer 1 raw source intake envelope for LLM, external, or internal reviewed semantic evidence batches before canonical normalization
- `semantic_evidence_batch.schema.json`
  - offline Layer 2 normalized evidence lane emitted after raw source batches are deduped into one common semantic-evidence shape
  - current example-frame source work requires active, shadow, and phrase-control rows together before a batch is promotion-relevant
  - `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py` builds the current no-spend reviewed fixture in that shape
  - `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py` builds the current non-LLM reverse-aux source batch in that shape, with expected gaps preserved
  - `scripts/testing/semantic_llm_example_frame_contract_en_es.py` renders the current no-spend contract read for raw intake or normalized evidence batches; pass `--required-family-json` when a queue or dataset family set must be covered
  - `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py` renders the current no-spend missing-row generation plan from a required-family contract read; it plans only missing active/shadow/phrase-control rows and keeps reviewed case sentences plus translation targets out of prompt input
  - `scripts/testing/semantic_llm_example_frame_generation_run_en_es.py` executes or replays that plan with the same raw-response, journal, and spend-guard discipline as the prompt bakeoff runner
  - `scripts/testing/semantic_example_frame_batch_merge_en_es.py` builds a virtual composite evidence batch for contract/prototype probes
  - `scripts/testing/semantic_llm_example_frame_generation_quality_gate_en_es.py` gates generated source batches after contract/prototype reads so structural completeness cannot be mistaken for promotion readiness
- `semantic_family_inventory.schema.json`
  - planning schema for family-level queue memory, triage hypotheses, and additive semantic-generation tracking
- `semantic_prompt_spec_en_es_v10.json`
  - frozen prompt wording + model-default bundle for the first bounded `en-es` cue bakeoff
  - current defaults:
    - proxy `gpt-5.4-mini`
    - target `gpt-5.4`
- `semantic_report_event_batch.schema.json`
  - planning schema for append-only raw semantic user report events attached to concrete runtime rule fires
- `semantic_local_override_bundle.schema.json`
  - planning schema for profile-local semantic safety overrides that can suppress bad rules without mutating shared semantic truth
- `semantic_admit_batch_request.schema.json`
  - current helper/runtime request contract for batched semantic admission over concrete matched contexts
  - carries pair/profile, explicit offset encoding, fallback policy, optional requested decision policy, and matched rule pointers plus local context text
- `semantic_admit_batch_response.schema.json`
  - current helper/runtime response contract for batched semantic admission decisions
  - carries the resolved decision policy, actual replace/abstain outcome, reason codes, and compact score summaries for diagnostics
- `sentence_veto_case.schema.json`
  - research-only benchmark schema for fixed active-vs-shadow sentence-level veto evaluation
  - intended current use: compare scorer families, context transforms, evidence views, and threshold ladders without changing the mined shadow source

Datasets:
- `docs/test_inputs/semantic_veto_representative_gap_rows_en_es.json`
  - research-only `en-es` representative gap row dataset for Stage 1 sampling
  - currently 25 corpus-like app-candidate proxy rows
  - purpose: fill the Stage 1 representative-frame target from 95 to 120 rows without using targeted P0, stress, or LLM discovery rows
  - caveat: agent-authored corpus-like proxy lane; not observed browser logs and human review is still required before promotion claims
- `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json`
  - research-only `en-es` filled Stage 1 representative sentence-veto dataset
  - currently 19 trigger families / 120 labeled sentences
  - purpose: score the filled representative frame with ordinary sentence-veto harnesses using existing v10 family evidence
  - caveat: includes 25 agent-authored corpus-like proxy rows; not final browsing-distribution evidence
- `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json`
  - research-only `en-es` Stage 1 P0 manual discovery dataset generated from the scientific sampling expansion plan
  - currently 2 trigger families / 20 draft labeled sentences
  - purpose: confirm the first P0 targeted curve-mechanism cell contracts before spending LLM generation budget
  - caveat: agent-authored draft lane; not representative browsing evidence and not locked evaluation
- `docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json`
  - research-only `en-es` word-group diagnostic dataset generated from the frozen semantic-veto frequency/polysemy pilot
  - currently 29 authored trigger families / 121 draft labeled sentences
  - purpose: compare veto behavior by pre-outcome source-frequency and WordNet-polysemy groups before spending broader LLM generation budget
  - caveat: agent-authored draft lane; low-polysemy controls are not shadow-balanced when no honest shadow exists
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
  - current curated `en-es` runtime-veto harness dataset
  - currently 19 ambiguity families / 95 labeled sentences
  - expands `v9` with one held-out cross-POS weak-active-support family:
    - `report` as a noun-active / verb-shadow family with one new held-out report-style false-abstain probe row and a lexicalized `report back` phrase row
  - purpose: test whether new held-out residue keeps widening through weak-active-support rather than reopening phrase leakage
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v9.json`
  - preserved prior held-out weak-active-support slice
  - 18 ambiguity families / 90 labeled sentences
  - retained frozen for before/after comparison against `v10`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v8.json`
  - preserved prior held-out weak-active-support slice
  - 17 ambiguity families / 85 labeled sentences
  - retained frozen for before/after comparison against `v9`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v7.json`
  - preserved prior held-out weak-active-support slice
  - 16 ambiguity families / 80 labeled sentences
  - retained frozen for before/after comparison against `v8`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v6.json`
  - preserved prior held-out phrase-risk validation slice
  - 15 ambiguity families / 75 labeled sentences
  - retained frozen for before/after comparison against `v7`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v5.json`
  - preserved prior held-out-growth and phrase-leak review slice
  - 14 ambiguity families / 70 labeled sentences
  - retained frozen for before/after comparison against `v6`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v4.json`
  - preserved prior held-out-growth slice
  - 12 ambiguity families / 60 labeled sentences
  - retained frozen for before/after comparison against `v5`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v3.json`
  - preserved prior phrase-lane expansion slice
  - 10 ambiguity families / 50 labeled sentences
  - retained frozen for before/after comparison against `v4`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
  - preserved prior main runtime-veto slice
  - 8 ambiguity families / 40 labeled sentences
  - retained frozen for before/after comparison against `v3`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v1.json`
  - preserved earlier starter slice
  - 4 ambiguity families / 20 labeled sentences

See also:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_feedback_promotion_flow.md`
- `core/lexishift_core/rulegen/semantic_evidence.py`
