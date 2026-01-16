import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from vocab_replacer import (  # noqa: E402
    FORM_PLURAL,
    FORM_POSSESSIVE,
    InflectionGenerator,
    InflectionSpec,
    expand_phrase,
)


class InflectionTests(unittest.TestCase):
    def test_expand_phrase_last_word(self) -> None:
        spec = InflectionSpec(forms=frozenset({FORM_PLURAL, FORM_POSSESSIVE}))
        forms = expand_phrase("twilight sky", spec=spec)
        self.assertIn("twilight skies", forms)
        self.assertIn("twilight sky's", forms)

    def test_expand_single_word(self) -> None:
        generator = InflectionGenerator()
        spec = InflectionSpec(forms=frozenset({FORM_PLURAL, FORM_POSSESSIVE}))
        forms = expand_phrase("twilight", generator=generator, spec=spec)
        self.assertIn("twilights", forms)
        self.assertIn("twilight's", forms)


if __name__ == "__main__":
    unittest.main()
