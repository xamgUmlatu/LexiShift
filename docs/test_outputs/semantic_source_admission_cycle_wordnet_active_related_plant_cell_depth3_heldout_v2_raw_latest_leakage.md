# en-es LLM Example-Frame Leakage Audit

- Status: `review`
- Generated: `2026-04-25T05:28:03Z`
- Batch: `en-es:wordnet-example-frames:en-es-wordnet-cell-active-related-depth3-heldout-v2-20260425a`
- Filtered batch: `en-es:wordnet-example-frames:en-es-wordnet-cell-active-related-depth3-heldout-v2-20260425a:filtered`

## Summary

- Input rows: `86`
- Leakage hits: `0`
- Duplicate hits: `29`
- Rejected rows: `29`
- Kept rows: `57`
- Jaccard threshold: `0.75`
- Duplicate jaccard threshold: `0.92`
- Min contained tokens: `5`
- Min duplicate tokens: `4`

## Leakage Rows

| Row | Family | Evidence | Matched Case | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |

## Duplicate Rows

| Row | Family | Evidence | Matched Row | Reason | Jaccard |
| --- | --- | --- | --- | --- | ---: |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-1` | `en-es:sentence-veto:cell:celula` | (biology) the basic structural and functional unit of all organisms; they may exist as... | `en-es-sentence-veto-cell-celula:active-wordnet-definition-1` | `source_duplicate_exact_text` | 1.0 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-22` | `en-es:sentence-veto:cell:celula` | a cell that is a structural and functional unit of a plant | `en-es-sentence-veto-cell-celula:active-wordnet-definition-1` | `source_duplicate_token_sequence_contained` | 0.2069 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-23` | `en-es:sentence-veto:cell:celula` | primitive cell or group of cells from which a mother cell develops | `en-es-sentence-veto-cell-celula:active-wordnet-definition-12` | `source_duplicate_token_sequence_contained` | 0.4375 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-33` | `en-es:sentence-veto:cell:celula` | any of the cells making up the skin | `en-es-sentence-veto-cell-celula:active-wordnet-definition-11` | `source_duplicate_token_sequence_contained` | 0.2105 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-35` | `en-es:sentence-veto:cell:celula` | a cell that is part of tumor | `en-es-sentence-veto-cell-celula:active-wordnet-definition-22` | `source_duplicate_token_sequence_contained` | 0.3636 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-36` | `en-es:sentence-veto:cell:celula` | a cell that is part of a bone | `en-es-sentence-veto-cell-celula:active-wordnet-definition-35` | `source_duplicate_token_sequence_contained` | 0.7143 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-39` | `en-es:sentence-veto:cell:celula` | one of the cells of the retina that is sensitive to light | `en-es-sentence-veto-cell-celula:active-wordnet-definition-11` | `source_duplicate_token_sequence_contained` | 0.1364 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-42` | `en-es:sentence-veto:cell:celula` | a cell that is specialized to conduct nerve impulses | `en-es-sentence-veto-cell-celula:active-wordnet-definition-36` | `source_duplicate_token_sequence_contained` | 0.2727 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-43` | `en-es:sentence-veto:cell:celula` | a cell of the neuroglia | `en-es-sentence-veto-cell-celula:active-wordnet-definition-15` | `source_duplicate_token_sequence_contained` | 0.6 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-44` | `en-es:sentence-veto:cell:celula` | a hybrid cell resulting from the fusion of a lymphocyte and a tumor cell; used to cultu... | `en-es-sentence-veto-cell-celula:active-wordnet-definition-13` | `source_duplicate_token_sequence_contained` | 0.24 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-49` | `en-es:sentence-veto:cell:celula` | (genetics) an organism having two identical alleles of a particular gene and so breedin... | `en-es-sentence-veto-cell-celula:active-wordnet-definition-48` | `source_duplicate_token_sequence_contained` | 0.5 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-52` | `en-es:sentence-veto:cell:celula` | a cell from which bone develops | `en-es-sentence-veto-cell-celula:active-wordnet-definition-51` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-54` | `en-es:sentence-veto:cell:celula` | a cell from which connective tissue develops | `en-es-sentence-veto-cell-celula:active-wordnet-definition-52` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-55` | `en-es:sentence-veto:cell:celula` | a cell from which a nerve cell develops | `en-es-sentence-veto-cell-celula:active-wordnet-definition-52` | `source_duplicate_token_sequence_contained` | 0.7143 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-57` | `en-es:sentence-veto:cell:celula` | a female gametocyte that develops into an ovum after two meiotic divisions | `en-es-sentence-veto-cell-celula:active-wordnet-definition-18` | `source_duplicate_token_sequence_contained` | 0.1667 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-58` | `en-es:sentence-veto:cell:celula` | a male gametocyte that develops into four spermatids | `en-es-sentence-veto-cell-celula:active-wordnet-definition-57` | `source_duplicate_token_sequence_contained` | 0.3077 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-59` | `en-es:sentence-veto:cell:celula` | cell from which a spore develops | `en-es-sentence-veto-cell-celula:active-wordnet-definition-55` | `source_duplicate_token_sequence_contained` | 0.7143 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-60` | `en-es:sentence-veto:cell:celula` | an elongated contractile cell in striated muscle tissue | `en-es-sentence-veto-cell-celula:active-wordnet-definition-31` | `source_duplicate_token_sequence_contained` | 0.3333 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-65` | `en-es:sentence-veto:cell:celula` | short fiber that conducts toward the cell body of the neuron | `en-es-sentence-veto-cell-celula:active-wordnet-definition-64` | `source_duplicate_token_sequence_contained` | 0.5385 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-66` | `en-es:sentence-veto:cell:celula` | a nerve fiber that carries impulses toward the muscles or glands | `en-es-sentence-veto-cell-celula:active-wordnet-definition-63` | `source_duplicate_token_sequence_contained` | 0.2353 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-67` | `en-es:sentence-veto:cell:celula` | a nerve fiber that carries impulses toward the central nervous system | `en-es-sentence-veto-cell-celula:active-wordnet-definition-66` | `source_duplicate_token_sequence_contained` | 0.5 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-69` | `en-es:sentence-veto:cell:celula` | Any of the long, thin, microscopic fibrils that run through the body of a neuron and ex... | `en-es-sentence-veto-cell-celula:active-wordnet-definition-64` | `source_duplicate_token_sequence_contained` | 0.2 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-70` | `en-es:sentence-veto:cell:celula` | any of the cells making up the epidermis | `en-es-sentence-veto-cell-celula:active-wordnet-definition-33` | `source_duplicate_token_sequence_contained` | 0.75 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-71` | `en-es:sentence-veto:cell:celula` | a cell in the germinal layer of the skin (the prickle-cell layer); has many spines and... | `en-es-sentence-veto-cell-celula:active-wordnet-definition-20` | `source_duplicate_token_sequence_contained` | 0.1667 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-73` | `en-es:sentence-veto:cell:celula` | an epithelial cell that shaped like a cube | `en-es-sentence-veto-cell-celula:active-wordnet-definition-72` | `source_duplicate_token_sequence_contained` | 0.4545 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-74` | `en-es:sentence-veto:cell:celula` | an epithelial cell that secretes mucous | `en-es-sentence-veto-cell-celula:active-wordnet-definition-73` | `source_duplicate_token_sequence_contained` | 0.375 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-76` | `en-es:sentence-veto:cell:celula` | an epithelial cell that is flat like a plate and form a single layer of epithelial tissue | `en-es-sentence-veto-cell-celula:active-wordnet-definition-72` | `source_duplicate_token_sequence_contained` | 0.2778 |
| `en-es-sentence-veto-cell-celula:active-wordnet-definition-78` | `en-es:sentence-veto:cell:celula` | a cell that is part of a malignant tumor | `en-es-sentence-veto-cell-celula:active-wordnet-definition-36` | `source_duplicate_token_sequence_contained` | 0.625 |
| `en-es-sentence-veto-cell-celula:shadow-en-es-sentence-veto-cell-celda-shadow-wordnet-definition-1` | `en-es:sentence-veto:cell:celula` | a room where a prisoner is kept | `en-es-sentence-veto-cell-celula:shadow-en-es-sentence-veto-cell-celda-shadow-wordnet-definition-1` | `source_duplicate_exact_text` | 1.0 |

## Recommendation

- Use the filtered batch for downstream prototype reads, and replace the source-duplicate rows before any promotion claim.
