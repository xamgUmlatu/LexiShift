# en-es Browsing-Based SRS Admission Research

- Status: `ok`
- Decision: `srs_browsing_admission_research_ready`
- Documents: `2`
- Source lookup hits: `18`
- Target lookup hits: `0`
- Unmapped tokens: `12`
- Boosted lemmas: `32`
- Ambiguous boosted lemmas: `24`

## Policy

- `browsing_signal_cap`: `16.0`
- `browsing_alpha`: `0.25`
- `max_browsing_boost`: `1.35`
- `replacement_exposure_weight`: `0.35`
- `ambiguity_confidence_exponent`: `0.5`
- `max_unique_tokens_per_document`: `160`
- `max_count_per_token_per_document`: `3`

## Top Browsing Signals

| Lemma | Signal | Boost | Source Terms | Target Terms | Ambiguous Source Terms |
| --- | ---: | ---: | --- | --- | --- |
| `documento` | 0.2447 | 1.0612 | document | - | - |
| `dolor` | 0.2447 | 1.0612 | pain | - | - |
| `fila` | 0.2447 | 1.0612 | rate | - | - |
| `haber` | 0.2447 | 1.0612 | credit | - | - |
| `infección` | 0.2447 | 1.0612 | infection | - | - |
| `pago` | 0.2447 | 1.0612 | payment | - | - |
| `prestar` | 0.2447 | 1.0612 | loan | - | - |
| `valor` | 0.2447 | 1.0612 | value | - | - |
| `banco` | 0.1888 | 1.0472 | bank | - | bank |
| `cliente` | 0.1888 | 1.0472 | buyer | - | buyer |
| `comprador` | 0.1888 | 1.0472 | buyer | - | buyer |
| `doctor` | 0.1888 | 1.0472 | doctor | - | doctor |
| `escaño` | 0.1888 | 1.0472 | bank | - | bank |
| `interesar` | 0.1888 | 1.0472 | interest | - | interest |
| `interés` | 0.1888 | 1.0472 | interest | - | interest |
| `medicamento` | 0.1888 | 1.0472 | medicine | - | medicine |
| `medicina` | 0.1888 | 1.0472 | medicine | - | medicine |
| `médico` | 0.1888 | 1.0472 | doctor | - | doctor |
| `visita` | 0.1888 | 1.0472 | visit | - | visit |
| `visitar` | 0.1888 | 1.0472 | visit | - | visit |

## Top Unmapped Tokens

| Token | Count |
| --- | ---: |
| `mortgage` | 2 |
| `approved` | 1 |
| `clinic` | 1 |
| `diagnosis` | 1 |
| `discussed` | 1 |
| `income` | 1 |
| `monthly` | 1 |
| `patient` | 1 |
| `recovery` | 1 |
| `reviewing` | 1 |
| `symptoms` | 1 |

## Browsing-Boosted Top Admission Preview

| Lemma | Neutral Rank | Browsing Rank | Delta | Signal | Boost | Readiness | Difficulty | Source Terms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `cambiar` | 144 | 1 | 143 | 0.1609 | 1.0402 | 1.0 | 0.306 | change |
| `visitar` | 290 | 2 | 288 | 0.1888 | 1.0472 | 1.0 | 0.3197 | visit |
| `prestar` | 457 | 3 | 454 | 0.2447 | 1.0612 | 1.0 | 0.3338 | loan |
| `firmar` | 373 | 4 | 369 | 0.1609 | 1.0402 | 1.0 | 0.327 | sign |
| `turquesa` | 1 | 5 | -4 | 0.0 | 1.0 | 0.9947 | 0.2906 | - |
| `bambalina` | 2 | 6 | -4 | 0.0 | 1.0 | 0.9951 | 0.2909 | - |
| `jalea` | 3 | 7 | -4 | 0.0 | 1.0 | 0.9944 | 0.2903 | - |
| `apreciable` | 4 | 8 | -4 | 0.0 | 1.0 | 0.9942 | 0.2902 | - |
| `alineado` | 5 | 9 | -4 | 0.0 | 1.0 | 0.9941 | 0.2901 | - |
| `laringe` | 6 | 10 | -4 | 0.0 | 1.0 | 0.9954 | 0.2913 | - |
| `veleidad` | 7 | 11 | -4 | 0.0 | 1.0 | 0.994 | 0.29 | - |
| `promulgado` | 8 | 12 | -4 | 0.0 | 1.0 | 0.9938 | 0.2898 | - |
| `simétrico` | 9 | 13 | -4 | 0.0 | 1.0 | 0.9957 | 0.2916 | - |
| `concienciación` | 10 | 14 | -4 | 0.0 | 1.0 | 0.9936 | 0.2896 | - |
| `interestelar` | 11 | 15 | -4 | 0.0 | 1.0 | 0.9959 | 0.2917 | - |
| `inorgánico` | 12 | 16 | -4 | 0.0 | 1.0 | 0.993 | 0.2892 | - |
| `expansivo` | 13 | 17 | -4 | 0.0 | 1.0 | 0.9964 | 0.2922 | - |
| `experimentado` | 14 | 18 | -4 | 0.0 | 1.0 | 0.9926 | 0.2889 | - |
| `reluciente` | 15 | 19 | -4 | 0.0 | 1.0 | 0.9925 | 0.2888 | - |
| `nodo` | 16 | 20 | -4 | 0.0 | 1.0 | 0.9967 | 0.2926 | - |

## Canonical Helper/Core Probe

- Scope: `canonical_helper_core_read_only_probe`
- Helper status: `ok`
- Accepted signals: `32`
- Aggregate items retained: `32`
- Admission budget: `10`
- Raw text stored: `False`
- URL stored: `False`
- Runtime SRS mutation: `False`

| Strength | Browsing Budget | Browsing Lane Share | Relevant Share | Driven Share | Selected |
| --- | ---: | ---: | ---: | ---: | --- |
| `off` | 0 | 0.0 | 0.0 | 0.0 | turquesa, bambalina, jalea, apreciable, alineado, laringe, veleidad, promulgado, simétrico, concienciación |
| `balanced` | 2 | 0.2 | 0.2 | 0.2 | cambiar, visitar, turquesa, bambalina, jalea, apreciable, alineado, laringe, veleidad, promulgado |
| `strong` | 5 | 0.5 | 0.5 | 0.5 | prestar, cambiar, visitar, firmar, interesar, turquesa, bambalina, jalea, apreciable, alineado |

| Strength | Lemma | Selected | Lane | Approx P | Browsing P | General P | Signal |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `off` | `turquesa` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `bambalina` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `jalea` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `apreciable` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `alineado` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `laringe` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `veleidad` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `off` | `promulgado` | True | `general` | 0.005675 | 0.0 | 0.005675 | 0.0 |
| `balanced` | `cambiar` | True | `browsing` | 0.305272 | 0.30214 | 0.004488 | 0.160858 |
| `balanced` | `visitar` | True | `browsing` | 0.302758 | 0.299664 | 0.004418 | 0.188761 |
| `balanced` | `turquesa` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `balanced` | `bambalina` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `balanced` | `jalea` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `balanced` | `apreciable` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `balanced` | `alineado` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `balanced` | `laringe` | True | `general` | 0.004542 | 0.0 | 0.004542 | 0.0 |
| `strong` | `prestar` | True | `browsing` | 0.594703 | 0.593598 | 0.002718 | 0.244651 |
| `strong` | `cambiar` | True | `browsing` | 0.593905 | 0.592761 | 0.002807 | 0.160858 |
| `strong` | `visitar` | True | `browsing` | 0.592367 | 0.591238 | 0.002763 | 0.188761 |
| `strong` | `firmar` | True | `browsing` | 0.585011 | 0.583871 | 0.00274 | 0.160858 |
| `strong` | `interesar` | True | `browsing` | 0.574653 | 0.57353 | 0.002633 | 0.188761 |
| `strong` | `turquesa` | True | `general` | 0.002841 | 0.0 | 0.002841 | 0.0 |
| `strong` | `bambalina` | True | `general` | 0.002841 | 0.0 | 0.002841 | 0.0 |
| `strong` | `jalea` | True | `general` | 0.002841 | 0.0 | 0.002841 | 0.0 |

## Research Findings

| Severity | Finding | Detail |
| --- | --- | --- |
| `info` | `unmapped_browsing_tokens_present` | Some usable page tokens had no source/target lookup hit; inspect top_unmapped_tokens before treating source coverage as complete. |
| `review` | `source_target_ambiguity_is_material` | At least half of boosted lemmas came from ambiguous source mappings; production scoring should keep confidence damping and review LP-specific minimum confidence thresholds. |
| `review` | `ranked_preview_is_sensitive_to_small_boosts` | The ranked top-N preview can move clustered candidates sharply; production admission should validate realized sampling share, not only rank movement. |

## Limitations

- This is a read-only research harness; it does not capture live browser pages.
- Topic inference from browsing is intentionally out of scope for P0.
- Source-target ambiguity is dampened, not solved semantically.
- Visible-text extraction is approximated from supplied plain text fixtures.
- Browsing boosts admission scores only in this diagnostic report; scheduling is untouched.
