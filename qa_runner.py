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
            f"--json-report",
            f"--json-report-file={json_report_path}",
        ],
        cwd=project_root,
        env=env,
    )

    if result.returncode == 0:
        print(f"📊 Reports generated:")
        print(f"   HTML: {html_report_path}")
        print(f"   JSON: {json_report_path}")
    else:
        print(f"📊 Reports generated (with test failures):")
        print(f"   HTML: {html_report_path}")
        print(f"   JSON: {json_report_path}")

    return result.returncode == 0


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
        """,
    )

    parser.add_argument(
        "--help-detailed", action="store_true", help="Show detailed help and documentation"
    )

    args = parser.parse_args()

    # Handle detailed help
    if args.help_detailed:
        show_help()
        return True

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
