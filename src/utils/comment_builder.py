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
        metadata: Dict[str, Any] = None,
        screenshot_sections: Dict[str, str] = None,
    ) -> str:
        """
        Build comprehensive comment body with all sections

        Args:
            generation_result: Test generation metadata
            execution_result: Test execution results
            suite_results: Full test suite results
            test_file_path: Path to generated test file
            metadata: AutoQA metadata with flow_name, tier, area, etag
            screenshot_sections: Pre-built screenshot markdown sections

        Returns:
            Complete markdown comment body
        """
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).astimezone().isoformat()

        # Determine overall status
        overall_status = "✅ SUCCESS" if execution_result.get("success", False) else "❌ FAILED"
        status_emoji = "✅" if execution_result.get("success", False) else "❌"

        # Extract metadata (from parameter or generation_result)
        if metadata is None:
            metadata = generation_result.get("metadata", {})

        # Build sections
        metadata_section = self.build_metadata_section(metadata)
        steps_section = self.build_steps_section(metadata.get("steps", []))
        results_section = self.build_results_section(execution_result, suite_results)
        artifacts_section = self.build_artifacts_section(test_file_path, screenshot_sections)

        comment_body = f"""
## {status_emoji} AutoQA Test Generation Results

**Status:** {overall_status}
**Timestamp:** {timestamp}
**Generated Test:** `{test_file_path}`
**Environment:** Staging

{metadata_section}

{steps_section}

{results_section}

{artifacts_section}

### 🔗 Action Details
- **Repository:** {self.target_repo}
- **PR:** #{self.pr_number}
- **Action:** AISquare Studio AutoQA

---
*🤖 This test was automatically generated and executed by AutoQA*
*For policy details, see: `.github/autoqa-policy.yml`*

<!-- AutoQA-Comment-Marker -->
"""

        return comment_body.strip()

    def build_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """
        Build the metadata section

        Args:
            metadata: AutoQA metadata dict

        Returns:
            Formatted markdown section
        """
        flow_name = metadata.get("flow_name", "unknown")
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        etag = metadata.get("etag", "")
        
        # Optionally hide area if it's the default
        area_line = ""
        if area and area != "general":
            area_line = f"\n- **Area:** `{area}`"

        return f"""### 📊 Test Metadata
- **Flow Name:** `{flow_name}`
- **Tier:** `{tier}`{area_line}
- **ETag:** `{etag[:12]}...` (idempotency hash)"""

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
            screenshot_path = execution_result.get("screenshot_path", "")
            error_screenshot = execution_result.get("error_screenshot_path", "")
            
            results += f"""

### ❌ Test Execution Failed

**Error Details:**
```
{error}
```

**What happened:**
- ✅ Test code was generated successfully
- ❌ Test execution on staging environment failed
- 📸 Screenshot captured for debugging
- 🚫 Test file was NOT committed to repository

**Why wasn't the test committed?**
AutoQA only commits tests that pass successfully. This ensures your test suite remains clean and all tests are verified to work.

**Next Steps:**
1. 📸 **Review the failure screenshot** in the artifacts section below
2. 🔍 **Check the error message** - it shows what assertion or step failed
3. ✏️ **Update the test steps** in your PR description if needed
4. 🔄 **Push a new commit** or edit the PR description to trigger AutoQA again
5. ✅ **Once the test passes**, it will be automatically committed

**Need help?**
- Check if the staging environment is accessible
- Verify the test steps match actual UI elements
- Ensure text/selectors in steps are accurate
- Tag @TahirRabia for assistance"""

        return results

    def build_artifacts_section(
        self, test_file_path: str, screenshot_sections: Dict[str, str] = None
    ) -> str:
        """
        Build the artifacts section with file and screenshot links

        Args:
            test_file_path: Path to generated test file
            screenshot_sections: Dict with 'success', 'error', and 'artifacts_header' screenshot markdown

        Returns:
            Formatted markdown section
        """
        artifacts = f"""### 📁 Generated Test File
- 📄 **Test File:** `{test_file_path}`"""

        # Add screenshot sections if provided
        if screenshot_sections:
            # Add artifacts header with link (from action_reporter)
            if screenshot_sections.get("artifacts_header"):
                artifacts += f"\n\n{screenshot_sections['artifacts_header']}"
            
            # Add success screenshot
            if screenshot_sections.get("success"):
                artifacts += screenshot_sections['success']
            
            # Add error screenshot (for failures)
            if screenshot_sections.get("error"):
                artifacts += screenshot_sections['error']

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
