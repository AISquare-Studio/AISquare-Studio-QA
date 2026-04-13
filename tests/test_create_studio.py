"""
Studio creation tests using CrewAI + Playwright.
"""

import pytest

from src.crews.qa_crew import QACrew


class TestCreateStudio:
    """Test class for studio creation functionality."""

    def setup_method(self):
        """Setup method called before each test."""
        self.qa_crew = QACrew()

    @pytest.mark.studio
    @pytest.mark.smoke
    def test_create_studio_basic(self, reports_dir):
        """Test that a new studio can be created successfully."""
        result = self.qa_crew.run_test_scenario("create_studio", "create_studio_basic")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Studio Test"

        if not result.get("success", False):
            pytest.fail(
                "Create studio test failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

        print(f"\nTest Result: {result['execution_result']}")

    @pytest.mark.studio
    @pytest.mark.regression
    def test_create_studio_empty_name(self, reports_dir):
        """Test that creating a studio without a name shows a validation error."""
        result = self.qa_crew.run_test_scenario("create_studio", "create_studio_empty_name")

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Create Studio With Empty Name Test"

        print(f"\nTest Result: {result.get('execution_result', 'No execution result')}")


@pytest.mark.studio
def test_create_studio_scenarios_exist():
    """Test that create studio scenarios are properly configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "test_scenarios" in test_data
    assert "create_studio" in test_data["test_scenarios"]
    assert "create_studio_basic" in test_data["test_scenarios"]["create_studio"]
    assert "create_studio_empty_name" in test_data["test_scenarios"]["create_studio"]

    # Verify selectors are defined
    assert "create_studio_page" in test_data["selectors"]
    assert "studio_name_input" in test_data["selectors"]["create_studio_page"]
    assert "submit_button" in test_data["selectors"]["create_studio_page"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
