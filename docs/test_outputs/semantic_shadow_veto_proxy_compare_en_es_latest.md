# en-es Shadow Veto Proxy Comparison

- Status: `ok`
- Generated: `2026-04-10T21:42:38Z`
- Comparison meaning: use the reviewed trigger-overlap gold as a lower-bound veto proxy.
- Decision rule: if a shadow source emits any blockers for an ambiguous trigger row, count that row as `abstain`; otherwise count it as `allow`.
- Limitation: this is not the sentence-level cosine veto benchmark. It measures whether a shadow source carries enough blocker structure to support abstention on the reviewed ambiguity families.

## Summary
| Shadow Source | Seed Mode | Accuracy | Abstain Recall | Harmful Allow | Allow Precision | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| curated_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| reviewed_auto_shadows | benchmark_reviewed | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% |
| auto_shadows | rulegen_top3_plus_forward_gloss | 93.9% | 80.0% | 20.0% | 98.5% | 5.1% |
| borrowed_trigger_auto_shadows | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 93.2% | 100.0% | 0.0% | 100.0% | 7.2% |
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
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:tier:smoke | 78 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 70 | 100.0% | 100.0% | 0.0% | 0.0% |

### reviewed_auto_shadows
- Label: `Reviewed-trigger auto shadows`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Overall accuracy: `100.0%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `0.0%`
- Delta vs curated accuracy: `0.0%`
- Delta vs curated abstain recall: `0.0%`
- Delta vs curated harmful allow: `0.0%`
- Delta vs curated overblocking: `0.0%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:tier:smoke | 78 | 100.0% | 100.0% | 0.0% | 0.0% |
| dimension:tier:hard | 70 | 100.0% | 100.0% | 0.0% | 0.0% |

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
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:tier:smoke | 78 | 94.9% | 80.0% | 20.0% | 4.1% |
| dimension:tier:hard | 70 | 92.9% | 80.0% | 20.0% | 6.2% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard']
  - `trabajo` / `job` gold=['cargo'] promoted=[] cases=['en-es:trabajo'] tiers=['smoke']
- Sample false-abstain rows:
  - `camino` / `road` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke']
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke']
  - `camino` / `path` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke']
  - `campo` / `field` promoted=['área'] cases=['en-es:campo'] tiers=['hard']
  - `cargo` / `position` promoted=['plaza'] cases=['en-es:cargo'] tiers=['hard']

### borrowed_trigger_auto_shadows
- Label: `Source-only borrowed-trigger shadows`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Overall accuracy: `93.2%`
- Abstain recall on ambiguous rows: `100.0%`
- Harmful allow rate: `0.0%`
- Allow precision: `100.0%`
- Overblocking rate: `7.2%`
- Delta vs curated accuracy: `-6.8%`
- Delta vs curated abstain recall: `0.0%`
- Delta vs curated harmful allow: `0.0%`
- Delta vs curated overblocking: `7.2%`
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:tier:smoke | 78 | 93.6% | 100.0% | 0.0% | 6.8% |
| dimension:tier:hard | 70 | 92.9% | 100.0% | 0.0% | 7.7% |
- Sample false-abstain rows:
  - `banco` / `bank` promoted=['escuela'] cases=['en-es:banco'] tiers=['smoke']
  - `camino` / `road` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke']
  - `camino` / `way` promoted=['medio'] cases=['en-es:camino'] tiers=['smoke']
  - `camino` / `path` promoted=['derecho'] cases=['en-es:camino'] tiers=['smoke']
  - `campo` / `field` promoted=['área'] cases=['en-es:campo'] tiers=['hard']

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
- Slice summaries:

| Slice | Rows | Accuracy | Abstain Recall | Harmful Allow | Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: |
| dimension:tier:smoke | 78 | 93.6% | 0.0% | 100.0% | 0.0% |
| dimension:tier:hard | 70 | 92.9% | 0.0% | 100.0% | 0.0% |
- Sample harmful-allow rows:
  - `cargo` / `job` gold=['trabajo'] promoted=[] cases=['en-es:cargo'] tiers=['hard']
  - `coger` / `take` gold=['llevar'] promoted=[] cases=['en-es:coger'] tiers=['hard']
  - `cuadro` / `table` gold=['tabla'] promoted=[] cases=['en-es:cuadro'] tiers=['hard']
  - `llevar` / `take` gold=['coger'] promoted=[] cases=['en-es:llevar'] tiers=['smoke']
  - `malla` / `net` gold=['red'] promoted=[] cases=['en-es:malla'] tiers=['hard']
