"""
Action Reporter for GitHub Actions

Orchestrates reporting and status updates for AutoQA action.
Uses composition pattern with specialized utility classes for:
- Comment building (CommentBuilder)
- Screenshot embedding (ScreenshotEmbedManager)
- GitHub API operations (GitHubCommentClient)
"""

import os
from typing import Dict, Any
from pathlib import Path
from src.utils.comment_builder import CommentBuilder
from src.utils.screenshot_handler import ScreenshotHandler
from src.utils.screenshot_embed_manager import ScreenshotEmbedManager
from src.utils.github_comment_client import GitHubCommentClient


class ActionReporter:
    """Orchestrates reporting for GitHub Actions"""
    
    def __init__(self):
        """Initialize reporter with GitHub context and utility components"""
        # GitHub context from environment
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.pr_number = os.getenv('PR_NUMBER') or self._extract_pr_number()
        self.target_repo = os.getenv('TARGET_REPOSITORY')
        self.github_workspace = Path(os.getenv('GITHUB_WORKSPACE', '.'))
        self.github_run_id = os.getenv('GITHUB_RUN_ID')
        self.github_run_number = os.getenv('GITHUB_RUN_NUMBER')
        
        # Initialize utility components
        self.screenshot_handler = ScreenshotHandler()
        
        self.comment_builder = CommentBuilder(
            target_repo=self.target_repo,
            pr_number=self.pr_number,
            github_run_id=self.github_run_id
        )
        
        self.screenshot_manager = ScreenshotEmbedManager(
            screenshot_handler=self.screenshot_handler,
            github_token=self.github_token,
            target_repo=self.target_repo,
            github_run_id=self.github_run_id,
            github_workspace=self.github_workspace
        )
        
        self.github_client = GitHubCommentClient(
            github_token=self.github_token,
            target_repo=self.target_repo
        )
    
    def _extract_pr_number(self) -> str:
        """Extract PR number from GitHub event"""
        try:
            github_ref = os.getenv('GITHUB_REF', '')
            if '/pull/' in github_ref:
                return github_ref.split('/pull/')[1].split('/')[0]
        except:
            pass
        return 'unknown'
    
    def create_pr_comment(self, generation_result: Dict[str, Any], 
                         execution_result: Dict[str, Any],
                         suite_results: Dict[str, Any],
                         test_file_path: str) -> None:
        """
        Create or update PR comment with AutoQA results
        
        Args:
            generation_result: Test generation metadata
            execution_result: Test execution results
            suite_results: Full test suite results
            test_file_path: Path to generated test file
        """
        # Process screenshots
        screenshot_sections = self._process_screenshots(execution_result)
        
        # Build comment body using CommentBuilder
        comment_body = self.comment_builder.build_comment_body(
            generation_result=generation_result,
            execution_result=execution_result,
            suite_results=suite_results,
            test_file_path=test_file_path,
            screenshot_sections=screenshot_sections
        )
        
        # Set as GitHub Actions step summary
        self._set_step_summary(comment_body)
        
        # Post to PR using GitHubCommentClient
        if self.github_token and self.pr_number and self.target_repo:
            self.github_client.post_or_update_comment(self.pr_number, comment_body)
        
        # Print for GitHub Actions logs
        print("📝 AutoQA Results Summary:")
        print(comment_body)
    
    def _process_screenshots(self, execution_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Process screenshots and generate markdown sections
        
        Args:
            execution_result: Execution results containing screenshot paths
            
        Returns:
            Dict with 'success' and 'error' screenshot markdown sections
        """
        screenshot_sections = {}
        
        # Success screenshot
        screenshot_path = execution_result.get('screenshot_path')
        if screenshot_path:
            resolved_path = self.screenshot_handler.resolve_screenshot_path(screenshot_path)
            if resolved_path and resolved_path.exists():
                embedded_screenshot = self.screenshot_manager.embed_screenshot(
                    str(resolved_path), "Success Screenshot"
                )
                if embedded_screenshot:
                    screenshot_sections['success'] = embedded_screenshot
                else:
                    # Fallback: provide artifact link
                    if self.github_run_id and self.target_repo:
                        artifacts_url = f"https://github.com/{self.target_repo}/actions/runs/{self.github_run_id}"
                        screenshot_sections['success'] = f"*Screenshot available in [GitHub Actions Artifacts]({artifacts_url})*"
            else:
                print(f"⚠️ Screenshot file not found: {screenshot_path}")
                if self.github_run_id and self.target_repo:
                    artifacts_url = f"https://github.com/{self.target_repo}/actions/runs/{self.github_run_id}"
                    screenshot_sections['success'] = f"*Screenshot available in [GitHub Actions Artifacts]({artifacts_url})*"
        
        # Error screenshot
        error_screenshot = execution_result.get('error_screenshot_path')
        if error_screenshot:
            error_file = self.screenshot_handler.resolve_screenshot_path(error_screenshot)
            if error_file and error_file.exists():
                embedded_error = self.screenshot_manager.embed_screenshot(
                    str(error_file), "Error Screenshot"
                )
                if embedded_error:
                    screenshot_sections['error'] = embedded_error
                else:
                    # Fallback: provide artifact link
                    if self.github_run_id and self.target_repo:
                        artifacts_url = f"https://github.com/{self.target_repo}/actions/runs/{self.github_run_id}"
                        screenshot_sections['error'] = f"*Error screenshot available in [GitHub Actions Artifacts]({artifacts_url})*"
        
        return screenshot_sections
    
    def _set_step_summary(self, content: str) -> None:
        """Set GitHub Actions step summary"""
        try:
            summary_file = os.getenv('GITHUB_STEP_SUMMARY')
            if summary_file:
                with open(summary_file, 'a') as f:
                    f.write(content)
                    f.write('\n\n')
                print("✅ Added to GitHub Actions step summary")
        except Exception as e:
            print(f"⚠️ Could not write step summary: {e}")
    
    def report_error(self, error_message: str, details: Dict[str, Any] = None) -> None:
        """
        Report error with GitHub Actions formatting
        
        Args:
            error_message: Error message to report
            details: Optional error details dict
        """
        print(f"::error::{error_message}")
        
        if details:
            print("Error Details:")
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def report_warning(self, warning_message: str) -> None:
        """
        Report warning with GitHub Actions formatting
        
        Args:
            warning_message: Warning message to report
        """
        print(f"::warning::{warning_message}")
    
    def report_notice(self, notice_message: str) -> None:
        """
        Report notice with GitHub Actions formatting
        
        Args:
            notice_message: Notice message to report
        """
        print(f"::notice::{notice_message}")
    
    def report_status(self, status: str, message: str) -> None:
        """
        Report status with appropriate formatting
        
        Args:
            status: Status level (success, warning, error)
            message: Status message
        """
        if status == 'success':
            print(f"✅ {message}")
        elif status == 'warning':
            self.report_warning(message)
        elif status == 'error':
            self.report_error(message)
        else:
            print(f"ℹ️ {message}")
    
    def report_step(self, step: str, status: str = None) -> None:
        """
        Report execution step
        
        Args:
            step: Step description
            status: Optional status (running, success, failed)
        """
        if status == 'running':
            print(f"⏳ {step}...")
        elif status == 'success':
            print(f"✅ {step}")
        elif status == 'failed':
            print(f"❌ {step}")
        else:
            print(f"▶️ {step}")
    
    def report_summary(self, summary: Dict[str, Any]) -> None:
        """
        Report execution summary
        
        Args:
            summary: Summary dict with execution metrics
        """
        print("\n" + "="*50)
        print("EXECUTION SUMMARY")
        print("="*50)
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("="*50 + "\n")
