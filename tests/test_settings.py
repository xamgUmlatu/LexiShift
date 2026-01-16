import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from vocab_replacer import (  # noqa: E402
    AppSettings,
    ImportExportSettings,
    Profile,
    SynonymSourceSettings,
    load_app_settings,
    save_app_settings,
)


class SettingsTests(unittest.TestCase):
    def test_round_trip_app_settings(self) -> None:
        settings = AppSettings(
            profiles=(
                Profile(
                    profile_id="default",
                    name="Default",
                    dataset_path="vocab.json",
                    description="Primary pool",
                ),
            ),
            active_profile_id="default",
            import_export=ImportExportSettings(
                allow_code_export=True,
                default_export_format="code",
            ),
            synonyms=SynonymSourceSettings(
                wordnet_dir="/tmp/wordnet",
                moby_path="/tmp/moby.txt",
                max_synonyms=50,
                include_phrases=True,
            ),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "settings.json")
            save_app_settings(settings, path)
            loaded = load_app_settings(path)

        self.assertEqual(loaded.active_profile_id, "default")
        self.assertEqual(loaded.profiles[0].dataset_path, "vocab.json")
        self.assertTrue(loaded.import_export.allow_code_export)
        self.assertEqual(loaded.synonyms.max_synonyms, 50)


if __name__ == "__main__":
    unittest.main()
