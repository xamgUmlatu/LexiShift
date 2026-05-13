# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-13T20:15:10Z`
- Denominator source-target families: `570`
- Current active-only covered families: `416` (73.0%)
- Uncovered active-only families: `154`
- Runnable request packet families: `30`
- Runnable request packet expected items: `60`
- Runnable request packet estimated input tokens: `17431`
- Runnable request packet output-token budget: `8400`
- Source-target review: `approved:30, excluded:103, unreviewed:21`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 196 | 83.4% | 39 | `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio`, `chase` -> `cazar` |
| `zipf_3_to_4_mid` | 152 | 110 | 72.4% | 42 | `abandonment` -> `cesión`, `abstraction` -> `robo`, `acquaintance` -> `notoriedad`, `bark` -> `barco`, `barn` -> `puesto`, `bleak` -> `lúgubre` |
| `zipf_below_3_rare` | 52 | 15 | 28.8% | 37 | `abate` -> `decrecer`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `admonition` -> `exhortación`, `affable` -> `gracioso` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 179 | 81.7% | 40 | `abstraction` -> `robo`, `action` -> `batalla`, `affable` -> `gracioso`, `alternation` -> `alternativa`, `bark` -> `barco`, `beburntdown` -> `quemar` |
| `zipf_3_to_4_mid` | 206 | 154 | 74.8% | 52 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abrogate` -> `abolir`, `acquaintance` -> `notoriedad`, `annotation` -> `anotación`, `ask` -> `demandar` |
| `zipf_below_3_rare` | 61 | 17 | 27.9% | 44 | `abate` -> `decrecer`, `aberration` -> `yerro`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer`, `begrudge` -> `deplorar` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 28730 | 14000 | P2_exposure_first:2, P3_exposure_first:48 |
| `en-es-active-only-full-v1-tranche-002` | 1 | 1 | 2 | 574 | 280 | P3_exposure_first:1 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 84 | `P2_exposure_first` | `scuffle` | `batalla` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_narrow_active_mapping` |
| 85 | `P2_exposure_first` | `skilful` | `experto` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 0.4795 | `approve_narrow_active_mapping` |
| 86 | `P3_exposure_first` | `bleak` | `lúgubre` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 87 | `P3_exposure_first` | `blunt` | `despuntar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 88 | `P3_exposure_first` | `diminish` | `decrecer` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 89 | `P3_exposure_first` | `dismal` | `lúgubre` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 91 | `P3_exposure_first` | `dreary` | `lúgubre` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 92 | `P3_exposure_first` | `envious` | `envidioso` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 94 | `P3_exposure_first` | `inflate` | `inflar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 96 | `P3_exposure_first` | `mourn` | `deplorar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 98 | `P3_exposure_first` | `overlay` | `forrar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 99 | `P3_exposure_first` | `pheasant` | `faisán` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 101 | `P3_exposure_first` | `prussian` | `prusiano` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 102 | `P3_exposure_first` | `quarrel` | `reñir` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 104 | `P3_exposure_first` | `roast` | `asar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 105 | `P3_exposure_first` | `sigh` | `suspirar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_direct_mapping` |
| 106 | `P3_exposure_first` | `toast` | `asar` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 0.4360 | `approve_narrow_active_mapping` |
| 116 | `P3_exposure_first` | `aberration` | `equivocación` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 117 | `P3_exposure_first` | `abrogate` | `abolir` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 118 | `P3_exposure_first` | `annotation` | `anotación` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 119 | `P3_exposure_first` | `cede` | `ceder` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 120 | `P3_exposure_first` | `crevice` | `grieta` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 121 | `P3_exposure_first` | `depute` | `delegar` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 122 | `P3_exposure_first` | `housefly` | `mosca` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 123 | `P3_exposure_first` | `mitten` | `guante` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 124 | `P3_exposure_first` | `nourish` | `alimentar` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 125 | `P3_exposure_first` | `omelette` | `tortilla` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 126 | `P3_exposure_first` | `poseur` | `farsante` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_narrow_active_mapping` |
| 129 | `P3_exposure_first` | `watercourse` | `cauce` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 0.3920 | `approve_direct_mapping` |
| 130 | `P3_exposure_first` | `attitudinizer` | `farsante` | `missing` | `zipf_3_to_4_mid` | 0.3350 | `approve_narrow_active_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_tranche_010_pre_spend_en_es_latest.json \
  --run-id en-es-active-only-full-v1-tranche-010-approved \
  --max-requests 30 \
  --require-selected-request-count 30 \
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
