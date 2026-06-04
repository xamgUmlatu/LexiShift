# Documentation Governance

Status: Active policy
Role: Canonical current
Owner: engineering
Last updated: 2026-05-16
Source-of-truth: documentation policy; enforced through `scripts/dev/check_doc_references.py` and the linked routing docs.

## Purpose

Make LexiShift documentation operable as a maintained system instead of a loose collection of notes.

This policy exists to:

1. keep current truth easy to find,
2. separate implemented behavior from plans and generated evidence,
3. give future grooming work a clear standard,
4. make documentation regressions cheap to catch in repo-safety checks.

## North Star

A contributor or agent should be able to answer three questions quickly and correctly:

1. what is implemented now,
2. what is still planning or mixed-status design,
3. where to verify the claim in code, tests, or generated evidence.

## Current Authority Model

Use this order when deciding what is true:

1. source code, manifests, controller graphs, and runtime defaults
2. `docs/developer/feature_state_matrix.md` for cross-cutting status, evidence, and known doc/code mismatches
3. routing/classification docs:
   - `docs/README.md`
   - `docs/developer/README.md`
   - `docs/architecture/README.md`
4. current implementation/reference docs in the relevant domain
5. generated evidence under `docs/test_outputs/`

Important rule:

- generated reports are evidence, not architecture or backlog authority by themselves

## Documentation Roles

Every maintained doc should fit one primary role:

1. `Canonical current`
2. `Mixed`
3. `Planning / WIP`
4. `Draft decision log`
5. `Runbook / operational`
6. `Generated evidence`
7. `Archive / legacy`

Use one exact `Role:` value from the list above in maintained doc metadata.

## Required Metadata

For docs used in active planning, current behavior, or routing:

1. `Status`
2. `Role`
3. `Purpose`
4. `Last updated`
5. `Last verified` when the doc makes present-tense implementation claims
6. `Verification` or `Source-of-truth` pointers when the doc is relied on operationally

For generated evidence docs:

1. generator/source command or producing workflow
2. timestamp or dated filename
3. scope/pair/profile where relevant

## Canonical Routing Docs

The current routing layer for the repo is:

1. `README.md`
2. `docs/README.md`
3. `docs/developer/README.md`
4. `docs/developer/developer_reference.md`
5. `docs/architecture/README.md`
6. `docs/developer/feature_state_matrix.md`

These docs should stay concise, current, and checker-covered.

## Documentation Integrity Gate

Canonical doc integrity is enforced by:

1. script: `scripts/dev/check_doc_references.py`
   - validates top metadata on canonical docs (`Status`, `Role`, `Last updated`)
   - validates referenced repo paths in canonical docs
2. package commands:
   - `npm --prefix scripts run check:docs`
   - `npm --prefix scripts run check:docs:report`
3. repo safety:
   - `npm --prefix scripts run check`
   - `npm --prefix scripts run check:changed`

Scope rule:

- the doc-reference checker should stay focused on canonical routing and policy docs
- `feature_state_matrix.md` remains covered separately by `scripts/dev/feature_state_audit.py`

## Truth-Verification Workflow Before Taking Work

Before acting on a documented task or status claim:

1. read the routing doc for that area
2. check whether the owning doc is `Canonical current`, `Mixed`, or `Planning / WIP`
3. verify current behavior in code/tests/artifacts when the change is implementation-facing
4. keep known contradictions explicit in `docs/developer/feature_state_matrix.md`
5. avoid promoting a planning doc into current truth just because it is detailed

## Salvage-Forward And Archive Policy

When a doc becomes mostly outdated:

1. identify the small amount of surviving value
2. migrate that value into the right current doc first
3. only then downgrade or retire the older doc

Archive rule for future grooming:

1. prefer `docs/archive/<domain>/...` for newly retired docs
2. mark archived docs clearly as historical or superseded
3. keep `legacy_root_readme_snapshot.md` as a grandfathered archive until a later cleanup pass decides otherwise

## Generated And Built Docs Policy

Treat these as non-authoritative outputs unless explicitly referenced as evidence:

1. `docs/test_outputs/`
2. `docs/_site/`
3. the local Jekyll cache directory

They may be operationally useful, but they should not become the default planning path.

Generated evidence cleanup must start from ownership and retention class, not
from size or duplicate filenames alone. Use
`npm --prefix scripts run inventory:structure` to review the generated-output
retention buckets before pruning:

1. baselines require explicit metric/rationale notes,
2. dev-workflow and SRS journey latest artifacts support handoff and CI review,
3. experiment payloads require a surviving summary or canonical downstream
   artifact before archival,
4. older phase/sample evidence should be migrated or summarized before removal,
5. root-level latest aliases should be rerouted before any delete/archive move.

## Handoff To Grooming

The next-step grooming queue lives in:

- `documentation_grooming_workstream.md`

That workstream should use this policy as the acceptance standard.
