# Semantic Feedback Promotion Flow

Status: active plan
Role: Planning / governance
Purpose: define how future semantic user reports can be captured, acted on locally, and promoted conservatively without poisoning shared semantic truth
Last updated: 2026-04-15
Last verified: 2026-04-15 repo-doc review against the semantic-routing data lifecycle, queueing plan, and existing extension/helper feedback architecture
Source-of-truth: planning doc only; current implemented truth still lives in existing SRS feedback code paths and future semantic-routing implementation work
Related docs:
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

## Goal

Allow future semantic user reporting to improve safety and prioritization without letting noisy raw feedback directly rewrite shared semantic truth.

The governing asymmetry remains:

- false abstain is acceptable
- harmful replace is not

That means negative feedback is mainly useful as:

- local protection
- review prioritization
- and queueing evidence

not as automatic truth.

## Core separation

The future system should keep three layers separate:

1. raw report events
2. local safety overrides
3. shared semantic promotion

Those layers should not be collapsed.

## Layer 1. Raw report events

Future user semantic reports should first land as append-only event rows.

Planned schema:

- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`

These events should preserve:

- which exact rule fired
- which semantic family it belonged to
- which generation and policy produced it
- what the user reported

This is evidence, not truth.

Current intended v1 posture:

- the report is global
- it is attached to one concrete runtime rule application
- it does not automatically block or suppress locally
- and it should carry only privacy-safe metadata by default

## Layer 2. Local safety overrides

Users should be allowed to protect themselves immediately.

The safest first product action is:

- local suppression or local force-abstain for the reported rule/family

Planned schema:

- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`

These overrides should be:

- profile-local or helper-local
- immediately actionable
- reversible
- and explicitly separate from shared semantic generations

This gives the user a real escape hatch without polluting the global semantic pipeline.

Important separation for v1:

- reporting and local suppression are different actions
- a user may report globally without blocking locally
- a user may block locally without sending a global report

## Layer 3. Family-level aggregation

Raw report events should later roll up into family-level triage memory.

Planned schema:

- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

This layer is where the repo should decide:

- whether repeated feedback points to a real family-level problem
- whether the family likely needs shadow data, cue data, an algorithm fix, or a phrase/parsing fix
- and whether the family should be queued for review or later LLM generation

## Promotion ladder

The conservative intended promotion flow is:

1. User reports a bad semantic outcome on one concrete rule fire.
2. The repo stores a raw report event with provenance.
3. Offline aggregation updates family-level evidence and queue state.
4. Repeated or high-value families are promoted for manual review.
5. A separate local suppression action may exist, but it is not implied by the report itself.
6. Manual review decides one of:
   - keep local-only
   - add or refine shadow data
   - add or refine cue data
   - fix algorithm
   - fix phrase/parsing behavior
   - leave unresolved
7. Only after review does shared semantic truth change.
8. Any accepted change enters the normal compile -> validate -> publish lifecycle.

## What should be automatic

Safe automatic behavior:

- append raw report events
- aggregate repeated failures into family-level evidence
- rank families for review

## What should stay review-gated

Review-gated behavior:

- creating shared shadow candidates
- creating shared cue data
- changing pair-global competition sets
- changing published semantic generations
- promoting mined user-feedback patterns into global semantic truth

## Why this is the right posture

This posture preserves three important properties:

- users can protect themselves immediately
- the repo can learn from repeated failures
- and shared semantic truth remains auditable instead of being rewritten by raw reports

## Expected first implementation sequence

The first eventual product slice should be:

1. record raw semantic report events
2. surface aggregated family-review queues to operators
3. optionally add separate local suppression controls

The repo should not start with:

- automatic global semantic mutation from user reports

That is the wrong starting posture.
