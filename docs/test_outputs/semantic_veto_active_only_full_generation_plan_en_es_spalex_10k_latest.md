# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-05-16T18:43:47Z`
- Denominator source-target families: `4260`
- Current active-only covered families: `49` (1.1%)
- Uncovered active-only families: `4211`
- Runnable request packet families: `50`
- Runnable request packet expected items: `100`
- Runnable request packet estimated input tokens: `28929`
- Runnable request packet output-token budget: `14000`
- Source-target review: `approved:406, excluded:115, unreviewed:3690`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 897 | 16 | 1.8% | 881 | `able` -> `capaz`, `above` -> `arriba`, `access` -> `agresión`, `access` -> `ataque`, `access` -> `entrada`, `access` -> `instinto` |
| `zipf_4_to_5_common` | 1784 | 11 | 0.6% | 1773 | `ability` -> `capacidad`, `ability` -> `disposición`, `ability` -> `habilidad`, `ability` -> `poder`, `abroad` -> `fuera`, `absence` -> `ausencia` |
| `zipf_3_to_4_mid` | 1072 | 14 | 1.3% | 1058 | `abandonment` -> `cesión`, `abbey` -> `abadía`, `abbot` -> `abad`, `abbreviation` -> `abreviatura`, `abdomen` -> `vientre`, `abide` -> `aguardar` |
| `zipf_below_3_rare` | 326 | 8 | 2.5% | 318 | `abate` -> `decrecer`, `abate` -> `disminuir`, `abatement` -> `baja`, `abatement` -> `descuento`, `abatement` -> `reducción`, `aberration` -> `desvío` |
| `missing` | 181 | 0 | 0.0% | 181 | `aberrance` -> `desvío`, `abreact` -> `descargar`, `accidence` -> `acaso`, `acclivity` -> `cuesta`, `accusal` -> `acusación`, `accusal` -> `cargo` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 692 | 10 | 1.5% | 682 | `abatement` -> `baja`, `abide` -> `esperar`, `ability` -> `capacidad`, `ability` -> `poder`, `above` -> `arriba`, `abroad` -> `fuera` |
| `zipf_4_to_5_common` | 2065 | 18 | 0.9% | 2047 | `abate` -> `disminuir`, `abatement` -> `descuento`, `abatement` -> `reducción`, `aberration` -> `error`, `abet` -> `sostener`, `abhorrence` -> `horror` |
| `zipf_3_to_4_mid` | 1407 | 18 | 1.3% | 1389 | `abandonment` -> `cesión`, `abbey` -> `abadía`, `abbot` -> `abad`, `abdomen` -> `vientre`, `aberrance` -> `desvío`, `aberration` -> `desvío` |
| `zipf_below_3_rare` | 96 | 3 | 3.1% | 93 | `abate` -> `decrecer`, `abbreviation` -> `abreviatura`, `aberration` -> `yerro`, `abide` -> `aguardar`, `adjacent` -> `contiguo`, `admonition` -> `exhortación` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27700 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 27742 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 27624 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 27724 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 27667 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 27766 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 27536 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-008` | 50 | 50 | 100 | 27715 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-009` | 50 | 50 | 100 | 27910 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-010` | 50 | 50 | 100 | 27841 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-011` | 50 | 50 | 100 | 27735 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-012` | 50 | 50 | 100 | 27856 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-013` | 50 | 50 | 100 | 27925 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-014` | 50 | 50 | 100 | 27808 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-015` | 50 | 50 | 100 | 27846 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-016` | 50 | 50 | 100 | 27903 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-017` | 50 | 50 | 100 | 27826 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-018` | 50 | 50 | 100 | 27934 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-019` | 50 | 50 | 100 | 27821 | 14000 | P0_exposure_first:46, P1_exposure_first:4 |
| `en-es-active-only-full-v1-tranche-020` | 50 | 50 | 100 | 28158 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-021` | 50 | 50 | 100 | 28055 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-022` | 50 | 50 | 100 | 27828 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-023` | 50 | 50 | 100 | 27840 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-024` | 50 | 50 | 100 | 27911 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-025` | 50 | 50 | 100 | 28385 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-026` | 50 | 50 | 100 | 27947 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-027` | 50 | 50 | 100 | 28025 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-028` | 50 | 50 | 100 | 28044 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-029` | 50 | 50 | 100 | 27777 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-030` | 50 | 50 | 100 | 27781 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-031` | 50 | 50 | 100 | 28117 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-032` | 50 | 50 | 100 | 27884 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-033` | 50 | 50 | 100 | 27875 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-034` | 50 | 50 | 100 | 28028 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-035` | 50 | 50 | 100 | 28114 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-036` | 50 | 50 | 100 | 28062 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-037` | 50 | 50 | 100 | 27795 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-038` | 50 | 50 | 100 | 27784 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-039` | 50 | 50 | 100 | 27915 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-040` | 50 | 50 | 100 | 27806 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-041` | 50 | 50 | 100 | 28119 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-042` | 50 | 50 | 100 | 27986 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-043` | 50 | 50 | 100 | 28076 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-044` | 50 | 50 | 100 | 28106 | 14000 | P1_exposure_first:26, P2_exposure_first:24 |
| `en-es-active-only-full-v1-tranche-045` | 50 | 50 | 100 | 27958 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-046` | 50 | 50 | 100 | 28101 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-047` | 50 | 50 | 100 | 27979 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-048` | 50 | 50 | 100 | 27890 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-049` | 50 | 50 | 100 | 27870 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-050` | 50 | 50 | 100 | 27881 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-051` | 50 | 50 | 100 | 28017 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-052` | 50 | 50 | 100 | 27955 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-053` | 50 | 50 | 100 | 27784 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-054` | 50 | 50 | 100 | 28229 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-055` | 50 | 50 | 100 | 27890 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-056` | 50 | 50 | 100 | 28202 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-057` | 50 | 50 | 100 | 28020 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-058` | 50 | 50 | 100 | 27964 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-059` | 50 | 50 | 100 | 28013 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-060` | 50 | 50 | 100 | 28002 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-061` | 50 | 50 | 100 | 28284 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-062` | 50 | 50 | 100 | 28230 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-063` | 50 | 50 | 100 | 28030 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-064` | 50 | 50 | 100 | 28090 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-065` | 50 | 50 | 100 | 28177 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-066` | 50 | 50 | 100 | 28130 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-067` | 50 | 50 | 100 | 27884 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-068` | 50 | 50 | 100 | 28012 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-069` | 50 | 50 | 100 | 28119 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-070` | 50 | 50 | 100 | 28157 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-071` | 50 | 50 | 100 | 27993 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-072` | 50 | 50 | 100 | 28040 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-073` | 50 | 50 | 100 | 28069 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-074` | 50 | 50 | 100 | 28185 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-075` | 50 | 50 | 100 | 28115 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-076` | 50 | 50 | 100 | 28427 | 14000 | P2_exposure_first:18, P3_exposure_first:32 |
| `en-es-active-only-full-v1-tranche-077` | 50 | 50 | 100 | 28382 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-078` | 50 | 50 | 100 | 28321 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-079` | 50 | 50 | 100 | 28075 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-080` | 50 | 50 | 100 | 28233 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-081` | 50 | 50 | 100 | 28357 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-082` | 46 | 46 | 92 | 26345 | 12880 | P3_exposure_first:46 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 31 | `P0_exposure_first` | `away` | `lejos` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 36 | `P0_exposure_first` | `beginning` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 41 | `P0_exposure_first` | `between` | `entre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 54 | `P0_exposure_first` | `century` | `siglo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 58 | `P0_exposure_first` | `chief` | `jefe` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 90 | `P0_exposure_first` | `even` | `par` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 98 | `P0_exposure_first` | `far` | `lejos` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 131 | `P0_exposure_first` | `hour` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 138 | `P0_exposure_first` | `inside` | `dentro` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 146 | `P0_exposure_first` | `just` | `sólo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 161 | `P0_exposure_first` | `light` | `luz` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 164 | `P0_exposure_first` | `little` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 173 | `P0_exposure_first` | `making` | `producción` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 185 | `P0_exposure_first` | `more` | `más` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 186 | `P0_exposure_first` | `morning` | `mañana` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 190 | `P0_exposure_first` | `music` | `música` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 192 | `P0_exposure_first` | `national` | `nacional` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 195 | `P0_exposure_first` | `need` | `necesidad` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 206 | `P0_exposure_first` | `now` | `actualmente` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 211 | `P0_exposure_first` | `official` | `oficial` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 218 | `P0_exposure_first` | `only` | `sólo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 262 | `P0_exposure_first` | `read` | `leer` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 269 | `P0_exposure_first` | `room` | `espacio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 275 | `P0_exposure_first` | `section` | `departamento` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 287 | `P0_exposure_first` | `small` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 298 | `P0_exposure_first` | `space` | `espacio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 301 | `P0_exposure_first` | `stand` | `puesto` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 304 | `P0_exposure_first` | `start` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 323 | `P0_exposure_first` | `time` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 355 | `P0_exposure_first` | `work` | `trabajar` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 365 | `P0_exposure_first` | `access` | `entrada` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 379 | `P0_exposure_first` | `ask` | `preguntar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 407 | `P0_exposure_first` | `break` | `romper` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 415 | `P0_exposure_first` | `car` | `automóvil` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 442 | `P0_exposure_first` | `close` | `estrecho` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 461 | `P0_exposure_first` | `court` | `patio` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 466 | `P0_exposure_first` | `cup` | `taza` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 480 | `P0_exposure_first` | `double` | `doble` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 482 | `P0_exposure_first` | `eight` | `ocho` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 493 | `P0_exposure_first` | `exactly` | `justamente` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 495 | `P0_exposure_first` | `face` | `rostro` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 549 | `P0_exposure_first` | `ice` | `hielo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 573 | `P0_exposure_first` | `light` | `débil` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 592 | `P0_exposure_first` | `maybe` | `quizás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 595 | `P0_exposure_first` | `million` | `millón` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 600 | `P0_exposure_first` | `never` | `jamás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 601 | `P0_exposure_first` | `nice` | `rico` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 608 | `P0_exposure_first` | `officer` | `funcionario` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |
| 609 | `P0_exposure_first` | `official` | `funcionario` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 612 | `P0_exposure_first` | `old` | `anciano` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_narrow_active_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_10k_latest.json \
  --run-id en-es-active-only-full-v1-tranche-001-approved \
  --max-requests 50 \
  --require-selected-request-count 50 \
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
