"""
Login functionality tests using CrewAI + Playwright.
"""

import pytest

from src.crews.qa_crew import QACrew


class TestLoginFunctionality:
    """Test class for login functionality."""

    def setup_method(self):
        """Setup method called before each test."""
        self.qa_crew = QACrew()

    @pytest.mark.login
    @pytest.mark.smoke
    def test_valid_login(self, reports_dir):
        """Test successful login with valid credentials."""
        result = self.qa_crew.run_test_scenario("login", "valid_login")

        # Check that the test was executed
        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Valid Login Test"

        # Check if test passed (this will help identify issues)
        if not result.get("success", False):
            pytest.fail(
                "Login test failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

        print(f"\\nTest Result: {result['execution_result']}")

    @pytest.mark.login
    @pytest.mark.smoke
    def test_invalid_login(self, reports_dir):
        """Test failed login with invalid credentials."""
        result = self.qa_crew.run_test_scenario("login", "invalid_login")

        # Check that the test was executed
        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Invalid Login Test"

        # For invalid login, we expect the test to detect the error appropriately
        print(f"\\nTest Result: {result.get('execution_result', 'No execution result')}")

    @pytest.mark.login
    @pytest.mark.regression
    def test_all_login_scenarios(self, reports_dir):
        """Run all login test scenarios."""
        results = self.qa_crew.run_all_login_tests()

        # Check that both scenarios were executed
        assert "valid_login" in results
        assert "invalid_login" in results

        print("\\nAll Login Tests Results:")
        for scenario, result in results.items():
            success_status = "✅ Success" if result.get("success", False) else "❌ Failed"
            print(f"  {scenario}: {success_status}")

            # Print any errors for debugging
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
            elif "execution_result" in result and not result["execution_result"].get(
                "success", False
            ):
                print(f"    Execution Error: {result['execution_result'].get('error', 'Unknown')}")


@pytest.mark.login
def test_framework_initialization():
    """Test that the QA framework initializes correctly."""
    qa_crew = QACrew()
    assert qa_crew is not None

    # Test that we can load test data
    test_data = qa_crew.load_test_data()
    assert "test_scenarios" in test_data
    assert "login" in test_data["test_scenarios"]

    # Test that we can load environment config
    env_config = qa_crew.load_environment_config()
    assert env_config is not None


if __name__ == "__main__":
    # Run tests directly if this file is executed
    pytest.main([__file__, "-v"])
