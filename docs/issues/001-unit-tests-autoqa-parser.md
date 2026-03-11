<!--
Title: [TESTING] Add unit tests for AutoQAParser
Labels: good first issue, testing, help wanted
-->

# Add Unit Tests for `AutoQAParser`

## Summary

The `AutoQAParser` class (`src/autoqa/parser.py`) is a core component responsible for parsing PR
descriptions, extracting metadata, validating inputs, and computing ETags for idempotency. It
currently has **zero dedicated unit tests**, making it risky for contributors to modify without
confidence that existing behavior is preserved.

## Why This Matters

- Contributors cannot verify their parser changes don't break existing functionality
- The parser is a critical entry point — bugs here cascade through the entire pipeline
- Good test coverage makes code review faster and more reliable

## What to Test

The `AutoQAParser` class has the following public methods that need test coverage:

### `has_autoqa_tag(pr_body: str) -> bool`
- ✅ Returns `True` when PR body contains a valid `autoqa` fenced code block
- ✅ Returns `False` for empty string, `None`, or PR bodies without the tag
- ✅ Edge case: multiple code blocks where only one is `autoqa`

### `extract_autoqa_block(pr_body: str) -> Optional[Dict]`
- ✅ Extracts metadata and steps from a well-formed block
- ✅ Returns `None` for malformed or missing blocks
- ✅ Handles blocks with only metadata (no steps)

### `parse_autoqa_metadata(metadata_block: str) -> Dict[str, Any]`
- ✅ Parses `flow_name`, `tier`, and `area` from metadata
- ✅ Applies defaults (`tier: "B"`, `area: "general"`) when values are missing
- ✅ Normalizes values (e.g., lowercase tier)

### `parse_test_steps(pr_body: str) -> List[str]`
- ✅ Extracts numbered steps from the autoqa block
- ✅ Returns empty list when no steps are found

### `validate_metadata(metadata: Dict) -> Tuple[bool, List[str]]`
- ✅ Passes for valid metadata with required fields
- ✅ Fails when `flow_name` is missing
- ✅ Fails when `flow_name` exceeds 50 characters
- ✅ Fails when `tier` is not A, B, or C
- ✅ Fails when `area` exceeds 30 characters

### `compute_etag(metadata: Dict, steps: List[str]) -> str`
- ✅ Returns consistent SHA256 hash for same inputs
- ✅ Returns different hash when inputs change
- ✅ Is case-insensitive (canonicalized steps)

### `canonicalize_steps(steps: List[str]) -> List[str]`
- ✅ Strips whitespace and lowercases all steps
- ✅ Handles empty list

## Getting Started

1. Create `tests/test_parser.py`
2. Import the parser: `from src.autoqa.parser import AutoQAParser`
3. Write pytest test functions for each method above
4. Run tests: `pytest tests/test_parser.py -v`

## Example Test

```python
import pytest
from src.autoqa.parser import AutoQAParser


class TestHasAutoqaTag:
    def test_returns_true_for_valid_autoqa_block(self):
        pr_body = """
## Description
Some PR description

```autoqa
flow_name: login_flow
tier: A
area: authentication

1. Navigate to the login page
2. Enter valid credentials
3. Click the login button
4. Verify dashboard is displayed
```
"""
        assert AutoQAParser.has_autoqa_tag(pr_body) is True

    def test_returns_false_for_empty_body(self):
        assert AutoQAParser.has_autoqa_tag("") is False

    def test_returns_false_for_no_autoqa_block(self):
        pr_body = "## Just a regular PR\nNo autoqa here."
        assert AutoQAParser.has_autoqa_tag(pr_body) is False
```

## Acceptance Criteria

- [ ] All public methods listed above have at least 2 test cases each
- [ ] Tests pass with `pytest tests/test_parser.py -v`
- [ ] Tests do not require external services (no API calls, no browser)
- [ ] Tests follow existing project conventions (see `pytest.ini`)
