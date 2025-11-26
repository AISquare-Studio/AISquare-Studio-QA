"""
Planner Agent: Generates Playwright test code based on natural language test scenarios.
"""

from typing import Any, Dict

from crewai import Agent


class PlannerAgent:
    """Agent responsible for generating Playwright test code from test scenarios."""

    def __init__(self, llm=None, tools=None):
        self.agent = Agent(
            role="QA Test Code Planner",
            goal="Generate robust and reliable Playwright Python code for automated testing",
            backstory="""You are a senior SDET (Software Development Engineer in Test) with extensive
            experience in web automation testing. You specialize in creating clean, maintainable,
            and reliable Playwright code that follows best practices. You always include proper
            waits, error handling, and assertions in your generated code.
            
            You have access to the source code of the application under test. 
            Use the directory_read_tool and file_read_tool to explore the codebase, 
            understand the application structure, find route definitions, and identify 
            stable selectors (like data-testid) directly from the component files.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,  # Pass the configured LLM
            tools=tools or [],
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for code generation."""
        return """
        You are a Playwright code generator. Generate ONLY Python code using Playwright sync API.

        RULES:
        1. Only import from 'playwright.sync_api'
        2. Create a function called 'run_test(page, config)'
        3. Use proper waits (page.wait_for_selector, page.wait_for_load_state)
        4. Include assertions using standard Python assert statements
        5. Handle timeouts gracefully
        6. Use the EXACT selectors provided in the AVAILABLE SELECTORS list (use first selector in each list)
        7. Add page.wait_for_timeout(5000) after clicking login button for processing time
        8. For login success verification, check if '/dashboard' is in page.url after login
        9. Add comments for key steps
        10. Return ONLY the function code, no markdown or explanations
        11. IMPORTANT: Use config['login_url'] directly - do NOT add /login to it as it's already included

        FORBIDDEN:
        - No imports other than playwright.sync_api
        - No os, subprocess, eval, exec calls
        - No file operations
        - No network requests outside of page interactions
        - Do not use selectors not provided in AVAILABLE SELECTORS

        Example structure:
        ```python
        def run_test(page, config):
            # Navigate to login page (login_url is complete URL, don't add /login)
            page.goto(config['login_url'])

            # Wait for page to load
            page.wait_for_load_state('networkidle')

            # Your test steps here

            # Assert success condition
            assert condition, "Test assertion message"
        ```

        CRITICAL: config['login_url'] contains the full URL including /login path.
        Do NOT concatenate or add /login to it.

            # Assert success condition
            assert condition, "Test assertion message"
        ```
        """

    def generate_test_code(self, scenario: Dict[str, Any], selectors: Dict[str, Any]) -> str:
        """
        Generate Playwright test code for a given scenario.

        Args:
            scenario: Test scenario details from YAML
            selectors: CSS selectors for page elements

        Returns:
            Generated Playwright code as string
        """

        # Create detailed prompt with scenario and selectors
        prompt = f"""
        {self.get_system_prompt()}

        Generate Playwright code for this test scenario:

        SCENARIO: {scenario['name']}
        DESCRIPTION: {scenario['description']}

        STEPS:
        {chr(10).join(f"- {step}" for step in scenario['steps'])}

        EXPECTED RESULT: {scenario['expected_result']}

        AVAILABLE SELECTORS:
        {chr(10).join(f"- {key}: {value}" for key, value in selectors.items())}

        Generate the run_test(page, config) function that implements these steps.
        The config parameter will contain login_url, email, password, and timeout values.
        """

        return prompt
