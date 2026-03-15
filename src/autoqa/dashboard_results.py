"""
Dashboard Results Builder for AutoQA.

Transforms gap-analysis and test-suite results into the unified JSON
schema consumed by the AutoQA Dashboard (Phase 1).

The output JSON has three top-level keys:

* ``gap_analysis`` – coverage information (present / missing workflows).
* ``summary``      – run-level metadata (PR number, commit SHA, counts).
* ``test_cases``   – per-test details (status, duration, errors, screenshots).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default output location
DEFAULT_DASHBOARD_PATH = "reports/dashboard_results.json"


class DashboardResultsBuilder:
    """Build a dashboard-ready JSON payload from AutoQA run data.

    Parameters
    ----------
    pr_number : int or str, optional
        Pull-request number for the current run.
    commit_sha : str, optional
        Git commit SHA for the current run.
    execution_mode : str, optional
        Execution mode (e.g. ``"pr_validation"``, ``"suite"``).
    timestamp : str, optional
        ISO-8601 timestamp.  Defaults to *now*.
    """

    def __init__(
        self,
        pr_number: Optional[Any] = None,
        commit_sha: Optional[str] = None,
        execution_mode: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        self.pr_number = int(pr_number) if pr_number else None
        self.commit_sha = commit_sha or ""
        self.execution_mode = execution_mode or "pr_validation"
        self.timestamp = timestamp or datetime.now().isoformat()

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def build_gap_analysis(self, gap_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform internal gap-analysis data to the dashboard schema.

        Parameters
        ----------
        gap_results : dict, optional
            Output of ``GapAnalysisDB.run_analysis()`` or
            ``GapAnalysisDB.get_latest_run()``.

        Returns
        -------
        dict
            ``gap_analysis`` section conforming to the dashboard PRD.
        """
        if not gap_results:
            return {
                "coverage_percent": 0.0,
                "total_workflows": 0,
                "tested_workflows": 0,
                "missing_workflows": 0,
                "present_workflows": [],
                "missing_workflows_list": [],
            }

        present = gap_results.get("workflows_present", [])
        missing = gap_results.get("workflows_missing", [])

        present_workflows = [
            {
                "module": w.get("module_name", ""),
                "source_path": w.get("source_path", ""),
                "test_file": w.get("test_file", ""),
                "tier": w.get("tier", "C"),
                "area": w.get("area", "general"),
            }
            for w in present
        ]

        missing_workflows_list = [
            {
                "module": w.get("module_name", ""),
                "source_path": w.get("source_path", ""),
            }
            for w in missing
        ]

        return {
            "coverage_percent": gap_results.get("coverage_pct", 0.0),
            "total_workflows": gap_results.get("total_modules", 0),
            "tested_workflows": gap_results.get("present_count", 0),
            "missing_workflows": gap_results.get("missing_count", 0),
            "present_workflows": present_workflows,
            "missing_workflows_list": missing_workflows_list,
        }

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def build_summary(self, suite_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build the ``summary`` section from suite-run results.

        Parameters
        ----------
        suite_results : dict, optional
            Output of ``ActionRunner._run_test_suite()``.

        Returns
        -------
        dict
            ``summary`` section conforming to the dashboard PRD.
        """
        if not suite_results:
            return {
                "timestamp": self.timestamp,
                "execution_mode": self.execution_mode,
                "pr_number": self.pr_number,
                "commit_sha": self.commit_sha,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": 0.0,
            }

        return {
            "timestamp": self.timestamp,
            "execution_mode": self.execution_mode,
            "pr_number": self.pr_number,
            "commit_sha": self.commit_sha,
            "total_tests": suite_results.get("total_tests", 0),
            "passed": suite_results.get("passed", 0),
            "failed": suite_results.get("failed", 0),
            "skipped": suite_results.get("skipped", 0),
            "duration_seconds": suite_results.get("execution_time", 0.0),
        }

    # ------------------------------------------------------------------
    # Test cases
    # ------------------------------------------------------------------

    def build_test_cases(
        self, suite_results: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build the ``test_cases`` list from suite detailed results.

        Parameters
        ----------
        suite_results : dict, optional
            Output of ``ActionRunner._run_test_suite()`` which contains
            a ``detailed_results`` list.

        Returns
        -------
        list[dict]
            ``test_cases`` list conforming to the dashboard PRD.
        """
        if not suite_results:
            return []

        detailed = suite_results.get("detailed_results", [])
        test_cases: List[Dict[str, Any]] = []

        for test in detailed:
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "unknown")
            error_msg = test.get("error", "")

            # Map pytest outcomes to dashboard status values
            status = self._map_status(outcome)

            # Infer flow_name from nodeid
            flow_name = self._infer_flow_name(nodeid)

            # Infer tier and area from nodeid path
            tier = self._infer_tier_from_nodeid(nodeid)
            area = self._infer_area_from_nodeid(nodeid)

            # Build error_type from error_message
            error_type = self._extract_error_type(error_msg) if error_msg else ""

            case: Dict[str, Any] = {
                "test_id": nodeid,
                "flow_name": flow_name,
                "tier": tier,
                "area": area,
                "status": status,
                "duration_seconds": round(test.get("duration", 0.0), 2),
                "screenshots": [],
            }

            if error_msg:
                case["error_message"] = error_msg
            if error_type:
                case["error_type"] = error_type

            test_cases.append(case)

        return test_cases

    # ------------------------------------------------------------------
    # Full build
    # ------------------------------------------------------------------

    def build(
        self,
        gap_results: Optional[Dict[str, Any]] = None,
        suite_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the complete dashboard JSON payload.

        Parameters
        ----------
        gap_results : dict, optional
            Output of ``GapAnalysisDB.run_analysis()``.
        suite_results : dict, optional
            Output of ``ActionRunner._run_test_suite()``.

        Returns
        -------
        dict
            Full dashboard payload with ``gap_analysis``, ``summary``,
            and ``test_cases`` keys.
        """
        return {
            "gap_analysis": self.build_gap_analysis(gap_results),
            "summary": self.build_summary(suite_results),
            "test_cases": self.build_test_cases(suite_results),
        }

    def build_and_save(
        self,
        gap_results: Optional[Dict[str, Any]] = None,
        suite_results: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the dashboard payload and write it to a JSON file.

        Parameters
        ----------
        gap_results : dict, optional
            Output of ``GapAnalysisDB.run_analysis()``.
        suite_results : dict, optional
            Output of ``ActionRunner._run_test_suite()``.
        output_path : str, optional
            File path for the JSON output.  Defaults to
            ``reports/dashboard_results.json``.

        Returns
        -------
        dict
            The dashboard payload that was written.
        """
        payload = self.build(gap_results, suite_results)

        path = Path(output_path or DEFAULT_DASHBOARD_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"Dashboard results saved to {path}")
        return payload

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_status(outcome: str) -> str:
        """Map pytest outcome to dashboard status."""
        mapping = {
            "passed": "passed",
            "failed": "failed",
            "error": "failed",
            "skipped": "skipped",
            "xfailed": "skipped",
            "xpassed": "passed",
        }
        return mapping.get(outcome, "unknown")

    @staticmethod
    def _infer_flow_name(nodeid: str) -> str:
        """Derive a dotted flow name from a pytest node ID.

        Example:
            ``tests/autoqa/A/auth/test_user_login.py::TestLogin::test_login``
            → ``"user_login"``
        """
        file_part = nodeid.split("::")[0] if "::" in nodeid else nodeid
        stem = Path(file_part).stem  # e.g. "test_user_login"
        if stem.startswith("test_"):
            return stem[5:]
        return stem

    _CRITICAL_KEYWORDS = ["auth", "payment", "checkout", "signup", "login"]
    _IMPORTANT_KEYWORDS = ["dashboard", "settings", "profile", "search", "account"]

    @classmethod
    def _infer_tier_from_nodeid(cls, nodeid: str) -> str:
        """Infer tier from the nodeid path.

        Checks for an explicit tier directory (e.g. ``tests/autoqa/A/...``)
        first, then falls back to keyword-based inference.
        """
        parts = Path(nodeid.split("::")[0]).parts
        # Check for explicit tier directory (single uppercase letter)
        for part in parts:
            if len(part) == 1 and part in ("A", "B", "C"):
                return part

        # Keyword-based fallback
        lowered = nodeid.lower()
        for kw in cls._CRITICAL_KEYWORDS:
            if kw in lowered:
                return "A"
        for kw in cls._IMPORTANT_KEYWORDS:
            if kw in lowered:
                return "B"
        return "C"

    @staticmethod
    def _infer_area_from_nodeid(nodeid: str) -> str:
        """Infer area from the nodeid path.

        Looks for the directory immediately before the test file.
        """
        parts = Path(nodeid.split("::")[0]).parts
        if len(parts) >= 2:
            candidate = parts[-2]
            # Skip single-letter tier directories
            if len(candidate) == 1 and candidate in ("A", "B", "C"):
                if len(parts) >= 3:
                    return parts[-3]
                return "general"
            return candidate
        return "general"

    @staticmethod
    def _extract_error_type(error_message: str) -> str:
        """Extract the exception class name from an error message.

        Handles patterns like ``"AssertionError: message"`` or
        ``"TypeError: something"``.
        """
        if not error_message:
            return ""
        # Look for "ErrorType:" pattern
        if ":" in error_message:
            candidate = error_message.split(":")[0].strip()
            # Basic heuristic: error types are typically CamelCase or end in Error/Exception
            if candidate and (
                candidate[0].isupper()
                and (
                    candidate.endswith("Error")
                    or candidate.endswith("Exception")
                    or candidate.endswith("Failure")
                )
            ):
                return candidate
        return ""
