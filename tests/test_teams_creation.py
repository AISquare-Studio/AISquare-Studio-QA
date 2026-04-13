"""
Teams creation tests using CrewAI + Playwright.

Covers the happy path, validation errors, and cancel flow for creating teams.
"""

import pytest

from src.crews.qa_crew import QACrew


class TestTeamsCreation:
    """Verify team creation flows work correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_create_team_form_renders(self, reports_dir):
        """Team creation form opens with all required fields."""
        result = self.qa_crew.run_test_scenario("teams_creation", "create_team_form_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Team Form Renders"

        if not result.get("success", False):
            pytest.fail(
                "Create team form did not render correctly:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_create_team_basic(self, reports_dir):
        """Full happy path: create a new team successfully."""
        result = self.qa_crew.run_test_scenario("teams_creation", "create_team_basic")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Team Basic Flow"

        if not result.get("success", False):
            pytest.fail(
                "Create team basic flow failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_create_team_empty_name(self, reports_dir):
        """Creating a team without a name shows a validation error."""
        result = self.qa_crew.run_test_scenario("teams_creation", "create_team_empty_name")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Team Empty Name Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.teams
    @pytest.mark.regression
    def test_create_team_duplicate_name(self, reports_dir):
        """Creating a team with a duplicate name shows an error."""
        result = self.qa_crew.run_test_scenario("teams_creation", "create_team_duplicate_name")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Team Duplicate Name Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.teams
    @pytest.mark.regression
    def test_create_team_cancel(self, reports_dir):
        """Cancelling the creation form closes it without creating a team."""
        result = self.qa_crew.run_test_scenario("teams_creation", "create_team_cancel")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Team Cancel Closes Form"

        if not result.get("success", False):
            pytest.fail(
                "Cancel flow did not work correctly:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


@pytest.mark.teams
def test_teams_creation_scenarios_exist():
    """Verify all teams creation scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "teams_creation" in test_data["test_scenarios"]

    expected = [
        "create_team_form_renders",
        "create_team_basic",
        "create_team_empty_name",
        "create_team_duplicate_name",
        "create_team_cancel",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["teams_creation"], (
            f"Missing scenario: {scenario}"
        )

    assert "teams_creation_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
