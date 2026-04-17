import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import (  # noqa: E402
    AppSettings,
    ImportExportSettings,
    Profile,
    SynonymSourceSettings,
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

    def test_export_import_app_settings_code_preserves_resource_pack_split(self) -> None:
        settings = AppSettings(
            profiles=(Profile(profile_id="default", name="Default", dataset_path="vocab.json"),),
            active_profile_id="default",
            synonyms=SynonymSourceSettings(
                managed_language_pack_ids=("freedict-en-es",),
                language_pack_paths={"kaikki-en-es": "/tmp/kaikki.sqlite"},
                managed_frequency_pack_ids=("freq-en-coca",),
                frequency_pack_paths={"freq-manual": "/tmp/freq-manual.sqlite"},
                embedding_pack_paths={"embed-manual": "/tmp/embed-manual.sqlite"},
                embedding_pair_pack_ids={"en-es": ("embed-xling-es",)},
                embedding_pair_paths={"en-es": ("/tmp/manual.vec.sqlite",)},
                embedding_pair_enabled={"en-es": True},
            ),
        )

        payload = export_app_settings_code(settings)
        loaded = import_app_settings_code(payload)

        self.assertEqual(tuple(loaded.synonyms.managed_language_pack_ids), ("freedict-en-es",))
        self.assertEqual(
            loaded.synonyms.language_pack_paths,
            {"kaikki-en-es": "/tmp/kaikki.sqlite"},
        )
        self.assertEqual(tuple(loaded.synonyms.managed_frequency_pack_ids), ("freq-en-coca",))
        self.assertEqual(
            loaded.synonyms.frequency_pack_paths,
            {"freq-manual": "/tmp/freq-manual.sqlite"},
        )
        self.assertEqual(
            loaded.synonyms.embedding_pack_paths,
            {"embed-manual": "/tmp/embed-manual.sqlite"},
        )
        self.assertEqual(
            list(loaded.synonyms.embedding_pair_pack_ids.get("en-es", [])),
            ["embed-xling-es"],
        )
        self.assertEqual(
            list(loaded.synonyms.embedding_pair_paths.get("en-es", [])),
            ["/tmp/manual.vec.sqlite"],
        )
        self.assertTrue(loaded.synonyms.embedding_pair_enabled.get("en-es"))


if __name__ == "__main__":
    unittest.main()
