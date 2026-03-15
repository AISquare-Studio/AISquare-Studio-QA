"""
Tests for the Dashboard Results Builder.

Validates the transformation of gap-analysis and suite-results data
into the unified JSON schema consumed by the AutoQA Dashboard.
"""

import json

import pytest

from src.autoqa.dashboard_results import DashboardResultsBuilder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def builder():
    """Create a DashboardResultsBuilder with sample PR context."""
    return DashboardResultsBuilder(
        pr_number=42,
        commit_sha="abc123def456",
        execution_mode="pr_validation",
        timestamp="2026-03-03T14:30:00Z",
    )


@pytest.fixture
def sample_gap_results():
    """Sample output from GapAnalysisDB.run_analysis()."""
    return {
        "run_id": 1,
        "timestamp": "2026-03-03T14:30:00Z",
        "total_modules": 5,
        "present_count": 3,
        "missing_count": 2,
        "coverage_pct": 60.0,
        "workflows_present": [
            {
                "module_name": "parser",
                "source_path": "src/autoqa/parser.py",
                "test_file": "tests/test_parser.py",
                "tier": "C",
                "area": "autoqa",
            },
            {
                "module_name": "login",
                "source_path": "src/auth/login.py",
                "test_file": "tests/test_login.py",
                "tier": "A",
                "area": "auth",
            },
            {
                "module_name": "dashboard_views",
                "source_path": "src/dashboard/dashboard_views.py",
                "test_file": "tests/test_dashboard_views.py",
                "tier": "B",
                "area": "dashboard",
            },
        ],
        "workflows_missing": [
            {
                "module_name": "reporter",
                "source_path": "src/autoqa/reporter.py",
                "reason": "no_test_file",
                "suggested_test": "tests/test_reporter.py",
            },
            {
                "module_name": "logger",
                "source_path": "src/utils/logger.py",
                "reason": "no_test_file",
                "suggested_test": "tests/test_logger.py",
            },
        ],
    }


@pytest.fixture
def sample_suite_results():
    """Sample output from ActionRunner._run_test_suite()."""
    return {
        "success": False,
        "total_tests": 4,
        "passed": 3,
        "failed": 1,
        "skipped": 0,
        "execution_time": 12.5,
        "detailed_results": [
            {
                "name": "test_successful_registration",
                "nodeid": (
                    "tests/autoqa/A/auth/test_registration.py"
                    "::TestRegistration::test_successful_registration"
                ),
                "outcome": "passed",
                "duration": 3.2,
                "error": "",
            },
            {
                "name": "test_login_success",
                "nodeid": "tests/autoqa/A/auth/test_login.py::test_login_success",
                "outcome": "passed",
                "duration": 2.1,
                "error": "",
            },
            {
                "name": "test_login_invalid_password",
                "nodeid": "tests/autoqa/A/auth/test_login.py::test_login_invalid_password",
                "outcome": "failed",
                "duration": 5.1,
                "error": "AssertionError: Expected error message not displayed",
            },
            {
                "name": "test_dashboard_load",
                "nodeid": "tests/autoqa/B/dashboard/test_dashboard.py::test_dashboard_load",
                "outcome": "passed",
                "duration": 1.8,
                "error": "",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------


class TestBuildGapAnalysis:
    """Tests for build_gap_analysis()."""

    def test_empty_gap_results(self, builder):
        result = builder.build_gap_analysis(None)
        assert result["coverage_percent"] == 0.0
        assert result["total_workflows"] == 0
        assert result["tested_workflows"] == 0
        assert result["missing_workflows"] == 0
        assert result["present_workflows"] == []
        assert result["missing_workflows_list"] == []

    def test_coverage_percent(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        assert result["coverage_percent"] == 60.0

    def test_workflow_counts(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        assert result["total_workflows"] == 5
        assert result["tested_workflows"] == 3
        assert result["missing_workflows"] == 2

    def test_present_workflow_fields(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        present = result["present_workflows"]
        assert len(present) == 3

        first = present[0]
        assert "module" in first
        assert "source_path" in first
        assert "test_file" in first
        assert "tier" in first
        assert "area" in first

    def test_present_workflow_values(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        parser_wf = result["present_workflows"][0]
        assert parser_wf["module"] == "parser"
        assert parser_wf["source_path"] == "src/autoqa/parser.py"
        assert parser_wf["test_file"] == "tests/test_parser.py"
        assert parser_wf["tier"] == "C"
        assert parser_wf["area"] == "autoqa"

    def test_missing_workflow_fields(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        missing = result["missing_workflows_list"]
        assert len(missing) == 2

        first = missing[0]
        assert "module" in first
        assert "source_path" in first
        # missing workflows should not have test_file or tier
        assert "test_file" not in first

    def test_missing_workflow_values(self, builder, sample_gap_results):
        result = builder.build_gap_analysis(sample_gap_results)
        reporter_wf = result["missing_workflows_list"][0]
        assert reporter_wf["module"] == "reporter"
        assert reporter_wf["source_path"] == "src/autoqa/reporter.py"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class TestBuildSummary:
    """Tests for build_summary()."""

    def test_empty_suite_results(self, builder):
        result = builder.build_summary(None)
        assert result["timestamp"] == "2026-03-03T14:30:00Z"
        assert result["execution_mode"] == "pr_validation"
        assert result["pr_number"] == 42
        assert result["commit_sha"] == "abc123def456"
        assert result["total_tests"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["skipped"] == 0
        assert result["duration_seconds"] == 0.0

    def test_with_suite_results(self, builder, sample_suite_results):
        result = builder.build_summary(sample_suite_results)
        assert result["total_tests"] == 4
        assert result["passed"] == 3
        assert result["failed"] == 1
        assert result["skipped"] == 0
        assert result["duration_seconds"] == 12.5

    def test_pr_metadata(self, builder, sample_suite_results):
        result = builder.build_summary(sample_suite_results)
        assert result["pr_number"] == 42
        assert result["commit_sha"] == "abc123def456"
        assert result["execution_mode"] == "pr_validation"


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestBuildTestCases:
    """Tests for build_test_cases()."""

    def test_empty_suite_results(self, builder):
        result = builder.build_test_cases(None)
        assert result == []

    def test_test_case_count(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        assert len(result) == 4

    def test_passed_test_fields(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        passed = [t for t in result if t["status"] == "passed"]
        assert len(passed) == 3

        first = passed[0]
        assert "test_id" in first
        assert "flow_name" in first
        assert "tier" in first
        assert "area" in first
        assert "status" in first
        assert "duration_seconds" in first
        assert "screenshots" in first

    def test_failed_test_has_error(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        failed = [t for t in result if t["status"] == "failed"]
        assert len(failed) == 1

        fail = failed[0]
        assert "error_message" in fail
        assert "AssertionError" in fail["error_message"]
        assert fail["error_type"] == "AssertionError"

    def test_test_id_is_nodeid(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        first = result[0]
        assert "::" in first["test_id"]

    def test_flow_name_extracted(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        flow_names = [t["flow_name"] for t in result]
        assert "registration" in flow_names
        assert "login" in flow_names
        assert "dashboard" in flow_names

    def test_tier_inferred_from_path(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        # tests/autoqa/A/auth/* → tier A
        auth_tests = [t for t in result if "auth" in t["test_id"]]
        for t in auth_tests:
            assert t["tier"] == "A"

        # tests/autoqa/B/dashboard/* → tier B
        dashboard_tests = [t for t in result if "dashboard" in t["test_id"]]
        for t in dashboard_tests:
            assert t["tier"] == "B"

    def test_area_inferred_from_path(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        auth_tests = [t for t in result if "auth" in t["test_id"]]
        for t in auth_tests:
            assert t["area"] == "auth"

    def test_duration_is_rounded(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        for t in result:
            # Check that duration has at most 2 decimal places
            assert t["duration_seconds"] == round(t["duration_seconds"], 2)

    def test_screenshots_default_empty(self, builder, sample_suite_results):
        result = builder.build_test_cases(sample_suite_results)
        for t in result:
            assert t["screenshots"] == []


# ---------------------------------------------------------------------------
# Full build
# ---------------------------------------------------------------------------


class TestBuild:
    """Tests for the full build() method."""

    def test_all_keys_present(self, builder, sample_gap_results, sample_suite_results):
        result = builder.build(sample_gap_results, sample_suite_results)
        assert "gap_analysis" in result
        assert "summary" in result
        assert "test_cases" in result

    def test_gap_analysis_populated(self, builder, sample_gap_results, sample_suite_results):
        result = builder.build(sample_gap_results, sample_suite_results)
        assert result["gap_analysis"]["coverage_percent"] == 60.0

    def test_summary_populated(self, builder, sample_gap_results, sample_suite_results):
        result = builder.build(sample_gap_results, sample_suite_results)
        assert result["summary"]["total_tests"] == 4

    def test_test_cases_populated(self, builder, sample_gap_results, sample_suite_results):
        result = builder.build(sample_gap_results, sample_suite_results)
        assert len(result["test_cases"]) == 4

    def test_empty_inputs(self, builder):
        result = builder.build(None, None)
        assert result["gap_analysis"]["total_workflows"] == 0
        assert result["summary"]["total_tests"] == 0
        assert result["test_cases"] == []

    def test_only_gap_results(self, builder, sample_gap_results):
        result = builder.build(sample_gap_results, None)
        assert result["gap_analysis"]["coverage_percent"] == 60.0
        assert result["summary"]["total_tests"] == 0
        assert result["test_cases"] == []

    def test_only_suite_results(self, builder, sample_suite_results):
        result = builder.build(None, sample_suite_results)
        assert result["gap_analysis"]["total_workflows"] == 0
        assert result["summary"]["total_tests"] == 4
        assert len(result["test_cases"]) == 4

    def test_json_serializable(self, builder, sample_gap_results, sample_suite_results):
        result = builder.build(sample_gap_results, sample_suite_results)
        # Should not raise
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized == result


# ---------------------------------------------------------------------------
# Build and save
# ---------------------------------------------------------------------------


class TestBuildAndSave:
    """Tests for build_and_save()."""

    def test_creates_file(self, builder, sample_gap_results, tmp_path):
        output = tmp_path / "dashboard_results.json"
        builder.build_and_save(
            gap_results=sample_gap_results,
            output_path=str(output),
        )
        assert output.exists()

    def test_file_is_valid_json(self, builder, sample_suite_results, tmp_path):
        output = tmp_path / "dashboard_results.json"
        builder.build_and_save(
            suite_results=sample_suite_results,
            output_path=str(output),
        )
        with open(output, "r") as f:
            data = json.load(f)
        assert "gap_analysis" in data
        assert "summary" in data
        assert "test_cases" in data

    def test_creates_parent_directories(self, builder, tmp_path):
        output = tmp_path / "deep" / "nested" / "results.json"
        builder.build_and_save(output_path=str(output))
        assert output.exists()

    def test_returns_payload(self, builder, sample_gap_results, tmp_path):
        output = tmp_path / "dashboard_results.json"
        payload = builder.build_and_save(
            gap_results=sample_gap_results,
            output_path=str(output),
        )
        assert payload["gap_analysis"]["coverage_percent"] == 60.0


# ---------------------------------------------------------------------------
# Helper methods
# ---------------------------------------------------------------------------


class TestHelpers:
    """Tests for static/class helper methods."""

    def test_map_status_passed(self):
        assert DashboardResultsBuilder._map_status("passed") == "passed"

    def test_map_status_failed(self):
        assert DashboardResultsBuilder._map_status("failed") == "failed"

    def test_map_status_error(self):
        assert DashboardResultsBuilder._map_status("error") == "failed"

    def test_map_status_skipped(self):
        assert DashboardResultsBuilder._map_status("skipped") == "skipped"

    def test_map_status_xfailed(self):
        assert DashboardResultsBuilder._map_status("xfailed") == "skipped"

    def test_map_status_xpassed(self):
        assert DashboardResultsBuilder._map_status("xpassed") == "passed"

    def test_map_status_unknown(self):
        assert DashboardResultsBuilder._map_status("foobar") == "unknown"

    def test_infer_flow_name_full_nodeid(self):
        nodeid = "tests/autoqa/A/auth/test_user_login.py::TestLogin::test_login"
        assert DashboardResultsBuilder._infer_flow_name(nodeid) == "user_login"

    def test_infer_flow_name_simple(self):
        nodeid = "tests/test_parser.py::test_parse"
        assert DashboardResultsBuilder._infer_flow_name(nodeid) == "parser"

    def test_infer_flow_name_no_prefix(self):
        nodeid = "tests/parser.py::test_parse"
        assert DashboardResultsBuilder._infer_flow_name(nodeid) == "parser"

    def test_infer_tier_explicit_a(self):
        nodeid = "tests/autoqa/A/auth/test_login.py::test_login"
        assert DashboardResultsBuilder._infer_tier_from_nodeid(nodeid) == "A"

    def test_infer_tier_explicit_b(self):
        nodeid = "tests/autoqa/B/dashboard/test_dash.py::test_dash"
        assert DashboardResultsBuilder._infer_tier_from_nodeid(nodeid) == "B"

    def test_infer_tier_keyword_fallback(self):
        nodeid = "tests/test_login.py::test_login"
        assert DashboardResultsBuilder._infer_tier_from_nodeid(nodeid) == "A"

    def test_infer_tier_default_c(self):
        nodeid = "tests/test_utils.py::test_helper"
        assert DashboardResultsBuilder._infer_tier_from_nodeid(nodeid) == "C"

    def test_infer_area_from_path(self):
        nodeid = "tests/autoqa/A/auth/test_login.py::test_login"
        assert DashboardResultsBuilder._infer_area_from_nodeid(nodeid) == "auth"

    def test_infer_area_skips_tier_dir(self):
        nodeid = "tests/autoqa/A/test_login.py::test_login"
        assert DashboardResultsBuilder._infer_area_from_nodeid(nodeid) == "autoqa"

    def test_infer_area_general(self):
        nodeid = "test_login.py::test_login"
        assert DashboardResultsBuilder._infer_area_from_nodeid(nodeid) == "general"

    def test_extract_error_type_assertion(self):
        msg = "AssertionError: Expected error message not displayed"
        assert DashboardResultsBuilder._extract_error_type(msg) == "AssertionError"

    def test_extract_error_type_type_error(self):
        msg = "TypeError: 'NoneType' object is not subscriptable"
        assert DashboardResultsBuilder._extract_error_type(msg) == "TypeError"

    def test_extract_error_type_no_colon(self):
        msg = "Something went wrong"
        assert DashboardResultsBuilder._extract_error_type(msg) == ""

    def test_extract_error_type_empty(self):
        assert DashboardResultsBuilder._extract_error_type("") == ""

    def test_extract_error_type_not_error_class(self):
        msg = "lowercase: not an error type"
        assert DashboardResultsBuilder._extract_error_type(msg) == ""


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    """Tests for DashboardResultsBuilder constructor."""

    def test_pr_number_int(self):
        builder = DashboardResultsBuilder(pr_number=42)
        assert builder.pr_number == 42

    def test_pr_number_str(self):
        builder = DashboardResultsBuilder(pr_number="42")
        assert builder.pr_number == 42

    def test_pr_number_none(self):
        builder = DashboardResultsBuilder(pr_number=None)
        assert builder.pr_number is None

    def test_defaults(self):
        builder = DashboardResultsBuilder()
        assert builder.pr_number is None
        assert builder.commit_sha == ""
        assert builder.execution_mode == "pr_validation"
        assert builder.timestamp is not None
