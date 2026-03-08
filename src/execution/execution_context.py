"""
ExecutionContext: Maintains state and context between test steps during active execution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionContext:
    """
    Tracks browser state, discovered selectors, and execution history
    between test steps during active execution.
    """

    def __init__(self, page: Page, config: Dict[str, Any]):
        """
        Initialize execution context.

        Args:
            page: Playwright page instance
            config: Test configuration dict
        """
        self.page = page
        self.config = config
        self.step_history: List[Dict[str, Any]] = []
        self.discovered_selectors: Dict[str, List[str]] = {}
        self.current_url: str = ""
        self.current_title: str = ""
        self.execution_metadata: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
        }

    def capture_state(self) -> Dict[str, Any]:
        """
        Capture current page state including URL, title, and available selectors.

        Returns:
            Dict containing current page state
        """
        try:
            self.current_url = self.page.url
            self.current_title = self.page.title()

            # Capture page state
            state = {
                "url": self.current_url,
                "title": self.current_title,
                "timestamp": datetime.now().isoformat(),
                "discovered_selectors": self.discovered_selectors.copy(),
                "step_count": len(self.step_history),
            }

            logger.info(f"Captured state - URL: {self.current_url}, Title: {self.current_title}")
            return state

        except Exception as e:
            logger.error(f"Failed to capture page state: {str(e)}")
            return {
                "url": "unknown",
                "title": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def add_discovered_selectors(self, element_type: str, selectors: List[str]):
        """
        Add discovered selectors for a specific element type.

        Args:
            element_type: Type of element (e.g., 'button', 'input', 'link')
            selectors: List of CSS selectors found
        """
        if element_type not in self.discovered_selectors:
            self.discovered_selectors[element_type] = []

        # Add unique selectors
        for selector in selectors:
            if selector not in self.discovered_selectors[element_type]:
                self.discovered_selectors[element_type].append(selector)

        logger.info(
            f"Added {len(selectors)} selectors for {element_type}. "
            f"Total for type: {len(self.discovered_selectors[element_type])}"
        )

    def record_step_result(
        self,
        step_number: int,
        description: str,
        code: str,
        success: bool,
        execution_time: float,
        error: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ):
        """
        Record the result of a step execution.

        Args:
            step_number: Step index (1-based)
            description: Step description
            code: Generated code for this step
            success: Whether step succeeded
            execution_time: Time taken in seconds
            error: Error message if failed
            screenshot_path: Path to screenshot if captured
        """
        step_result = {
            "step_number": step_number,
            "description": description,
            "code": code,
            "success": success,
            "execution_time": execution_time,
            "url_before": self.current_url,
            "url_after": self.page.url,
            "timestamp": datetime.now().isoformat(),
        }

        if error:
            step_result["error"] = error
        if screenshot_path:
            step_result["screenshot_path"] = screenshot_path

        self.step_history.append(step_result)

        # Update metadata
        self.execution_metadata["total_steps"] += 1
        if success:
            self.execution_metadata["successful_steps"] += 1
        else:
            self.execution_metadata["failed_steps"] += 1

        # Update current state
        self.current_url = self.page.url

        logger.info(
            f"Step {step_number} recorded: {'✓ SUCCESS' if success else '✗ FAILED'} "
            f"({execution_time:.2f}s)"
        )

    def get_previous_steps_summary(self) -> str:
        """
        Generate a summary of previous steps for context.

        Returns:
            Formatted string summarizing previous steps
        """
        if not self.step_history:
            return "No previous steps executed yet."

        summary_lines = ["Previous steps executed:"]
        for step in self.step_history[-5:]:  # Last 5 steps
            status = "✓" if step["success"] else "✗"
            summary_lines.append(f"  {status} Step {step['step_number']}: {step['description']}")

        return "\n".join(summary_lines)

    def get_available_selectors_for_element(self, element_hint: str) -> List[str]:
        """
        Get available selectors that might match the element hint.

        Args:
            element_hint: Description of element (e.g., "button", "email input")

        Returns:
            List of potentially matching selectors
        """
        # Simple keyword matching for now
        matching_selectors = []
        hint_lower = element_hint.lower()

        for element_type, selectors in self.discovered_selectors.items():
            if element_type.lower() in hint_lower or hint_lower in element_type.lower():
                matching_selectors.extend(selectors)

        return matching_selectors

    def get_context_for_agent(self) -> Dict[str, Any]:
        """
        Get comprehensive context for the agent to generate next step.

        Returns:
            Dict containing all relevant context
        """
        return {
            "current_state": {
                "url": self.current_url,
                "title": self.current_title,
            },
            "step_count": len(self.step_history),
            "previous_steps": self.get_previous_steps_summary(),
            "discovered_selectors": self.discovered_selectors,
            "success_rate": (
                f"{self.execution_metadata['successful_steps']}/"
                f"{self.execution_metadata['total_steps']}"
                if self.execution_metadata["total_steps"] > 0
                else "0/0"
            ),
            "last_successful_step": self._get_last_successful_step(),
        }

    def _get_last_successful_step(self) -> Optional[Dict[str, Any]]:
        """Get the last successful step result."""
        for step in reversed(self.step_history):
            if step["success"]:
                return step
        return None

    def has_failed_steps(self) -> bool:
        """Check if any steps have failed."""
        return self.execution_metadata["failed_steps"] > 0

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get final execution summary.

        Returns:
            Dict containing execution statistics and results
        """
        return {
            "metadata": self.execution_metadata,
            "total_steps": self.execution_metadata["total_steps"],
            "successful_steps": self.execution_metadata["successful_steps"],
            "failed_steps": self.execution_metadata["failed_steps"],
            "success_rate": (
                self.execution_metadata["successful_steps"] / self.execution_metadata["total_steps"]
                if self.execution_metadata["total_steps"] > 0
                else 0
            ),
            "final_url": self.current_url,
            "step_history": self.step_history,
            "discovered_selectors": self.discovered_selectors,
        }

    def clear(self):
        """Clear execution context for new test run."""
        self.step_history.clear()
        self.discovered_selectors.clear()
        self.execution_metadata = {
            "start_time": datetime.now().isoformat(),
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
        }
        logger.info("Execution context cleared")
