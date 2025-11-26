"""
Cross-Repository Manager for AutoQA
Handles operations between the action repository and target repository
"""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrossRepoManager:
    """Manages cross-repository operations for AutoQA action"""

    def __init__(self, target_workspace: Path, action_path: Path):
        self.target_workspace = target_workspace
        self.action_path = action_path
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.target_branch = os.getenv("TARGET_BRANCH", "main")
        self.test_directory = os.getenv("TEST_DIRECTORY", "tests/autoQA")
        self.create_pr = os.getenv("CREATE_PR", "false").lower() == "true"

    def commit_test_file(self, code: str, metadata: Dict[str, Any]) -> Path:
        """
        Commit generated test file to target repository
        
        Args:
            code: Generated test code
            metadata: AutoQA metadata including flow_name, tier, area, steps, etag
            
        Returns:
            Path to created test file
        """
        # Extract components from metadata
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        flow_name = metadata.get("flow_name", "unknown")
        
        # Ensure directory structure exists
        test_dir = self._ensure_directory_structure(tier, area)

        # Generate test file path
        test_file_path = self._generate_test_file_path(metadata)

        # Write test file with proper header
        test_content = self._create_test_file_content(code, metadata)
        test_file_path.write_text(test_content)

        # Commit to target repository
        self._commit_file_to_repo(test_file_path, metadata)

        return test_file_path

    def _ensure_directory_structure(self, tier: str, area: str = None) -> Path:
        """
        Ensure tests/autoqa/{tier}/{area}/ directory structure exists
        
        Args:
            tier: Test tier (A, B, or C)
            area: Optional area/module name (defaults to 'general')
            
        Returns:
            Path to the tier/area directory
        """
        # Base autoqa directory
        base_dir = self.target_workspace / self.test_directory
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create base __init__.py
        base_init = base_dir / "__init__.py"
        if not base_init.exists():
            base_init.write_text('"""AutoQA Generated Tests"""\n')
        
        # Tier directory
        tier_dir = base_dir / tier
        tier_dir.mkdir(exist_ok=True)
        
        tier_init = tier_dir / "__init__.py"
        if not tier_init.exists():
            tier_init.write_text(f'"""AutoQA Tier {tier} Tests"""\n')
        
        # Area directory (if specified and not default)
        if area and area != "general":
            area_dir = tier_dir / area
            area_dir.mkdir(exist_ok=True)
            
            area_init = area_dir / "__init__.py"
            if not area_init.exists():
                area_init.write_text(f'"""AutoQA {area.title()} Tests"""\n')
            
            return area_dir
        
        return tier_dir
    
    def _generate_test_file_path(self, metadata: Dict[str, Any]) -> Path:
        """
        Generate test file path following pattern: tests/autoqa/{tier}/{area}/test_{flow_name}.py
        
        Args:
            metadata: AutoQA metadata with tier, area, flow_name
            
        Returns:
            Path object for the test file
        """
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        flow_name = metadata.get("flow_name", "unknown")
        
        # Get the tier/area directory
        test_dir = self._ensure_directory_structure(tier, area)
        
        # Base filename
        base_filename = f"test_{flow_name}.py"
        test_file_path = test_dir / base_filename
        
        # Handle conflicts with version suffix
        if test_file_path.exists():
            counter = 2
            while test_file_path.exists():
                versioned_filename = f"test_{flow_name}_v{counter}.py"
                test_file_path = test_dir / versioned_filename
                counter += 1
                
                if counter > 100:  # Safety limit
                    raise ValueError(f"Too many versions of test file: {flow_name}")
        
        return test_file_path

    def _create_test_file_content(self, code: str, metadata: Dict[str, Any]) -> str:
        """
        Create complete test file content with AutoQA-Generated header and metadata
        
        Args:
            code: Generated test code
            metadata: AutoQA metadata with all fields
            
        Returns:
            Complete file content as string
        """
        # Extract metadata components
        flow_name = metadata.get("flow_name", "unknown")
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        etag = metadata.get("etag", "")
        steps = metadata.get("steps", [])
        timestamp = self._format_iso8601_timestamp()
        
        # Build test class name from flow_name (CamelCase)
        class_name = self._flow_name_to_class_name(flow_name)
        
        # Build test method name from flow_name (snake_case)
        method_name = f"test_{flow_name}"

        header = f'''"""
# AutoQA-Generated
# Generated: {timestamp}
# Flow: {flow_name}
# Tier: {tier}
# Area: {area}
# ETag: {etag}

Test Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}

This test was automatically generated by AISquare Studio AutoQA.
For policy details, see: .github/autoqa-policy.yml
"""

import pytest
from playwright.sync_api import sync_playwright


class {class_name}:
    """AutoQA generated test class for {flow_name}"""

    @pytest.mark.autoqa
    @pytest.mark.tier_{tier.lower()}
    @pytest.mark.area_{area}
    def {method_name}(self):
        """
        Test: {flow_name}
        Tier: {tier} | Area: {area}
        """

        # Test configuration from environment
        import os
        base_url = os.getenv("STAGING_URL", "https://stg-home.aisquare.studio").rstrip("/")
        config = {{
            'base_url': base_url,
            'login_url': base_url + "/login",
            'email': os.getenv("STAGING_EMAIL", "test@example.com"),
            'password': os.getenv("STAGING_PASSWORD", "password123"),
            'headless': True,
            'timeout': 30000
        }}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config['headless'])
            page = browser.new_page()
            page.set_viewport_size({{"width": 1280, "height": 720}})

            try:
                # Execute generated test code
{self._indent_code(code, 16)}
            finally:
                browser.close()


# Standalone execution for testing
if __name__ == "__main__":
    test_instance = {class_name}()
    test_instance.{method_name}()
    print("✅ AutoQA test '{flow_name}' completed successfully")
'''

        return header
    
    def _flow_name_to_class_name(self, flow_name: str) -> str:
        """
        Convert flow_name to CamelCase class name
        
        Args:
            flow_name: Snake_case flow name
            
        Returns:
            CamelCase class name with Test prefix
        """
        # Split by underscore and capitalize each part
        parts = flow_name.split('_')
        camel = ''.join(word.capitalize() for word in parts)
        return f"Test{camel}"
    
    def _format_iso8601_timestamp(self) -> str:
        """
        Generate ISO8601 timestamp with timezone
        
        Returns:
            ISO8601 formatted timestamp string
        """
        return datetime.now(timezone.utc).astimezone().isoformat()

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block for proper formatting"""
        indent = " " * spaces
        lines = code.split("\n")
        indented_lines = []

        for line in lines:
            if line.strip():  # Don't indent empty lines
                indented_lines.append(indent + line)
            else:
                indented_lines.append("")

        return "\n".join(indented_lines)

    def _commit_file_to_repo(self, test_file_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Commit the test file to the target repository
        
        Args:
            test_file_path: Path to the test file
            metadata: AutoQA metadata for commit message
        """
        try:
            # Configure git for the action
            git_user_name = os.getenv("GIT_USER_NAME", "AutoQA Bot")
            git_user_email = os.getenv("GIT_USER_EMAIL", "rabia.tahirr@opengrowth.com")

            subprocess.run(
                ["git", "config", "user.name", git_user_name], cwd=self.target_workspace, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", git_user_email],
                cwd=self.target_workspace,
                check=True,
            )

            # Add the test file and any new __init__.py files
            relative_path = test_file_path.relative_to(self.target_workspace)
            
            # Add the specific file
            subprocess.run(
                ["git", "add", str(relative_path)], cwd=self.target_workspace, check=True
            )
            
            # Add any __init__.py files in the directory tree
            test_dir = test_file_path.parent
            while str(test_dir) != str(self.target_workspace):
                init_file = test_dir / "__init__.py"
                if init_file.exists():
                    init_relative = init_file.relative_to(self.target_workspace)
                    subprocess.run(
                        ["git", "add", str(init_relative)], 
                        cwd=self.target_workspace, 
                        check=False  # Don't fail if already tracked
                    )
                test_dir = test_dir.parent

            # Create commit message
            commit_message = self._generate_commit_message(metadata)

            # Commit the file
            subprocess.run(
                ["git", "commit", "-m", commit_message], cwd=self.target_workspace, check=True
            )

            logger.info(f"Committed test file: {relative_path}")

            # Push to remote repository or create PR
            if self.create_pr:
                self._create_pull_request(metadata)
            else:
                self._push_to_remote()

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit test file: {e}")
            raise

    def _push_to_remote(self) -> None:
        """Push committed changes to remote repository"""
        try:
            # Get current branch name
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.target_workspace,
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()

            # Check if we have a remote configured
            remote_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.target_workspace,
                capture_output=True,
                text=True,
            )

            if remote_result.returncode != 0:
                logger.warning("No remote 'origin' configured, skipping push")
                return

            logger.info(f"Pushing changes to origin/{current_branch}...")

            # Push to origin with authentication
            push_result = subprocess.run(
                ["git", "push", "origin", current_branch],
                cwd=self.target_workspace,
                capture_output=True,
                text=True,
            )

            if push_result.returncode == 0:
                logger.info("Successfully pushed changes to remote repository")
            else:
                logger.error(f"Push failed: {push_result.stderr}")
                logger.info("Possible causes:")
                logger.info("  - Branch protection rules preventing direct push")
                logger.info("  - Insufficient permissions on repository")
                logger.info("  - Network connectivity issues")
                logger.info("Note: Changes are committed locally but not pushed to remote")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push to remote: {e}")
            logger.info("Note: Changes are committed locally but not pushed to remote")
            # Don't re-raise the exception as commit was successful

    def _create_pull_request(self, metadata: Dict[str, Any]) -> None:
        """
        Create a pull request with the AutoQA test changes
        
        Args:
            metadata: AutoQA metadata for branch naming and description
        """
        try:
            flow_name = metadata.get("flow_name", "test")
            tier = metadata.get("tier", "B")
            
            # Create a new branch for the PR
            branch_name = f"autoqa/{tier.lower()}/{flow_name}"

            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name], cwd=self.target_workspace, check=True
            )

            # Push the new branch
            subprocess.run(
                ["git", "push", "origin", branch_name], cwd=self.target_workspace, check=True
            )

            logger.info(f"Created and pushed branch: {branch_name}")
            logger.info(f"Create a PR manually from {branch_name} to {self.target_branch}")
            logger.info(
                f"Or use GitHub CLI: gh pr create --title 'AutoQA: {flow_name}' --body"
                " 'Auto-generated test from AutoQA'"
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create pull request branch: {e}")
            logger.info("Falling back to direct push...")
            self._push_to_remote()

    def _generate_commit_message(self, metadata: Dict[str, Any]) -> str:
        """
        Generate descriptive commit message from metadata
        
        Args:
            metadata: AutoQA metadata
            
        Returns:
            Formatted commit message
        """
        flow_name = metadata.get("flow_name", "unknown")
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        steps = metadata.get("steps", [])
        
        message = f"AutoQA: Add {flow_name} test"
        
        if area and area != "general":
            message += f" [{tier}/{area}]"
        else:
            message += f" [Tier {tier}]"
        
        if steps:
            message += f" ({len(steps)} steps)"
        
        return message

    def discover_tests(self) -> List[Path]:
        """Discover existing test files in target repository"""
        test_dir = self.target_workspace / self.test_directory

        if not test_dir.exists():
            return []

        # Find all Python test files
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(test_dir.rglob(pattern))

        return test_files

    def get_test_metadata(self, test_file: Path) -> Optional[Dict[str, Any]]:
        """Extract metadata from test file"""
        try:
            content = test_file.read_text()

            # Extract metadata from docstring
            metadata = {}

            if "AutoQA Generated Test" in content:
                metadata["source"] = "AutoQA"
                metadata["generated"] = True

            # Extract other metadata as needed

            return metadata

        except Exception as e:
            logger.warning(f"Could not extract metadata from {test_file}: {e}")
            return None

    def cleanup_old_tests(self, max_tests: int = 50) -> None:
        """Clean up old AutoQA tests if too many exist"""
        test_files = self.discover_tests()
        autoqa_tests = [f for f in test_files if "autoqa" in f.name.lower()]

        if len(autoqa_tests) > max_tests:
            # Sort by modification time and remove oldest
            autoqa_tests.sort(key=lambda f: f.stat().st_mtime)
            to_remove = autoqa_tests[: len(autoqa_tests) - max_tests]

            for test_file in to_remove:
                try:
                    test_file.unlink()
                    logger.info(f"Removed old test: {test_file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove {test_file}: {e}")
