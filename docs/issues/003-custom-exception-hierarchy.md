<!--
Title: [IMPROVE] Add custom exception hierarchy for structured error handling
Labels: enhancement, code quality, help wanted
-->

# Add Custom Exception Hierarchy for Structured Error Handling

## Summary

The codebase currently uses broad `except Exception` patterns throughout core modules, which
masks bugs, prevents callers from handling specific failure modes, and makes debugging difficult.
A structured exception hierarchy would improve error handling, logging, and resilience.

## Problem

Multiple components catch `Exception` generically, losing valuable error context:

**`src/autoqa/action_runner.py` (line ~113):**
```python
except Exception as e:
    logger.error(f"AutoQA Action failed: {str(e)}")
    return self._set_outputs({"test_generated": "false", "error": str(e)})
```

**`src/crews/qa_crew.py` (line ~207):**
```python
except Exception:
    execution_data = {
        "success": False,
        "error": "Failed to parse execution result",
        "raw_result": str(execution_result),
    }
```

**`src/tools/dom_inspector.py` (line ~68):**
```python
except Exception as e:
    logger.error(f"Failed to discover selectors: {str(e)}")
    return {}
```

This makes it impossible to distinguish between:
- A parse error in the PR body (user fixable)
- An LLM API failure (retry-worthy)
- A Playwright browser crash (infrastructure issue)
- A security validation failure (should block execution)

## Proposed Solution

### 1. Create `src/exceptions.py` with the following hierarchy:

```python
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


class AutoQAExecutionError(AutoQAError):
    """Raised when test code execution fails."""
    pass


class AutoQAGenerationError(AutoQAError):
    """Raised when LLM code generation fails."""
    pass


class AutoQABrowserError(AutoQAExecutionError):
    """Raised when Playwright browser operations fail."""
    pass


class AutoQAGitHubAPIError(AutoQAError):
    """Raised when GitHub API operations fail."""
    pass
```

### 2. Update exception handling in key modules:

**In `src/autoqa/parser.py`:**
```python
from src.exceptions import AutoQAParseError, AutoQAValidationError

# Replace generic exceptions with specific ones
raise AutoQAParseError(f"Failed to extract autoqa block: {details}")
```

**In `src/agents/executor_agent.py`:**
```python
from src.exceptions import AutoQASecurityError

# In validate_code_safety():
raise AutoQASecurityError(f"Blocked import: {module_name}")
```

**In `src/autoqa/action_runner.py`:**
```python
from src.exceptions import (
    AutoQAError,
    AutoQAParseError,
    AutoQAGenerationError,
)

try:
    # ... execution logic
except AutoQAParseError as e:
    logger.error(f"PR parsing failed: {e}")
    return self._set_outputs({"test_generated": "false", "error": str(e)})
except AutoQAGenerationError as e:
    logger.error(f"Code generation failed: {e}")
    # Could retry here
except AutoQAError as e:
    logger.error(f"AutoQA failed: {e}")
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
```

### 3. Add unit tests for the exception hierarchy

```python
def test_autoqa_parse_error_is_autoqa_error():
    assert issubclass(AutoQAParseError, AutoQAError)

def test_autoqa_browser_error_is_execution_error():
    assert issubclass(AutoQABrowserError, AutoQAExecutionError)
```

## Files to Modify

| File | Change |
|------|--------|
| `src/exceptions.py` | **New** — Exception class definitions |
| `src/autoqa/parser.py` | Replace generic exceptions |
| `src/autoqa/action_runner.py` | Add specific exception handling |
| `src/agents/executor_agent.py` | Raise `AutoQASecurityError` |
| `src/crews/qa_crew.py` | Replace broad catches |
| `src/tools/dom_inspector.py` | Raise `AutoQABrowserError` |
| `tests/test_exceptions.py` | **New** — Test exception hierarchy |

## Acceptance Criteria

- [ ] `src/exceptions.py` defines the exception hierarchy
- [ ] At least 3 modules updated to use specific exceptions
- [ ] Broad `except Exception` catches are narrowed where possible
- [ ] New exceptions are importable and properly inherit from `AutoQAError`
- [ ] Unit tests validate the exception hierarchy
- [ ] Existing functionality is not broken
