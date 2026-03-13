"""
AutoQA Memory Tracker: Persistent tracking of test status and coverage gaps.

Scans test directories, runs tests, records results (pass/fail/error/skip),
identifies missing test coverage, and persists state to a JSON memory file.
This enables tracking which tests need fixing and which areas lack tests.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default memory file location
DEFAULT_MEMORY_PATH = "reports/autoqa_memory.json"

# Source directories to scan for coverage gaps
DEFAULT_SOURCE_DIRS = ["src"]

# Test directory to scan
DEFAULT_TEST_DIR = "tests"


class MemoryEntry:
    """Represents a single test's tracked state in memory."""

    def __init__(
        self,
        test_id: str,
        file_path: str,
        status: str = "unknown",
        last_run: Optional[str] = None,
        error_message: Optional[str] = None,
        duration: Optional[float] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ):
        self.test_id = test_id
        self.file_path = file_path
        self.status = status
        self.last_run = last_run
        self.error_message = error_message
        self.duration = duration
        self.history = history or []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "test_id": self.test_id,
            "file_path": self.file_path,
            "status": self.status,
            "last_run": self.last_run,
            "error_message": self.error_message,
            "duration": self.duration,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Deserialize from dictionary."""
        return cls(
            test_id=data["test_id"],
            file_path=data["file_path"],
            status=data.get("status", "unknown"),
            last_run=data.get("last_run"),
            error_message=data.get("error_message"),
            duration=data.get("duration"),
            history=data.get("history", []),
        )


class CoverageGap:
    """Represents a source module that lacks test coverage."""

    def __init__(
        self,
        source_path: str,
        module_name: str,
        has_test: bool = False,
        test_file: Optional[str] = None,
        reason: str = "no_test_file",
    ):
        self.source_path = source_path
        self.module_name = module_name
        self.has_test = has_test
        self.test_file = test_file
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_path": self.source_path,
            "module_name": self.module_name,
            "has_test": self.has_test,
            "test_file": self.test_file,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoverageGap":
        """Deserialize from dictionary."""
        return cls(
            source_path=data["source_path"],
            module_name=data["module_name"],
            has_test=data.get("has_test", False),
            test_file=data.get("test_file"),
            reason=data.get("reason", "no_test_file"),
        )


class AutoQAMemoryTracker:
    """
    Tracks test execution results and coverage gaps persistently.

    The memory tracker:
    1. Scans test directories for existing test files
    2. Runs pytest and captures per-test results (pass/fail/error/skip)
    3. Identifies source modules that lack corresponding test files
    4. Persists all state to a JSON memory file
    5. Provides query methods for failing tests, missing tests, summaries
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        memory_path: Optional[str] = None,
        test_dir: Optional[str] = None,
        source_dirs: Optional[List[str]] = None,
    ):
        """
        Initialize the memory tracker.

        Args:
            project_root: Root directory of the project (defaults to cwd).
            memory_path: Path to the JSON memory file (relative to project_root).
            test_dir: Test directory to scan (relative to project_root).
            source_dirs: Source directories to scan for coverage gaps.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.memory_path = self.project_root / (memory_path or DEFAULT_MEMORY_PATH)
        self.test_dir = test_dir or DEFAULT_TEST_DIR
        self.source_dirs = source_dirs or DEFAULT_SOURCE_DIRS

        self.test_entries: Dict[str, MemoryEntry] = {}
        self.coverage_gaps: List[CoverageGap] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "schema_version": "1.0",
        }

    def load(self) -> bool:
        """
        Load existing memory from the JSON file.

        Returns:
            True if memory was loaded successfully, False if no file exists.
        """
        if not self.memory_path.exists():
            logger.info(f"No existing memory file at {self.memory_path}")
            return False

        try:
            with open(self.memory_path, "r") as f:
                data = json.load(f)

            self.metadata = data.get("metadata", self.metadata)
            self.test_entries = {
                tid: MemoryEntry.from_dict(entry)
                for tid, entry in data.get("test_entries", {}).items()
            }
            self.coverage_gaps = [
                CoverageGap.from_dict(gap) for gap in data.get("coverage_gaps", [])
            ]

            logger.info(
                f"Loaded memory: {len(self.test_entries)} tests, "
                f"{len(self.coverage_gaps)} coverage gaps"
            )
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load memory file: {e}")
            return False

    def save(self) -> None:
        """Save memory to the JSON file."""
        self.metadata["last_updated"] = datetime.now().isoformat()

        data = {
            "metadata": self.metadata,
            "test_entries": {tid: entry.to_dict() for tid, entry in self.test_entries.items()},
            "coverage_gaps": [gap.to_dict() for gap in self.coverage_gaps],
            "summary": self.get_summary(),
        }

        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Memory saved to {self.memory_path}")

    def scan_test_files(self) -> List[str]:
        """
        Scan the test directory for test files.

        Returns:
            List of test file paths (relative to project_root).
        """
        test_path = self.project_root / self.test_dir
        if not test_path.exists():
            logger.warning(f"Test directory not found: {test_path}")
            return []

        test_files = []
        for f in sorted(test_path.rglob("test_*.py")):
            rel_path = str(f.relative_to(self.project_root))
            test_files.append(rel_path)

        logger.info(f"Found {len(test_files)} test files in {self.test_dir}/")
        return test_files

    def scan_source_modules(self) -> List[str]:
        """
        Scan source directories for Python modules.

        Returns:
            List of source module paths (relative to project_root).
        """
        modules = []
        for src_dir in self.source_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue
            for f in sorted(src_path.rglob("*.py")):
                if f.name.startswith("__"):
                    continue
                rel_path = str(f.relative_to(self.project_root))
                modules.append(rel_path)

        logger.info(f"Found {len(modules)} source modules")
        return modules

    def identify_coverage_gaps(self) -> List[CoverageGap]:
        """
        Identify source modules that lack corresponding test files.

        A module is considered covered if there exists a test file whose name
        contains the module name (e.g., src/autoqa/parser.py → test_parser.py).

        Returns:
            List of CoverageGap objects for uncovered modules.
        """
        source_modules = self.scan_source_modules()
        test_files = self.scan_test_files()

        # Build set of test-covered module names from test filenames
        covered_names = set()
        for tf in test_files:
            # Extract the module name from test_<name>.py
            test_name = Path(tf).stem  # e.g., "test_criteria_generator"
            if test_name.startswith("test_"):
                covered_names.add(test_name[5:])  # e.g., "criteria_generator"

        gaps = []
        for module_path in source_modules:
            module_name = Path(module_path).stem  # e.g., "parser"

            # Check if there's a matching test file
            has_test = module_name in covered_names
            test_file = None
            if has_test:
                # Find the actual test file
                for tf in test_files:
                    if Path(tf).stem == f"test_{module_name}":
                        test_file = tf
                        break

            gap = CoverageGap(
                source_path=module_path,
                module_name=module_name,
                has_test=has_test,
                test_file=test_file,
                reason="covered" if has_test else "no_test_file",
            )
            gaps.append(gap)

        self.coverage_gaps = gaps

        uncovered = [g for g in gaps if not g.has_test]
        logger.info(
            f"Coverage analysis: {len(gaps)} modules, "
            f"{len(gaps) - len(uncovered)} covered, {len(uncovered)} missing tests"
        )
        return gaps

    def run_tests(self, test_path: Optional[str] = None, markers: Optional[str] = None) -> bool:
        """
        Run pytest and capture per-test results via JSON report.

        Args:
            test_path: Specific test path to run (defaults to test_dir).
            markers: Pytest marker expression to filter tests.

        Returns:
            True if all tests passed, False otherwise.
        """
        target = test_path or self.test_dir
        json_report_path = self.project_root / "reports" / "json" / "_memory_tracker_results.json"
        json_report_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            target,
            "-v",
            "--tb=short",
            "--no-header",
            "--json-report",
            f"--json-report-file={json_report_path}",
        ]

        if markers:
            cmd.extend(["-m", markers])

        logger.info(f"Running tests: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )

        # Parse JSON report
        if json_report_path.exists():
            self._parse_json_report(json_report_path)
            # Clean up temporary report
            try:
                json_report_path.unlink()
            except OSError:
                pass
        else:
            logger.warning("JSON report file not generated")

        return result.returncode == 0

    def _parse_json_report(self, report_path: Path) -> None:
        """
        Parse a pytest-json-report file and update memory entries.

        Args:
            report_path: Path to the JSON report file.
        """
        try:
            with open(report_path, "r") as f:
                report = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to parse JSON report: {e}")
            return

        now = datetime.now().isoformat()

        for test in report.get("tests", []):
            test_id = test.get("nodeid", "")
            outcome = test.get("outcome", "unknown")
            duration = test.get("duration", 0.0)

            # Map pytest outcomes to our status values
            status_map = {
                "passed": "passed",
                "failed": "failed",
                "error": "error",
                "skipped": "skipped",
                "xfailed": "xfailed",
                "xpassed": "xpassed",
            }
            status = status_map.get(outcome, "unknown")

            # Extract error message if present
            error_message = None
            call_info = test.get("call", {})
            if isinstance(call_info, dict):
                crash = call_info.get("crash", {})
                if isinstance(crash, dict):
                    error_message = crash.get("message")
                if not error_message:
                    longrepr = call_info.get("longrepr")
                    if longrepr and isinstance(longrepr, str):
                        # Truncate long error messages
                        error_message = longrepr[:500]

            # Check setup phase for errors too
            setup_info = test.get("setup", {})
            if isinstance(setup_info, dict) and setup_info.get("outcome") == "error":
                status = "error"
                crash = setup_info.get("crash", {})
                if isinstance(crash, dict):
                    error_message = crash.get("message")

            # Extract file path from test_id
            file_path = test_id.split("::")[0] if "::" in test_id else test_id

            # Update or create memory entry
            if test_id in self.test_entries:
                entry = self.test_entries[test_id]
                # Append to history
                entry.history.append(
                    {
                        "status": entry.status,
                        "timestamp": entry.last_run,
                        "error_message": entry.error_message,
                    }
                )
                # Keep history bounded
                entry.history = entry.history[-10:]
                # Update current state
                entry.status = status
                entry.last_run = now
                entry.error_message = error_message
                entry.duration = duration
            else:
                self.test_entries[test_id] = MemoryEntry(
                    test_id=test_id,
                    file_path=file_path,
                    status=status,
                    last_run=now,
                    error_message=error_message,
                    duration=duration,
                )

        logger.info(f"Updated memory with {len(report.get('tests', []))} test results")

    def get_failing_tests(self) -> List[MemoryEntry]:
        """Get all tests with 'failed' or 'error' status."""
        return [e for e in self.test_entries.values() if e.status in ("failed", "error")]

    def get_passing_tests(self) -> List[MemoryEntry]:
        """Get all tests with 'passed' status."""
        return [e for e in self.test_entries.values() if e.status == "passed"]

    def get_missing_tests(self) -> List[CoverageGap]:
        """Get source modules that lack test files."""
        return [g for g in self.coverage_gaps if not g.has_test]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current memory state.

        Returns:
            Dictionary with counts by status and coverage info.
        """
        status_counts: Dict[str, int] = {}
        for entry in self.test_entries.values():
            status_counts[entry.status] = status_counts.get(entry.status, 0) + 1

        total_modules = len(self.coverage_gaps)
        covered_modules = sum(1 for g in self.coverage_gaps if g.has_test)
        uncovered_modules = total_modules - covered_modules

        return {
            "total_tests": len(self.test_entries),
            "status_counts": status_counts,
            "total_source_modules": total_modules,
            "covered_modules": covered_modules,
            "uncovered_modules": uncovered_modules,
            "coverage_percentage": (
                round(covered_modules / total_modules * 100, 1) if total_modules > 0 else 0
            ),
        }

    def generate_report(self) -> str:
        """
        Generate a human-readable markdown report of the memory state.

        Returns:
            Markdown-formatted report string.
        """
        summary = self.get_summary()
        lines = [
            "# 📋 AutoQA Memory Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Memory file:** `{self.memory_path}`",
            "",
            "---",
            "",
            "## 📊 Test Results Summary",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| Total Tests | {summary['total_tests']} |",
        ]

        for status, count in sorted(summary["status_counts"].items()):
            emoji = {
                "passed": "✅",
                "failed": "❌",
                "error": "💥",
                "skipped": "⏭️",
            }.get(status, "❓")
            lines.append(f"| {emoji} {status.title()} | {count} |")

        lines.extend(
            [
                "",
                "## 🔍 Test Coverage",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Source Modules | {summary['total_source_modules']} |",
                f"| Covered | {summary['covered_modules']} |",
                f"| Uncovered | {summary['uncovered_modules']} |",
                f"| Coverage | {summary['coverage_percentage']}% |",
            ]
        )

        # Failing tests section
        failing = self.get_failing_tests()
        if failing:
            lines.extend(
                [
                    "",
                    "## ❌ Failing Tests",
                    "",
                    "| Test | Status | Error |",
                    "|------|--------|-------|",
                ]
            )
            for entry in failing:
                error_short = (entry.error_message or "")[:80].replace("|", "\\|")
                lines.append(f"| `{entry.test_id}` | {entry.status} | {error_short} |")

        # Missing tests section
        missing = self.get_missing_tests()
        if missing:
            lines.extend(
                [
                    "",
                    "## 🔧 Missing Tests",
                    "",
                    "| Source Module | Suggested Test File |",
                    "|--------------|---------------------|",
                ]
            )
            for gap in missing:
                suggested = f"tests/test_{gap.module_name}.py"
                lines.append(f"| `{gap.source_path}` | `{suggested}` |")

        lines.append("")
        return "\n".join(lines)

    def update(self, run_tests: bool = True) -> Dict[str, Any]:
        """
        Full update cycle: load, scan, optionally run tests, and save.

        Args:
            run_tests: Whether to run pytest and capture results.

        Returns:
            Summary dictionary.
        """
        self.load()
        self.identify_coverage_gaps()

        if run_tests:
            self.run_tests()

        self.save()
        return self.get_summary()
