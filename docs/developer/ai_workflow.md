# AI-Assisted Rulegen Iteration Workflow

Status: active workflow
Last updated: 2026-03-11

Purpose:
- Keep rulegen tuning fast without sacrificing stability.
- Make each tuning change measurable, reviewable, and reversible.
- Convert benchmark failures into durable labeled cases.

This workflow is focused on rulegen/POS quality loops, not general coding.

## Why this exists

Rulegen quality changes can look successful while still being brittle if:
- benchmark coverage is too small,
- many parameter sets collapse to identical scores,
- POS drift silently changes candidate quality,
- case failures are not promoted back into benchmark labels.

The scripts and policy below enforce a tighter loop.

## Source files

- Benchmark dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
- Quality policy: `docs/test_inputs/rulegen_quality_policy.json`
- Baseline metrics: `docs/test_outputs/baselines/rulegen_quality_baseline.json`
- Benchmark runner: `scripts/testing/rulegen_benchmark.py`
- Quality gate: `scripts/testing/rulegen_quality_gate.py`
- Quality gate summary renderer: `scripts/testing/rulegen_quality_gate_summary.py`
- Triage extractor: `scripts/testing/rulegen_benchmark_triage.py`
- Focused audit wrapper: `scripts/testing/rulegen_pair_audit_cycle.py`
- Change-aware audit wrapper: `scripts/testing/rulegen_auto_audit.py`
- Feature state ledger: `docs/developer/feature_state_matrix.md`
- GenAI workflow contract: `docs/developer/genai_workflow_architecture.md`

## Standard loop

1. Run a benchmark sweep for the pair(s) you touched.

```bash
python3 scripts/testing/rulegen_benchmark.py \
  --pairs en-es \
  --json-output docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --markdown-output docs/test_outputs/rulegen_benchmark_en_es_latest.md \
  --html-output docs/test_outputs/rulegen_benchmark_en_es_latest.html
```

2. Run the quality gate.

```bash
python3 scripts/testing/rulegen_quality_gate.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --policy-json docs/test_inputs/rulegen_quality_policy.json \
  --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json \
  --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json \
  --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json
```

3. Generate triage artifacts from best-run failures/review cases.

```bash
python3 scripts/testing/rulegen_benchmark_triage.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --json-out docs/test_outputs/rulegen_benchmark_triage_latest.json \
  --markdown-out docs/test_outputs/rulegen_benchmark_triage_latest.md
```

4. Promote triage items into benchmark labels.
- Update `docs/test_inputs/rulegen_benchmark_cases.json`.
- Add/adjust `expected_top1_any`, `forbidden_top1`, `forbidden_any`, and `tier`.

5. Re-run steps 1-3 until gate passes and triage is empty (or clearly justified).

## Preferred wrappers

The commands above remain canonical. Use these wrappers when they fit the change:

```bash
python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-es
python3 scripts/testing/rulegen_auto_audit.py --base-ref origin/main
python3 scripts/testing/rulegen_auto_audit.py --pairs en-es --reverse-check-profile experiment --strict-gate
```

Wrapper responsibilities:
- `rulegen_pair_audit_cycle.py`
  - runs benchmark -> quality gate -> triage with one command,
  - forwards tuning knobs and emits summarized output.
- `rulegen_auto_audit.py`
  - infers touched rulegen pairs from git changes,
  - writes dated artifacts,
  - refreshes `*_latest` aliases,
  - records a manifest for run provenance.

Use direct commands instead of the wrappers when pair inference is ambiguous or artifact paths need manual control.

## Policy mechanics

`rulegen_quality_policy.json` currently enforces:
- required benchmark pair coverage (`en-es` hard-gated now, others recommended),
- dataset field/tier contract (`smoke` / `hard`),
- per-pair quality floors,
- delta budgets versus baseline,
- saturation warnings for low-sensitivity sweeps,
- POS mismatch and unknown-tag growth guardrails.

## Baseline update policy

Do not update baseline for a routine tuning PR.

Update `docs/test_outputs/baselines/rulegen_quality_baseline.json` only when:
- quality policy intentionally changes,
- benchmark dataset meaningfully expands,
- or a reviewed quality shift is accepted as the new target.

When baseline is updated, include in PR notes:
- old vs new metrics,
- why shift is intentional,
- rollback strategy.

## Artifact policy

For meaningful runs:

1. Keep immutable dated artifacts.
2. Update `*_latest` aliases from the same run.
3. Treat runs as non-comparable if policy, baseline, grader, or benchmark labels changed.
4. Preserve enough run metadata to recover the exact sweep later.

The auto-audit wrapper handles this automatically for standard rulegen runs.

When a human-facing summary is needed from the gate artifact, use:

```bash
npm --prefix scripts run quality:rulegen:gate:summary
```

## State tracking

Update `feature_state_matrix.md` when:
- default behavior changes,
- a feature becomes executable or default-on,
- the latest verification artifact changes materially,
- a doc/code mismatch is discovered or resolved.

Examples that should stay explicit:
- reverse-check implemented but not default-on,
- due-aware SRS serving documented but not end-to-end verified,
- extension-side helper-rule confidence gating documented but not code-verified.

## Future extension path

Current artifact gate is strict for `en-es` and advisory for `en-ja` / `en-de` / `es-en` until those pair artifacts are produced regularly.

As pair coverage matures:
1. Add those pairs to `required_benchmark_pairs`.
2. Tighten per-pair floors and delta budgets.
3. Enable stricter saturation mode (`--strict-saturation`) in CI/local gates.

## AI usage guidance

Use AI to accelerate:
- proposing new benchmark cases from triage output,
- summarizing sweep deltas,
- proposing candidate POS mappings for unknown tags.

Keep human review mandatory for:
- benchmark label updates,
- baseline changes,
- quality policy threshold changes.

Use a fresh reviewer/evaluator instance for:
- ranking logic changes,
- reverse-check tuning rollouts,
- benchmark policy or harness changes,
- any change that would redefine default quality claims.
