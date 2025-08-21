"""
Action Reporter for GitHub Actions
Handles reporting and status updates for AutoQA action
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime


class ActionReporter:
    """Handles reporting and status updates for GitHub Actions"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.pr_number = os.getenv('PR_NUMBER')
        self.target_repo = os.getenv('TARGET_REPOSITORY')
    
    def create_pr_comment(self, generation_result: Dict[str, Any], 
                         execution_result: Dict[str, Any],
                         suite_results: Dict[str, Any],
                         test_file_path: str) -> None:
        """Create or update PR comment with AutoQA results"""
        
        comment_body = self._build_comment_body(
            generation_result, execution_result, suite_results, test_file_path
        )
        
        # Set as GitHub Actions step summary
        self._set_step_summary(comment_body)
        
        # Print for GitHub Actions logs
        print("📝 AutoQA Results Summary:")
        print(comment_body)
    
    def _build_comment_body(self, generation_result: Dict[str, Any],
                           execution_result: Dict[str, Any],
                           suite_results: Dict[str, Any],
                           test_file_path: str) -> str:
        """Build comprehensive comment body"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Determine overall status
        overall_status = "✅ SUCCESS" if execution_result.get('success', False) else "❌ FAILED"
        status_emoji = "✅" if execution_result.get('success', False) else "❌"
        
        # Build steps section
        steps = generation_result.get('metadata', {}).get('steps', [])
        steps_section = self._build_steps_section(steps)
        
        # Build results section
        results_section = self._build_results_section(execution_result, suite_results)
        
        # Build artifacts section
        artifacts_section = self._build_artifacts_section(test_file_path, execution_result)
        
        comment_body = f"""
## {status_emoji} AutoQA Test Generation Results

**Status:** {overall_status}  
**Timestamp:** {timestamp}  
**Generated Test:** `{test_file_path}`  
**Environment:** Staging  

{steps_section}

{results_section}

{artifacts_section}

### 🔗 Action Details
- **Repository:** {self.target_repo}
- **PR:** #{self.pr_number}
- **Action:** AISquare Studio AutoQA

---
*🤖 This test was automatically generated and executed by AutoQA*
"""
        
        return comment_body.strip()
    
    def _build_steps_section(self, steps: List[str]) -> str:
        """Build the test steps section"""
        if not steps:
            return "### 📋 Test Steps\n*No steps found*"
        
        steps_list = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
        
        return f"""### 📋 Test Steps Generated
{steps_list}"""
    
    def _build_results_section(self, execution_result: Dict[str, Any], 
                              suite_results: Dict[str, Any]) -> str:
        """Build the results section"""
        
        # Individual test result
        test_status = "✅ PASSED" if execution_result.get('success', False) else "❌ FAILED"
        test_time = execution_result.get('execution_time', 0)
        
        results = f"""### 🧪 Test Execution Results
- **Generated Test:** {test_status}
- **Execution Time:** {test_time:.2f}s"""
        
        # Suite results if available
        if suite_results and suite_results.get('total_tests', 0) > 0:
            total = suite_results.get('total_tests', 0)
            passed = suite_results.get('passed', 0)
            failed = suite_results.get('failed', 0)
            suite_time = suite_results.get('execution_time', 0)
            
            results += f"""
- **Full Test Suite:** {passed}/{total} passed
- **Suite Execution Time:** {suite_time:.2f}s"""
        
        # Error details if failed
        if not execution_result.get('success', False):
            error = execution_result.get('error', 'Unknown error')
            results += f"""

**Error Details:**
```
{error}
```"""
        
        return results
    
    def _build_artifacts_section(self, test_file_path: str, 
                                execution_result: Dict[str, Any]) -> str:
        """Build the artifacts section"""
        
        artifacts = f"""### 📁 Generated Artifacts
- 📄 **Test File:** `{test_file_path}`"""
        
        # Screenshot if available
        screenshot_path = execution_result.get('screenshot_path')
        if screenshot_path:
            artifacts += f"\n- 📸 **Screenshot:** `{screenshot_path}`"
        
        # Error screenshot if available
        error_screenshot = execution_result.get('error_screenshot_path')
        if error_screenshot:
            artifacts += f"\n- 🚨 **Error Screenshot:** `{error_screenshot}`"
        
        return artifacts
    
    def _set_step_summary(self, content: str) -> None:
        """Set GitHub Actions step summary"""
        github_step_summary = os.getenv('GITHUB_STEP_SUMMARY')
        if github_step_summary:
            with open(github_step_summary, 'w') as f:
                f.write(content)
    
    def set_action_outputs(self, outputs: Dict[str, str]) -> None:
        """Set GitHub Action outputs"""
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                for key, value in outputs.items():
                    # Handle multiline values
                    if '\n' in str(value):
                        f.write(f"{key}<<EOF\n{value}\nEOF\n")
                    else:
                        f.write(f"{key}={value}\n")
    
    def create_check_run(self, status: str, conclusion: str, 
                        title: str, summary: str) -> None:
        """Create a check run for the action (future enhancement)"""
        # This would use GitHub API to create check runs
        # For now, just log the information
        print(f"📊 Check Run: {status} - {conclusion}")
        print(f"Title: {title}")
        print(f"Summary: {summary}")
    
    def report_error(self, error_message: str, details: Dict[str, Any] = None) -> None:
        """Report error with GitHub Actions formatting"""
        print(f"::error::{error_message}")
        
        if details:
            print("Error Details:")
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def report_warning(self, warning_message: str) -> None:
        """Report warning with GitHub Actions formatting"""
        print(f"::warning::{warning_message}")
    
    def report_notice(self, notice_message: str) -> None:
        """Report notice with GitHub Actions formatting"""
        print(f"::notice::{notice_message}")


# Testing
if __name__ == "__main__":
    reporter = ActionReporter()
    
    # Mock test data
    generation_result = {
        'success': True,
        'metadata': {
            'steps': [
                "Navigate to login page",
                "Enter valid credentials",
                "Click login button",
                "Verify dashboard appears"
            ]
        }
    }
    
    execution_result = {
        'success': True,
        'execution_time': 15.5,
        'screenshot_path': 'reports/screenshots/test_success.png'
    }
    
    suite_results = {
        'total_tests': 5,
        'passed': 5,
        'failed': 0,
        'execution_time': 45.2
    }
    
    test_file_path = "tests/autoQA/test_autoqa_login_20250821_1430.py"
    
    print("Testing ActionReporter...")
    reporter.create_pr_comment(generation_result, execution_result, suite_results, test_file_path)