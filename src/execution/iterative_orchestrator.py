"""
Iterative Test Orchestrator: Coordinates step-by-step test execution with real-time context.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import Crew
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from src.agents.step_executor_agent import StepExecutorAgent
from src.execution.execution_context import ExecutionContext
from src.execution.retry_handler import RetryHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IterativeTestOrchestrator:
    """
    Orchestrates iterative test execution where each step is generated,
    executed, and validated before moving to the next step.
    """

    def __init__(
        self,
        llm=None,
        max_retries: int = 2,
        screenshot_dir: Optional[Path] = None,
        tools: List[Any] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            llm: Language model configuration
            max_retries: Maximum retry attempts per step
            screenshot_dir: Directory to save screenshots
            tools: List of tools to provide to the agent
        """
        self.llm = llm
        self.step_executor = StepExecutorAgent(llm=llm, tools=tools)
        self.retry_handler = RetryHandler(max_retries=max_retries)
        self.screenshot_dir = screenshot_dir or Path("reports/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Initialize persistent Crew with memory enabled
        self.crew = Crew(
            agents=[self.step_executor.agent],
            tasks=[],  # Start empty, add tasks dynamically
            memory=True,  # Enable built-in memory
            verbose=False,  # Reduce console spam
            process="sequential"
        )

        # Track accumulated code for explicit context passing
        self.accumulated_code = []

    def run_active_execution(
        self,
        steps: List[str],
        config: Dict[str, Any],
        scenario: Dict[str, Any],
        existing_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute test steps iteratively with active context awareness.

        Args:
            steps: List of step descriptions
            config: Test configuration
            scenario: Scenario information
            existing_code: Optional existing test code for context

        Returns:
            Complete execution result with generated test code
        """
        logger.info("=" * 60)
        logger.info("Starting Active Iterative Execution")
        if existing_code:
            logger.info("Using existing test code for context")
        logger.info(f"Total steps: {len(steps)}")
        logger.info("=" * 60)

        overall_start = time.time()

        # Clear accumulated code for new test
        self.accumulated_code = []
        logger.info("Starting fresh execution - memory will accumulate naturally")

        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch(
                headless=config.get("headless", True),
                slow_mo=500,  # Slow down for better observation
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(self.screenshot_dir / "videos") if config.get("record_video") else None,
            )

            page = context.new_page()

            # Initialize execution context
            exec_context = ExecutionContext(page, config)

            # Initialize persistent execution globals for variable sharing between steps
            # This allows variables defined in one step (like timestamp) to be used in later steps
            execution_globals = {
                "page": page,
                "config": config,
                "TimeoutError": PlaywrightTimeoutError,
                # Add common modules that might be needed
            }

            # Execute steps iteratively
            generated_steps = []
            final_test_code_lines = []

            # Add imports and function definition
            final_test_code_lines.append("# Auto-generated test with active execution")
            final_test_code_lines.append("")
            final_test_code_lines.append("def run_test(page, config):")
            final_test_code_lines.append("    '''")
            final_test_code_lines.append(f"    Test: {scenario.get('name', 'Generated Test')}")
            final_test_code_lines.append(f"    Generated with active execution - {len(steps)} steps")
            final_test_code_lines.append("    '''")
            final_test_code_lines.append("")

            for i, step_description in enumerate(steps, start=1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"STEP {i}/{len(steps)}: {step_description}")
                logger.info(f"{'=' * 60}")

                # Capture current state
                current_state = exec_context.capture_state()
                logger.info(f"Current URL: {current_state['url']}")

                # Generate and execute this step
                step_result = self._execute_step_with_retry(
                    step_description=step_description,
                    step_number=i,
                    page=page,
                    exec_context=exec_context,
                    config=config,
                    accumulated_code=self.accumulated_code,
                    existing_code=existing_code,
                    execution_globals=execution_globals,
                )

                # Record result
                exec_context.record_step_result(
                    step_number=i,
                    description=step_description,
                    code=step_result["code"],
                    success=step_result["success"],
                    execution_time=step_result["execution_time"],
                    error=step_result.get("error"),
                    screenshot_path=step_result.get("screenshot_path"),
                )

                # Add to generated steps
                generated_steps.append(step_result)

                # Add to accumulated code on success
                if step_result["success"]:
                    self.accumulated_code.append({
                        'step_number': i,
                        'description': step_description,
                        'code': step_result['code'],
                        'url_after': page.url
                    })

                # Add code to final test (with proper indentation)
                if step_result["success"]:
                    final_test_code_lines.append(f"    # Step {i}: {step_description}")
                    for line in step_result["code"].split("\n"):
                        if line.strip():
                            final_test_code_lines.append(f"    {line}")
                    final_test_code_lines.append("")
                else:
                    # Add as comment if failed
                    final_test_code_lines.append(f"    # Step {i} FAILED: {step_description}")
                    final_test_code_lines.append(f"    # Error: {step_result.get('error', 'Unknown')}")
                    final_test_code_lines.append("")

                # Decide whether to continue
                if not step_result["success"]:
                    logger.warning(f"Step {i} failed. Stopping execution.")
                    break

                # Small delay between steps
                time.sleep(0.5)

            # Take final screenshot
            final_screenshot = None
            try:
                final_screenshot = str(
                    self.screenshot_dir / f"final_state_{int(time.time())}.png"
                )
                page.screenshot(path=final_screenshot)
                logger.info(f"Final screenshot saved: {final_screenshot}")
            except Exception as e:
                logger.error(f"Failed to capture final screenshot: {str(e)}")

            # Close browser
            browser.close()

        # Compile results
        overall_time = time.time() - overall_start
        execution_summary = exec_context.get_execution_summary()

        # Build final test code
        final_test_code = "\n".join(final_test_code_lines)

        result = {
            "success": execution_summary["failed_steps"] == 0,
            "generated_code": final_test_code,
            "execution_summary": execution_summary,
            "total_steps": len(steps),
            "completed_steps": execution_summary["total_steps"],
            "successful_steps": execution_summary["successful_steps"],
            "failed_steps": execution_summary["failed_steps"],
            "total_execution_time": overall_time,
            "step_details": generated_steps,
            "final_screenshot": final_screenshot,
            "retry_summary": self.retry_handler.get_retry_summary(),
            "discovered_selectors": execution_summary["discovered_selectors"],
        }

        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Steps: {result['total_steps']}")
        logger.info(f"Completed: {result['completed_steps']}")
        logger.info(f"Successful: {result['successful_steps']}")
        logger.info(f"Failed: {result['failed_steps']}")
        logger.info(f"Total Time: {overall_time:.2f}s")
        logger.info(f"Retries: {self.retry_handler.get_retry_summary()['total_retries']}")
        logger.info(f"Success Rate: {execution_summary['success_rate'] * 100:.1f}%")
        logger.info("=" * 60)

        return result

    def _execute_step_with_retry(
        self,
        step_description: str,
        step_number: int,
        page: Any,
        exec_context: ExecutionContext,
        config: Dict[str, Any],
        accumulated_code: List[Dict] = None,
        existing_code: Optional[str] = None,
        execution_globals: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single step with retry logic.

        Args:
            step_description: Step description
            step_number: Step number
            page: Playwright page
            exec_context: Execution context
            config: Test config
            accumulated_code: Previously generated code
            existing_code: Optional existing test code for context
            execution_globals: Optional persistent globals for variable sharing

        Returns:
            Step execution result
        """
        attempt = 0
        last_error = None
        last_code = None

        while attempt <= self.retry_handler.max_retries:
            try:
                # Generate code for this step
                if attempt == 0:
                    # First attempt - generate fresh
                    step_code = self.step_executor.generate_step_code(
                        step_description=step_description,
                        step_number=step_number,
                        page=page,
                        context=exec_context,
                        config=config,
                        accumulated_code=accumulated_code or [],
                        crew=self.crew,
                        existing_code=existing_code,
                    )
                else:
                    # Retry - analyze failure and modify
                    logger.info(f"Retry attempt {attempt} for step {step_number}")

                    analysis = self.retry_handler.analyze_failure(
                        step_description=step_description,
                        step_code=last_code,
                        error=last_error["error"],
                        error_type=last_error["error_type"],
                        page=page,
                    )

                    logger.info(f"Failure analysis: {analysis['likely_cause']}")
                    logger.info(f"Suggestions: {', '.join(analysis['suggestions'][:2])}")

                    # Generate retry code
                    step_code = self.retry_handler.generate_retry_code(
                        original_code=last_code,
                        analysis=analysis,
                        retry_attempt=attempt,
                    )

                    self.retry_handler.increment_retry(step_number)

                last_code = step_code

                # Execute the step
                execution_result = self.step_executor.execute_step(
                    step_code=step_code,
                    step_number=step_number,
                    page=page,
                    config=config,
                    execution_globals=execution_globals,
                )

                # If successful, return result
                if execution_result["success"]:
                    execution_result["code"] = step_code
                    execution_result["attempts"] = attempt + 1
                    return execution_result

                # If failed, store error and retry
                last_error = execution_result
                attempt += 1

            except Exception as e:
                logger.error(f"Unexpected error in step execution: {str(e)}")
                last_error = {
                    "error": str(e),
                    "error_type": "unexpected",
                }
                attempt += 1

        # All retries exhausted
        logger.error(f"Step {step_number} failed after {attempt} attempts")

        return {
            "success": False,
            "code": last_code or f"# Failed to generate code for: {step_description}",
            "error": last_error.get("error", "Unknown error") if last_error else "Failed to execute",
            "error_type": last_error.get("error_type", "unknown") if last_error else "unknown",
            "execution_time": 0,
            "attempts": attempt,
        }

    def reset(self):
        """Reset orchestrator state for new execution."""
        self.retry_handler.reset()
        self.accumulated_code = []

        # Reset crew memory
        if hasattr(self.crew, 'memory') and self.crew.memory:
            try:
                self.crew.memory.reset()
            except Exception as e:
                logger.warning(f"Could not reset crew memory: {str(e)}")

        logger.info("Orchestrator reset")
