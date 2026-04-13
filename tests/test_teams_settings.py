"""
Teams settings tests using CrewAI + Playwright.

Each settings section is tested independently so changes to one area
(e.g., members) do not break unrelated tests (e.g., general info).
"""

import pytest

from src.crews.qa_crew import QACrew


class TestTeamsSettingsRendering:
    """Verify team settings page sections render correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_settings_page_loads(self, reports_dir):
        """Team settings page loads after navigation."""
        result = self.qa_crew.run_test_scenario("teams_settings", "settings_page_loads")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Settings Page Loads"

        if not result.get("success", False):
            pytest.fail(
                "Team settings page failed to load:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_general_settings_section_renders(self, reports_dir):
        """General settings section renders with name and description fields."""
        result = self.qa_crew.run_test_scenario("teams_settings", "general_settings_section_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team General Settings Section Renders"

        if not result.get("success", False):
            pytest.fail(
                "General settings section did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_members_section_renders(self, reports_dir):
        """Members/permissions section renders in team settings."""
        result = self.qa_crew.run_test_scenario("teams_settings", "members_section_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Members Section Renders"

        if not result.get("success", False):
            pytest.fail(
                "Members section did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_save_button_visible(self, reports_dir):
        """Save/update button is present and interactable."""
        result = self.qa_crew.run_test_scenario("teams_settings", "save_button_visible")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Settings Save Button Visible"

        if not result.get("success", False):
            pytest.fail(
                "Save button was not visible:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_danger_zone_renders(self, reports_dir):
        """Danger zone section renders with delete/archive option."""
        result = self.qa_crew.run_test_scenario("teams_settings", "danger_zone_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Settings Danger Zone Renders"

        if not result.get("success", False):
            pytest.fail(
                "Danger zone did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


class TestTeamsSettingsUpdates:
    """Verify team settings can be updated successfully."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.regression
    def test_update_team_name(self, reports_dir):
        """Team name can be updated through settings."""
        result = self.qa_crew.run_test_scenario("teams_settings", "update_team_name")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Update Team Name"

        if not result.get("success", False):
            pytest.fail(
                "Updating team name failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_update_team_description(self, reports_dir):
        """Team description can be updated through settings."""
        result = self.qa_crew.run_test_scenario("teams_settings", "update_team_description")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Update Team Description"

        if not result.get("success", False):
            pytest.fail(
                "Updating team description failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


@pytest.mark.teams
def test_teams_settings_scenarios_exist():
    """Verify all teams settings scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "teams_settings" in test_data["test_scenarios"]

    expected = [
        "settings_page_loads",
        "general_settings_section_renders",
        "members_section_renders",
        "update_team_name",
        "update_team_description",
        "save_button_visible",
        "danger_zone_renders",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["teams_settings"], (
            f"Missing scenario: {scenario}"
        )

    assert "teams_settings_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
