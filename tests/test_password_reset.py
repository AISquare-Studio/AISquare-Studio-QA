"""
Password reset / recovery tests using CrewAI + Playwright.

Strategy:
- UI tests: cover the forgot-password form, validation, and navigation
  without needing email access.
- Token-based tests: retrieve the reset token from the staging backend
  (RESET_TOKEN_API env var or MailHog API) to test the full reset flow,
  password validation, and expired-token handling.

Required env vars for token-based tests:
  RESET_TOKEN_API  — staging endpoint that returns the latest reset token
                     for a given email (e.g., GET /api/test/reset-token?email=...)
  OR
  MAILHOG_API      — MailHog API base URL (e.g., http://localhost:8025/api/v2)
"""

import pytest

from src.crews.qa_crew import QACrew


# ---------------------------------------------------------------------------
# Forgot password page UI
# ---------------------------------------------------------------------------


class TestForgotPasswordUI:
    """Verify the forgot-password page renders and validates correctly."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.password_reset
    @pytest.mark.smoke
    def test_forgot_password_link_visible(self, reports_dir):
        """Forgot password link is visible on the login page."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_link_visible"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Link Visible"

        if not result.get("success", False):
            pytest.fail(
                "Forgot password link was not visible:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.password_reset
    @pytest.mark.smoke
    def test_forgot_password_page_loads(self, reports_dir):
        """Forgot password page loads with email input and submit button."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_page_loads"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Page Loads"

        if not result.get("success", False):
            pytest.fail(
                "Forgot password page did not load correctly:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.password_reset
    @pytest.mark.smoke
    def test_forgot_password_submit_valid_email(self, reports_dir):
        """Submitting a valid email shows a success/confirmation message."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_submit_valid_email"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Submit Valid Email"

        if not result.get("success", False):
            pytest.fail(
                "Submit valid email did not show success:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_forgot_password_submit_invalid_email(self, reports_dir):
        """Invalid email format shows a validation error."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_submit_invalid_email"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Submit Invalid Email Format"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_forgot_password_submit_empty_email(self, reports_dir):
        """Empty email field shows a validation error."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_submit_empty_email"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Submit Empty Email"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_forgot_password_unregistered_email(self, reports_dir):
        """Unregistered email shows an appropriate message."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_unregistered_email"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Unregistered Email"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_forgot_password_back_to_login(self, reports_dir):
        """Back-to-login link navigates back to the login page."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "forgot_password_back_to_login"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Forgot Password Back To Login"

        if not result.get("success", False):
            pytest.fail(
                "Back to login navigation failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Reset page (token from staging backend)
# ---------------------------------------------------------------------------


class TestResetPasswordWithToken:
    """Full reset flow using a token retrieved from the staging backend.

    These tests require either RESET_TOKEN_API or MAILHOG_API to be set
    so the generated Playwright code can fetch the token programmatically.
    """

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.password_reset
    @pytest.mark.smoke
    def test_reset_page_loads_with_token(self, reports_dir):
        """Reset page loads with new-password and confirm-password fields."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_page_loads_with_token"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Page Loads With Token"

        if not result.get("success", False):
            pytest.fail(
                "Reset page did not load with token:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.password_reset
    @pytest.mark.smoke
    def test_reset_password_success(self, reports_dir):
        """Full happy path: request reset, get token, set new password, verify."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_password_success"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Full Flow Success"

        if not result.get("success", False):
            pytest.fail(
                "Full password reset flow failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_reset_password_mismatch(self, reports_dir):
        """Mismatched passwords show a validation error."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_password_mismatch"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Mismatch Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_reset_password_too_short(self, reports_dir):
        """Password below minimum length shows a validation error."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_password_too_short"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Too Short Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_reset_password_empty_fields(self, reports_dir):
        """Empty password fields show validation errors."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_password_empty_fields"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Empty Fields Validation"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.password_reset
    @pytest.mark.regression
    def test_reset_password_expired_token(self, reports_dir):
        """Expired or invalid token shows an error with option to request a new one."""
        result = self.qa_crew.run_test_scenario(
            "password_reset", "reset_password_expired_token"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Reset Password Expired Token"

        if not result.get("success", False):
            pytest.fail(
                "Expired token handling failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Config sanity check
# ---------------------------------------------------------------------------


@pytest.mark.password_reset
def test_password_reset_scenarios_exist():
    """Verify all password reset scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "password_reset" in test_data["test_scenarios"]

    expected = [
        "forgot_password_link_visible",
        "forgot_password_page_loads",
        "forgot_password_submit_valid_email",
        "forgot_password_submit_invalid_email",
        "forgot_password_submit_empty_email",
        "forgot_password_unregistered_email",
        "forgot_password_back_to_login",
        "reset_page_loads_with_token",
        "reset_password_success",
        "reset_password_mismatch",
        "reset_password_too_short",
        "reset_password_empty_fields",
        "reset_password_expired_token",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["password_reset"], (
            f"Missing scenario: {scenario}"
        )

    assert "password_reset_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
