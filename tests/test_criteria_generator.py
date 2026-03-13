"""
Tests for TestCriteriaGenerator (Proposal 16)

Tests the core logic of auto-criteria generation, tier inference,
criteria parsing, comment building, and approval checking.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.autoqa.criteria_generator import (
    CRITERIA_COMMENT_MARKER,
    DiffAnalyzer,
    TestCriteriaGenerator,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def generator():
    """Create a TestCriteriaGenerator with test defaults."""
    return TestCriteriaGenerator(
        github_token="test-token",
        target_repo="owner/repo",
    )


@pytest.fixture
def diff_analyzer():
    """Create a DiffAnalyzer with test defaults."""
    return DiffAnalyzer(
        github_token="test-token",
        target_repo="owner/repo",
    )


# ---------------------------------------------------------------------------
# DiffAnalyzer
# ---------------------------------------------------------------------------


class TestDiffAnalyzer:
    """Tests for DiffAnalyzer."""

    def test_headers(self, diff_analyzer):
        headers = diff_analyzer._headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test-token"

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_get_pr_diff_success(self, mock_get, diff_analyzer):
        mock_get.return_value = MagicMock(
            status_code=200,
            text="diff --git a/file.py b/file.py\n+new line",
        )
        diff = diff_analyzer.get_pr_diff("42")
        assert diff is not None
        assert "diff --git" in diff

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_get_pr_diff_failure(self, mock_get, diff_analyzer):
        mock_get.return_value = MagicMock(status_code=404)
        diff = diff_analyzer.get_pr_diff("42")
        assert diff is None

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_get_pr_info_success(self, mock_get, diff_analyzer):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "title": "Fix login",
                "body": "Updated auth flow",
                "changed_files": 3,
            },
        )
        info = diff_analyzer.get_pr_info("42")
        assert info["title"] == "Fix login"
        assert info["changed_files"] == 3

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_get_changed_file_paths(self, mock_get, diff_analyzer):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"filename": "src/auth/login.py"},
                {"filename": "src/dashboard/views.py"},
            ],
        )
        paths = diff_analyzer.get_changed_file_paths("42")
        assert len(paths) == 2
        assert "src/auth/login.py" in paths

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_get_changed_file_paths_failure(self, mock_get, diff_analyzer):
        mock_get.return_value = MagicMock(status_code=500)
        paths = diff_analyzer.get_changed_file_paths("42")
        assert paths == []


# ---------------------------------------------------------------------------
# Tier Inference
# ---------------------------------------------------------------------------


class TestTierInference:
    """Tests for tier inference from file paths."""

    def test_critical_path_returns_tier_a(self, generator):
        assert generator.infer_tier(["src/auth/login.py"]) == "A"
        assert generator.infer_tier(["src/payment/checkout.py"]) == "A"

    def test_important_path_returns_tier_b(self, generator):
        assert generator.infer_tier(["src/dashboard/views.py"]) == "B"
        assert generator.infer_tier(["src/settings/profile.py"]) == "B"

    def test_other_path_returns_tier_c(self, generator):
        assert generator.infer_tier(["README.md"]) == "C"
        assert generator.infer_tier(["docs/changelog.md"]) == "C"

    def test_mixed_paths_returns_highest(self, generator):
        paths = ["README.md", "src/auth/login.py", "src/dashboard/views.py"]
        assert generator.infer_tier(paths) == "A"

    def test_empty_paths_returns_tier_c(self, generator):
        assert generator.infer_tier([]) == "C"

    def test_custom_critical_paths(self):
        gen = TestCriteriaGenerator(
            github_token="t",
            target_repo="o/r",
            config={
                "tier_inference": {
                    "critical_paths": ["billing"],
                    "important_paths": ["notifications"],
                },
            },
        )
        assert gen.infer_tier(["src/billing/invoice.py"]) == "A"
        assert gen.infer_tier(["src/notifications/email.py"]) == "B"
        assert gen.infer_tier(["src/auth/login.py"]) == "C"  # Not in custom config


# ---------------------------------------------------------------------------
# Criteria Parsing
# ---------------------------------------------------------------------------


class TestCriteriaParsing:
    """Tests for _parse_criteria_response."""

    def test_valid_json_array(self, generator):
        raw = json.dumps(
            [
                {
                    "flow_name": "user_login",
                    "tier": "A",
                    "area": "auth",
                    "steps": ["Go to /login", "Enter email", "Click login"],
                    "confidence": 90,
                }
            ]
        )
        criteria = generator._parse_criteria_response(raw)
        assert len(criteria) == 1
        assert criteria[0]["flow_name"] == "user_login"
        assert criteria[0]["tier"] == "A"
        assert criteria[0]["confidence"] == 90

    def test_json_with_markdown_fences(self, generator):
        raw = '```json\n[{"flow_name": "test", "steps": ["step1"]}]\n```'
        criteria = generator._parse_criteria_response(raw)
        assert len(criteria) == 1
        assert criteria[0]["flow_name"] == "test"
        # Defaults applied
        assert criteria[0]["tier"] == "C"
        assert criteria[0]["area"] == "general"
        assert criteria[0]["confidence"] == 50

    def test_single_object_wrapped_in_list(self, generator):
        raw = json.dumps({"flow_name": "signup", "steps": ["Go to /signup"], "tier": "a"})
        criteria = generator._parse_criteria_response(raw)
        assert len(criteria) == 1
        assert criteria[0]["tier"] == "A"  # Normalised to uppercase

    def test_missing_required_fields_skipped(self, generator):
        raw = json.dumps(
            [
                {"flow_name": "valid", "steps": ["step1"]},
                {"flow_name": "no_steps"},  # Missing steps
                {"steps": ["step1"]},  # Missing flow_name
            ]
        )
        criteria = generator._parse_criteria_response(raw)
        assert len(criteria) == 1
        assert criteria[0]["flow_name"] == "valid"

    def test_flow_name_normalisation(self, generator):
        raw = json.dumps(
            [
                {
                    "flow_name": "User Login Flow!!!",
                    "steps": ["step1"],
                }
            ]
        )
        criteria = generator._parse_criteria_response(raw)
        assert criteria[0]["flow_name"] == "user_login_flow"

    def test_flow_name_length_cap(self, generator):
        raw = json.dumps(
            [
                {
                    "flow_name": "a" * 100,
                    "steps": ["step1"],
                }
            ]
        )
        criteria = generator._parse_criteria_response(raw)
        assert len(criteria[0]["flow_name"]) <= 50

    def test_empty_array_response(self, generator):
        raw = "[]"
        criteria = generator._parse_criteria_response(raw)
        assert criteria == []

    def test_invalid_json_returns_empty(self, generator):
        raw = "This is not JSON at all"
        criteria = generator._parse_criteria_response(raw)
        assert criteria == []

    def test_non_dict_items_skipped(self, generator):
        raw = json.dumps(["string_item", 42, None])
        criteria = generator._parse_criteria_response(raw)
        assert criteria == []


# ---------------------------------------------------------------------------
# Comment Building
# ---------------------------------------------------------------------------


class TestCommentBuilding:
    """Tests for criteria comment generation."""

    def test_criteria_comment_contains_marker(self, generator):
        criteria = [
            {
                "flow_name": "user_login",
                "tier": "A",
                "area": "auth",
                "steps": ["Go to /login", "Enter email"],
                "confidence": 90,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert CRITERIA_COMMENT_MARKER in comment

    def test_criteria_comment_contains_flow_details(self, generator):
        criteria = [
            {
                "flow_name": "user_login",
                "tier": "A",
                "area": "auth",
                "steps": ["Go to /login", "Enter email"],
                "confidence": 90,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "user_login" in comment
        assert "Tier A" in comment
        assert "auth" in comment
        assert "90/100" in comment
        assert "Go to /login" in comment

    def test_criteria_comment_contains_autoqa_block(self, generator):
        criteria = [
            {
                "flow_name": "user_login",
                "tier": "A",
                "area": "auth",
                "steps": ["step1"],
                "confidence": 80,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "```autoqa" in comment
        assert "flow_name: user_login" in comment

    def test_high_confidence_label(self, generator):
        criteria = [
            {
                "flow_name": "test",
                "tier": "A",
                "area": "auth",
                "steps": ["s1"],
                "confidence": 85,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "✅ High" in comment

    def test_medium_confidence_label(self, generator):
        criteria = [
            {
                "flow_name": "test",
                "tier": "B",
                "area": "general",
                "steps": ["s1"],
                "confidence": 60,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "⚠️ Medium" in comment

    def test_low_confidence_label(self, generator):
        criteria = [
            {
                "flow_name": "test",
                "tier": "C",
                "area": "general",
                "steps": ["s1"],
                "confidence": 30,
            }
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "❓ Low" in comment

    def test_no_criteria_comment(self, generator):
        comment = generator._build_no_criteria_comment()
        assert "No user-facing flows" in comment
        assert CRITERIA_COMMENT_MARKER in comment

    def test_multiple_criteria_generates_multiple_sections(self, generator):
        criteria = [
            {"flow_name": "login", "tier": "A", "area": "auth", "steps": ["s1"], "confidence": 90},
            {"flow_name": "signup", "tier": "A", "area": "auth", "steps": ["s2"], "confidence": 85},
        ]
        comment = generator._build_criteria_comment(criteria)
        assert "Flow 1:" in comment
        assert "Flow 2:" in comment
        assert "login" in comment
        assert "signup" in comment


# ---------------------------------------------------------------------------
# Approval Instructions
# ---------------------------------------------------------------------------


class TestApprovalInstructions:
    """Tests for approval instruction text."""

    def test_reaction_approval_instructions(self):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "reaction"})
        msg = gen._approval_instructions()
        assert "👍" in msg

    def test_comment_approval_instructions(self):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "comment"})
        msg = gen._approval_instructions()
        assert "/autoqa approve" in msg

    def test_label_approval_instructions(self):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "label"})
        msg = gen._approval_instructions()
        assert "autoqa:approved" in msg


# ---------------------------------------------------------------------------
# Auto-Proceed Logic
# ---------------------------------------------------------------------------


class TestAutoProceeed:
    """Tests for should_auto_proceed logic."""

    def test_auto_mode_high_confidence_proceeds(self):
        gen = TestCriteriaGenerator(
            "t", "o/r", config={"mode": "auto", "auto_proceed_threshold": 80}
        )
        criteria = [
            {"flow_name": "a", "confidence": 90},
            {"flow_name": "b", "confidence": 85},
        ]
        assert gen.should_auto_proceed(criteria) is True

    def test_auto_mode_low_confidence_does_not_proceed(self):
        gen = TestCriteriaGenerator(
            "t", "o/r", config={"mode": "auto", "auto_proceed_threshold": 80}
        )
        criteria = [
            {"flow_name": "a", "confidence": 90},
            {"flow_name": "b", "confidence": 60},  # Below threshold
        ]
        assert gen.should_auto_proceed(criteria) is False

    def test_suggest_mode_never_auto_proceeds(self):
        gen = TestCriteriaGenerator(
            "t", "o/r", config={"mode": "suggest", "auto_proceed_threshold": 0}
        )
        criteria = [{"flow_name": "a", "confidence": 100}]
        assert gen.should_auto_proceed(criteria) is False

    def test_empty_criteria_does_not_auto_proceed(self):
        gen = TestCriteriaGenerator(
            "t", "o/r", config={"mode": "auto", "auto_proceed_threshold": 0}
        )
        assert gen.should_auto_proceed([]) is False


# ---------------------------------------------------------------------------
# Default Configuration
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    """Tests for default configuration values."""

    def test_default_config_keys(self, generator):
        config = generator.config
        assert config["enabled"] is True
        assert config["mode"] == "suggest"
        assert config["auto_proceed_threshold"] == 85
        assert config["max_flows_per_pr"] == 5
        assert config["approval_mechanism"] == "reaction"

    def test_config_override(self):
        gen = TestCriteriaGenerator("t", "o/r", config={"mode": "auto", "max_flows_per_pr": 10})
        assert gen.config["mode"] == "auto"
        assert gen.config["max_flows_per_pr"] == 10

    def test_tier_inference_defaults(self, generator):
        ti = generator.config["tier_inference"]
        assert "auth" in ti["critical_paths"]
        assert "dashboard" in ti["important_paths"]


# ---------------------------------------------------------------------------
# Tier Override (apply_tier_inference)
# ---------------------------------------------------------------------------


class TestApplyTierInference:
    """Tests for _apply_tier_inference override logic."""

    def test_upgrades_tier_when_paths_are_critical(self, generator):
        criteria = [{"flow_name": "test", "tier": "C", "steps": ["s1"]}]
        result = generator._apply_tier_inference(criteria, ["src/auth/login.py"])
        assert result[0]["tier"] == "A"

    def test_does_not_downgrade_tier(self, generator):
        criteria = [{"flow_name": "test", "tier": "A", "steps": ["s1"]}]
        result = generator._apply_tier_inference(criteria, ["README.md"])
        assert result[0]["tier"] == "A"  # Stays A, not downgraded to C


# ---------------------------------------------------------------------------
# Generate Criteria (integration with mocked LLM)
# ---------------------------------------------------------------------------


class TestGenerateCriteria:
    """Integration tests for generate_criteria with mocked dependencies."""

    @patch.object(DiffAnalyzer, "get_pr_diff", return_value=None)
    def test_generate_criteria_no_diff(self, mock_diff, generator):
        result = generator.generate_criteria("42")
        assert result["success"] is False
        assert "Could not fetch PR diff" in result["error"]

    @patch.object(
        DiffAnalyzer,
        "get_changed_file_paths",
        return_value=["src/auth/login.py"],
    )
    @patch.object(
        DiffAnalyzer,
        "get_pr_diff",
        return_value="diff --git a/src/auth/login.py b/src/auth/login.py\n+new code",
    )
    def test_generate_criteria_with_llm(self, mock_diff, mock_paths, generator):
        mock_llm = MagicMock()
        mock_llm.call.return_value = json.dumps(
            [
                {
                    "flow_name": "login_test",
                    "tier": "A",
                    "area": "auth",
                    "steps": ["Go to /login", "Enter credentials"],
                    "confidence": 92,
                }
            ]
        )
        result = generator.generate_criteria("42", pr_title="Fix login", llm=mock_llm)
        assert result["success"] is True
        assert len(result["criteria"]) == 1
        assert result["criteria"][0]["flow_name"] == "login_test"
        assert "comment_body" in result

    @patch.object(
        DiffAnalyzer,
        "get_changed_file_paths",
        return_value=["README.md"],
    )
    @patch.object(
        DiffAnalyzer,
        "get_pr_diff",
        return_value="diff --git a/README.md b/README.md\n+update docs",
    )
    def test_generate_criteria_no_flows_detected(self, mock_diff, mock_paths, generator):
        mock_llm = MagicMock()
        mock_llm.call.return_value = "[]"
        result = generator.generate_criteria("42", llm=mock_llm)
        assert result["success"] is True
        assert result["criteria"] == []
        assert "No user-facing flows" in result.get("message", "")

    @patch.object(DiffAnalyzer, "get_pr_diff", return_value="big diff content")
    def test_generate_criteria_llm_failure(self, mock_diff, generator):
        mock_llm = MagicMock()
        mock_llm.call.side_effect = Exception("LLM error")
        result = generator.generate_criteria("42", llm=mock_llm)
        assert result["success"] is False

    @patch.object(
        DiffAnalyzer,
        "get_changed_file_paths",
        return_value=["src/settings/profile.py"],
    )
    @patch.object(
        DiffAnalyzer,
        "get_pr_diff",
        return_value="diff content",
    )
    def test_max_flows_cap(self, mock_diff, mock_paths):
        gen = TestCriteriaGenerator("t", "o/r", config={"max_flows_per_pr": 2})
        mock_llm = MagicMock()
        mock_llm.call.return_value = json.dumps(
            [{"flow_name": f"flow_{i}", "steps": ["s1"], "confidence": 90} for i in range(10)]
        )
        result = gen.generate_criteria("42", llm=mock_llm)
        assert result["success"] is True
        assert len(result["criteria"]) <= 2

    @patch.object(
        DiffAnalyzer,
        "get_changed_file_paths",
        return_value=["src/auth/login.py"],
    )
    @patch.object(DiffAnalyzer, "get_pr_diff")
    def test_diff_truncation(self, mock_diff, mock_paths):
        gen = TestCriteriaGenerator("t", "o/r", config={"max_diff_length": 100})
        mock_diff.return_value = "x" * 200
        mock_llm = MagicMock()
        mock_llm.call.return_value = "[]"
        gen.generate_criteria("42", llm=mock_llm)
        # Verify the prompt sent to LLM contains truncated diff
        call_args = mock_llm.call.call_args[0][0]
        prompt_content = call_args[0]["content"]
        assert "truncated" in prompt_content


# ---------------------------------------------------------------------------
# Approval Checking
# ---------------------------------------------------------------------------


class TestApprovalChecking:
    """Tests for check_approval with mocked GitHub API."""

    @patch("src.autoqa.criteria_generator.requests.get")
    @patch(
        "src.utils.github_comment_client.GitHubCommentClient.find_existing_autoqa_comment",
        return_value=123,
    )
    def test_reaction_approval_found(self, mock_find_comment, mock_criteria_get, generator):
        # Mock reactions on the criteria comment
        mock_criteria_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"content": "+1", "user": {"login": "dev"}}],
        )
        result = generator.check_approval("42")
        assert result["approved"] is True
        assert result["mechanism"] == "reaction"

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_comment_approval_found(self, mock_get):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "comment"})
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"body": "/autoqa approve"},
            ],
        )
        result = gen.check_approval("42")
        assert result["approved"] is True
        assert result["mechanism"] == "comment"

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_label_approval_found(self, mock_get):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "label"})
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"name": "autoqa:approved"}],
        )
        result = gen.check_approval("42")
        assert result["approved"] is True
        assert result["mechanism"] == "label"

    @patch("src.autoqa.criteria_generator.requests.get")
    def test_label_approval_not_found(self, mock_get):
        gen = TestCriteriaGenerator("t", "o/r", config={"approval_mechanism": "label"})
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"name": "bug"}],
        )
        result = gen.check_approval("42")
        assert result["approved"] is False
