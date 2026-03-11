# AGENTS

Repository-local instructions for AI coding agents.

## Primary quality loop (rulegen / POS changes)

If a change touches rulegen scoring, candidate filtering, POS normalization, or LP tuning:

1. Run benchmark sweep for touched pairs.
2. Run quality gate.
3. Run benchmark triage extraction.
4. Run targeted tests for changed modules.

Required commands (default artifacts):

```bash
python3 scripts/testing/rulegen_benchmark.py \
  --pairs en-es \
  --json-output docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --markdown-output docs/test_outputs/rulegen_benchmark_en_es_latest.md \
  --html-output docs/test_outputs/rulegen_benchmark_en_es_latest.html

python3 scripts/testing/rulegen_quality_gate.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --policy-json docs/test_inputs/rulegen_quality_policy.json \
  --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json \
  --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json \
  --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json

python3 scripts/testing/rulegen_benchmark_triage.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --json-out docs/test_outputs/rulegen_benchmark_triage_latest.json \
  --markdown-out docs/test_outputs/rulegen_benchmark_triage_latest.md
```

Convenience wrappers may orchestrate the same loop, but they do not replace the canonical commands above:

```bash
python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-es
python3 scripts/testing/rulegen_auto_audit.py --base-ref origin/main
```

## Baseline and policy safety

- Do not update `docs/test_outputs/baselines/rulegen_quality_baseline.json` in routine tuning PRs.
- Baseline update requires explicit rationale and metric delta notes.
- Keep `docs/test_inputs/rulegen_quality_policy.json` thresholds conservative; tighten only with supporting pair coverage.

## Failure-to-case promotion

For each FAIL/REVIEW triage item:
- either update benchmark cases in `docs/test_inputs/rulegen_benchmark_cases.json`,
- or document why it remains unresolved.

## Meta workflow and state tracking

- For workflow/meta changes, keep `implemented`, `default-on`, and `verified` as separate states.
- Update `docs/developer/feature_state_matrix.md` when default behavior, verification evidence, or known doc/code mismatches change.
- Keep known contradictions explicit until code and docs converge; do not silently mark features as shipped based on docs alone.
- Use `docs/developer/genai_workflow_architecture.md` for agent-role boundaries, model-instance split guidance, and harness policy.
- Prefer `npm --prefix scripts run check` before concluding workflow/tooling changes.
- Treat the local `pre-push` hook as a mirror of `npm --prefix scripts run check`, not as a separate validation policy.
- Use `npm --prefix scripts run build` when validating build/package workflow changes or when a local build smoke is warranted.

## Source of truth docs

Read before major changes:
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/rulegen_congruity_implementation_plan.md`
- `docs/rulegen/pos_normalization_workstream.md`
- `docs/developer/ai_workflow.md`
- `docs/developer/genai_workflow_architecture.md`
- `docs/developer/feature_state_matrix.md`
