"""
Tooltip visual regression tests using CrewAI + Playwright.

Purpose: catch divergence between hardcoded tooltip implementations
(e.g., note editor Tooltip.jsx) and the token-based design-system tooltip.

Coverage:
- Standard tooltip: render, styling against design tokens, positioning
- Note editor tooltip: render, styling parity with standard, arrow
- Walkthrough tooltip: render, styling, navigation controls
- Themed tooltip: light mode, dark mode
- Cross-surface consistency: dashboard vs editor, across pages
"""

import pytest

from src.crews.qa_crew import QACrew


# ---------------------------------------------------------------------------
# Standard tooltip
# ---------------------------------------------------------------------------


class TestStandardTooltip:
    """Verify standard tooltip rendering, styling, and positioning."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_standard_tooltip_renders(self, reports_dir):
        """Standard tooltip appears on hover and disappears on leave."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "standard_tooltip_renders"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Standard Tooltip Renders On Hover"

        if not result.get("success", False):
            pytest.fail(
                "Standard tooltip did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_standard_tooltip_styling(self, reports_dir):
        """Standard tooltip computed styles match design tokens."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "standard_tooltip_styling"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Standard Tooltip Matches Design Tokens"

        if not result.get("success", False):
            pytest.fail(
                "Standard tooltip styling does not match design tokens:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_standard_tooltip_positioning(self, reports_dir):
        """Standard tooltip is positioned correctly without overlap or clipping."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "standard_tooltip_positioning"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Standard Tooltip Positions Correctly"

        if not result.get("success", False):
            pytest.fail(
                "Standard tooltip positioning incorrect:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Note editor tooltip (the hardcoded Tooltip.jsx)
# ---------------------------------------------------------------------------


class TestNoteEditorTooltip:
    """Verify note editor tooltip matches the design-system tooltip."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_note_editor_tooltip_renders(self, reports_dir):
        """Note editor toolbar tooltip appears on hover."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "note_editor_tooltip_renders"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Note Editor Tooltip Renders On Hover"

        if not result.get("success", False):
            pytest.fail(
                "Note editor tooltip did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_note_editor_tooltip_styling(self, reports_dir):
        """Note editor tooltip styles match the standard design-token tooltip exactly."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "note_editor_tooltip_styling"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Note Editor Tooltip Matches Design Tokens"

        if not result.get("success", False):
            pytest.fail(
                "Note editor tooltip styling diverged from design tokens:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_note_editor_tooltip_arrow(self, reports_dir):
        """Note editor tooltip arrow renders and matches tooltip background."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "note_editor_tooltip_arrow"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Note Editor Tooltip Arrow Renders"

        if not result.get("success", False):
            pytest.fail(
                "Note editor tooltip arrow issue:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Walkthrough tooltip
# ---------------------------------------------------------------------------


class TestWalkthroughTooltip:
    """Verify walkthrough/onboarding tooltip rendering and navigation."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_walkthrough_tooltip_renders(self, reports_dir):
        """Walkthrough tooltip renders with content and navigation controls."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "walkthrough_tooltip_renders"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Walkthrough Tooltip Renders"

        if not result.get("success", False):
            pytest.fail(
                "Walkthrough tooltip did not render:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_walkthrough_tooltip_styling(self, reports_dir):
        """Walkthrough tooltip styles match design tokens."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "walkthrough_tooltip_styling"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Walkthrough Tooltip Matches Design Tokens"

        if not result.get("success", False):
            pytest.fail(
                "Walkthrough tooltip styling does not match design tokens:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_walkthrough_tooltip_navigation(self, reports_dir):
        """Walkthrough Next/Previous/Skip controls work correctly."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "walkthrough_tooltip_navigation"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Walkthrough Tooltip Navigation Works"

        if not result.get("success", False):
            pytest.fail(
                "Walkthrough tooltip navigation failed:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Themed tooltip (dark/light mode)
# ---------------------------------------------------------------------------


class TestThemedTooltip:
    """Verify tooltip styling adapts correctly to light and dark themes."""

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_themed_tooltip_light_mode(self, reports_dir):
        """Tooltip uses correct light-mode token values."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "themed_tooltip_light_mode"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Tooltip Light Mode Styling"

        if not result.get("success", False):
            pytest.fail(
                "Light mode tooltip styling incorrect:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_themed_tooltip_dark_mode(self, reports_dir):
        """Tooltip uses correct dark-mode token values, distinct from light mode."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "themed_tooltip_dark_mode"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Tooltip Dark Mode Styling"

        if not result.get("success", False):
            pytest.fail(
                "Dark mode tooltip styling incorrect or still using light-mode values:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Cross-surface consistency (the key regression catch)
# ---------------------------------------------------------------------------


class TestTooltipConsistency:
    """Verify tooltip styling is identical across different surfaces.

    This is the core guard against the original bug: hardcoded Tooltip.jsx
    in the note editor diverging from the token-based design-system tooltip.
    """

    def setup_method(self):
        self.qa_crew = QACrew()

    @pytest.mark.tooltip_visual
    @pytest.mark.smoke
    def test_tooltip_consistency_dashboard_vs_editor(self, reports_dir):
        """Dashboard tooltip and note editor tooltip have identical computed styles."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "tooltip_consistency_dashboard_vs_editor"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Tooltip Consistency Dashboard vs Note Editor"

        if not result.get("success", False):
            pytest.fail(
                "Tooltip styles differ between dashboard and note editor:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )

    @pytest.mark.tooltip_visual
    @pytest.mark.regression
    def test_tooltip_consistency_across_pages(self, reports_dir):
        """Tooltip styling is consistent across at least three different pages."""
        result = self.qa_crew.run_test_scenario(
            "tooltip_visual", "tooltip_consistency_across_pages"
        )

        assert result is not None
        assert "scenario" in result
        assert result["scenario"]["name"] == "Tooltip Consistency Across Pages"

        if not result.get("success", False):
            pytest.fail(
                "Tooltip styles are inconsistent across pages:"
                f" {result.get('execution_result', {}).get('error', 'Unknown error')}"
            )


# ---------------------------------------------------------------------------
# Config sanity check
# ---------------------------------------------------------------------------


@pytest.mark.tooltip_visual
def test_tooltip_visual_scenarios_exist():
    """Verify all tooltip visual regression scenarios are configured."""
    qa_crew = QACrew()
    test_data = qa_crew.load_test_data()

    assert "tooltip_visual" in test_data["test_scenarios"]

    expected = [
        "standard_tooltip_renders",
        "standard_tooltip_styling",
        "standard_tooltip_positioning",
        "note_editor_tooltip_renders",
        "note_editor_tooltip_styling",
        "note_editor_tooltip_arrow",
        "walkthrough_tooltip_renders",
        "walkthrough_tooltip_styling",
        "walkthrough_tooltip_navigation",
        "themed_tooltip_light_mode",
        "themed_tooltip_dark_mode",
        "tooltip_consistency_dashboard_vs_editor",
        "tooltip_consistency_across_pages",
    ]
    for scenario in expected:
        assert scenario in test_data["test_scenarios"]["tooltip_visual"], (
            f"Missing scenario: {scenario}"
        )

    assert "tooltip_visual_page" in test_data["selectors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
