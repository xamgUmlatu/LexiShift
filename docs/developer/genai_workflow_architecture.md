# GenAI Workflow Architecture

Status: active meta workflow
Last updated: 2026-03-11

## Purpose

This document defines how GenAI-driven implementation work should operate in this repository.

It exists to keep three things explicit:
- which workflow is canonical,
- when independent model instances are required,
- which evidence is needed before a feature can be treated as shipped.

This document extends the existing rulegen/POS quality loop. It does not replace `AGENTS.md` or `ai_workflow.md`.

## Existing Infrastructure To Preserve

These files are already part of the working system and remain canonical:

1. `../../AGENTS.md`
   - Required rulegen/POS benchmark -> gate -> triage loop.
2. `ai_workflow.md`
   - Rulegen/POS-specific iteration workflow.
3. `feature_state_matrix.md`
   - Dated feature-state ledger and mismatch tracker.
4. `../../scripts/testing/rulegen_pair_audit_cycle.py`
   - Existing focused wrapper around the canonical rulegen loop.
5. `../../scripts/testing/rulegen_auto_audit.py`
   - Change-aware wrapper that infers touched pairs and manages dated plus `*_latest` artifacts.

If a future meta workflow conflicts with those files, update the conflict explicitly rather than silently assuming the newer text wins.

## Operating Principles

1. Source code remains the primary truth.
2. Docs must distinguish `planned`, `scaffolded`, `implemented`, `default-on`, and `verified`.
3. Quality-affecting changes require explicit artifacts, not just narrative claims.
4. Wrapper scripts may orchestrate the canonical loop, but they must not hide or replace the underlying commands.
5. Known doc/code mismatches stay visible until they are resolved and re-verified.
6. GenAI should propose and implement changes; harnesses and independent review should certify them.

## Agent Roles

Use small, bounded roles rather than one broad autonomous agent.

### 1. Researcher

- Reads only the necessary docs, code, and current artifacts.
- Produces:
  - current behavior summary,
  - relevant source-of-truth files,
  - last verified artifact paths,
  - open contradictions.

### 2. Planner

- Converts the state summary into a bounded change plan.
- Must define:
  - acceptance criteria,
  - touched language pairs,
  - required harness runs,
  - rollback conditions,
  - whether a fresh reviewer instance is required.

### 3. Implementer

- Makes the code or doc changes only.
- Must not silently update:
  - benchmark baselines,
  - benchmark labels,
  - grading policy,
  - release defaults.

### 4. Reviewer

- Uses a fresh model instance for non-trivial work.
- Focuses on:
  - bugs,
  - regressions,
  - missing tests,
  - unsafe assumptions,
  - harness blind spots.

### 5. Evaluator

- Runs the harness and reports what changed.
- Must separate:
  - capability movement,
  - regression risk,
  - harness ambiguity,
  - non-comparable runs.

### 6. Curator

- Converts failures and newly learned facts into durable repo state.
- Typical outputs:
  - benchmark case updates,
  - triage notes,
  - `feature_state_matrix.md` updates,
  - follow-up workstream docs.

## When To Use Separate Model Instances

Use a fresh model instance when independence matters more than shared context.

### Separate instance required

1. Review after non-trivial implementation.
2. Benchmark triage and benchmark-label suggestions.
3. Benchmark policy, baseline, or grader changes.
4. Prompt or workflow-contract changes that affect many future runs.
5. High-risk ranking or SRS logic changes.
6. Any model-assisted judging/grading flow.

### Same instance is acceptable

1. Small local refactors with deterministic tests.
2. One-file doc updates.
3. Narrow tooling changes with obvious CLI verification.
4. Cases where strict automated checks fully determine success.

## Harness Architecture

Treat the harness as product infrastructure.

Every meaningful quality run should answer:
1. What changed?
2. What was expected to improve?
3. Did quality move?
4. Did regressions appear?
5. Can the result be trusted?

### Layer 1: Fast deterministic checks

- Targeted unit tests for changed modules.
- Syntax checks.
- Serialization and schema checks.

### Layer 2: Capability evals

- Benchmark sweeps for touched pairs.
- Reverse-check `off/on` experiments when ranking behavior changes.
- Pair-specific summary metrics and top-run comparisons.

### Layer 3: Regression evals

- Fixed must-pass cases for previously resolved failures.
- Stable case sets kept separate from exploratory capability sweeps.

### Layer 4: Harness health checks

- Saturation warnings.
- Ambiguous or low-sensitivity sweeps.
- Changed grader/policy/baseline detection.

### Layer 5: Artifact and transcript review

- Read failure cases and suspicious wins directly.
- Promote durable failures into benchmark or workstream artifacts.

## Rulegen Workflow

### Canonical commands

The canonical rulegen loop remains the benchmark -> quality gate -> triage sequence in `../../AGENTS.md`.

### Preferred wrappers

Use these wrappers when they fit the change:

```bash
python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-es
python3 scripts/testing/rulegen_auto_audit.py --base-ref origin/main
python3 scripts/testing/rulegen_auto_audit.py --pairs en-es --reverse-check-profile experiment --strict-gate
```

Wrapper policy:
- `rulegen_pair_audit_cycle.py` remains the focused orchestration layer.
- `rulegen_auto_audit.py` adds:
  - changed-file pair inference,
  - dated artifact paths,
  - `*_latest` alias updates,
  - manifest output for run provenance.
- `rulegen_quality_gate_summary.py` is the preferred human-facing renderer for gate JSON in CI and handoff docs.

Use the canonical commands directly when:
- wrapper defaults are not appropriate,
- you need full control over artifacts or sweep inputs,
- pair inference would be ambiguous.

## Artifact Policy

For generated quality artifacts:

1. Write immutable dated outputs for every meaningful run.
2. Update `*_latest` aliases only from the same run.
3. Store run provenance with the artifacts when possible.
4. Treat runs as non-comparable when policy, baseline, benchmark labels, or grading semantics changed.

Recommended artifact pattern:
- dated files: `..._2026-03-11.json`
- latest aliases: `..._latest.json`
- manifest: `rulegen_auto_audit_<pair_suffix>_2026-03-11.json`

## Repository Safety Commands

Use these commands for general repo safeties before feature work expands:

```bash
npm --prefix scripts run check
npm --prefix scripts run build
```

Current intent:
- `check` is stable and non-mutating.
- `check:changed` is the preferred branch-scope workflow command before heavier quality work.
- `build` is a local build smoke for maintained build surfaces.
- `check:style` is the advisory path for repo-wide Ruff debt.
- `check:report`, `check:changed:report`, and `build:report` are the machine-readable workflow surfaces for automation and agent hand-offs.
- `check:summary` renders a stable Markdown handoff from the JSON workflow reports and is the preferred human-facing summary layer.
- local `pre-push` should mirror `check`, not a separate ad hoc command set.
- Repo-wide style lint is intentionally not part of default `check` until existing Ruff debt is reduced.

When a workflow stage is consumed by another agent step, prefer the JSON-report variants over scraping terminal output.
When branch-scope change reports are dominated by earlier branch work, use `check:changed:local` or `check:changed:staged` for the current edit loop and keep `check:changed` as the broader integration signal.

## Feature-State Discipline

Use `feature_state_matrix.md` as the repo ledger for workflow state.

Update it when:
1. a feature moves between `planned`, `scaffolded`, `implemented`, `default-on`, or `verified`,
2. default behavior changes,
3. an artifact becomes the new verification point,
4. a doc/code mismatch is discovered or resolved,
5. a strategy becomes executable rather than planning-only.

Do not collapse these states into a single "done" label.

## Human Escalation Points

Require explicit human review or sign-off for:

1. benchmark baseline changes,
2. quality policy threshold changes,
3. benchmark label updates that redefine expected quality,
4. release-default toggles,
5. harness grader changes,
6. destructive migrations or data resets.

## Current Repository Mismatches To Preserve Explicitly

These are active mismatches, not wording accidents:

1. Reverse-check is implemented and tunable, but not yet default-on.
2. SRS docs define due-aware serving, but current helper publication and runtime gating are not yet verified as due-aware end to end.
3. Rulegen docs describe runtime confidence filtering, but extension-side helper-rule confidence gating is not yet verified in code.
4. SRS planner docs describe multiple strategies, but executable behavior is still dominated by `frequency_bootstrap`.

These items should remain visible in `feature_state_matrix.md` until code, docs, and artifacts converge.

## Near-Term Meta Priorities

1. Keep reverse-check experiments in the standard audit loop while the feature is being tuned.
2. Extend the same artifact discipline to SRS quality work once due-aware serving starts.
3. Preserve a fresh-reviewer step for ranking, SRS scheduler, and harness changes.
4. Keep feature-state dates exact so future agents can recover current behavior quickly.
