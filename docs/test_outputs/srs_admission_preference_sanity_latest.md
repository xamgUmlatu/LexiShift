# SRS Admission Preference Sanity

- status: PASS
- pass_count: 6
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
