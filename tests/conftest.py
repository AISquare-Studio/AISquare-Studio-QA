"""
Pytest configuration and fixtures.
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def reports_dir(project_root):
    """Ensure reports directory exists."""
    reports_path = project_root / "reports"
    screenshots_path = reports_path / "screenshots"
    
    reports_path.mkdir(exist_ok=True)
    screenshots_path.mkdir(exist_ok=True)
    
    return reports_path


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from environment."""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        'login_url': os.getenv('STAGING_LOGIN_URL', 'https://example.com/login'),
        'base_url': os.getenv('STAGING_URL', 'https://example.com'),
        'valid_email': os.getenv('VALID_EMAIL', 'test@example.com'),
        'valid_password': os.getenv('VALID_PASSWORD', 'password123'),
        'invalid_email': os.getenv('INVALID_EMAIL', 'invalid@example.com'),
        'invalid_password': os.getenv('INVALID_PASSWORD', 'wrongpassword'),
        'headless': os.getenv('HEADLESS_MODE', 'false').lower() == 'true',
        'timeout': int(os.getenv('TIMEOUT', '30000'))
    }
