# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T20:32:10Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 99.3% | 90.0% | 10.0% | 99.3% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 93.9% | 80.0% | 20.0% | 98.5% | 5.1% |
| no_shadows | rulegen_top3_plus_forward_gloss | 93.2% | 0.0% | 100.0% | 93.2% | 0.0% |

## Details

### curated_shadows
- Label: `Curated overlap oracle`
- Seed mode: `benchmark_reviewed`
- Policy: `gold_overlap_oracle`
- Overall accuracy: `100.0%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `0.0%`

### reviewed_auto_shadows
- Label: `Reviewed-trigger auto shadows`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Overall accuracy: `99.3%`
- Abstain recall on ambiguous rows: `90.0%`
- Harmful allow rate: `10.0%`
- Allow precision: `99.3%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-0.7%`
- Delta vs curated abstain recall: `-10.0%`
- Delta vs curated harmful allow: `10.0%`
- Delta vs curated overblocking: `0.0%`
- Sample harmful-allow rows:
  - `trabajo` / `job` gold=['cargo'] promoted=[]

### auto_shadows
- Label: `Source-only auto shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Overall accuracy: `93.9%`
- Abstain recall on ambiguous rows: `80.0%`
- Harmful allow rate: `20.0%`
- Allow precision: `98.5%`
- Overblocking rate: `5.1%`
- Delta vs curated accuracy: `-6.1%`
- Delta vs curated abstain recall: `-20.0%`
- Delta vs curated harmful allow: `20.0%`
- Delta vs curated overblocking: `5.1%`
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `trabajo` / `job` gold=['cargo'] promoted=[]
- Sample false-abstain rows:
  - `camino` / `road` promoted=['derecho']
  - `camino` / `way` promoted=['medio']
  - `camino` / `path` promoted=['derecho']
  - `campo` / `field` promoted=['área']
  - `cargo` / `position` promoted=['plaza']

### no_shadows
- Label: `No shadow veto`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `none`
- Overall accuracy: `93.2%`
- Abstain recall on ambiguous rows: `0.0%`
- Harmful allow rate: `100.0%`
- Allow precision: `93.2%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `-6.8%`
- Delta vs curated abstain recall: `-100.0%`
- Delta vs curated harmful allow: `100.0%`
- Delta vs curated overblocking: `0.0%`
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[]
  - `coger` / `take` gold=['llevar'] promoted=[]
  - `cuadro` / `table` gold=['tabla'] promoted=[]
  - `llevar` / `take` gold=['coger'] promoted=[]
  - `malla` / `net` gold=['red'] promoted=[]
