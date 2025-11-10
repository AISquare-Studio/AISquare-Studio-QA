"""
Executor Agent: Safely executes generated Playwright test code.
"""

import ast
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from crewai import Agent


class ExecutorAgent:
    """Agent responsible for safely executing generated Playwright test code."""

    def __init__(self, llm=None):
        self.agent = Agent(
            role="Test Execution Specialist",
            goal="Safely execute Playwright test code and provide detailed results",
            backstory="""You are a test execution expert who ensures that generated test code
            runs safely and reliably. You validate code before execution, handle errors gracefully,
            and provide comprehensive feedback on test results including screenshots and logs.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,  # Pass the configured LLM
        )

    def validate_code_safety(self, code: str) -> Tuple[bool, str]:  # noqa: C901
        """
        Validate that the generated code is safe to execute.

        Args:
            code: Python code string to validate

        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            # Parse the code into AST
            tree = ast.parse(code)

            # Check for forbidden imports and calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_allowed_import(alias.name):
                            return False, f"Forbidden import: {alias.name}"

                elif isinstance(node, ast.ImportFrom):
                    if not self._is_allowed_import(node.module):
                        return False, f"Forbidden import from: {node.module}"

                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec", "open", "__import__"]:
                            return False, f"Forbidden function call: {node.func.id}"
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ["system", "popen", "spawn"]:
                            return False, f"Forbidden method call: {node.func.attr}"

            # Check that run_test function exists
            function_found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "run_test":
                    function_found = True
                    break

            if not function_found:
                return False, "No run_test function found in generated code"

            return True, "Code validation passed"

        except SyntaxError as e:
            return False, f"Syntax error in generated code: {str(e)}"
        except Exception as e:
            return False, f"Code validation error: {str(e)}"

    def _is_allowed_import(self, module_name: str) -> bool:
        """Check if an import is allowed."""
        if module_name is None:
            return False

        allowed_modules = ["playwright", "playwright.sync_api", "time", "datetime", "re"]

        return any(module_name.startswith(allowed) for allowed in allowed_modules)

    def execute_test(self, code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the validated test code.

        Args:
            code: Validated Python code to execute
            config: Test configuration including URLs and credentials

        Returns:
            Test execution results dictionary
        """
        # Validate code first
        is_safe, validation_message = self.validate_code_safety(code)
        if not is_safe:
            return {
                "success": False,
                "error": f"Code validation failed: {validation_message}",
                "screenshot_path": None,
                "execution_time": 0,
            }

        try:
            # Create temporary file for the test code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
                # Write the complete test script
                test_script = self._create_test_script(code, config)
                temp_file.write(test_script)
                temp_file_path = temp_file.name

            # Execute the test script
            result = subprocess.run(
                ["python", temp_file_path],
                capture_output=True,
                text=True,
                timeout=config.get("timeout", 60),
            )

            # Parse the result
            if result.returncode == 0:
                try:
                    output_data = json.loads(result.stdout)
                    return output_data
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "message": "Test completed successfully",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr or result.stdout,
                    "returncode": result.returncode,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timed out"}
        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}"}
        finally:
            # Clean up temporary file
            try:
                Path(temp_file_path).unlink()
            except Exception:
                pass

    def _create_test_script(self, code: str, config: Dict[str, Any]) -> str:
        """
        Create the complete test script with imports and execution logic.
        Loads template from file and replaces placeholders.
        """
        # Load template from file
        template_path = Path(__file__).parent.parent / "templates" / "test_execution_template.py"

        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            raise RuntimeError(f"Test execution template not found at: {template_path}")

        # Replace placeholders with actual values
        script = template.replace("{{USER_CODE}}", code)
        script = script.replace("{{SCENARIO_NAME}}", repr(config.get("scenario_name", "test")))
        script = script.replace("{{CONFIG}}", repr(config))
        script = script.replace("{{HEADLESS}}", str(config.get("headless", True)))

        return script
