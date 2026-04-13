"""
Teams page rendering tests using CrewAI + Playwright.

Each section is tested independently so a single broken section
does not cascade into failures for unrelated areas of the page.
"""

import pytest

from src.crews.qa_crew import QACrew


class TestTeamsPageRendering:
    """Verify the Teams page and its sections render correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_page_loads_successfully(self, reports_dir):
        """Teams page loads without errors."""
        result = self.qa_crew.run_test_scenario("teams_page", "page_loads_successfully")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Teams Page Loads"

        if not result.get("success", False):
            pytest.fail(
                "Teams page failed to load:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_header_section_renders(self, reports_dir):
        """Header section renders with title and action buttons."""
        result = self.qa_crew.run_test_scenario("teams_page", "header_section_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Teams Page Header Renders"

        if not result.get("success", False):
            pytest.fail(
                "Teams header did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_teams_list_renders(self, reports_dir):
        """Teams list/grid renders with team items or empty state."""
        result = self.qa_crew.run_test_scenario("teams_page", "teams_list_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Teams List Section Renders"

        if not result.get("success", False):
            pytest.fail(
                "Teams list did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_team_card_details_render(self, reports_dir):
        """Individual team card shows name and member count."""
        result = self.qa_crew.run_test_scenario("teams_page", "team_card_details_render")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Card Details Render"

        if not result.get("success", False):
            pytest.fail(
                "Team card details did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_search_teams_works(self, reports_dir):
        """Search/filter on the Teams page works correctly."""
        result = self.qa_crew.run_test_scenario("teams_page", "search_teams_works")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Teams Search Works"

        if not result.get("success", False):
            pytest.fail(
                "Teams search did not work:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


@pytest.mark.teams
def test_teams_page_scenarios_exist():
    """Verify all teams page scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "teams_page" in test_data["test_scenarios"]

    expected = [
        "page_loads_successfully",
        "header_section_renders",
        "teams_list_renders",
        "team_card_details_render",
        "search_teams_works",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["teams_page"], (
            f"Missing scenario: {scenario}"
        )

    assert "teams_page_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
