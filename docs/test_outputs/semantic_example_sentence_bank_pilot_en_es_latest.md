# en-es Example Sentence Bank Pilot

- Status: `ok`
- Generated: `2026-04-25T01:20:27Z`
- Source: `example_sentence_bank` / `external_example_corpus`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Inventory: `semantic_family_inventory_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`

## Resources
- Data root: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift`
- `forward_pack`: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/freedict-es-en/main.sqlite` (`exists=True`, provider=`freedict`)
- `reverse_pack`: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-en-es.sqlite` (`exists=True`, provider=`wiktionary`)

## Summary
- Target families: `6`
- Negative-control families: `2`
- Target families with any example-bearing rows: `0`
- Target families with trigger-matched example-bearing rows: `0`
- Target families with reverse-side auxiliary sense text but no examples: `6`
- Target families with any reverse-side auxiliary sense text: `6`
- Example source ready on current packs: `False`

## Family Coverage
| Family | Role | Any Examples | Trigger-Matched Examples | Reverse Aux Text | Pilot Read |
| --- | --- | ---: | ---: | ---: | --- |
| `plant -> planta` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `drink -> bebida` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `check -> cheque` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `order -> pedido` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `trip -> viaje` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `report -> informe` | `target` | 0 | 0 | 1 | `no_examples_but_aux_text_available` |
| `play -> obra` | `negative_control` | 0 | 0 | 0 | `guardrail_only` |
| `watch -> reloj` | `negative_control` | 0 | 0 | 1 | `guardrail_only` |

## Sample Aux Text
- `plant -> planta`:
  - `organism capable of photosynthesis`
- `drink -> bebida`:
  - `served beverage`
- `check -> cheque`:
  - `mark used as an indicator`
- `order -> pedido`:
  - `request for some product or service`
- `trip -> viaje`:
  - `journey`
- `report -> informe`:
  - `information describing events`
- `watch -> reloj`:
  - `portable or wearable timepiece`

## Recommendation
- Current installed packs do not expose queued-family example rows for `example_sentence_bank`; if we want that control before prompt spend, we need dedicated source ingestion. The only immediately available non-LLM cue-like signal on this slice is reverse-side auxiliary sense text.
