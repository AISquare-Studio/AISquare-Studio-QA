"""
Pytest configuration and enhanced fixtures for better test reporting.
"""

import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "screenshots").mkdir(exist_ok=True)
    (reports_dir / "html").mkdir(exist_ok=True)
    (reports_dir / "json").mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def reports_dir(project_root):
    """Ensure reports directory exists."""
    reports_path = project_root / "reports"
    screenshots_path = reports_path / "screenshots"
    html_path = reports_path / "html"
    json_path = reports_path / "json"

    reports_path.mkdir(exist_ok=True)
    screenshots_path.mkdir(exist_ok=True)
    html_path.mkdir(exist_ok=True)
    json_path.mkdir(exist_ok=True)

    return reports_path


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from environment."""
    from dotenv import load_dotenv

    load_dotenv()

    return {
        "login_url": os.getenv("STAGING_LOGIN_URL", "https://example.com/login"),
        "base_url": os.getenv("STAGING_URL", "https://example.com"),
        "valid_email": os.getenv("VALID_EMAIL", "test@example.com"),
        "valid_password": os.getenv("VALID_PASSWORD", "password123"),
        "invalid_email": os.getenv("INVALID_EMAIL", "invalid@example.com"),
        "invalid_password": os.getenv("INVALID_PASSWORD", "wrongpassword"),
        "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
        "timeout": int(os.getenv("TIMEOUT", "30000")),
    }


@pytest.fixture(autouse=True)
def test_info(request):
    """Provide test information for each test."""
    test_name = request.node.name
    test_class = request.node.cls.__name__ if request.node.cls else "NoClass"

    print(f"\\n🧪 Running Test: {test_class}::{test_name}")

    yield

    print(f"✅ Completed Test: {test_class}::{test_name}")


def pytest_runtest_makereport(item, call):
    """Generate custom test reports."""
    if call.when == "call":
        # Add custom data to test report
        if hasattr(item, "rep_setup"):
            item.rep_setup.outcome = call.outcome
        if hasattr(item, "rep_call"):
            item.rep_call.outcome = call.outcome
