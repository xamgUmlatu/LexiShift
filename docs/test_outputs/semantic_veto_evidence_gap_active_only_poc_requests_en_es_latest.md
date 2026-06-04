# en-es Semantic Veto Active-Only PoC Requests

- Status: `ok`
- Decision: `active_only_poc_generation_batch_frozen`
- Generated: `2026-05-08T20:34:43Z`
- Prompt id: `semantic_veto_evidence_gap_generation_v5`
- Source request packet: `docs/test_outputs/semantic_veto_evidence_gap_generation_requests_en_es_latest.json`
- Requests frozen: `24`
- Families: `24`
- Expected generated items: `48`
- Expected output-token budget: `6720`

## Arm Summary

| Arm | Requests | Families | Expected items |
| --- | ---: | ---: | ---: |
| `high_need` | 8 | 8 | 16 |
| `low_control` | 8 | 8 | 16 |
| `middle_control` | 8 | 8 | 16 |

## Checks

- Source request count: `72`
- Selected slot type: `active_evidence_expansion`
- Selected request count: `24`
- Issue count: `0`

## Request Sample

| Arm | Family | Trigger | Target | Items |
| --- | --- | --- | --- | ---: |
| `high_need` | `en-es:full-family-repaired-full:adjoining:vecino` | `adjoining` | `vecino` | 2 |
| `high_need` | `en-es:full-family-repaired-full:entirely:enteramente` | `entirely` | `enteramente` | 2 |
| `high_need` | `en-es:full-family-repaired-full:bouillon:caldo` | `bouillon` | `caldo` | 2 |
| `high_need` | `en-es:full-family-repaired-full:december:diciembre` | `december` | `diciembre` | 2 |
| `high_need` | `en-es:full-family-repaired-full:american:americano` | `american` | `americano` | 2 |
| `high_need` | `en-es:full-family-repaired-full:among:entre` | `among` | `entre` | 2 |
| `high_need` | `en-es:full-family-repaired-full:begin:comenzar` | `begin` | `comenzar` | 2 |
| `high_need` | `en-es:full-family-repaired-full:dentist:dentista` | `dentist` | `dentista` | 2 |
| `middle_control` | `en-es:full-family-repaired-full:brother:hermano` | `brother` | `hermano` | 2 |
| `middle_control` | `en-es:full-family-repaired-full:german:alem-n` | `german` | `alemán` | 2 |
| `middle_control` | `en-es:full-family-repaired-full:heart:coraz-n` | `heart` | `corazón` | 2 |
| `middle_control` | `en-es:full-family-repaired-full:rumanian:rumano` | `rumanian` | `rumano` | 2 |

## Next Steps

- Run the frozen active-only request packet once with explicit live spend guards.
- Admit generated responses structurally before scoring.
- Run contribution and score-contribution reports against frozen repaired-full cases.
- Use the result as the PoC follow-through reading; do not keep cycling thresholds unless a new product goal is set.

## Limitations

- `active evidence only`
- `not a full semantic-veto source coverage plan`
- `does not generate shadow or no-winner rows`
- `does not change runtime policy`
- `intended as one follow-through PoC batch, not a new iterative optimization loop`
