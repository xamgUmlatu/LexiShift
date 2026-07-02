# en-ja SRS Topic Autotag Wikidata Claim Probe

- Status: `ok`
- Decision: `wikidata_claim_probe_has_topic_evidence`
- Generated: `2026-06-30T22:06:37+00:00`
- Selected labels: `6`
- Evidence rows: `6 `
- Search requests: `0`
- Entity requests: `0`

## Candidate Sample

| Band | Labels |
| --- | ---: |
| `0.10-0.15` | 1 |
| `0.20-0.25` | 4 |
| `0.35-0.40` | 1 |

## Topics

| Topic | Rows | Lemmas |
| --- | ---: | ---: |
| `anime_manga_pop_culture` | 1 | 1 |
| `food_cooking` | 1 | 1 |
| `games` | 1 | 1 |
| `medicine_health` | 1 | 1 |
| `plants_nature` | 1 | 1 |
| `sports_fitness` | 1 | 1 |

## Review Sample

| Topic | Lemma | Reading | Score | Source label | Wikidata item | Description | Path |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `anime_manga_pop_culture` | `漫画` | `まんが` | 0.123432 | `comics` | `Q1004` 漫画 | 絵や文章で物語などの情報を伝える創作物 | `Q1004` |
| `food_cooking` | `寿司` | `すし` | 0.233497 | `food` | `Q46383` 寿司 | 米飯と主に魚介類を組み合わせた日本料理 | `Q46383 -> Q11559422 -> Q746549 -> Q2095` |
| `games` | `将棋` | `しょうぎ` | 0.381788 | `board game` | `Q131375` 将棋 | 2人で行うボードゲームの一つ | `Q131375 -> Q18703581 -> Q131436` |
| `medicine_health` | `癌` | `がん` | 0.224555 | `disease` | `Q12078` 悪性腫瘍 | 無目的無秩序に無限増殖し、周囲の正常組織に浸潤・転移して悪影響を及ぼす進行性腫瘍 | `Q12078 -> Q12136` |
| `plants_nature` | `桜` | `さくら` | 0.223369 | `flower` | `Q871991` サクラ | バラ目バラ科の樹木、およびその花 | `Q871991 -> Q506` |
| `sports_fitness` | `野球` | `やきゅう` | 0.240826 | `sport` | `Q5369` 野球 | チームスポーツの一つ | `Q5369 -> Q349` |

## Findings

- `PASS` `wikidata_claim_probe_completed`: Checked 6 exact labels, found 6 exact entities, mapped 6, missed roots for 0. Reading identity gate: accepted_exact_source_reading=1, accepted_unique_surface_reading=5.
- `PASS` `wikidata_claim_evidence_generated`: Generated 6 Wikidata claim evidence rows.

## Limitations

- This probe samples exact labels only; it does not measure full Wikidata coverage.
- Wikidata labels identify entities/concepts, not SRS sense suitability by themselves.
- Claim ancestry can miss useful rows when Wikidata models a term through properties outside P31/P279/P171.
- Rows generated here are mining evidence only; promotion requires source-specific guards and review.
