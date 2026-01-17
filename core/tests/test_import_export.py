import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import (  # noqa: E402
    AppSettings,
    ImportExportSettings,
    Profile,
    VocabDataset,
    VocabRule,
    export_app_settings_code,
    export_dataset_code,
    import_app_settings_code,
    import_dataset_code,
)


class ImportExportTests(unittest.TestCase):
    def test_export_import_code(self) -> None:
        dataset = VocabDataset(rules=(VocabRule(source_phrase="twilight", replacement="gloaming"),))
        payload = export_dataset_code(dataset)
        loaded = import_dataset_code(payload)
        self.assertEqual(loaded.rules[0].replacement, "gloaming")

    def test_export_import_app_settings_code(self) -> None:
        settings = AppSettings(
            profiles=(Profile(profile_id="default", name="Default", dataset_path="vocab.json"),),
            active_profile_id="default",
            import_export=ImportExportSettings(default_export_format="code"),
        )
        payload = export_app_settings_code(settings)
        loaded = import_app_settings_code(payload)
        self.assertEqual(loaded.active_profile_id, "default")


if __name__ == "__main__":
    unittest.main()
