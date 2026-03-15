#!/usr/bin/env python3
"""
AISquare Studio QA - Main Test Runner
====================================

Production-ready AI-powered testing framework for login/signup functionality.
Powered by CrewAI + Playwright with OpenAI GPT-4 integration.

Usage:
    python qa_runner.py                    # Run all tests
    python qa_runner.py --help             # Show help

Requirements:
    - OpenAI API key (for AI test generation)
    - Staging environment credentials
    - Python 3.11+ with requirements.txt installed

Authors: GitHub Copilot + AISquare Studio
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_banner():
    """Print the application banner."""
    print("=" * 70)
    print("🚀 AISquare Studio QA - AI-Powered Test Automation")
    print("=" * 70)
    print("📅 Framework: CrewAI + Playwright + OpenAI GPT-4")
    print(f"📅 Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()


def run_staging_tests():
    """Run tests against staging environment."""
    print("� Running tests against staging environment...")

    # Check if .env exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ No .env file found. Please create one with your staging configuration.")
        print("💡 See README.md for setup instructions.")
        return False

    # Create timestamp for reports
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure reports directories exist
    html_reports_dir = project_root / "reports" / "html"
    json_reports_dir = project_root / "reports" / "json"
    html_reports_dir.mkdir(parents=True, exist_ok=True)
    json_reports_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HEADLESS_MODE"] = env.get("HEADLESS_MODE", "true")

    # Generate HTML and JSON reports
    html_report_path = html_reports_dir / f"test_execution_{timestamp}.html"
    json_report_path = json_reports_dir / f"test_execution_{timestamp}.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes",
            "--durations=10",
            f"--html={html_report_path}",
            "--self-contained-html",
            "--json-report",
            f"--json-report-file={json_report_path}",
        ],
        cwd=project_root,
        env=env,
    )

    if result.returncode == 0:
        print("📊 Reports generated:")
        print(f"   HTML: {html_report_path}")
        print(f"   JSON: {json_report_path}")
    else:
        print("📊 Reports generated (with test failures):")
        print(f"   HTML: {html_report_path}")
        print(f"   JSON: {json_report_path}")

    return result.returncode == 0


def run_memory_scan():
    """Scan tests and source files, update memory without running tests."""
    from src.autoqa.memory_tracker import AutoQAMemoryTracker

    tracker = AutoQAMemoryTracker(project_root=str(project_root))
    tracker.load()
    tracker.identify_coverage_gaps()
    tracker.save()

    summary = tracker.get_summary()
    print("📋 AutoQA Memory Scan Complete")
    print(f"   Source modules:  {summary['total_source_modules']}")
    print(f"   Covered:         {summary['covered_modules']}")
    print(f"   Missing tests:   {summary['uncovered_modules']}")
    print(f"   Coverage:        {summary['coverage_percentage']}%")
    print(f"   Memory saved to: {tracker.memory_path}")
    return True


def run_memory_update():
    """Run tests and update the memory with results."""
    from src.autoqa.memory_tracker import AutoQAMemoryTracker

    tracker = AutoQAMemoryTracker(project_root=str(project_root))
    summary = tracker.update(run_tests=True)

    print("📋 AutoQA Memory Update Complete")
    print(f"   Total tests:     {summary['total_tests']}")
    for status, count in sorted(summary["status_counts"].items()):
        emoji = {"passed": "✅", "failed": "❌", "error": "💥", "skipped": "⏭️"}.get(status, "❓")
        print(f"   {emoji} {status.title()}: {count}")
    print(f"   Coverage:        {summary['coverage_percentage']}%")
    print(f"   Memory saved to: {tracker.memory_path}")
    return summary["status_counts"].get("failed", 0) == 0


def run_memory_report():
    """Generate and print a markdown report from current memory."""
    from src.autoqa.memory_tracker import AutoQAMemoryTracker

    tracker = AutoQAMemoryTracker(project_root=str(project_root))
    if not tracker.load():
        print("❌ No memory file found. Run --memory-update first.")
        return False

    # Reload coverage gaps from disk
    tracker.identify_coverage_gaps()
    report = tracker.generate_report()
    print(report)
    return True


def run_gap_driven():
    """Generate test criteria for uncovered modules based on memory gaps."""
    from src.autoqa.gap_driven_generator import GapDrivenGenerator

    generator = GapDrivenGenerator(project_root=str(project_root))
    result = generator.generate_criteria_for_gaps()

    if not result.get("success"):
        print(f"❌ Gap-driven generation failed: {result.get('error', 'unknown')}")
        return False

    criteria = result.get("criteria", [])
    gaps_found = result.get("gaps_found", 0)

    print("📋 AutoQA Gap-Driven Test Criteria")
    print(f"   Uncovered modules: {gaps_found}")
    print(f"   Criteria generated: {len(criteria)}")
    print()

    if not criteria:
        print("   ✅ No testable flows found in uncovered modules.")
        return True

    for i, c in enumerate(criteria, 1):
        confidence = c.get("confidence", 0)
        print(f"   {i}. {c['flow_name']} (Tier {c['tier']}, Area: {c['area']})")
        print(f"      Source: {c.get('source_module', 'unknown')}")
        print(f"      Confidence: {confidence}/100")
        print(f"      Steps: {len(c.get('steps', []))}")
        print()

    # Print full comment body
    comment_body = result.get("comment_body", "")
    if comment_body:
        print("---")
        print(comment_body)

    return True


def run_gap_analysis():
    """Run gap analysis and persist results to a SQLite database."""
    from src.autoqa.gap_analysis_db import GapAnalysisDB

    db = GapAnalysisDB(project_root=str(project_root))
    results = db.run_analysis()

    print("📋 AutoQA Gap Analysis Complete")
    print(f"   Database:        {db.db_path}")
    print(f"   Total modules:   {results['total_modules']}")
    print(f"   Present:         {results['present_count']}")
    print(f"   Missing:         {results['missing_count']}")
    print(f"   Coverage:        {results['coverage_pct']}%")
    print()

    if results["workflows_present"]:
        print("   ✅ Workflows Present:")
        for w in results["workflows_present"]:
            test = w.get("test_file") or "N/A"
            print(f"      • {w['module_name']} ({w['source_path']}) → {test}")
        print()

    if results["workflows_missing"]:
        print("   ❌ Workflows Missing:")
        for w in results["workflows_missing"]:
            suggested = w.get("suggested_test") or "N/A"
            print(f"      • {w['module_name']} ({w['source_path']}) → {suggested}")
        print()

    return True


def show_help():
    """Show detailed help information."""
    print_banner()
    print("📖 HELP & DOCUMENTATION")
    print("=" * 70)
    print()
    print("🎯 QUICK START:")
    print("   1. Create .env file with staging configuration")
    print("   2. python qa_runner.py                   # Run all tests")
    print()
    print("🔧 COMMANDS:")
    print("   --help              Show this help message")
    print("   --memory-scan       Scan tests and source files for coverage gaps")
    print("   --memory-update     Run tests and update memory with results")
    print("   --memory-report     Print a markdown report from current memory")
    print("   --gap-driven        Generate test criteria for uncovered modules")
    print("   --gap-analysis      Run gap analysis and persist results to database")
    print()
    print("📁 PROJECT STRUCTURE:")
    print("   config/             Configuration files (YAML)")
    print("   src/                AI agents and tools")
    print("   tests/              Pytest test suites")
    print("   reports/            Test execution reports and screenshots")
    print()
    print("🌐 ENVIRONMENT VARIABLES:")
    print("   OPENAI_API_KEY      Required for AI test generation")
    print("   STAGING_LOGIN_URL   Your staging login page URL")
    print("   STAGING_EMAIL       Test email for staging")
    print("   STAGING_PASSWORD    Test password for staging")
    print()
    print("📚 DOCUMENTATION:")
    print("   README.md           Main project documentation")
    print()
    print("🐛 TROUBLESHOOTING:")
    print("   • Check .env file configuration")
    print("   • Verify OpenAI API key is valid")
    print("   • Review HTML reports in reports/html/ for detailed results")
    print("   • Check screenshots in reports/screenshots/ for visual debugging")
    print()


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="AISquare Studio QA - AI-Powered Test Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python qa_runner.py                    # Run all staging tests
    python qa_runner.py --memory-scan      # Scan for coverage gaps
    python qa_runner.py --memory-update    # Run tests and update memory
    python qa_runner.py --memory-report    # Print memory report
    python qa_runner.py --gap-driven       # Generate tests for uncovered modules
    python qa_runner.py --gap-analysis     # Run gap analysis to database
        """,
    )

    parser.add_argument(
        "--help-detailed", action="store_true", help="Show detailed help and documentation"
    )
    parser.add_argument(
        "--memory-scan",
        action="store_true",
        help="Scan tests and source files for coverage gaps",
    )
    parser.add_argument(
        "--memory-update",
        action="store_true",
        help="Run tests and update memory with results",
    )
    parser.add_argument(
        "--memory-report",
        action="store_true",
        help="Print a markdown report from current memory",
    )
    parser.add_argument(
        "--gap-driven",
        action="store_true",
        help="Generate test criteria for uncovered modules based on memory gaps",
    )
    parser.add_argument(
        "--gap-analysis",
        action="store_true",
        help="Run gap analysis and persist present/missing workflows to a SQLite database",
    )

    args = parser.parse_args()

    # Handle detailed help
    if args.help_detailed:
        show_help()
        return True

    # Handle memory commands
    if args.memory_scan:
        print_banner()
        return run_memory_scan()

    if args.memory_update:
        print_banner()
        return run_memory_update()

    if args.memory_report:
        return run_memory_report()

    if args.gap_driven:
        print_banner()
        return run_gap_driven()

    if args.gap_analysis:
        print_banner()
        return run_gap_analysis()

    # Default: run staging tests
    print("🎯 Running AI-powered tests against staging environment...")
    print("💡 Ensure .env file is configured with staging details")
    print("💡 Use --help-detailed for comprehensive documentation")
    print()

    return run_staging_tests()


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1

        if success:
            print("\n🎉 All operations completed successfully!")
        else:
            print("\n❌ Some operations failed. Check output above.")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
