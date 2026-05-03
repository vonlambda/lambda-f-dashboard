"""
smoke_test.py — Tier 3 Phase C CI smoke test.

Runs in GitHub Actions on every push to main. Catches breakage in the
production code path BEFORE the next 07:00 daily run on the local
Windows scheduler would push broken signals to the dashboard.

Tests are intentionally narrow: import sanity + signal-pipeline contract
checks on synthetic data. We don't fetch live yfinance data here (slow,
flaky in CI). Heavier numerical regression tests can be added later
with committed parquet fixtures if needed.

Run locally:
    cd lambda-f-engine
    python -m pytest tests/  -v
or:
    python tests/smoke_test.py
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

# Make the engine modules importable when run from repo root or tests/
ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)


def _make_synthetic_prices(n_days=700, n_assets=6, seed=42):
    """Generate plausible synthetic price series for n_assets over n_days.

    Date count is derived from the requested business-day range to avoid
    weekend/calendar mismatches between local and CI runners.
    """
    dates = pd.date_range(end=pd.Timestamp.today().normalize(),
                          periods=n_days, freq='B')
    actual = len(dates)  # may be slightly less than n_days near weekends
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, 0.02, size=(actual, n_assets))
    # Inject a regime shift in the second half
    half = actual // 2
    returns[half:, :] += rng.normal(0, 0.01, size=(actual - half, n_assets))
    prices_arr = 100 * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(prices_arr, index=dates,
                        columns=[f'TKR{i}' for i in range(n_assets)])


class TestImports(unittest.TestCase):
    """Guard against import-time breakage from refactors."""

    def test_lambda_factors_imports(self):
        import lambda_factors  # noqa: F401
        from lambda_factors import compute_lambda_method_c, PARAMS  # noqa: F401

    def test_reflexivity_calculator_imports(self):
        from reflexivity_calculator import (  # noqa: F401
            get_reflexivity, get_quadrant, get_macro_stress_score,
        )

    def test_outcome_tracker_imports(self):
        from outcome_tracker import (  # noqa: F401
            track_new_calls, update_pending_outcomes,
            compute_detection_stats, compute_systemic_score,
            render_recent_calls_table, REPRESENTATIVE_TICKER,
            TP_DRAWDOWN_THRESHOLD, TP_WINDOW_DAYS,
        )

    def test_quadrant_matrix_imports(self):
        from quadrant_matrix import (  # noqa: F401
            generate_quadrant_matrix, push_quadrant_matrix_to_github,
        )


class TestLambdaPipeline(unittest.TestCase):
    """Method C produces sane output on synthetic data."""

    @classmethod
    def setUpClass(cls):
        from lambda_factors import compute_lambda_method_c
        cls.prices = _make_synthetic_prices()
        cls.compute = staticmethod(compute_lambda_method_c)

    def test_returns_three_values(self):
        result = TestLambdaPipeline.compute(self.prices)
        self.assertEqual(len(result), 3)

    def test_returns_floats_and_series(self):
        current, pct, series = TestLambdaPipeline.compute(self.prices)
        self.assertIsInstance(current, float)
        self.assertIsInstance(pct, float)
        self.assertIsInstance(series, pd.Series)

    def test_percentile_in_range(self):
        _, pct, _ = TestLambdaPipeline.compute(self.prices)
        self.assertGreaterEqual(pct, 0.0)
        self.assertLessEqual(pct, 100.0)

    def test_series_no_nan_at_end(self):
        _, _, series = TestLambdaPipeline.compute(self.prices)
        self.assertFalse(np.isnan(series.iloc[-1]))

    def test_handles_short_data(self):
        short = self.prices.iloc[:50]
        current, pct, series = TestLambdaPipeline.compute(short)
        self.assertIsNone(current)
        self.assertIsNone(pct)
        self.assertIsNone(series)


class TestQuadrantClassifier(unittest.TestCase):
    """get_quadrant maps (Λ%, R) into the right cell of the 2×2 grid."""

    def test_q1_low_low(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(50, 30), 'Q1')

    def test_q2_low_high(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(50, 80), 'Q2')

    def test_q3_high_low(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(80, 30), 'Q3')

    def test_q4_high_high(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(80, 80), 'Q4')

    def test_q3_star_when_reflex_unknown(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(80, None), 'Q3*')

    def test_q1_star_when_reflex_unknown(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(50, None), 'Q1*')

    def test_boundary_p75(self):
        from reflexivity_calculator import get_quadrant
        self.assertIn(get_quadrant(75, 30), ('Q3', 'Q3*'))

    def test_boundary_r60(self):
        from reflexivity_calculator import get_quadrant
        self.assertEqual(get_quadrant(50, 60), 'Q2')


class TestSystemicScore(unittest.TestCase):
    """compute_systemic_score produces correct weighted sum."""

    def test_all_q1(self):
        from outcome_tracker import compute_systemic_score
        results = [{'quadrant': 'Q1'} for _ in range(10)]
        s = compute_systemic_score(results)
        self.assertEqual(s['score'], 0)
        self.assertEqual(s['max_score'], 30)
        self.assertEqual(s['label'], 'CALM')

    def test_all_q4(self):
        from outcome_tracker import compute_systemic_score
        results = [{'quadrant': 'Q4'} for _ in range(10)]
        s = compute_systemic_score(results)
        self.assertEqual(s['score'], 30)
        self.assertEqual(s['label'], 'ELEVATED SYSTEMIC RISK')

    def test_mixed(self):
        from outcome_tracker import compute_systemic_score
        # 2 Q4 + 4 Q3 + 0 Q2 + 4 Q1 = 6 + 8 + 0 + 0 = 14
        results = (
            [{'quadrant': 'Q4'}] * 2
            + [{'quadrant': 'Q3'}] * 4
            + [{'quadrant': 'Q1'}] * 4
        )
        s = compute_systemic_score(results)
        self.assertEqual(s['score'], 14)
        # 14/30 = 47% — WATCH band (>=33%)
        self.assertEqual(s['label'], 'WATCH')

    def test_q_star_treated_as_unstarred(self):
        from outcome_tracker import compute_systemic_score
        # Q3* should weight the same as Q3
        results = [{'quadrant': 'Q3*'}] * 5
        s = compute_systemic_score(results)
        self.assertEqual(s['score'], 10)


class TestOutcomeTracker(unittest.TestCase):
    """outcome_tracker classifier honors the pre-registered 20% / 90d rule."""

    def test_tp_threshold_constant(self):
        from outcome_tracker import TP_DRAWDOWN_THRESHOLD, TP_WINDOW_DAYS
        self.assertEqual(TP_DRAWDOWN_THRESHOLD, 0.20)
        self.assertEqual(TP_WINDOW_DAYS, 90)

    def test_classify_above_threshold(self):
        from outcome_tracker import _classify
        self.assertEqual(_classify(0.21), 'true_positive')
        self.assertEqual(_classify(0.20), 'true_positive')

    def test_classify_below_threshold(self):
        from outcome_tracker import _classify
        self.assertEqual(_classify(0.19), 'false_positive')
        self.assertEqual(_classify(0.0), 'false_positive')

    def test_classify_pending(self):
        from outcome_tracker import _classify
        self.assertEqual(_classify(None), 'pending')


class TestDetectionStats(unittest.TestCase):
    def test_empty(self):
        from outcome_tracker import compute_detection_stats
        s = compute_detection_stats(rows=[])
        self.assertEqual(s['total_resolved'], 0)
        self.assertEqual(s['true_positives'], 0)
        self.assertEqual(s['pending'], 0)
        self.assertIsNone(s['detection_rate'])

    def test_mixed(self):
        from outcome_tracker import compute_detection_stats
        rows = [
            {'status': 'true_positive', 'market': 'Bonds'},
            {'status': 'false_positive', 'market': 'Gold'},
            {'status': 'pending', 'market': 'Crypto (BTC)'},
        ]
        s = compute_detection_stats(rows=rows)
        self.assertEqual(s['total_resolved'], 2)
        self.assertEqual(s['true_positives'], 1)
        self.assertEqual(s['pending'], 1)
        self.assertAlmostEqual(s['detection_rate'], 50.0)


if __name__ == '__main__':
    # Allow running directly without pytest
    unittest.main(verbosity=2)
