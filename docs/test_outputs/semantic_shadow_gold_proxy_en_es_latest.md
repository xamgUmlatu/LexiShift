# en-es Shadow Gold-Proxy Evaluation

- Status: `ok`
- Generated: `2026-04-10T18:23:28Z`
- Inventory status: `ok`
- Proxy meaning: reviewed trigger overlaps in the rulegen benchmark act as the current lower-bound gold for which targets should compete for the same English trigger.
- Blind spot: this proxy will under-credit real semantic blockers when the competing benchmark target does not explicitly list the same English trigger, so rows like `marco / frame -> cuadro` can appear as overblocking here even though they are useful runtime shadows.
- Benchmark targets: `63`
- Reviewed triggers: `148`

## Candidate Pool
- Gold trigger rows: `10`
- Gold rows with active support: `9` (`90.0%`)
- Gold rows with mined overlap: `9` (`90.0%`)
- Gold rows with exact mined set: `0` (`0.0%`)

## same_pos_lenient_v1
- Candidate precision: `2.8%`
- Candidate recall: `90.0%`
- Candidate F1: `5.5%`
- Gold trigger hit rate: `90.0%`
- Top-1 gold trigger hit rate: `90.0%`
- Gold trigger exact-match rate: `0.0%`
- Underblocking rows: `1`
- Overblocking rows: `116`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=['yob', 'tarea', 'talacha']
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir', 'ultimar', 'terminarse']
  - `acabar` / `end` promoted=['salir', 'parte', 'ultimar']
  - `agua` / `water` promoted=['wata', 'linfa', 'fluidos corporales']
  - `amigo` / `friend` promoted=['parcero', 'novio', 'novia']
  - `amor` / `love` promoted=['nada', 'hacer el amor', 'cero']

## support_score_v1
- Candidate precision: `14.1%`
- Candidate recall: `90.0%`
- Candidate F1: `24.3%`
- Gold trigger hit rate: `90.0%`
- Top-1 gold trigger hit rate: `90.0%`
- Gold trigger exact-match rate: `50.0%`
- Underblocking rows: `1`
- Overblocking rows: `36`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `road` promoted=['canal']
  - `camino` / `way` promoted=['canal']
  - `camino` / `path` promoted=['canal']

## benchmark_backed_v1
- Candidate precision: `10.2%`
- Candidate recall: `90.0%`
- Candidate F1: `18.4%`
- Gold trigger hit rate: `90.0%`
- Top-1 gold trigger hit rate: `90.0%`
- Gold trigger exact-match rate: `40.0%`
- Underblocking rows: `1`
- Overblocking rows: `55`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir', 'parte']
  - `camino` / `road` promoted=['canal']
  - `camino` / `way` promoted=['canal']
  - `camino` / `path` promoted=['canal']

## cross_checked_v1
- Candidate precision: `14.1%`
- Candidate recall: `90.0%`
- Candidate F1: `24.3%`
- Gold trigger hit rate: `90.0%`
- Top-1 gold trigger hit rate: `90.0%`
- Gold trigger exact-match rate: `50.0%`
- Underblocking rows: `1`
- Overblocking rows: `36`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `road` promoted=['canal']
  - `camino` / `way` promoted=['canal']
  - `camino` / `path` promoted=['canal']

## cross_checked_backoff_missing_active_v1
- Candidate precision: `14.1%`
- Candidate recall: `90.0%`
- Candidate F1: `24.3%`
- Gold trigger hit rate: `90.0%`
- Top-1 gold trigger hit rate: `90.0%`
- Gold trigger exact-match rate: `50.0%`
- Underblocking rows: `1`
- Overblocking rows: `36`
- Sample underblocked rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `road` promoted=['canal']
  - `camino` / `way` promoted=['canal']
  - `camino` / `path` promoted=['canal']

## none
- Candidate precision: `n/a`
- Candidate recall: `0.0%`
- Candidate F1: `n/a`
- Gold trigger hit rate: `0.0%`
- Top-1 gold trigger hit rate: `0.0%`
- Gold trigger exact-match rate: `0.0%`
- Underblocking rows: `10`
- Overblocking rows: `0`
- Sample underblocked rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `coger` / `take` gold=['llevar'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `llevar` / `take` gold=['coger'] promoted=[]
  - `malla` / `net` gold=['red'] promoted=[]

## gold_overlap_oracle
- Candidate precision: `100.0%`
- Candidate recall: `100.0%`
- Candidate F1: `100.0%`
- Gold trigger hit rate: `100.0%`
- Top-1 gold trigger hit rate: `100.0%`
- Gold trigger exact-match rate: `100.0%`
- Underblocking rows: `0`
- Overblocking rows: `0`
