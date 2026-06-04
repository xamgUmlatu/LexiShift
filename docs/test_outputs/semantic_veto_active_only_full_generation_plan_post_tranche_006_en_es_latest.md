# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `review`
- Decision: `active_only_full_generation_plan_needs_review`
- Generated: `2026-05-13T17:40:31Z`
- Denominator source-target families: `570`
- Current active-only covered families: `300` (52.6%)
- Uncovered active-only families: `270`
- Runnable request packet families: `0`
- Runnable request packet expected items: `0`
- Runnable request packet estimated input tokens: `0`
- Runnable request packet output-token budget: `0`
- Source-target review: `excluded:49, unreviewed:221`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 109 | 95 | 87.2% | 14 | `action` -> `batalla`, `ask` -> `demandar`, `become` -> `acontecer`, `capital` -> `capital`, `chief` -> `amo`, `director` -> `director` |
| `zipf_4_to_5_common` | 235 | 175 | 74.5% | 60 | `adjacent` -> `contiguo`, `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta`, `calm` -> `silencio` |
| `zipf_3_to_4_mid` | 152 | 22 | 14.5% | 130 | `abandonment` -> `cesión`, `abiding` -> `continuo`, `abolish` -> `abolir`, `abstraction` -> `robo`, `accompaniment` -> `acompañamiento`, `accountable` -> `responsable` |
| `zipf_below_3_rare` | 52 | 8 | 15.4% | 44 | `abate` -> `decrecer`, `abatement` -> `descuento`, `aberration` -> `equivocación`, `aberration` -> `yerro`, `abrogate` -> `abolir`, `acquaint` -> `informar` |
| `missing` | 22 | 0 | 0.0% | 22 | `attitudinizer` -> `farsante`, `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `conversance` -> `notoriedad`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 84 | 66 | 78.6% | 18 | `barn` -> `puesto`, `capital` -> `capital`, `centennial` -> `siglo`, `compartment` -> `departamento`, `crisis` -> `crisis`, `depression` -> `crisis` |
| `zipf_4_to_5_common` | 219 | 147 | 67.1% | 72 | `abatement` -> `descuento`, `abiding` -> `continuo`, `abstraction` -> `robo`, `accountable` -> `responsable`, `acquaint` -> `informar`, `action` -> `batalla` |
| `zipf_3_to_4_mid` | 206 | 82 | 39.8% | 124 | `abandonment` -> `cesión`, `aberration` -> `equivocación`, `abolish` -> `abolir`, `abrogate` -> `abolir`, `accompaniment` -> `acompañamiento`, `accuse` -> `acusar` |
| `zipf_below_3_rare` | 61 | 5 | 8.2% | 56 | `abate` -> `decrecer`, `aberration` -> `yerro`, `adjacent` -> `contiguo`, `admonition` -> `exhortación`, `battlefront` -> `frontón`, `become` -> `acontecer` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 26419 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 26550 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 26494 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 26599 | 14000 | P2_exposure_first:2, P3_exposure_first:48 |
| `en-es-active-only-full-v1-tranche-005` | 21 | 21 | 42 | 11264 | 5880 | P3_exposure_first:21 |

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
