"""
Unit tests for AutoQAParser (closes issue #19).

Tests every public method of AutoQAParser without requiring external
services, API calls, or a browser.

Run with:
    pytest tests/test_parser.py -v
"""

import hashlib
import json

import pytest

from src.autoqa.parser import AutoQAParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PR_BODY_VALID = """\
## Feature: User Login

Some description of the PR.

```autoqa
flow_name: user_login_success
tier: A
area: auth
```
1. Navigate to login page at "/login"
2. Enter valid email address
3. Enter valid password
4. Click the login button
5. Verify the dashboard appears
"""

PR_BODY_NO_AREA = """\
```autoqa
flow_name: simple_test
tier: B
```
1. Navigate to homepage
2. Verify page loads
"""

PR_BODY_NO_STEPS = """\
```autoqa
flow_name: no_steps_flow
tier: A
area: auth
```
"""

PR_BODY_NO_AUTOQA = """\
## Regular PR

This PR does not contain any autoqa block.
Just normal markdown.
"""

PR_BODY_OTHER_FENCES = """\
Here is some Python code:

```python
print("hello world")
```

And some YAML:

```yaml
key: value
```
"""

PR_BODY_MULTI_FENCES = """\
```python
x = 1
```

```autoqa
flow_name: multi_test
tier: C
```
1. Only step
"""


@pytest.fixture
def parser():
    return AutoQAParser()


# ---------------------------------------------------------------------------
# has_autoqa_tag
# ---------------------------------------------------------------------------


class TestHasAutoqaTag:
    """Tests for has_autoqa_tag(pr_body) -> bool."""

    def test_returns_true_for_valid_autoqa_block(self, parser):
        assert parser.has_autoqa_tag(PR_BODY_VALID) is True

    def test_returns_false_for_empty_string(self, parser):
        assert parser.has_autoqa_tag("") is False

    def test_returns_false_for_none(self, parser):
        assert parser.has_autoqa_tag(None) is False

    def test_returns_false_when_no_autoqa_block_present(self, parser):
        assert parser.has_autoqa_tag(PR_BODY_NO_AUTOQA) is False

    def test_returns_false_for_other_fenced_blocks(self, parser):
        assert parser.has_autoqa_tag(PR_BODY_OTHER_FENCES) is False

    def test_returns_true_when_autoqa_mixed_with_other_fences(self, parser):
        assert parser.has_autoqa_tag(PR_BODY_MULTI_FENCES) is True

    def test_returns_false_for_plain_text(self, parser):
        assert parser.has_autoqa_tag("Just plain text without any code blocks.") is False

    def test_returns_true_for_block_without_area(self, parser):
        assert parser.has_autoqa_tag(PR_BODY_NO_AREA) is True


# ---------------------------------------------------------------------------
# extract_autoqa_block
# ---------------------------------------------------------------------------


class TestExtractAutoqaBlock:
    """Tests for extract_autoqa_block(pr_body) -> Optional[Dict]."""

    def test_extracts_metadata_and_steps(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_VALID)
        assert result is not None
        assert "metadata" in result
        assert "steps" in result

    def test_metadata_contains_flow_name(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_VALID)
        assert result["metadata"]["flow_name"] == "user_login_success"

    def test_metadata_contains_tier(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_VALID)
        assert result["metadata"]["tier"] == "A"

    def test_metadata_contains_area(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_VALID)
        assert result["metadata"]["area"] == "auth"

    def test_steps_are_extracted_correctly(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_VALID)
        assert len(result["steps"]) == 5
        assert result["steps"][0] == 'Navigate to login page at "/login"'
        assert result["steps"][-1] == "Verify the dashboard appears"

    def test_returns_none_for_empty_body(self, parser):
        assert parser.extract_autoqa_block("") is None

    def test_returns_none_for_none(self, parser):
        assert parser.extract_autoqa_block(None) is None

    def test_returns_none_when_no_autoqa_block(self, parser):
        assert parser.extract_autoqa_block(PR_BODY_NO_AUTOQA) is None

    def test_returns_none_when_block_has_no_steps(self, parser):
        # A block with metadata but no numbered steps → None
        assert parser.extract_autoqa_block(PR_BODY_NO_STEPS) is None

    def test_works_with_multiple_fenced_blocks(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_MULTI_FENCES)
        assert result is not None
        assert result["metadata"]["flow_name"] == "multi_test"
        assert len(result["steps"]) == 1

    def test_applies_default_area_when_missing(self, parser):
        result = parser.extract_autoqa_block(PR_BODY_NO_AREA)
        assert result is not None
        assert result["metadata"]["area"] == "general"

    def test_applies_default_tier_when_missing(self, parser):
        body = """\
```autoqa
flow_name: no_tier_flow
```
1. Navigate to homepage
"""
        result = parser.extract_autoqa_block(body)
        assert result is not None
        assert result["metadata"]["tier"] == "B"


# ---------------------------------------------------------------------------
# parse_autoqa_metadata
# ---------------------------------------------------------------------------


class TestParseAutoqaMetadata:
    """Tests for parse_autoqa_metadata(metadata_block: str) -> Dict."""

    def test_parses_all_three_fields(self, parser):
        block = "flow_name: login_test\ntier: A\narea: auth\n"
        meta = parser.parse_autoqa_metadata(block)
        assert meta["flow_name"] == "login_test"
        assert meta["tier"] == "A"
        assert meta["area"] == "auth"

    def test_normalizes_tier_to_uppercase(self, parser):
        block = "flow_name: test\ntier: a\n"
        meta = parser.parse_autoqa_metadata(block)
        assert meta["tier"] == "A"

    def test_applies_default_tier_b(self, parser):
        block = "flow_name: test_flow\n"
        meta = parser.parse_autoqa_metadata(block)
        assert meta["tier"] == "B"

    def test_applies_default_area_general(self, parser):
        block = "flow_name: test_flow\ntier: C\n"
        meta = parser.parse_autoqa_metadata(block)
        assert meta["area"] == "general"

    def test_normalizes_flow_name_spaces(self, parser):
        block = "flow_name: My Login Flow\ntier: B\n"
        meta = parser.parse_autoqa_metadata(block)
        # Spaces should be replaced with underscores and lowercased
        assert " " not in meta["flow_name"]
        assert meta["flow_name"] == meta["flow_name"].lower()

    def test_normalizes_area_to_snake_case(self, parser):
        block = "flow_name: test\ntier: B\narea: User Auth\n"
        meta = parser.parse_autoqa_metadata(block)
        assert " " not in meta["area"]

    def test_extra_fields_are_preserved(self, parser):
        block = "flow_name: test\ntier: A\ncustom_key: custom_value\n"
        meta = parser.parse_autoqa_metadata(block)
        assert "custom_key" in meta


# ---------------------------------------------------------------------------
# parse_test_steps
# ---------------------------------------------------------------------------


class TestParseTestSteps:
    """Tests for parse_test_steps(pr_body: str) -> List[str]."""

    def test_extracts_numbered_steps(self, parser):
        steps = parser.parse_test_steps(PR_BODY_VALID)
        assert len(steps) == 5

    def test_returns_empty_list_when_no_autoqa_block(self, parser):
        steps = parser.parse_test_steps(PR_BODY_NO_AUTOQA)
        assert steps == []

    def test_returns_empty_list_for_empty_body(self, parser):
        steps = parser.parse_test_steps("")
        assert steps == []

    def test_returns_empty_list_for_none(self, parser):
        steps = parser.parse_test_steps(None)
        assert steps == []

    def test_returns_empty_list_when_no_steps_in_block(self, parser):
        steps = parser.parse_test_steps(PR_BODY_NO_STEPS)
        assert steps == []

    def test_steps_have_no_leading_number(self, parser):
        steps = parser.parse_test_steps(PR_BODY_VALID)
        for step in steps:
            # Steps should not start with a digit followed by a dot
            assert not step[0].isdigit()

    def test_step_content_matches_expected(self, parser):
        steps = parser.parse_test_steps(PR_BODY_VALID)
        assert "login" in steps[0].lower() or "navigate" in steps[0].lower()


# ---------------------------------------------------------------------------
# validate_metadata
# ---------------------------------------------------------------------------


class TestValidateMetadata:
    """Tests for validate_metadata(metadata: Dict) -> Tuple[bool, List[str]]."""

    def test_valid_metadata_passes(self, parser):
        meta = {"flow_name": "user_login", "tier": "A", "area": "auth"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is True
        assert errors == []

    def test_valid_without_area_passes(self, parser):
        meta = {"flow_name": "simple_flow", "tier": "B"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is True

    def test_all_valid_tiers_pass(self, parser):
        for tier in ("A", "B", "C"):
            meta = {"flow_name": "test", "tier": tier}
            is_valid, _ = parser.validate_metadata(meta)
            assert is_valid is True, f"Tier {tier!r} should be valid"

    def test_fails_when_flow_name_missing(self, parser):
        meta = {"tier": "A"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False
        assert any("flow_name" in e for e in errors)

    def test_fails_when_flow_name_is_empty(self, parser):
        meta = {"flow_name": "", "tier": "A"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False

    def test_fails_when_flow_name_exceeds_50_chars(self, parser):
        meta = {"flow_name": "a" * 51, "tier": "A"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False
        assert any("flow_name" in e.lower() or "50" in e for e in errors)

    def test_passes_at_exactly_50_chars(self, parser):
        meta = {"flow_name": "a" * 50, "tier": "B"}
        is_valid, _ = parser.validate_metadata(meta)
        assert is_valid is True

    def test_fails_when_tier_is_missing(self, parser):
        meta = {"flow_name": "test_flow"}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False
        assert any("tier" in e for e in errors)

    def test_fails_when_tier_is_invalid(self, parser):
        for bad_tier in ("D", "X", "1", "AA"):
            meta = {"flow_name": "test_flow", "tier": bad_tier}
            is_valid, errors = parser.validate_metadata(meta)
            assert is_valid is False, f"Tier {bad_tier!r} should be invalid"
            assert any("tier" in e.lower() for e in errors)

    def test_fails_when_area_exceeds_30_chars(self, parser):
        meta = {"flow_name": "test_flow", "tier": "B", "area": "a" * 31}
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False
        assert any("area" in e.lower() or "30" in e for e in errors)

    def test_passes_at_exactly_30_chars_area(self, parser):
        meta = {"flow_name": "test_flow", "tier": "C", "area": "a" * 30}
        is_valid, _ = parser.validate_metadata(meta)
        assert is_valid is True

    def test_returns_multiple_errors_when_multiple_issues(self, parser):
        meta = {"tier": "X"}  # Missing flow_name AND invalid tier
        is_valid, errors = parser.validate_metadata(meta)
        assert is_valid is False
        assert len(errors) >= 2


# ---------------------------------------------------------------------------
# compute_etag
# ---------------------------------------------------------------------------


class TestComputeEtag:
    """Tests for compute_etag(metadata: Dict, steps: List[str]) -> str."""

    def _make_metadata(self):
        return {"flow_name": "user_login", "tier": "A", "area": "auth"}

    def _make_steps(self):
        return ["Navigate to login page", "Enter valid credentials", "Click login button"]

    def test_returns_string(self, parser):
        etag = parser.compute_etag(self._make_metadata(), self._make_steps())
        assert isinstance(etag, str)

    def test_returns_sha256_length(self, parser):
        etag = parser.compute_etag(self._make_metadata(), self._make_steps())
        assert len(etag) == 64

    def test_consistent_for_same_inputs(self, parser):
        etag1 = parser.compute_etag(self._make_metadata(), self._make_steps())
        etag2 = parser.compute_etag(self._make_metadata(), self._make_steps())
        assert etag1 == etag2

    def test_different_when_flow_name_changes(self, parser):
        meta1 = {"flow_name": "login", "tier": "A", "area": "auth"}
        meta2 = {"flow_name": "signup", "tier": "A", "area": "auth"}
        steps = self._make_steps()
        assert parser.compute_etag(meta1, steps) != parser.compute_etag(meta2, steps)

    def test_different_when_tier_changes(self, parser):
        steps = self._make_steps()
        meta_a = {"flow_name": "test", "tier": "A", "area": "auth"}
        meta_b = {"flow_name": "test", "tier": "B", "area": "auth"}
        assert parser.compute_etag(meta_a, steps) != parser.compute_etag(meta_b, steps)

    def test_different_when_steps_change(self, parser):
        meta = self._make_metadata()
        steps1 = ["Step one"]
        steps2 = ["Step two"]
        assert parser.compute_etag(meta, steps1) != parser.compute_etag(meta, steps2)

    def test_case_insensitive_canonicalization(self, parser):
        meta = self._make_metadata()
        steps_lower = ["navigate to login page", "enter email"]
        steps_upper = ["NAVIGATE TO LOGIN PAGE", "ENTER EMAIL"]
        assert parser.compute_etag(meta, steps_lower) == parser.compute_etag(meta, steps_upper)

    def test_whitespace_normalized(self, parser):
        meta = self._make_metadata()
        steps_normal = ["navigate to login page"]
        steps_extra_spaces = ["  navigate   to   login   page  "]
        assert parser.compute_etag(meta, steps_normal) == parser.compute_etag(
            meta, steps_extra_spaces
        )

    def test_empty_steps_list(self, parser):
        meta = self._make_metadata()
        etag = parser.compute_etag(meta, [])
        assert isinstance(etag, str)
        assert len(etag) == 64

    def test_matches_manual_sha256(self, parser):
        meta = {"flow_name": "login", "tier": "A", "area": "auth"}
        steps = ["go to login"]
        payload = json.dumps(
            {
                "flow_name": "login",
                "tier": "A",
                "area": "auth",
                "steps": ["go to login"],
            },
            sort_keys=True,
        )
        expected = hashlib.sha256(payload.encode()).hexdigest()
        assert parser.compute_etag(meta, steps) == expected


# ---------------------------------------------------------------------------
# canonicalize_steps
# ---------------------------------------------------------------------------


class TestCanonicalizeSteps:
    """Tests for canonicalize_steps(steps: List[str]) -> List[str]."""

    def test_lowercases_steps(self, parser):
        result = parser.canonicalize_steps(["NAVIGATE TO PAGE", "CLICK BUTTON"])
        assert result == ["navigate to page", "click button"]

    def test_strips_leading_trailing_whitespace(self, parser):
        result = parser.canonicalize_steps(["  navigate to page  "])
        assert result == ["navigate to page"]

    def test_collapses_internal_whitespace(self, parser):
        result = parser.canonicalize_steps(["navigate   to    page"])
        assert result == ["navigate to page"]

    def test_handles_empty_list(self, parser):
        result = parser.canonicalize_steps([])
        assert result == []

    def test_handles_single_step(self, parser):
        result = parser.canonicalize_steps(["Only One Step"])
        assert result == ["only one step"]

    def test_preserves_step_count(self, parser):
        steps = ["Step one", "Step two", "Step three"]
        result = parser.canonicalize_steps(steps)
        assert len(result) == 3

    def test_mixed_case_and_whitespace(self, parser):
        result = parser.canonicalize_steps(["  NAVIGATE  To  The  LOGIN  PAGE  "])
        assert result == ["navigate to the login page"]


# ---------------------------------------------------------------------------
# steps_to_scenario
# ---------------------------------------------------------------------------


class TestStepsToScenario:
    """Tests for steps_to_scenario(steps, metadata) -> Dict."""

    def test_returns_dict(self, parser):
        steps = ["Go to login", "Enter password"]
        meta = {"flow_name": "login", "tier": "A", "area": "auth"}
        result = parser.steps_to_scenario(steps, meta)
        assert isinstance(result, dict)

    def test_uses_flow_name_as_scenario_name(self, parser):
        steps = ["Step one"]
        meta = {"flow_name": "my_flow", "tier": "B"}
        result = parser.steps_to_scenario(steps, meta)
        assert result["name"] == "my_flow"

    def test_includes_steps_in_result(self, parser):
        steps = ["Step A", "Step B"]
        meta = {"flow_name": "test", "tier": "C"}
        result = parser.steps_to_scenario(steps, meta)
        assert result["steps"] == ["Step A", "Step B"]

    def test_includes_metadata(self, parser):
        steps = ["Step one"]
        meta = {"flow_name": "test", "tier": "A", "area": "auth"}
        result = parser.steps_to_scenario(steps, meta)
        assert result["metadata"] == meta

    def test_returns_empty_dict_for_empty_steps(self, parser):
        result = parser.steps_to_scenario([], {"flow_name": "test", "tier": "A"})
        assert result == {}

    def test_works_without_metadata(self, parser):
        steps = ["Step one", "Step two"]
        result = parser.steps_to_scenario(steps)
        assert isinstance(result, dict)
        assert "steps" in result


# ---------------------------------------------------------------------------
# get_metadata_summary
# ---------------------------------------------------------------------------


class TestGetMetadataSummary:
    """Tests for get_metadata_summary(metadata: Dict) -> str."""

    def test_returns_string(self, parser):
        meta = {"flow_name": "login", "tier": "A", "area": "auth"}
        result = parser.get_metadata_summary(meta)
        assert isinstance(result, str)

    def test_includes_flow_name(self, parser):
        meta = {"flow_name": "login_flow", "tier": "B"}
        result = parser.get_metadata_summary(meta)
        assert "login_flow" in result

    def test_includes_tier(self, parser):
        meta = {"flow_name": "test", "tier": "A"}
        result = parser.get_metadata_summary(meta)
        assert "A" in result

    def test_includes_area_when_not_default(self, parser):
        meta = {"flow_name": "test", "tier": "B", "area": "payments"}
        result = parser.get_metadata_summary(meta)
        assert "payments" in result

    def test_excludes_area_when_default(self, parser):
        meta = {"flow_name": "test", "tier": "B", "area": "general"}
        result = parser.get_metadata_summary(meta)
        # Default area "general" should not appear in the summary
        assert "general" not in result
