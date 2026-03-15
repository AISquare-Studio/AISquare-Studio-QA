"""
Tests for the Gap Analysis Database Manager.

Tests database creation, analysis execution, querying, persistence,
and integration with the memory tracker.
"""

import sqlite3

import pytest

from src.autoqa.gap_analysis_db import GapAnalysisDB

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

    # Create test files (only parser and runner — reporter and logger are gaps)
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").touch()
    (test_dir / "test_parser.py").write_text("def test_parse(): assert True\n")
    (test_dir / "test_runner.py").write_text("def test_run(): assert True\n")

    # Create reports directory
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    return tmp_path


@pytest.fixture
def gap_db(tmp_project):
    """Create a GapAnalysisDB instance with the temporary project."""
    return GapAnalysisDB(
        project_root=str(tmp_project),
        db_path="reports/gap_analysis.db",
        test_dir="tests",
        source_dirs=["src"],
    )


# ---------------------------------------------------------------------------
# Database creation
# ---------------------------------------------------------------------------


class TestDatabaseCreation:
    """Tests for database initialization and table creation."""

    def test_creates_database_file(self, gap_db, tmp_project):
        db_file = tmp_project / "reports" / "gap_analysis.db"
        assert db_file.exists()

    def test_creates_tables(self, gap_db):
        conn = sqlite3.connect(str(gap_db.db_path))
        try:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "analysis_runs" in tables
            assert "workflows_present" in tables
            assert "workflows_missing" in tables
        finally:
            conn.close()

    def test_creates_parent_directories(self, tmp_path):
        GapAnalysisDB(
            project_root=str(tmp_path),
            db_path="deep/nested/dir/gap.db",
        )
        assert (tmp_path / "deep" / "nested" / "dir" / "gap.db").exists()

    def test_reuses_existing_database(self, gap_db):
        """Opening the same database twice should not raise or lose data."""
        gap_db.run_analysis()
        db2 = GapAnalysisDB(
            project_root=str(gap_db.project_root),
            db_path="reports/gap_analysis.db",
            test_dir="tests",
            source_dirs=["src"],
        )
        latest = db2.get_latest_run()
        assert latest is not None


# ---------------------------------------------------------------------------
# Analysis execution
# ---------------------------------------------------------------------------


class TestRunAnalysis:
    """Tests for the run_analysis() method."""

    def test_returns_summary(self, gap_db):
        result = gap_db.run_analysis()
        assert "run_id" in result
        assert "timestamp" in result
        assert "total_modules" in result
        assert "present_count" in result
        assert "missing_count" in result
        assert "coverage_pct" in result
        assert "workflows_present" in result
        assert "workflows_missing" in result

    def test_identifies_present_workflows(self, gap_db):
        result = gap_db.run_analysis()
        present_names = {w["module_name"] for w in result["workflows_present"]}
        assert "parser" in present_names
        assert "runner" in present_names

    def test_identifies_missing_workflows(self, gap_db):
        result = gap_db.run_analysis()
        missing_names = {w["module_name"] for w in result["workflows_missing"]}
        assert "reporter" in missing_names
        assert "logger" in missing_names

    def test_coverage_percentage(self, gap_db):
        result = gap_db.run_analysis()
        # 2 covered out of 4 modules = 50%
        assert result["coverage_pct"] == 50.0

    def test_missing_has_suggested_test(self, gap_db):
        result = gap_db.run_analysis()
        for w in result["workflows_missing"]:
            assert "suggested_test" in w
            assert w["suggested_test"].startswith("tests/test_")
            assert w["suggested_test"].endswith(".py")

    def test_present_count_plus_missing_equals_total(self, gap_db):
        result = gap_db.run_analysis()
        assert result["present_count"] + result["missing_count"] == result["total_modules"]

    def test_all_covered_shows_zero_missing(self, tmp_project):
        """When all modules have tests, missing count should be 0."""
        test_dir = tmp_project / "tests"
        (test_dir / "test_reporter.py").write_text("def test_report(): assert True\n")
        (test_dir / "test_logger.py").write_text("def test_log(): assert True\n")

        db = GapAnalysisDB(
            project_root=str(tmp_project),
            test_dir="tests",
            source_dirs=["src"],
        )
        result = db.run_analysis()
        assert result["missing_count"] == 0
        assert result["coverage_pct"] == 100.0


# ---------------------------------------------------------------------------
# Persistence and querying
# ---------------------------------------------------------------------------


class TestPersistence:
    """Tests for database persistence and query methods."""

    def test_get_latest_run_returns_none_initially(self, gap_db):
        latest = gap_db.get_latest_run()
        assert latest is None

    def test_get_latest_run_after_analysis(self, gap_db):
        gap_db.run_analysis()
        latest = gap_db.get_latest_run()
        assert latest is not None
        assert latest["total_modules"] > 0

    def test_get_latest_run_returns_most_recent(self, gap_db):
        gap_db.run_analysis()
        gap_db.run_analysis()
        latest = gap_db.get_latest_run()
        assert latest["run_id"] == 2

    def test_latest_run_includes_workflows(self, gap_db):
        gap_db.run_analysis()
        latest = gap_db.get_latest_run()
        assert len(latest["workflows_present"]) > 0
        assert len(latest["workflows_missing"]) > 0

    def test_get_run_history(self, gap_db):
        gap_db.run_analysis()
        gap_db.run_analysis()
        gap_db.run_analysis()
        history = gap_db.get_run_history(limit=2)
        assert len(history) == 2
        # Most recent first
        assert history[0]["id"] > history[1]["id"]

    def test_get_run_history_empty(self, gap_db):
        history = gap_db.get_run_history()
        assert history == []

    def test_data_persisted_across_instances(self, gap_db, tmp_project):
        gap_db.run_analysis()

        db2 = GapAnalysisDB(
            project_root=str(tmp_project),
            db_path="reports/gap_analysis.db",
            test_dir="tests",
            source_dirs=["src"],
        )
        latest = db2.get_latest_run()
        assert latest is not None
        assert latest["total_modules"] > 0


# ---------------------------------------------------------------------------
# Tier and area inference
# ---------------------------------------------------------------------------


class TestTierAreaInference:
    """Tests for tier and area inference from source paths."""

    def test_critical_path_tier_a(self, gap_db):
        assert gap_db._infer_tier("src/auth/login.py") == "A"

    def test_important_path_tier_b(self, gap_db):
        assert gap_db._infer_tier("src/dashboard/views.py") == "B"

    def test_other_path_tier_c(self, gap_db):
        assert gap_db._infer_tier("src/utils/helper.py") == "C"

    def test_area_from_path(self, gap_db):
        assert gap_db._infer_area("src/autoqa/parser.py") == "autoqa"

    def test_area_from_short_path(self, gap_db):
        assert gap_db._infer_area("parser.py") == "general"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_project(self, tmp_path):
        """Project with no source or test files."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        db = GapAnalysisDB(
            project_root=str(tmp_path),
            test_dir="tests",
            source_dirs=["src"],
        )
        result = db.run_analysis()
        assert result["total_modules"] == 0
        assert result["present_count"] == 0
        assert result["missing_count"] == 0
        assert result["coverage_pct"] == 0.0

    def test_multiple_runs_accumulate(self, gap_db):
        gap_db.run_analysis()
        gap_db.run_analysis()
        history = gap_db.get_run_history()
        assert len(history) == 2
