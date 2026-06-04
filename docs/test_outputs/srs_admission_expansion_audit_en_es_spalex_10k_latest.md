# en-es SRS Admission Expansion Audit

- Status: `ok`
- Decision: `srs_admission_expansion_audit_passed`
- Generated: `2026-05-16T18:54:35+00:00`
- Frequency DB: `/private/tmp/lexishift-spalex-audit/data-root/frequency_packs/freq-es-spalex-expanded-v1/main.sqlite`
- SRS seed rows: `10000`
- Unique lemmas: `10000`
- POS mapped: `9435` (94.3%)
- Topic rows: `1353` (13.5%)
- Non-lexical/function-heavy rows in top 100: `19` rank-order -> `0` admission-order

## Scope

This is an SRS admission integration audit. It does not mutate helper state, publish runtime SRS sets, change the veto algorithm, or generate semantic-veto helper data.

## Findings

- `PASS` `candidate_reaches_top_n`: Candidate pack reaches target size.
- `PASS` `seed_selection_reaches_top_n`: SRS seed path selected top_n rows.
- `PASS` `pos_mapped_for_frontier`: POS mapping covers the 10k frontier.
- `PASS` `topic_rows_available`: Topic rows are available for profile lift.
- `WARN` `topic_coverage_sparse`: Topic coverage is sparse; do not claim complete interest tailoring.
- `PASS` `pos_weighting_changes_frontier`: POS weighting demotes non-lexical/function-heavy rows in the top preview.
- `PASS` `profile_interest_supported:medicine`: Profile interest has enough tagged support for diagnostic reranking.
- `PASS` `profile_interest_supported:finance`: Profile interest has enough tagged support for diagnostic reranking.
- `PASS` `profile_interest_supported:sports`: Profile interest has enough tagged support for diagnostic reranking.
- `PASS` `profile_interest_supported:music`: Profile interest has enough tagged support for diagnostic reranking.

## Seed Admission

| Metric | Value |
| --- | ---: |
| top_n requested | 10000 |
| selected rows | 10000 |
| unique lemmas | 10000 |
| POS mapped share | 94.3% |
| topic row share | 13.5% |

### POS Buckets

| Bucket | Count |
| --- | ---: |
| `adjective` | 1487 |
| `adverb` | 228 |
| `noun` | 6542 |
| `other` | 638 |
| `verb` | 1105 |

### Top Topics

| Topic | Count |
| --- | ---: |
| `lifestyle` | 464 |
| `sciences` | 422 |
| `natural_sciences` | 335 |
| `hobbies` | 261 |
| `sports` | 208 |
| `physical_sciences` | 187 |
| `medicine` | 170 |
| `government` | 164 |
| `politics` | 158 |
| `mathematics` | 152 |
| `entertainment` | 136 |
| `human_sciences` | 125 |
| `engineering` | 112 |
| `games` | 109 |
| `finance` | 100 |
| `anatomy` | 97 |
| `law` | 94 |
| `business` | 91 |
| `music` | 88 |
| `biology` | 83 |

### Rank-Order Preview

| Lemma | Rank | POS | Admission | Topics |
| --- | ---: | --- | ---: | --- |
| `el` | 1.0 | `other` | 0.4 | none |
| `no` | 2.0 | `adverb` | 0.549999 | none |
| `más` | 3.0 | `adverb` | 0.549998 | mathematics, sciences |
| `ese` | 4.0 | `other` | 0.399998 | none |
| `entre` | 5.0 | `other` | 0.399997 | none |
| `hasta` | 6.0 | `other` | 0.399996 | none |
| `deber` | 7.0 | `verb` | 0.699991 | none |
| `pues` | 8.0 | `other` | 0.399994 | none |
| `sólo` | 9.0 | `adverb` | 0.549991 | none |
| `poner` | 10.0 | `verb` | 0.699987 | business, electrical_engineering, electricity, electromagnetism |
| `siglo` | 11.0 | `noun` | 0.999979 | none |
| `llamar` | 12.0 | `verb` | 0.699984 | none |
| `mayor` | 13.0 | `adjective` | 0.849979 | entertainment, government, lifestyle, military |
| `nacional` | 14.0 | `adjective` | 0.849977 | none |
| `político` | 15.0 | `adjective` | 0.849975 | none |
| `millón` | 16.0 | `noun` | 0.999969 | none |
| `preguntar` | 17.0 | `verb` | 0.699977 | none |
| `hora` | 18.0 | `noun` | 0.999965 | education |
| `trabajar` | 19.0 | `verb` | 0.699974 | none |
| `pequeño` | 20.0 | `adjective` | 0.849967 | none |

### Admission-Order Preview

| Lemma | Rank | POS | Admission | Topics |
| --- | ---: | --- | ---: | --- |
| `siglo` | 11.0 | `noun` | 0.999979 | none |
| `millón` | 16.0 | `noun` | 0.999969 | none |
| `hora` | 18.0 | `noun` | 0.999965 | education |
| `música` | 25.0 | `noun` | 0.99995 | none |
| `principio` | 27.0 | `noun` | 0.999946 | none |
| `movimiento` | 31.0 | `noun` | 0.999938 | banking, business, entertainment, finance |
| `luz` | 32.0 | `noun` | 0.999936 | anatomy, architecture, business, electrical_engineering |
| `mayoría` | 33.0 | `noun` | 0.999934 | none |
| `fondo` | 37.0 | `noun` | 0.999926 | none |
| `hermano` | 38.0 | `noun` | 0.999923 | none |
| `producción` | 40.0 | `noun` | 0.999919 | none |
| `teatro` | 41.0 | `noun` | 0.999917 | none |
| `área` | 46.0 | `noun` | 0.999907 | mathematics, sciences |
| `autor` | 47.0 | `noun` | 0.999905 | none |
| `capital` | 48.0 | `noun` | 0.999903 | business, finance |
| `estilo` | 49.0 | `noun` | 0.999901 | biology, botany, natural_sciences |
| `resto` | 50.0 | `noun` | 0.999899 | mathematics, sciences |
| `sol` | 51.0 | `noun` | 0.999897 | chemistry, natural_sciences, physical_sciences |
| `espacio` | 52.0 | `noun` | 0.999895 | media, publishing, typography |
| `necesidad` | 54.0 | `noun` | 0.99989 | none |

## Profile Scenarios

### `medicine`

- status: `eligible`
- support candidates: `170`
- support mass: `89.280909`
- exact-interest rows in top preview: `20`

| Profile Rank | Neutral Rank | Lemma | POS | Admission | Topics |
| ---: | ---: | --- | --- | ---: | --- |
| 1 | 95 | `estadio` | `noun` | 0.999579 | medicine, sciences |
| 2 | 262 | `fluido` | `noun` | 0.99895 | medicine, sciences |
| 3 | 759 | `fibrosis` | `noun` | 0.997081 | medicine, sciences |
| 4 | 1431 | `acceso` | `noun` | 0.994816 | medicine, sciences |
| 5 | 1530 | `toma` | `noun` | 0.994545 | medicine, sciences |
| 6 | 1587 | `producto` | `noun` | 0.994391 | medicine, sciences |
| 7 | 1601 | `nacido` | `noun` | 0.994352 | medicine, sciences |
| 8 | 1985 | `episodio` | `noun` | 0.9932 | medicine, sciences |
| 9 | 2173 | `rechazo` | `noun` | 0.992614 | medicine, sciences |
| 10 | 2240 | `paciente` | `noun` | 0.992428 | medicine, sciences |
| 11 | 2481 | `fomento` | `noun` | 0.991683 | medicine, sciences |
| 12 | 3982 | `sonda` | `noun` | 0.986563 | medicine, sciences |
| 13 | 6498 | `distensión` | `noun` | 0.976812 | medicine, sciences |
| 14 | 37 | `rostro` | `noun` | 0.999837 | anatomy, medicine, sciences |
| 15 | 116 | `oreja` | `noun` | 0.999492 | anatomy, medicine, sciences |
| 16 | 228 | `cadera` | `noun` | 0.999075 | anatomy, medicine, sciences |
| 17 | 289 | `lomo` | `noun` | 0.998856 | anatomy, medicine, sciences |
| 18 | 346 | `mama` | `noun` | 0.998644 | anatomy, medicine, sciences |
| 19 | 364 | `costilla` | `noun` | 0.998577 | anatomy, medicine, sciences |
| 20 | 376 | `lagarto` | `noun` | 0.998508 | anatomy, medicine, sciences |

### `finance`

- status: `eligible`
- support candidates: `100`
- support mass: `65.385078`
- exact-interest rows in top preview: `20`

| Profile Rank | Neutral Rank | Lemma | POS | Admission | Topics |
| ---: | ---: | --- | --- | ---: | --- |
| 1 | 15 | `capital` | `noun` | 0.999903 | business, finance |
| 2 | 928 | `trust` | `noun` | 0.996435 | business, finance |
| 3 | 1265 | `valor` | `noun` | 0.995263 | business, finance |
| 4 | 1299 | `interés` | `noun` | 0.995174 | business, finance |
| 5 | 1413 | `plaza` | `noun` | 0.994866 | business, commerce, entertainment, finance |
| 6 | 1809 | `bolsa` | `noun` | 0.993739 | business, finance |
| 7 | 1923 | `firma` | `noun` | 0.993387 | business, finance |
| 8 | 2012 | `letra` | `noun` | 0.993116 | banking, business, finance |
| 9 | 2014 | `obligación` | `noun` | 0.993111 | business, finance |
| 10 | 2177 | `crédito` | `noun` | 0.992602 | business, finance |
| 11 | 3318 | `prestación` | `noun` | 0.988804 | business, finance |
| 12 | 5164 | `cédula` | `noun` | 0.982218 | business, finance |
| 13 | 5709 | `vencimiento` | `noun` | 0.979978 | business, finance |
| 14 | 6025 | `solvencia` | `noun` | 0.978724 | business, finance |
| 15 | 6 | `movimiento` | `noun` | 0.999938 | banking, business, entertainment, finance |
| 16 | 413 | `boom` | `noun` | 0.998386 | business, economics, finance, sciences |
| 17 | 140 | `fusión` | `noun` | 0.999405 | economics, finance, sciences |
| 18 | 912 | `secano` | `noun` | 0.996495 | agriculture, business, finance, lifestyle |
| 19 | 1565 | `ejercicio` | `noun` | 0.994455 | economics, finance, sciences |
| 20 | 1935 | `oferta` | `noun` | 0.993358 | economics, finance, sciences |

### `sports`

- status: `eligible`
- support candidates: `208`
- support mass: `146.182194`
- exact-interest rows in top preview: `20`

| Profile Rank | Neutral Rank | Lemma | POS | Admission | Topics |
| ---: | ---: | --- | --- | ---: | --- |
| 1 | 189 | `narrador` | `noun` | 0.999217 | hobbies, lifestyle, sports |
| 2 | 282 | `remate` | `noun` | 0.998879 | hobbies, lifestyle, sports |
| 3 | 394 | `descuento` | `noun` | 0.998457 | hobbies, lifestyle, sports |
| 4 | 410 | `plantel` | `noun` | 0.998396 | hobbies, lifestyle, sports |
| 5 | 1168 | `final` | `noun` | 0.995524 | hobbies, lifestyle, sports |
| 6 | 1305 | `resultado` | `noun` | 0.995161 | hobbies, lifestyle, sports |
| 7 | 1323 | `lucha` | `noun` | 0.995109 | hobbies, lifestyle, sports |
| 8 | 1341 | `puerta` | `noun` | 0.995063 | hobbies, lifestyle, sports |
| 9 | 1417 | `disco` | `noun` | 0.994858 | athletics, hobbies, lifestyle, sports |
| 10 | 1524 | `selección` | `noun` | 0.994558 | hobbies, lifestyle, sports |
| 11 | 1738 | `global` | `noun` | 0.993953 | hobbies, lifestyle, sports |
| 12 | 1938 | `asistencia` | `noun` | 0.993349 | hobbies, lifestyle, sports |
| 13 | 2246 | `salto` | `noun` | 0.99241 | hobbies, lifestyle, sports |
| 14 | 2283 | `descanso` | `noun` | 0.9923 | hobbies, lifestyle, sports |
| 15 | 2391 | `tiro` | `noun` | 0.991976 | hobbies, lifestyle, sports |
| 16 | 2396 | `pase` | `noun` | 0.991956 | hobbies, lifestyle, sports |
| 17 | 2472 | `plantilla` | `noun` | 0.99171 | hobbies, lifestyle, sports |
| 18 | 2682 | `esquina` | `noun` | 0.991004 | hobbies, lifestyle, sports |
| 19 | 2698 | `peña` | `noun` | 0.990957 | hobbies, lifestyle, sports |
| 20 | 2815 | `portero` | `noun` | 0.990552 | hobbies, lifestyle, sports |

### `music`

- status: `eligible`
- support candidates: `88`
- support mass: `64.070162`
- exact-interest rows in top preview: `20`

| Profile Rank | Neutral Rank | Lemma | POS | Admission | Topics |
| ---: | ---: | --- | --- | ---: | --- |
| 1 | 38 | `orquesta` | `noun` | 0.999832 | entertainment, lifestyle, music |
| 2 | 166 | `ronda` | `noun` | 0.999313 | entertainment, lifestyle, music |
| 3 | 333 | `acompañamiento` | `noun` | 0.998682 | entertainment, lifestyle, music |
| 4 | 419 | `blues` | `noun` | 0.998369 | entertainment, lifestyle, music |
| 5 | 1097 | `son` | `noun` | 0.995775 | entertainment, lifestyle, music |
| 6 | 1118 | `grupo` | `noun` | 0.995678 | entertainment, lifestyle, music |
| 7 | 1143 | `bajo` | `noun` | 0.995598 | entertainment, lifestyle, music |
| 8 | 1393 | `ámbito` | `noun` | 0.994912 | entertainment, lifestyle, music |
| 9 | 1462 | `tercera` | `noun` | 0.994729 | entertainment, lifestyle, music |
| 10 | 1651 | `escala` | `noun` | 0.994207 | entertainment, lifestyle, music |
| 11 | 1717 | `clave` | `noun` | 0.994008 | entertainment, lifestyle, music |
| 12 | 1727 | `nota` | `noun` | 0.993982 | entertainment, lifestyle, music |
| 13 | 2004 | `espiritual` | `noun` | 0.99314 | entertainment, lifestyle, music |
| 14 | 2141 | `piano` | `noun` | 0.992712 | entertainment, lifestyle, music |
| 15 | 2296 | `ópera` | `noun` | 0.992264 | entertainment, lifestyle, music |
| 16 | 2558 | `prima` | `noun` | 0.991438 | entertainment, lifestyle, music |
| 17 | 2744 | `armonía` | `noun` | 0.990811 | entertainment, lifestyle, music |
| 18 | 2810 | `fantasía` | `noun` | 0.990568 | entertainment, lifestyle, music |
| 19 | 2866 | `pabellón` | `noun` | 0.990376 | entertainment, lifestyle, music |
| 20 | 2906 | `toque` | `noun` | 0.990241 | entertainment, lifestyle, music |

## Limitations

- This audit does not mutate SRS state, run helper publication, or change default packs.
- Profile scenarios prove that tagged rows can receive admission pressure; they do not prove that topic labels are complete or perfectly precise.
- Topic metadata is sparse relative to the full 10k frontier, so untagged rows remain general-frequency candidates.
- Semantic-veto evidence coverage remains a downstream concern after SRS admission readiness.
