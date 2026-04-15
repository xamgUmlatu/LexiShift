# Rulegen Profile Bank Analysis (en-es)

- Generated at: `2026-03-28T18:40:51.321304+00:00`
- Profiles: `canonical`, `admission-tight`, `combined-balanced`, `family-followup`

## Aggregate Metrics

| Profile | Objective | Top1 | Top3 | ForbidAny | AvgRules | Triage | Config |
|---|---:|---:|---:|---:|---:|---:|---|
| canonical | 133.455 | 90.91% | 100.00% | 0.00% | 2.91 | 7 | `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=0.20 w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| admission-tight | 140.623 | 90.91% | 96.10% | 0.00% | 1.32 | 7 | `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| combined-balanced | 137.896 | 90.91% | 100.00% | 0.00% | 2.17 | 7 | `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| family-followup | 139.922 | 90.91% | 100.00% | 0.00% | 1.83 | 7 | `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off` |

## Main Reading

- Top-1 winner differences across the frozen profile bank: **1 cases**.
- Top-3 coverage differences across the frozen profile bank: **3 cases**.
- Rule-count differences across the frozen profile bank: **59 cases**.

## Trait Regions

- `candidate_variant_pressure` = `variant-absent`
  case_count=76 best=`admission-tight`
  avg_case_objective: `canonical`=133.34, `admission-tight`=140.45, `combined-balanced`=137.76, `family-followup`=139.82
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:clave`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:dinero`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hora`, `en-es:lengua`, `en-es:libro`, `en-es:llevar`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:marco`, `en-es:margen`, `en-es:masa`, `en-es:medio`, `en-es:meter`, `en-es:movimiento`, `en-es:mundo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:planta`, `en-es:plaza`, `en-es:presentar`, `en-es:puerto`, `en-es:punto`, `en-es:quitar`, `en-es:radio`, `en-es:ratón`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:sección`, `en-es:según`, `en-es:seña`, `en-es:señal`, `en-es:subir`, `en-es:tabla`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:vida`, `en-es:vista`, `en-es:área`
- `candidate_reverse_hit_band` = `1-2`
  case_count=48 best=`admission-tight`
  avg_case_objective: `canonical`=139.75, `admission-tight`=146.00, `combined-balanced`=142.00, `family-followup`=143.38
  cases: `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:cadena`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:gato`, `en-es:lengua`, `en-es:libro`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:margen`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:puerto`, `en-es:quitar`, `en-es:ratón`, `en-es:sección`, `en-es:según`, `en-es:seña`, `en-es:señal`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-heavy`
  case_count=42 best=`family-followup`
  avg_case_objective: `canonical`=127.95, `admission-tight`=135.81, `combined-balanced`=134.52, `family-followup`=136.95
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:carta`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:ese`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hora`, `en-es:lengua`, `en-es:llevar`, `en-es:luz`, `en-es:malla`, `en-es:marco`, `en-es:margen`, `en-es:medio`, `en-es:meter`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:presentar`, `en-es:punto`, `en-es:quitar`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:según`, `en-es:subir`, `en-es:tabla`, `en-es:vida`
- `candidate_row_count_band` = `0-4`
  case_count=38 best=`admission-tight`
  avg_case_objective: `canonical`=145.53, `admission-tight`=149.95, `combined-balanced`=146.16, `family-followup`=146.95
  cases: `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:camino`, `en-es:capital`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:lengua`, `en-es:libro`, `en-es:madre`, `en-es:margen`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:perfil`, `en-es:planta`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:seña`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-light`
  case_count=34 best=`admission-tight`
  avg_case_objective: `canonical`=140.00, `admission-tight`=146.18, `combined-balanced`=141.76, `family-followup`=143.35
  cases: `en-es:amigo`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:clave`, `en-es:cura`, `en-es:dinero`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:libro`, `en-es:madre`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:planta`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:seña`, `en-es:señal`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:vista`, `en-es:área`
- `candidate_definition_bucket_band` = `3-4`
  case_count=26 best=`admission-tight`
  avg_case_objective: `canonical`=140.69, `admission-tight`=148.77, `combined-balanced`=143.46, `family-followup`=145.08
  cases: `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:camino`, `en-es:canal`, `en-es:cargo`, `en-es:carta`, `en-es:cura`, `en-es:ese`, `en-es:firma`, `en-es:hasta`, `en-es:lengua`, `en-es:madre`, `en-es:malla`, `en-es:margen`, `en-es:masa`, `en-es:mundo`, `en-es:orden`, `en-es:padre`, `en-es:perfil`, `en-es:planta`, `en-es:radio`, `en-es:sección`, `en-es:según`, `en-es:subir`, `en-es:área`
- `candidate_reverse_hit_band` = `3-5`
  case_count=23 best=`family-followup`
  avg_case_objective: `canonical`=124.78, `admission-tight`=133.65, `combined-balanced`=131.83, `family-followup`=134.96
  cases: `en-es:acabar`, `en-es:batería`, `en-es:camino`, `en-es:campo`, `en-es:carta`, `en-es:clave`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:fondo`, `en-es:hasta`, `en-es:hora`, `en-es:marco`, `en-es:meter`, `en-es:planta`, `en-es:presentar`, `en-es:punto`, `en-es:radio`, `en-es:tabla`, `en-es:vida`, `en-es:vista`
- `candidate_row_count_band` = `5-9`
  case_count=22 best=`admission-tight`
  avg_case_objective: `canonical`=131.27, `admission-tight`=142.73, `combined-balanced`=137.00, `family-followup`=139.73
  cases: `en-es:agua`, `en-es:batería`, `en-es:cadena`, `en-es:campo`, `en-es:canal`, `en-es:cargo`, `en-es:clave`, `en-es:cura`, `en-es:hasta`, `en-es:hora`, `en-es:luz`, `en-es:malla`, `en-es:marco`, `en-es:padre`, `en-es:plaza`, `en-es:presentar`, `en-es:punto`, `en-es:según`, `en-es:señal`, `en-es:tabla`, `en-es:trama`, `en-es:vista`
- `candidate_definition_bucket_band` = `0-2`
  case_count=20 best=`admission-tight`
  avg_case_objective: `canonical`=149.20, `admission-tight`=152.20, `combined-balanced`=149.20, `family-followup`=150.10
  cases: `en-es:amigo`, `en-es:amor`, `en-es:capital`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:libro`, `en-es:movimiento`, `en-es:nota`, `en-es:ocurrir`, `en-es:puerto`, `en-es:ratón`, `en-es:seña`, `en-es:tecla`, `en-es:trabajo`
- `candidate_family` = `register_region`
  case_count=18 best=`family-followup`
  avg_case_objective: `canonical`=133.44, `admission-tight`=142.78, `combined-balanced`=140.11, `family-followup`=143.11
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:coger`, `en-es:cura`, `en-es:ese`, `en-es:gato`, `en-es:hora`, `en-es:llevar`, `en-es:madre`, `en-es:medio`, `en-es:meter`, `en-es:mundo`, `en-es:padre`, `en-es:ratón`, `en-es:red`, `en-es:salir`, `en-es:tabla`
- `candidate_definition_bucket_band` = `5-7`
  case_count=15 best=`admission-tight`
  avg_case_objective: `canonical`=127.47, `admission-tight`=138.67, `combined-balanced`=133.47, `family-followup`=135.47
  cases: `en-es:agua`, `en-es:cadena`, `en-es:campo`, `en-es:clave`, `en-es:fondo`, `en-es:hora`, `en-es:luz`, `en-es:marco`, `en-es:plaza`, `en-es:presentar`, `en-es:punto`, `en-es:señal`, `en-es:tabla`, `en-es:trama`, `en-es:vista`
- `candidate_definition_bucket_band` = `8+`
  case_count=15 best=`family-followup`
  avg_case_objective: `canonical`=105.33, `admission-tight`=112.13, `combined-balanced`=116.93, `family-followup`=121.33
  cases: `en-es:acabar`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:gato`, `en-es:llevar`, `en-es:medio`, `en-es:meter`, `en-es:parte`, `en-es:quitar`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:vida`
- `candidate_family` = `math_geometry`
  case_count=8 best=`family-followup`
  avg_case_objective: `canonical`=93.50, `admission-tight`=86.75, `combined-balanced`=96.50, `family-followup`=98.75
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:cuadro`, `en-es:cuenta`, `en-es:medio`, `en-es:subir`, `en-es:tabla`, `en-es:trama`
- `candidate_family` = `mechanics_tools`
  case_count=8 best=`family-followup`
  avg_case_objective: `canonical`=105.25, `admission-tight`=99.25, `combined-balanced`=109.00, `family-followup`=111.25
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:cuenta`, `en-es:luz`, `en-es:radio`, `en-es:red`, `en-es:subir`, `en-es:tabla`
- `candidate_row_count_band` = `10-14`
  case_count=8 best=`family-followup`
  avg_case_objective: `canonical`=112.50, `admission-tight`=111.00, `combined-balanced`=118.50, `family-followup`=123.00
  cases: `en-es:acabar`, `en-es:cuenta`, `en-es:fondo`, `en-es:gato`, `en-es:meter`, `en-es:quitar`, `en-es:red`, `en-es:vida`
- `candidate_row_count_band` = `15+`
  case_count=8 best=`family-followup`
  avg_case_objective: `canonical`=102.00, `admission-tight`=118.50, `combined-balanced`=119.25, `family-followup`=123.00
  cases: `en-es:coger`, `en-es:cuadro`, `en-es:derecho`, `en-es:llevar`, `en-es:medio`, `en-es:parte`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `computing`
  case_count=6 best=`family-followup`
  avg_case_objective: `canonical`=112.67, `admission-tight`=108.67, `combined-balanced`=114.67, `family-followup`=116.67
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:cuenta`, `en-es:perfil`, `en-es:subir`, `en-es:tabla`
- `candidate_family` = `art_media`
  case_count=5 best=`family-followup`
  avg_case_objective: `canonical`=124.40, `admission-tight`=120.80, `combined-balanced`=128.00, `family-followup`=129.20
  cases: `en-es:cadena`, `en-es:cuadro`, `en-es:lengua`, `en-es:medio`, `en-es:vista`
- `candidate_reverse_hit_band` = `6+`
  case_count=5 best=`family-followup`
  avg_case_objective: `canonical`=111.20, `admission-tight`=118.40, `combined-balanced`=124.40, `family-followup`=128.00
  cases: `en-es:llevar`, `en-es:medio`, `en-es:red`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `government_law`
  case_count=4 best=`admission-tight`
  avg_case_objective: `canonical`=122.50, `admission-tight`=149.50, `combined-balanced`=143.50, `family-followup`=148.00
  cases: `en-es:medio`, `en-es:parte`, `en-es:presentar`, `en-es:vista`
- `candidate_family` = `biology`
  case_count=3 best=`admission-tight`
  avg_case_objective: `canonical`=144.00, `admission-tight`=154.00, `combined-balanced`=148.00, `family-followup`=148.00
  cases: `en-es:luz`, `en-es:planta`, `en-es:radio`
- `candidate_family` = `communication_network`
  case_count=2 best=`family-followup`
  avg_case_objective: `canonical`=89.00, `admission-tight`=71.00, `combined-balanced`=95.00, `family-followup`=98.00
  cases: `en-es:medio`, `en-es:red`
- `candidate_family` = `music`
  case_count=2 best=`admission-tight`
  avg_case_objective: `canonical`=145.00, `admission-tight`=154.00, `combined-balanced`=148.00, `family-followup`=148.00
  cases: `en-es:batería`, `en-es:clave`
