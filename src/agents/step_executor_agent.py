"""
Step Executor Agent: Generates and executes single test steps with context awareness.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from crewai import Agent, Crew, Task
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.execution.execution_context import ExecutionContext
from src.tools.dom_inspector import DOMInspectorTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StepExecutorAgent:
    """
    Agent responsible for generating and executing individual test steps.
    Works with live page context to discover selectors and validate actions.
    """

    def __init__(self, llm=None):
        """
        Initialize step executor agent.

        Args:
            llm: Language model configuration
        """
        self.agent = Agent(
            role="Iterative Test Step Executor",
            goal="Generate and execute individual test steps with real-time page context",
            backstory="""You are an expert test automation engineer who excels at writing 
            precise, reliable Playwright code for individual test steps. You analyze the current 
            page state, discover the best selectors, and generate code that works on the first try. 
            You use real-time information about the page to make intelligent decisions about 
            selectors and waits.""",
            verbose=False,  # Reduce console spam
            allow_delegation=False,
            llm=llm,
        )

    def generate_step_code(
        self,
        step_description: str,
        step_number: int,
        page: Page,
        context: ExecutionContext,
        config: Dict[str, Any],
        accumulated_code: List[Dict] = None,  # New: previously generated code
        crew: Crew = None,  # New: persistent crew instance
    ) -> str:
        """
        Generate Playwright code for a single step using real page context.

        Args:
            step_description: Natural language description of the step
            step_number: Current step number (1-based)
            page: Playwright page instance
            context: Execution context with history
            config: Test configuration
            accumulated_code: List of previously generated code steps
            crew: Persistent Crew instance with memory

        Returns:
            Generated Python code for this step
        """
        try:
            logger.info(f"Generating code for step {step_number}: {step_description}")

            # Discover current page selectors
            inspector = DOMInspectorTool(page)
            page_structure = inspector.get_page_structure()

            # Try to find best selector for this step
            suggested_selector = inspector.find_best_selector_for_element(step_description)
            
            # Format accumulated code for context
            previous_code_context = self._format_accumulated_code(accumulated_code or [])

            # Build context-aware prompt with accumulated code
            prompt = self._build_step_prompt(
                step_description=step_description,
                step_number=step_number,
                page_structure=page_structure,
                suggested_selector=suggested_selector,
                execution_context=context.get_context_for_agent(),
                config=config,
                previous_code=previous_code_context,  # New: pass formatted code
            )

            # Use persistent crew if provided, otherwise create temporary one
            if crew is not None:
                # Create task for persistent crew (benefits from memory)
                code_generation_task = Task(
                    description=prompt,
                    expected_output="Single Python statement or block for this step only",
                    agent=self.agent,
                )
                
                # Execute on persistent crew
                generated_code = crew.kickoff_for_each([code_generation_task])
            else:
                # Fallback: create temporary crew (for backward compatibility)
                code_generation_task = Task(
                    description=prompt,
                    expected_output="Single Python statement or block for this step only",
                    agent=self.agent,
                )
                
                temp_crew = Crew(agents=[self.agent], tasks=[code_generation_task], verbose=False)
                generated_code = temp_crew.kickoff()

            # Clean the code
            cleaned_code = self._clean_generated_code(str(generated_code))

            logger.info(f"Generated code for step {step_number}:\n{cleaned_code}")
            return cleaned_code

        except Exception as e:
            logger.error(f"Failed to generate code for step {step_number}: {str(e)}")
            # Return a simple comment as fallback
            return f"# Error generating step {step_number}: {str(e)}"

    def execute_step(
        self,
        step_code: str,
        step_number: int,
        page: Page,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a single step's code and capture results.

        Args:
            step_code: Python code to execute
            step_number: Step number
            page: Playwright page instance
            config: Test configuration

        Returns:
            Execution result dict with success, error, timing
        """
        logger.info(f"Executing step {step_number}...")

        start_time = time.time()
        result = {
            "success": False,
            "step_number": step_number,
            "execution_time": 0,
            "url_before": page.url,
            "url_after": page.url,
        }

        try:
            # Create execution namespace with page and config
            exec_namespace = {
                "page": page,
                "config": config,
                "TimeoutError": PlaywrightTimeoutError,
            }

            # Execute the step code
            exec(step_code, exec_namespace)

            # Capture results
            result["success"] = True
            result["url_after"] = page.url
            result["execution_time"] = time.time() - start_time

            logger.info(
                f"✓ Step {step_number} executed successfully "
                f"({result['execution_time']:.2f}s)"
            )

        except PlaywrightTimeoutError as e:
            result["error"] = f"Timeout: {str(e)}"
            result["error_type"] = "timeout"
            result["execution_time"] = time.time() - start_time
            logger.error(f"✗ Step {step_number} timed out: {str(e)}")

        except Exception as e:
            result["error"] = str(e)
            result["error_type"] = "execution_error"
            result["execution_time"] = time.time() - start_time
            logger.error(f"✗ Step {step_number} failed: {str(e)}")

        return result

    def validate_step_success(
        self,
        step_description: str,
        execution_result: Dict[str, Any],
        page: Page,
    ) -> Tuple[bool, str]:
        """
        Validate if a step executed successfully based on expected outcome.

        Args:
            step_description: Original step description
            execution_result: Result from execute_step
            page: Current page state

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not execution_result["success"]:
            return False, f"Step failed: {execution_result.get('error', 'Unknown error')}"

        # For now, basic validation - can be enhanced
        if "verify" in step_description.lower() or "assert" in step_description.lower():
            # Verification steps - check if no error was raised
            return True, "Verification step completed without errors"

        return True, "Step executed successfully"

    def _format_accumulated_code(self, accumulated_code: List[Dict]) -> str:
        """
        Format previously generated code for context.
        
        Args:
            accumulated_code: List of previous step dicts
            
        Returns:
            Formatted string with previous code
        """
        if not accumulated_code:
            return "# This is the first step - no previous code"
        
        lines = ["# Previously generated code (for context):"]
        for item in accumulated_code:
            lines.append(f"\n# Step {item['step_number']}: {item['description']}")
            lines.append(item['code'])
            if item.get('url_after'):
                lines.append(f"# After this step, URL was: {item['url_after']}")
        
        lines.append("\n# Now generate the next step...")
        return "\n".join(lines)

    def _build_step_prompt(
        self,
        step_description: str,
        step_number: int,
        page_structure: Dict[str, Any],
        suggested_selector: Optional[str],
        execution_context: Dict[str, Any],
        config: Dict[str, Any],
        previous_code: str = "",  # New parameter
    ) -> str:
        """Build context-aware prompt for step code generation."""

        selector_info = (
            f"\nSUGGESTED SELECTOR: {suggested_selector}"
            if suggested_selector
            else "\nNo specific selector found - infer from page structure"
        )

        prompt = f"""
You are building a Playwright test step-by-step. Here's the context of what you've done so far:

{previous_code}

CURRENT STEP ({step_number}): {step_description}

CURRENT PAGE STATE:
- URL: {page_structure.get('url', 'unknown')}
- Title: {page_structure.get('title', 'unknown')}
- Buttons available: {page_structure.get('buttons_count', 0)}
- Inputs available: {page_structure.get('inputs_count', 0)}
- Links available: {page_structure.get('links_count', 0)}
{selector_info}

EXECUTION CONTEXT:
{execution_context.get('previous_steps', 'First step')}

RULES FOR THIS STEP:
1. Generate ONLY the code for THIS step - not the entire test
2. You CAN reference the page state from previous steps
3. Keep consistency with previous code style and selectors
4. Use the 'page' variable (already available in scope)
5. Use the 'config' variable for any configuration values
6. If suggested selector is provided, USE IT
7. Always add appropriate waits (wait_for_selector, wait_for_load_state)
8. For navigation: use page.goto(url)
9. For clicks: use page.click(selector)
10. For input: use page.fill(selector, value)
11. For assertions: use standard Python assert statements
12. Add a wait_for_timeout(1000) after actions that trigger changes

IMPORTANT:
- Return ONLY executable Python code (no markdown, no explanations)
- Code should be 1-5 lines maximum for this single step
- Do NOT include function definitions or imports
- Do NOT repeat previous steps
- Build on the context established by previous steps

Example patterns (use similar style to previous steps if applicable):
- Navigation: page.goto(config['login_url'])
              page.wait_for_load_state('networkidle')
- Click: page.click("button[data-testid='submit']")
         page.wait_for_timeout(1000)
- Input: page.fill("input[name='email']", config['email'])

Generate code for: {step_description}
"""

        return prompt

    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code by removing markdown and extra formatting."""
        code = str(code).strip()

        # Remove markdown code blocks
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]

        if code.endswith("```"):
            code = code[:-3]

        code = code.strip("`").strip()

        # Remove common explanatory phrases that might sneak in
        code_lines = []
        for line in code.split("\n"):
            line = line.strip()
            # Skip empty lines and comments that are explanations
            if line and not line.startswith("# Here") and not line.startswith("# This"):
                code_lines.append(line)

        return "\n".join(code_lines)
