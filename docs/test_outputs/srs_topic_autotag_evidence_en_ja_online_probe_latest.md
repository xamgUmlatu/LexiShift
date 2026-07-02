# en-ja SRS Topic Autotag Evidence

- Status: `ok`
- Decision: `srs_topic_autotag_evidence_ready`
- Generated: `2026-06-30T15:51:00+00:00`
- Evidence rows: `0`
- Review sample rows: `0`

## Source Summary

| Source | Rows | Lemmas | Topics | Avg confidence |
| --- | ---: | ---: | ---: | ---: |

## Topic Summary

| Topic | Rows | Lemmas | Sources |
| --- | ---: | ---: | ---: |

## Review Sample

| # | Source | Topic | Lemma | Reading | Score | Band | Membership | Confidence | Evidence | Glosses |
| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |

## Findings

- `PASS` `candidate_universe_loaded`: Loaded 500 en-ja corrected difficulty candidates.
- `WARN` `wikidata_sparql_failed`: Wikidata SPARQL probe failed; trying API search fallback: HTTP Error 429: Aggressively rate-limiting to 1 req / min - this rule was created during active wdqs outage (797a132)
- `PASS` `wikidata_api_search_completed`: Queried Wikidata wbsearchentities fallback for 10 exact labels.
- `PASS` `ndl_online_completed`: Queried Web NDL Authorities for 10 bounded labels.
- `WARN` `jawikipedia_online_failed`: ja.wikipedia probe failed: HTTP Error 429: Too Many Requests
- `WARN` `topic_evidence_empty`: No topic evidence rows were generated for the selected sources.

## Limitations

- This artifact compares source strategies; it does not decide product topic membership.
- JMDict field evidence is high precision but sparse and still sense-polysemy-sensitive.
- Gloss, WordNet, Wikipedia category, and NDL keyword evidence are candidate-generation signals until reviewed.
- Wikidata/NDL/Wikipedia online adapters are intentionally bounded; full coverage should use cached/dump-based ingestion if promoted.
