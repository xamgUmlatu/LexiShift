# Semantic LLM Generation Budget Reference

Purpose: keep the token and cost arithmetic for semantic-veto LLM generation in one
small reference so future paid batches can be priced before they run and reconciled
after they finish.

This reference is for planning only. Before a live run, re-check the current model
prices on the official [OpenAI API pricing page](https://openai.com/api/pricing/)
and pass the rates explicitly to the run harness.

## Current Price Snapshot

Snapshot date: 2026-05-12.

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
- models that reject sampling controls should be run with
  `--omit-temperature`; the report should then record `selected_temperature:
  null`

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

## Observed Active-Only Scale Tranche Cost Anchor

Artifacts:

- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_generation_run_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_scale_tranche_v1_continue_repair_generation_run_en_es_latest.json`
- `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-active-only-scale-tranche-v1-20260510-001_journal.jsonl`
- `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-active-only-scale-tranche-v1-continue-repair-20260510-001_journal.jsonl`

Observed run shape:

- model: `gpt-5.4-mini`
- request scope: `16` remaining uncovered active-only product-scope families
- accepted active responses after resume: `16`
- admitted active items after repair: `32`
- initial run had one invalid request-id typo that was retried with `--resume
  --retry-invalid-outputs`
- follow-up `continue -> durar` repair run had a request-id metadata typo but
  usable exact-token sentences; the downstream repaired generated-response file
  corrects only request-id metadata and leaves generated sentences unchanged

Latest accepted-run summary:

- input tokens: `7,547`
- output tokens: `2,742`
- actual cost at the 2026-05-09 `gpt-5.4-mini` snapshot: about `$0.018`

Journal-inclusive paid outcomes:

- outcomes: `18` (`16` accepted, `2` invalid metadata/token-shape repair
  attempts)
- input tokens: `8,469`
- output tokens: `3,079`
- actual cost at the 2026-05-09 `gpt-5.4-mini` snapshot: about `$0.020`

This is the best anchor for small active-only continuation tranches. It
confirms that the active-only request shape remains extremely cheap compared
with the `$100` budget; the quality stop remains downstream usefulness, not
price.

## Observed Full Active-Only Tranche 001 Cost Anchor

Artifacts:

- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_generation_run_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_work_repair_generation_run_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_repaired_generation_admission_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_001_source_packaging_en_es_latest.json`
- `docs/test_outputs/semantic_veto_en-es-active-only-combined-full-v1-tranche-001_pack_builder_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_001_pack_install_en_es_latest.json`

Observed run shape:

- model: `gpt-5.4-mini`
- request scope: `42` reviewed/approved uncovered active-only SRS-derived
  source-target families
- main accepted responses: `42/42`
- repaired admitted active items: `84/84`
- one generated item used `works` instead of the exact runtime trigger token
  `work`; a one-request repair plus explicit operator repair produced the final
  admitted response bundle
- source packaging produced `84` canonical `anchor_cue` rows across `42`
  families
- combined pack build now covers `91/570` current SRS-derived source-target
  families with `194` normalized evidence rows

Accepted main-run usage:

- input tokens: `20,992`
- output tokens: `7,411`
- actual cost at the 2026-05-12 `gpt-5.4-mini` snapshot: about `$0.049`

One-request repair usage:

- input tokens: `498`
- output tokens: `172`
- actual cost at the 2026-05-12 `gpt-5.4-mini` snapshot: about `$0.001`

Total accepted main plus repair cost was about `$0.050`. This confirms the
budget posture: even after moving from product-scope pilots to SRS-derived
tranches, active-only cue generation remains cheap. The gating work is now
source-target review, admission quality, and product-feel checks, not dollar
cost.

## Observed Full Active-Only Tranche 002 Cost Anchor

Artifacts:

- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_002_generation_run_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_full_v1_tranche_002_repaired_generation_admission_en_es_latest.json`
- `docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_002_pack_install_en_es_latest.json`

Observed run shape:

- model: `gpt-5.4-mini`
- request scope: `44` reviewed/approved uncovered active-only SRS-derived
  source-target families
- first completed bundle accepted `42/44` responses and reported `2` invalid
  outputs caused by request-id metadata drift
- one guarded retry reproduced those same two metadata mistakes, so the final
  admitted response bundle applied `2` explicit operator repairs that restored
  request/family/slot ids while preserving generated sentence content
- repaired admitted active items: `88/88`
- source packaging produced `88` canonical `anchor_cue` rows across `44`
  families
- combined pack build now covers `135/570` current SRS-derived source-target
  families with `282` normalized evidence rows

Journal-inclusive paid outcome usage:

- outcome events: `46`
- completed outcomes: `42`
- invalid-output outcomes: `4`
- input tokens: `23,080`
- output tokens: `8,297`
- actual cost at the 2026-05-12 `gpt-5.4-mini` snapshot: about `$0.055`

This is slightly more expensive than tranche 001 because two invalid metadata
outputs were retried, but it is still trivial relative to the `$100` budget.
The practical limiter remains reviewed source-target quality and downstream
admission/packaging hygiene.

## Observed Balanced v1 Follow-Through Cost Anchor

Artifact:

- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_generation_run_en_es_latest.json`

Observed latest accepted-run usage:

- requests: `54`
- generated items: `80`
- accepted response summary: `36,840` input tokens / `11,899` output tokens
- journal-inclusive paid outcomes: `37,543` input tokens / `12,085` output tokens
- one invalid request-id output was retried with `--resume --retry-invalid-outputs`

Journal-inclusive actual-cost estimate by model:

| Model | Cost |
| --- | ---: |
| `gpt-5.4-mini` | `$0.083` |
| `gpt-5.4` | `$0.275` |
| `gpt-5.5` | `$0.550` |

This is the better anchor for the current active/shadow/no-winner v7 prompt
shape. It confirms that the `$100` budget is far above the cost of the current
research batches; the constraint is generated-row usefulness, especially
shadow/competitor validity.

## Observed Stronger-Model Shadow Probe Cost Anchor

Artifacts:

- `docs/test_outputs/semantic_veto_product_scope_band_grading_v1_shadow_gpt55_generation_run_en_es_latest.json`
- `docs/test_outputs/experiments/semantic_veto_evidence_gap_batches/en-es-semantic-veto-evidence-gap-generation-product-scope-band-grading-v1-shadow-gpt55-20260510-002_journal.jsonl`

Observed run shape:

- model: `gpt-5.5`
- request scope: the six `high_need` `shadow_or_competitor_evidence_probe`
  requests from `product_scope_band_grading_v1`
- `temperature`: omitted with `--omit-temperature`
- initial max output tokens: `700`
- retry max output tokens: `1400` for the three truncated JSON responses

Accepted-response summary:

- requests: `6`
- accepted responses: `6`
- generated items admitted downstream: `12`
- final accepted-summary usage: `5,216` input tokens / `4,349` output tokens

Journal-inclusive paid outcomes:

- outcomes: `9` (`3` invalid truncated outputs plus `6` accepted outputs)
- input tokens: `7,807`
- output tokens: `6,449`
- reasoning tokens included in output: `3,767`
- cost at the 2026-05-09 `gpt-5.5` snapshot: about `$0.233`

This probe is a useful reminder that final accepted-run summaries can undercount
spend when invalid outputs are retried. For budget reconciliation after retries,
sum usage from the journal, not only the latest accepted response rows.

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

## Full `en-es` Scale Note

The 49-family active-only product-smoke pack is not full `en-es` coverage. It is
the current proven fixture.

The current no-spend denominator pass has now computed the installed
SRS-admissible semantic-family universe for scale planning:

- 1,984 unique full SRS-admissible Spanish targets,
- 570 current generated `en-es` source-target rule families,
- 536 unique English source triggers,
- 342 unique Spanish active targets,
- 135 source-target families currently covered by the combined active-only
  product-smoke plus full-tranche pack,
- 435 active-only uncovered source-target families,
- 150 source-target rows reviewed across the first three pre-spend slices,
- 129 of those reviewed candidates approved for paid active-only generation,
- 21 rejected before spend because they were no-visible or weak source-target
  mappings,
- 414 currently queued source-target families after known cumulative rejections,
- 828 expected active cue rows if the currently queued families are generated
  at 2 rows per family,
- 9 queue tranches after known cumulative rejections, with future tranche rows
  still requiring the same pre-spend source-target review.

The current runnable paid packet is the tranche-003 pre-spend request plan:

- `43` reviewed and approved source-target families,
- `86` expected active cue rows,
- `22,570` estimated input tokens,
- `12,040` output-token budget.

Older table rows such as `common-source active-only pass` remain historical
planning anchors, not the denominator for the whole product. Do not spend
toward broad generated shadows until active-only coverage has been measured and
the remaining harmful-replace cases are known.

## Live-Run Guard Pattern

Every paid run should pass explicit pricing and cardinality guards:

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json <request-packet.json> \
  --json-out <run-output.json> \
  --markdown-out <run-output.md> \
  --batch-dir "$LEXISHIFT_DATA_DIR/language_packs/en-es/semantic_generation_runs/<run-id>" \
  --run-id <stable-run-id> \
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
| next active-only reviewed tranche | `43` | `$1` | `$5` |
| larger active-only tranche | `100` | `$2` | `$10` |
| common-source active-only pass | `344` | `$5` | `$25` |

These caps are intentionally much higher than the expected mini costs but still
prevent accidental runaway spending from a wrong packet, wrong request count, or
wrong model/rate combination.

## Durable Run Artifact Contract

For research-only rehearsals, the default `docs/test_outputs/experiments`
location is acceptable. For actual scale generation, set `--batch-dir` to the
local application data root, for example:

```text
$LEXISHIFT_DATA_DIR/language_packs/en-es/semantic_generation_runs/<run-id>
```

If `LEXISHIFT_DATA_DIR` is not set, the current helper default on macOS is under:

```text
~/Library/Application Support/LexiShift/LexiShift
```

The evidence-gap runner now writes the following run artifacts:

| Artifact | When written | Purpose |
| --- | --- | --- |
| `*_run_manifest.json` | before live spend, finalized after bundle write | Stable run identity, selected request hash, model/prompt metadata, artifact paths, final summary. |
| `*_request_queue.jsonl` | before live spend | Exact selected request rows. This is the queue that can be resumed or audited. |
| `*_journal.jsonl` | during live spend | Append-only resume ledger. Completed outcomes are skipped on `--resume`; ambiguous started-without-outcome rows block automatic resume. |
| `*_raw_responses.jsonl` | immediately after each live outcome, then finalized atomically | Paid source material, including invalid outputs and API errors. This is one of the most important files to back up. |
| `*_failures.jsonl` | immediately after each failed live outcome, then finalized atomically | Invalid output and API-error rows for repair/retry review. |
| `*_raw_responses.json` | final bundle write | Human-readable raw-response bundle used by downstream tooling. |
| `*_generated_responses.json` | final bundle write | Accepted generated responses for admission/postprocess. |

Final JSON/Markdown/JSONL bundle writes are atomic: the runner writes a temp file,
flushes it, and renames it into place. During live execution, append-only journal,
raw-response, and failure events are flushed and fsynced request by request, so an
interruption should lose at most the in-flight request.

Resume policy:

- use the same `--run-id`, request packet, filters, model settings, and
  `--batch-dir`;
- add `--resume`;
- add `--retry-invalid-outputs` only when intentionally retrying invalid model
  output;
- do not hand-edit the journal, raw-response JSONL, or queue files unless doing a
  deliberate recovery with a separate audit note.

## Update Recipe

When a new paid batch finishes:

1. Back up the run directory, especially `*_run_manifest.json`,
   `*_request_queue.jsonl`, `*_journal.jsonl`, `*_raw_responses.jsonl`, and
   `*_failures.jsonl`.
2. Record the selected model, request count, accepted response count, accepted
   item count, `input_tokens`, and `output_tokens`.
3. Compute actual cost with the formula above and the rates used for that run.
4. Compare actual output tokens against the safety estimate and ceiling.
5. Update this document only when the price snapshot changes, the prompt shape
   changes materially, or a new completed run becomes the better scaling anchor.
6. Keep the raw generation run, admission report, and downstream contribution
   report linked from the semantic-veto registry so later batches can be compared
   instead of regenerated blindly.
