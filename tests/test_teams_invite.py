"""
Teams invite tests using CrewAI + Playwright.

Covers the invite modal rendering, happy path, validation errors,
cancel flow, duplicate detection, pending invites display, and
workspace redirect correctness.
"""

import pytest

from src.crews.qa_crew import QACrew


# ---------------------------------------------------------------------------
# Invite UI rendering
# ---------------------------------------------------------------------------


class TestTeamsInviteRendering:
    """Verify the invite UI elements render correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_invite_button_visible(self, reports_dir):
        """Invite / Add Member button is visible on the team page."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_button_visible")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Button Visible"

        if not result.get("success", False):
            pytest.fail(
                "Invite button was not visible:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_invite_modal_opens(self, reports_dir):
        """Invite modal opens with email, role selector, and submit button."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_modal_opens")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Modal Opens"

        if not result.get("success", False):
            pytest.fail(
                "Invite modal did not open correctly:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_invite_role_selector_renders(self, reports_dir):
        """Role selector shows available roles."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_role_selector_renders")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Role Selector Renders"

        if not result.get("success", False):
            pytest.fail(
                "Role selector did not render correctly:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.regression
    def test_pending_invites_visible(self, reports_dir):
        """Pending invites section displays sent invitations."""
        result = self.qa_crew.run_test_scenario("teams_invite", "pending_invites_visible")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Pending Invites Visible"

        if not result.get("success", False):
            pytest.fail(
                "Pending invites section was not visible:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Invite happy path & redirect
# ---------------------------------------------------------------------------


class TestTeamsInviteFlow:
    """Verify the end-to-end invite flow and workspace redirect."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_invite_member_by_email(self, reports_dir):
        """Full happy path: invite a member and verify workspace redirect."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_member_by_email")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Member By Email"

        if not result.get("success", False):
            pytest.fail(
                "Invite member flow failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.teams
    @pytest.mark.smoke
    def test_invite_redirects_to_correct_workspace(self, reports_dir):
        """After sending an invite the user stays on the correct workspace."""
        result = self.qa_crew.run_test_scenario(
            "teams_invite", "invite_redirects_to_correct_workspace"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Redirects To Correct Workspace"

        if not result.get("success", False):
            pytest.fail(
                "Invite did not redirect to correct workspace:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Invite validation
# ---------------------------------------------------------------------------


class TestTeamsInviteValidation:
    """Verify invite form validation and error handling."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.teams
    @pytest.mark.regression
    def test_invite_invalid_email(self, reports_dir):
        """Invalid email format shows a validation error."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_invalid_email")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Invalid Email Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.teams
    @pytest.mark.regression
    def test_invite_empty_email(self, reports_dir):
        """Empty email field shows a validation error."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_empty_email")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Empty Email Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.teams
    @pytest.mark.regression
    def test_invite_duplicate_member(self, reports_dir):
        """Inviting an existing member shows a duplicate error."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_duplicate_member")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Duplicate Member"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.teams
    @pytest.mark.regression
    def test_invite_cancel_closes_modal(self, reports_dir):
        """Cancelling the invite modal closes it without sending."""
        result = self.qa_crew.run_test_scenario("teams_invite", "invite_cancel_closes_modal")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Team Invite Cancel Closes Modal"

        if not result.get("success", False):
            pytest.fail(
                "Cancel did not close the invite modal:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Config sanity check
# ---------------------------------------------------------------------------


@pytest.mark.teams
def test_teams_invite_scenarios_exist():
    """Verify all teams invite scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "teams_invite" in test_data["test_scenarios"]

    expected = [
        "invite_button_visible",
        "invite_modal_opens",
        "invite_role_selector_renders",
        "invite_member_by_email",
        "invite_redirects_to_correct_workspace",
        "invite_invalid_email",
        "invite_empty_email",
        "invite_duplicate_member",
        "invite_cancel_closes_modal",
        "pending_invites_visible",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["teams_invite"], (
            f"Missing scenario: {scenario}"
        )

    assert "teams_invite_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
