"""Custom exception hierarchy for structured error handling in AutoQA."""


class AutoQAError(Exception):
    """Base exception for all AutoQA errors."""

    pass


class AutoQAParseError(AutoQAError):
    """Raised when PR body or autoqa block parsing fails."""

    pass


class AutoQAValidationError(AutoQAError):
    """Raised when metadata or configuration validation fails."""

    pass


class AutoQASecurityError(AutoQAError):
    """Raised when code fails AST safety validation."""

    pass


class AutoQAGenerationError(AutoQAError):
    """Raised when LLM code generation fails."""

    pass


class AutoQAExecutionError(AutoQAError):
    """Raised when test code execution fails."""

    pass


class AutoQABrowserError(AutoQAExecutionError):
    """Raised when Playwright browser operations fail."""

    pass


class AutoQAGitHubAPIError(AutoQAError):
    """Raised when GitHub API operations fail."""

    pass
