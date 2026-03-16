"""
Test ID Scanner for AutoQA Gap Analysis.

Scans for ``data-testid`` definitions in a registry file and references in
test files to calculate user-flow-oriented coverage.  A ``data-testid`` is
a kebab-case, natural-language identifier attached to a UI component (e.g.
``login-email-input``, ``dashboard-header``).

Coverage model
--------------
* **Registry** (``config/testid_registry.yaml``) declares every
  ``data-testid`` that the application exposes, grouped by flow and area.
* **Test files** (``test_*.py``) are scanned for ``data-testid`` references
  (e.g. ``page.locator('[data-testid="login-email-input"]')``).
* **Coverage** = referenced test IDs / total registered test IDs.

Scope modes
-----------
* **full** – analyse the entire registry and all test files.
* **pr** – only consider test IDs whose *flow* appears in the list of
  changed files (requires a list of changed paths).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default paths
DEFAULT_REGISTRY_PATH = "config/testid_registry.yaml"

# Regex to find data-testid references in Python test files.
# Matches patterns like:
#   [data-testid="some-id"]
#   [data-testid='some-id']
#   data-testid="some-id"
#   data_testid="some-id"   (underscore variant sometimes used)
#   get_by_test_id("some-id")
TESTID_REFERENCE_PATTERNS = [
    re.compile(r"""data-testid=["']([a-z0-9][a-z0-9\-]*)["']"""),
    re.compile(r"""data_testid=["']([a-z0-9][a-z0-9\-]*)["']"""),
    re.compile(r"""get_by_test_id\(\s*["']([a-z0-9][a-z0-9\-]*)["']\s*\)"""),
]


class TestIdEntry:
    """A single ``data-testid`` defined in the registry."""

    def __init__(
        self,
        testid: str,
        flow: str,
        area: str = "general",
        tier: str = "C",
        description: str = "",
    ):
        self.testid = testid
        self.flow = flow
        self.area = area
        self.tier = tier
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "testid": self.testid,
            "flow": self.flow,
            "area": self.area,
            "tier": self.tier,
            "description": self.description,
        }


class TestIdCoverageResult:
    """Result of a test-ID coverage scan."""

    def __init__(
        self,
        total_testids: int,
        covered_testids: int,
        covered_ids: List[str],
        uncovered_ids: List[str],
        uncovered_entries: List[TestIdEntry],
        coverage_pct: float,
        scope: str,
    ):
        self.total_testids = total_testids
        self.covered_testids = covered_testids
        self.covered_ids = covered_ids
        self.uncovered_ids = uncovered_ids
        self.uncovered_entries = uncovered_entries
        self.coverage_pct = coverage_pct
        self.scope = scope

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_testids": self.total_testids,
            "covered_testids": self.covered_testids,
            "covered_ids": self.covered_ids,
            "uncovered_ids": self.uncovered_ids,
            "uncovered_entries": [e.to_dict() for e in self.uncovered_entries],
            "coverage_pct": self.coverage_pct,
            "scope": self.scope,
        }


class TestIdScanner:
    """Scans a registry and test files to compute ``data-testid`` coverage.

    Parameters
    ----------
    project_root : str, optional
        Root directory of the target project.
    registry_path : str, optional
        Path (relative to *project_root*) to the YAML registry file.
    test_dir : str, optional
        Directory (relative to *project_root*) containing test files.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        registry_path: Optional[str] = None,
        test_dir: Optional[str] = None,
    ):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.registry_path = self.project_root / (registry_path or DEFAULT_REGISTRY_PATH)
        self.test_dir = test_dir or "tests"

    # ------------------------------------------------------------------
    # Registry loading
    # ------------------------------------------------------------------

    def load_registry(self) -> List[TestIdEntry]:
        """Load and parse the test-ID registry YAML file.

        Returns
        -------
        list[TestIdEntry]
            All ``data-testid`` entries defined in the registry.
        """
        if not self.registry_path.exists():
            logger.warning(f"Test ID registry not found: {self.registry_path}")
            return []

        try:
            with open(self.registry_path, "r") as fh:
                data = yaml.safe_load(fh) or {}
        except Exception as exc:
            logger.error(f"Failed to load test ID registry: {exc}")
            return []

        entries: List[TestIdEntry] = []
        for flow_def in data.get("flows", []):
            flow_name = flow_def.get("name", "unknown")
            area = flow_def.get("area", "general")
            tier = flow_def.get("tier", "C")
            for tid_def in flow_def.get("testids", []):
                if isinstance(tid_def, str):
                    entries.append(
                        TestIdEntry(
                            testid=tid_def,
                            flow=flow_name,
                            area=area,
                            tier=tier,
                        )
                    )
                elif isinstance(tid_def, dict):
                    entries.append(
                        TestIdEntry(
                            testid=tid_def.get("id", ""),
                            flow=flow_name,
                            area=area,
                            tier=tier,
                            description=tid_def.get("description", ""),
                        )
                    )

        logger.info(f"Loaded {len(entries)} test IDs from registry")
        return entries

    # ------------------------------------------------------------------
    # Test-file scanning
    # ------------------------------------------------------------------

    def scan_test_files_for_testids(self) -> Set[str]:
        """Scan all ``test_*.py`` files for ``data-testid`` references.

        Returns
        -------
        set[str]
            Set of referenced test-ID strings.
        """
        test_path = self.project_root / self.test_dir
        if not test_path.exists():
            logger.warning(f"Test directory not found: {test_path}")
            return set()

        referenced: Set[str] = set()
        for test_file in sorted(test_path.rglob("test_*.py")):
            try:
                content = test_file.read_text(encoding="utf-8")
            except Exception:
                continue
            referenced.update(self._extract_testids_from_text(content))

        logger.info(f"Found {len(referenced)} unique test-ID references in test files")
        return referenced

    # ------------------------------------------------------------------
    # Coverage calculation
    # ------------------------------------------------------------------

    def calculate_coverage(
        self,
        scope: str = "full",
        changed_files: Optional[List[str]] = None,
    ) -> TestIdCoverageResult:
        """Calculate ``data-testid`` coverage.

        Parameters
        ----------
        scope : str
            ``"full"`` for the entire registry, ``"pr"`` to limit to
            flows touched by the PR (requires *changed_files*).
        changed_files : list[str], optional
            Paths changed in the PR (relative to project root).  Only
            used when *scope* is ``"pr"``.

        Returns
        -------
        TestIdCoverageResult
        """
        all_entries = self.load_registry()
        if not all_entries:
            return TestIdCoverageResult(
                total_testids=0,
                covered_testids=0,
                covered_ids=[],
                uncovered_ids=[],
                uncovered_entries=[],
                coverage_pct=0.0,
                scope=scope,
            )

        # Filter entries when PR-scoped
        if scope == "pr" and changed_files is not None:
            entries = self._filter_entries_by_changed_files(all_entries, changed_files)
        else:
            entries = all_entries

        if not entries:
            return TestIdCoverageResult(
                total_testids=0,
                covered_testids=0,
                covered_ids=[],
                uncovered_ids=[],
                uncovered_entries=[],
                coverage_pct=0.0,
                scope=scope,
            )

        referenced = self.scan_test_files_for_testids()

        # Build ID sets
        all_ids = {e.testid for e in entries}
        covered = all_ids & referenced
        uncovered = all_ids - referenced
        uncovered_entries = [e for e in entries if e.testid in uncovered]

        total = len(all_ids)
        pct = round(len(covered) / total * 100, 1) if total else 0.0

        logger.info(
            f"Test-ID coverage ({scope}): {len(covered)}/{total} "
            f"({pct}%) — {len(uncovered)} uncovered"
        )

        return TestIdCoverageResult(
            total_testids=total,
            covered_testids=len(covered),
            covered_ids=sorted(covered),
            uncovered_ids=sorted(uncovered),
            uncovered_entries=uncovered_entries,
            coverage_pct=pct,
            scope=scope,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_testids_from_text(text: str) -> Set[str]:
        """Extract all ``data-testid`` values from a block of text."""
        found: Set[str] = set()
        for pattern in TESTID_REFERENCE_PATTERNS:
            found.update(pattern.findall(text))
        return found

    @staticmethod
    def _filter_entries_by_changed_files(
        entries: List[TestIdEntry],
        changed_files: List[str],
    ) -> List[TestIdEntry]:
        """Return only entries whose *flow* or *area* matches a changed file.

        Matching heuristic: if any changed file path contains the flow
        name or the area name (case-insensitive) it is considered relevant.
        """
        lowered_paths = [p.lower() for p in changed_files]

        def _is_relevant(entry: TestIdEntry) -> bool:
            flow_kw = entry.flow.lower().replace("_", "-")
            area_kw = entry.area.lower().replace("_", "-")
            for path in lowered_paths:
                # Also match underscore variants
                path_norm = path.replace("_", "-")
                if flow_kw in path_norm or area_kw in path_norm:
                    return True
            return False

        return [e for e in entries if _is_relevant(e)]

    def generate_uncovered_report(
        self,
        result: TestIdCoverageResult,
    ) -> str:
        """Generate a markdown report of uncovered test IDs.

        Parameters
        ----------
        result : TestIdCoverageResult
            Output from :meth:`calculate_coverage`.

        Returns
        -------
        str
            Markdown-formatted report.
        """
        lines = [
            "## 🏷️ AutoQA Test-ID Coverage Report",
            "",
            f"**Scope:** {result.scope}",
            f"**Total test IDs:** {result.total_testids}",
            f"**Covered:** {result.covered_testids}",
            f"**Uncovered:** {len(result.uncovered_ids)}",
            f"**Coverage:** {result.coverage_pct}%",
            "",
        ]

        if not result.uncovered_entries:
            lines.append("✅ All registered `data-testid` values are covered by tests!\n")
            return "\n".join(lines)

        # Group uncovered by flow
        by_flow: Dict[str, List[TestIdEntry]] = {}
        for entry in result.uncovered_entries:
            by_flow.setdefault(entry.flow, []).append(entry)

        lines.append("### Uncovered Test IDs\n")
        lines.append("| Flow | Test ID | Tier | Area | Description |")
        lines.append("|------|---------|------|------|-------------|")
        for flow, flow_entries in sorted(by_flow.items()):
            for entry in flow_entries:
                desc = entry.description or "—"
                lines.append(
                    f"| `{flow}` | `{entry.testid}` | {entry.tier} | {entry.area} | {desc} |"
                )

        lines.append("")
        return "\n".join(lines)
