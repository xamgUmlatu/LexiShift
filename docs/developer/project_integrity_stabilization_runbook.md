# Project Integrity Stabilization Runbook

Status: active stabilization runbook
Role: Runbook / operational
Last updated: 2026-04-15
Last verified: 2026-04-15 clean-tree routing and checkpoint review
Source-of-truth: stabilization instructions only; code/tests/artifacts still decide runtime truth.
Verification: start from a clean worktree, keep seam-specific validation attached to each checkpoint, and run `python3 scripts/dev/check_doc_references.py` before handoff.

Purpose:
- give a follow-on agent a strict operating spec for a stabilization pass,
- reduce contradiction across docs, schemas, helper APIs, extension behavior, and evidence artifacts,
- prioritize project integrity over new feature work.

## Starting Point

- Branch: `codex/veto-data-sources-exp`
- Latest checkpoint when this runbook was written: `dd157c1` (`Port SRS admission preferences into extension UI`)
- Expected starting condition: clean worktree

If the branch is not clean when work begins:

1. stop,
2. identify whether the drift is intentional follow-up work or unrelated residue,
3. restore a clean checkpoint before broad stabilization work.

## Mission

This is not a feature-expansion pass.

The goal is to make the current system easier to trust by doing three things:

1. reconcile documentation with the executable contract,
2. identify and reduce structural/health risks,
3. verify code correctness/integrity on the highest-risk cross-layer seams.

## Non-Negotiable Rules

1. Do not weaken health gates, doc checks, or baselines just to get green.
2. Do not silently promote planning docs into "current truth".
3. Do not mark a feature as effectively shipped unless code/tests/artifacts support the claim.
4. If code and docs disagree, code/tests win; update docs or log the mismatch explicitly.
5. Keep `implemented`, `default-on`, and `verified` separate.
6. Keep the worktree clean at each checkpoint commit.
7. Prefer narrow seam-by-seam commits over broad mixed cleanups.

## Read First

Read these before making stabilization decisions:

1. `AGENTS.md`
2. `docs/developer/documentation_governance.md`
3. `docs/developer/feature_state_matrix.md`
4. `docs/developer/project_health_gate_structure.md`
5. `docs/developer/project_health_remediation_workstream.md`
6. `docs/developer/srs_admission_selective_port_sequence.md`
7. `docs/developer/srs_admission_merge_seam_map.md`
8. `docs/srs/srs_profile_schema.md`
9. `docs/rulegen/semantic_routing_implementation_roadmap.md`
10. `docs/rulegen/semantic_routing_publication_contract.md`
11. `docs/rulegen/semantic_routing_runtime_readiness.md`
12. `docs/rulegen/semantic_routing_data_contract.md`

## Primary Audit Surfaces

Prioritize these seams because they now carry the most integration risk:

### Extension / options / controller graph

- `apps/chrome-extension/options.html`
- `apps/chrome-extension/options/core/bootstrap/`
- `apps/chrome-extension/options/controllers/srs/`
- `apps/chrome-extension/shared/helper/helper_client.js`

### Helper / native host / SRS execution seam

- `scripts/helper/lexishift_native_host.py`
- `core/lexishift_core/helper/engine.py`
- `core/lexishift_core/helper/use_cases/`

### Cross-cutting docs / schema / state ledger

- `docs/developer/feature_state_matrix.md`
- `docs/srs/srs_profile_schema.md`
- `docs/developer/srs_admission_selective_port_sequence.md`
- `docs/rulegen/semantic_routing_*`

## Required Work Order

Do the pass in this order.

### Phase 0: Reconfirm Baseline

Before editing:

1. confirm branch and worktree state,
2. identify latest checkpoint commit,
3. note any open contradictions already documented in `feature_state_matrix.md`,
4. avoid starting with speculative cleanup.

### Phase 1: Documentation Reconciliation

Objective:
- make current docs accurately describe the executable system.

Required actions:

1. identify all docs that make present-tense claims about:
   - semantic veto runtime behavior,
   - helper publication/runtime contracts,
   - SRS profile/planning schema,
   - admission preview/rebalance/options flows.
2. verify those claims against code/tests/artifacts.
3. update docs to match current behavior.
4. if a contradiction cannot be fixed in the same pass, log it explicitly in `docs/developer/feature_state_matrix.md`.

Important rule:
- do not over-generalize schema claims beyond the current implementation.

Examples of acceptable outcomes:
- narrowing docs from "unknown keys are preserved" to "fixed v1 allowlist"
- marking a flow as implemented-but-not-default-on
- noting that a UI scaffold exists while a broader generalization problem remains unresolved

### Phase 2: Health-Risk Audit

Objective:
- identify structural risks before they become harder to unwind.

Required actions:

1. inspect large/high-churn files touched by recent work.
2. split files only when the split follows a real seam.
3. look for:
   - oversized controllers/formatters/workflows,
   - duplicate schema normalization logic,
   - extension/helper message-name drift,
   - docs that route to stale or planning-only surfaces,
   - stale generated evidence being cited as if it were architecture truth.
4. add targeted remediation where it materially reduces future breakage.

Do not:
- do broad mechanical churn without a concrete integrity gain.

### Phase 3: Code Correctness / Integrity Verification

Objective:
- verify the highest-risk cross-layer flows instead of trusting recent momentum.

Use these minimum commands as applicable:

```bash
python3 scripts/dev/check_doc_references.py
git diff --check
npm --prefix scripts run check:changed
```

If the pass touches SRS/admission/publication/runtime surfaces, run:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json
```

If the pass touches extension/helper semantic runtime or the native-host seam, run:

```bash
python3 -m pytest \
  core/tests/helper/test_helper_engine.py \
  core/tests/architecture/test_extension_structure.py \
  core/tests/dev/test_helper_translation_dict_entrypoints.py \
  -q
```

If the pass touches semantic publication/runtime behavior more broadly, also run:

```bash
python3 -m pytest \
  core/tests/rulegen/test_semantic_publication.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py \
  core/tests/helper/test_rulegen_outputs.py \
  -q
```

If the pass touches rulegen scoring/candidate filtering/POS behavior, obey the full AGENTS rulegen loop.

### Phase 4: State Ledger And Handoff Cleanup

Objective:
- leave the repo easier to resume correctly.

Required actions:

1. update `docs/developer/feature_state_matrix.md` for any meaningful status/evidence change.
2. keep known contradictions explicit until fully resolved.
3. ensure routing docs point to the current canonical surfaces.
4. checkpoint cleanly with intentional commit messages.

## Stop Conditions

Stop and hand off instead of forcing through if any of these happen:

1. the branch is not clean and the extra changes are not clearly part of the stabilization pass,
2. a required claim would need baseline/policy weakening to appear verified,
3. a contradiction spans multiple domains and cannot be resolved without feature work,
4. a doc or status claim cannot be tied back to code/tests/artifacts with reasonable confidence.

## Required Deliverables

The agent should leave behind:

1. updated docs that match current code truth,
2. explicit mismatch notes in `feature_state_matrix.md` where needed,
3. any justified integrity refactors needed to reduce health risk,
4. fresh validation evidence for the touched seams,
5. a clean worktree.

## Default Commit Strategy

Prefer this sequence unless a tighter seam suggests otherwise:

1. routing/doc-governance fixes,
2. integrity remediation on one concrete seam,
3. verification and state-ledger cleanup,
4. clean checkpoint commit after each seam.

## Reporting Format

At the end of the pass, report in this order:

1. findings/risks fixed or still open,
2. exact docs updated,
3. exact validations run,
4. remaining unresolved contradictions,
5. next recommended stabilization move.

## Anti-Patterns

Avoid these during the pass:

- broad "cleanup" that mixes docs, schemas, runtime behavior, and unrelated refactors
- updating baselines/policies without explicit rationale
- replacing precise contradictions with vague reassurance
- citing generated outputs as if they were the architecture source-of-truth
- committing with unrelated worktree residue

## Success Condition

This pass is successful if:

1. another contributor can recover current truth faster,
2. the repo has fewer hidden contradictions,
3. the highest-risk seams have fresh evidence,
4. the branch ends cleaner and more trustworthy than it started.
