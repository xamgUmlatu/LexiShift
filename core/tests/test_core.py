import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import Replacer, VocabPool


class ReplacerTests(unittest.TestCase):
    def test_phrase_replacement(self) -> None:
        pool = VocabPool.from_mapping(
            {
                "twilight": "gloaming",
                "stunned into silence": "overawed",
            }
        )
        replacer = Replacer(pool)
        text = "At twilight, she was stunned into silence."
        result = replacer.replace_text(text)
        self.assertEqual(result, "At gloaming, she was overawed.")


if __name__ == "__main__":
    unittest.main()
