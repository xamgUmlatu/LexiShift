from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_curve_search_en_ja import (  # noqa: E402
    FeatureSetSpec,
    GatedFeatureSpec,
    _calibration_fold_ids,
    _cross_validate_candidate,
    _feature_matrix,
    _fit_candidate,
    _predict,
    _sample_weights,
    _target_values,
    _transform,
)


class TestSrsLearnerDifficultyCurveSearch(unittest.TestCase):
    def test_curve_transforms_are_bounded_and_monotonic(self) -> None:
        values = np.array([0.0, 0.25, 0.5, 0.75, 1.0], dtype=np.float32)

        self.assertEqual(_transform(values, "identity").tolist(), values.tolist())
        self.assertAlmostEqual(float(_transform(values, "sqrt")[1]), 0.5)
        self.assertAlmostEqual(float(_transform(values, "square")[3]), 0.5625)
        self.assertEqual(
            [round(float(value), 2) for value in _transform(values, "tail50")],
            [0.0, 0.0, 0.0, 0.5, 1.0],
        )
        self.assertEqual(
            [round(float(value), 2) for value in _transform(values, "tail75")],
            [0.0, 0.0, 0.0, 0.0, 1.0],
        )
        self.assertEqual(
            [round(float(value), 2) for value in _transform(values, "tail20")],
            [0.0, 0.06, 0.38, 0.69, 1.0],
        )
        self.assertEqual(
            [round(float(value), 2) for value in _transform(values, "head35")],
            [1.0, 0.29, 0.0, 0.0, 0.0],
        )
        self.assertGreater(float(_transform(values, "bump50")[2]), 0.99)
        self.assertLess(float(_transform(values, "bump50")[0]), 0.01)
        self.assertLess(float(_transform(values, "bump50")[4]), 0.01)

    def test_feature_matrix_includes_missing_and_interactions(self) -> None:
        spec = FeatureSetSpec(
            "test",
            signals=("frequency", "risk"),
            transforms=("identity", "square"),
            include_missing=True,
            interactions=(("frequency", "risk"),),
        )
        matrix, names = _feature_matrix(
            spec,
            signal_arrays={
                "frequency": np.array([0.2, 0.8], dtype=np.float32),
                "risk": np.array([0.5, 0.0], dtype=np.float32),
            },
            present_arrays={
                "frequency": np.array([True, True]),
                "risk": np.array([True, False]),
            },
        )

        self.assertEqual(
            names,
            (
                "frequency:identity",
                "frequency:square",
                "risk:identity",
                "risk:square",
                "risk:missing",
                "frequency*risk",
            ),
        )
        self.assertEqual(matrix.shape, (2, 6))
        self.assertAlmostEqual(float(matrix[1, 4]), 1.0)
        self.assertAlmostEqual(float(matrix[0, 5]), 0.1)

    def test_feature_matrix_includes_soft_gated_features(self) -> None:
        spec = FeatureSetSpec(
            "test",
            signals=("frequency",),
            transforms=("identity",),
            gated_features=(
                GatedFeatureSpec(
                    "gate",
                    signals=("risk",),
                    transforms=("identity", "square"),
                ),
            ),
        )
        matrix, names = _feature_matrix(
            spec,
            signal_arrays={
                "frequency": np.array([0.2, 0.8], dtype=np.float32),
                "gate": np.array([0.0, 0.5], dtype=np.float32),
                "risk": np.array([0.5, 0.8], dtype=np.float32),
            },
            present_arrays={},
        )

        self.assertEqual(
            names,
            (
                "frequency:identity",
                "gate|risk:identity",
                "gate|risk:square",
            ),
        )
        self.assertEqual(matrix.shape, (2, 3))
        self.assertAlmostEqual(float(matrix[0, 1]), 0.0)
        self.assertAlmostEqual(float(matrix[1, 1]), 0.4)
        self.assertAlmostEqual(float(matrix[1, 2]), 0.32)

    def test_target_transforms_and_weight_modes(self) -> None:
        expected = np.array([0.1, 0.5, 0.9, np.nan], dtype=np.float32)

        identity = _target_values(expected, transform="identity")
        self.assertTrue(np.isnan(identity[3]))
        self.assertLess(float(_target_values(expected, transform="logit")[0]), 0.0)
        self.assertGreater(float(_target_values(expected, transform="logit")[2]), 0.0)

        weights = _sample_weights(expected, mode="beginner_tail")
        self.assertEqual([float(value) for value in weights[:3]], [2.0, 1.0, 2.0])

    def test_ridge_candidate_can_fit_simple_increasing_signal(self) -> None:
        matrix = np.array([[0.0], [0.5], [1.0], [0.25]], dtype=np.float32)
        calibration_context = {
            "component_indices": np.array([0, 1, 2], dtype=np.int64),
            "expected_values": np.array([0.1, 0.5, 0.9], dtype=np.float32),
        }
        y = _target_values(calibration_context["expected_values"], transform="identity")
        weights = _sample_weights(calibration_context["expected_values"], mode="uniform")

        candidate = _fit_candidate(
            matrix,
            feature_names=("risk:identity",),
            calibration_context=calibration_context,
            feature_set="test",
            alpha=0.01,
            target_transform="identity",
            sample_weight_mode="uniform",
            y=y,
            sample_weights=weights,
        )
        predictions = _predict(matrix, candidate)

        self.assertLess(float(predictions[0]), float(predictions[1]))
        self.assertLess(float(predictions[1]), float(predictions[2]))

    def test_cross_validation_reports_fold_stability(self) -> None:
        matrix = np.array([[0.0], [0.25], [0.5], [0.75], [1.0]], dtype=np.float32)
        calibration_context = {
            "component_indices": np.array([0, 1, 2, 3, 4], dtype=np.int64),
            "expected_values": np.array([0.05, 0.2, 0.5, 0.75, 0.95], dtype=np.float32),
            "expected_bands": ["", "", "", "", ""],
            "labels": ["a", "b", "c", "d", "e"],
        }
        y = _target_values(calibration_context["expected_values"], transform="identity")
        weights = _sample_weights(calibration_context["expected_values"], mode="uniform")
        folds = _calibration_fold_ids(calibration_context, fold_count=2)

        self.assertEqual(set(int(value) for value in folds), {0, 1})

        result = _cross_validate_candidate(
            matrix,
            feature_names=("risk:identity",),
            calibration_context=calibration_context,
            target_positions=np.linspace(0.0, 1.0, 5, dtype=np.float32),
            feature_set="test",
            alpha=0.01,
            target_transform="identity",
            sample_weight_mode="uniform",
            y=y,
            sample_weights=weights,
            fold_ids=folds,
        )

        self.assertEqual(result["fold_count"], 2)
        self.assertIsNotNone(result["balanced_mean"])
        self.assertEqual(len(result["folds"]), 2)


if __name__ == "__main__":
    unittest.main()
