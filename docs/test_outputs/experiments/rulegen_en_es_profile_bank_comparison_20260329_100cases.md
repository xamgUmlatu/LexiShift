# Rulegen Profile Bank Analysis (en-es)

- Generated at: `2026-03-28T20:28:55.234371+00:00`
- Profiles: `canonical`, `admission-tight`, `combined-balanced`, `family-followup`

## Aggregate Metrics

| Profile | Objective | Top1 | Top3 | ForbidAny | AvgRules | Triage | Config |
|---|---:|---:|---:|---:|---:|---:|---|
| canonical | 131.180 | 89.00% | 100.00% | 0.00% | 2.97 | 11 | `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| admission-tight | 136.900 | 88.00% | 100.00% | 0.00% | 1.85 | 12 | `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| combined-balanced | 134.860 | 88.00% | 100.00% | 0.00% | 2.19 | 12 | `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10` |
| family-followup | 136.900 | 88.00% | 100.00% | 0.00% | 1.85 | 12 | `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off` |

## Main Reading

- Top-1 winner differences across the frozen profile bank: **1 cases**.
- Top-3 coverage differences across the frozen profile bank: **0 cases**.
- Rule-count differences across the frozen profile bank: **54 cases**.

## Trait Regions

- `candidate_variant_pressure` = `variant-absent`
  case_count=99 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=131.07, `admission-tight`=136.79, `combined-balanced`=134.73, `family-followup`=136.79
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:aplicación`, `en-es:archivo`, `en-es:banco`, `en-es:banda`, `en-es:batería`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:carpeta`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:clave`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:dinero`, `en-es:directorio`, `en-es:enlace`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:lengua`, `en-es:libro`, `en-es:llevar`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:mando`, `en-es:marco`, `en-es:margen`, `en-es:masa`, `en-es:medio`, `en-es:mensaje`, `en-es:meter`, `en-es:movimiento`, `en-es:mundo`, `en-es:móvil`, `en-es:navegador`, `en-es:nodo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:pantalla`, `en-es:parte`, `en-es:patrón`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:plaza`, `en-es:portal`, `en-es:presentar`, `en-es:puente`, `en-es:puerto`, `en-es:punto`, `en-es:quitar`, `en-es:radio`, `en-es:ratón`, `en-es:red`, `en-es:registro`, `en-es:sacar`, `en-es:salir`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:seña`, `en-es:señal`, `en-es:sitio`, `en-es:subir`, `en-es:tabla`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:trazo`, `en-es:tráfico`, `en-es:ventana`, `en-es:vida`, `en-es:vista`, `en-es:área`
- `candidate_reverse_hit_band` = `1-2`
  case_count=63 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=140.86, `admission-tight`=143.08, `combined-balanced`=141.65, `family-followup`=143.08
  cases: `en-es:agua`, `en-es:amigo`, `en-es:amor`, `en-es:aplicación`, `en-es:archivo`, `en-es:banco`, `en-es:cadena`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:carpeta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:enlace`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:gato`, `en-es:hilo`, `en-es:lengua`, `en-es:libro`, `en-es:luz`, `en-es:madre`, `en-es:malla`, `en-es:margen`, `en-es:masa`, `en-es:mensaje`, `en-es:movimiento`, `en-es:mundo`, `en-es:móvil`, `en-es:nodo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:portal`, `en-es:puente`, `en-es:puerto`, `en-es:quitar`, `en-es:ratón`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:seña`, `en-es:señal`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:trazo`, `en-es:tráfico`, `en-es:ventana`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-heavy`
  case_count=53 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=126.30, `admission-tight`=133.70, `combined-balanced`=131.21, `family-followup`=133.70
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:batería`, `en-es:carpeta`, `en-es:carta`, `en-es:celda`, `en-es:coger`, `en-es:crear`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:ese`, `en-es:fondo`, `en-es:gato`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:lengua`, `en-es:llevar`, `en-es:luz`, `en-es:malla`, `en-es:mando`, `en-es:marco`, `en-es:margen`, `en-es:medio`, `en-es:meter`, `en-es:móvil`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:padre`, `en-es:pantalla`, `en-es:parte`, `en-es:perfil`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:quitar`, `en-es:red`, `en-es:registro`, `en-es:sacar`, `en-es:salir`, `en-es:según`, `en-es:servidor`, `en-es:sitio`, `en-es:subir`, `en-es:tabla`, `en-es:ventana`, `en-es:vida`
- `candidate_row_count_band` = `0-4`
  case_count=48 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=143.96, `admission-tight`=145.46, `combined-balanced`=144.71, `family-followup`=145.46
  cases: `en-es:amigo`, `en-es:amor`, `en-es:archivo`, `en-es:banco`, `en-es:camino`, `en-es:capital`, `en-es:carta`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:ese`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:lengua`, `en-es:libro`, `en-es:madre`, `en-es:margen`, `en-es:masa`, `en-es:mensaje`, `en-es:movimiento`, `en-es:mundo`, `en-es:navegador`, `en-es:nodo`, `en-es:nota`, `en-es:ocurrir`, `en-es:orden`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:portal`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:servidor`, `en-es:seña`, `en-es:subir`, `en-es:tecla`, `en-es:trabajo`, `en-es:trazo`, `en-es:tráfico`, `en-es:área`
- `candidate_phrase_pressure` = `phrase-light`
  case_count=46 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=136.57, `admission-tight`=140.35, `combined-balanced`=138.78, `family-followup`=140.35
  cases: `en-es:amigo`, `en-es:aplicación`, `en-es:banda`, `en-es:cadena`, `en-es:camino`, `en-es:campo`, `en-es:canal`, `en-es:capital`, `en-es:cargo`, `en-es:casa`, `en-es:caso`, `en-es:ciudad`, `en-es:clave`, `en-es:cura`, `en-es:dinero`, `en-es:directorio`, `en-es:enlace`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:firma`, `en-es:libro`, `en-es:madre`, `en-es:masa`, `en-es:mensaje`, `en-es:movimiento`, `en-es:mundo`, `en-es:navegador`, `en-es:nodo`, `en-es:patrón`, `en-es:pestaña`, `en-es:planta`, `en-es:portal`, `en-es:puerto`, `en-es:radio`, `en-es:ratón`, `en-es:sección`, `en-es:seña`, `en-es:señal`, `en-es:tecla`, `en-es:trabajo`, `en-es:trama`, `en-es:trazo`, `en-es:tráfico`, `en-es:vista`, `en-es:área`
- `candidate_definition_bucket_band` = `3-4`
  case_count=35 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=132.29, `admission-tight`=134.57, `combined-balanced`=132.86, `family-followup`=134.57
  cases: `en-es:aplicación`, `en-es:archivo`, `en-es:banco`, `en-es:banda`, `en-es:batería`, `en-es:camino`, `en-es:canal`, `en-es:cargo`, `en-es:carta`, `en-es:cura`, `en-es:ese`, `en-es:firma`, `en-es:hasta`, `en-es:lengua`, `en-es:madre`, `en-es:malla`, `en-es:mando`, `en-es:margen`, `en-es:masa`, `en-es:mundo`, `en-es:móvil`, `en-es:navegador`, `en-es:orden`, `en-es:padre`, `en-es:patrón`, `en-es:perfil`, `en-es:pestaña`, `en-es:planta`, `en-es:radio`, `en-es:sección`, `en-es:según`, `en-es:servidor`, `en-es:subir`, `en-es:ventana`, `en-es:área`
- `candidate_row_count_band` = `5-9`
  case_count=32 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=126.69, `admission-tight`=132.75, `combined-balanced`=129.94, `family-followup`=132.75
  cases: `en-es:agua`, `en-es:aplicación`, `en-es:banda`, `en-es:batería`, `en-es:cadena`, `en-es:campo`, `en-es:canal`, `en-es:cargo`, `en-es:clave`, `en-es:cura`, `en-es:hasta`, `en-es:hilo`, `en-es:hora`, `en-es:luz`, `en-es:malla`, `en-es:mando`, `en-es:marco`, `en-es:móvil`, `en-es:padre`, `en-es:pantalla`, `en-es:patrón`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:según`, `en-es:señal`, `en-es:sitio`, `en-es:tabla`, `en-es:trama`, `en-es:ventana`, `en-es:vista`
- `candidate_reverse_hit_band` = `3-5`
  case_count=29 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=120.21, `admission-tight`=130.76, `combined-balanced`=127.66, `family-followup`=130.76
  cases: `en-es:acabar`, `en-es:banda`, `en-es:batería`, `en-es:camino`, `en-es:campo`, `en-es:carta`, `en-es:clave`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:cura`, `en-es:derecho`, `en-es:fondo`, `en-es:hasta`, `en-es:hora`, `en-es:mando`, `en-es:marco`, `en-es:meter`, `en-es:pantalla`, `en-es:patrón`, `en-es:pestaña`, `en-es:planta`, `en-es:presentar`, `en-es:punto`, `en-es:radio`, `en-es:sitio`, `en-es:tabla`, `en-es:vida`, `en-es:vista`
- `candidate_definition_bucket_band` = `0-2`
  case_count=27 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=149.11, `admission-tight`=150.00, `combined-balanced`=149.11, `family-followup`=150.00
  cases: `en-es:amigo`, `en-es:amor`, `en-es:capital`, `en-es:casa`, `en-es:caso`, `en-es:celda`, `en-es:ciudad`, `en-es:crear`, `en-es:dinero`, `en-es:directorio`, `en-es:escuela`, `en-es:estilo`, `en-es:familia`, `en-es:libro`, `en-es:mensaje`, `en-es:movimiento`, `en-es:nodo`, `en-es:nota`, `en-es:ocurrir`, `en-es:portal`, `en-es:puerto`, `en-es:ratón`, `en-es:seña`, `en-es:tecla`, `en-es:trabajo`, `en-es:trazo`, `en-es:tráfico`
- `candidate_family` = `register_region`
  case_count=24 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=130.67, `admission-tight`=136.00, `combined-balanced`=133.00, `family-followup`=136.00
  cases: `en-es:acabar`, `en-es:agua`, `en-es:amigo`, `en-es:carpeta`, `en-es:coger`, `en-es:cura`, `en-es:ese`, `en-es:gato`, `en-es:hora`, `en-es:llevar`, `en-es:madre`, `en-es:mando`, `en-es:medio`, `en-es:meter`, `en-es:mundo`, `en-es:móvil`, `en-es:padre`, `en-es:pantalla`, `en-es:ratón`, `en-es:red`, `en-es:salir`, `en-es:sitio`, `en-es:tabla`, `en-es:tráfico`
- `candidate_definition_bucket_band` = `5-7`
  case_count=22 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=124.55, `admission-tight`=134.64, `combined-balanced`=132.18, `family-followup`=134.64
  cases: `en-es:agua`, `en-es:cadena`, `en-es:campo`, `en-es:carpeta`, `en-es:clave`, `en-es:enlace`, `en-es:fondo`, `en-es:hilo`, `en-es:hora`, `en-es:luz`, `en-es:marco`, `en-es:pantalla`, `en-es:plaza`, `en-es:presentar`, `en-es:puente`, `en-es:punto`, `en-es:registro`, `en-es:señal`, `en-es:sitio`, `en-es:tabla`, `en-es:trama`, `en-es:vista`
- `candidate_definition_bucket_band` = `8+`
  case_count=15 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=105.33, `admission-tight`=121.33, `combined-balanced`=116.93, `family-followup`=121.33
  cases: `en-es:acabar`, `en-es:coger`, `en-es:cuadro`, `en-es:cuenta`, `en-es:derecho`, `en-es:gato`, `en-es:llevar`, `en-es:medio`, `en-es:meter`, `en-es:parte`, `en-es:quitar`, `en-es:red`, `en-es:sacar`, `en-es:salir`, `en-es:vida`
- `candidate_family` = `math_geometry`
  case_count=13 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=103.08, `admission-tight`=110.00, `combined-balanced`=108.15, `family-followup`=110.00
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuadro`, `en-es:cuenta`, `en-es:enlace`, `en-es:medio`, `en-es:navegador`, `en-es:pantalla`, `en-es:pestaña`, `en-es:subir`, `en-es:tabla`, `en-es:trama`
- `candidate_family` = `mechanics_tools`
  case_count=13 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=110.77, `admission-tight`=117.69, `combined-balanced`=115.85, `family-followup`=117.69
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuenta`, `en-es:enlace`, `en-es:luz`, `en-es:navegador`, `en-es:pantalla`, `en-es:pestaña`, `en-es:radio`, `en-es:red`, `en-es:subir`, `en-es:tabla`
- `candidate_family` = `computing`
  case_count=12 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=119.00, `admission-tight`=124.50, `combined-balanced`=123.00, `family-followup`=124.50
  cases: `en-es:archivo`, `en-es:cadena`, `en-es:carpeta`, `en-es:cuenta`, `en-es:enlace`, `en-es:navegador`, `en-es:nodo`, `en-es:pantalla`, `en-es:perfil`, `en-es:pestaña`, `en-es:subir`, `en-es:tabla`
- `candidate_row_count_band` = `10-14`
  case_count=11 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=108.73, `admission-tight`=120.73, `combined-balanced`=116.36, `family-followup`=120.73
  cases: `en-es:acabar`, `en-es:carpeta`, `en-es:cuenta`, `en-es:enlace`, `en-es:fondo`, `en-es:gato`, `en-es:meter`, `en-es:quitar`, `en-es:red`, `en-es:registro`, `en-es:vida`
- `candidate_row_count_band` = `15+`
  case_count=8 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=102.00, `admission-tight`=123.00, `combined-balanced`=119.25, `family-followup`=123.00
  cases: `en-es:coger`, `en-es:cuadro`, `en-es:derecho`, `en-es:llevar`, `en-es:medio`, `en-es:parte`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `art_media`
  case_count=6 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=128.33, `admission-tight`=132.33, `combined-balanced`=131.33, `family-followup`=132.33
  cases: `en-es:cadena`, `en-es:cuadro`, `en-es:lengua`, `en-es:medio`, `en-es:ventana`, `en-es:vista`
- `candidate_family` = `government_law`
  case_count=6 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=127.00, `admission-tight`=148.00, `combined-balanced`=143.00, `family-followup`=148.00
  cases: `en-es:banda`, `en-es:enlace`, `en-es:medio`, `en-es:parte`, `en-es:presentar`, `en-es:vista`
- `candidate_reverse_hit_band` = `6+`
  case_count=6 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=95.67, `admission-tight`=114.67, `combined-balanced`=110.67, `family-followup`=114.67
  cases: `en-es:llevar`, `en-es:medio`, `en-es:red`, `en-es:registro`, `en-es:sacar`, `en-es:salir`
- `candidate_family` = `biology`
  case_count=5 best=`admission-tight`, `combined-balanced`, `family-followup`
  avg_case_objective: `canonical`=145.60, `admission-tight`=149.20, `combined-balanced`=149.20, `family-followup`=149.20
  cases: `en-es:luz`, `en-es:nodo`, `en-es:pestaña`, `en-es:planta`, `en-es:radio`
- `candidate_family` = `communication_network`
  case_count=4 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=92.00, `admission-tight`=98.00, `combined-balanced`=96.50, `family-followup`=98.00
  cases: `en-es:medio`, `en-es:navegador`, `en-es:puente`, `en-es:red`
- `candidate_family` = `music`
  case_count=3 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=140.00, `admission-tight`=148.00, `combined-balanced`=146.00, `family-followup`=148.00
  cases: `en-es:banda`, `en-es:batería`, `en-es:clave`
- `candidate_family` = `chemistry`
  case_count=2 best=`admission-tight`, `family-followup`
  avg_case_objective: `canonical`=139.00, `admission-tight`=148.00, `combined-balanced`=145.00, `family-followup`=148.00
  cases: `en-es:enlace`, `en-es:radio`
