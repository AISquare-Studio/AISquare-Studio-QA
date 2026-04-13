"""
Studio Manager tests using CrewAI + Playwright.

Tests are split into small, focused scenarios to minimize cascading failures:
- Page rendering: each section tested independently
- Tabs: each tab tested in isolation
- Search: each search behavior tested separately
"""

import pytest

from src.crews.qa_crew import QACrew


# ---------------------------------------------------------------------------
# Page rendering tests
# ---------------------------------------------------------------------------


class TestStudioManagerRendering:
    """Verify that the Studio Manager page and its sections render correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_page_loads_successfully(self, reports_dir):
        """Studio Manager page loads without errors."""
        result = self.qa_crew.run_test_scenario("studio_manager", "page_loads_successfully")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Page Loads"

        if not result.get("success", False):
            pytest.fail(
                "Studio Manager page failed to load:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_header_section_renders(self, reports_dir):
        """Header section renders with title and action buttons."""
        result = self.qa_crew.run_test_scenario("studio_manager", "header_section_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Header Renders"

        if not result.get("success", False):
            pytest.fail(
                "Header section did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_studio_list_section_renders(self, reports_dir):
        """Main studio list/grid area renders with items or empty state."""
        result = self.qa_crew.run_test_scenario("studio_manager", "studio_list_section_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager List Section Renders"

        if not result.get("success", False):
            pytest.fail(
                "Studio list section did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.regression
    def test_sidebar_navigation_renders(self, reports_dir):
        """Sidebar or navigation panel renders with menu items."""
        result = self.qa_crew.run_test_scenario("studio_manager", "sidebar_navigation_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Sidebar Renders"

        if not result.get("success", False):
            pytest.fail(
                "Sidebar navigation did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Tab tests — each tab isolated so one tab breaking doesn't fail the others
# ---------------------------------------------------------------------------


class TestStudioManagerTabs:
    """Verify that all tabs in Studio Manager render and are navigable."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_default_tab_is_active(self, reports_dir):
        """Default/first tab is active when the page loads."""
        result = self.qa_crew.run_test_scenario("studio_manager", "default_tab_is_active")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Default Tab Active"

        if not result.get("success", False):
            pytest.fail(
                "Default tab was not active on load:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_second_tab_renders(self, reports_dir):
        """Second tab can be clicked and its content renders."""
        result = self.qa_crew.run_test_scenario("studio_manager", "second_tab_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Second Tab Renders"

        if not result.get("success", False):
            pytest.fail(
                "Second tab did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_third_tab_renders(self, reports_dir):
        """Third tab can be clicked and its content renders."""
        result = self.qa_crew.run_test_scenario("studio_manager", "third_tab_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Third Tab Renders"

        if not result.get("success", False):
            pytest.fail(
                "Third tab did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.regression
    def test_tab_switching_preserves_state(self, reports_dir):
        """Switching between tabs works and each shows its own content."""
        result = self.qa_crew.run_test_scenario("studio_manager", "tab_switching_preserves_state")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Tab Switching Works"

        if not result.get("success", False):
            pytest.fail(
                "Tab switching failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------


class TestStudioManagerSearch:
    """Verify Studio Manager search functionality."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_search_input_visible(self, reports_dir):
        """Search input field is present and interactable."""
        result = self.qa_crew.run_test_scenario("studio_manager", "search_input_visible")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Search Input Visible"

        if not result.get("success", False):
            pytest.fail(
                "Search input was not visible:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.regression
    def test_search_filters_studios(self, reports_dir):
        """Typing in search filters the displayed studios."""
        result = self.qa_crew.run_test_scenario("studio_manager", "search_filters_studios")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Search Filters Results"

        if not result.get("success", False):
            pytest.fail(
                "Search filtering did not work:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.regression
    def test_search_no_results_state(self, reports_dir):
        """Searching for a non-existent term shows empty state."""
        result = self.qa_crew.run_test_scenario("studio_manager", "search_no_results_state")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Search No Results"

        if not result.get("success", False):
            pytest.fail(
                "No-results state was not shown:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.studio
    @pytest.mark.regression
    def test_search_clear_restores_results(self, reports_dir):
        """Clearing the search restores the full studio list."""
        result = self.qa_crew.run_test_scenario("studio_manager", "search_clear_restores_results")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Studio Manager Search Clear Restores List"

        if not result.get("success", False):
            pytest.fail(
                "Clearing search did not restore results:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Config sanity check
# ---------------------------------------------------------------------------


@pytest.mark.studio
def test_studio_manager_scenarios_exist():
    """Verify all studio manager scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "studio_manager" in test_data["test_scenarios"]

    expected_scenarios = [
        "page_loads_successfully",
        "header_section_renders",
        "studio_list_section_renders",
        "sidebar_navigation_renders",
        "default_tab_is_active",
        "second_tab_renders",
        "third_tab_renders",
        "tab_switching_preserves_state",
        "search_input_visible",
        "search_filters_studios",
        "search_no_results_state",
        "search_clear_restores_results",
    ]

    for scenario in expected_scenarios:
        assert scenario in test_data["test_scenarios"]["studio_manager"], (
            f"Missing scenario: {scenario}"
        )

    assert "studio_manager_page" in test_data["selectors"]
    assert "tabs_container" in test_data["selectors"]["studio_manager_page"]
    assert "search_input" in test_data["selectors"]["studio_manager_page"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
