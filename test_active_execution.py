#!/usr/bin/env python3
"""
Test script for Active Execution mode
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crews.qa_crew import QACrew  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def test_active_execution():
    """Test active execution with a simple login scenario."""

    # Set up test environment
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    if not os.environ["OPENAI_API_KEY"]:
        logger.error("OPENAI_API_KEY not set!")
        return

    # Create test scenario
    scenario = {
        "name": "Active Execution Test - Login",
        "description": "Test active iterative execution with login flow",
        "steps": [
            "Navigate to login page at https://stg-home.aisquare.studio/login",
            "Enter email 'test@example.com' in the email input field",
            "Enter password 'password123' in the password input field",
            "Click the login button",
            "Verify the page URL contains '/dashboard'",
        ],
        "metadata": {
            "flow_name": "active_test_login",
            "tier": "A",
            "area": "auth",
        }
    }

    # Create test config
    config = {
        "base_url": "https://stg-home.aisquare.studio",
        "login_url": "https://stg-home.aisquare.studio/login",
        "email": "test@example.com",
        "password": "password123",
        "headless": True,
        "timeout": 30000,
        "max_retries": 2,
    }

    logger.info("=" * 60)
    logger.info("Testing Active Execution Mode")
    logger.info("=" * 60)

    # Initialize QA crew
    qa_crew = QACrew()

    # Run active execution
    result = qa_crew.run_active_autoqa_scenario(scenario, config)

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Completed Steps: {result.get('completed_steps', 0)}/{result.get('total_steps', 0)}")
    logger.info(f"Failed Steps: {result.get('failed_steps', 0)}")
    logger.info(f"Total Time: {result.get('total_execution_time', 0):.2f}s")

    if result.get("retry_summary"):
        logger.info(f"Total Retries: {result['retry_summary'].get('total_retries', 0)}")

    logger.info("\nGenerated Code:")
    logger.info("-" * 60)
    print(result.get('generated_code', 'No code generated'))
    logger.info("-" * 60)

    if result.get('discovered_selectors'):
        logger.info("\nDiscovered Selectors:")
        for elem_type, selectors in result['discovered_selectors'].items():
            logger.info(f"  {elem_type}: {len(selectors)} found")

    return result


if __name__ == "__main__":
    test_active_execution()
