# Semantic Routing Planning Schemas

Status: planning-only
Role: schema sketch for future semantic-routing integration

These schema files do not describe a shipped runtime contract yet.
They exist so future implementation can converge on one LP-symmetric data shape instead of inventing pair-specific payloads ad hoc.

Files:
- `semantic_admission.schema.json`
  - planned per-rule pointer stored under future `rule.metadata.semantic_admission`
- `semantic_inventory.schema.json`
  - planned sidecar inventory published alongside ruleset/snapshot for semantic routing
  - intended future helper artifact naming: `srs_semantic_inventory_<pair>.json`
  - includes optional pair capability summary for active-pointer modes and default unavailable reasons
- `semantic_admit_batch_request.schema.json`
  - planned helper/runtime request contract for batched semantic admission over concrete matched contexts
  - carries pair/profile, explicit offset encoding, fallback policy, optional requested decision policy, and matched rule pointers plus local context text
- `semantic_admit_batch_response.schema.json`
  - planned helper/runtime response contract for batched semantic admission decisions
  - carries the resolved decision policy, actual replace/abstain outcome, reason codes, and compact score summaries for diagnostics
- `sentence_veto_case.schema.json`
  - research-only benchmark schema for fixed active-vs-shadow sentence-level veto evaluation
  - intended current use: compare scorer families, context transforms, evidence views, and threshold ladders without changing the mined shadow source

Datasets:
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
  - current curated `en-es` runtime-veto harness dataset
  - currently 8 ambiguity families / 40 labeled sentences
  - purpose: separate runtime scorer quality from upstream shadow-mining quality
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v1.json`
  - preserved earlier starter slice
  - 4 ambiguity families / 20 labeled sentences

See also:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
