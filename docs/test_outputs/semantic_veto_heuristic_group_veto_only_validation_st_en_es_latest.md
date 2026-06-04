# en-es Semantic Veto Veto-Only Validation

- Status: `review`
- Decision: `veto_only_validation_product_target_not_met`
- Generated: `2026-05-05T02:16:18Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Sources: `1`
- Rows evaluated: `1`
- Product target pass rows: `0`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `source_reports_read` | `1` |
| `input_case_rows_read` | `121` |
| `policy_rows_emitted` | `1` |
| `phrase_modes` | `shadow_or_phrase_score` |
| `shadow_lead_grid` | `0.05` |
| `shadow_score_grid` | `0.0` |

## Sources

| Source | Suite | Cases | Positives | Negatives | Original harmful | Original false abstain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | semantic_veto_heuristic_group_sentence_veto_st_en_es | 121 | 58 | 63 | 21 | 6 |

## Top Validation Rows

| Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target | Source breakdowns |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| shadow_or_phrase_score | 0.05 | 0.0 | 100.0% | 47.6% | 62.2 | fail | semantic_veto_heuristic_group_sentence_veto_st_en_es: pos 100.0%, neg 47.6% |

## Passing Rows

_No rows._

## Failure Samples For Best Row

| Source | Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:man:hombre:004 | man | abstain | shadow | negative_allow |  | 0.6427 | 0.6118 | -0.0308 | Two guards man the front gate after dark. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:man:hombre:005 | man | abstain | none | negative_allow |  | 0.5596 | 0.5216 | -0.038 | Man, that was a close call at the end. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:work:trabajo:005 | work | abstain | none | negative_allow |  | 0.602 | 0.6324 | 0.0305 | The plan will work out if everyone stays calm. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:call:llamada:005 | call | abstain | none | negative_allow |  | 0.5925 | 0.5957 | 0.0032 | They decided to call off the outdoor concert. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:yes:si:003 | yes | abstain | none | negative_allow |  | 0.487 | 0.0 | -0.487 | The button label reads yes in lowercase letters. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:money:dinero:003 | money | abstain | none | negative_allow |  | 0.6436 | 0.0 | -0.6436 | Money talks in that old proverb. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:percent:por_ciento:003 | percent | abstain | none | negative_allow |  | 0.5698 | 0.0 | -0.5698 | The percent sign appeared in every spreadsheet cell. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:often:a_menudo:003 | often | abstain | none | negative_allow |  | 0.5711 | 0.0 | -0.5711 | Little and often is his training motto. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:green:verde:005 | green | abstain | none | negative_allow |  | 0.5672 | 0.5697 | 0.0024 | The driver waited for the green light. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:trade:comercio:003 | trade | abstain | shadow | negative_allow |  | 0.6279 | 0.65 | 0.0221 | The children trade cards after school. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:trade:comercio:005 | trade | abstain | none | negative_allow |  | 0.5358 | 0.5322 | -0.0036 | The trade-off was clear after the test. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:deep:profundo:005 | deep | abstain | none | negative_allow |  | 0.6452 | 0.6015 | -0.0437 | Deep down, he knew the answer. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:particular:especifico:004 | particular | abstain | shadow | negative_allow |  | 0.5707 | 0.6053 | 0.0346 | The lawyer checked every particular of the claim. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:particular:especifico:005 | particular | abstain | none | negative_allow |  | 0.6531 | 0.6421 | -0.011 | That problem matters in particular today. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:therefore:por_lo_tanto:003 | therefore | abstain | none | negative_allow |  | 0.749 | 0.0 | -0.749 | The proof ended with the word therefore. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:senate:senado:003 | senate | abstain | none | negative_allow |  | 0.5549 | 0.0 | -0.5549 | The URL senate.gov appeared in the notes. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:participant:participante:003 | participant | abstain | none | negative_allow |  | 0.5231 | 0.0 | -0.5231 | The database field participant id was blank. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:crisis:crisis:003 | crisis | abstain | none | negative_allow |  | 0.5535 | 0.0 | -0.5535 | Crisis Core was listed as the game title. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:upgrade:actualizacion:004 | upgrade | abstain | shadow | negative_allow |  | 0.5965 | 0.6248 | 0.0283 | The city will upgrade the old bridge next year. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:upgrade:actualizacion:005 | upgrade | abstain | none | negative_allow |  | 0.5807 | 0.5826 | 0.002 | The upgrade path changed after the merger. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:hammer:martillo:003 | hammer | abstain | shadow | negative_allow |  | 0.7019 | 0.6813 | -0.0206 | Workers hammer the metal into shape. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:hammer:martillo:005 | hammer | abstain | none | negative_allow |  | 0.6128 | 0.6579 | 0.045 | She tried to hammer home the main point. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:unnecessary:innecesario:003 | unnecessary | abstain | none | negative_allow |  | 0.5605 | 0.0 | -0.5605 | The label read unnecessary in red ink. |
| semantic_veto_heuristic_group_sentence_veto_st_en_es | en-es:heuristic-group:suitable:adecuado:003 | suitable | abstain | none | negative_allow |  | 0.5293 | 0.0 | -0.5293 | The file named suitable.txt was missing. |

## Recommendation

- No veto-only blocker policy meets the configured product target on these validation reports.
- Treat the v10 pass as insufficient until stress and representative validation improve.
