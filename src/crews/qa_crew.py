"""
QA Crew: Main orchestration of CrewAI agents for test automation.
"""

from crewai import Agent, Task, Crew
from src.agents.planner_agent import PlannerAgent
from src.agents.executor_agent import ExecutorAgent
from src.tools.playwright_executor import create_playwright_executor_tool
from typing import Dict, Any
import yaml
import os
import json
from pathlib import Path


class QACrew:
    """Main crew that orchestrates test planning and execution."""
    
    def __init__(self):
        self.planner_agent_wrapper = PlannerAgent()
        self.executor_agent_wrapper = ExecutorAgent()
        self.playwright_executor = create_playwright_executor_tool()
        
        # Initialize the actual CrewAI agents
        self.planner_agent = self.planner_agent_wrapper.agent
        self.executor_agent = self.executor_agent_wrapper.agent
    
    def load_test_data(self) -> Dict[str, Any]:
        """Load test scenarios and selectors from YAML file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "test_data.yaml"
        
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def load_environment_config(self) -> Dict[str, Any]:
        """Load environment configuration from .env file."""
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            'login_url': os.getenv('STAGING_LOGIN_URL', 'https://example.com/login'),
            'base_url': os.getenv('STAGING_URL', 'https://example.com'),
            'valid_email': os.getenv('VALID_EMAIL', 'test@example.com'),
            'valid_password': os.getenv('VALID_PASSWORD', 'password123'),
            'invalid_email': os.getenv('INVALID_EMAIL', 'invalid@example.com'),
            'invalid_password': os.getenv('INVALID_PASSWORD', 'wrongpassword'),
            'headless': os.getenv('HEADLESS_MODE', 'false').lower() == 'true',
            'timeout': int(os.getenv('TIMEOUT', '30000'))
        }
    
    def run_test_scenario(self, scenario_type: str, scenario_name: str) -> Dict[str, Any]:
        """
        Run a specific test scenario.
        
        Args:
            scenario_type: Type of scenario (e.g., 'login')
            scenario_name: Name of specific scenario (e.g., 'valid_login')
            
        Returns:
            Test execution results
        """
        # Load test data and environment config
        test_data = self.load_test_data()
        env_config = self.load_environment_config()
        
        # Get the specific scenario
        scenario = test_data['test_scenarios'][scenario_type][scenario_name]
        selectors = test_data['selectors']['login_page']
        
        # Create test configuration
        test_config = env_config.copy()
        test_config.update({
            'scenario_name': scenario_name,
            'scenario_type': scenario_type
        })
        
        # Set credentials based on scenario
        if scenario_name == 'valid_login':
            test_config.update({
                'email': test_config['valid_email'],
                'password': test_config['valid_password']
            })
        elif scenario_name == 'invalid_login':
            test_config.update({
                'email': test_config['valid_email'],  # Use valid email but invalid password
                'password': test_config['invalid_password']
            })
        
        # Step 1: Generate test code using Planner Agent
        print(f"🤖 Generating test code for: {scenario['name']}")
        code_prompt = self.planner_agent_wrapper.generate_test_code(scenario, selectors)
        
        # Create planning task
        planning_task = Task(
            description=code_prompt,
            expected_output="Playwright Python code for the test scenario",
            agent=self.planner_agent
        )
        
        # Create a simple crew for code generation
        planning_crew = Crew(
            agents=[self.planner_agent],
            tasks=[planning_task],
            verbose=True
        )
        
        # Generate the code
        generated_code = planning_crew.kickoff()
        
        # Step 2: Validate and execute the code
        print(f"🔒 Validating generated code...")
        is_safe, validation_message = self.executor_agent_wrapper.validate_code_safety(str(generated_code))
        
        if not is_safe:
            return {
                'scenario': scenario,
                'config': test_config,
                'success': False,
                'error': f"Code validation failed: {validation_message}",
                'generated_code': str(generated_code)
            }
        
        print(f"✅ Code validation passed")
        print(f"🎭 Executing test scenario...")
        
        # Step 3: Execute the validated code
        execution_result = self.playwright_executor(str(generated_code), test_config)
        
        # Parse execution result
        try:
            execution_data = json.loads(execution_result) if isinstance(execution_result, str) else execution_result
        except:
            execution_data = {'success': False, 'error': 'Failed to parse execution result', 'raw_result': str(execution_result)}
        
        return {
            'scenario': scenario,
            'config': test_config,
            'generated_code': str(generated_code),
            'validation_result': validation_message,
            'execution_result': execution_data,
            'success': execution_data.get('success', False)
        }
    
    def run_all_login_tests(self) -> Dict[str, Any]:
        """Run all login test scenarios."""
        results = {}
        
        login_scenarios = ['valid_login', 'invalid_login']
        
        for scenario_name in login_scenarios:
            print(f"\\n{'='*50}")
            print(f"Running scenario: {scenario_name}")
            print(f"{'='*50}")
            
            try:
                result = self.run_test_scenario('login', scenario_name)
                results[scenario_name] = result
                
                print(f"✅ Scenario {scenario_name} completed")
                
            except Exception as e:
                print(f"❌ Scenario {scenario_name} failed: {str(e)}")
                results[scenario_name] = {
                    'error': str(e),
                    'success': False
                }
        
        return results
