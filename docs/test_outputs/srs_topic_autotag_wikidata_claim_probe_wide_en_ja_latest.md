# en-ja SRS Topic Autotag Wikidata Claim Probe

- Status: `ok`
- Decision: `wikidata_claim_probe_has_topic_evidence`
- Generated: `2026-06-30T23:36:34+00:00`
- Selected labels: `250`
- Evidence rows: `3 `
- Search requests: `0`
- Entity requests: `247`

## Candidate Sample

| Band | Labels |
| --- | ---: |
| `0.00-0.05` | 2 |
| `0.05-0.10` | 6 |
| `0.10-0.15` | 11 |
| `0.15-0.20` | 18 |
| `0.20-0.25` | 27 |
| `0.25-0.30` | 6 |
| `0.30-0.35` | 8 |
| `0.35-0.40` | 12 |
| `0.40-0.45` | 17 |
| `0.45-0.50` | 19 |
| `0.50-0.55` | 13 |
| `0.55-0.60` | 14 |
| `0.60-0.65` | 10 |
| `0.65-0.70` | 11 |
| `0.70-0.75` | 14 |
| `0.75-0.80` | 13 |
| `0.80-0.85` | 16 |
| `0.85-0.90` | 15 |
| `0.90-0.95` | 13 |
| `0.95-1.00` | 5 |

## Topics

| Topic | Rows | Lemmas |
| --- | ---: | ---: |
| `law_politics_civics` | 1 | 1 |
| `medicine_health` | 2 | 2 |

## Review Sample

| Topic | Lemma | Reading | Score | Source label | Wikidata item | Description | Path |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `law_politics_civics` | `犯人` | `はんにん` | 0.250015 | `legal person role` | `Q2159907` 犯罪者 | 法律によって禁じられ刑罰が科される根拠となる事実・行為を行った人物 | `Q2159907 -> Q57735705` |
| `medicine_health` | `ショック` | `しょっく` | 0.197316 | `disease` | `Q178061` ショック | medical condition of insufficient blood flow to the tissues of the body | `Q178061 -> Q179630 -> Q12136` |
| `medicine_health` | `鼻茸` | `はなたけ` | 0.874425 | `disease` | `Q8055111`  |  | `Q8055111 -> Q10267828 -> Q12136` |

## Findings

- `PASS` `wikidata_claim_probe_completed`: Checked 250 exact labels, found 101 exact entities, skipped 25 disambiguation pages, mapped 3, missed roots for 73. Reading identity gate: accepted_exact_source_reading=39, accepted_unique_surface_reading=62.
- `WARN` `wikidata_rate_limited`: Wikidata returned HTTP 429 267 time(s); probe stopped affected branches.
- `PASS` `wikidata_claim_evidence_generated`: Generated 3 Wikidata claim evidence rows.

## Limitations

- This probe samples exact labels only; it does not measure full Wikidata coverage.
- Wikidata labels identify entities/concepts, not SRS sense suitability by themselves.
- Claim ancestry can miss useful rows when Wikidata models a term through properties outside P31/P279/P171.
- Rows generated here are mining evidence only; promotion requires source-specific guards and review.
