# en-ja SRS Topic Autotag Wikidata Exact-Label Lists

- Status: `review`
- Decision: `wikidata_exact_label_list_needs_more_roots_or_sampling`
- Generated: `2026-07-01T03:06:21+00:00`
- Eligible labels: `70336`
- Collections: `1`
- Evidence rows: `0 `
- SPARQL requests: `0`
- SPARQL cache hits: `0`

## Topics

| Topic | Rows | Lemmas | New vs current overlay |
| --- | ---: | ---: | ---: |

## Collections

| Collection | Topic | Rows | Lemmas | New vs current overlay |
| --- | --- | ---: | ---: | ---: |

## Review Sample

| Topic | Lemma | Reading | Score | Collection | Wikidata item | Root | New? |
| --- | --- | --- | ---: | --- | --- | --- | --- |

## Findings

- `WARN` `wikidata_list_evidence_empty`: No exact-label Wikidata list rows matched the selected candidate universe.
- `WARN` `wikidata_list_partial_due_to_endpoint_errors`: 1 SPARQL batch query/queries failed after retries.

## Limitations

- This is exact-label list evidence only; it is not a complete Wikidata topic inventory.
- Japanese aliases are disabled by default because aliases tend to reintroduce broad-sense noise.
- Rows generated here are mining evidence only; promotion should follow sample review and source-specific guards.
