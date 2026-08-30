# en-ja SRS Topic Autotag NDL Authority Probe

- Status: `ok`
- Decision: `ndl_authority_probe_complete`
- Generated: `2026-07-01T00:24:57+00:00`
- Evidence rows: `4`
- Expected chunks: `1`
- Complete chunks: `1`
- Missing chunks: `0`
- Eligible labels: `7`

## Authority Schemes

| Scheme | Rows |
| --- | ---: |
| `genreformTerms` | 1 |
| `topicalTerms` | 5 |

## Topics

| Topic | Rows | Lemmas |
| --- | ---: | ---: |
| `anime_manga_pop_culture` | 1 | 1 |
| `games` | 1 | 1 |
| `medicine_health` | 1 | 1 |
| `sports_fitness` | 1 | 1 |

## Review Sample

| Topic | Lemma | Reading | Score | Source label | NDL label | Broader | Related context |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `anime_manga_pop_culture` | `漫画` | `まんが` | 0.123 | `漫画` | `漫画` | `絵画` | `諷刺画, 漫画家, キャラクター, 漫画喫茶` |
| `games` | `将棋` | `しょうぎ` | 0.382 | `ゲーム` | `将棋` | `ボードゲーム` | `英語 (将棋用)` |
| `medicine_health` | `医学` | `いがく` | 0.140 | `医学` | `医学` | `` | `医療, 医学教育, 医学研究, 漢方医学` |
| `sports_fitness` | `野球` | `やきゅう` | 0.241 | `野球` | `野球` | `` | `野球場, ワールドベースボールクラシック, セイバーメトリクス, 英語 (野球用)` |

## Findings

- `PASS` `ndl_chunk_reports_loaded`: Loaded 1 chunk report(s) from /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/srs_topic_autotag_ndl_authority_probe_chunks_en_ja.
- `PASS` `ndl_merged_evidence_present`: Merged 4 evidence rows.
