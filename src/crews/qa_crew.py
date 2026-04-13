"""
QA Crew: Main orchestration of CrewAI agents for test automation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from crewai import Crew, Task
from crewai_tools import DirectoryReadTool, FileReadTool

from src.agents.executor_agent import ExecutorAgent
from src.agents.planner_agent import PlannerAgent
from src.execution.iterative_orchestrator import IterativeTestOrchestrator
from src.tools.playwright_executor import create_playwright_executor_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QACrew:
    """Main crew that orchestrates test planning and execution."""

    def __init__(self, model_name=None):
        # Configure LLM - use gpt-4.1 by default or from environment
        from crewai import LLM

        model = model_name or os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4.1")

        llm = LLM(
            model=model,
            timeout=300,  # 5 minutes
            max_retries=3,
        )

        # Initialize agent wrappers with configured LLM
        target_repo_path = os.getenv("TARGET_REPO_PATH", ".")
        self.file_read_tool = FileReadTool(root_dir=target_repo_path)
        self.directory_read_tool = DirectoryReadTool(root_dir=target_repo_path)

        self.planner_agent_wrapper = PlannerAgent(
            llm=llm, tools=[self.file_read_tool, self.directory_read_tool]
        )
        self.executor_agent_wrapper = ExecutorAgent(llm=llm)
        self.playwright_executor = create_playwright_executor_tool()

        # Initialize iterative orchestrator for active execution
        self.iterative_orchestrator = IterativeTestOrchestrator(
            llm=llm, tools=[self.file_read_tool, self.directory_read_tool]
        )

        # Initialize the actual CrewAI agents
        self.planner_agent = self.planner_agent_wrapper.agent
        self.executor_agent = self.executor_agent_wrapper.agent

    def load_test_data(self) -> Dict[str, Any]:
        """Load test scenarios and selectors from YAML file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "test_data.yaml"

        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def load_environment_config(self) -> Dict[str, Any]:
        """Load environment configuration from .env file."""
        try:
            from dotenv import load_dotenv

            load_dotenv()  # This will fail silently if no .env file exists
        except ImportError:
            pass  # dotenv might not be available in action environment

        # Use staging environment configuration
        base_url = os.getenv("STAGING_URL", "https://stg-home.aisquare.studio")
        # Remove trailing slash to ensure consistent URL construction
        base_url = base_url.rstrip("/")

        return {
            "base_url": base_url,
            "login_url": f"{base_url}/login",
            "valid_email": os.getenv("STAGING_EMAIL", "test@example.com"),
            "valid_password": os.getenv("STAGING_PASSWORD", "password123"),
            "invalid_email": os.getenv("INVALID_EMAIL", "invalid@example.com"),
            "invalid_password": os.getenv("INVALID_PASSWORD", "wrongpassword"),
            "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
            "timeout": int(os.getenv("TIMEOUT", "30000")),
        }

    def _clean_generated_code(self, raw_code: str) -> str:
        """Clean generated code by removing markdown blocks and extra formatting."""
        code = str(raw_code).strip()

        # Remove markdown code blocks
        if code.startswith("```python"):
            code = code[9:]  # Remove ```python
        elif code.startswith("```"):
            code = code[3:]  # Remove ```

        if code.endswith("```"):
            code = code[:-3]  # Remove trailing ```

        # Remove any remaining backticks at the start/end
        code = code.strip("`").strip()

        # Split into lines and clean each line
        lines = code.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip empty lines at the beginning
            if not cleaned_lines and not line.strip():
                continue
            cleaned_lines.append(line)

        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)

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
        scenario = test_data["test_scenarios"][scenario_type][scenario_name]

        # Look up selectors by scenario type, fall back to login_page for backwards compatibility
        selector_key = f"{scenario_type}_page"
        selectors = test_data["selectors"].get(selector_key, test_data["selectors"].get("login_page", {}))

        # Create test configuration
        test_config = env_config.copy()
        test_config.update({"scenario_name": scenario_name, "scenario_type": scenario_type})

        # Default to valid credentials (most scenarios need an authenticated user)
        test_config.update(
            {"email": test_config["valid_email"], "password": test_config["valid_password"]}
        )

        # Override with invalid credentials for specific login scenarios
        if scenario_type == "login" and scenario_name == "invalid_login":
            test_config["password"] = test_config["invalid_password"]

        # Step 1: Generate test code using Planner Agent
        logger.info(f"Generating test code for: {scenario['name']}")
        code_prompt = self.planner_agent_wrapper.generate_test_code(scenario, selectors)

        # Create planning task
        planning_task = Task(
            description=code_prompt,
            expected_output="Playwright Python code for the test scenario",
            agent=self.planner_agent,
        )

        # Create a simple crew for code generation
        planning_crew = Crew(agents=[self.planner_agent], tasks=[planning_task], verbose=True)

        # Generate the code
        generated_code_raw = planning_crew.kickoff()

        # Clean the generated code by removing markdown blocks
        generated_code = self._clean_generated_code(str(generated_code_raw))

        # Step 2: Validate and execute the code
        logger.info("Validating generated code...")
        is_safe, validation_message = self.executor_agent_wrapper.validate_code_safety(
            generated_code
        )

        if not is_safe:
            return {
                "scenario": scenario,
                "config": test_config,
                "success": False,
                "error": f"Code validation failed: {validation_message}",
                "generated_code": generated_code,
            }

        logger.info("Code validation passed")
        logger.info("Executing test scenario...")

        # Step 3: Execute the validated code
        execution_result = self.playwright_executor(generated_code, test_config)

        # Parse execution result
        try:
            execution_data = (
                json.loads(execution_result)
                if isinstance(execution_result, str)
                else execution_result
            )
        except Exception:
            execution_data = {
                "success": False,
                "error": "Failed to parse execution result",
                "raw_result": str(execution_result),
            }

        return {
            "scenario": scenario,
            "config": test_config,
            "generated_code": generated_code,
            "validation_result": validation_message,
            "execution_result": execution_data,
            "success": execution_data.get("success", False),
        }

    def run_autoqa_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run AutoQA scenario with generated steps."""
        logger.info(f"Running AutoQA scenario: {scenario.get('name', 'Unknown')}")

        # Load selectors (use login selectors as default for now)
        test_data = self.load_test_data()
        selectors = test_data["selectors"]["login_page"]

        # Don't load environment config here - it will be passed from action_runner

        # Create basic test configuration that will be updated by action_runner
        test_config = {
            "scenario_name": "autoqa_generated",
            "scenario_type": "autoqa",
        }

        try:
            # Generate test code using existing Planner Agent
            logger.info("Generating test code for AutoQA scenario...")
            code_prompt = self.planner_agent_wrapper.generate_test_code(scenario, selectors)

            # Create planning task
            planning_task = Task(
                description=code_prompt,
                expected_output="Playwright Python code for AutoQA scenario",
                agent=self.planner_agent,
            )

            # Create crew for code generation
            planning_crew = Crew(agents=[self.planner_agent], tasks=[planning_task], verbose=True)

            # Generate the code
            generated_code_raw = planning_crew.kickoff()
            generated_code = self._clean_generated_code(str(generated_code_raw))

            # Validate the code
            logger.info("Validating generated code...")
            is_safe, validation_message = self.executor_agent_wrapper.validate_code_safety(
                generated_code
            )

            if not is_safe:
                return {
                    "success": False,
                    "error": f"Code validation failed: {validation_message}",
                    "generated_code": generated_code,
                    "validation_result": validation_message,
                }

            logger.info("Code validation passed")

            return {
                "success": True,
                "generated_code": generated_code,
                "validation_result": validation_message,
                "scenario": scenario,
                "config": test_config,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"AutoQA scenario failed: {str(e)}")
            return {"success": False, "error": str(e), "scenario": scenario}

    def run_active_autoqa_scenario(
        self, scenario: Dict[str, Any], config: Dict[str, Any], existing_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run AutoQA scenario with active iterative execution.

        This method uses the new IterativeTestOrchestrator to execute steps
        one at a time with real-time context awareness, selector discovery,
        and automatic retry logic.

        Args:
            scenario: Test scenario with steps
            config: Test configuration including URLs and credentials
            existing_code: Optional existing test code for context

        Returns:
            Execution result with generated code and execution details
        """
        logger.info(f"Running ACTIVE AutoQA scenario: {scenario.get('name', 'Unknown')}")
        logger.info("Using iterative execution with real-time context")
        if existing_code:
            logger.info("Using existing test code for context")

        try:
            # Extract steps from scenario
            steps = scenario.get("steps", [])

            if not steps:
                return {
                    "success": False,
                    "error": "No steps provided in scenario",
                }

            # Run active execution
            result = self.iterative_orchestrator.run_active_execution(
                steps=steps, config=config, scenario=scenario, existing_code=existing_code
            )

            # Enhance result with scenario metadata
            result["scenario"] = scenario
            result["config"] = config
            result["timestamp"] = datetime.now().isoformat()
            result["execution_mode"] = "active_iterative"

            return result

        except Exception as e:
            logger.error(f"Active AutoQA execution failed: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

            return {
                "success": False,
                "error": str(e),
                "scenario": scenario,
                "execution_mode": "active_iterative",
            }

    def execute_generated_test(self, test_code: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generated test code with configuration."""
        logger.info("Executing generated test...")

        try:
            # Execute using the playwright executor tool
            execution_result = self.playwright_executor(test_code, test_config)

            # Parse execution result
            try:
                execution_data = (
                    json.loads(execution_result)
                    if isinstance(execution_result, str)
                    else execution_result
                )
            except Exception:
                execution_data = {
                    "success": False,
                    "error": "Failed to parse execution result",
                    "raw_result": str(execution_result),
                }

            return execution_data

        except Exception as e:
            return {"success": False, "error": f"Test execution failed: {str(e)}"}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests (existing + generated)."""
        logger.info("Running complete test suite...")

        results = {
            "login_tests": {},
            "generated_tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }

        # Run existing login scenarios
        login_scenarios = ["valid_login", "invalid_login"]

        for scenario_name in login_scenarios:
            try:
                result = self.run_test_scenario("login", scenario_name)
                results["login_tests"][scenario_name] = result

                results["summary"]["total"] += 1
                if result.get("success", False):
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

            except Exception as e:
                results["login_tests"][scenario_name] = {"error": str(e), "success": False}
                results["summary"]["total"] += 1
                results["summary"]["failed"] += 1

        return results

    def run_all_login_tests(self) -> Dict[str, Any]:
        """Run all login test scenarios."""
        results = {}

        login_scenarios = ["valid_login", "invalid_login"]

        for scenario_name in login_scenarios:
            logger.info(f"\\n{'='*50}")
            logger.info(f"Running scenario: {scenario_name}")
            logger.info(f"{'='*50}")

            try:
                result = self.run_test_scenario("login", scenario_name)
                results[scenario_name] = result

                logger.info(f"Scenario {scenario_name} completed")

            except Exception as e:
                logger.error(f"Scenario {scenario_name} failed: {str(e)}")
                results[scenario_name] = {"error": str(e), "success": False}

        return results
