"""
Screenshot Embed Manager for GitHub PR Comments

Handles screenshot embedding, base64 encoding, and GitHub upload
for inclusion in PR comments.
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from src.utils.logger import get_logger
from src.utils.screenshot_handler import ScreenshotHandler

logger = get_logger(__name__)


class ScreenshotEmbedManager:
    """Manages screenshot embedding and upload for PR comments"""

    def __init__(
        self,
        screenshot_handler: ScreenshotHandler,
        github_token: str = None,
        target_repo: str = None,
        github_run_id: str = None,
        github_workspace: Path = None,
    ):
        """
        Initialize screenshot embed manager

        Args:
            screenshot_handler: ScreenshotHandler instance for path resolution
            github_token: GitHub API token for uploads
            target_repo: Target repository in format 'owner/repo'
            github_run_id: GitHub Actions run ID for artifact links
            github_workspace: GitHub workspace path
        """
        self.screenshot_handler = screenshot_handler
        self.github_token = github_token
        self.target_repo = target_repo
        self.github_run_id = github_run_id
        self.github_workspace = github_workspace or Path(".")

    def embed_screenshot(self, screenshot_path: str, title: str) -> str:
        """
        Embed screenshot in comment or create artifact link

        Args:
            screenshot_path: Path to screenshot file
            title: Title/caption for the screenshot

        Returns:
            Markdown string with embedded image or artifact link
        """
        try:
            # Resolve screenshot path
            screenshot_file = self.screenshot_handler.resolve_screenshot_path(screenshot_path)

            if not screenshot_file or not screenshot_file.exists():
                logger.warning(f"Screenshot file not found: {screenshot_path}")
                return ""

            # Get screenshot metadata
            screenshot_info = self.screenshot_handler.get_screenshot_info(screenshot_file)
            file_size_kb = screenshot_info["size"] / 1024

            logger.info(f"Processing screenshot: {screenshot_path} ({file_size_kb:.1f} KB)")

            # Read screenshot data
            with open(screenshot_file, "rb") as f:
                image_data = f.read()

            # Method 1: Try uploading to GitHub repository
            if self.github_token and self.target_repo:
                screenshot_url = self.upload_to_github(screenshot_file.name, image_data)
                if screenshot_url:
                    return f"![{title}]({screenshot_url})"

            # Method 2: Base64 embed for small images
            if screenshot_info["can_embed"]:
                return self.create_base64_embed(image_data, title, file_size_kb)

            # Method 3: Artifact link for large images
            return self.create_artifact_link(screenshot_path, screenshot_info)

        except Exception as e:
            logger.warning(f"Could not process screenshot: {e}")
            return f"**{title}:** `{screenshot_path}` (Processing failed: {str(e)})"

    def upload_to_github(self, filename: str, image_data: bytes) -> Optional[str]:
        """
        Upload screenshot to GitHub repository

        Args:
            filename: Name of the screenshot file
            image_data: Raw image bytes

        Returns:
            URL of uploaded screenshot, or None if upload fails
        """
        try:
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"autoqa_screenshot_{timestamp}_{filename}"

            # Upload path in repository
            upload_path = f"autoqa-screenshots/{unique_filename}"

            url = f"https://api.github.com/repos/{self.target_repo}/contents/{upload_path}"

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            # Encode image data
            base64_content = base64.b64encode(image_data).decode("utf-8")

            data = {
                "message": f"AutoQA: Upload screenshot {unique_filename}",
                "content": base64_content,
                "branch": "main",  # or create a special branch for screenshots
            }

            response = requests.put(url, headers=headers, json=data, timeout=30)

            if response.status_code in [200, 201]:
                response_data = response.json()
                # Return the raw URL for direct image embedding
                download_url = response_data.get("content", {}).get("download_url")
                if download_url:
                    logger.info(f"Screenshot uploaded to GitHub: {download_url}")
                    return download_url
                else:
                    logger.warning("Upload response missing download_url")
                    return None
            else:
                logger.warning(f"Failed to upload screenshot: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Error uploading screenshot to GitHub: {e}")
            return None

    def create_base64_embed(self, image_data: bytes, title: str, file_size_kb: float) -> str:
        """
        Create base64 embedded image

        Args:
            image_data: Raw image bytes
            title: Image title/caption
            file_size_kb: File size in KB

        Returns:
            Markdown with base64 data URL
        """
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        logger.info(f"Embedding screenshot as base64 data URL ({file_size_kb:.1f} KB)")
        return f"![{title}](data:image/png;base64,{encoded_image})"

    def create_artifact_link(self, screenshot_path: str, screenshot_info: dict) -> str:
        """
        Create artifact link for large screenshots

        Args:
            screenshot_path: Path to screenshot file
            screenshot_info: Screenshot metadata from ScreenshotHandler

        Returns:
            Markdown with artifact details and link
        """
        file_size_kb = screenshot_info["size"] / 1024

        artifacts_url = ""
        if self.github_run_id and self.target_repo:
            artifacts_url = (
                f"https://github.com/{self.target_repo}/actions/runs/{self.github_run_id}"
            )

        return f"""
<details>
<summary>📸 Screenshot ({file_size_kb:.1f} KB) - Click to view details</summary>

**File:** `{screenshot_path}`
**Size:** {file_size_kb:.1f} KB
**Timestamp:** {screenshot_info['timestamp']}

> 🖼️ Screenshot captured during test execution.
> This screenshot shows the browser state when the test completed.
>
> **Note:** Image is too large to embed directly in comment.
> The screenshot file is available in the repository at the path above.

</details>

*💡 To view the screenshot: Check the `{screenshot_path}` file or [download from artifacts]({artifacts_url})*"""
