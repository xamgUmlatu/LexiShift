# SP7 SRS Quality Artifact Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 harness publication normalization plus targeted tests
Purpose: bound the first SP7 slice around SRS quality evidence-artifact churn so the published `latest` JSON stays reviewable across behavior-preserving reruns without changing the underlying harness semantics
Source-of-truth: packet only; executable truth still lives in the harness code, targeted tests, generated artifacts, and `feature_state_matrix.md`
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `../srs/srs_helper_practical_guide.md`
- `../../scripts/testing/srs_quality_harness.py`
- `../../scripts/testing/srs_quality_summary.py`
- `../../core/tests/dev/test_srs_quality_harness.py`
- `../../core/tests/dev/test_srs_quality_summary.py`

## Slice

- Track: `SP7`
- Slice: evidence-artifact normalization
- Title: SRS quality latest-artifact stabilization
- Pass type: tooling-noise reduction

## Exact Seam

Primary code/evidence surface:

- `scripts/testing/srs_quality_harness.py`
- `core/tests/dev/test_srs_quality_harness.py`
- `docs/test_outputs/srs_quality_latest.json`
- `docs/test_outputs/srs_quality_summary_latest.md`

Primary docs/state surface:

- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- SRS scheduler correctness or scoring semantics
- expansion of harness pair coverage beyond the current `en-ja` / `en-de` lanes
- the due-aware warning policy
- broader generated-artifact normalization across unrelated harnesses

## Risk Score

- likelihood: `medium`
- blast radius: `low`
- observability: `high`
- priority: `medium`

Reasoning:

- the underlying harness behavior was already useful, but the published JSON mixed stable contract data with rerun-local temp paths, timestamps, and generation ids
- that noise did not break product behavior, but it made evidence refreshes harder to review and could hide the smaller contract changes that actually matter

## Contract Sketch

The intended current SP7 artifact-publication contract is:

1. the in-memory harness report can retain full raw details for local callers and debugging
2. the committed `docs/test_outputs/srs_quality_latest.json` artifact should normalize transient publication noise
3. normalization must preserve stable semantic content:
   - summary counts and statuses
   - pair/scenario structure
   - stable pack identities and diagnostics fields
4. the summary renderer should continue to consume the published JSON without special-case logic

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| The `latest` JSON artifact used to churn on temp-root paths, timestamps, and generation ids even when harness semantics were unchanged. | `N-016`, prior artifact diffs | direct artifact inspection before this slice | `verified before this slice` |
| Publication-side normalization can remove that noise without mutating stable contract fields. | `scripts/testing/srs_quality_harness.py` | `core/tests/dev/test_srs_quality_harness.py` | `fixed in this slice` |
| The human-facing summary still renders from the normalized JSON artifact. | `scripts/testing/srs_quality_summary.py` | targeted summary test plus rerender in this slice | `verified in this slice` |
| The SRS harness state-ledger row should reflect that the published artifact is now stable by design rather than by convention. | `feature_state_matrix.md` | direct doc/state update in this slice | `fixed in this slice` |

## Invariants

1. behavior-preserving harness reruns should not produce large diffs from temp directories or wall-clock metadata alone
2. stable identifiers such as pair names, pack ids, counts, and warning/fail semantics must remain unchanged
3. raw runtime detail should be normalized only at the published-artifact boundary, not stripped from the harness internals wholesale
4. the summary renderer must keep working against the normalized artifact without a forked schema

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Maintainer reruns the harness with no behavioral change | published JSON keeps the same stable placeholders instead of fresh temp/timestamp churn |
| Maintainer reviews a real harness delta | meaningful count/status/diagnostic changes remain visible because transient noise is reduced |
| Summary markdown is regenerated from the normalized JSON | summary output remains unchanged except where real harness results changed |
| Python caller uses the raw report object before publication | raw values remain available because normalization is publication-only |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_srs_quality_harness.py core/tests/dev/test_srs_quality_summary.py -q`
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
- `python3 scripts/testing/srs_quality_summary.py --quality-json docs/test_outputs/srs_quality_latest.json --markdown-out docs/test_outputs/srs_quality_summary_latest.md`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. normalize only the committed `latest` JSON publication path
2. add focused regression coverage for temp paths, timestamps, generation ids, and raw-report immutability
3. update the state ledger so the artifact-stability contract is explicit
4. resolve `N-016` once the published artifact and docs agree

## Outcome

Result:

- `docs/test_outputs/srs_quality_latest.json` now publishes a stable `artifact_normalization` contract and replaces rerun-local temp roots, timestamps, and generation-id suffixes with fixed placeholders
- the raw harness report remains available before publication, so this slice reduced review noise without throwing away local debugging detail
- evidence refreshes for the SRS harness should now surface semantic changes more clearly because the largest rerun-only churn was removed
