from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    PosMatchScoringConfig,
    RuleCandidate,
    RuleScoringConfig,
    build_pos_match_provider,
)
from lexishift_core.rulegen.pairs.en_de import (  # noqa: E402
    EnDeRulegenConfig,
    generate_en_de_results,
)


class TestRulegenPosMetadata(unittest.TestCase):
    def test_pos_match_provider_scores_exact_and_compatible_and_unknown(self) -> None:
        provider = build_pos_match_provider()

        exact = RuleCandidate(
            source_phrase="house",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={
                "pos": {
                    "source": {"canonical": "noun"},
                    "target": {"canonical": "noun"},
                }
            },
        )
        compatible = RuleCandidate(
            source_phrase="it",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={
                "pos": {
                    "source": {"canonical": "pronoun"},
                    "target": {"canonical": "noun"},
                }
            },
        )
        unknown = RuleCandidate(
            source_phrase="house",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={},
        )

        self.assertAlmostEqual(provider(exact), 1.0, places=6)
        self.assertAlmostEqual(provider(compatible), 0.5, places=6)
        self.assertAlmostEqual(provider(unknown), 0.0, places=6)

    def test_pos_match_provider_falls_back_to_dictionary_when_source_missing(self) -> None:
        provider = build_pos_match_provider()
        candidate = RuleCandidate(
            source_phrase="house",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={
                "pos": {
                    "dictionary": {"canonical": "noun"},
                    "target": {"canonical": "noun"},
                }
            },
        )
        self.assertAlmostEqual(provider(candidate), 1.0, places=6)

    def test_pos_match_provider_supports_legacy_dict_entry_flat_key(self) -> None:
        provider = build_pos_match_provider()
        candidate = RuleCandidate(
            source_phrase="house",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={
                "target_pos_canonical": "noun",
                "dict_entry_pos_canonical": "noun",
            },
        )
        self.assertAlmostEqual(provider(candidate), 1.0, places=6)

    def test_pos_match_provider_ignores_other_canonical(self) -> None:
        provider = build_pos_match_provider()
        candidate = RuleCandidate(
            source_phrase="house",
            replacement="Haus",
            language_pair="en-de",
            source_dict="freedict_de_en",
            metadata={
                "pos": {
                    "dictionary": {"canonical": "other"},
                    "target": {"canonical": "noun"},
                }
            },
        )
        self.assertAlmostEqual(provider(candidate), 0.0, places=6)

    def test_en_de_rulegen_includes_pos_metadata_and_pos_bonus(self) -> None:
        records = {"Haus": [FreedictGlossRecord(translation="house", pos_raw="noun")]}
        config_without_target_pos = EnDeRulegenConfig(
            translation_dict_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            include_variants=False,
        )
        config_with_target_pos = EnDeRulegenConfig(
            translation_dict_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            include_variants=False,
            word_packages_by_target={
                "Haus": {
                    "version": 1,
                    "language_tag": "de",
                    "surface": "Haus",
                    "source": {"provider": "freq-de-default"},
                    "pos_raw": "SUB",
                    "pos_canonical": "noun",
                }
            },
        )

        without_target_pos = generate_en_de_results(("Haus",), config=config_without_target_pos)
        with_target_pos = generate_en_de_results(("Haus",), config=config_with_target_pos)

        self.assertEqual(len(without_target_pos), 1)
        self.assertEqual(len(with_target_pos), 1)
        self.assertGreater(with_target_pos[0].confidence, without_target_pos[0].confidence)
        metadata = with_target_pos[0].rule.metadata
        self.assertIsNotNone(metadata)
        self.assertIsNotNone(metadata.pos)
        self.assertEqual(metadata.pos["source"]["canonical"], "noun")
        self.assertEqual(metadata.pos["target"]["canonical"], "noun")
        self.assertEqual(metadata.pos["dictionary"]["canonical"], "noun")

    def test_en_de_rulegen_can_disable_pos_scoring_signal(self) -> None:
        records = {"Haus": [FreedictGlossRecord(translation="house", pos_raw="noun")]}
        config_pos_enabled = EnDeRulegenConfig(
            translation_dict_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            include_variants=False,
            word_packages_by_target={
                "Haus": {
                    "version": 1,
                    "language_tag": "de",
                    "surface": "Haus",
                    "source": {"provider": "freq-de-default"},
                    "pos_raw": "SUB",
                    "pos_canonical": "noun",
                }
            },
        )
        config_pos_disabled = EnDeRulegenConfig(
            translation_dict_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            include_variants=False,
            word_packages_by_target={
                "Haus": {
                    "version": 1,
                    "language_tag": "de",
                    "surface": "Haus",
                    "source": {"provider": "freq-de-default"},
                    "pos_raw": "SUB",
                    "pos_canonical": "noun",
                }
            },
            scoring=RuleScoringConfig(
                pos_match=PosMatchScoringConfig(enabled=False),
            ),
        )

        enabled = generate_en_de_results(("Haus",), config=config_pos_enabled)
        disabled = generate_en_de_results(("Haus",), config=config_pos_disabled)

        self.assertEqual(len(enabled), 1)
        self.assertEqual(len(disabled), 1)
        self.assertGreater(enabled[0].confidence, disabled[0].confidence)


if __name__ == "__main__":
    unittest.main()
