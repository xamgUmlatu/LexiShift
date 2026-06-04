# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T19:24:51Z`
- Denominator source-target families: `570`
- Current active-only covered families: `378` (66.3%)
- Uncovered active-only families: `192`
- Runnable request packet families: `38`
- Runnable request packet expected items: `76`
- Runnable request packet estimated input tokens: `21928`
- Runnable request packet output-token budget: `10640`
- Source-target review: `approved:38, excluded:83, unreviewed:71`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 196 | 83.4% | 39 | `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio`, `chase` -> `cazar` |
| `zipf_3_to_4_mid` | 152 | 79 | 52.0% | 73 | `abandonment` -> `cesión`, `abstraction` -> `robo`, `acquaintance` -> `notoriedad`, `bark` -> `barco`, `barn` -> `puesto`, `bleak` -> `lúgubre` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 172 | 78.5% | 47 | `abatement` -> `descuento`, `abstraction` -> `robo`, `acquaint` -> `informar`, `action` -> `batalla`, `affable` -> `gracioso`, `alternation` -> `alternativa` |
| `zipf_3_to_4_mid` | 206 | 123 | 59.7% | 83 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abrogate` -> `abolir`, `acquaintance` -> `notoriedad`, `annotation` -> `anotación`, `ask` -> `demandar` |
| `zipf_below_3_rare` | 61 | 17 | 27.9% | 44 | `abate` -> `decrecer`, `aberration` -> `yerro`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer`, `begrudge` -> `deplorar` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 28618 | 14000 | P2_exposure_first:40, P3_exposure_first:10 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 28142 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 9 | 9 | 18 | 5089 | 2520 | P3_exposure_first:9 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 72 | `P2_exposure_first` | `glove` | `guante` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 73 | `P2_exposure_first` | `goose` | `ganso` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 74 | `P2_exposure_first` | `idol` | `ídolo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 75 | `P2_exposure_first` | `inflammation` | `inflamación` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 77 | `P2_exposure_first` | `intoxicated` | `ebrio` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 78 | `P2_exposure_first` | `jest` | `bromear` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 79 | `P2_exposure_first` | `lick` | `lamer` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 80 | `P2_exposure_first` | `mist` | `niebla` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 81 | `P2_exposure_first` | `mosaic` | `mosaico` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 82 | `P2_exposure_first` | `nameless` | `anónimo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 83 | `P2_exposure_first` | `offspring` | `descendiente` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 84 | `P2_exposure_first` | `patriarch` | `patriarca` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 85 | `P2_exposure_first` | `phenomenal` | `fenomenal` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 86 | `P2_exposure_first` | `pigeon` | `paloma` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 87 | `P2_exposure_first` | `protestant` | `protestante` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 88 | `P2_exposure_first` | `relinquish` | `ceder` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 89 | `P2_exposure_first` | `restrain` | `reprimir` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 91 | `P2_exposure_first` | `romanian` | `rumano` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 92 | `P2_exposure_first` | `satisfy` | `complacer` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 93 | `P2_exposure_first` | `skirt` | `falda` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 95 | `P2_exposure_first` | `subscriber` | `abonado` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 97 | `P2_exposure_first` | `swede` | `sueco` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_narrow_active_mapping` |
| 98 | `P2_exposure_first` | `terrace` | `terraza` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 99 | `P2_exposure_first` | `unmarried` | `soltero` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 100 | `P2_exposure_first` | `urine` | `orina` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 101 | `P2_exposure_first` | `viper` | `víbora` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 102 | `P2_exposure_first` | `wasp` | `avispa` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 103 | `P2_exposure_first` | `wholly` | `enteramente` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 104 | `P2_exposure_first` | `widower` | `viudo` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 105 | `P2_exposure_first` | `willow` | `sauce` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 106 | `P2_exposure_first` | `zinc` | `zinc` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 0.5060 | `approve_direct_mapping` |
| 110 | `P2_exposure_first` | `abatement` | `descuento` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_narrow_active_mapping` |
| 111 | `P2_exposure_first` | `acquaint` | `informar` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_narrow_active_mapping` |
| 114 | `P2_exposure_first` | `barque` | `barco` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_direct_mapping` |
| 117 | `P2_exposure_first` | `depository` | `depósito` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_direct_mapping` |
| 118 | `P2_exposure_first` | `mayhap` | `quizás` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_direct_mapping` |
| 120 | `P2_exposure_first` | `perchance` | `quizás` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_direct_mapping` |
| 121 | `P2_exposure_first` | `repose` | `descansar` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_narrow_active_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_009_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-009-approved \
  --max-requests 38 \
  --require-selected-request-count 38 \
  --expected-output-tokens 280 \
  --input-rate-per-1m <current-input-rate> \
  --output-rate-per-1m <current-output-rate> \
  --max-estimated-cost-usd <small-tranche-budget> \
  --max-estimated-cost-ceiling-usd <small-tranche-ceiling> \
  --execute-live --resume
```

## Guardrails

| Check | Value |
| --- | --- |
| `denominator_present` | `True` |
| `selected_rows_do_not_overlap_existing_coverage` | `True` |
| `request_ids_unique` | `True` |
| `request_family_ids_unique` | `True` |
| `all_requests_active_only` | `True` |
| `all_requests_have_prompt_text` | `True` |
| `all_requests_have_target` | `True` |
| `selected_rows_review_approved_or_review_inactive` | `True` |

## Limitations

- `full denominator is current installed SRS rulegen output, not all possible en-es words`
- `active-only rows do not add repaired shadows or phrase/no-winner controls`
- `Zipf ordering is an exposure queue, not proof of veto difficulty`
- `source-target-only rows have weaker sense hints than manually reviewed families`
- `manual pre-spend source-target review covers only rows present in the review manifest`
- `live generation must be run in small resumable tranches with explicit spend guards`

## Next Steps

- Run the first request tranche only, with --max-requests and --require-selected-request-count matching the selected request count.
- Run postprocess, admission, source packaging, inventory replay, helper smoke, and live-page scan on that tranche before continuing.
- Append admitted rows to the product-smoke active-only pack only after replay shows the same soft-assist behavior.
- Generate shadows only for high-need or observed-harm families after active-only coverage has been measured.
