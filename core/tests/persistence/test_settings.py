import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core import (  # noqa: E402
    AppSettings,
    ImportExportSettings,
    Profile,
    SynonymSourceSettings,
    load_app_settings,
    resolve_secondary_language_pack_paths,
    save_app_settings,
    settings_to_dict,
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
                managed_language_pack_ids=("freedict-en-es",),
                managed_frequency_pack_ids=("freq-en-coca",),
                embedding_pack_paths={"embed-xling-es": "/tmp/embed-xling-es/main.sqlite"},
                embedding_pair_pack_ids={"en-es": ("embed-xling-es",)},
                embedding_pair_paths={"en-es": ("/tmp/manual.vec.sqlite",)},
                embedding_pair_enabled={"en-es": True},
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
        self.assertEqual(tuple(loaded.synonyms.managed_language_pack_ids), ("freedict-en-es",))
        self.assertEqual(tuple(loaded.synonyms.managed_frequency_pack_ids), ("freq-en-coca",))
        self.assertEqual(
            list(loaded.synonyms.embedding_pair_pack_ids.get("en-es", [])),
            ["embed-xling-es"],
        )
        self.assertEqual(
            list(loaded.synonyms.embedding_pair_paths.get("en-es", [])),
            ["/tmp/manual.vec.sqlite"],
        )
        self.assertTrue(loaded.synonyms.embedding_pair_enabled.get("en-es"))

    def test_round_trip_resource_settings_keep_managed_and_manual_fields_separate(self) -> None:
        settings = AppSettings(
            synonyms=SynonymSourceSettings(
                wordnet_dir="/tmp/wordnet",
                moby_path="/tmp/moby.txt",
                managed_language_pack_ids=("freedict-en-es",),
                language_pack_paths={
                    "wordnet-en": "/tmp/wordnet",
                    "kaikki-en-es": "/tmp/kaikki.sqlite",
                },
                managed_frequency_pack_ids=("freq-en-coca",),
                frequency_pack_paths={"freq-manual": "/tmp/freq-manual.sqlite"},
                embedding_pack_paths={"embed-manual": "/tmp/embed-manual.sqlite"},
                embedding_pair_pack_ids={"en-es": ("embed-xling-es",)},
                embedding_pair_paths={"en-es": ("/tmp/manual.vec.sqlite",)},
                embedding_pair_enabled={"en-es": True},
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "settings.json")
            save_app_settings(settings, path)
            loaded = load_app_settings(path)

        synonyms = loaded.synonyms
        self.assertIsNotNone(synonyms)
        self.assertEqual(tuple(synonyms.managed_language_pack_ids), ("freedict-en-es",))
        self.assertEqual(
            synonyms.language_pack_paths,
            {
                "wordnet-en": "/tmp/wordnet",
                "kaikki-en-es": "/tmp/kaikki.sqlite",
            },
        )
        self.assertEqual(tuple(synonyms.managed_frequency_pack_ids), ("freq-en-coca",))
        self.assertEqual(
            synonyms.frequency_pack_paths,
            {"freq-manual": "/tmp/freq-manual.sqlite"},
        )
        self.assertEqual(
            synonyms.embedding_pack_paths,
            {"embed-manual": "/tmp/embed-manual.sqlite"},
        )
        self.assertEqual(
            list(synonyms.embedding_pair_pack_ids.get("en-es", [])),
            ["embed-xling-es"],
        )
        self.assertEqual(
            list(synonyms.embedding_pair_paths.get("en-es", [])),
            ["/tmp/manual.vec.sqlite"],
        )
        self.assertTrue(synonyms.embedding_pair_enabled.get("en-es"))

    def test_settings_to_dict_uses_explicit_resource_pack_keys(self) -> None:
        payload = settings_to_dict(
            AppSettings(
                synonyms=SynonymSourceSettings(
                    managed_language_pack_ids=("freedict-en-es",),
                    language_pack_paths={"kaikki-en-es": "/tmp/kaikki.sqlite"},
                    managed_frequency_pack_ids=("freq-en-coca",),
                    frequency_pack_paths={"freq-manual": "/tmp/freq-manual.sqlite"},
                    embedding_pack_paths={"embed-manual": "/tmp/embed-manual.sqlite"},
                    embedding_pair_pack_ids={"en-es": ("embed-xling-es",)},
                    embedding_pair_paths={"en-es": ("/tmp/manual.vec.sqlite",)},
                )
            )
        )

        synonyms = payload["synonyms"]
        self.assertIn("language_pack_paths", synonyms)
        self.assertIn("frequency_pack_paths", synonyms)
        self.assertIn("embedding_pack_paths", synonyms)
        self.assertNotIn("language_packs", synonyms)
        self.assertNotIn("frequency_packs", synonyms)
        self.assertNotIn("embedding_packs", synonyms)

    def test_resolve_secondary_language_pack_paths_prefers_binding_map_entries(self) -> None:
        resolved = resolve_secondary_language_pack_paths(
            SynonymSourceSettings(
                language_pack_paths={
                    "wordnet-en": "/tmp/wordnet-binding",
                    "moby-en": "/tmp/moby-binding.txt",
                },
                wordnet_dir="/tmp/wordnet-legacy",
                moby_path="/tmp/moby-legacy.txt",
            )
        )

        self.assertEqual(
            resolved,
            {
                "wordnet-en": "/tmp/wordnet-binding",
                "moby-en": "/tmp/moby-binding.txt",
            },
        )

    def test_resolve_secondary_language_pack_paths_falls_back_to_legacy_fields(self) -> None:
        resolved = resolve_secondary_language_pack_paths(
            SynonymSourceSettings(
                wordnet_dir="/tmp/wordnet-legacy",
                moby_path="/tmp/moby-legacy.txt",
            )
        )

        self.assertEqual(
            resolved,
            {
                "wordnet-en": "/tmp/wordnet-legacy",
                "moby-en": "/tmp/moby-legacy.txt",
            },
        )


if __name__ == "__main__":
    unittest.main()
