# en-es Semantic Veto Zipf Boundary Sweep

- Status: `ok`
- Decision: `zipf_boundary_sweep_established`
- Generated: `2026-05-06T00:44:11Z`
- Case rows: `120`
- Full source-target pairs: `570`
- Schemes swept: `240`
- Best scheme: `zipf_5p4_4p4_3p4`
- Current scheme rank: `129`

## Top Boundary Schemes

| Rank | Scheme | Thresholds | Objective | Eta2 | Pos Range | Neg Range | Underfilled | Max Family Share |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `zipf_5p4_4p4_3p4` | 5.4 / 4.4 / 3.4 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 38.8% |
| 2 | `zipf_5p4_4p4_3p6` | 5.4 / 4.4 / 3.6 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 38.8% |
| 3 | `zipf_5p4_4p4_3p8` | 5.4 / 4.4 / 3.8 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 38.8% |
| 4 | `zipf_5p4_4p4_4p0` | 5.4 / 4.4 / 4.0 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 38.8% |
| 5 | `zipf_5p4_4p4_3p2` | 5.4 / 4.4 / 3.2 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 39.1% |
| 6 | `zipf_5p4_4p4_3p0` | 5.4 / 4.4 / 3.0 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 41.4% |
| 7 | `zipf_5p4_4p4_2p8` | 5.4 / 4.4 / 2.8 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 43.7% |
| 8 | `zipf_5p4_4p4_2p6` | 5.4 / 4.4 / 2.6 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 46.1% |
| 9 | `zipf_5p4_4p4_2p4` | 5.4 / 4.4 / 2.4 | 0.1023 | 0.0156 | 0.6667 | 0.0000 | 2 | 47.9% |
| 10 | `zipf_5p4_4p6_3p8` | 5.4 / 4.6 / 3.8 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 31.9% |
| 11 | `zipf_5p4_4p6_4p0` | 5.4 / 4.6 / 4.0 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 35.8% |
| 12 | `zipf_5p4_4p6_3p6` | 5.4 / 4.6 / 3.6 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 38.8% |
| 13 | `zipf_5p4_4p6_3p4` | 5.4 / 4.6 / 3.4 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 43.7% |
| 14 | `zipf_5p4_4p6_3p2` | 5.4 / 4.6 / 3.2 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 48.9% |
| 15 | `zipf_5p4_4p6_3p0` | 5.4 / 4.6 / 3.0 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 51.2% |
| 16 | `zipf_5p4_4p6_2p8` | 5.4 / 4.6 / 2.8 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 53.5% |
| 17 | `zipf_5p4_4p6_2p6` | 5.4 / 4.6 / 2.6 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 56.0% |
| 18 | `zipf_5p4_4p6_2p4` | 5.4 / 4.6 / 2.4 | 0.0985 | 0.0135 | 0.5000 | 0.0000 | 1 | 57.7% |
| 19 | `zipf_5p0_4p4_3p8` | 5.0 / 4.4 / 3.8 | 0.0723 | 0.0190 | 0.5333 | 0.0000 | 2 | 28.4% |
| 20 | `zipf_5p0_4p4_3p6` | 5.0 / 4.4 / 3.6 | 0.0723 | 0.0190 | 0.5333 | 0.0000 | 2 | 28.9% |

## Current Scheme

- Scheme: `current_5_4_3`
- Rank: `129`
- Objective: `-0.0014`

Observed case bands:

| Band | Cases | Failure | Positive Abstain | Negative Allow |
| --- | ---: | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 68 | 38.2% | 86.7% | 0.0% |
| `zipf_4_to_5_common` | 52 | 26.9% | 60.9% | 0.0% |
| `zipf_3_to_4_mid` | 0 | n/a | n/a | n/a |
| `zipf_below_3_rare` | 0 | n/a | n/a | n/a |
| `missing` | 0 | n/a | n/a | n/a |

Full generated source-family bands:

| Band | Families | Share | Sources |
| --- | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 109 | 19.1% | 101 |
| `zipf_4_to_5_common` | 235 | 41.2% | 218 |
| `zipf_3_to_4_mid` | 152 | 26.7% | 144 |
| `zipf_below_3_rare` | 52 | 9.1% | 51 |
| `missing` | 22 | 3.9% | 22 |

## Interpretation

- A high rank means the boundary scheme separates current observed outcomes while keeping the full source-family denominator usable.
- A small gap from the best scheme means threshold tuning is probably less important than adding representative rows.
- A large gap would justify adding alternate reporting bands before relying on current 5/4/3 bands for data budgeting.

## Limitations

- `observed_rows_are_still_underpowered_for_boundary_promotion`
- `objective_is_diagnostic_not_a_proof_of_optimal_bands`
- `full_source_family_distribution_uses_current_rulegen_output_only`
- `wordfreq_zipf_is_not_cefr_or_actual_browser_token_frequency`

## Next Steps

- Use this report to decide whether future expansion should keep current bands or add alternate reporting bands.
- Rerun after representative mid and rare rows are filled.
- Treat current-band ties or small objective gaps as evidence that more rows matter more than threshold tuning.
