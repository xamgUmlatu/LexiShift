from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_TAXONOMY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_CURRENT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde" / "main.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = (
    DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en" / "main.sqlite"
)
DEFAULT_DIFFICULTY_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_es_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_family_depth_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_topic_family_depth_audit_en_es_latest.md"
)
DEFAULT_PRIOR_EXPANSION_AUDIT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_expansion_audit_en_es_spalex_10k_latest.json"
)
DEFAULT_TOP_N = 10000
DIFFICULTY_BANDS: tuple[tuple[str, float, float], ...] = (
    ("0.00-0.20", 0.0, 0.2),
    ("0.20-0.40", 0.2, 0.4),
    ("0.40-0.60", 0.4, 0.6),
    ("0.60-0.80", 0.6, 0.8),
    ("0.80-1.00", 0.8, 1.0),
)
REGISTER_REVIEW_LABELS: dict[str, dict[str, tuple[str, ...]]] = {
    "casual_slang_register": {
        "sense_tags": ("colloquial", "slang", "informal", "vulgar"),
        "sense_categories": (
            "spanish_slang",
            "spanish_colloquialisms",
            "spanish_informal_terms",
            "spanish_vulgarities",
        ),
        "entry_categories": (
            "spanish_slang",
            "spanish_colloquialisms",
            "spanish_informal_terms",
            "spanish_vulgarities",
        ),
    },
    "formal_professional_register": {
        "sense_tags": ("formal", "literary"),
        "sense_categories": ("spanish_formal_terms", "spanish_literary_terms"),
        "entry_categories": ("spanish_formal_terms", "spanish_literary_terms"),
    },
}
