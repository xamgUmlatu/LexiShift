# Rulegen Profile Bank Analysis (en-es)

- Generated at: `2026-03-28T20:09:39.321711+00:00`
- Profiles: `canonical`, `admission-tight`, `combined-balanced`, `family-followup`

## Aggregate Metrics

| Profile | Objective | Top1 | Top3 | ForbidAny | AvgRules | Triage | Config |
|---|---:|---:|---:|---:|---:|---:|---|
| canonical | 133.455 | 90.91% | 100.00% | 0.00% | 2.91 | 8 | `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| admission-tight | 138.727 | 89.77% | 100.00% | 0.00% | 1.84 | 9 | `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| combined-balanced | 136.818 | 89.77% | 100.00% | 0.00% | 2.16 | 9 | `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| family-followup | 138.727 | 89.77% | 100.00% | 0.00% | 1.84 | 9 | `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off` |

## Main Reading

- Top-1 winner differences across the frozen profile bank: **1 cases**.
- Top-3 coverage differences across the frozen profile bank: **0 cases**.
- Rule-count differences across the frozen profile bank: **46 cases**.

## Trait Regions

- `candidate_variant_pressure` = `variant-absent`
  case_count=87 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=133.36, `admission-tight`=138.62, `combined-balanced`=136.69, `family-followup`=138.62
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:carpeta`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:clave`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:lengua`, `en-es:libro`, `en-es:llevar`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:marco`, `en-es:margen`, `en-es:masa`, `en-es:medio`, `en-es:meter`, `en-es:movimiento`, `en-es:mundo`, `en-es:móvil`, `en-es:navegador`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:plaza`, `en-es:portal`, `en-es:presentar`, `en-es:puente`, `en-es:puerto`, `en-es:punto`, `en-es:quitar`, `en-es:radio`, `en-es:ratón`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:seña`, `en-es:señal`, `en-es:subir`, `en-es:tabla`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:ventana`, `en-es:vida`, `en-es:vista`, `en-es:área`
- `candidate_reverse_hit_band` = `1-2`
  case_count=57 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=140.32, `admission-tight`=142.46, `combined-balanced`=141.09, `family-followup`=142.46
  cases: `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:cadena`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:carpeta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:gato`, `en-es:hilo`, `en-es:lengua`, `en-es:libro`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:margen`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:móvil`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:portal`, `en-es:puente`, `en-es:puerto`, `en-es:quitar`, `en-es:ratón`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:seña`, `en-es:señal`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:ventana`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-heavy`
  case_count=49 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=129.96, `admission-tight`=136.61, `combined-balanced`=134.29, `family-followup`=136.61
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:carpeta`, `en-es:carta`, `en-es:celda`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:ese`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:lengua`, `en-es:llevar`, `en-es:luz`, `en-es:malla`, `en-es:marco`, `en-es:margen`, `en-es:medio`, `en-es:meter`, `en-es:móvil`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:quitar`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:según`, `en-es:servidor`, `en-es:subir`, `en-es:tabla`, `en-es:ventana`, `en-es:vida`
- `candidate_row_count_band` = `0-4`
  case_count=44 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=143.59, `admission-tight`=145.09, `combined-balanced`=144.41, `family-followup`=145.09
  cases: `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:camino`, `en-es:capital`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:lengua`, `en-es:libro`, `en-es:madre`, `en-es:margen`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:navegador`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:portal`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:servidor`, `en-es:seña`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-light`
  case_count=38 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=137.74, `admission-tight`=141.21, `combined-balanced`=139.79, `family-followup`=141.21
  cases: `en-es:amigo`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:clave`, `en-es:cura`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:libro`, `en-es:madre`, `en-es:masa`, `en-es:movimiento`, `en-es:mundo`, `en-es:navegador`, `en-es:pestaña`, `en-es:planta`, `en-es:portal`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:seña`, `en-es:señal`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:vista`, `en-es:área`
- `candidate_definition_bucket_band` = `3-4`
  case_count=31 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=137.87, `admission-tight`=139.29, `combined-balanced`=137.74, `family-followup`=139.29
  cases: `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:camino`, `en-es:canal`, `en-es:cargo`, `en-es:carta`, `en-es:cura`, `en-es:ese`, `en-es:firma`, `en-es:hasta`, `en-es:lengua`, `en-es:madre`, `en-es:malla`, `en-es:margen`, `en-es:masa`, `en-es:mundo`, `en-es:móvil`, `en-es:navegador`, `en-es:orden`, `en-es:padre`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:radio`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:subir`, `en-es:ventana`, `en-es:área`
- `candidate_row_count_band` = `5-9`
  case_count=26 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=131.77, `admission-tight`=136.92, `combined-balanced`=134.15, `family-followup`=136.92
  cases: `en-es:agua`, `en-es:batería`, `en-es:cadena`, `en-es:campo`, `en-es:canal`, `en-es:cargo`, `en-es:clave`, `en-es:cura`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:luz`, `en-es:malla`, `en-es:marco`, `en-es:móvil`, `en-es:padre`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:según`, `en-es:señal`, `en-es:tabla`, `en-es:trama`, `en-es:ventana`, `en-es:vista`
- `candidate_reverse_hit_band` = `3-5`
  case_count=24 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=125.25, `admission-tight`=135.50, `combined-balanced`=132.50, `family-followup`=135.50
  cases: `en-es:acabar`, `en-es:batería`, `en-es:camino`, `en-es:campo`, `en-es:carta`, `en-es:clave`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:fondo`, `en-es:hasta`, `en-es:hora`, `en-es:marco`, `en-es:meter`, `en-es:pestaña`, `en-es:planta`, `en-es:presentar`, `en-es:punto`, `en-es:radio`, `en-es:tabla`, `en-es:vida`, `en-es:vista`
- `candidate_definition_bucket_band` = `0-2`
  case_count=23 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=149.30, `admission-tight`=150.09, `combined-balanced`=149.30, `family-followup`=150.09
  cases: `en-es:amigo`, `en-es:amor`, `en-es:capital`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:libro`, `en-es:movimiento`, `en-es:nota`, `en-es:ocurrir`, `en-es:portal`, `en-es:puerto`, `en-es:ratón`, `en-es:seña`, `en-es:tecla`, `en-es:trabajo`
- `candidate_family` = `register_region`
  case_count=20 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=134.00, `admission-tight`=138.60, `combined-balanced`=135.60, `family-followup`=138.60
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:carpeta`, `en-es:coger`, `en-es:cura`, `en-es:ese`, `en-es:gato`, `en-es:hora`, `en-es:llevar`, `en-es:madre`, `en-es:medio`, `en-es:meter`, `en-es:mundo`, `en-es:móvil`, `en-es:padre`, `en-es:ratón`, `en-es:red`, `en-es:salir`, `en-es:tabla`
- `candidate_definition_bucket_band` = `5-7`
  case_count=18 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=128.56, `admission-tight`=137.22, `combined-balanced`=135.22, `family-followup`=137.22
  cases: `en-es:agua`, `en-es:cadena`, `en-es:campo`, `en-es:carpeta`, `en-es:clave`, `en-es:fondo`, `en-es:hilo`, `en-es:hora`, `en-es:luz`, `en-es:marco`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:señal`, `en-es:tabla`, `en-es:trama`, `en-es:vista`
- `candidate_definition_bucket_band` = `8+`
  case_count=15 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=105.33, `admission-tight`=121.33, `combined-balanced`=116.93, `family-followup`=121.33
  cases: `en-es:acabar`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:gato`, `en-es:llevar`, `en-es:medio`, `en-es:meter`, `en-es:parte`, `en-es:quitar`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:vida`
- `candidate_family` = `math_geometry`
  case_count=11 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=97.09, `admission-tight`=103.09, `combined-balanced`=101.45, `family-followup`=103.09
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuadro`, `en-es:cuenta`, `en-es:medio`, `en-es:navegador`, `en-es:pestaña`, `en-es:subir`, `en-es:tabla`, `en-es:trama`
- `candidate_family` = `mechanics_tools`
  case_count=11 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=106.18, `admission-tight`=112.18, `combined-balanced`=110.55, `family-followup`=112.18
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuenta`, `en-es:luz`, `en-es:navegador`, `en-es:pestaña`, `en-es:radio`, `en-es:red`, `en-es:subir`, `en-es:tabla`
- `candidate_family` = `computing`
  case_count=9 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=111.33, `admission-tight`=116.00, `combined-balanced`=114.67, `family-followup`=116.00
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuenta`, `en-es:navegador`, `en-es:perfil`, `en-es:pestaña`, `en-es:subir`, `en-es:tabla`
- `candidate_row_count_band` = `10-14`
  case_count=9 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=115.78, `admission-tight`=125.78, `combined-balanced`=121.78, `family-followup`=125.78
  cases: `en-es:acabar`, `en-es:carpeta`, `en-es:cuenta`, `en-es:fondo`, `en-es:gato`, `en-es:meter`, `en-es:quitar`, `en-es:red`, `en-es:vida`
- `candidate_row_count_band` = `15+`
  case_count=8 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=102.00, `admission-tight`=123.00, `combined-balanced`=119.25, `family-followup`=123.00
  cases: `en-es:coger`, `en-es:cuadro`, `en-es:derecho`, `en-es:llevar`, `en-es:medio`, `en-es:parte`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `art_media`
  case_count=6 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=128.33, `admission-tight`=132.33, `combined-balanced`=131.33, `family-followup`=132.33
  cases: `en-es:cadena`, `en-es:cuadro`, `en-es:lengua`, `en-es:medio`, `en-es:ventana`, `en-es:vista`
- `candidate_reverse_hit_band` = `6+`
  case_count=5 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=111.20, `admission-tight`=128.00, `combined-balanced`=124.40, `family-followup`=128.00
  cases: `en-es:llevar`, `en-es:medio`, `en-es:red`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `biology`
  case_count=4 best=`admission-tight`, `combined-balanced`, `family-followup`
  avg_case_objective: `canonical`=143.50, `admission-tight`=148.00, `combined-balanced`=148.00, `family-followup`=148.00
  cases: `en-es:luz`, `en-es:pestaña`, `en-es:planta`, `en-es:radio`
- `candidate_family` = `communication_network`
  case_count=4 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=92.00, `admission-tight`=98.00, `combined-balanced`=96.50, `family-followup`=98.00
  cases: `en-es:medio`, `en-es:navegador`, `en-es:puente`, `en-es:red`
- `candidate_family` = `government_law`
  case_count=4 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=122.50, `admission-tight`=148.00, `combined-balanced`=143.50, `family-followup`=148.00
  cases: `en-es:medio`, `en-es:parte`, `en-es:presentar`, `en-es:vista`
- `candidate_family` = `music`
  case_count=2 best=`admission-tight`, `combined-balanced`, `family-followup`
  avg_case_objective: `canonical`=142.00, `admission-tight`=148.00, `combined-balanced`=148.00, `family-followup`=148.00
  cases: `en-es:batería`, `en-es:clave`
