from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import lexishift_core.rulegen.pairs.en_es_support as en_es_support  # noqa: E402
from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.pairs.en_es_gloss_processing import (  # noqa: E402
    build_reverse_lookup,
    collect_sanitized_gloss_records,
    normalize_reverse_token_with_pos,
)


class TestRulegenEnEsGlossProcessing(unittest.TestCase):
    def test_support_module_reexports_gloss_processing_helpers(self) -> None:
        self.assertIs(
            en_es_support.collect_sanitized_gloss_records, collect_sanitized_gloss_records
        )
        self.assertIs(en_es_support.build_reverse_lookup, build_reverse_lookup)
        self.assertIs(
            en_es_support.normalize_reverse_token_with_pos,
            normalize_reverse_token_with_pos,
        )

    def test_collect_sanitized_gloss_records_splits_verbal_comma_lists(self) -> None:
        records = [
            FreedictGlossRecord(
                translation="to run, sprint",
                pos_raw="verb",
                metadata={"sense_ord": 2},
            )
        ]

        cleaned = collect_sanitized_gloss_records(records)

        self.assertEqual([record.translation for record in cleaned], ["to run", "to sprint"])
        self.assertEqual([record.pos_raw for record in cleaned], ["verb", "verb"])
        self.assertEqual(cleaned[0].metadata["gloss_fragment_source_text"], "to run")
        self.assertEqual(cleaned[1].metadata["gloss_fragment_source_text"], "sprint")
        self.assertEqual(cleaned[1].metadata["gloss_fragment_operations"], ("prepend_to_prefix",))
        self.assertEqual(cleaned[1].metadata["sense_ord"], 2)

    def test_collect_sanitized_gloss_records_upgrades_duplicate_blank_pos(self) -> None:
        cleaned = collect_sanitized_gloss_records(
            [
                FreedictGlossRecord(translation="house", pos_raw="", metadata={"source": "first"}),
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"source": "second"},
                ),
            ]
        )

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0].translation, "house")
        self.assertEqual(cleaned[0].pos_raw, "noun")
        self.assertEqual(cleaned[0].metadata["source"], "first")

    def test_normalize_reverse_token_with_pos_only_strips_verbal_infinitives(self) -> None:
        self.assertEqual(normalize_reverse_token_with_pos("to run", pos_raw="verb"), "run")
        self.assertEqual(normalize_reverse_token_with_pos("to house", pos_raw="noun"), "to house")
        self.assertEqual(
            normalize_reverse_token_with_pos("  TO Sprint ", pos_raw="auxiliary"), "sprint"
        )

    def test_build_reverse_lookup_normalizes_sources_and_deduplicates_targets(self) -> None:
        lookup = build_reverse_lookup(
            {
                "to run": [
                    FreedictGlossRecord(translation="correr", pos_raw="verb"),
                    FreedictGlossRecord(translation="correr", pos_raw="verb"),
                    FreedictGlossRecord(translation="ejecutar", pos_raw="verb"),
                ]
            }
        )

        self.assertEqual(lookup, {"run": ("correr", "ejecutar")})

    def test_definition_bucket_key_splits_legacy_freedict_gloss_rows(self) -> None:
        record = FreedictGlossRecord(
            translation="alley",
            pos_raw="noun",
            metadata={"entry_ord": 9652, "gloss_ord": 1},
        )
        auxiliary_record = FreedictGlossRecord(
            translation="alley",
            pos_raw="noun",
            metadata={"entry_ord": 9652, "sense_ord": 0, "gloss_ord": 1},
        )

        self.assertEqual(
            en_es_support.build_definition_bucket_key(record, fallback_index=0),
            "sense:9652:gloss:1",
        )
        self.assertEqual(
            en_es_support.build_definition_bucket_key(auxiliary_record, fallback_index=0),
            "sense:9652:0",
        )


if __name__ == "__main__":
    unittest.main()
