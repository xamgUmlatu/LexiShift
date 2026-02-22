# Phase 0 POS Baseline Findings

Status: Baseline captured  
Last updated: 2026-02-22

## Scope

Pairs covered (Phase 0 target set):

- `en-ja`
- `en-es`
- `es-en`
- `en-de`

Probe script:

- `scripts/testing/pos_normalization_probe.py`

Artifact:

- `docs/test_outputs/phase0_pos_baseline/phase0_pos_probe_2026-02-22.json`

Command used:

```bash
python3 scripts/testing/pos_normalization_probe.py \
  --pairs en-ja,en-es,es-en,en-de \
  --top-n 2000 \
  --json-out docs/test_outputs/phase0_pos_baseline/phase0_pos_probe_2026-02-22.json
```

Important:
- The probe computes an inferred canonical POS for analysis-only baseline reporting.
- Runtime admission behavior currently uses `core/lexishift_core/srs/admission_policy.py`
  (`classify_pos_bucket`), not this inferred canonical mapping.

## Summary Table

| Pair | Seed count | Non-empty POS | Inferred canonical mapped rate | Runtime bucket mismatch rate | Main finding |
| --- | ---: | ---: | ---: | ---: | --- |
| `en-ja` | 1,898 | 1,898 | 92.94% | 6.22% | Mostly good coverage; numerals and suffix categories drift to noun/other behavior. |
| `en-es` | 2,000 | 2,000 | 100.00% | 98.90% | Runtime collapses almost all entries into `other` despite rich compact POS tags (`n/j/v/r/...`). |
| `es-en` | 2,000 | 2,000 | 99.50% | 97.65% | Same collapse pattern as `en-es` with COCA compact tags. |
| `en-de` | 1,981 | 319 | 97.07% | 0.00% | Runtime bucketing is consistent when POS exists, but POS is sparse (`<EMPTY>` dominates). |

## Representative POS-Driven Behavior Checks

### 1) Spanish compact tags are not interpreted by runtime admission buckets

Observed in both `en-es` and `es-en`:

- Raw tags are dominated by compact one-letter tags (`n`, `j`, `v`, `r`).
- Inferred canonical distribution is strongly lexical (noun/adjective/verb/adverb).
- Runtime bucket distribution is `other = 100%` for both pairs.

Representative examples:

- `en-es`: `no (r)`, `más (r)`, `deber (v)` expected adverb/verb buckets but runtime bucket is `other`.
- `es-en`: `do (v)`, `could (v)`, `man (n)`, `very (r)` expected verb/noun/adverb buckets but runtime bucket is `other`.

Interpretation:
- Current generic runtime classifier looks for textual substrings like `"noun"` / `"verb"`,
  so compact tags are treated as unknown.

### 2) Japanese has broad POS signal, with bounded drift

`en-ja` top raw tags include:

- `名詞-普通名詞-一般`
- `名詞-普通名詞-サ変可能`
- `動詞-一般`
- `名詞-普通名詞-副詞可能`

Runtime vs inferred mismatch examples:

- `一`, `二`, `三`, `十`, `年` (raw like `名詞-数詞` / counter-capable noun) are interpreted
  as noun in runtime buckets while inferred canonical treats them as numeral (`other` admission bucket).

Interpretation:
- Japanese POS behavior is not collapsed overall, but numeral/counter semantics are currently coarse.

### 3) German runtime bucketing is aligned where POS exists, but POS is sparse

`en-de` top raw distribution:

- `<EMPTY>`: 1,662 / 1,981 seeds
- non-empty examples: `ADV:MOD`, `ADV:TMP`, `KON:UNT`, `ZUS`, `ZAL`

Findings:

- Runtime bucket mismatch is `0.00%` for analyzed rows.
- Coverage issue is sparsity (most rows have no POS), not interpretation mismatch.
- Unmapped non-empty DE tags observed: `ZUS`, `ZAL`, `NEG`, `ZAL|ZUS`.

## Raw Tag Distribution Snapshots by Source Pack

From the same probe artifact (`top_n=2000`):

- `freq-ja-bccwj.sqlite`: rich Japanese multi-part tags.
- `freq-es-cde.sqlite`: compact tags (`n/j/v/r/...`).
- `freq-en-coca.sqlite`: compact tags (`n/j/v/r/...`) plus minor tags (`u`, `m`, `p`, ...).
- `freq-de-default.sqlite`: mostly `<EMPTY>` plus DE morphological tags.

This confirms the main Phase 0 diagnostic:
- Two sparse-behavior causes coexist:
  - interpretation mismatch (ES/EN compact tags -> runtime `other`)
  - source sparsity (`en-de` many empty POS rows)
