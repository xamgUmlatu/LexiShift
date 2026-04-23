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
  - offline Layer 1 raw LLM intake envelope for shadow, bridge, or cue proposal batches before canonical normalization
- `semantic_evidence_batch.schema.json`
  - offline Layer 2 normalized evidence lane emitted after raw source batches are deduped into one common semantic-evidence shape
- `semantic_family_inventory.schema.json`
  - planning schema for family-level queue memory, triage hypotheses, and additive semantic-generation tracking
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
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v9.json`
  - current curated `en-es` runtime-veto harness dataset
  - currently 18 ambiguity families / 90 labeled sentences
  - expands `v8` with one held-out cross-POS weak-active-support family:
    - `trip` as a noun-active / verb-shadow family with one held-out trip-style false-abstain row and a lexicalized `trip up` phrase row
  - purpose: test whether new held-out residue keeps widening through weak-active-support rather than reopening phrase leakage
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
