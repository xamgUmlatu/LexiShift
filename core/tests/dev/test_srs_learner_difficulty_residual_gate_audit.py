from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_gate_audit_en_ja import (  # noqa: E402
    GateSpec,
    ResidualClusterSpec,
    _correction_probes,
    _gate_metrics,
    _oracle_cluster_correction_probes,
)


class TestSrsLearnerDifficultyResidualGateAudit(unittest.TestCase):
    def test_gate_metrics_reports_precision_recall_and_lift(self) -> None:
        rows = [
            _row(-0.30, {"risk": 1.0}),
            _row(-0.20, {"risk": 1.0}),
            _row(0.05, {"risk": 0.0}),
            _row(-0.40, {"risk": 0.0}),
        ]
        gate = GateSpec("risk_gate", "risk", minimums=(("risk", 0.75),))

        metrics = _gate_metrics(rows, gate, lambda row: float(row["residual"]) <= -0.25)

        self.assertEqual(metrics["selected_count"], 2)
        self.assertEqual(metrics["true_positive_count"], 1)
        self.assertEqual(metrics["false_positive_count"], 1)
        self.assertAlmostEqual(float(metrics["precision"]), 0.5)
        self.assertAlmostEqual(float(metrics["recall"]), 0.5)

    def test_correction_probe_fits_calibration_delta_and_evaluates_holdout(self) -> None:
        gate = GateSpec("risk_gate", "risk", minimums=(("risk", 0.75),))
        cluster = ResidualClusterSpec(
            "too_high",
            "too high",
            lambda row: float(row["residual"]) <= -0.25,
        )
        calibration = [
            _row(-0.30, {"risk": 1.0}),
            _row(-0.20, {"risk": 1.0}),
            _row(-0.25, {"risk": 1.0}),
            _row(-0.35, {"risk": 1.0}),
            _row(0.00, {"risk": 0.0}),
        ]
        holdout = [
            _row(-0.30, {"risk": 1.0}),
            _row(-0.10, {"risk": 1.0}),
            _row(0.00, {"risk": 0.0}),
        ]

        probes = _correction_probes(
            calibration,
            holdout,
            cluster_specs=(cluster,),
            gate_specs=(gate,),
        )
        probe = next(row for row in probes if row["gate_id"] == gate.gate_id)

        self.assertLess(float(probe["delta"]), 0.0)
        self.assertLess(float(probe["holdout_mae_after"]), float(probe["holdout_mae_before"]))

    def test_oracle_cluster_probe_shows_upper_bound_when_cluster_is_known(self) -> None:
        cluster = ResidualClusterSpec(
            "too_high",
            "too high",
            lambda row: float(row["residual"]) <= -0.25,
        )
        calibration = [
            _row(-0.30, {}),
            _row(-0.20, {}),
            _row(-0.25, {}),
            _row(-0.35, {}),
            _row(-0.28, {}),
        ]
        holdout = [
            _row(-0.30, {}),
            _row(-0.10, {}),
            _row(0.05, {}),
        ]

        probes = _oracle_cluster_correction_probes(
            calibration,
            holdout,
            cluster_specs=(cluster,),
        )
        probe = probes[0]

        self.assertEqual(probe["cluster_id"], "too_high")
        self.assertLess(float(probe["cluster_mae_after"]), float(probe["cluster_mae_before"]))


def _row(residual: float, signals: dict[str, float]) -> dict[str, object]:
    expected = 0.5
    observed = expected - residual
    return {
        "label": "x",
        "expected": expected,
        "observed": observed,
        "residual": residual,
        "absolute_error": abs(residual),
        "signals": signals,
    }


if __name__ == "__main__":
    unittest.main()
