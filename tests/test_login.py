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
    
    def test_valid_login(self, reports_dir):
        """Test successful login with valid credentials."""
        result = self.qa_crew.run_test_scenario('login', 'valid_login')
        
        # Check that the test was executed
        assert result is not None
        assert 'scenario' in result
        assert result['scenario']['name'] == 'Valid Login Test'
        
        print(f"\\nTest Result: {result['crew_result']}")
    
    def test_invalid_login(self, reports_dir):
        """Test failed login with invalid credentials."""
        result = self.qa_crew.run_test_scenario('login', 'invalid_login')
        
        # Check that the test was executed
        assert result is not None
        assert 'scenario' in result
        assert result['scenario']['name'] == 'Invalid Login Test'
        
        print(f"\\nTest Result: {result['crew_result']}")
    
    def test_all_login_scenarios(self, reports_dir):
        """Run all login test scenarios."""
        results = self.qa_crew.run_all_login_tests()
        
        # Check that both scenarios were executed
        assert 'valid_login' in results
        assert 'invalid_login' in results
        
        print(f"\\nAll Login Tests Results:")
        for scenario, result in results.items():
            print(f"  {scenario}: {'✅ Success' if not result.get('error') else '❌ Failed'}")


if __name__ == "__main__":
    # Run tests directly if this file is executed
    pytest.main([__file__, "-v"])
