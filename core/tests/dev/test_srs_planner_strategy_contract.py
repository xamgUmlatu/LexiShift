from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.engine import (  # noqa: E402
    SrsRebalanceJobConfig,
    SetPlanningJobConfig,
    apply_srs_rebalance,
    plan_srs_rebalance,
    plan_srs_set,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsStore,
    save_srs_inventory,
    save_srs_store,
)


def _create_frequency_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                lform TEXT,
                wtype TEXT,
                sublemma TEXT,
                sense_topics TEXT,
                topics TEXT,
                topic TEXT,
                profile_topics TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO frequency (
                lemma,
                core_rank,
                pmw,
                pos,
                lform,
                wtype,
                sublemma,
                sense_topics,
                topics,
                topic,
                profile_topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("alpha", 1.0, 100.0, "n", None, None, None, None, None, None, None),
        )
        conn.commit()
    finally:
        conn.close()
    return path


class TestSrsPlannerStrategyContract(unittest.TestCase):
    def test_helper_plan_keeps_profile_bootstrap_as_frequency_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            payload = plan_srs_set(
                paths,
                config=SetPlanningJobConfig(
                    pair="en-en",
                    strategy="profile_bootstrap",
                    objective="bootstrap",
                    profile_context={"interests": ["animals"]},
                ),
            )

            self.assertEqual(payload["pair"], "en-en")
            self.assertEqual(payload["plan"]["strategy_requested"], "profile_bootstrap")
            self.assertEqual(payload["plan"]["strategy_effective"], "frequency_bootstrap")
            self.assertEqual(payload["plan"]["execution_mode"], "frequency_bootstrap")
            self.assertTrue(payload["plan"]["can_execute"])

    def test_helper_rebalance_keeps_profile_growth_as_effective_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            source_db = _create_frequency_db(root / "freq.sqlite")

            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-en:alpha",
                            lemma="alpha",
                            language_pair="en-en",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-en": SrsPairInventory(active_item_ids=("en-en:alpha",)),
                    }
                ),
                paths.srs_inventory_path_for("default"),
            )

            with patch(
                "lexishift_core.helper.engine.build_seed_candidates",
                return_value=[],
            ):
                preview = plan_srs_rebalance(
                    paths,
                    config=SrsRebalanceJobConfig(
                        pair="en-en",
                        set_source_db=source_db,
                        max_active_items=1,
                        profile_context={"interests": ["animals"]},
                    ),
                )
                applied = apply_srs_rebalance(
                    paths,
                    config=SrsRebalanceJobConfig(
                        pair="en-en",
                        set_source_db=source_db,
                        max_active_items=1,
                        profile_context={"interests": ["animals"]},
                    ),
                )

            self.assertEqual(preview["pair"], "en-en")
            self.assertEqual(preview["plan"]["strategy_requested"], "profile_growth")
            self.assertEqual(preview["plan"]["strategy_effective"], "profile_growth")
            self.assertEqual(preview["plan"]["objective"], "rebalance")
            self.assertEqual(preview["plan"]["execution_mode"], "rebalance_preview")
            self.assertTrue(preview["plan"]["can_execute"])

            self.assertEqual(applied["pair"], "en-en")
            self.assertEqual(applied["plan"]["strategy_requested"], "profile_growth")
            self.assertEqual(applied["plan"]["strategy_effective"], "profile_growth")
            self.assertEqual(applied["plan"]["execution_mode"], "rebalance_apply")
            self.assertTrue(applied["plan"]["can_execute"])
            self.assertFalse(applied["applied"])


if __name__ == "__main__":
    unittest.main()
