import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "benchmark", Path(__file__).resolve().parents[1] / "scripts" / "benchmark.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def score(expected, findings, approved=False):
    return benchmark.score_run(expected, {"approved": approved, "findings": findings})


class BenchmarkTests(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(
            benchmark.extract_json('ignore```json\n{"approved": true, "findings": []}\n```tail'),
            {"approved": True, "findings": []})
        self.assertIsNone(benchmark.extract_json("no object here"))
        self.assertIsNone(benchmark.extract_json("prefix {not json} suffix"))

    def test_score_run_findings_false_positives_and_forbidden_hits(self):
        clean = {"expected_verdict": True, "findings": [],
                 "forbidden": [{"r": "Risk", "matcher": "sql"}]}
        clean_score = score(clean, [{"r": "Risk", "severity": "major", "file": "user_sql.py",
                                     "line": 7, "summary": "Possible SQL injection"}])
        self.assertEqual(
            {k: clean_score[k] for k in ("recall", "verdict_ok", "false_positive",
                                         "forbidden_hit", "is_approve_case", "parsed", "approved")},
            {"recall": None, "verdict_ok": False, "false_positive": True,
             "forbidden_hit": True, "is_approve_case": True, "parsed": True, "approved": False})

        seeded = {"expected_verdict": False, "forbidden": [], "findings": [
            {"r": "Reliability", "severity": "major", "matcher": "test"},
            {"r": "Resilience", "severity": "major", "matcher": "timeout"}]}
        seeded_score = score(seeded, [{"r": "Reliability", "severity": "major",
                                       "file": "billing.py", "line": 10,
                                       "summary": "New billing logic has no test coverage"}])
        self.assertEqual(seeded_score["recall"], 0.5)
        self.assertTrue(seeded_score["verdict_ok"])
        self.assertFalse(seeded_score["false_positive"])
        self.assertFalse(seeded_score["is_approve_case"])

    def test_aggregate_computes_suite_level_stats_per_run(self):
        fixtures = [
            {"name": "bug", "expected_verdict": False, "forbidden": [], "findings": [
                {"r": "Reliability", "matcher": "test"}, {"r": "Resilience", "matcher": "timeout"}]},
            {"name": "clean", "expected_verdict": True, "findings": [], "forbidden": []},
            {"name": "trap", "expected_verdict": True, "findings": [],
             "forbidden": [{"r": "Risk", "matcher": "sql"}]},
        ]
        s = lambda recall, ok, fp=False, forbidden=False, parsed=True, approved=False: {
            "recall": recall, "verdict_ok": ok, "false_positive": fp, "forbidden_hit": forbidden,
            "is_approve_case": recall is None, "parsed": parsed, "approved": approved}
        per_run = [
            ("bug", 0, s(0.5, True)), ("clean", 0, s(None, True, approved=True)),
            ("trap", 0, s(None, True, approved=True)), ("bug", 1, s(1.0, True)),
            ("clean", 1, s(None, False, fp=True)),
            ("trap", 1, s(None, False, fp=True, forbidden=True, parsed=False)),
        ]
        summary = benchmark.aggregate(per_run, fixtures, runs=2)

        self.assertAlmostEqual(summary["recall"]["mean"], 0.75)
        self.assertAlmostEqual(summary["recall"]["std"], math.sqrt(0.125))
        self.assertAlmostEqual(summary["verdict_accuracy"]["mean"], (1.0 + 1.0 / 3.0) / 2.0)
        self.assertAlmostEqual(summary["false_positive_rate"]["mean"], 0.5)
        self.assertAlmostEqual(summary["false_positive_rate"]["std"], math.sqrt(0.5))
        self.assertEqual(summary["false_positive_rate"]["n_cases"], 2)
        self.assertAlmostEqual(summary["forbidden_hit_rate"]["mean"], 0.5)
        self.assertAlmostEqual(summary["forbidden_hit_rate"]["std"], math.sqrt(0.5))
        self.assertEqual(summary["forbidden_hit_rate"]["n_cases"], 1)
        self.assertAlmostEqual(summary["parse_rate"]["mean"], (1.0 + 2.0 / 3.0) / 2.0)

    def test_render_md_includes_metrics_and_modal_verdicts(self):
        bench = {"config": {"model": "test-model", "runs": 2, "fixtures": 2,
                             "conditions": ["with-skill"]},
                 "summary": {"with-skill": {
                     "recall": {"mean": 1.0, "std": 0.0},
                     "verdict_accuracy": {"mean": 0.75, "std": 0.35},
                     "verdict_consistency": {"mean": 1.0},
                     "false_positive_rate": {"mean": 0.0, "std": 0.0},
                     "forbidden_hit_rate": {"mean": None, "std": None},
                     "parse_rate": {"mean": 1.0}}},
                 "per_fixture": {"with-skill": [
                     {"fixture": "clean", "run": 0, "approved": True},
                     {"fixture": "clean", "run": 1, "approved": True},
                     {"fixture": "bug", "run": 0, "approved": False},
                     {"fixture": "bug", "run": 1, "approved": False}]}}
        md = benchmark.render_md(bench, [{"name": "clean", "expected_verdict": True},
                                         {"name": "bug", "expected_verdict": False}])
        for text in ("# Code Review 4R — Benchmark", "| Recall (seeded findings) ↑ | 100% ± 0 |",
                     "| clean | approve | approve |", "| bug | reject | reject |"):
            self.assertIn(text, md)


if __name__ == "__main__":
    unittest.main()
