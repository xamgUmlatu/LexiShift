from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig  # noqa: E402


class TestRulegenEnEsKaikkiPolicy(unittest.TestCase):
    def _generate(
        self,
        target: str,
        records: list[FreedictGlossRecord],
        *,
        reverse_records: dict[str, list[FreedictGlossRecord]] | None = None,
        max_definitions_per_target: int | None = 3,
        allow_multiword_glosses: bool = False,
    ):
        return generate_en_es_results(
            [target],
            config=EnEsRulegenConfig(
                freedict_es_en_path=Path("/tmp/unused"),
                gloss_records_by_target={target: records},
                reverse_gloss_records_by_source=reverse_records,
                source_dict_id="wiktionary_es_en",
                reverse_source_dict_id="wiktionary_en_es",
                dictionary_pos_source_profile="wiktionary",
                include_variants=False,
                max_definitions_per_target=max_definitions_per_target,
                allow_multiword_glosses=allow_multiword_glosses,
                reverse_check=ReverseCheckScoringConfig(enabled=True),
            ),
        )

    def test_kaikki_keeps_that_and_filters_shadowed_informal_interjection(self) -> None:
        results = self._generate(
            "ese",
            [
                FreedictGlossRecord(
                    translation="The name of the Latin script letter S/s.",
                    pos_raw="noun",
                ),
                FreedictGlossRecord(
                    translation="that",
                    pos_raw="det",
                    metadata={
                        "entry_tags": ["demonstrative"],
                        "sense_tags": ["masculine", "singular"],
                    },
                ),
                FreedictGlossRecord(
                    translation="hello",
                    pos_raw="intj",
                    metadata={
                        "sense_tags": ["Mexico", "informal"],
                        "sense_categories": ["Spanish informal terms"],
                    },
                ),
            ],
            reverse_records={
                "that": [FreedictGlossRecord(translation="ese", pos_raw="det")],
                "hello": [FreedictGlossRecord(translation="hola", pos_raw="intj")],
            },
        )

        self.assertEqual([result.candidate.source_phrase for result in results], ["that"])
        metadata = results[0].candidate.metadata
        self.assertEqual(metadata.get("dictionary_pos_canonical"), "determiner")
        self.assertTrue(bool(metadata.get("reverse_check_hit")))
        self.assertEqual(metadata.get("reverse_check_rank"), 0)

    def test_kaikki_function_word_phrase_survives_multiword_filter(self) -> None:
        results = self._generate(
            "según",
            [
                FreedictGlossRecord(
                    translation="according to",
                    pos_raw="prep",
                )
            ],
            reverse_records={
                "according to": [FreedictGlossRecord(translation="según", pos_raw="prep")]
            },
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].candidate.source_phrase, "according to")
        self.assertEqual(
            results[0].candidate.metadata.get("dictionary_pos_canonical"), "adposition"
        )
        self.assertTrue(bool(results[0].candidate.metadata.get("reverse_check_hit")))

    def test_kaikki_demotes_function_word_adverb_below_adposition_candidates(self) -> None:
        results = self._generate(
            "hasta",
            [
                FreedictGlossRecord(
                    translation="even",
                    pos_raw="adv",
                ),
                FreedictGlossRecord(
                    translation="until",
                    pos_raw="prep",
                ),
                FreedictGlossRecord(
                    translation="up to, to the point of, as much as",
                    pos_raw="prep",
                ),
            ],
            reverse_records={
                "until": [FreedictGlossRecord(translation="hasta", pos_raw="prep")],
                "up to": [FreedictGlossRecord(translation="hasta", pos_raw="prep")],
                "to the point of": [FreedictGlossRecord(translation="hasta", pos_raw="prep")],
                "as much as": [FreedictGlossRecord(translation="hasta", pos_raw="prep")],
                "even": [FreedictGlossRecord(translation="incluso", pos_raw="adv")],
            },
        )

        phrases = [result.candidate.source_phrase for result in results]
        self.assertEqual(phrases[0], "until")
        self.assertIn("up to", phrases)
        self.assertNotIn("even", phrases)

    def test_kaikki_recovers_verb_list_candidates_for_ocurrir(self) -> None:
        results = self._generate(
            "ocurrir",
            [
                FreedictGlossRecord(
                    translation="to happen, to occur",
                    pos_raw="verb",
                )
            ],
        )

        phrases = [result.candidate.source_phrase for result in results]
        self.assertEqual(phrases[:2], ["happen", "occur"])

    def test_kaikki_reverse_check_strips_english_infinitive_for_verbs(self) -> None:
        results = self._generate(
            "sacar",
            [
                FreedictGlossRecord(
                    translation="to withdraw, to take out",
                    pos_raw="verb",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                    },
                ),
                FreedictGlossRecord(
                    translation="to take off, remove",
                    pos_raw="verb",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 1,
                        "gloss_ord": 0,
                    },
                ),
            ],
            reverse_records={
                "withdraw": [FreedictGlossRecord(translation="sacar", pos_raw="verb")],
                "take out": [FreedictGlossRecord(translation="sacar", pos_raw="verb")],
                "remove": [FreedictGlossRecord(translation="sacar", pos_raw="verb")],
            },
            max_definitions_per_target=None,
            allow_multiword_glosses=True,
        )

        by_source = {
            result.candidate.source_phrase: result.candidate.metadata for result in results
        }
        self.assertTrue(bool(by_source["withdraw"].get("reverse_check_hit")))
        self.assertEqual(by_source["withdraw"].get("reverse_check_source_norm"), "withdraw")
        self.assertTrue(bool(by_source["take out"].get("reverse_check_hit")))
        self.assertEqual(by_source["take out"].get("reverse_check_source_norm"), "take out")
        self.assertTrue(bool(by_source["remove"].get("reverse_check_hit")))
        self.assertEqual(by_source["remove"].get("reverse_check_source_norm"), "remove")

    def test_kaikki_recovers_general_verb_candidates_before_domain_specific_presentar(self) -> None:
        results = self._generate(
            "presentar",
            [
                FreedictGlossRecord(
                    translation="to present, to submit",
                    pos_raw="verb",
                ),
                FreedictGlossRecord(
                    translation="to introduce (someone), to acquaint",
                    pos_raw="verb",
                ),
                FreedictGlossRecord(
                    translation="to file (a lawsuit), to lodge (an appeal, a complaint)",
                    pos_raw="verb",
                    metadata={"sense_topics": ["law"]},
                ),
                FreedictGlossRecord(
                    translation="to table (e.g., a resolution, an amendment)",
                    pos_raw="verb",
                    metadata={"sense_topics": ["government"]},
                ),
            ],
            max_definitions_per_target=None,
        )

        phrases = [result.candidate.source_phrase for result in results]
        self.assertGreaterEqual(len(phrases), 3)
        self.assertEqual(phrases[0], "present")
        self.assertIn("submit", phrases)
        self.assertIn("introduce", phrases)
        self.assertIn("table", phrases)
        self.assertLess(phrases.index("present"), phrases.index("table"))

    def test_kaikki_recovers_alias_and_semicolon_lexical_lists(self) -> None:
        plaza_results = self._generate(
            "plaza",
            [
                FreedictGlossRecord(
                    translation="plaza, town square",
                    pos_raw="noun",
                )
            ],
        )
        parte_results = self._generate(
            "parte",
            [
                FreedictGlossRecord(
                    translation="part; section; portion; share; piece; bit; cut; proportion",
                    pos_raw="noun",
                )
            ],
            max_definitions_per_target=None,
        )

        plaza_phrases = [result.candidate.source_phrase for result in plaza_results]
        parte_phrases = [result.candidate.source_phrase for result in parte_results]
        self.assertEqual(plaza_phrases, ["plaza"])
        self.assertEqual(parte_phrases[:5], ["part", "section", "portion", "share", "piece"])

    def test_kaikki_strips_inline_parenthetical_annotations_for_lexical_senses(self) -> None:
        results = self._generate(
            "cuadro",
            [
                FreedictGlossRecord(
                    translation="square (a polygon with four straight sides of equal length and four right angles)",
                    pos_raw="noun",
                ),
                FreedictGlossRecord(
                    translation="frame (a piece of photographic film containing an image)",
                    pos_raw="noun",
                ),
            ],
        )

        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["square", "frame"],
        )

    def test_kaikki_interleaves_sense_groups_for_split_lexical_outputs(self) -> None:
        results = self._generate(
            "cuadro",
            [
                FreedictGlossRecord(
                    translation="square, rectangle",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_topics": ["geometry"],
                    },
                ),
                FreedictGlossRecord(
                    translation="frame",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 1,
                        "gloss_ord": 0,
                    },
                ),
                FreedictGlossRecord(
                    translation="table, chart, graph",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 2,
                        "gloss_ord": 0,
                    },
                ),
            ],
            max_definitions_per_target=3,
        )

        self.assertEqual(
            [result.candidate.source_phrase for result in results[:5]],
            ["square", "frame", "table", "rectangle", "chart"],
        )


if __name__ == "__main__":
    unittest.main()
