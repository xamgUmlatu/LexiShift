# en-es Semantic Veto Active-Only Full Generation Plan

- Status: `ok`
- Decision: `active_only_full_generation_plan_ready`
- Generated: `2026-06-07T19:14:33Z`
- Denominator source-target families: `17328`
- Current active-only covered families: `23` (0.1%)
- Uncovered active-only families: `17305`
- Runnable request packet families: `50`
- Runnable request packet expected items: `100`
- Runnable request packet estimated input tokens: `28754`
- Runnable request packet output-token budget: `14000`
- Source-target review: `approved:247, excluded:6, unreviewed:17052`

## What This Means

The current pack is a product-smoke control, not full en-es coverage. This report treats the SRS Zipf bridge full source-target pairs as the current installed en-es semantic-veto denominator, then prepares only the next active-only tranche for safe generation.

## Source-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 2696 | 10 | 0.4% | 2686 | `a certain` -> `cierto`, `a lot of` -> `mucho`, `a lot` -> `mucho`, `a specific` -> `cierto`, `able` -> `apto`, `able` -> `capaz` |
| `zipf_4_to_5_common` | 6444 | 8 | 0.1% | 6436 | `-elect` -> `electo`, `-er` -> `más`, `-est` -> `más`, `a handful` -> `cuanto`, `abandon` -> `abandonar`, `abandon` -> `ceder` |
| `zipf_3_to_4_mid` | 5776 | 4 | 0.1% | 5772 | `abandonment` -> `abandono`, `abbey` -> `abadía`, `abbot` -> `abad`, `abbreviation` -> `abreviatura`, `abdomen` -> `abdomen`, `abdomen` -> `vientre` |
| `zipf_below_3_rare` | 2287 | 1 | 0.0% | 2286 | `abacus` -> `ábaco`, `abattoir` -> `matadero`, `abduct` -> `secuestrar`, `abhor` -> `renegar`, `abnegation` -> `abnegación`, `abominable` -> `abominable` |
| `missing` | 125 | 0 | 0.0% | 125 | `abbeystead` -> `abadía`, `abstractedness` -> `abstracción`, `acclivity` -> `subida`, `acronymic` -> `acrónimo`, `adret` -> `solana`, `alambre` -> `alambre` |

## Target-Band Coverage

| Band | Families | Covered | Covered Share | Uncovered | Sample Uncovered |
| --- | ---: | ---: | ---: | ---: | --- |
| `zipf_5_plus_very_common` | 1558 | 9 | 0.6% | 1549 | `-er` -> `más`, `-est` -> `más`, `a certain` -> `cierto`, `a handful` -> `cuanto`, `a lot of` -> `mucho`, `a lot` -> `mucho` |
| `zipf_4_to_5_common` | 6589 | 8 | 0.1% | 6581 | `-elect` -> `electo`, `abandon` -> `abandonar`, `abandon` -> `renunciar`, `abandoned` -> `abandonado`, `abandonment` -> `abandono`, `ability` -> `facultad` |
| `zipf_3_to_4_mid` | 8612 | 6 | 0.1% | 8606 | `abandon` -> `ceder`, `abattoir` -> `matadero`, `abbey` -> `abadía`, `abbeystead` -> `abadía`, `abbot` -> `abad`, `abdomen` -> `abdomen` |
| `zipf_below_3_rare` | 569 | 0 | 0.0% | 569 | `abacus` -> `ábaco`, `abbreviation` -> `abreviatura`, `abnegation` -> `abnegación`, `absorbed` -> `absorto`, `act` -> `acontecer`, `add-on` -> `añadidura` |

## Queue Plan

Known rejected source-target rows are excluded from this queue, but future tranche rows may still require the same pre-spend review before live calls.

| Tranche | Families | Requests | Expected items | Input tokens | Output-token budget | Tier mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `en-es-active-only-full-v1-tranche-001` | 50 | 50 | 100 | 27646 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-002` | 50 | 50 | 100 | 27579 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-003` | 50 | 50 | 100 | 27811 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-004` | 50 | 50 | 100 | 27698 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-005` | 50 | 50 | 100 | 27629 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-006` | 50 | 50 | 100 | 27474 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-007` | 50 | 50 | 100 | 27674 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-008` | 50 | 50 | 100 | 27495 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-009` | 50 | 50 | 100 | 27771 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-010` | 50 | 50 | 100 | 27518 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-011` | 50 | 50 | 100 | 27830 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-012` | 50 | 50 | 100 | 27634 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-013` | 50 | 50 | 100 | 27546 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-014` | 50 | 50 | 100 | 27598 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-015` | 50 | 50 | 100 | 27487 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-016` | 50 | 50 | 100 | 27444 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-017` | 50 | 50 | 100 | 27778 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-018` | 50 | 50 | 100 | 27590 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-019` | 50 | 50 | 100 | 27872 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-020` | 50 | 50 | 100 | 27876 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-021` | 50 | 50 | 100 | 27747 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-022` | 50 | 50 | 100 | 27752 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-023` | 50 | 50 | 100 | 27710 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-024` | 50 | 50 | 100 | 27627 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-025` | 50 | 50 | 100 | 27688 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-026` | 50 | 50 | 100 | 27832 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-027` | 50 | 50 | 100 | 27587 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-028` | 50 | 50 | 100 | 27605 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-029` | 50 | 50 | 100 | 27752 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-030` | 50 | 50 | 100 | 27774 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-031` | 50 | 50 | 100 | 27722 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-032` | 50 | 50 | 100 | 27962 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-033` | 50 | 50 | 100 | 27977 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-034` | 50 | 50 | 100 | 27717 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-035` | 50 | 50 | 100 | 27645 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-036` | 50 | 50 | 100 | 27787 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-037` | 50 | 50 | 100 | 27692 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-038` | 50 | 50 | 100 | 27693 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-039` | 50 | 50 | 100 | 27779 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-040` | 50 | 50 | 100 | 27792 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-041` | 50 | 50 | 100 | 27680 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-042` | 50 | 50 | 100 | 27918 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-043` | 50 | 50 | 100 | 27784 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-044` | 50 | 50 | 100 | 27769 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-045` | 50 | 50 | 100 | 27782 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-046` | 50 | 50 | 100 | 27819 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-047` | 50 | 50 | 100 | 27832 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-048` | 50 | 50 | 100 | 27708 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-049` | 50 | 50 | 100 | 27771 | 14000 | P0_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-050` | 50 | 50 | 100 | 27977 | 14000 | P0_exposure_first:16, P1_exposure_first:34 |
| `en-es-active-only-full-v1-tranche-051` | 50 | 50 | 100 | 28101 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-052` | 50 | 50 | 100 | 27940 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-053` | 50 | 50 | 100 | 28151 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-054` | 50 | 50 | 100 | 28029 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-055` | 50 | 50 | 100 | 27835 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-056` | 50 | 50 | 100 | 27746 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-057` | 50 | 50 | 100 | 27732 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-058` | 50 | 50 | 100 | 27719 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-059` | 50 | 50 | 100 | 27840 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-060` | 50 | 50 | 100 | 27935 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-061` | 50 | 50 | 100 | 27887 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-062` | 50 | 50 | 100 | 28450 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-063` | 50 | 50 | 100 | 28417 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-064` | 50 | 50 | 100 | 28154 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-065` | 50 | 50 | 100 | 27724 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-066` | 50 | 50 | 100 | 27951 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-067` | 50 | 50 | 100 | 28210 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-068` | 50 | 50 | 100 | 28133 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-069` | 50 | 50 | 100 | 27628 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-070` | 50 | 50 | 100 | 28085 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-071` | 50 | 50 | 100 | 28111 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-072` | 50 | 50 | 100 | 28166 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-073` | 50 | 50 | 100 | 28003 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-074` | 50 | 50 | 100 | 27698 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-075` | 50 | 50 | 100 | 27770 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-076` | 50 | 50 | 100 | 27794 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-077` | 50 | 50 | 100 | 27848 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-078` | 50 | 50 | 100 | 27851 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-079` | 50 | 50 | 100 | 27802 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-080` | 50 | 50 | 100 | 28298 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-081` | 50 | 50 | 100 | 28431 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-082` | 50 | 50 | 100 | 27958 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-083` | 50 | 50 | 100 | 27822 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-084` | 50 | 50 | 100 | 27955 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-085` | 50 | 50 | 100 | 27893 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-086` | 50 | 50 | 100 | 27802 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-087` | 50 | 50 | 100 | 27868 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-088` | 50 | 50 | 100 | 27984 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-089` | 50 | 50 | 100 | 28103 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-090` | 50 | 50 | 100 | 27936 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-091` | 50 | 50 | 100 | 28023 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-092` | 50 | 50 | 100 | 27632 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-093` | 50 | 50 | 100 | 28137 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-094` | 50 | 50 | 100 | 28087 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-095` | 50 | 50 | 100 | 28130 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-096` | 50 | 50 | 100 | 27745 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-097` | 50 | 50 | 100 | 28115 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-098` | 50 | 50 | 100 | 28235 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-099` | 50 | 50 | 100 | 27627 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-100` | 50 | 50 | 100 | 27866 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-101` | 50 | 50 | 100 | 27984 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-102` | 50 | 50 | 100 | 27716 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-103` | 50 | 50 | 100 | 27734 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-104` | 50 | 50 | 100 | 27886 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-105` | 50 | 50 | 100 | 27953 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-106` | 50 | 50 | 100 | 28024 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-107` | 50 | 50 | 100 | 27877 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-108` | 50 | 50 | 100 | 27743 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-109` | 50 | 50 | 100 | 28046 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-110` | 50 | 50 | 100 | 27907 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-111` | 50 | 50 | 100 | 27792 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-112` | 50 | 50 | 100 | 27815 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-113` | 50 | 50 | 100 | 27809 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-114` | 50 | 50 | 100 | 27675 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-115` | 50 | 50 | 100 | 27791 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-116` | 50 | 50 | 100 | 27785 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-117` | 50 | 50 | 100 | 27682 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-118` | 50 | 50 | 100 | 27743 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-119` | 50 | 50 | 100 | 27728 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-120` | 50 | 50 | 100 | 27677 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-121` | 50 | 50 | 100 | 27757 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-122` | 50 | 50 | 100 | 27992 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-123` | 50 | 50 | 100 | 27818 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-124` | 50 | 50 | 100 | 27752 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-125` | 50 | 50 | 100 | 27775 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-126` | 50 | 50 | 100 | 27656 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-127` | 50 | 50 | 100 | 27799 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-128` | 50 | 50 | 100 | 27912 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-129` | 50 | 50 | 100 | 27888 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-130` | 50 | 50 | 100 | 27719 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-131` | 50 | 50 | 100 | 27739 | 14000 | P1_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-132` | 50 | 50 | 100 | 28150 | 14000 | P1_exposure_first:1, P2_exposure_first:49 |
| `en-es-active-only-full-v1-tranche-133` | 50 | 50 | 100 | 28020 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-134` | 50 | 50 | 100 | 28080 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-135` | 50 | 50 | 100 | 27927 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-136` | 50 | 50 | 100 | 27725 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-137` | 50 | 50 | 100 | 27657 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-138` | 50 | 50 | 100 | 27650 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-139` | 50 | 50 | 100 | 27702 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-140` | 50 | 50 | 100 | 27898 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-141` | 50 | 50 | 100 | 27895 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-142` | 50 | 50 | 100 | 28311 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-143` | 50 | 50 | 100 | 28185 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-144` | 50 | 50 | 100 | 27801 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-145` | 50 | 50 | 100 | 27992 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-146` | 50 | 50 | 100 | 28129 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-147` | 50 | 50 | 100 | 27634 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-148` | 50 | 50 | 100 | 27985 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-149` | 50 | 50 | 100 | 28173 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-150` | 50 | 50 | 100 | 27860 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-151` | 50 | 50 | 100 | 27714 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-152` | 50 | 50 | 100 | 27912 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-153` | 50 | 50 | 100 | 27900 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-154` | 50 | 50 | 100 | 27845 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-155` | 50 | 50 | 100 | 27728 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-156` | 50 | 50 | 100 | 28037 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-157` | 50 | 50 | 100 | 27993 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-158` | 50 | 50 | 100 | 27880 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-159` | 50 | 50 | 100 | 27797 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-160` | 50 | 50 | 100 | 27890 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-161` | 50 | 50 | 100 | 27918 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-162` | 50 | 50 | 100 | 27918 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-163` | 50 | 50 | 100 | 27860 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-164` | 50 | 50 | 100 | 27941 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-165` | 50 | 50 | 100 | 27710 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-166` | 50 | 50 | 100 | 27723 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-167` | 50 | 50 | 100 | 28115 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-168` | 50 | 50 | 100 | 27957 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-169` | 50 | 50 | 100 | 27962 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-170` | 50 | 50 | 100 | 28050 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-171` | 50 | 50 | 100 | 27996 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-172` | 50 | 50 | 100 | 27748 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-173` | 50 | 50 | 100 | 27974 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-174` | 50 | 50 | 100 | 27803 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-175` | 50 | 50 | 100 | 27740 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-176` | 50 | 50 | 100 | 27844 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-177` | 50 | 50 | 100 | 27965 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-178` | 50 | 50 | 100 | 28027 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-179` | 50 | 50 | 100 | 27813 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-180` | 50 | 50 | 100 | 27667 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-181` | 50 | 50 | 100 | 27916 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-182` | 50 | 50 | 100 | 28026 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-183` | 50 | 50 | 100 | 27800 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-184` | 50 | 50 | 100 | 27839 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-185` | 50 | 50 | 100 | 28147 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-186` | 50 | 50 | 100 | 28172 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-187` | 50 | 50 | 100 | 27818 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-188` | 50 | 50 | 100 | 27942 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-189` | 50 | 50 | 100 | 27901 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-190` | 50 | 50 | 100 | 28285 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-191` | 50 | 50 | 100 | 28108 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-192` | 50 | 50 | 100 | 28104 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-193` | 50 | 50 | 100 | 28229 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-194` | 50 | 50 | 100 | 27966 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-195` | 50 | 50 | 100 | 28126 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-196` | 50 | 50 | 100 | 27802 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-197` | 50 | 50 | 100 | 27919 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-198` | 50 | 50 | 100 | 27828 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-199` | 50 | 50 | 100 | 27987 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-200` | 50 | 50 | 100 | 28166 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-201` | 50 | 50 | 100 | 27868 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-202` | 50 | 50 | 100 | 27921 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-203` | 50 | 50 | 100 | 27921 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-204` | 50 | 50 | 100 | 28098 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-205` | 50 | 50 | 100 | 27969 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-206` | 50 | 50 | 100 | 27904 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-207` | 50 | 50 | 100 | 28136 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-208` | 50 | 50 | 100 | 27879 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-209` | 50 | 50 | 100 | 27985 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-210` | 50 | 50 | 100 | 27932 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-211` | 50 | 50 | 100 | 27822 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-212` | 50 | 50 | 100 | 27977 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-213` | 50 | 50 | 100 | 28032 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-214` | 50 | 50 | 100 | 28085 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-215` | 50 | 50 | 100 | 28124 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-216` | 50 | 50 | 100 | 27924 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-217` | 50 | 50 | 100 | 27882 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-218` | 50 | 50 | 100 | 27794 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-219` | 50 | 50 | 100 | 27788 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-220` | 50 | 50 | 100 | 27929 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-221` | 50 | 50 | 100 | 28358 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-222` | 50 | 50 | 100 | 28069 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-223` | 50 | 50 | 100 | 28191 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-224` | 50 | 50 | 100 | 28066 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-225` | 50 | 50 | 100 | 28121 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-226` | 50 | 50 | 100 | 28133 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-227` | 50 | 50 | 100 | 27915 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-228` | 50 | 50 | 100 | 27953 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-229` | 50 | 50 | 100 | 27945 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-230` | 50 | 50 | 100 | 27960 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-231` | 50 | 50 | 100 | 28077 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-232` | 50 | 50 | 100 | 28010 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-233` | 50 | 50 | 100 | 28085 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-234` | 50 | 50 | 100 | 28348 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-235` | 50 | 50 | 100 | 28443 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-236` | 50 | 50 | 100 | 27944 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-237` | 50 | 50 | 100 | 27973 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-238` | 50 | 50 | 100 | 27946 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-239` | 50 | 50 | 100 | 28239 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-240` | 50 | 50 | 100 | 28239 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-241` | 50 | 50 | 100 | 28376 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-242` | 50 | 50 | 100 | 27899 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-243` | 50 | 50 | 100 | 27939 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-244` | 50 | 50 | 100 | 28153 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-245` | 50 | 50 | 100 | 28196 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-246` | 50 | 50 | 100 | 28276 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-247` | 50 | 50 | 100 | 27917 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-248` | 50 | 50 | 100 | 27842 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-249` | 50 | 50 | 100 | 28003 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-250` | 50 | 50 | 100 | 27886 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-251` | 50 | 50 | 100 | 27876 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-252` | 50 | 50 | 100 | 27881 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-253` | 50 | 50 | 100 | 27921 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-254` | 50 | 50 | 100 | 28144 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-255` | 50 | 50 | 100 | 28385 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-256` | 50 | 50 | 100 | 28209 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-257` | 50 | 50 | 100 | 28388 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-258` | 50 | 50 | 100 | 27952 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-259` | 50 | 50 | 100 | 27841 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-260` | 50 | 50 | 100 | 27952 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-261` | 50 | 50 | 100 | 27977 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-262` | 50 | 50 | 100 | 28097 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-263` | 50 | 50 | 100 | 28057 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-264` | 50 | 50 | 100 | 27936 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-265` | 50 | 50 | 100 | 28114 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-266` | 50 | 50 | 100 | 28036 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-267` | 50 | 50 | 100 | 28054 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-268` | 50 | 50 | 100 | 28044 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-269` | 50 | 50 | 100 | 28048 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-270` | 50 | 50 | 100 | 28152 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-271` | 50 | 50 | 100 | 27935 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-272` | 50 | 50 | 100 | 28354 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-273` | 50 | 50 | 100 | 28279 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-274` | 50 | 50 | 100 | 27932 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-275` | 50 | 50 | 100 | 28079 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-276` | 50 | 50 | 100 | 28123 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-277` | 50 | 50 | 100 | 28256 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-278` | 50 | 50 | 100 | 27728 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-279` | 50 | 50 | 100 | 27961 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-280` | 50 | 50 | 100 | 28055 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-281` | 50 | 50 | 100 | 27976 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-282` | 50 | 50 | 100 | 27788 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-283` | 50 | 50 | 100 | 27927 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-284` | 50 | 50 | 100 | 27942 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-285` | 50 | 50 | 100 | 27954 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-286` | 50 | 50 | 100 | 28280 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-287` | 50 | 50 | 100 | 27973 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-288` | 50 | 50 | 100 | 27936 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-289` | 50 | 50 | 100 | 27976 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-290` | 50 | 50 | 100 | 27919 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-291` | 50 | 50 | 100 | 28275 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-292` | 50 | 50 | 100 | 27967 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-293` | 50 | 50 | 100 | 27946 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-294` | 50 | 50 | 100 | 27902 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-295` | 50 | 50 | 100 | 27930 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-296` | 50 | 50 | 100 | 28097 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-297` | 50 | 50 | 100 | 28128 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-298` | 50 | 50 | 100 | 28122 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-299` | 50 | 50 | 100 | 28042 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-300` | 50 | 50 | 100 | 27949 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-301` | 50 | 50 | 100 | 28105 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-302` | 50 | 50 | 100 | 27992 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-303` | 50 | 50 | 100 | 28196 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-304` | 50 | 50 | 100 | 28162 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-305` | 50 | 50 | 100 | 27986 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-306` | 50 | 50 | 100 | 28015 | 14000 | P2_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-307` | 50 | 50 | 100 | 28065 | 14000 | P2_exposure_first:25, P3_exposure_first:25 |
| `en-es-active-only-full-v1-tranche-308` | 50 | 50 | 100 | 28064 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-309` | 50 | 50 | 100 | 27928 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-310` | 50 | 50 | 100 | 28003 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-311` | 50 | 50 | 100 | 28026 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-312` | 50 | 50 | 100 | 28246 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-313` | 50 | 50 | 100 | 28159 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-314` | 50 | 50 | 100 | 28081 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-315` | 50 | 50 | 100 | 28058 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-316` | 50 | 50 | 100 | 27962 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-317` | 50 | 50 | 100 | 28230 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-318` | 50 | 50 | 100 | 28071 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-319` | 50 | 50 | 100 | 28270 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-320` | 50 | 50 | 100 | 28088 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-321` | 50 | 50 | 100 | 28113 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-322` | 50 | 50 | 100 | 27945 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-323` | 50 | 50 | 100 | 27970 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-324` | 50 | 50 | 100 | 28018 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-325` | 50 | 50 | 100 | 28308 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-326` | 50 | 50 | 100 | 28191 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-327` | 50 | 50 | 100 | 28047 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-328` | 50 | 50 | 100 | 28090 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-329` | 50 | 50 | 100 | 28073 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-330` | 50 | 50 | 100 | 28136 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-331` | 50 | 50 | 100 | 28125 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-332` | 50 | 50 | 100 | 28233 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-333` | 50 | 50 | 100 | 28156 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-334` | 50 | 50 | 100 | 28072 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-335` | 50 | 50 | 100 | 28024 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-336` | 50 | 50 | 100 | 28061 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-337` | 50 | 50 | 100 | 28088 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-338` | 50 | 50 | 100 | 28010 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-339` | 50 | 50 | 100 | 28249 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-340` | 50 | 50 | 100 | 28122 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-341` | 50 | 50 | 100 | 28248 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-342` | 50 | 50 | 100 | 28155 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-343` | 50 | 50 | 100 | 28153 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-344` | 50 | 50 | 100 | 28165 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-345` | 50 | 50 | 100 | 28075 | 14000 | P3_exposure_first:50 |
| `en-es-active-only-full-v1-tranche-346` | 49 | 49 | 98 | 27538 | 13720 | P3_exposure_first:49 |

## Selected Request Families

| Rank | Tier | Source | Target | Source band | Target band | Need | Review |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 72 | `P0_exposure_first` | `beginning` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 78 | `P0_exposure_first` | `between` | `entre` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 106 | `P0_exposure_first` | `century` | `siglo` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 111 | `P0_exposure_first` | `chief` | `jefe` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 190 | `P0_exposure_first` | `even` | `par` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 212 | `P0_exposure_first` | `far` | `lejos` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 303 | `P0_exposure_first` | `hour` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 322 | `P0_exposure_first` | `inside` | `dentro` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 367 | `P0_exposure_first` | `light` | `luz` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 372 | `P0_exposure_first` | `little` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 420 | `P0_exposure_first` | `more` | `más` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 425 | `P0_exposure_first` | `music` | `música` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 427 | `P0_exposure_first` | `national` | `nacional` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 430 | `P0_exposure_first` | `need` | `necesidad` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 444 | `P0_exposure_first` | `now` | `actualmente` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_narrow_active_mapping` |
| 451 | `P0_exposure_first` | `official` | `oficial` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 550 | `P0_exposure_first` | `read` | `leer` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 621 | `P0_exposure_first` | `small` | `pequeño` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 648 | `P0_exposure_first` | `space` | `espacio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_direct_mapping` |
| 655 | `P0_exposure_first` | `start` | `principio` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 711 | `P0_exposure_first` | `time` | `hora` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 786 | `P0_exposure_first` | `work` | `trabajar` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 1.0000 | `approve_polysemic_active_mapping` |
| 837 | `P0_exposure_first` | `ask` | `preguntar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 897 | `P0_exposure_first` | `break` | `romper` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 960 | `P0_exposure_first` | `close` | `estrecho` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1030 | `P0_exposure_first` | `cup` | `taza` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1065 | `P0_exposure_first` | `double` | `doble` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1104 | `P0_exposure_first` | `exactly` | `justamente` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1113 | `P0_exposure_first` | `face` | `rostro` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1281 | `P0_exposure_first` | `ice` | `hielo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1407 | `P0_exposure_first` | `maybe` | `quizás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1422 | `P0_exposure_first` | `million` | `millón` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1452 | `P0_exposure_first` | `never` | `jamás` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1465 | `P0_exposure_first` | `official` | `funcionario` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1623 | `P0_exposure_first` | `red` | `rojo` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1644 | `P0_exposure_first` | `rest` | `descansar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1672 | `P0_exposure_first` | `run` | `correr` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1728 | `P0_exposure_first` | `show` | `mostrar` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1919 | `P0_exposure_first` | `visit` | `visita` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_polysemic_active_mapping` |
| 1948 | `P0_exposure_first` | `west` | `oeste` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1953 | `P0_exposure_first` | `wife` | `esposa` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 0.9300 | `approve_direct_mapping` |
| 1975 | `P0_exposure_first` | `absence` | `falta` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 1986 | `P0_exposure_first` | `afternoon` | `tarde` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 2008 | `P0_exposure_first` | `author` | `autor` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 2025 | `P0_exposure_first` | `boss` | `jefe` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 2205 | `P0_exposure_first` | `lack` | `falta` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_polysemic_active_mapping` |
| 2212 | `P0_exposure_first` | `lay` | `poner` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_polysemic_active_mapping` |
| 2225 | `P0_exposure_first` | `majority` | `mayoría` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 2300 | `P0_exposure_first` | `politician` | `político` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |
| 2345 | `P0_exposure_first` | `republic` | `república` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 0.8860 | `approve_direct_mapping` |

## Safe First-Run Command Shape

```bash
python3 scripts/testing/semantic_veto_evidence_gap_generation_run_en_es.py \
  --request-json docs/test_outputs/semantic_veto_active_only_full_generation_plan_en_es_spalex_only_10k_latest.json \
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
