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

See also:
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
