# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `review`
- Decision: `active_only_full_generation_plan_needs_review`
- Generated: `2026-05-13T20:18:27Z`
- Denominator source-target families: `570`
- Current active-only covered families: `446` (78.2%)
- Uncovered active-only families: `124`
- Runnable request packet families: `0`
- Runnable request packet expected items: `0`
- Runnable request packet estimated input tokens: `0`
- Runnable request packet output-token budget: `0`
- Source-target review: `excluded:103, unreviewed:21`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 196 | 83.4% | 39 | `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio`, `chase` -> `cazar` |
| `zipf_3_to_4_mid` | 152 | 125 | 82.2% | 27 | `abandonment` -> `cesión`, `abstraction` -> `robo`, `acquaintance` -> `notoriedad`, `bark` -> `barco`, `barn` -> `puesto`, `builder` -> `labrador` |
| `zipf_below_3_rare` | 52 | 29 | 55.8% | 23 | `abate` -> `decrecer`, `aberration` -> `yerro`, `admonition` -> `exhortación`, `affable` -> `gracioso`, `alternation` -> `alternativa`, `battlefront` -> `frontón` |
| `missing` | 22 | 1 | 4.5% | 21 | `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán`, `gobackwards` -> `retroceder` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 181 | 82.7% | 38 | `abstraction` -> `robo`, `action` -> `batalla`, `affable` -> `gracioso`, `alternation` -> `alternativa`, `bark` -> `barco`, `beburntdown` -> `quemar` |
| `zipf_3_to_4_mid` | 206 | 167 | 81.1% | 39 | `abandonment` -> `cesión`, `acquaintance` -> `notoriedad`, `ask` -> `demandar`, `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario` |
| `zipf_below_3_rare` | 61 | 32 | 52.5% | 29 | `abate` -> `decrecer`, `aberration` -> `yerro`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer`, `begrudge` -> `deplorar` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 21 | 21 | 42 | 11926 | 5880 | P3_exposure_first:21 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |

## No Runnable Paid Command Yet

The selected request packet is empty. Expand source-target review before running the paid generation harness.

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

- Expand the source-target review manifest for the next uncovered tranche before any paid generation.
- Rerun this planner with the updated review manifest and require a nonzero selected request count before calling the live generation harness.
- Keep the current combined pack as the product-smoke control while the next tranche is reviewed.

## Issues

- `uncovered_rows_exist_but_no_requests_selected`
