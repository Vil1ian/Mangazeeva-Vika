import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import analyzer


class AnalyzerTests(unittest.TestCase):
    def test_parse_valid(self):
        row = analyzer.parse_line("2026-09-01T00:00:00Z | ERROR | api | E1 | bad\n")
        self.assertEqual(row["eventCode"], "E1")
        self.assertEqual(row["level"], "ERROR")

    def test_parse_bad_fields_and_empty(self):
        for line in ("broken", "2026-01-01T00:00:00Z | INFO | api | | message",
                     "2026-01-01T00:00:00Z | INFO | api | E1 | "):
            with self.assertRaises(ValueError):
                analyzer.parse_line(line)

    def test_parse_bad_date_level_and_timezone(self):
        for line in ("not-date | INFO | api | E1 | msg",
                     "2026-01-01T00:00:00Z | NOTICE | api | E1 | msg",
                     "2026-01-01T00:00:00 | INFO | api | E1 | msg",
                     "2026-01-01T00:00:00+02:00 | INFO | api | E1 | msg"):
            with self.assertRaises(ValueError):
                analyzer.parse_line(line)

    def args(self, path, **kwargs):
        values = dict(input=str(path), from_time=None, to_time=None, level=None,
                      source=None, top=5, format="json", output=None)
        values.update(kwargs)
        return SimpleNamespace(**values)

    def test_analyze_filters_boundaries_and_top(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "log.txt"
            p.write_text(
                "2026-01-01T00:00:00Z | ERROR | api | E1 | one\n"
                "2026-01-01T01:00:00Z | ERROR | api | E1 | two\n"
                "2026-01-01T02:00:00Z | INFO | worker | I1 | three\n"
                "bad row\n", encoding="utf-8")
            result = analyzer.analyze(self.args(
                p, from_time="2026-01-01T00:00:00Z",
                to_time="2026-01-01T02:00:00Z", level="ERROR", source="api", top=1))
            self.assertEqual(result["matched_events"], 2)
            self.assertEqual(result["invalid_lines"], 1)
            self.assertEqual(result["top_error_codes"], [{"code": "E1", "count": 2}])
            self.assertEqual(result["invalid_rows"][0]["line"], 4)

    def test_date_bounds_dd_mm_yy(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dates.log"
            p.write_text(
                "2026-09-02T23:59:59Z | INFO | api | I0 | before\n"
                "2026-09-03T00:00:00Z | INFO | api | I1 | start included\n"
                "2026-09-04T12:00:00Z | INFO | api | I2 | inside\n"
                "2026-09-05T00:00:00Z | INFO | api | I3 | end excluded\n",
                encoding="utf-8")
            result = analyzer.analyze(self.args(
                p, from_time="03.09.26", to_time="05.09.26"))
            self.assertEqual(result["matched_events"], 2)
            self.assertEqual(result["levels"], {"INFO": 2})

    def test_filter_and_aggregation_helpers(self):
        event = analyzer.parse_line(
            "2026-09-03T00:00:00Z | ERROR | api | E1 | bad")
        start = analyzer.parse_bound("03.09.26", "--from")
        end = analyzer.parse_bound("04.09.26", "--to")
        self.assertTrue(analyzer.matches_filters(event, start, end, "ERROR", "api"))
        self.assertFalse(analyzer.matches_filters(event, start, end, "INFO", "api"))
        counts = {"matched_events": 0, "levels": analyzer.Counter(),
                  "sources": analyzer.Counter(), "top_codes": analyzer.Counter()}
        analyzer.aggregate_event(event, counts)
        self.assertEqual(counts["matched_events"], 1)
        self.assertEqual(counts["top_codes"]["E1"], 1)

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty"
            p.write_text("", encoding="utf-8")
            result = analyzer.analyze(self.args(p))
            self.assertEqual(result["total_lines"], 0)
            self.assertEqual(result["matched_events"], 0)

    def test_only_corrupted_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.log"
            p.write_text("bad one\nnot-a-date | INFO | api | E1 | message\n", encoding="utf-8")
            result = analyzer.analyze(self.args(p))
            self.assertEqual(result["valid_lines"], 0)
            self.assertEqual(result["invalid_lines"], 2)
            self.assertEqual(result["matched_events"], 0)

    def test_large_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "large.log"
            row = "2026-01-01T00:00:00Z | INFO | api | I1 | ok\n"
            with p.open("w", encoding="utf-8") as f:
                for _ in range(5000):
                    f.write(row)
            result = analyzer.analyze(self.args(p))
            self.assertEqual(result["total_lines"], 5000)
            self.assertEqual(result["matched_events"], 5000)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                analyzer.analyze(self.args(Path(tmp) / "missing"))

    def test_invalid_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "log"
            p.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                analyzer.analyze(self.args(p, from_time="yesterday"))
            with self.assertRaises(ValueError):
                analyzer.analyze(self.args(p, from_time="2026-02-01T00:00:00Z",
                                           to_time="2026-01-01T00:00:00Z"))

    def test_write_json_and_csv(self):
        result = {"total_lines": 1, "valid_lines": 1, "invalid_lines": 0,
                  "matched_events": 1, "levels": {"INFO": 1}, "sources": {"api": 1},
                  "top_error_codes": [], "invalid_rows": []}
        with tempfile.TemporaryDirectory() as tmp:
            j, c = Path(tmp)/"a.json", Path(tmp)/"a.csv"
            analyzer.write_result(result, "json", str(j))
            analyzer.write_result(result, "csv", str(c))
            self.assertEqual(json.loads(j.read_text())["matched_events"], 1)
            self.assertIn("metric,name,count", c.read_text())

    def test_main_success_and_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "log"
            p.write_text("2026-01-01T00:00:00Z | INFO | api | I1 | hi\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(analyzer.main(["--input", str(p)]), 0)
            self.assertIn('"matched_events": 1', out.getvalue())
            with self.assertRaises(SystemExit) as caught:
                analyzer.main(["--input", str(p), "--top", "-1"])
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(analyzer.main(["--input", str(p/"missing")]), 1)


if __name__ == "__main__":
    unittest.main()
