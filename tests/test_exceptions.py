"""Tests for the AutoQA custom exception hierarchy."""

import pytest

from src.exceptions import (
    AutoQABrowserError,
    AutoQAError,
    AutoQAExecutionError,
    AutoQAGenerationError,
    AutoQAGitHubAPIError,
    AutoQAParseError,
    AutoQASecurityError,
    AutoQAValidationError,
)


class TestExceptionHierarchy:
    """Verify that all exceptions inherit correctly."""

    def test_parse_error_is_autoqa_error(self):
        assert issubclass(AutoQAParseError, AutoQAError)

    def test_validation_error_is_autoqa_error(self):
        assert issubclass(AutoQAValidationError, AutoQAError)

    def test_security_error_is_autoqa_error(self):
        assert issubclass(AutoQASecurityError, AutoQAError)

    def test_generation_error_is_autoqa_error(self):
        assert issubclass(AutoQAGenerationError, AutoQAError)

    def test_execution_error_is_autoqa_error(self):
        assert issubclass(AutoQAExecutionError, AutoQAError)

    def test_browser_error_is_execution_error(self):
        assert issubclass(AutoQABrowserError, AutoQAExecutionError)

    def test_browser_error_is_autoqa_error(self):
        assert issubclass(AutoQABrowserError, AutoQAError)

    def test_github_api_error_is_autoqa_error(self):
        assert issubclass(AutoQAGitHubAPIError, AutoQAError)


class TestExceptionMessages:
    """Verify exceptions carry messages correctly."""

    def test_parse_error_message(self):
        err = AutoQAParseError("Missing autoqa block")
        assert str(err) == "Missing autoqa block"

    def test_security_error_message(self):
        err = AutoQASecurityError("Blocked import: subprocess")
        assert str(err) == "Blocked import: subprocess"

    def test_browser_error_caught_as_execution_error(self):
        with pytest.raises(AutoQAExecutionError):
            raise AutoQABrowserError("Browser crashed")

    def test_all_caught_as_autoqa_error(self):
        exceptions = [
            AutoQAParseError("a"),
            AutoQAValidationError("b"),
            AutoQASecurityError("c"),
            AutoQAGenerationError("d"),
            AutoQAExecutionError("e"),
            AutoQABrowserError("f"),
            AutoQAGitHubAPIError("g"),
        ]
        for exc in exceptions:
            with pytest.raises(AutoQAError):
                raise exc
