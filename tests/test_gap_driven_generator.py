"""
Tests for GapDrivenGenerator.

Tests the core logic of gap-driven test criteria generation including
memory integration, source reading, criteria parsing, tier inference,
comment building, and auto-proceed behaviour.
"""

import json
from unittest.mock import patch

import pytest

from src.autoqa.gap_driven_generator import GAP_CRITERIA_COMMENT_MARKER, GapDrivenGenerator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create source modules
    src_dir = tmp_path / "src" / "autoqa"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").touch()
    (src_dir / "parser.py").write_text(
        "class Parser:\n    def parse(self, text):\n        return text.split()\n"
    )
    (src_dir / "runner.py").write_text("class Runner:\n    def run(self):\n        return True\n")
    (src_dir / "reporter.py").write_text(
        "class Reporter:\n    def report(self, data):\n        return str(data)\n"
    )

    src_utils = tmp_path / "src" / "utils"
    src_utils.mkdir(parents=True)
    (src_utils / "__init__.py").touch()
    (src_utils / "logger.py").write_text("def get_logger(name): pass\n")

    # Create test files (only for parser and runner — reporter and logger are gaps)
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").touch()
    (test_dir / "test_parser.py").write_text("def test_parse(): assert True\n")
    (test_dir / "test_runner.py").write_text("def test_run(): assert True\n")

    # Create reports directory
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "json").mkdir()

    return tmp_path


@pytest.fixture
def generator(tmp_project):
    """Create a GapDrivenGenerator with the temporary project."""
    return GapDrivenGenerator(
        project_root=str(tmp_project),
        github_token="test-token",
        target_repo="owner/repo",
    )


# ---------------------------------------------------------------------------
# Source reading
# ---------------------------------------------------------------------------


class TestSourceReading:
    """Tests for reading source files of uncovered modules."""

    def test_read_existing_source(self, generator, tmp_project):
        content = generator._read_source("src/autoqa/reporter.py")
        assert content is not None
        assert "class Reporter" in content

    def test_read_nonexistent_source(self, generator):
        content = generator._read_source("src/nonexistent.py")
        assert content is None

    def test_read_source_truncation(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"max_source_length": 10},
        )
        content = gen._read_source("src/autoqa/reporter.py")
        assert content is not None
        assert "truncated" in content


# ---------------------------------------------------------------------------
# Tier inference from path
# ---------------------------------------------------------------------------


class TestTierInferenceFromPath:
    """Tests for inferring tier from source module paths."""

    def test_critical_path_returns_tier_a(self, generator):
        assert generator._infer_tier_from_path("src/auth/login.py") == "A"

    def test_important_path_returns_tier_b(self, generator):
        assert generator._infer_tier_from_path("src/dashboard/views.py") == "B"

    def test_other_path_returns_tier_c(self, generator):
        assert generator._infer_tier_from_path("src/utils/helper.py") == "C"

    def test_custom_critical_paths(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={
                "tier_inference": {
                    "critical_paths": ["billing"],
                    "important_paths": [],
                }
            },
        )
        assert gen._infer_tier_from_path("src/billing/invoice.py") == "A"
        assert gen._infer_tier_from_path("src/auth/login.py") == "C"


# ---------------------------------------------------------------------------
# Criteria parsing
# ---------------------------------------------------------------------------


class TestCriteriaParsing:
    """Tests for parsing LLM criteria responses."""

    def test_valid_json_array(self, generator):
        raw = json.dumps(
            [
                {
                    "flow_name": "test_report",
                    "tier": "B",
                    "area": "reporting",
                    "steps": ["Step 1", "Step 2"],
                    "confidence": 80,
                }
            ]
        )
        result = generator._parse_criteria_response(raw)
        assert len(result) == 1
        assert result[0]["flow_name"] == "test_report"

    def test_json_with_markdown_fences(self, generator):
        raw = '```json\n[{"flow_name": "test_x", "steps": ["s1"]}]\n```'
        result = generator._parse_criteria_response(raw)
        assert len(result) == 1

    def test_missing_required_fields_skipped(self, generator):
        raw = json.dumps([{"flow_name": "valid", "steps": ["s1"]}, {"tier": "A"}])
        result = generator._parse_criteria_response(raw)
        assert len(result) == 1

    def test_flow_name_normalisation(self, generator):
        raw = json.dumps([{"flow_name": "My Flow Name!", "steps": ["s"]}])
        result = generator._parse_criteria_response(raw)
        assert result[0]["flow_name"] == "my_flow_name"

    def test_invalid_json_returns_empty(self, generator):
        result = generator._parse_criteria_response("not json at all")
        assert result == []

    def test_tier_normalisation(self, generator):
        raw = json.dumps([{"flow_name": "t", "steps": ["s"], "tier": "a"}])
        result = generator._parse_criteria_response(raw)
        assert result[0]["tier"] == "A"

    def test_invalid_tier_defaults_to_c(self, generator):
        raw = json.dumps([{"flow_name": "t", "steps": ["s"], "tier": "X"}])
        result = generator._parse_criteria_response(raw)
        assert result[0]["tier"] == "C"


# ---------------------------------------------------------------------------
# Coverage gap detection integration
# ---------------------------------------------------------------------------


class TestGapDetection:
    """Tests for gap detection via memory tracker integration."""

    def test_identifies_uncovered_modules(self, generator):
        generator.tracker.identify_coverage_gaps()
        missing = generator.tracker.get_missing_tests()
        missing_names = {g.module_name for g in missing}
        assert "reporter" in missing_names
        assert "logger" in missing_names
        assert "parser" not in missing_names

    def test_get_memory_summary(self, generator):
        summary = generator.get_memory_summary()
        assert "total_source_modules" in summary
        assert "uncovered_modules" in summary
        assert summary["uncovered_modules"] > 0


# ---------------------------------------------------------------------------
# Generate criteria for gaps
# ---------------------------------------------------------------------------


class TestGenerateCriteriaForGaps:
    """Tests for the full gap-driven criteria generation workflow."""

    def test_no_gaps_returns_empty_criteria(self, tmp_project):
        """When all modules have tests, no criteria should be generated."""
        # Add test files for all modules
        test_dir = tmp_project / "tests"
        (test_dir / "test_reporter.py").write_text("def test_report(): assert True\n")
        (test_dir / "test_logger.py").write_text("def test_log(): assert True\n")

        gen = GapDrivenGenerator(project_root=str(tmp_project))
        result = gen.generate_criteria_for_gaps()
        assert result["success"] is True
        assert result["criteria"] == []
        assert result["gaps_found"] == 0

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_generates_criteria_for_uncovered_modules(self, mock_llm, generator):
        """Should call LLM for uncovered modules and return criteria."""
        mock_llm.return_value = json.dumps(
            [
                {
                    "flow_name": "test_reporter_output",
                    "tier": "B",
                    "area": "reporting",
                    "steps": ["Create reporter", "Call report()", "Verify output"],
                    "confidence": 75,
                }
            ]
        )

        result = generator.generate_criteria_for_gaps()
        assert result["success"] is True
        assert result["gaps_found"] > 0
        assert len(result["criteria"]) > 0
        assert mock_llm.called

    @patch.object(GapDrivenGenerator, "_call_llm", return_value=None)
    def test_llm_failure_returns_empty_criteria(self, mock_llm, generator):
        """When LLM fails, the gap should be skipped."""
        result = generator.generate_criteria_for_gaps()
        assert result["success"] is True
        assert result["gaps_found"] > 0
        # Criteria may be empty if all LLM calls fail
        gap_details = result.get("gap_details", [])
        assert len(gap_details) > 0

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_max_modules_cap(self, mock_llm, tmp_project):
        """Should respect the max_modules_per_run configuration."""
        mock_llm.return_value = json.dumps(
            [{"flow_name": "test_x", "steps": ["s1"], "confidence": 90}]
        )

        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"max_modules_per_run": 1},
        )
        result = gen.generate_criteria_for_gaps()
        assert result["success"] is True
        assert result["gaps_processed"] <= 1

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_max_criteria_per_module_cap(self, mock_llm, generator):
        """Should cap criteria per module."""
        mock_llm.return_value = json.dumps(
            [{"flow_name": f"flow_{i}", "steps": ["s"], "confidence": 80} for i in range(10)]
        )

        generator.config["max_criteria_per_module"] = 2
        result = generator.generate_criteria_for_gaps()
        # Each module should produce at most 2 criteria
        for detail in result.get("gap_details", []):
            if detail.get("criteria_count"):
                assert detail["criteria_count"] <= 2

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_source_module_tagged_on_criteria(self, mock_llm, generator):
        """Each criterion should include the source_module path."""
        mock_llm.return_value = json.dumps(
            [{"flow_name": "test_thing", "steps": ["s1"], "confidence": 80}]
        )

        result = generator.generate_criteria_for_gaps()
        for c in result.get("criteria", []):
            assert "source_module" in c
            assert c["source_module"].endswith(".py")


# ---------------------------------------------------------------------------
# Auto-proceed behaviour
# ---------------------------------------------------------------------------


class TestAutoProceed:
    """Tests for auto-proceed logic."""

    def test_auto_mode_high_confidence_proceeds(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"mode": "auto", "auto_proceed_threshold": 80},
        )
        criteria = [{"confidence": 90}, {"confidence": 85}]
        assert gen.should_auto_proceed(criteria) is True

    def test_auto_mode_low_confidence_does_not_proceed(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"mode": "auto", "auto_proceed_threshold": 80},
        )
        criteria = [{"confidence": 90}, {"confidence": 70}]
        assert gen.should_auto_proceed(criteria) is False

    def test_suggest_mode_never_auto_proceeds(self, generator):
        criteria = [{"confidence": 100}]
        assert generator.should_auto_proceed(criteria) is False

    def test_empty_criteria_does_not_auto_proceed(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"mode": "auto"},
        )
        assert gen.should_auto_proceed([]) is False


# ---------------------------------------------------------------------------
# Comment building
# ---------------------------------------------------------------------------


class TestCommentBuilding:
    """Tests for markdown comment generation."""

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_comment_contains_marker(self, mock_llm, generator):
        mock_llm.return_value = json.dumps(
            [{"flow_name": "test_x", "steps": ["s1"], "confidence": 80}]
        )
        result = generator.generate_criteria_for_gaps()
        comment = result.get("comment_body", "")
        assert GAP_CRITERIA_COMMENT_MARKER in comment

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_comment_contains_coverage_stats(self, mock_llm, generator):
        mock_llm.return_value = json.dumps(
            [{"flow_name": "test_x", "steps": ["s1"], "confidence": 80}]
        )
        result = generator.generate_criteria_for_gaps()
        comment = result.get("comment_body", "")
        assert "Coverage" in comment
        assert "Uncovered modules" in comment

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_comment_contains_autoqa_block(self, mock_llm, generator):
        mock_llm.return_value = json.dumps(
            [
                {
                    "flow_name": "test_reporter",
                    "tier": "B",
                    "area": "reporting",
                    "steps": ["Create reporter"],
                    "confidence": 80,
                }
            ]
        )
        result = generator.generate_criteria_for_gaps()
        comment = result.get("comment_body", "")
        assert "```autoqa" in comment
        assert "flow_name: test_reporter" in comment

    def test_no_gaps_comment(self, tmp_project):
        test_dir = tmp_project / "tests"
        (test_dir / "test_reporter.py").write_text("def test_report(): assert True\n")
        (test_dir / "test_logger.py").write_text("def test_log(): assert True\n")

        gen = GapDrivenGenerator(project_root=str(tmp_project))
        result = gen.generate_criteria_for_gaps()
        comment = result.get("comment_body", "")
        assert "no gaps detected" in comment.lower() or "All source modules" in comment

    @patch.object(GapDrivenGenerator, "_call_llm")
    def test_comment_contains_confidence_label(self, mock_llm, generator):
        mock_llm.return_value = json.dumps(
            [{"flow_name": "test_x", "steps": ["s1"], "confidence": 90}]
        )
        result = generator.generate_criteria_for_gaps()
        comment = result.get("comment_body", "")
        assert "✅ High" in comment


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    """Tests for default configuration handling."""

    def test_default_config_keys(self, generator):
        assert "max_modules_per_run" in generator.config
        assert "max_source_length" in generator.config
        assert "max_criteria_per_module" in generator.config
        assert "mode" in generator.config

    def test_config_override(self, tmp_project):
        gen = GapDrivenGenerator(
            project_root=str(tmp_project),
            config={"max_modules_per_run": 5, "mode": "auto"},
        )
        assert gen.config["max_modules_per_run"] == 5
        assert gen.config["mode"] == "auto"
        # Defaults should still be present
        assert "max_source_length" in gen.config

    def test_tier_inference_defaults(self, generator):
        tier_config = generator.config.get("tier_inference", {})
        assert "critical_paths" in tier_config
        assert "login" in tier_config["critical_paths"]
