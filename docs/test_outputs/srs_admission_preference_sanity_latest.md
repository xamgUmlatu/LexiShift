# SRS Admission Preference Sanity

- status: PASS
- pass_count: 10
- warn_count: 0
- fail_count: 0
- pair: en-en

## Findings
- PASS `NEUTRAL_ORDER_STABLE`: Neutral profile preserved the neutral seed order. (money, home, case, funny, livestream)
- PASS `EXPLICIT_INTEREST_LIFTS_TOPIC_MATCHES`: Explicit `animals` interest promoted animal-related candidates. (gain=4.333333)
- PASS `EXPLICIT_PREVIEW_EXPLAINS_TOPIC_BIAS`: Preview explanation surfaced topic-affinity-driven reranking. (Boosted by topic_affinity, while remaining supported by coverage_gain.)
- PASS `IMPLICIT_TOPIC_BIAS_LIFTS_MATCHES`: Derived implicit topic weights promoted media-related candidates. (gain=2.5)
- PASS `IMPLICIT_SIGNAL_SOURCE_IS_DERIVED`: Implicit scenario routed through derived topic-bias normalization. (empirical_trends.topic_bias)
- PASS `LIVE_METADATA_COVERAGE_AUDIT_AVAILABLE`: Synthetic sanity passes the scoring seam, and live frequency-source topic coverage is now tracked by the dedicated frontier audit.
- PASS `PREFERENCE_STRENGTH_TOP_N_MONOTONIC`: Increasing topic strength did not reduce the number of focus-topic candidates in the top-N preview. ([0, 2, 3, 4])
- PASS `PREFERENCE_STRENGTH_MASS_MONOTONIC`: Increasing topic strength did not reduce focus-topic first-draw selection mass. ([0.282282, 0.403289, 0.419019, 0.448115])
- PASS `PROFICIENCY_SHIFTS_TOP_N_DIFFICULTY`: Higher proficiency shifted the top-N preview toward harder words. (0.412)
- PASS `HIGH_PROFICIENCY_TOPIC_PRESSURE_VISIBLE`: A strong topic preference still increased focus-topic presence for high-proficiency users. (2)

## Scenario previews

### neutral
- description: No profile signals. Ranking should stay near neutral frequency order.
- active_signals: none
- signal_sources: {}
- top_lemmas: money, home, case, funny, livestream
- average_focus_rank: None
- money [delta=+0, score=0.44]: Kept in neutral frequency order because profile signals were effectively neutral.
- home [delta=+0, score=0.418]: Kept in neutral frequency order because profile signals were effectively neutral.
- case [delta=+0, score=0.396]: Kept in neutral frequency order because profile signals were effectively neutral.

### explicit_animals
- description: Explicit `animals` interest should promote animal-related vocabulary.
- active_signals: interests
- signal_sources: {"interests": "interests"}
- top_lemmas: dog, elephant, money, home, fur
- average_focus_rank: 2.666667
- dog [delta=+5, score=0.5025]: Boosted by topic_affinity, while remaining supported by coverage_gain.
- elephant [delta=+5, score=0.4805]: Boosted by topic_affinity, while remaining supported by coverage_gain.
- money [delta=-2, score=0.44]: Still supported by coverage_gain, but moved down because other items received stronger overall profile lift.

### implicit_streaming_comedy
- description: Derived implicit topic weights should promote media-related vocabulary without introducing a new planner contract.
- active_signals: interests
- signal_sources: {"interests": "empirical_trends.topic_bias"}
- top_lemmas: funny, money, livestream, home, case
- average_focus_rank: 2.0
- funny [delta=+3, score=0.4605]: Boosted by topic_affinity, while remaining supported by coverage_gain.
- money [delta=-1, score=0.44]: Still supported by coverage_gain, but moved down because other items received stronger overall profile lift.
- livestream [delta=+2, score=0.431353]: Boosted by topic_affinity, while remaining supported by coverage_gain.

## Preference Matrix
- top_n: 5
- focus_lemmas: dog, elephant, falcon, reptile
- topic_strength_top_n_counts: [0, 2, 3, 4]
- topic_strength_first_draw_probabilities: [0.282282, 0.403289, 0.419019, 0.448115]
- proficiency_average_top_difficulty_delta: 0.412
- high_proficiency_topic_top_n_delta: 2

### matrix/neutral
- description: No profile signals.
- top_lemmas: money, home, food, travel, music
- focus_top_n_count: 0
- focus_average_rank: 7.75
- focus_first_draw_probability: 0.282282
- average_top_difficulty: 0.24

### matrix/animals_light
- description: Light animals preference at mid proficiency.
- top_lemmas: dog, travel, music, elephant, food
- focus_top_n_count: 2
- focus_average_rank: 4.5
- focus_first_draw_probability: 0.403289
- average_top_difficulty: 0.364

### matrix/animals_medium
- description: Medium animals preference at mid proficiency.
- top_lemmas: dog, elephant, travel, music, falcon
- focus_top_n_count: 3
- focus_average_rank: 3.75
- focus_first_draw_probability: 0.419019
- average_top_difficulty: 0.44

### matrix/animals_strong
- description: Strong animals preference at mid proficiency.
- top_lemmas: dog, elephant, falcon, travel, reptile
- focus_top_n_count: 4
- focus_average_rank: 2.75
- focus_first_draw_probability: 0.448115
- average_top_difficulty: 0.492

### matrix/proficiency_low
- description: Low proficiency without topic preference.
- top_lemmas: money, home, food, travel, music
- focus_top_n_count: 0
- focus_average_rank: 7.75
- focus_first_draw_probability: 0.216106
- average_top_difficulty: 0.24

### matrix/proficiency_mid
- description: Mid proficiency without topic preference.
- top_lemmas: travel, music, dog, elephant, food
- focus_top_n_count: 2
- focus_average_rank: 5.25
- focus_first_draw_probability: 0.386522
- average_top_difficulty: 0.364

### matrix/proficiency_high
- description: High proficiency without topic preference.
- top_lemmas: falcon, thesis, reptile, hypothesis, algorithm
- focus_top_n_count: 2
- focus_average_rank: 4.25
- focus_first_draw_probability: 0.491561
- average_top_difficulty: 0.652

### matrix/animals_high_proficiency
- description: Strong animals preference at high proficiency.
- top_lemmas: elephant, falcon, reptile, dog, thesis
- focus_top_n_count: 4
- focus_average_rank: 2.5
- focus_first_draw_probability: 0.666211
- average_top_difficulty: 0.548
