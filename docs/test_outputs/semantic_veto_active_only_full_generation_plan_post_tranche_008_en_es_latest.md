# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `review`
- Decision: `active_only_full_generation_plan_needs_review`
- Generated: `2026-05-13T18:49:13Z`
- Denominator source-target families: `570`
- Current active-only covered families: `378` (66.3%)
- Uncovered active-only families: `192`
- Runnable request packet families: `0`
- Runnable request packet expected items: `0`
- Runnable request packet estimated input tokens: `0`
- Runnable request packet output-token budget: `0`
- Source-target review: `excluded:71, unreviewed:121`

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
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 28066 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 28170 | 14000 | P2_exposure_first:2, P3_exposure_first:48 |
| `en-es-active-only-full-v1-tranche-003` | 21 | 21 | 42 | 11926 | 5880 | P3_exposure_first:21 |

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
