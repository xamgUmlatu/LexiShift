# en-es Shadow Seed Comparison

- Status: `ok`
- Generated: `2026-04-10T04:40:58Z`
- Comparison meaning: keep the miner, promotion policy, and lower-bound gold proxy fixed; swap only the seed trigger source.
- Goal: estimate how much current shadow quality depends on reviewed benchmark triggers versus rulegen-emitted sources.
- Gold targets: `63`
- Gold reviewed triggers: `148`

## Strict Policy Snapshot (`cross_checked_v1`)
| Seed Mode | Seed Triggers | Inventory Coverage | Gold Trigger Coverage | Candidate Recall | Candidate Precision | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | 148 | 100.0% | 100.0% | 90.0% | 64.3% | 3.6% |
| rulegen_top3_sources | 148 | 60.1% | 70.0% | 40.0% | 36.4% | 5.1% |
| rulegen_all_sources | 191 | 66.2% | 70.0% | 40.0% | 33.3% | 5.8% |
| rulegen_top3_plus_forward_gloss | 362 | 73.0% | 90.0% | 80.0% | 32.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 364 | 73.0% | 90.0% | 80.0% | 32.0% | 9.4% |

## benchmark_reviewed
- Seed targets: `63`
- Seed triggers: `148`
- Inventory coverage: `148 / 148` (`100.0%`)
- Gold trigger coverage: `10 / 10` (`100.0%`)
- Gold rows with active support: `9 / 10` (`90.0%`)
- Candidate-pool overlap recall: `90.0%`
- `cross_checked_v1` candidate precision: `64.3%`
- `cross_checked_v1` candidate recall: `90.0%`
- `cross_checked_v1` gold hit rate: `90.0%`
- `cross_checked_v1` overblocking rate: `3.6%`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_top3_sources
- Seed targets: `63`
- Seed triggers: `148`
- Inventory coverage: `89 / 148` (`60.1%`)
- Gold trigger coverage: `7 / 10` (`70.0%`)
- Gold rows with active support: `7 / 10` (`70.0%`)
- Candidate-pool overlap recall: `40.0%`
- `cross_checked_v1` candidate precision: `36.4%`
- `cross_checked_v1` candidate recall: `40.0%`
- `cross_checked_v1` gold hit rate: `40.0%`
- `cross_checked_v1` overblocking rate: `5.1%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `quitar` / `remove` gold=['sacar'] promoted=[]
  - `sacar` / `remove` gold=['quitar'] promoted=[]
  - `tabla` / `table` gold=['cuadro'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]

## rulegen_all_sources
- Seed targets: `63`
- Seed triggers: `191`
- Inventory coverage: `98 / 148` (`66.2%`)
- Gold trigger coverage: `7 / 10` (`70.0%`)
- Gold rows with active support: `7 / 10` (`70.0%`)
- Candidate-pool overlap recall: `40.0%`
- `cross_checked_v1` candidate precision: `33.3%`
- `cross_checked_v1` candidate recall: `40.0%`
- `cross_checked_v1` gold hit rate: `40.0%`
- `cross_checked_v1` overblocking rate: `5.8%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `quitar` / `remove` gold=['sacar'] promoted=[]
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
- `cross_checked_v1` candidate precision: `32.0%`
- `cross_checked_v1` candidate recall: `80.0%`
- `cross_checked_v1` gold hit rate: `80.0%`
- `cross_checked_v1` overblocking rate: `9.4%`
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
- `cross_checked_v1` candidate precision: `32.0%`
- `cross_checked_v1` candidate recall: `80.0%`
- `cross_checked_v1` gold hit rate: `80.0%`
- `cross_checked_v1` overblocking rate: `9.4%`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]
