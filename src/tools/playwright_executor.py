"""
Playwright Executor Tool: Custom CrewAI tool for Playwright test execution.
"""

import json
from typing import Any, Dict

from playwright.sync_api import sync_playwright

from src.utils.screenshot_handler import ScreenshotHandler


def create_playwright_executor_tool():
    """Create a Playwright executor function for CrewAI."""

    def execute_playwright_code(code: str, config: Dict[str, Any]) -> str:
        """
        Execute Playwright test code.

        Args:
            code: Python code containing run_test function
            config: Configuration dictionary with URLs, credentials, etc.

        Returns:
            JSON string with execution results
        """
        # Initialize screenshot handler
        screenshot_handler = ScreenshotHandler()
        scenario_name = config.get("scenario_name", "test")

        try:
            result = {"success": False, "message": "", "error": "", "screenshot_path": None}

            browser = None
            page = None

            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=config.get("headless", False))
                page = browser.new_page()

                # Set viewport
                page.set_viewport_size({"width": 1280, "height": 720})

                # Create safe execution environment
                exec_globals = {"page": page, "config": config, "assert": safe_assert}

                try:
                    # Execute the code (define the function)
                    exec(code, exec_globals)

                    # Call the run_test function
                    exec_globals["run_test"](page, config)

                    # Capture success screenshot
                    screenshot_path = screenshot_handler.capture_screenshot(
                        page, ScreenshotHandler.SUCCESS, scenario_name
                    )

                    result.update(
                        {
                            "success": True,
                            "message": "Test executed successfully",
                            "screenshot_path": screenshot_path,
                        }
                    )

                except AssertionError as e:
                    result.update(
                        {
                            "success": False,
                            "error": f"Assertion failed: {str(e)}",
                            "message": "Test assertion failed",
                        }
                    )

                    # Capture failure screenshot
                    failure_screenshot = screenshot_handler.capture_screenshot(
                        page, ScreenshotHandler.FAILURE, scenario_name
                    )
                    if failure_screenshot:
                        result["screenshot_path"] = failure_screenshot

                except Exception as e:
                    result.update(
                        {"success": False, "error": str(e), "message": "Test execution failed"}
                    )

                    # Capture error screenshot
                    error_screenshot = screenshot_handler.capture_screenshot(
                        page, ScreenshotHandler.ERROR, scenario_name
                    )
                    if error_screenshot:
                        result["screenshot_path"] = error_screenshot

                # Close browser after all screenshots are taken
                browser.close()

        except Exception as outer_error:
            # Handle any outer exceptions (playwright setup issues, etc.)
            result.update(
                {
                    "success": False,
                    "error": f"Playwright execution error: {str(outer_error)}",
                    "message": "Failed to initialize browser or playwright",
                }
            )

        return json.dumps(result, indent=2)

    return execute_playwright_code


def safe_assert(condition, message="Assertion failed"):
    """Safe assertion function with detailed error messages."""
    if not condition:
        raise AssertionError(message)
