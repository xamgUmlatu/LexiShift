from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_beta_preflight_en_es import build_report, render_markdown  # noqa: E402


class SrsBetaPreflightEnEsTests(unittest.TestCase):
    def test_preflight_passes_automated_checks_and_surfaces_manual_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            options_html = root / "options.html"
            locale_root = root / "_locales"
            taxonomy_audit = root / "taxonomy_audit.json"
            srs_quality = root / "srs_quality.json"
            profile_journey = root / "profile_journey.json"
            installed_journey = root / "installed_journey.json"
            _write_locales(locale_root)
            taxonomy.write_text(json.dumps(_taxonomy()), encoding="utf-8")
            options_html.write_text(
                """
                <button data-srs-topic-interest="animals"></button>
                <button data-srs-topic-interest="food_cooking"></button>
                """,
                encoding="utf-8",
            )
            taxonomy_audit.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "summary": {"issues": []},
                        "findings": [
                            {
                                "level": "PASS",
                                "code": "family_mvp_picker_visibility_valid",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            _write_quality(srs_quality, status="PASS")
            _write_quality(profile_journey, status="PASS", warn_count=1)
            _write_quality(installed_journey, status="PASS")

            report = build_report(
                taxonomy_path=taxonomy,
                options_html_path=options_html,
                locale_root=locale_root,
                taxonomy_audit_path=taxonomy_audit,
                srs_quality_path=srs_quality,
                profile_journey_path=profile_journey,
                installed_journey_path=installed_journey,
                generated_at="2026-05-27T00:00:00+00:00",
            )

        self.assertEqual(report["summary"]["status"], "REVIEW")
        findings = {row["code"]: row for row in report["findings"]}
        self.assertEqual(findings["strict_mvp_picker_matches_taxonomy"]["level"], "PASS")
        self.assertEqual(findings["hidden_topics_absent_from_picker"]["level"], "PASS")
        self.assertEqual(findings["en_es_profile_journey_latest_review"]["level"], "WARN")
        self.assertEqual(report["summary"]["manual_counts"], {"PENDING": 5})
        markdown = render_markdown(report)
        self.assertIn("Manual Beta Signoff", markdown)
        self.assertIn("plants_nature and travel_places_transport stay hidden", markdown)

    def test_preflight_fails_when_options_picker_exposes_beta_topic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            taxonomy = root / "taxonomy.json"
            options_html = root / "options.html"
            locale_root = root / "_locales"
            _write_locales(locale_root)
            taxonomy.write_text(json.dumps(_taxonomy()), encoding="utf-8")
            options_html.write_text(
                """
                <button data-srs-topic-interest="animals"></button>
                <button data-srs-topic-interest="plants_nature"></button>
                """,
                encoding="utf-8",
            )

            report = build_report(
                taxonomy_path=taxonomy,
                options_html_path=options_html,
                locale_root=locale_root,
                taxonomy_audit_path=root / "missing.json",
                srs_quality_path=root / "missing-quality.json",
                profile_journey_path=root / "missing-profile.json",
                installed_journey_path=root / "missing-installed.json",
                generated_at="2026-05-27T00:00:00+00:00",
            )

        self.assertEqual(report["summary"]["status"], "FAIL")
        findings = {row["code"]: row for row in report["findings"]}
        self.assertEqual(findings["strict_mvp_picker_mismatch"]["level"], "FAIL")
        self.assertEqual(findings["hidden_topics_absent_from_picker"]["level"], "FAIL")


def _taxonomy() -> dict[str, object]:
    return {
        "families": [
            {
                "id": "animals",
                "mvp_picker_visibility": "strict_mvp_visible",
            },
            {
                "id": "food_cooking",
                "mvp_picker_visibility": "strict_mvp_visible",
            },
            {
                "id": "plants_nature",
                "mvp_picker_visibility": "future_beta_hidden",
            },
        ]
    }


def _write_locales(root: Path) -> None:
    for locale in ("en", "de", "ja", "zh"):
        locale_dir = root / locale
        locale_dir.mkdir(parents=True)
        (locale_dir / "messages.json").write_text(
            json.dumps(
                {
                    "topic_srs_animals": {"message": "Animals"},
                    "topic_srs_food_cooking": {"message": "Food"},
                }
            ),
            encoding="utf-8",
        )


def _write_quality(path: Path, *, status: str, warn_count: int = 0) -> None:
    path.write_text(
        json.dumps(
            {
                "summary": {
                    "status": status,
                    "pass_count": 2,
                    "warn_count": warn_count,
                    "fail_count": 0,
                    "should_fail": False,
                },
                "findings": [
                    {
                        "level": "WARN",
                        "code": "SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED",
                    }
                ]
                if warn_count
                else [],
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
