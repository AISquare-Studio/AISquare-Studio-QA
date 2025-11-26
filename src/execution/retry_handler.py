"""
Retry Handler: Analyzes failures and suggests corrections for step execution.
"""

import re
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page

from src.tools.dom_inspector import DOMInspectorTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetryHandler:
    """
    Handles retry logic for failed test steps.
    Analyzes errors and suggests alternative approaches.
    """

    def __init__(self, max_retries: int = 2):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts per step
        """
        self.max_retries = max_retries
        self.retry_count: Dict[int, int] = {}  # step_number -> retry_count

    def should_retry(self, step_number: int) -> bool:
        """
        Check if a step should be retried.

        Args:
            step_number: Step number to check

        Returns:
            True if retry attempts remain
        """
        current_retries = self.retry_count.get(step_number, 0)
        return current_retries < self.max_retries

    def increment_retry(self, step_number: int) -> int:
        """
        Increment retry count for a step.

        Args:
            step_number: Step number

        Returns:
            New retry count
        """
        self.retry_count[step_number] = self.retry_count.get(step_number, 0) + 1
        return self.retry_count[step_number]

    def analyze_failure(
        self,
        step_description: str,
        step_code: str,
        error: str,
        error_type: str,
        page: Page,
    ) -> Dict[str, Any]:
        """
        Analyze why a step failed and suggest corrections.

        Args:
            step_description: Original step description
            step_code: Code that failed
            error: Error message
            error_type: Type of error (timeout, execution_error, etc.)
            page: Current page state

        Returns:
            Analysis dict with suggestions
        """
        logger.info(f"Analyzing failure: {error_type}")

        analysis = {
            "error_type": error_type,
            "error_message": error,
            "likely_cause": None,
            "suggestions": [],
            "alternative_selectors": [],
        }

        # Analyze based on error type
        if error_type == "timeout":
            analysis.update(self._analyze_timeout_error(step_code, error, page, step_description))
        elif "selector" in error.lower() or "element" in error.lower():
            analysis.update(self._analyze_selector_error(step_description, step_code, page))
        else:
            analysis.update(self._analyze_generic_error(error, step_code))

        return analysis

    def generate_retry_code(
        self,
        original_code: str,
        analysis: Dict[str, Any],
        retry_attempt: int,
    ) -> str:
        """
        Generate modified code for retry attempt based on analysis.

        Args:
            original_code: Original code that failed
            analysis: Failure analysis
            retry_attempt: Current retry attempt number

        Returns:
            Modified code to retry
        """
        logger.info(f"Generating retry code (attempt {retry_attempt})")

        # Try alternative selectors if available
        if analysis.get("alternative_selectors"):
            return self._replace_selector(
                original_code, 
                analysis["alternative_selectors"][retry_attempt - 1]
            )

        # Apply suggestions
        modified_code = original_code
        for suggestion in analysis.get("suggestions", []):
            if "increase timeout" in suggestion.lower():
                modified_code = self._increase_timeout(modified_code)
            elif "add wait" in suggestion.lower():
                modified_code = self._add_wait_before(modified_code)

        return modified_code

    def _analyze_timeout_error(
        self, 
        step_code: str, 
        error: str, 
        page: Page,
        step_description: str = None
    ) -> Dict[str, Any]:
        """Analyze timeout errors."""
        # Extract selector from error or code
        selector = self._extract_selector_from_code(step_code)

        return {
            "likely_cause": "Element not found (selector mismatch) or page state not ready",
            "suggestions": [
                "Try alternative selector (prioritized)",
                "Check if element is in an iframe",
                "Verify element visibility",
                "Increase wait timeout (last resort)",
            ],
            "alternative_selectors": self._find_alternative_selectors(selector, page, step_description) if selector else []
        }

    def _analyze_selector_error(
        self, 
        step_description: str, 
        step_code: str, 
        page: Page
    ) -> Dict[str, Any]:
        """Analyze selector-related errors."""
        inspector = DOMInspectorTool(page)
        
        # Try to find better selector
        alternative = inspector.find_best_selector_for_element(step_description)
        
        alternatives = [alternative] if alternative else []
        
        # Also get other potential selectors
        discovered = inspector.discover_selectors()
        current_selector = self._extract_selector_from_code(step_code)
        
        # Add more alternatives from discovered elements
        for element_type, elements in discovered.items():
            for element in elements[:3]:  # Top 3 of each type
                sel = element.get("best_selector")
                if sel and sel != current_selector and sel not in alternatives:
                    alternatives.append(sel)

        return {
            "likely_cause": "Selector not found on current page",
            "suggestions": [
                "Try alternative selector",
                "Wait for page to fully load",
                "Check if element is in iframe",
                "Verify element is visible",
            ],
            "alternative_selectors": alternatives[:3],  # Limit to 3 alternatives
        }

    def _analyze_generic_error(self, error: str, step_code: str) -> Dict[str, Any]:
        """Analyze generic execution errors."""
        suggestions = ["Review generated code syntax", "Check page state"]

        if "assert" in error.lower():
            suggestions.append("Assertion failed - verify expected condition")
        
        if "attribute" in error.lower():
            suggestions.append("Check if element has expected attributes")

        return {
            "likely_cause": "Code execution error",
            "suggestions": suggestions,
            "alternative_selectors": [],
        }

    def _extract_selector_from_code(self, code: str) -> Optional[str]:
        """Extract CSS selector from code string."""
        # Match common Playwright selector patterns
        patterns = [
            r'\.click\(["\']([^"\']+)["\']\)',
            r'\.fill\(["\']([^"\']+)["\']\s*,',
            r'\.wait_for_selector\(["\']([^"\']+)["\']\)',
            r'\.query_selector\(["\']([^"\']+)["\']\)',
        ]

        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                return match.group(1)

        return None

    def _find_alternative_selectors(
        self, 
        original_selector: Optional[str], 
        page: Page,
        step_description: str = None
    ) -> List[str]:
        """Find alternative selectors similar to the original or matching description."""
        if not original_selector and not step_description:
            return []

        try:
            inspector = DOMInspectorTool(page)
            alternatives = []

            # If we have a description, use the smart finder first
            if step_description:
                relevant = inspector.find_relevant_elements(step_description)
                for el in relevant[:3]:
                    sel = el.get("best_selector")
                    if sel and sel != original_selector:
                        alternatives.append(sel)
            
            # Fallback to general discovery if needed
            if not alternatives:
                discovered = inspector.discover_selectors()
                for element_type, elements in discovered.items():
                    for element in elements[:2]:  # Top 2 from each type
                        selector = element.get("best_selector")
                        if selector and selector != original_selector:
                            alternatives.append(selector)

            return alternatives[:5]  # Return top 5

        except Exception as e:
            logger.error(f"Error finding alternatives: {str(e)}")
            return []

    def _replace_selector(self, code: str, new_selector: str) -> str:
        """Replace selector in code with new one."""
        # Replace in common Playwright methods
        patterns = [
            (r'(\.click\(["\'])([^"\']+)(["\'])', rf'\g<1>{new_selector}\g<3>'),
            (r'(\.fill\(["\'])([^"\']+)(["\'])', rf'\g<1>{new_selector}\g<3>'),
            (r'(\.wait_for_selector\(["\'])([^"\']+)(["\'])', rf'\g<1>{new_selector}\g<3>'),
        ]

        modified = code
        for pattern, replacement in patterns:
            modified = re.sub(pattern, replacement, modified)

        return modified

    def _increase_timeout(self, code: str) -> str:
        """Increase timeout values in code."""
        # Increase wait_for_timeout values
        code = re.sub(
            r'wait_for_timeout\((\d+)\)',
            lambda m: f'wait_for_timeout({int(m.group(1)) * 2})',
            code
        )

        # Add timeout parameter if not present
        if 'wait_for_selector' in code and 'timeout=' not in code:
            code = re.sub(
                r'wait_for_selector\(([^)]+)\)',
                r'wait_for_selector(\1, timeout=10000)',
                code
            )

        return code

    def _add_wait_before(self, code: str) -> str:
        """Add wait before action."""
        lines = code.split('\n')
        if lines:
            # Add wait before first action line
            return "page.wait_for_load_state('networkidle')\n" + code
        return code

    def get_retry_summary(self) -> Dict[str, int]:
        """Get summary of retry attempts."""
        return {
            "total_retries": sum(self.retry_count.values()),
            "steps_retried": len(self.retry_count),
            "retry_details": self.retry_count.copy(),
        }

    def reset(self):
        """Reset retry counters."""
        self.retry_count.clear()
        logger.info("Retry handler reset")
