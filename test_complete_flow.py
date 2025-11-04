#!/usr/bin/env python3
from src.autoqa.action_reporter import ActionReporter
from src.tools.playwright_executor import create_playwright_executor_tool
import os
import json

# Set up environment
os.environ["GITHUB_WORKSPACE"] = "/Users/rabiatahir/Desktop/AISquare-Studio-QA"
os.environ["TARGET_REPOSITORY"] = "test/repo"
os.environ["PR_NUMBER"] = "123"

# Test complete flow: playwright executor -> reporter
executor = create_playwright_executor_tool()

test_code = '''
def run_test(page, config):
    page.goto("data:text/html,<h1>AutoQA Test Success</h1><p>This test passed</p>")
    page.wait_for_load_state("networkidle")
    print("Test completed successfully")
'''

config = {
    "scenario_name": "pr_comment_test",
    "headless": True,
    "timeout": 30000
}

print("🧪 Testing complete flow: execution -> screenshot -> PR comment...")

# Execute test and get result with screenshot
execution_result = json.loads(executor(test_code, config))
print(f"✅ Test executed. Screenshot: {execution_result.get('screenshot_path', 'NOT FOUND')}")

# Create reporter and test PR comment generation
reporter = ActionReporter()

generation_result = {
    "success": True,
    "metadata": {
        "steps": [
            "Navigate to test page",
            "Verify success message", 
            "Capture screenshot"
        ]
    }
}

suite_results = {"total_tests": 1, "passed": 1, "failed": 0}
test_file_path = "tests/autoqa/test_pr_comment.py"

print("\n📝 Generating PR comment with embedded screenshot...")
reporter.create_pr_comment(generation_result, execution_result, suite_results, test_file_path)