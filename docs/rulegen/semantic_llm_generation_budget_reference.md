# Semantic LLM Generation Budget Reference

Purpose: keep the token and cost arithmetic for semantic-veto LLM generation in one
small reference so future paid batches can be priced before they run and reconciled
after they finish.

This reference is for planning only. Before a live run, re-check the current model
prices on the official [OpenAI API pricing page](https://openai.com/api/pricing/)
and pass the rates explicitly to the run harness.

## Current Price Snapshot

Snapshot date: 2026-05-09.

| Model | Input / 1M tokens | Output / 1M tokens | Notes |
| --- | ---: | ---: | --- |
| `gpt-5.4-mini` | `$0.75` | `$4.50` | Current default for the evidence-gap run harness. |
| `gpt-5.4` | `$2.50` | `$15.00` | Use only when a measured mini-quality limit justifies it. |
| `gpt-5.5` | `$5.00` | `$30.00` | Use only for narrow confirmation or hard rows. |

The OpenAI pricing page also lists Batch API as 50% cheaper for inputs and
outputs, with asynchronous completion over roughly a day. Use Batch only when
latency does not matter; current semantic-veto batches are small enough that
standard processing is already inexpensive.

## Formula

For a completed run:

```text
actual_cost =
  (actual_input_tokens / 1_000_000) * input_rate_per_1m
  + (actual_output_tokens / 1_000_000) * output_rate_per_1m
```

For a planned run:

```text
estimated_cost_expected =
  (estimated_input_tokens / 1_000_000) * input_rate_per_1m
  + (request_count * expected_output_tokens / 1_000_000) * output_rate_per_1m

estimated_cost_ceiling =
  (estimated_input_tokens / 1_000_000) * input_rate_per_1m
  + (request_count * max_output_tokens / 1_000_000) * output_rate_per_1m
```

Current harness defaults:

- `chars_per_token`: `4.0`
- `expected_output_tokens`: `180`
- `max_output_tokens`: `700`
- default model: `gpt-5.4-mini`

Implementation anchor:

- `scripts/testing/semantic_veto_evidence_gap_generation_run_safety.py`
- `scripts/testing/semantic_veto_evidence_gap_generation_run_core.py`

## Observed Active-Only PoC Cost Anchor

Artifact:

- `docs/test_outputs/semantic_veto_evidence_gap_generation_run_active_only_poc_en_es_latest.json`

Observed usage:

- requests: `24`
- generated items: `48`
- input tokens: `11,421`
- output tokens: `4,177`
- average input tokens per request: `475.875`
- average output tokens per request: `174.042`

Actual-cost estimate by model:

| Model | Cost |
| --- | ---: |
| `gpt-5.4-mini` | `$0.027` |
| `gpt-5.4` | `$0.091` |
| `gpt-5.5` | `$0.182` |

The active-only PoC is a useful scaling anchor because it used the current
generation prompt shape and accepted all `24` responses without invalid outputs.
It should not be treated as a guarantee for longer prompt shapes such as
shadow, phrase/no-winner, or judge/review prompts.

## Scaled Planning Estimates

These estimates scale from the observed active-only PoC token mix. They are
good enough for budget planning, but a new prompt shape should run the safety
report before execution.

| Planned batch | Approx requests | Approx rows | Mini | GPT-5.4 | GPT-5.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| active-only tranche | `50` | `100` | `$0.057` | `$0.190` | `$0.380` |
| active-only tranche | `100` | `200` | `$0.114` | `$0.380` | `$0.760` |
| common-source active-only coverage | `344` | `688` | `$0.392` | `$1.307` | `$2.615` |
| current top-25 priority packet | `62` | `124` | `$0.071` | `$0.236` | `$0.471` |

Mini expected and ceiling estimates using the harness defaults:

| Planned requests | Expected cost | Max-output ceiling |
| ---: | ---: | ---: |
| `50` | `$0.058` | `$0.175` |
| `100` | `$0.117` | `$0.351` |
| `344` | `$0.401` | `$1.206` |
| `62` | `$0.072` | `$0.217` |

## Budget Posture

The current `$100` budget is not the limiting factor for the planned generation
scale. At the observed active-only token mix, even `gpt-5.5` stays in the low
dollars for hundreds of requests.

The limiting factor is data validity:

- whether generated rows target the right source-target sense,
- whether shadow rows are real competitor contexts,
- whether phrase/no-winner rows exercise actual replacement triggers,
- and whether the generated evidence improves frozen evaluation after admission.

Spend should therefore be controlled by tranche quality, not by attempting to
use the whole budget. A small tranche that fails downstream should stop the
current prompt path even if almost no budget was spent.

## Live-Run Guard Pattern

Every paid run should pass explicit pricing and cardinality guards:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-packet <request-packet.json> \
  --json-out <run-output.json> \
  --markdown-out <run-output.md> \
  --execute-live \
  --model-id gpt-5.4-mini \
  --input-rate-per-1m 0.75 \
  --output-rate-per-1m 4.50 \
  --require-selected-request-count <expected-request-count> \
  --max-estimated-cost-usd <expected-cost-cap> \
  --max-estimated-cost-ceiling-usd <ceiling-cost-cap>
```

Recommended initial caps:

| Batch | `--require-selected-request-count` | Expected cap | Ceiling cap |
| --- | ---: | ---: | ---: |
| next active-only tranche | `50` | `$1` | `$5` |
| larger active-only tranche | `100` | `$2` | `$10` |
| common-source active-only pass | `344` | `$5` | `$25` |

These caps are intentionally much higher than the expected mini costs but still
prevent accidental runaway spending from a wrong packet, wrong request count, or
wrong model/rate combination.

## Update Recipe

When a new paid batch finishes:

1. Record the selected model, request count, accepted response count, accepted
   item count, `input_tokens`, and `output_tokens`.
2. Compute actual cost with the formula above and the rates used for that run.
3. Compare actual output tokens against the safety estimate and ceiling.
4. Update this document only when the price snapshot changes, the prompt shape
   changes materially, or a new completed run becomes the better scaling anchor.
5. Keep the raw generation run, admission report, and downstream contribution
   report linked from the semantic-veto registry so later batches can be compared
   instead of regenerated blindly.
