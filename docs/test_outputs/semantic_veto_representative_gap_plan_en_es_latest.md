# en-es Semantic Veto Representative Gap Plan

- Status: `ok`
- Decision: `representative_gap_closed`
- Generated: `2026-05-05T18:21:51Z`
- Remaining representative rows needed: `0`
- Open primary collection slots: `0`
- LLM locked proxy rows available: `16`

## Source Audit

| Source | Class | Rows/Quota | Primary Eligible | Reason |
| --- | --- | ---: | --- | --- |
| `current_stage1_representative_frame` | `current_primary_proxy_frame` | `120` | `False` | Representative target is currently filled in Stage 1. |
| `existing_product_quality_stress_rows` | `stress` | `48` | `False` | Stress rows are known hard cases and would bias representative estimates. |
| `existing_llm_pilot_locked_eval_rows` | `generated_proxy` | `16` | `False` | Generated pilot rows can be proxy diagnostics, not primary browsing evidence. |
| `existing_llm_pilot_discovery_rows` | `generated_discovery` | `56` | `False` | Discovery rows are not locked representative rows. |
| `runtime_observed_semantic_admit_contexts` | `primary_observed` | `0` | `True` | Deferred preferred source. Export normal helper/browser semantic-admit candidate contexts with trigger, candidate replacement, page sentence, profile/pair metadata, and no score/outcome filtering when observed logs are available. |
| `corpus_sampled_app_candidate_contexts` | `primary_corpus_proxy` | `25` | `True` | Sample corpus-like English sentences for normal admitted source-trigger and target-candidate pairs by frequency or expected exposure, then label after sampling. |
| `llm_pilot_locked_eval_proxy_backstop` | `generated_proxy_backstop` | `0` | `False` | Existing locked LLM pilot rows may exercise scoring and reporting if primary rows lag, but must not be counted as representative browsing rows. |

## Open Slots

_No open slots._

## Proxy Backstop

| Row | Trigger | Gold Type | Counts Primary? | Sentence |
| --- | --- | --- | --- | --- |
| `pilotrow:pilot_bank_banco:positive_active:001` | `bank` | `positive_active` | `False` | The bank approved the loan after reviewing the business plan. |
| `pilotrow:pilot_bank_banco:positive_active:002` | `bank` | `positive_active` | `False` | For the quarterly treasury review, the auditors confirmed that the bank held the reserve funds securely. |
| `pilotrow:pilot_board_tablero:positive_active:003` | `board` | `positive_active` | `False` | The board, mounted above the desk, shows today’s schedule clearly. |
| `pilotrow:pilot_branch_sucursal:positive_active:001` | `branch` | `positive_active` | `False` | The branch, just off Main Street, opens at nine. |
| `pilotrow:pilot_check_cheque:positive_active:001` | `check` | `positive_active` | `False` | Deposit the check today at the bank. |
| `pilotrow:pilot_file_archivo:shadow_negative:001` | `file` | `shadow_negative` | `False` | Breaking news: the file on the table was a sharp metal tool, not a document. |
| `pilotrow:pilot_file_archivo:shadow_negative:002` | `file` | `shadow_negative` | `False` | The technician checked the server logs, and the file on the drill bit was worn smooth. |
| `pilotrow:pilot_match_partido:phrase_no_winner:001` | `match` | `phrase_no_winner` | `False` | The colors on the new sofa match the curtains, and the room feels brighter after the renovation. |
| `pilotrow:pilot_match_partido:shadow_negative:002` | `match` | `shadow_negative` | `False` | The technician checked whether the connector pins match the socket after the firmware update. |
| `pilotrow:pilot_order_pedido:positive_active:001` | `order` | `positive_active` | `False` | The order, placed online after the sale, ships tomorrow. |
| `pilotrow:pilot_play_obra:positive_active:003` | `play` | `positive_active` | `False` | The play adaptation opened to strong reviews on the streaming site. |
| `pilotrow:pilot_play_obra:shadow_negative:002` | `play` | `shadow_negative` | `False` | The server logs show a failed play in the deployment pipeline. |

## Methodology

- Primary rule: Only rows sampled from normal observed or corpus-like app candidate contexts before scoring can fill the primary representative shortfall.
- Proxy rule: Generated or targeted rows may be used as temporary proxy/backstop diagnostics, but they do not count toward the primary representative product-quality target.
- Random seed: `semantic_veto_representative_gap_en_es_v1_2026_05_06`
- Do not fill representative product rows with targeted P0, stress, or known-failure rows.
- Sample source trigger, candidate replacement, and context before scoring.
- Label rows only after sampling, and keep product-like sampling separate from discovery hypotheses.
- Generated rows may be used as temporary backstop diagnostics, but they do not count toward primary representative product estimates.
- Corpus-like app-candidate proxy rows may fill the current primary-proxy target only when their sampling frame is independent of scorer outcomes and targeted failure cells.
- Keep the current closure caveat visible until the 25 corpus-like rows are human-reviewed or replaced by observed runtime/browser contexts.

## Next Steps

- Human-review the 25 corpus-like representative gap rows before using them for promotion claims.
- Keep the filled 120-row representative scoring and product-quality reports current after any row review or source refresh.
- Prefer observed semantic-admit contexts for the next representative refresh when browser/helper logs are available.
- Keep LLM pilot locked rows as proxy diagnostics only; do not count them as observed representative browsing rows.
