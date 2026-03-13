"""
Gap-Driven Test Generator for AutoQA.

Reads coverage gap data from the memory tracker and generates test criteria
for uncovered source modules.  This bridges the ``AutoQAMemoryTracker``
(which detects which modules lack tests) with the ``TestCriteriaGenerator``
(which produces structured test criteria from source context).

Workflow:
  1. Load memory state and identify coverage gaps
  2. Read source code of uncovered modules
  3. Use LLM to generate test criteria for each uncovered module
  4. Return criteria in the standard format consumed by ``ActionRunner``
  5. Optionally post a PR comment with the suggested criteria
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.autoqa.memory_tracker import AutoQAMemoryTracker, CoverageGap
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GAP_CRITERIA_COMMENT_MARKER = "<!-- AutoQA-Gap-Driven-Criteria-Marker -->"

# LLM prompt for generating test criteria from source code of an uncovered module
GAP_CRITERIA_PROMPT = """You are an expert QA engineer for a web application.
The following source module has NO test coverage.  Analyse the code and
generate test criteria so we can create automated tests for it.

For each testable flow or behaviour in this module, produce a JSON object with:
- "flow_name": a short snake_case identifier (max 50 chars)
- "tier": "A" (critical: auth/payment/checkout/signup),
         "B" (important: dashboard/settings/profile/search),
         or "C" (nice-to-have: docs/cosmetic/minor)
- "area": a short snake_case tag for the functional area (max 30 chars)
- "steps": a list of numbered natural-language test steps
- "confidence": an integer 0-100 indicating how confident you are

Return a JSON array.  If the module contains no testable logic, return [].
Do NOT wrap the JSON in markdown fences.

Module path: {module_path}

Source code:
```
{source_code}
```
"""

# Default configuration
DEFAULT_GAP_DRIVEN_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "max_modules_per_run": 10,
    "max_source_length": 8000,
    "max_criteria_per_module": 3,
    "auto_proceed_threshold": 85,
    "mode": "suggest",  # "suggest" | "auto"
    "approval_mechanism": "reaction",  # "reaction" | "comment" | "label"
    "tier_inference": {
        "critical_paths": ["auth", "payment", "checkout", "signup", "login"],
        "important_paths": [
            "dashboard",
            "settings",
            "profile",
            "search",
            "account",
        ],
    },
}


class GapDrivenGenerator:
    """Generates test criteria for source modules that lack test coverage.

    Uses memory tracker data to identify uncovered modules, reads their
    source code, and calls an LLM to produce structured test criteria.
    The criteria can then be fed into the standard ``ActionRunner`` pipeline
    for test generation, execution, and commit.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        github_token: Optional[str] = None,
        target_repo: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_path: Optional[str] = None,
        test_dir: Optional[str] = None,
        source_dirs: Optional[List[str]] = None,
    ):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        self.target_repo = target_repo or os.getenv("TARGET_REPOSITORY", "")

        self.config = dict(DEFAULT_GAP_DRIVEN_CONFIG)
        if config:
            self.config.update(config)

        # Initialize memory tracker
        self.tracker = AutoQAMemoryTracker(
            project_root=str(self.project_root),
            memory_path=memory_path,
            test_dir=test_dir,
            source_dirs=source_dirs,
        )

    # ---- public API --------------------------------------------------------

    def generate_criteria_for_gaps(
        self,
        llm=None,
    ) -> Dict[str, Any]:
        """Identify coverage gaps and generate test criteria for uncovered modules.

        Args:
            llm: An optional CrewAI ``LLM`` instance.  When ``None`` a
                 default is constructed from environment variables.

        Returns:
            A dict with ``success``, ``criteria`` (list of dicts),
            ``gaps_found`` (int), ``comment_body`` (markdown), and
            ``gap_details`` (list of gap summaries).
        """
        # 1. Load memory and identify gaps
        self.tracker.load()
        self.tracker.identify_coverage_gaps()
        missing = self.tracker.get_missing_tests()

        if not missing:
            logger.info("No coverage gaps found — all modules have tests")
            return {
                "success": True,
                "criteria": [],
                "gaps_found": 0,
                "message": "All source modules have test coverage",
                "comment_body": self._build_no_gaps_comment(),
            }

        logger.info(f"Found {len(missing)} uncovered modules")

        # Cap the number of modules to process
        max_modules = self.config.get("max_modules_per_run", 10)
        modules_to_process = missing[:max_modules]

        # 2. Generate criteria for each uncovered module
        all_criteria: List[Dict[str, Any]] = []
        gap_details: List[Dict[str, Any]] = []

        for gap in modules_to_process:
            source_code = self._read_source(gap.source_path)
            if not source_code:
                gap_details.append(
                    {
                        "module": gap.module_name,
                        "source_path": gap.source_path,
                        "status": "skipped",
                        "reason": "could_not_read_source",
                    }
                )
                continue

            criteria = self._generate_for_module(gap, source_code, llm)
            if criteria:
                all_criteria.extend(criteria)
                gap_details.append(
                    {
                        "module": gap.module_name,
                        "source_path": gap.source_path,
                        "status": "criteria_generated",
                        "criteria_count": len(criteria),
                    }
                )
            else:
                gap_details.append(
                    {
                        "module": gap.module_name,
                        "source_path": gap.source_path,
                        "status": "no_testable_flows",
                    }
                )

        # 3. Build comment
        comment_body = self._build_gap_criteria_comment(all_criteria, missing, gap_details)

        return {
            "success": True,
            "criteria": all_criteria,
            "gaps_found": len(missing),
            "gaps_processed": len(modules_to_process),
            "gap_details": gap_details,
            "comment_body": comment_body,
        }

    def post_criteria_comment(
        self,
        pr_number: str,
        comment_body: str,
    ) -> bool:
        """Post (or update) the gap-driven criteria comment on a PR.

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
            marker=GAP_CRITERIA_COMMENT_MARKER,
        )

    def should_auto_proceed(self, criteria: List[Dict[str, Any]]) -> bool:
        """Return ``True`` if all criteria exceed the auto-proceed threshold."""
        if self.config.get("mode") != "auto":
            return False

        threshold = self.config.get("auto_proceed_threshold", 85)
        if not criteria:
            return False

        return all(c.get("confidence", 0) >= threshold for c in criteria)

    def get_memory_summary(self) -> Dict[str, Any]:
        """Load memory and return a summary of the current state."""
        self.tracker.load()
        self.tracker.identify_coverage_gaps()
        return self.tracker.get_summary()

    # ---- internal helpers --------------------------------------------------

    def _read_source(self, source_path: str) -> Optional[str]:
        """Read source file content, truncating if necessary."""
        full_path = self.project_root / source_path
        if not full_path.exists():
            logger.warning(f"Source file not found: {full_path}")
            return None

        try:
            content = full_path.read_text(encoding="utf-8")
            max_len = self.config.get("max_source_length", 8000)
            if len(content) > max_len:
                content = content[:max_len] + "\n... (source truncated)"
            return content
        except Exception as exc:
            logger.error(f"Error reading source file {source_path}: {exc}")
            return None

    def _generate_for_module(
        self,
        gap: CoverageGap,
        source_code: str,
        llm=None,
    ) -> List[Dict[str, Any]]:
        """Generate test criteria for a single uncovered module."""
        prompt = GAP_CRITERIA_PROMPT.format(
            module_path=gap.source_path,
            source_code=source_code,
        )

        raw_response = self._call_llm(prompt, llm)
        if raw_response is None:
            logger.warning(f"LLM call failed for module {gap.module_name}")
            return []

        criteria = self._parse_criteria_response(raw_response)

        # Apply tier inference from module path
        inferred_tier = self._infer_tier_from_path(gap.source_path)
        for c in criteria:
            # Only upgrade tier (never downgrade)
            if self._tier_priority(inferred_tier) > self._tier_priority(c.get("tier", "C")):
                c["tier"] = inferred_tier
            # Tag the source module
            c["source_module"] = gap.source_path

        # Cap criteria per module
        max_per_module = self.config.get("max_criteria_per_module", 3)
        return criteria[:max_per_module]

    def _infer_tier_from_path(self, source_path: str) -> str:
        """Infer tier from a source module's file path."""
        tier_config = self.config.get("tier_inference", {})
        critical = tier_config.get("critical_paths", [])
        important = tier_config.get("important_paths", [])

        lowered = source_path.lower()
        for keyword in critical:
            if keyword in lowered:
                return "A"
        for keyword in important:
            if keyword in lowered:
                return "B"
        return "C"

    @staticmethod
    def _tier_priority(tier: str) -> int:
        return {"A": 3, "B": 2, "C": 1}.get(tier, 0)

    def _call_llm(self, prompt: str, llm=None) -> Optional[str]:
        """Call the LLM and return the raw text response."""
        try:
            if llm is not None:
                response = llm.call([{"role": "user", "content": prompt}])
                return response if isinstance(response, str) else str(response)

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set — cannot call LLM")
                return None

            model = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1")
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
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
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

        valid: List[Dict[str, Any]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            if "flow_name" not in item or "steps" not in item:
                continue
            item["flow_name"] = re.sub(r"[^\w]+", "_", item["flow_name"]).strip("_").lower()[:50]
            item.setdefault("tier", "C")
            item["tier"] = str(item["tier"]).upper()
            if item["tier"] not in ("A", "B", "C"):
                item["tier"] = "C"
            item.setdefault("area", "general")
            item["area"] = re.sub(r"[^\w]+", "_", item["area"]).strip("_").lower()[:30]
            item.setdefault("confidence", 50)
            if not isinstance(item["steps"], list):
                item["steps"] = [str(item["steps"])]
            valid.append(item)
        return valid

    # ---- comment building --------------------------------------------------

    def _build_gap_criteria_comment(
        self,
        criteria: List[Dict[str, Any]],
        all_gaps: List[CoverageGap],
        gap_details: List[Dict[str, Any]],
    ) -> str:
        """Build a markdown PR comment for gap-driven criteria."""
        summary = self.tracker.get_summary()

        header = (
            "## 🔍 AutoQA Gap-Driven Test Criteria\n\nBased on the memory tracker analysis, the"
            " following source modules lack test coverage.  AutoQA has generated test criteria for"
            f" them.\n\n**Coverage:** {summary.get('coverage_percentage', 0)}%"
            f" ({summary.get('covered_modules', 0)}/{summary.get('total_source_modules', 0)} modules)\n**Uncovered"
            f" modules:** {len(all_gaps)}\n**Modules processed:** {len(gap_details)}\n\n"
        )

        if not criteria:
            body = (
                header
                + "No testable flows were detected in the uncovered modules.\n\n"
                + f"{GAP_CRITERIA_COMMENT_MARKER}\n"
            )
            return body

        # Build criteria sections
        sections = []
        for i, c in enumerate(criteria, 1):
            confidence = c.get("confidence", 0)
            confidence_label = (
                "✅ High" if confidence >= 80 else "⚠️ Medium" if confidence >= 50 else "❓ Low"
            )
            steps_md = "\n".join(f"{j}. {s}" for j, s in enumerate(c["steps"], 1))
            source = c.get("source_module", "unknown")
            sections.append(
                f"### Flow {i}: `{c['flow_name']}`\n"
                f"**Source:** `{source}` · **Tier:** {c['tier']} · **Area:** {c['area']}\n\n"
                "```autoqa\n"
                f"flow_name: {c['flow_name']}\n"
                f"tier: {c['tier']}\n"
                f"area: {c['area']}\n"
                "```\n"
                f"{steps_md}\n\n"
                f"**Confidence:** {confidence}/100 {confidence_label}\n"
            )

        approval_msg = self._approval_instructions()

        body = (
            header
            + "\n---\n\n".join(sections)
            + f"\n---\n\n{approval_msg}\n\n{GAP_CRITERIA_COMMENT_MARKER}\n"
        )
        return body

    @staticmethod
    def _build_no_gaps_comment() -> str:
        return (
            "## 🔍 AutoQA Gap-Driven Test Criteria\n\n"
            "✅ All source modules have test coverage — no gaps detected!\n\n"
            f"{GAP_CRITERIA_COMMENT_MARKER}\n"
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
