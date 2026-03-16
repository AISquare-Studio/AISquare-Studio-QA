"""
Gap Analysis Database Manager for AutoQA.

Provides a SQLite-backed store for tracking which test workflows exist
and which are missing.  The database is created automatically if it does
not exist, making it safe to run on repositories that already have AutoQA
tests but have never used the gap-analysis feature.

Tables
------
workflows_present
    Records of test workflows that exist in the repository.
workflows_missing
    Records of source modules / functional areas that lack tests.
analysis_runs
    Metadata for each gap-analysis execution.
testid_coverage
    Records of ``data-testid`` coverage from the test-ID registry.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.autoqa.memory_tracker import AutoQAMemoryTracker
from src.autoqa.testid_scanner import TestIdScanner
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default database location
DEFAULT_DB_PATH = "reports/gap_analysis.db"


class GapAnalysisDB:
    """SQLite database for persisting gap-analysis results.

    Attributes:
        db_path: Absolute path to the SQLite database file.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        db_path: Optional[str] = None,
        test_dir: Optional[str] = None,
        source_dirs: Optional[List[str]] = None,
        scope: str = "full",
        changed_files: Optional[List[str]] = None,
        registry_path: Optional[str] = None,
    ):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / (db_path or DEFAULT_DB_PATH)
        self.test_dir = test_dir or "tests"
        self.source_dirs = source_dirs or ["src"]
        self.scope = scope
        self.changed_files = changed_files
        self.registry_path = registry_path
        self._ensure_db()

    # ------------------------------------------------------------------
    # Database setup
    # ------------------------------------------------------------------

    def _ensure_db(self) -> None:
        """Create the database and tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        created = not self.db_path.exists()
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   TEXT    NOT NULL,
                    total_modules   INTEGER NOT NULL DEFAULT 0,
                    present_count   INTEGER NOT NULL DEFAULT 0,
                    missing_count   INTEGER NOT NULL DEFAULT 0,
                    coverage_pct    REAL    NOT NULL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS workflows_present (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id      INTEGER NOT NULL,
                    module_name TEXT    NOT NULL,
                    source_path TEXT    NOT NULL,
                    test_file   TEXT,
                    tier        TEXT,
                    area        TEXT,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS workflows_missing (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id      INTEGER NOT NULL,
                    module_name TEXT    NOT NULL,
                    source_path TEXT    NOT NULL,
                    reason      TEXT    NOT NULL DEFAULT 'no_test_file',
                    suggested_test TEXT,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS testid_coverage (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id      INTEGER NOT NULL,
                    testid      TEXT    NOT NULL,
                    flow        TEXT    NOT NULL,
                    area        TEXT    NOT NULL DEFAULT 'general',
                    tier        TEXT    NOT NULL DEFAULT 'C',
                    covered     INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

        if created:
            logger.info(f"Created gap-analysis database at {self.db_path}")
        else:
            logger.info(f"Opened existing gap-analysis database at {self.db_path}")

    # ------------------------------------------------------------------
    # Analysis execution
    # ------------------------------------------------------------------

    def run_analysis(self) -> Dict[str, Any]:
        """Execute gap analysis and persist results to the database.

        Scans source directories and test directories using the memory
        tracker, then writes the results into the ``workflows_present``
        and ``workflows_missing`` tables.  Additionally scans for
        ``data-testid`` coverage from the test-ID registry.

        Returns:
            Summary dict with keys ``run_id``, ``timestamp``,
            ``total_modules``, ``present_count``, ``missing_count``,
            ``coverage_pct``, ``workflows_present``,
            ``workflows_missing``, and ``testid_coverage``.
        """
        tracker = AutoQAMemoryTracker(
            project_root=str(self.project_root),
            test_dir=self.test_dir,
            source_dirs=self.source_dirs,
        )
        tracker.load()
        gaps = tracker.identify_coverage_gaps()

        present = [g for g in gaps if g.has_test]
        missing = [g for g in gaps if not g.has_test]
        total = len(gaps)
        coverage_pct = round(len(present) / total * 100, 1) if total > 0 else 0.0
        timestamp = datetime.now().isoformat()

        # ---- test-ID coverage ------------------------------------------
        scanner = TestIdScanner(
            project_root=str(self.project_root),
            registry_path=self.registry_path,
            test_dir=self.test_dir,
        )
        testid_result = scanner.calculate_coverage(
            scope=self.scope,
            changed_files=self.changed_files,
        )

        # Persist to database
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO analysis_runs
                   (timestamp, total_modules, present_count, missing_count, coverage_pct)
                   VALUES (?, ?, ?, ?, ?)""",
                (timestamp, total, len(present), len(missing), coverage_pct),
            )
            run_id = cur.lastrowid

            for g in present:
                cur.execute(
                    """INSERT INTO workflows_present
                       (run_id, module_name, source_path, test_file, tier, area)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        g.module_name,
                        g.source_path,
                        g.test_file,
                        self._infer_tier(g.source_path),
                        self._infer_area(g.source_path),
                    ),
                )

            for g in missing:
                suggested = self._suggested_test_path(g.module_name)
                cur.execute(
                    """INSERT INTO workflows_missing
                       (run_id, module_name, source_path, reason, suggested_test)
                       VALUES (?, ?, ?, ?, ?)""",
                    (run_id, g.module_name, g.source_path, g.reason, suggested),
                )

            # Persist test-ID coverage rows
            # Build lookup from all registry entries for covered IDs
            all_registry = scanner.load_registry()
            entry_by_id = {e.testid: e for e in all_registry}

            for entry in testid_result.uncovered_entries:
                cur.execute(
                    """INSERT INTO testid_coverage
                       (run_id, testid, flow, area, tier, covered)
                       VALUES (?, ?, ?, ?, ?, 0)""",
                    (run_id, entry.testid, entry.flow, entry.area, entry.tier),
                )
            for tid in testid_result.covered_ids:
                reg = entry_by_id.get(tid)
                cur.execute(
                    """INSERT INTO testid_coverage
                       (run_id, testid, flow, area, tier, covered)
                       VALUES (?, ?, ?, ?, ?, 1)""",
                    (
                        run_id,
                        tid,
                        reg.flow if reg else "",
                        reg.area if reg else "",
                        reg.tier if reg else "",
                    ),
                )

            conn.commit()
        finally:
            conn.close()

        present_list = [
            {
                "module_name": g.module_name,
                "source_path": g.source_path,
                "test_file": g.test_file,
                "tier": self._infer_tier(g.source_path),
                "area": self._infer_area(g.source_path),
            }
            for g in present
        ]
        missing_list = [
            {
                "module_name": g.module_name,
                "source_path": g.source_path,
                "reason": g.reason,
                "suggested_test": self._suggested_test_path(g.module_name),
            }
            for g in missing
        ]

        logger.info(
            f"Gap analysis complete: {len(present)} present, "
            f"{len(missing)} missing ({coverage_pct}% coverage)"
        )

        return {
            "run_id": run_id,
            "timestamp": timestamp,
            "total_modules": total,
            "present_count": len(present),
            "missing_count": len(missing),
            "coverage_pct": coverage_pct,
            "workflows_present": present_list,
            "workflows_missing": missing_list,
            "testid_coverage": testid_result.to_dict(),
        }

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Return the most recent analysis run summary, or ``None``."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT * FROM analysis_runs ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                return None

            run_id = row["id"]
            present = [
                dict(r)
                for r in conn.execute(
                    "SELECT module_name, source_path, test_file, tier, area "
                    "FROM workflows_present WHERE run_id = ?",
                    (run_id,),
                ).fetchall()
            ]
            missing = [
                dict(r)
                for r in conn.execute(
                    "SELECT module_name, source_path, reason, suggested_test "
                    "FROM workflows_missing WHERE run_id = ?",
                    (run_id,),
                ).fetchall()
            ]

            return {
                "run_id": row["id"],
                "timestamp": row["timestamp"],
                "total_modules": row["total_modules"],
                "present_count": row["present_count"],
                "missing_count": row["missing_count"],
                "coverage_pct": row["coverage_pct"],
                "workflows_present": present,
                "workflows_missing": missing,
            }
        finally:
            conn.close()

    def get_run_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return summaries of recent analysis runs (most recent first)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM analysis_runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Tier / area inference helpers
    # ------------------------------------------------------------------

    _CRITICAL_KEYWORDS = ["auth", "payment", "checkout", "signup", "login"]
    _IMPORTANT_KEYWORDS = ["dashboard", "settings", "profile", "search", "account"]

    def _infer_tier(self, source_path: str) -> str:
        lowered = source_path.lower()
        for kw in self._CRITICAL_KEYWORDS:
            if kw in lowered:
                return "A"
        for kw in self._IMPORTANT_KEYWORDS:
            if kw in lowered:
                return "B"
        return "C"

    @staticmethod
    def _suggested_test_path(module_name: str) -> str:
        """Return the conventional test file path for a module."""
        return f"tests/test_{module_name}.py"

    @staticmethod
    def _infer_area(source_path: str) -> str:
        parts = Path(source_path).parts
        if len(parts) >= 2:
            return parts[-2]
        return "general"
