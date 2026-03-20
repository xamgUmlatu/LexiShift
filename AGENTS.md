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

When a concise handoff is needed from the latest rulegen artifacts:

```bash
npm --prefix scripts run quality:rulegen:benchmark:summary
npm --prefix scripts run quality:rulegen:gate:summary
npm --prefix scripts run quality:rulegen:triage:summary
```

## Primary quality loop (SRS scheduler / admission / publication changes)

If a change touches SRS scheduling, admission refresh, helper publication, set execution, or runtime SRS serving:

1. Run the synthetic SRS quality harness.
2. Render the Markdown summary when a human-facing handoff is needed.
3. Run targeted tests for changed SRS modules.
4. Keep synthetic coverage limits explicit if the touched pair is outside current harness support.

Required command (default artifact):

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json
```

Human-facing summary:

```bash
python3 scripts/testing/srs_quality_summary.py \
  --quality-json docs/test_outputs/srs_quality_latest.json \
  --markdown-out docs/test_outputs/srs_quality_summary_latest.md
```

Current harness coverage:
- bootstrap/publication/runtime diagnostics for `en-ja` and `en-de`
- feedback-cycle pause/resume scenario for `en-ja`
- due-aware publication mismatch surfaced as a warning, not a hard pass/fail gate

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
- Use `docs/developer/documentation_governance.md` for documentation authority, archive, and canonical-routing rules before broad doc cleanup.
- Use `docs/developer/genai_workflow_architecture.md` for agent-role boundaries, model-instance split guidance, and harness policy.
- Prefer `npm --prefix scripts run check` before concluding workflow/tooling changes; it now includes strict Windows parity and strict repo-wide Ruff style in the default repo-safety gate.
- Use `npm --prefix scripts run check:state` when workflow changes update `docs/developer/feature_state_matrix.md` or when a status claim/evidence path changes materially; it compares against `HEAD` and should stay clean before commit.
- Treat the local `pre-push` hook as a mirror of `npm --prefix scripts run check`, not as a separate validation policy.
- Use `npm --prefix scripts run build` when validating build/package workflow changes or when a local build smoke is warranted.
- Use `npm --prefix scripts run build:report` for the full build contract; hosted macOS CI should mirror that exact entrypoint.
- Use `npm --prefix scripts run build:ci:report` when validating non-macOS hosted-runner behavior or CI-safe build normalization.
- Use `npm --prefix scripts run check:windows:parity` when GUI/helper packaging, Windows build parity, helper autostart, native-messaging install, or Windows workflow coverage changes and you need the standalone parity JSON/Markdown artifacts.
- `npm --prefix scripts run check:changed` now infers and runs the Windows parity audit when those files change; Windows CI runs the strict parity variant.
- `npm --prefix scripts run check:changed` now infers heavier quality loops from substantive file changes so Python AST-equivalent churn, JSON pretty-print churn, and Markdown/text reflow do not automatically trigger rulegen audit.
- For GitHub Pages workflow changes or docs-site deployment changes, run `cd docs && bundle exec jekyll build --trace` before concluding the change, and keep `docs/runbooks/github_pages_setup.md` aligned with the active deployment model.

## Source of truth docs

Read before major changes:
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/rulegen_congruity_implementation_plan.md`
- `docs/rulegen/pos_normalization_workstream.md`
- `docs/developer/documentation_governance.md`
- `docs/developer/ai_workflow.md`
- `docs/developer/genai_workflow_architecture.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/windows_gui_parity_workstream.md`
