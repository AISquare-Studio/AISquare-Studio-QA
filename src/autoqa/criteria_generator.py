"""
Test Criteria Generator for AutoQA (Proposal 16)

Automatically analyzes PR code diffs and generates test criteria
(flow_name, tier, area, and test steps) so developers don't have to
write them manually.  The generated criteria are posted as a PR comment
for developer review/approval before test generation proceeds.

Workflow:
  1. Fetch PR diff via GitHub API
  2. Feed diff + optional context to the LLM
  3. Parse structured criteria from LLM response
  4. Post suggested criteria as a PR comment
  5. Check for developer approval (reaction / comment / label)
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERIA_COMMENT_MARKER = "<!-- AutoQA-Criteria-Suggestion-Marker -->"

# LLM prompt for generating test criteria from a diff
CRITERIA_GENERATION_PROMPT = """You are an expert QA engineer for a web application.
Analyze the following code diff from a pull request and generate test criteria.

For each user-facing flow affected by these changes, produce a JSON object with:
- "flow_name": a short snake_case identifier (max 50 chars)
- "tier": "A" (critical: auth/payment/checkout/signup),
         "B" (important: dashboard/settings/profile/search),
         or "C" (nice-to-have: docs/cosmetic/minor)
- "area": a short snake_case tag for the area (max 30 chars)
- "steps": a list of numbered natural-language test steps a human would follow
- "confidence": an integer 0-100 indicating how confident you are in these criteria

Return a JSON array of such objects.  If no user-facing changes are found,
return an empty array [].  Do NOT wrap the JSON in markdown fences.

PR Title: {pr_title}

Code Diff:
```
{diff}
```
"""

# Default tier-inference path mappings
DEFAULT_CRITICAL_PATHS = ["auth", "payment", "checkout", "signup", "login"]
DEFAULT_IMPORTANT_PATHS = [
    "dashboard",
    "settings",
    "profile",
    "search",
    "account",
]


class DiffAnalyzer:
    """Fetches and analyses PR diffs via the GitHub API."""

    def __init__(self, github_token: str, target_repo: str):
        self.github_token = github_token
        self.target_repo = target_repo
        self.base_url = "https://api.github.com"

    # ---- public API --------------------------------------------------------

    def get_pr_diff(self, pr_number: str) -> Optional[str]:
        """Fetch the unified diff for a pull request.

        Args:
            pr_number: Pull request number.

        Returns:
            The diff as a string, or ``None`` on failure.
        """
        url = f"{self.base_url}/repos/{self.target_repo}/pulls/{pr_number}"
        headers = self._headers()
        headers["Accept"] = "application/vnd.github.v3.diff"

        try:
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                return response.text
            logger.warning(f"Failed to fetch PR diff: HTTP {response.status_code}")
        except Exception as exc:
            logger.error(f"Error fetching PR diff: {exc}")
        return None

    def get_pr_info(self, pr_number: str) -> Optional[Dict[str, Any]]:
        """Fetch basic PR metadata (title, body, changed files).

        Args:
            pr_number: Pull request number.

        Returns:
            Dict with ``title``, ``body``, and ``changed_files`` keys,
            or ``None`` on failure.
        """
        url = f"{self.base_url}/repos/{self.target_repo}/pulls/{pr_number}"
        headers = self._headers()

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", ""),
                    "body": data.get("body", ""),
                    "changed_files": data.get("changed_files", 0),
                }
            logger.warning(f"Failed to fetch PR info: HTTP {response.status_code}")
        except Exception as exc:
            logger.error(f"Error fetching PR info: {exc}")
        return None

    def get_changed_file_paths(self, pr_number: str) -> List[str]:
        """Return the list of file paths changed in a PR.

        Args:
            pr_number: Pull request number.

        Returns:
            List of relative file paths.
        """
        url = f"{self.base_url}/repos/{self.target_repo}/pulls/{pr_number}/files"
        headers = self._headers()

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return [f.get("filename", "") for f in response.json()]
            logger.warning(f"Failed to fetch changed files: HTTP {response.status_code}")
        except Exception as exc:
            logger.error(f"Error fetching changed files: {exc}")
        return []

    # ---- helpers -----------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }


class TestCriteriaGenerator:
    """Generates test criteria from PR diffs using an LLM."""

    def __init__(
        self,
        github_token: str,
        target_repo: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.github_token = github_token
        self.target_repo = target_repo
        self.diff_analyzer = DiffAnalyzer(github_token, target_repo)

        # Merge caller-supplied config with defaults
        self.config = self._default_config()
        if config:
            self.config.update(config)

    # ---- configuration -----------------------------------------------------

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            "enabled": True,
            "mode": "suggest",  # "suggest" | "auto"
            "auto_proceed_threshold": 85,
            "include_existing_tests": True,
            "max_flows_per_pr": 5,
            "max_diff_length": 12000,
            "approval_mechanism": "reaction",  # "reaction" | "comment" | "label"
            "tier_inference": {
                "critical_paths": DEFAULT_CRITICAL_PATHS,
                "important_paths": DEFAULT_IMPORTANT_PATHS,
            },
        }

    # ---- public API --------------------------------------------------------

    def generate_criteria(
        self,
        pr_number: str,
        pr_title: str = "",
        llm=None,
    ) -> Dict[str, Any]:
        """Analyse a PR diff and return suggested test criteria.

        Args:
            pr_number: The pull request number.
            pr_title: PR title for context.
            llm: An optional CrewAI ``LLM`` instance.  When ``None`` a
                 default is constructed from environment variables.

        Returns:
            A dict with keys ``success``, ``criteria`` (list of dicts),
            and ``comment_body`` (formatted markdown).
        """
        # 1. Fetch diff
        diff = self.diff_analyzer.get_pr_diff(pr_number)
        if not diff:
            return {
                "success": False,
                "error": "Could not fetch PR diff",
                "criteria": [],
            }

        # Truncate very large diffs to stay within token limits
        if len(diff) > self.config["max_diff_length"]:
            diff = diff[: self.config["max_diff_length"]] + "\n... (diff truncated)"

        # 2. Build LLM prompt
        prompt = CRITERIA_GENERATION_PROMPT.format(
            pr_title=pr_title or "(untitled)",
            diff=diff,
        )

        # 3. Call LLM
        raw_response = self._call_llm(prompt, llm)
        if raw_response is None:
            return {
                "success": False,
                "error": "LLM call failed",
                "criteria": [],
            }

        # 4. Parse structured criteria from LLM output
        criteria = self._parse_criteria_response(raw_response)

        if not criteria:
            return {
                "success": True,
                "criteria": [],
                "message": "No user-facing flows detected in this PR",
                "comment_body": self._build_no_criteria_comment(),
            }

        # 5. Apply tier inference overrides based on changed file paths
        changed_paths = self.diff_analyzer.get_changed_file_paths(pr_number)
        criteria = self._apply_tier_inference(criteria, changed_paths)

        # Cap to configured max
        criteria = criteria[: self.config["max_flows_per_pr"]]

        # 6. Build comment body
        comment_body = self._build_criteria_comment(criteria)

        return {
            "success": True,
            "criteria": criteria,
            "comment_body": comment_body,
        }

    def post_criteria_comment(
        self,
        pr_number: str,
        comment_body: str,
    ) -> bool:
        """Post (or update) the suggested-criteria comment on a PR.

        Args:
            pr_number: Pull request number.
            comment_body: Markdown content.

        Returns:
            ``True`` on success.
        """
        from src.utils.github_comment_client import GitHubCommentClient

        client = GitHubCommentClient(self.github_token, self.target_repo)
        return client.post_or_update_comment(
            pr_number,
            comment_body,
            marker=CRITERIA_COMMENT_MARKER,
        )

    def check_approval(self, pr_number: str) -> Dict[str, Any]:
        """Check whether the developer has approved suggested criteria.

        Supports three mechanisms controlled by
        ``self.config["approval_mechanism"]``:

        * ``"reaction"`` – 👍 reaction on the criteria comment.
        * ``"comment"`` – A comment containing ``/autoqa approve``.
        * ``"label"``   – The ``autoqa:approved`` label on the PR.

        Returns:
            Dict with ``approved`` (bool) and ``mechanism`` (str).
        """
        mechanism = self.config.get("approval_mechanism", "reaction")
        headers = self._github_headers()

        if mechanism == "reaction":
            return self._check_reaction_approval(pr_number, headers)
        elif mechanism == "comment":
            return self._check_comment_approval(pr_number, headers)
        elif mechanism == "label":
            return self._check_label_approval(pr_number, headers)
        else:
            logger.warning(f"Unknown approval mechanism: {mechanism}")
            return {"approved": False, "mechanism": mechanism}

    def should_auto_proceed(self, criteria: List[Dict[str, Any]]) -> bool:
        """Return ``True`` if all criteria exceed the auto-proceed threshold."""
        if self.config.get("mode") != "auto":
            return False

        threshold = self.config.get("auto_proceed_threshold", 85)
        if not criteria:
            return False

        return all(c.get("confidence", 0) >= threshold for c in criteria)

    # ---- tier inference ----------------------------------------------------

    def infer_tier(self, file_paths: List[str]) -> str:
        """Infer the highest-priority tier from a list of changed file paths.

        Args:
            file_paths: Relative file paths touched by the PR.

        Returns:
            ``"A"``, ``"B"``, or ``"C"``.
        """
        tier_config = self.config.get("tier_inference", {})
        critical = tier_config.get("critical_paths", DEFAULT_CRITICAL_PATHS)
        important = tier_config.get("important_paths", DEFAULT_IMPORTANT_PATHS)

        lowered = [p.lower() for p in file_paths]

        for path in lowered:
            for keyword in critical:
                if keyword in path:
                    return "A"

        for path in lowered:
            for keyword in important:
                if keyword in path:
                    return "B"

        return "C"

    # ---- internal helpers --------------------------------------------------

    def _apply_tier_inference(
        self,
        criteria: List[Dict[str, Any]],
        changed_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """Override tier with file-path-based inference when appropriate."""
        inferred = self.infer_tier(changed_paths)
        for c in criteria:
            # Only upgrade tier (never downgrade from what the LLM chose)
            llm_tier = c.get("tier", "C")
            if self._tier_priority(inferred) > self._tier_priority(llm_tier):
                c["tier"] = inferred
        return criteria

    @staticmethod
    def _tier_priority(tier: str) -> int:
        return {"A": 3, "B": 2, "C": 1}.get(tier, 0)

    def _call_llm(self, prompt: str, llm=None) -> Optional[str]:
        """Call the LLM and return the raw text response."""
        try:
            if llm is not None:
                # CrewAI LLM instance
                response = llm.call([{"role": "user", "content": prompt}])
                return response if isinstance(response, str) else str(response)

            # Fallback: direct OpenAI-compatible API call
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set – cannot call LLM")
                return None

            model = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1")
            # Strip provider prefix if present (e.g. "openai/gpt-4.1" → "gpt-4.1")
            if "/" in model:
                model = model.split("/", 1)[1]

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                },
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            logger.error(f"OpenAI API error: HTTP {response.status_code}")
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
        return None

    def _parse_criteria_response(self, raw: str) -> List[Dict[str, Any]]:
        """Extract a list of criteria dicts from the LLM's text response."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find a JSON array in the text
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.error("Could not parse JSON criteria from LLM response")
                    return []
            else:
                logger.error("No JSON array found in LLM response")
                return []

        if not isinstance(parsed, list):
            parsed = [parsed]

        # Validate & normalise each criterion
        valid = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            if "flow_name" not in item or "steps" not in item:
                continue
            # Normalise
            item["flow_name"] = re.sub(r"[^\w]+", "_", item["flow_name"]).strip("_").lower()[:50]
            item.setdefault("tier", "C")
            item["tier"] = item["tier"].upper() if item["tier"] in ("a", "b", "c") else item["tier"]
            item.setdefault("area", "general")
            item["area"] = re.sub(r"[^\w]+", "_", item["area"]).strip("_").lower()[:30]
            item.setdefault("confidence", 50)
            if not isinstance(item["steps"], list):
                item["steps"] = [str(item["steps"])]
            valid.append(item)
        return valid

    # ---- comment building --------------------------------------------------

    def _build_criteria_comment(self, criteria: List[Dict[str, Any]]) -> str:
        """Build a markdown PR comment with suggested criteria."""
        approval_msg = self._approval_instructions()
        sections = []

        for i, c in enumerate(criteria, 1):
            confidence = c.get("confidence", 0)
            confidence_label = (
                "✅ High" if confidence >= 80 else "⚠️ Medium" if confidence >= 50 else "❓ Low"
            )
            steps_md = "\n".join(f"{j}. {s}" for j, s in enumerate(c["steps"], 1))
            sections.append(
                f"**Flow {i}: {c['flow_name']}** (Tier {c['tier']}, Area: {c['area']})\n"
                "```autoqa\n"
                f"flow_name: {c['flow_name']}\n"
                f"tier: {c['tier']}\n"
                f"area: {c['area']}\n"
                "```\n"
                f"{steps_md}\n\n"
                f"**Confidence: {confidence}/100** {confidence_label}\n"
            )

        body = (
            "## 🤖 AutoQA Suggested Test Criteria\n\n"
            "Based on the changes in this PR, I suggest testing the following flows:\n\n"
            + "\n---\n\n".join(sections)
            + f"\n---\n\n{approval_msg}\n\n{CRITERIA_COMMENT_MARKER}\n"
        )
        return body

    @staticmethod
    def _build_no_criteria_comment() -> str:
        return (
            "## 🤖 AutoQA Suggested Test Criteria\n\n"
            "No user-facing flows were detected in this PR.  "
            "If you believe tests are needed, add a manual `autoqa` block to the "
            "PR description.\n\n"
            f"{CRITERIA_COMMENT_MARKER}\n"
        )

    def _approval_instructions(self) -> str:
        mechanism = self.config.get("approval_mechanism", "reaction")
        if mechanism == "reaction":
            return (
                "React with 👍 on this comment to approve these criteria and "
                "trigger test generation, or reply with `/autoqa edit` to modify."
            )
        elif mechanism == "comment":
            return (
                "Reply with `/autoqa approve` to approve these criteria, "
                "or `/autoqa edit` to modify."
            )
        elif mechanism == "label":
            return (
                "Add the `autoqa:approved` label to this PR to approve "
                "these criteria, or reply with `/autoqa edit` to modify."
            )
        return ""

    # ---- approval checking -------------------------------------------------

    def _github_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _check_reaction_approval(self, pr_number: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check for a 👍 reaction on the criteria suggestion comment."""
        from src.utils.github_comment_client import GitHubCommentClient

        client = GitHubCommentClient(self.github_token, self.target_repo)
        comment_id = client.find_existing_autoqa_comment(pr_number, marker=CRITERIA_COMMENT_MARKER)
        if not comment_id:
            return {"approved": False, "mechanism": "reaction", "reason": "no_comment"}

        url = (
            f"https://api.github.com/repos/{self.target_repo}"
            f"/issues/comments/{comment_id}/reactions"
        )
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                for reaction in resp.json():
                    if reaction.get("content") == "+1":
                        return {"approved": True, "mechanism": "reaction"}
        except Exception as exc:
            logger.warning(f"Error checking reactions: {exc}")

        return {"approved": False, "mechanism": "reaction"}

    def _check_comment_approval(self, pr_number: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check for a ``/autoqa approve`` comment."""
        url = f"https://api.github.com/repos/{self.target_repo}/issues/{pr_number}/comments"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                for comment in resp.json():
                    body = comment.get("body", "").strip().lower()
                    if "/autoqa approve" in body:
                        return {"approved": True, "mechanism": "comment"}
        except Exception as exc:
            logger.warning(f"Error checking comments: {exc}")

        return {"approved": False, "mechanism": "comment"}

    def _check_label_approval(self, pr_number: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check for the ``autoqa:approved`` label on the PR."""
        url = f"https://api.github.com/repos/{self.target_repo}/issues/{pr_number}/labels"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                for label in resp.json():
                    if label.get("name") == "autoqa:approved":
                        return {"approved": True, "mechanism": "label"}
        except Exception as exc:
            logger.warning(f"Error checking labels: {exc}")

        return {"approved": False, "mechanism": "label"}
