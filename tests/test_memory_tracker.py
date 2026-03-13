"""
Tests for AutoQA Memory Tracker.

Tests scanning, result tracking, coverage gap detection,
persistence, and reporting.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.autoqa.memory_tracker import AutoQAMemoryTracker, CoverageGap, MemoryEntry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create source modules
    src_dir = tmp_path / "src" / "autoqa"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").touch()
    (src_dir / "parser.py").write_text("# parser module\n")
    (src_dir / "runner.py").write_text("# runner module\n")
    (src_dir / "reporter.py").write_text("# reporter module\n")

    src_utils = tmp_path / "src" / "utils"
    src_utils.mkdir(parents=True)
    (src_utils / "__init__.py").touch()
    (src_utils / "logger.py").write_text("# logger module\n")

    # Create test files
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").touch()
    (test_dir / "test_parser.py").write_text("def test_parse(): assert True\n")
    (test_dir / "test_runner.py").write_text("def test_run(): assert True\n")

    # Create reports directory
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "json").mkdir()

    return tmp_path


@pytest.fixture
def tracker(tmp_project):
    """Create a tracker with the temporary project."""
    return AutoQAMemoryTracker(
        project_root=str(tmp_project),
        memory_path="reports/autoqa_memory.json",
        test_dir="tests",
        source_dirs=["src"],
    )


# ---------------------------------------------------------------------------
# MemoryEntry
# ---------------------------------------------------------------------------


class TestMemoryEntry:
    """Tests for MemoryEntry serialization."""

    def test_to_dict(self):
        entry = MemoryEntry(
            test_id="tests/test_foo.py::test_bar",
            file_path="tests/test_foo.py",
            status="passed",
            last_run="2026-01-01T00:00:00",
            duration=1.23,
        )
        d = entry.to_dict()
        assert d["test_id"] == "tests/test_foo.py::test_bar"
        assert d["status"] == "passed"
        assert d["duration"] == 1.23
        assert d["history"] == []

    def test_from_dict_roundtrip(self):
        original = MemoryEntry(
            test_id="tests/test_x.py::test_y",
            file_path="tests/test_x.py",
            status="failed",
            last_run="2026-03-01T12:00:00",
            error_message="AssertionError",
            duration=0.5,
            history=[{"status": "passed", "timestamp": "2026-02-01T00:00:00"}],
        )
        d = original.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.test_id == original.test_id
        assert restored.status == original.status
        assert restored.error_message == original.error_message
        assert len(restored.history) == 1

    def test_from_dict_defaults(self):
        entry = MemoryEntry.from_dict(
            {
                "test_id": "t::x",
                "file_path": "t.py",
            }
        )
        assert entry.status == "unknown"
        assert entry.last_run is None
        assert entry.history == []


# ---------------------------------------------------------------------------
# CoverageGap
# ---------------------------------------------------------------------------


class TestCoverageGap:
    """Tests for CoverageGap serialization."""

    def test_to_dict(self):
        gap = CoverageGap(
            source_path="src/autoqa/parser.py",
            module_name="parser",
            has_test=True,
            test_file="tests/test_parser.py",
            reason="covered",
        )
        d = gap.to_dict()
        assert d["has_test"] is True
        assert d["reason"] == "covered"

    def test_from_dict_roundtrip(self):
        original = CoverageGap(
            source_path="src/utils/helper.py",
            module_name="helper",
            has_test=False,
            reason="no_test_file",
        )
        d = original.to_dict()
        restored = CoverageGap.from_dict(d)
        assert restored.module_name == "helper"
        assert restored.has_test is False


# ---------------------------------------------------------------------------
# AutoQAMemoryTracker – scanning
# ---------------------------------------------------------------------------


class TestMemoryTrackerScanning:
    """Tests for file scanning functionality."""

    def test_scan_test_files(self, tracker):
        files = tracker.scan_test_files()
        assert len(files) == 2
        assert any("test_parser.py" in f for f in files)
        assert any("test_runner.py" in f for f in files)

    def test_scan_source_modules(self, tracker):
        modules = tracker.scan_source_modules()
        # Should find parser.py, runner.py, reporter.py, logger.py
        # but NOT __init__.py files
        names = [Path(m).stem for m in modules]
        assert "parser" in names
        assert "runner" in names
        assert "reporter" in names
        assert "logger" in names
        assert "__init__" not in names

    def test_scan_nonexistent_test_dir(self, tmp_path):
        t = AutoQAMemoryTracker(
            project_root=str(tmp_path),
            test_dir="nonexistent",
        )
        files = t.scan_test_files()
        assert files == []


# ---------------------------------------------------------------------------
# Coverage gap detection
# ---------------------------------------------------------------------------


class TestCoverageGapDetection:
    """Tests for coverage gap identification."""

    def test_identifies_covered_modules(self, tracker):
        gaps = tracker.identify_coverage_gaps()
        covered = [g for g in gaps if g.has_test]
        covered_names = {g.module_name for g in covered}
        assert "parser" in covered_names
        assert "runner" in covered_names

    def test_identifies_uncovered_modules(self, tracker):
        gaps = tracker.identify_coverage_gaps()
        uncovered = [g for g in gaps if not g.has_test]
        uncovered_names = {g.module_name for g in uncovered}
        assert "reporter" in uncovered_names
        assert "logger" in uncovered_names

    def test_get_missing_tests(self, tracker):
        tracker.identify_coverage_gaps()
        missing = tracker.get_missing_tests()
        missing_names = {g.module_name for g in missing}
        assert "reporter" in missing_names
        assert "parser" not in missing_names


# ---------------------------------------------------------------------------
# Persistence (save/load)
# ---------------------------------------------------------------------------


class TestMemoryPersistence:
    """Tests for save and load functionality."""

    def test_save_creates_file(self, tracker):
        tracker.identify_coverage_gaps()
        tracker.save()
        assert tracker.memory_path.exists()

    def test_save_load_roundtrip(self, tracker):
        # Add some test entries
        tracker.test_entries["t::a"] = MemoryEntry(
            test_id="t::a",
            file_path="t.py",
            status="passed",
            last_run="2026-01-01T00:00:00",
        )
        tracker.test_entries["t::b"] = MemoryEntry(
            test_id="t::b",
            file_path="t.py",
            status="failed",
            error_message="boom",
        )
        tracker.identify_coverage_gaps()
        tracker.save()

        # Create a new tracker and load
        tracker2 = AutoQAMemoryTracker(
            project_root=str(tracker.project_root),
            memory_path="reports/autoqa_memory.json",
            test_dir="tests",
            source_dirs=["src"],
        )
        loaded = tracker2.load()
        assert loaded is True
        assert len(tracker2.test_entries) == 2
        assert tracker2.test_entries["t::a"].status == "passed"
        assert tracker2.test_entries["t::b"].status == "failed"
        assert len(tracker2.coverage_gaps) > 0

    def test_load_nonexistent_returns_false(self, tracker):
        assert tracker.load() is False

    def test_load_invalid_json(self, tracker):
        tracker.memory_path.parent.mkdir(parents=True, exist_ok=True)
        tracker.memory_path.write_text("not valid json{{{")
        assert tracker.load() is False

    def test_save_creates_parent_dirs(self, tmp_path):
        t = AutoQAMemoryTracker(
            project_root=str(tmp_path),
            memory_path="deep/nested/dir/memory.json",
        )
        t.save()
        assert (tmp_path / "deep" / "nested" / "dir" / "memory.json").exists()


# ---------------------------------------------------------------------------
# JSON report parsing
# ---------------------------------------------------------------------------


class TestJsonReportParsing:
    """Tests for pytest JSON report parsing."""

    def test_parse_passing_tests(self, tracker, tmp_project):
        report = {
            "tests": [
                {
                    "nodeid": "tests/test_parser.py::test_parse",
                    "outcome": "passed",
                    "duration": 0.01,
                },
            ]
        }
        report_path = tmp_project / "reports" / "json" / "test_report.json"
        report_path.write_text(json.dumps(report))

        tracker._parse_json_report(report_path)
        assert "tests/test_parser.py::test_parse" in tracker.test_entries
        entry = tracker.test_entries["tests/test_parser.py::test_parse"]
        assert entry.status == "passed"

    def test_parse_failing_tests(self, tracker, tmp_project):
        report = {
            "tests": [
                {
                    "nodeid": "tests/test_x.py::test_fail",
                    "outcome": "failed",
                    "duration": 0.5,
                    "call": {
                        "crash": {"message": "AssertionError: expected 1 got 2"},
                    },
                },
            ]
        }
        report_path = tmp_project / "reports" / "json" / "test_report.json"
        report_path.write_text(json.dumps(report))

        tracker._parse_json_report(report_path)
        entry = tracker.test_entries["tests/test_x.py::test_fail"]
        assert entry.status == "failed"
        assert "AssertionError" in entry.error_message

    def test_parse_error_in_setup(self, tracker, tmp_project):
        report = {
            "tests": [
                {
                    "nodeid": "tests/test_y.py::test_err",
                    "outcome": "error",
                    "duration": 0.0,
                    "setup": {
                        "outcome": "error",
                        "crash": {"message": "ImportError: missing module"},
                    },
                },
            ]
        }
        report_path = tmp_project / "reports" / "json" / "test_report.json"
        report_path.write_text(json.dumps(report))

        tracker._parse_json_report(report_path)
        entry = tracker.test_entries["tests/test_y.py::test_err"]
        assert entry.status == "error"
        assert "ImportError" in entry.error_message

    def test_history_accumulates(self, tracker, tmp_project):
        report_path = tmp_project / "reports" / "json" / "test_report.json"

        # First run: passing
        report = {
            "tests": [
                {"nodeid": "t::a", "outcome": "passed", "duration": 0.1},
            ]
        }
        report_path.write_text(json.dumps(report))
        tracker._parse_json_report(report_path)
        assert tracker.test_entries["t::a"].status == "passed"
        assert len(tracker.test_entries["t::a"].history) == 0

        # Second run: failing
        report["tests"][0]["outcome"] = "failed"
        report_path.write_text(json.dumps(report))
        tracker._parse_json_report(report_path)
        assert tracker.test_entries["t::a"].status == "failed"
        assert len(tracker.test_entries["t::a"].history) == 1
        assert tracker.test_entries["t::a"].history[0]["status"] == "passed"

    def test_history_bounded_to_10(self, tracker, tmp_project):
        report_path = tmp_project / "reports" / "json" / "test_report.json"
        report = {
            "tests": [
                {"nodeid": "t::bounded", "outcome": "passed", "duration": 0.1},
            ]
        }
        # Run 15 times
        for i in range(15):
            report_path.write_text(json.dumps(report))
            tracker._parse_json_report(report_path)

        entry = tracker.test_entries["t::bounded"]
        # History should be capped at 10 entries
        assert len(entry.history) <= 10

    def test_parse_invalid_report(self, tracker, tmp_project):
        report_path = tmp_project / "reports" / "json" / "bad.json"
        report_path.write_text("not json")
        # Should not raise
        tracker._parse_json_report(report_path)


# ---------------------------------------------------------------------------
# Query methods
# ---------------------------------------------------------------------------


class TestQueryMethods:
    """Tests for get_failing_tests, get_passing_tests, get_summary."""

    def test_get_failing_tests(self, tracker):
        tracker.test_entries["a"] = MemoryEntry(test_id="a", file_path="a.py", status="passed")
        tracker.test_entries["b"] = MemoryEntry(test_id="b", file_path="b.py", status="failed")
        tracker.test_entries["c"] = MemoryEntry(test_id="c", file_path="c.py", status="error")
        failing = tracker.get_failing_tests()
        assert len(failing) == 2
        ids = {e.test_id for e in failing}
        assert ids == {"b", "c"}

    def test_get_passing_tests(self, tracker):
        tracker.test_entries["a"] = MemoryEntry(test_id="a", file_path="a.py", status="passed")
        tracker.test_entries["b"] = MemoryEntry(test_id="b", file_path="b.py", status="failed")
        passing = tracker.get_passing_tests()
        assert len(passing) == 1
        assert passing[0].test_id == "a"

    def test_get_summary(self, tracker):
        tracker.test_entries["a"] = MemoryEntry(test_id="a", file_path="a.py", status="passed")
        tracker.test_entries["b"] = MemoryEntry(test_id="b", file_path="b.py", status="failed")
        tracker.identify_coverage_gaps()

        summary = tracker.get_summary()
        assert summary["total_tests"] == 2
        assert summary["status_counts"]["passed"] == 1
        assert summary["status_counts"]["failed"] == 1
        assert summary["total_source_modules"] > 0
        assert "coverage_percentage" in summary


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    """Tests for markdown report generation."""

    def test_report_contains_header(self, tracker):
        tracker.identify_coverage_gaps()
        report = tracker.generate_report()
        assert "AutoQA Memory Report" in report

    def test_report_contains_failing_section(self, tracker):
        tracker.test_entries["t::fail"] = MemoryEntry(
            test_id="t::fail",
            file_path="t.py",
            status="failed",
            error_message="assert False",
        )
        report = tracker.generate_report()
        assert "Failing Tests" in report
        assert "t::fail" in report

    def test_report_contains_missing_section(self, tracker):
        tracker.identify_coverage_gaps()
        report = tracker.generate_report()
        assert "Missing Tests" in report
        # reporter.py and logger.py should be listed as missing
        assert "reporter" in report

    def test_report_no_failing_section_when_all_pass(self, tracker):
        tracker.test_entries["t::ok"] = MemoryEntry(
            test_id="t::ok", file_path="t.py", status="passed"
        )
        report = tracker.generate_report()
        assert "Failing Tests" not in report


# ---------------------------------------------------------------------------
# Full update cycle
# ---------------------------------------------------------------------------


class TestUpdateCycle:
    """Tests for the full update() workflow."""

    def test_update_without_running_tests(self, tracker):
        summary = tracker.update(run_tests=False)
        assert "total_tests" in summary
        assert "total_source_modules" in summary
        assert tracker.memory_path.exists()

    @patch.object(AutoQAMemoryTracker, "run_tests", return_value=True)
    def test_update_with_running_tests(self, mock_run, tracker):
        tracker.update(run_tests=True)
        mock_run.assert_called_once()
        assert tracker.memory_path.exists()
