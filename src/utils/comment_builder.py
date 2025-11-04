"""
Comment Builder for GitHub PR Comments

Handles the construction of markdown-formatted comment content
for AutoQA test results to be posted on GitHub Pull Requests.
"""

from datetime import datetime
from typing import Any, Dict, List


class CommentBuilder:
    """Builds markdown comment content for PR comments"""

    def __init__(self, target_repo: str = None, pr_number: str = None, github_run_id: str = None):
        """
        Initialize comment builder with GitHub context

        Args:
            target_repo: GitHub repository in format 'owner/repo'
            pr_number: Pull request number
            github_run_id: GitHub Actions run ID for artifact links
        """
        self.target_repo = target_repo
        self.pr_number = pr_number
        self.github_run_id = github_run_id

    def build_comment_body(
        self,
        generation_result: Dict[str, Any],
        execution_result: Dict[str, Any],
        suite_results: Dict[str, Any],
        test_file_path: str,
        screenshot_sections: Dict[str, str] = None,
    ) -> str:
        """
        Build comprehensive comment body with all sections

        Args:
            generation_result: Test generation metadata
            execution_result: Test execution results
            suite_results: Full test suite results
            test_file_path: Path to generated test file
            screenshot_sections: Pre-built screenshot markdown sections

        Returns:
            Complete markdown comment body
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine overall status
        overall_status = "✅ SUCCESS" if execution_result.get("success", False) else "❌ FAILED"
        status_emoji = "✅" if execution_result.get("success", False) else "❌"

        # Build sections
        steps_section = self.build_steps_section(
            generation_result.get("metadata", {}).get("steps", [])
        )
        results_section = self.build_results_section(execution_result, suite_results)
        artifacts_section = self.build_artifacts_section(test_file_path, screenshot_sections)

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

<!-- AutoQA-Comment-Marker -->
"""

        return comment_body.strip()

    def build_steps_section(self, steps: List[str]) -> str:
        """
        Build the test steps section

        Args:
            steps: List of test step descriptions

        Returns:
            Formatted markdown section
        """
        if not steps:
            return "### 📋 Test Steps\n*No steps found*"

        steps_list = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

        return f"""### 📋 Test Steps Generated
{steps_list}"""

    def build_results_section(
        self, execution_result: Dict[str, Any], suite_results: Dict[str, Any]
    ) -> str:
        """
        Build the results section with execution details

        Args:
            execution_result: Individual test execution result
            suite_results: Full test suite results (if available)

        Returns:
            Formatted markdown section
        """
        # Individual test result
        test_status = "✅ PASSED" if execution_result.get("success", False) else "❌ FAILED"
        test_time = execution_result.get("execution_time", 0)

        results = f"""### 🧪 Test Execution Results
- **Generated Test:** {test_status}
- **Execution Time:** {test_time:.2f}s"""

        # Suite results if available
        if suite_results and suite_results.get("total_tests", 0) > 0:
            total = suite_results.get("total_tests", 0)
            passed = suite_results.get("passed", 0)
            suite_time = suite_results.get("execution_time", 0)

            results += f"""
- **Full Test Suite:** {passed}/{total} passed
- **Suite Execution Time:** {suite_time:.2f}s"""

        # Error details if failed
        if not execution_result.get("success", False):
            error = execution_result.get("error", "Unknown error")
            results += f"""

**Error Details:**
```
{error}
```"""

        return results

    def build_artifacts_section(
        self, test_file_path: str, screenshot_sections: Dict[str, str] = None
    ) -> str:
        """
        Build the artifacts section with file and screenshot links

        Args:
            test_file_path: Path to generated test file
            screenshot_sections: Dict with 'success' and 'error' screenshot markdown

        Returns:
            Formatted markdown section
        """
        artifacts = f"""### 📁 Generated Artifacts
- 📄 **Test File:** `{test_file_path}`"""

        # Add link to GitHub Actions artifacts
        if self.github_run_id and self.target_repo:
            artifacts_url = (
                f"https://github.com/{self.target_repo}/actions/runs/{self.github_run_id}"
            )
            artifacts += f"\n- 📦 **[View All Artifacts & Screenshots]({artifacts_url})**"

        # Add screenshot sections if provided
        if screenshot_sections:
            if screenshot_sections.get("success"):
                artifacts += f"\n\n### 📸 Success Screenshot\n{screenshot_sections['success']}"
            if screenshot_sections.get("error"):
                artifacts += f"\n\n### 🚨 Error Screenshot\n{screenshot_sections['error']}"

        return artifacts

    def build_header(self, status: str, test_file_path: str) -> str:
        """
        Build compact header for comment

        Args:
            status: Overall test status
            test_file_path: Path to generated test file

        Returns:
            Formatted header line
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        status_emoji = "✅" if "success" in status.lower() else "❌"

        return (
            f"## {status_emoji} AutoQA Test Generation Results\n**Status:** {status} |"
            f" **Generated:** `{test_file_path}` | **Time:** {timestamp}"
        )
