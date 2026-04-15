# SRS Admission Interest Review (`en-es`)

Generated: `2026-04-15T01:32:38.614941+00:00`
Profile: `suisui`
Frequency DB: `C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-es-cde.sqlite`

## Review Basis

This artifact uses the current probabilistic `profile_bootstrap` initialization path.

- `ranked frontier` means the full scored bootstrap frontier sorted by profile score for inspection only.
- `simulated admitted set` means the actual 40-word admission draw from that full frontier using `weighted_without_replacement`.
- Fixed seeds are used here only so this review stays reproducible.
- This replaces the earlier outdated review that sampled from the already-admitted set instead of the full scored frontier.

## Shared Settings

- pair: `en-es`
- bootstrap_top_n: `800`
- initial_active_count: `40`
- selection_policy: `weighted_without_replacement`
- review_seeds: `7, 19, 41`
- proficiency_estimate: `0`
- challenge_target: `0`
- challenge_spread: `none`

## Interest Scenario: `sports`

### Profile Context

- selected_count: `800`
- selected_unique_count: `798`
- admitted_count: `40`
- selector_version: `profile_bootstrap_v3`
- selector_policy_version: `profile_bootstrap_policy_v2`
- active_signals: `interests, proficiency, challenge_preference`
- missing_signals: `none`
- explicit_topic_weight: `1`
- proficiency_estimate: `0`
- challenge_target: `0`

### Topic Support In Neutral Frontier

- candidate_count: `23`
- candidate_ratio: `0.0288`
- support_mass: `6.843738`
- support_mass_ratio: `0.022487`
- scarcity_multiplier_preview: `1`
- scarcity_readiness: `eligible`
- scarcity_readiness_reasons: `none`
- top_examples: `narrador, reunión, barrera, remate, marcar`

### Ranked Frontier Top 8

- topic_hits_in_top_8: `3`

- reunión [noun, score=0.462, mass=0.4971, delta=+32]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- siglo [noun, score=0.455, mass=0.5353, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- millón [noun, score=0.435, mass=0.5139, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- hora [noun, score=0.427, mass=0.5056, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- entrada [noun, score=0.415, mass=0.4574, delta=+47]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- música [noun, score=0.408, mass=0.4849, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- principio [noun, score=0.405, mass=0.4824, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- narrador [noun, score=0.405, mass=0.4102, delta=+216]
  Boosted by topic_affinity, while remaining supported by coverage_gain.

### Simulated Admitted Sets

#### Seed `7`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `4`
- avg_selection_mass_in_admitted_40: `0.3226`

- área [noun, score=0.377, mass=0.451, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- marcar [verb, score=0.373, mass=0.3733, delta=+354]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- luchar [verb, score=0.366, mass=0.3658, delta=+386]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- mayor [adjective, score=0.364, mass=0.4369, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- esfuerzo [noun, score=0.364, mass=0.4369, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- pista [noun, score=0.361, mass=0.4014, delta=+74]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- nacional [adjective, score=0.361, mass=0.4338, delta=-9]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- objetivo [noun, score=0.35, mass=0.421, delta=-11]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `19`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `2`
- avg_selection_mass_in_admitted_40: `0.2989`

- influencia [noun, score=0.362, mass=0.4354, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- penal [noun, score=0.35, mass=0.3567, delta=+347]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- piel [noun, score=0.346, mass=0.417, delta=-13]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- seleccionado [adjective, score=0.331, mass=0.3251, delta=+550]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- batalla [noun, score=0.328, mass=0.3962, delta=-14]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- auto [noun, score=0.305, mass=0.3707, delta=-16]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- experto [noun, score=0.303, mass=0.368, delta=-16]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- llamar [verb, score=0.292, mass=0.3558, delta=-18]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `41`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.2988`

- producción [noun, score=0.384, mass=0.4586, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- necesidad [noun, score=0.369, mass=0.442, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- presencia [noun, score=0.366, mass=0.4395, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- sombra [noun, score=0.337, mass=0.4071, delta=-14]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- departamento [noun, score=0.335, mass=0.4046, delta=-13]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- batalla [noun, score=0.328, mass=0.3962, delta=-14]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- instante [noun, score=0.324, mass=0.3923, delta=-14]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- puesto [noun, score=0.317, mass=0.3845, delta=-15]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

## Interest Scenario: `music`

### Profile Context

- selected_count: `800`
- selected_unique_count: `798`
- admitted_count: `40`
- selector_version: `profile_bootstrap_v3`
- selector_policy_version: `profile_bootstrap_policy_v2`
- active_signals: `interests, proficiency, challenge_preference`
- missing_signals: `none`
- explicit_topic_weight: `1`
- proficiency_estimate: `0`
- challenge_target: `0`

### Topic Support In Neutral Frontier

- candidate_count: `11`
- candidate_ratio: `0.0138`
- support_mass: `3.659525`
- support_mass_ratio: `0.012024`
- scarcity_multiplier_preview: `1.201`
- scarcity_readiness: `eligible`
- scarcity_readiness_reasons: `none`
- top_examples: `orquesta, ronda, continuo, acompañamiento, transportar`

### Ranked Frontier Top 8

- topic_hits_in_top_8: `5`

- orquesta [noun, score=0.507, mass=0.5223, delta=+40]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- movimiento [noun, score=0.478, mass=0.5267, delta=+4]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- siglo [noun, score=0.455, mass=0.5353, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- mayor [adjective, score=0.436, mass=0.4837, delta=+20]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- millón [noun, score=0.435, mass=0.5139, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- hora [noun, score=0.427, mass=0.5056, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- ronda [noun, score=0.424, mass=0.4274, delta=+183]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- continuo [adjective, score=0.41, mass=0.4109, delta=+238]
  Boosted by topic_affinity, while remaining supported by coverage_gain.

### Simulated Admitted Sets

#### Seed `7`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `2`
- avg_selection_mass_in_admitted_40: `0.3246`

- área [noun, score=0.377, mass=0.451, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- resto [noun, score=0.373, mass=0.4468, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- pista [noun, score=0.366, mass=0.4044, delta=+82]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- esfuerzo [noun, score=0.364, mass=0.4369, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- influencia [noun, score=0.362, mass=0.4354, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- favor [noun, score=0.361, mass=0.4336, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- palo [noun, score=0.361, mass=0.3986, delta=+86]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- junio [noun, score=0.346, mass=0.4175, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `19`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `0`
- avg_selection_mass_in_admitted_40: `0.2995`

- nacional [adjective, score=0.361, mass=0.4338, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- junio [noun, score=0.346, mass=0.4175, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- visita [noun, score=0.342, mass=0.4127, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- gusto [noun, score=0.328, mass=0.397, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- competencia [noun, score=0.322, mass=0.3899, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- no [adverb, score=0.298, mass=0.3623, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- alemán [adjective, score=0.297, mass=0.3619, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- hielo [noun, score=0.287, mass=0.3501, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `41`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.2974`

- producción [noun, score=0.384, mass=0.4586, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- necesidad [noun, score=0.369, mass=0.442, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- pista [noun, score=0.366, mass=0.4044, delta=+82]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- barco [noun, score=0.334, mass=0.4031, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- ingreso [noun, score=0.333, mass=0.4028, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- competencia [noun, score=0.322, mass=0.3899, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- cultivo [noun, score=0.318, mass=0.3851, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- real [adjective, score=0.314, mass=0.3809, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

## Interest Scenario: `games`

### Profile Context

- selected_count: `800`
- selected_unique_count: `798`
- admitted_count: `40`
- selector_version: `profile_bootstrap_v3`
- selector_policy_version: `profile_bootstrap_policy_v2`
- active_signals: `interests, proficiency, challenge_preference`
- missing_signals: `none`
- explicit_topic_weight: `1`
- proficiency_estimate: `0`
- challenge_target: `0`

### Topic Support In Neutral Frontier

- candidate_count: `15`
- candidate_ratio: `0.0187`
- support_mass: `4.164815`
- support_mass_ratio: `0.013684`
- scarcity_multiplier_preview: `1.134`
- scarcity_readiness: `eligible`
- scarcity_readiness_reasons: `none`
- top_examples: `barrera, sacar, corazón, penal, descartar`

### Ranked Frontier Top 8

- topic_hits_in_top_8: `4`

- siglo [noun, score=0.455, mass=0.5353, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- corazón [noun, score=0.452, mass=0.4895, delta=+33]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- jefe [noun, score=0.437, mass=0.484, delta=+23]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- millón [noun, score=0.435, mass=0.5139, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- hora [noun, score=0.427, mass=0.5056, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- entrada [noun, score=0.419, mass=0.4597, delta=+46]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- música [noun, score=0.408, mass=0.4849, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- barrera [noun, score=0.407, mass=0.4203, delta=+159]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.

### Simulated Admitted Sets

#### Seed `7`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `2`
- avg_selection_mass_in_admitted_40: `0.3239`

- área [noun, score=0.377, mass=0.451, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- palo [noun, score=0.372, mass=0.4062, delta=+100]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- enfermedad [noun, score=0.366, mass=0.4387, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- mayor [adjective, score=0.364, mass=0.4369, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- influencia [noun, score=0.362, mass=0.4354, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- favor [noun, score=0.361, mass=0.4336, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- silencio [noun, score=0.357, mass=0.429, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- lanzador [noun, score=0.346, mass=0.3491, delta=+416]
  Boosted by topic_affinity, while remaining supported by coverage_gain.

#### Seed `19`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `2`
- avg_selection_mass_in_admitted_40: `0.2967`

- nacional [adjective, score=0.361, mass=0.4338, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- lanzador [noun, score=0.346, mass=0.3491, delta=+416]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- altura [noun, score=0.341, mass=0.411, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- batalla [noun, score=0.328, mass=0.3962, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- competencia [noun, score=0.322, mass=0.3899, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- cazar [verb, score=0.298, mass=0.294, delta=+597]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- no [adverb, score=0.298, mass=0.3623, delta=-10]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- rival [noun, score=0.289, mass=0.352, delta=-9]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `41`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `0`
- avg_selection_mass_in_admitted_40: `0.2982`

- producción [noun, score=0.384, mass=0.4586, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- necesidad [noun, score=0.369, mass=0.442, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- enfermedad [noun, score=0.366, mass=0.4387, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- ingreso [noun, score=0.333, mass=0.4028, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- demanda [noun, score=0.333, mass=0.4018, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- competencia [noun, score=0.322, mass=0.3899, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- cultivo [noun, score=0.318, mass=0.3851, delta=-7]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- real [adjective, score=0.314, mass=0.3809, delta=-8]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

## Interest Scenario: `finance`

### Profile Context

- selected_count: `800`
- selected_unique_count: `798`
- admitted_count: `40`
- selector_version: `profile_bootstrap_v3`
- selector_policy_version: `profile_bootstrap_policy_v2`
- active_signals: `interests, proficiency, challenge_preference`
- missing_signals: `none`
- explicit_topic_weight: `1`
- proficiency_estimate: `0`
- challenge_target: `0`

### Topic Support In Neutral Frontier

- candidate_count: `12`
- candidate_ratio: `0.015`
- support_mass: `3.63129`
- support_mass_ratio: `0.011931`
- scarcity_multiplier_preview: `1.205`
- scarcity_readiness: `eligible`
- scarcity_readiness_reasons: `none`
- top_examples: `capital, movimiento, fusión, par, boom`

### Ranked Frontier Top 8

- topic_hits_in_top_8: `4`

- movimiento [noun, score=0.537, mass=0.5648, delta=+5]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- capital [noun, score=0.534, mass=0.5524, delta=+13]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- luz [noun, score=0.469, mass=0.5198, delta=+4]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- siglo [noun, score=0.455, mass=0.5353, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- par [noun, score=0.435, mass=0.4693, delta=+50]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- millón [noun, score=0.435, mass=0.5139, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- hora [noun, score=0.427, mass=0.5056, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- música [noun, score=0.408, mass=0.4849, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

### Simulated Admitted Sets

#### Seed `7`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `0`
- avg_selection_mass_in_admitted_40: `0.3255`

- estilo [noun, score=0.374, mass=0.4478, delta=-2]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- necesidad [noun, score=0.369, mass=0.442, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- mayor [adjective, score=0.364, mass=0.4369, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- influencia [noun, score=0.362, mass=0.4354, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- cuestión [noun, score=0.362, mass=0.4344, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- silencio [noun, score=0.357, mass=0.429, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- reunión [noun, score=0.356, mass=0.4282, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- pequeño [adjective, score=0.345, mass=0.4157, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `19`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.2982`

- favor [noun, score=0.361, mass=0.4336, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- funcionario [noun, score=0.345, mass=0.4156, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- altura [noun, score=0.341, mass=0.411, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- tropa [noun, score=0.326, mass=0.3948, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- patio [noun, score=0.321, mass=0.3882, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- alemán [adjective, score=0.297, mass=0.3619, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- estadio [noun, score=0.297, mass=0.3612, delta=-5]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- taller [noun, score=0.286, mass=0.3487, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `41`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.2971`

- teatro [noun, score=0.381, mass=0.4562, delta=-3]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- pista [noun, score=0.366, mass=0.4044, delta=+85]
  Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain.
- mayor [adjective, score=0.364, mass=0.4369, delta=-4]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- demanda [noun, score=0.333, mass=0.4018, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- diputado [noun, score=0.332, mass=0.4012, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- competencia [noun, score=0.322, mass=0.3899, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- puesto [noun, score=0.317, mass=0.3845, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- iniciativa [noun, score=0.314, mass=0.3803, delta=-6]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

## Interest Scenario: `animals`

### Profile Context

- selected_count: `800`
- selected_unique_count: `798`
- admitted_count: `40`
- selector_version: `profile_bootstrap_v3`
- selector_policy_version: `profile_bootstrap_policy_v2`
- active_signals: `interests, proficiency, challenge_preference`
- missing_signals: `none`
- explicit_topic_weight: `1`
- proficiency_estimate: `0`
- challenge_target: `0`

### Topic Support In Neutral Frontier

- candidate_count: `1`
- candidate_ratio: `0.0013`
- support_mass: `0.234251`
- support_mass_ratio: `0.00077`
- scarcity_multiplier_preview: `1`
- scarcity_readiness: `insufficient_labeled_support`
- scarcity_readiness_reasons: `support_count_below_min, support_mass_below_min`
- top_examples: `coral`

### Ranked Frontier Top 8

- topic_hits_in_top_8: `0`

- siglo [noun, score=0.455, mass=0.5353, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- millón [noun, score=0.435, mass=0.5139, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- hora [noun, score=0.427, mass=0.5056, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- música [noun, score=0.408, mass=0.4849, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- principio [noun, score=0.405, mass=0.4824, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- movimiento [noun, score=0.398, mass=0.4746, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- luz [noun, score=0.397, mass=0.4729, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- mayoría [noun, score=0.395, mass=0.4708, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.

### Simulated Admitted Sets

#### Seed `7`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `0`
- avg_selection_mass_in_admitted_40: `0.3233`

- sol [noun, score=0.371, mass=0.4453, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- enfermedad [noun, score=0.366, mass=0.4387, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- nacional [adjective, score=0.361, mass=0.4338, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- político [adjective, score=0.357, mass=0.4297, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- reunión [noun, score=0.356, mass=0.4282, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- crisis [noun, score=0.351, mass=0.4229, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- salud [noun, score=0.35, mass=0.4215, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- cuento [noun, score=0.339, mass=0.4092, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.

#### Seed `19`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.2964`

- corazón [noun, score=0.353, mass=0.4251, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- cuento [noun, score=0.339, mass=0.4092, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- par [noun, score=0.334, mass=0.4034, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- patio [noun, score=0.321, mass=0.3882, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- coral [noun, score=0.315, mass=0.3343, delta=+317]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- depósito [noun, score=0.296, mass=0.3602, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- humor [noun, score=0.293, mass=0.357, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- oreja [noun, score=0.284, mass=0.3469, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

#### Seed `41`

- admitted_count: `40`
- topic_hit_count_in_admitted_40: `1`
- avg_selection_mass_in_admitted_40: `0.295`

- estilo [noun, score=0.374, mass=0.4478, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- jefe [noun, score=0.363, mass=0.436, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- nacional [adjective, score=0.361, mass=0.4338, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- gusto [noun, score=0.328, mass=0.397, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- batalla [noun, score=0.328, mass=0.3962, delta=0]
  Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit.
- coral [noun, score=0.315, mass=0.3343, delta=+317]
  Boosted by topic_affinity, while remaining supported by coverage_gain.
- gen [noun, score=0.314, mass=0.3809, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.
- deuda [noun, score=0.311, mass=0.3775, delta=-1]
  Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift.

## Notes

- Repeated words across seeds are expected when some frontier items still carry higher mass than the rest.
- Variation should be judged over the full admitted 40-word sets, not only the first few displayed rows.
- Sparse topics will remain weak until topic labeling and coverage improve upstream.
