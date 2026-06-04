# en-es Shadow Gold-Proxy Evaluation

- Status: `ok`
- Generated: `2026-04-10T22:26:14Z`
- Inventory status: `ok`
- Proxy meaning: reviewed trigger overlaps in the rulegen benchmark act as the current lower-bound gold for which targets should compete for the same English trigger.
- Blind spot: this proxy will under-credit real semantic blockers when the competing benchmark target does not explicitly list the same English trigger, so rows like `marco / frame -> cuadro` can appear as overblocking here even though they are useful runtime shadows.
- Benchmark targets: `72`
- Reviewed triggers: `175`

## Candidate Pool
- Gold trigger rows: `33`
- Gold rows with active support: `14` (`42.4%`)
- Gold rows with mined overlap: `14` (`42.4%`)
- Gold rows with exact mined set: `0` (`0.0%`)

## same_pos_lenient_v1
- Candidate precision: `4.1%`
- Candidate recall: `26.0%`
- Candidate F1: `7.1%`
- Gold trigger hit rate: `36.4%`
- Top-1 gold trigger hit rate: `27.3%`
- Gold trigger exact-match rate: `0.0%`
- Underblocking rows: `21`
- Overblocking rows: `111`
- Sample underblocked rows:
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=['canal', 'trocha', 'trillo']
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]
  - `empleo` / `employment` gold=['ocupación'] promoted=[]
  - `empleo` / `job` gold=['cargo', 'ocupación', 'trabajo'] promoted=[]
  - `empleo` / `work` gold=['trabajo'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir', 'ultimar', 'terminarse']
  - `acabar` / `end` promoted=['salir', 'parte', 'ultimar']
  - `agua` / `water` promoted=['wata', 'linfa', 'fluidos corporales']
  - `amigo` / `friend` promoted=['parcero', 'novio', 'novia']
  - `amor` / `love` promoted=['nada', 'hacer el amor', 'cero']

## support_score_v1
- Candidate precision: `14.1%`
- Candidate recall: `18.0%`
- Candidate F1: `15.8%`
- Gold trigger hit rate: `27.3%`
- Top-1 gold trigger hit rate: `27.3%`
- Gold trigger exact-match rate: `12.1%`
- Underblocking rows: `24`
- Overblocking rows: `33`
- Sample underblocked rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=['canal']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=['canal']
  - `campo` / `field` gold=['terreno'] promoted=[]
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]
  - `empleo` / `employment` gold=['ocupación'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `way` promoted=['canal']
  - `canal` / `canal` promoted=['camino']
  - `canal` / `channel` promoted=['camino']

## benchmark_backed_v1
- Candidate precision: `10.2%`
- Candidate recall: `18.0%`
- Candidate F1: `13.0%`
- Gold trigger hit rate: `27.3%`
- Top-1 gold trigger hit rate: `27.3%`
- Gold trigger exact-match rate: `12.1%`
- Underblocking rows: `24`
- Overblocking rows: `52`
- Sample underblocked rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=['canal']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=['canal']
  - `campo` / `field` gold=['terreno'] promoted=[]
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]
  - `empleo` / `employment` gold=['ocupación'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir', 'parte']
  - `camino` / `way` promoted=['canal']
  - `canal` / `canal` promoted=['camino']
  - `canal` / `channel` promoted=['camino']

## cross_checked_v1
- Candidate precision: `14.1%`
- Candidate recall: `18.0%`
- Candidate F1: `15.8%`
- Gold trigger hit rate: `27.3%`
- Top-1 gold trigger hit rate: `27.3%`
- Gold trigger exact-match rate: `12.1%`
- Underblocking rows: `24`
- Overblocking rows: `33`
- Sample underblocked rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=['canal']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=['canal']
  - `campo` / `field` gold=['terreno'] promoted=[]
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]
  - `empleo` / `employment` gold=['ocupación'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `way` promoted=['canal']
  - `canal` / `canal` promoted=['camino']
  - `canal` / `channel` promoted=['camino']

## cross_checked_backoff_missing_active_v1
- Candidate precision: `14.1%`
- Candidate recall: `18.0%`
- Candidate F1: `15.8%`
- Gold trigger hit rate: `27.3%`
- Top-1 gold trigger hit rate: `27.3%`
- Gold trigger exact-match rate: `12.1%`
- Underblocking rows: `24`
- Overblocking rows: `33`
- Sample underblocked rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=['canal']
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=['canal']
  - `campo` / `field` gold=['terreno'] promoted=[]
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]
  - `empleo` / `employment` gold=['ocupación'] promoted=[]
- Sample overblocked rows:
  - `acabar` / `finish` promoted=['salir']
  - `acabar` / `end` promoted=['salir']
  - `camino` / `way` promoted=['canal']
  - `canal` / `canal` promoted=['camino']
  - `canal` / `channel` promoted=['camino']

## none
- Candidate precision: `n/a`
- Candidate recall: `0.0%`
- Candidate F1: `n/a`
- Gold trigger hit rate: `0.0%`
- Top-1 gold trigger hit rate: `0.0%`
- Gold trigger exact-match rate: `0.0%`
- Underblocking rows: `33`
- Overblocking rows: `0`
- Sample underblocked rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[]
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[]
  - `campo` / `field` gold=['terreno'] promoted=[]
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[]
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[]

## gold_overlap_oracle
- Candidate precision: `100.0%`
- Candidate recall: `100.0%`
- Candidate F1: `100.0%`
- Gold trigger hit rate: `100.0%`
- Top-1 gold trigger hit rate: `100.0%`
- Gold trigger exact-match rate: `100.0%`
- Underblocking rows: `0`
- Overblocking rows: `0`
