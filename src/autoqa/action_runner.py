#!/usr/bin/env python3
"""
GitHub Action Runner for AutoQA
Executes in target repository context while using AISquare-Studio-QA components
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add action components to path - must be before other src imports
action_path = Path(os.getenv("ACTION_PATH", "."))
sys.path.insert(0, str(action_path))

# noqa comments tell flake8 these imports are intentionally after path manipulation
from src.autoqa.action_reporter import ActionReporter  # noqa: E402
from src.autoqa.cross_repo_manager import CrossRepoManager  # noqa: E402
from src.autoqa.parser import AutoQAParser  # noqa: E402
from src.crews.qa_crew import QACrew  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


class ActionRunner:
    """Main runner for GitHub Action execution in target repository"""

    def __init__(self):
        self.target_repo = os.getenv("TARGET_REPOSITORY")
        self.target_workspace = Path(os.getenv("GITHUB_WORKSPACE"))
        self.action_path = Path(os.getenv("ACTION_PATH"))

        # Initialize components
        self.parser = AutoQAParser()
        self.qa_crew = QACrew()
        self.cross_repo = CrossRepoManager(
            target_workspace=self.target_workspace, action_path=self.action_path
        )
        self.reporter = ActionReporter()

        # Environment configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            "github_token": os.getenv("GITHUB_TOKEN"),
            "openai_api_key": os.getenv(
                "OPENAI_API_KEY"
            ),  # Accessed from repository secrets automatically
            "target_repo_path": os.getenv("TARGET_REPO_PATH", "."),
            "staging_url": os.getenv("STAGING_URL"),
            "staging_email": os.getenv("STAGING_EMAIL", "test@example.com"),
            "staging_password": os.getenv("STAGING_PASSWORD", "password123"),
            "git_user_name": os.getenv("GIT_USER_NAME", "AutoQA Bot"),
            "git_user_email": os.getenv("GIT_USER_EMAIL", "rabia.tahirr@opengrowth.com"),
            "pr_body": os.getenv("PR_BODY", ""),
            "test_directory": os.getenv("TEST_DIRECTORY", "tests/generated"),
            "run_existing_tests": True,  # Always run existing tests
        }

        return config

    def execute(self) -> Dict[str, Any]:
        """Main execution flow for AutoQA action"""
        try:
            logger.info(f"AutoQA Action starting for repository: {self.target_repo}")

            # Validate required configuration
            if not self.config["openai_api_key"]:
                return self._set_outputs(
                    {
                        "test_generated": "false",
                        "error": "OPENAI_API_KEY not found in repository secrets",
                    }
                )

            if not self.config["staging_url"]:
                logger.warning("STAGING_URL not provided, using default for testing")
                # Use default staging URL for testing
                self.config["staging_url"] = "https://stg-home.aisquare.studio"

            # Step 1: Check for AutoQA tag
            if not self.parser.has_autoqa_tag(self.config["pr_body"]):
                logger.info("No AutoQA tag found in PR description")
                return self._set_outputs(
                    {"test_generated": "false", "message": "No AutoQA tag found"}
                )

            # Step 2: Parse test steps
            steps = self.parser.parse_test_steps(self.config["pr_body"])
            logger.info(f"Parsed {len(steps)} test steps from AutoQA description")

            # Step 3: Generate test using CrewAI
            logger.info("Generating test code with CrewAI...")
            generation_result = self._generate_test_code(steps)

            if not generation_result["success"]:
                return self._handle_generation_failure(generation_result)

            # Step 4: Execute test on staging
            logger.info("Executing generated test on staging...")
            execution_result = self._execute_test(generation_result["code"])

            if not execution_result["success"]:
                return self._handle_execution_failure(execution_result)

            # Step 5: Commit test to target repository
            logger.info("Committing generated test to target repository...")
            test_file_path = self.cross_repo.commit_test_file(
                code=generation_result["code"],
                steps=steps,
                metadata=generation_result.get("metadata", {}),
            )

            # Step 6: Run existing tests if requested
            suite_results = {}
            if self.config["run_existing_tests"]:
                logger.info("Running full test suite...")
                suite_results = self._run_test_suite()

            # Step 7: Generate PR comment with results
            logger.info("Generating PR comment with results...")
            self.reporter.create_pr_comment(
                generation_result=generation_result,
                execution_result=execution_result,
                suite_results=suite_results,
                test_file_path=str(test_file_path),
            )

            # Step 8: Set outputs and create summary
            return self._set_outputs(
                {
                    "test_generated": "true",
                    "test_file_path": str(test_file_path),
                    "test_results": json.dumps(execution_result),
                    "suite_results": json.dumps(suite_results),
                    "generation_metadata": json.dumps(generation_result.get("metadata", {})),
                    "screenshot_path": execution_result.get("screenshot_path", ""),
                }
            )

        except Exception as e:
            logger.error(f"AutoQA Action failed: {str(e)}")
            return self._set_outputs({"test_generated": "false", "error": str(e)})

    def _generate_test_code(self, steps: List[str]) -> Dict[str, Any]:
        """Generate test code using CrewAI components"""
        try:
            # Convert steps to scenario format
            scenario = self.parser.steps_to_scenario(steps)

            # Use existing QA crew to generate code
            result = self.qa_crew.run_autoqa_scenario(scenario)

            return {
                "success": result.get("success", False),
                "code": result.get("generated_code", ""),
                "metadata": {
                    "steps": steps,
                    "scenario": scenario,
                    "generated_at": result.get("timestamp", ""),
                    "validation_result": result.get("validation_result", ""),
                },
            }

        except Exception as e:
            return {"success": False, "error": f"CrewAI generation failed: {str(e)}"}

    def _execute_test(self, test_code: str) -> Dict[str, Any]:
        """Execute generated test on staging environment"""
        try:
            # Validate required config
            if not self.config.get("staging_url"):
                return {"success": False, "error": "STAGING_URL is required but not provided"}

            # Create test configuration for staging
            base_url = self.config["staging_url"].rstrip("/")
            test_config = {
                "base_url": base_url,
                "login_url": f"{base_url}/login",
                "email": self.config.get("staging_email", "test@example.com"),
                "password": self.config.get("staging_password", "password123"),
                "headless": True,
                "timeout": 30000,
            }

            # Execute using existing executor
            result = self.qa_crew.execute_generated_test(test_code, test_config)

            return result

        except Exception as e:
            return {"success": False, "error": f"Test execution failed: {str(e)}"}

    def _run_test_suite(self) -> Dict[str, Any]:
        """Run full test suite in target repository"""
        try:
            # Discover tests in target repository
            test_files = self.cross_repo.discover_tests()

            if not test_files:
                return {"message": "No existing tests found"}

            # Execute test suite using pytest
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    str(self.target_workspace / self.config["test_directory"]),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=test_results.json",
                ],
                cwd=self.target_workspace,
                capture_output=True,
                text=True,
            )

            # Parse results
            results_file = self.target_workspace / "test_results.json"
            if results_file.exists():
                with open(results_file, "r") as f:
                    suite_data = json.load(f)

                return {
                    "success": result.returncode == 0,
                    "total_tests": len(test_files),
                    "passed": suite_data.get("summary", {}).get("passed", 0),
                    "failed": suite_data.get("summary", {}).get("failed", 0),
                    "execution_time": suite_data.get("duration", 0),
                }

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except Exception as e:
            return {"success": False, "error": f"Test suite execution failed: {str(e)}"}

    def _handle_generation_failure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test generation failure"""
        logger.error(f"Test generation failed: {result.get('error', 'Unknown error')}")
        return self._set_outputs(
            {"test_generated": "false", "error": result.get("error", "Test generation failed")}
        )

    def _handle_execution_failure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test execution failure"""
        logger.error(f"Test execution failed: {result.get('error', 'Unknown error')}")
        return self._set_outputs(
            {
                "test_generated": "false",
                "error": result.get("error", "Test execution failed"),
                "test_results": json.dumps(result),
            }
        )

    def _set_outputs(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Set GitHub Action outputs"""
        # Set outputs for GitHub Actions
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                for key, value in outputs.items():
                    # Escape multiline values
                    if "\n" in str(value):
                        f.write(f"{key}<<EOF\n{value}\nEOF\n")
                    else:
                        f.write(f"{key}={value}\n")

        # Also log for visibility
        logger.info("Action Outputs:")
        for key, value in outputs.items():
            logger.info(f"  {key}: {value}")

        return outputs


def main():
    """Main entry point for GitHub Action"""
    runner = ActionRunner()
    result = runner.execute()

    # Exit with appropriate code
    if result.get("test_generated") == "false" and "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
