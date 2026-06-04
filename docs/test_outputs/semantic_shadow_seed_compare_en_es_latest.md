# en-es Shadow Seed Comparison

- Status: `ok`
- Generated: `2026-04-10T18:23:13Z`
- Comparison meaning: keep the miner, promotion policy, and lower-bound gold proxy fixed; swap only the seed trigger source.
- Goal: estimate how much current shadow quality depends on reviewed benchmark triggers versus rulegen-emitted sources.
- Gold targets: `63`
- Gold reviewed triggers: `148`

## Strict Policy Snapshot (`cross_checked_v1`)
| Seed Mode | Seed Triggers | Inventory Coverage | Gold Trigger Coverage | Candidate Recall | Candidate Precision | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | 148 | 100.0% | 100.0% | 90.0% | 14.1% | 26.1% |
| rulegen_top3_sources | 148 | 60.1% | 70.0% | 50.0% | 11.6% | 20.3% |
| rulegen_all_sources | 191 | 66.2% | 70.0% | 50.0% | 11.1% | 21.7% |
| rulegen_top3_plus_forward_gloss | 362 | 73.0% | 90.0% | 80.0% | 12.1% | 25.4% |
| rulegen_all_plus_forward_gloss | 364 | 73.0% | 90.0% | 80.0% | 12.1% | 25.4% |

## benchmark_reviewed
- Seed targets: `63`
- Seed triggers: `148`
- Inventory coverage: `148 / 148` (`100.0%`)
- Gold trigger coverage: `10 / 10` (`100.0%`)
- Gold rows with active support: `9 / 10` (`90.0%`)
- Candidate-pool overlap recall: `90.0%`
- `cross_checked_v1` candidate precision: `14.1%`
- `cross_checked_v1` candidate recall: `90.0%`
- `cross_checked_v1` gold hit rate: `90.0%`
- `cross_checked_v1` overblocking rate: `26.1%`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_top3_sources
- Seed targets: `63`
- Seed triggers: `148`
- Inventory coverage: `89 / 148` (`60.1%`)
- Gold trigger coverage: `7 / 10` (`70.0%`)
- Gold rows with active support: `7 / 10` (`70.0%`)
- Candidate-pool overlap recall: `50.0%`
- `cross_checked_v1` candidate precision: `11.6%`
- `cross_checked_v1` candidate recall: `50.0%`
- `cross_checked_v1` gold hit rate: `50.0%`
- `cross_checked_v1` overblocking rate: `20.3%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `sacar` / `remove` gold=['quitar'] promoted=[]
  - `tabla` / `table` gold=['cuadro'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_all_sources
- Seed targets: `63`
- Seed triggers: `191`
- Inventory coverage: `98 / 148` (`66.2%`)
- Gold trigger coverage: `7 / 10` (`70.0%`)
- Gold rows with active support: `7 / 10` (`70.0%`)
- Candidate-pool overlap recall: `50.0%`
- `cross_checked_v1` candidate precision: `11.1%`
- `cross_checked_v1` candidate recall: `50.0%`
- `cross_checked_v1` gold hit rate: `50.0%`
- `cross_checked_v1` overblocking rate: `21.7%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `sacar` / `remove` gold=['quitar'] promoted=[]
  - `tabla` / `table` gold=['cuadro'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_top3_plus_forward_gloss
- Seed targets: `63`
- Seed triggers: `362`
- Inventory coverage: `108 / 148` (`73.0%`)
- Gold trigger coverage: `9 / 10` (`90.0%`)
- Gold rows with active support: `9 / 10` (`90.0%`)
- Candidate-pool overlap recall: `80.0%`
- `cross_checked_v1` candidate precision: `12.1%`
- `cross_checked_v1` candidate recall: `80.0%`
- `cross_checked_v1` gold hit rate: `80.0%`
- `cross_checked_v1` overblocking rate: `25.4%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_all_plus_forward_gloss
- Seed targets: `63`
- Seed triggers: `364`
- Inventory coverage: `108 / 148` (`73.0%`)
- Gold trigger coverage: `9 / 10` (`90.0%`)
- Gold rows with active support: `9 / 10` (`90.0%`)
- Candidate-pool overlap recall: `80.0%`
- `cross_checked_v1` candidate precision: `12.1%`
- `cross_checked_v1` candidate recall: `80.0%`
- `cross_checked_v1` gold hit rate: `80.0%`
- `cross_checked_v1` overblocking rate: `25.4%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]
