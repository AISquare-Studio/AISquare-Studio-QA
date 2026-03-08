"""
GitHub Comment Client for PR Comments

Handles GitHub API operations for creating and updating PR comments.
"""

from typing import Dict, Optional

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubCommentClient:
    """Handles GitHub API operations for PR comments"""

    def __init__(self, github_token: str, target_repo: str):
        """
        Initialize GitHub comment client

        Args:
            github_token: GitHub API token for authentication
            target_repo: Target repository in format 'owner/repo'
        """
        self.github_token = github_token
        self.target_repo = target_repo
        self.base_url = "https://api.github.com"

    def post_or_update_comment(
        self, pr_number: str, comment_body: str, marker: str = "<!-- AutoQA-Comment-Marker -->"
    ) -> bool:
        """
        Post new comment or update existing AutoQA comment

        Args:
            pr_number: Pull request number
            comment_body: Comment content in markdown
            marker: Unique marker to identify the comment type

        Returns:
            True if successful, False otherwise
        """
        if not self.github_token or not pr_number or not self.target_repo:
            logger.warning("Missing required GitHub context for PR comment")
            return False

        headers = self._get_headers()

        # Check for existing AutoQA comment
        existing_comment_id = self._find_existing_autoqa_comment(pr_number, headers, marker)

        if existing_comment_id:
            # Update existing comment
            return self.update_comment(existing_comment_id, comment_body, headers)
        else:
            # Create new comment
            return self.create_comment(pr_number, comment_body, headers)

    def find_existing_autoqa_comment(
        self, pr_number: str, marker: str = "<!-- AutoQA-Comment-Marker -->"
    ) -> Optional[int]:
        """
        Find existing AutoQA comment by marker

        Args:
            pr_number: Pull request number
            marker: Unique marker to identify the comment type

        Returns:
            Comment ID if found, None otherwise
        """
        headers = self._get_headers()
        return self._find_existing_autoqa_comment(pr_number, headers, marker)

    def _find_existing_autoqa_comment(
        self, pr_number: str, headers: Dict[str, str], marker: str
    ) -> Optional[int]:
        """
        Internal method to find existing AutoQA comment

        Args:
            pr_number: Pull request number
            headers: Request headers with authentication
            marker: Unique marker to identify the comment type

        Returns:
            Comment ID if found, None otherwise
        """
        try:
            # Get all comments on the PR
            url = f"{self.base_url}/repos/{self.target_repo}/issues/{pr_number}/comments"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                comments = response.json()

                # Look for our marker in comments
                for comment in comments:
                    body = comment.get("body", "")
                    # Check for our hidden marker
                    if marker in body:
                        logger.info(f"Found existing AutoQA comment: {comment['id']}")
                        return comment["id"]
                    # Fallback: check for AutoQA header (for legacy comments) - ONLY for default marker
                    elif marker == "<!-- AutoQA-Comment-Marker -->" and (
                        "## ✅ AutoQA" in body or "## ❌ AutoQA" in body
                    ):
                        logger.info(f"Found existing AutoQA comment (legacy): {comment['id']}")
                        return comment["id"]
            else:
                logger.warning(f"Failed to fetch PR comments: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"Error searching for existing comment: {e}")

        return None

    def update_comment(
        self, comment_id: int, comment_body: str, headers: Dict[str, str] = None
    ) -> bool:
        """
        Update existing comment

        Args:
            comment_id: ID of comment to update
            comment_body: New comment content
            headers: Optional request headers (will be generated if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            if headers is None:
                headers = self._get_headers()

            url = f"{self.base_url}/repos/{self.target_repo}/issues/comments/{comment_id}"

            data = {"body": comment_body}

            response = requests.patch(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                logger.info(f"Updated existing PR comment #{comment_id}")
                return True
            else:
                logger.warning(f"Failed to update comment: HTTP {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error updating PR comment: {e}")
            return False

    def create_comment(
        self, pr_number: str, comment_body: str, headers: Dict[str, str] = None
    ) -> bool:
        """
        Create new comment on PR

        Args:
            pr_number: Pull request number
            comment_body: Comment content
            headers: Optional request headers (will be generated if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            if headers is None:
                headers = self._get_headers()

            url = f"{self.base_url}/repos/{self.target_repo}/issues/{pr_number}/comments"

            data = {"body": comment_body}

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 201:
                logger.info(f"Created new PR comment on #{pr_number}")
                return True
            else:
                logger.warning(f"Failed to create comment: HTTP {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error creating PR comment: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication

        Returns:
            Headers dictionary
        """
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, url: str, data: dict = None) -> requests.Response:
        """
        Make authenticated HTTP request to GitHub API

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full API URL
            data: Optional request data

        Returns:
            Response object
        """
        headers = self._get_headers()

        if method.upper() == "GET":
            return requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            return requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PATCH":
            return requests.patch(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            return requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
