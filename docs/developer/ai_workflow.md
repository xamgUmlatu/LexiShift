# AI-Assisted Rulegen Iteration Workflow

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
- Triage extractor: `scripts/testing/rulegen_benchmark_triage.py`

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
