"""
Tests for the Test-ID Scanner module.

Covers registry loading, test-file scanning, coverage calculation
(both full and PR-scoped), filtering logic, and report generation.
"""

import pytest
import yaml

from src.autoqa.testid_scanner import TestIdCoverageResult, TestIdEntry, TestIdScanner

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project with a registry and test files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Registry with two flows
    registry = {
        "flows": [
            {
                "name": "login",
                "area": "auth",
                "tier": "A",
                "testids": [
                    {"id": "login-email-input", "description": "Email field"},
                    {"id": "login-password-input", "description": "Password field"},
                    {"id": "login-submit-button", "description": "Submit button"},
                ],
            },
            {
                "name": "dashboard",
                "area": "dashboard",
                "tier": "B",
                "testids": [
                    "dashboard-header",
                    "dashboard-logout-button",
                ],
            },
        ]
    }
    (config_dir / "testid_registry.yaml").write_text(yaml.dump(registry))

    # Test file that references some testids
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_login.py").write_text(
        """
import pytest

def test_login_success(page):
    page.locator('[data-testid="login-email-input"]').fill("user@example.com")
    page.locator('[data-testid="login-password-input"]').fill("secret")
    page.locator('[data-testid="login-submit-button"]').click()
"""
    )
    (test_dir / "test_dashboard.py").write_text(
        """
def test_dashboard_visible(page):
    assert page.locator('[data-testid="dashboard-header"]').is_visible()
"""
    )

    return tmp_path


@pytest.fixture
def scanner(tmp_project):
    return TestIdScanner(project_root=str(tmp_project))


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------


class TestRegistryLoading:
    """Tests for loading the test-ID registry."""

    def test_load_registry_returns_entries(self, scanner):
        entries = scanner.load_registry()
        assert len(entries) == 5  # 3 login + 2 dashboard

    def test_entries_have_correct_flow(self, scanner):
        entries = scanner.load_registry()
        login_entries = [e for e in entries if e.flow == "login"]
        assert len(login_entries) == 3

    def test_entries_have_correct_tier(self, scanner):
        entries = scanner.load_registry()
        login_entries = [e for e in entries if e.flow == "login"]
        assert all(e.tier == "A" for e in login_entries)

    def test_entries_have_description(self, scanner):
        entries = scanner.load_registry()
        email_entry = [e for e in entries if e.testid == "login-email-input"][0]
        assert email_entry.description == "Email field"

    def test_shorthand_string_testids(self, scanner):
        entries = scanner.load_registry()
        header = [e for e in entries if e.testid == "dashboard-header"][0]
        assert header.flow == "dashboard"
        assert header.description == ""

    def test_missing_registry_returns_empty(self, tmp_path):
        sc = TestIdScanner(project_root=str(tmp_path))
        assert sc.load_registry() == []

    def test_invalid_registry_returns_empty(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "testid_registry.yaml").write_text("{{{invalid")
        sc = TestIdScanner(project_root=str(tmp_path))
        assert sc.load_registry() == []


# ---------------------------------------------------------------------------
# Test-file scanning
# ---------------------------------------------------------------------------


class TestTestFileScanning:
    """Tests for scanning test files for data-testid references."""

    def test_finds_referenced_testids(self, scanner):
        refs = scanner.scan_test_files_for_testids()
        assert "login-email-input" in refs
        assert "login-password-input" in refs
        assert "login-submit-button" in refs
        assert "dashboard-header" in refs

    def test_does_not_find_unreferenced_testids(self, scanner):
        refs = scanner.scan_test_files_for_testids()
        assert "dashboard-logout-button" not in refs

    def test_nonexistent_test_dir_returns_empty(self, tmp_path):
        sc = TestIdScanner(project_root=str(tmp_path), test_dir="nonexistent")
        assert sc.scan_test_files_for_testids() == set()

    def test_get_by_test_id_pattern(self, tmp_project):
        test_dir = tmp_project / "tests"
        (test_dir / "test_alt.py").write_text('page.get_by_test_id("alt-element")\n')
        sc = TestIdScanner(project_root=str(tmp_project))
        refs = sc.scan_test_files_for_testids()
        assert "alt-element" in refs


# ---------------------------------------------------------------------------
# Coverage calculation – full scope
# ---------------------------------------------------------------------------


class TestCoverageCalculationFull:
    """Tests for full-scope coverage calculation."""

    def test_coverage_returns_result(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        assert isinstance(result, TestIdCoverageResult)

    def test_total_testids(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        assert result.total_testids == 5

    def test_covered_testids(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        # login-email-input, login-password-input, login-submit-button, dashboard-header
        assert result.covered_testids == 4

    def test_uncovered_testids(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        assert "dashboard-logout-button" in result.uncovered_ids

    def test_coverage_percentage(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        assert result.coverage_pct == 80.0

    def test_scope_label(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        assert result.scope == "full"

    def test_to_dict(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        d = result.to_dict()
        assert "total_testids" in d
        assert "covered_ids" in d
        assert "uncovered_entries" in d

    def test_no_registry_returns_zero(self, tmp_path):
        (tmp_path / "tests").mkdir()
        sc = TestIdScanner(project_root=str(tmp_path))
        result = sc.calculate_coverage()
        assert result.total_testids == 0
        assert result.coverage_pct == 0.0


# ---------------------------------------------------------------------------
# Coverage calculation – PR scope
# ---------------------------------------------------------------------------


class TestCoverageCalculationPR:
    """Tests for PR-scoped coverage calculation."""

    def test_pr_scope_filters_by_changed_files(self, scanner):
        result = scanner.calculate_coverage(
            scope="pr",
            changed_files=["src/auth/login.py"],
        )
        # Only login flow testids (3) should be considered
        assert result.total_testids == 3
        assert result.scope == "pr"

    def test_pr_scope_dashboard_changed(self, scanner):
        result = scanner.calculate_coverage(
            scope="pr",
            changed_files=["src/dashboard/views.py"],
        )
        # Only dashboard flow testids (2) should be considered
        assert result.total_testids == 2

    def test_pr_scope_no_matching_changes(self, scanner):
        result = scanner.calculate_coverage(
            scope="pr",
            changed_files=["src/utils/helper.py"],
        )
        assert result.total_testids == 0

    def test_pr_scope_no_changed_files_returns_empty(self, scanner):
        result = scanner.calculate_coverage(scope="pr", changed_files=[])
        assert result.total_testids == 0

    def test_pr_scope_none_changed_files_returns_all(self, scanner):
        # When changed_files is None with pr scope, no filtering happens
        result = scanner.calculate_coverage(scope="pr", changed_files=None)
        assert result.total_testids == 5


# ---------------------------------------------------------------------------
# TestIdEntry
# ---------------------------------------------------------------------------


class TestTestIdEntry:
    """Tests for TestIdEntry serialization."""

    def test_to_dict(self):
        entry = TestIdEntry(
            testid="login-email-input",
            flow="login",
            area="auth",
            tier="A",
            description="Email field",
        )
        d = entry.to_dict()
        assert d["testid"] == "login-email-input"
        assert d["flow"] == "login"
        assert d["tier"] == "A"


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    """Tests for the uncovered-test-ID report."""

    def test_report_contains_header(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        report = scanner.generate_uncovered_report(result)
        assert "Test-ID Coverage Report" in report

    def test_report_contains_uncovered_testid(self, scanner):
        result = scanner.calculate_coverage(scope="full")
        report = scanner.generate_uncovered_report(result)
        assert "dashboard-logout-button" in report

    def test_report_all_covered(self, tmp_project):
        # Add test covering the missing testid
        test_dir = tmp_project / "tests"
        (test_dir / "test_dashboard_more.py").write_text(
            "page.locator('[data-testid=\"dashboard-logout-button\"]').click()\n"
        )
        sc = TestIdScanner(project_root=str(tmp_project))
        result = sc.calculate_coverage(scope="full")
        report = sc.generate_uncovered_report(result)
        assert "All registered" in report
