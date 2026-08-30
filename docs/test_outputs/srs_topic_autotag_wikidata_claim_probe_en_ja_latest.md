# en-ja SRS Topic Autotag Wikidata Claim Probe

- Status: `ok`
- Decision: `wikidata_claim_probe_has_topic_evidence`
- Generated: `2026-06-30T23:31:28+00:00`
- Selected labels: `80`
- Evidence rows: `8 `
- Search requests: `0`
- Entity requests: `0`

## Candidate Sample

| Band | Labels |
| --- | ---: |
| `0.05-0.10` | 2 |
| `0.10-0.15` | 4 |
| `0.15-0.20` | 5 |
| `0.20-0.25` | 9 |
| `0.25-0.30` | 2 |
| `0.30-0.35` | 3 |
| `0.35-0.40` | 4 |
| `0.40-0.45` | 5 |
| `0.45-0.50` | 6 |
| `0.50-0.55` | 4 |
| `0.55-0.60` | 5 |
| `0.60-0.65` | 3 |
| `0.65-0.70` | 3 |
| `0.70-0.75` | 5 |
| `0.75-0.80` | 4 |
| `0.80-0.85` | 5 |
| `0.85-0.90` | 5 |
| `0.90-0.95` | 4 |
| `0.95-1.00` | 2 |

## Topics

| Topic | Rows | Lemmas |
| --- | ---: | ---: |
| `anime_manga_pop_culture` | 1 | 1 |
| `arts_literature_humanities` | 2 | 2 |
| `food_cooking` | 1 | 1 |
| `law_politics_civics` | 1 | 1 |
| `plants_nature` | 2 | 2 |
| `science_technology` | 1 | 1 |

## Review Sample

| Topic | Lemma | Reading | Score | Source label | Wikidata item | Description | Path |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `anime_manga_pop_culture` | `アフタヌーン` | `あふたぬーん` | 0.448058 | `manga` | `Q290043` 月刊アフタヌーン | 日本の漫画月刊誌 | `Q290043 -> Q15296520 -> Q8274` |
| `arts_literature_humanities` | `詩` | `し` | 0.102076 | `literary work` | `Q482` 詩 | 文学の一形式 | `Q482 -> Q7725634` |
| `arts_literature_humanities` | `スケッチ` | `すけっち` | 0.23286 | `drawing` | `Q5078274` スケッチ | 人物や風景などを大まかに描写すること | `Q5078274 -> Q93184` |
| `food_cooking` | `練り切り` | `ねりきり` | 0.893391 | `confection` | `Q11608010` 練り切り | 和菓子の一種 | `Q11608010 -> Q1063096 -> Q5159627` |
| `law_politics_civics` | `犯人` | `はんにん` | 0.250015 | `legal person role` | `Q2159907` 犯罪者 | 法律によって禁じられ刑罰が科される根拠となる事実・行為を行った人物 | `Q2159907 -> Q57735705` |
| `plants_nature` | `台風` | `たいふう` | 0.148941 | `tropical cyclone` | `Q140588` 台風 | 北西太平洋および南シナ海で発生する強い熱帯低気圧 | `Q140588 -> Q63100732 -> Q8092` |
| `plants_nature` | `くり` | `くり` | 0.482379 | `plant` | `Q717827` クリ | ブナ科クリ属の植物の総称 | `Q717827 -> Q129324 -> Q10884 -> Q757163 -> Q756` |
| `science_technology` | `エミュレート` | `えみゅれーと` | 0.943575 | `software` | `Q202871` エミュレータ | software that enables one computer system (called the host) to behave like another computer system (called the guest) | `Q202871 -> Q114981191 -> Q7397` |

## Findings

- `PASS` `wikidata_claim_probe_completed`: Checked 80 exact labels, found 32 exact entities, skipped 9 disambiguation pages, mapped 8, missed roots for 15. Reading identity gate: accepted_exact_source_reading=15, accepted_unique_surface_reading=17.
- `PASS` `wikidata_claim_evidence_generated`: Generated 8 Wikidata claim evidence rows.

## Limitations

- This probe samples exact labels only; it does not measure full Wikidata coverage.
- Wikidata labels identify entities/concepts, not SRS sense suitability by themselves.
- Claim ancestry can miss useful rows when Wikidata models a term through properties outside P31/P279/P171.
- Rows generated here are mining evidence only; promotion requires source-specific guards and review.
