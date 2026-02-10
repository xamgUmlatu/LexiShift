import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import (
    InflectionSettings,
    InflectionSpec,
    LearningSettings,
    MeaningRule,
    RuleMetadata,
    VocabRule,
    VocabSettings,
)
from lexishift_core.persistence.storage import VocabDataset, load_vocab_dataset, save_vocab_dataset


class StorageTests(unittest.TestCase):
    def test_round_trip_dataset(self) -> None:
        rules = [
            VocabRule(
                source_phrase="twilight",
                replacement="gloaming",
                tags=("poetic",),
                metadata=RuleMetadata(
                    label="time",
                    description="Preferred poetic substitute.",
                    examples=("The twilight deepened.",),
                    notes="Used in atmosphere-heavy scenes.",
                    script_forms={"kanji": "猫", "kana": "ねこ", "romaji": "neko"},
                ),
            )
        ]
        meaning_rules = [
            MeaningRule(
                source_phrases=("stunned into silence", "awed into silence"),
                replacement="overawed",
                metadata=RuleMetadata(label="emotion"),
            )
        ]
        settings = VocabSettings(
            inflections=InflectionSettings(spec=InflectionSpec()),
            learning=LearningSettings(enabled=True, show_original=True, show_original_mode="inline"),
        )
        dataset = VocabDataset(
            rules=tuple(rules),
            meaning_rules=tuple(meaning_rules),
            synonyms={"dawn": "twilight"},
            settings=settings,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "vocab.json")
            save_vocab_dataset(dataset, path)
            loaded = load_vocab_dataset(path)

        self.assertEqual(loaded.rules[0].metadata.label, "time")
        self.assertEqual(loaded.rules[0].metadata.script_forms["kana"], "ねこ")
        self.assertEqual(loaded.meaning_rules[0].source_phrases[0], "stunned into silence")
        self.assertEqual(loaded.synonyms["dawn"], "twilight")
        self.assertTrue(loaded.settings.learning.enabled)
        self.assertEqual(loaded.settings.learning.show_original_mode, "inline")


if __name__ == "__main__":
    unittest.main()
