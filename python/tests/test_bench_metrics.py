import importlib.util
import unittest
from pathlib import Path


def _load_metrics_module():
    metrics_path = Path(__file__).resolve().parents[2] / "examples" / "bench_metrics.py"
    spec = importlib.util.spec_from_file_location("bench_metrics", metrics_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load bench metrics module: {metrics_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBenchMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = _load_metrics_module()

    def test_wer_exact_match(self):
        self.assertEqual(self.metrics.wer("echo hello", "echo hello"), 0.0)

    def test_wer_missing_token(self):
        self.assertAlmostEqual(self.metrics.wer("echo hello", "echo"), 0.5)

    def test_cer_exact_match(self):
        self.assertEqual(self.metrics.cer("abc", "abc"), 0.0)

    def test_cer_missing_char(self):
        self.assertAlmostEqual(self.metrics.cer("abc", "ab"), 1 / 3)

    def test_ratio_exact_match(self):
        self.assertEqual(self.metrics.ratio("echo hello", "echo hello"), 1.0)

    def test_stats_values(self):
        avg, p50, p95, vmin, vmax = self.metrics.stats([1, 2, 3])
        self.assertEqual((avg, p50, p95, vmin, vmax), (2.0, 2.0, 3.0, 1.0, 3.0))

    def test_stats_empty(self):
        self.assertEqual(self.metrics.stats([]), (0.0, 0.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
