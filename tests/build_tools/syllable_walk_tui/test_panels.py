"""
Tests for syllable_walk_tui panel widgets.

Tests for PatchPanel, CombinerPanel, and SelectorPanel widgets.
"""

import pytest
from textual.widgets import Label

from build_tools.syllable_walk_tui.modules.generator import CombinerPanel, SelectorPanel
from build_tools.syllable_walk_tui.modules.oscillator import OscillatorPanel

# Backward compatibility alias for tests
PatchPanel = OscillatorPanel


class TestPatchPanel:
    """Tests for PatchPanel widget."""

    def test_initialization_with_name(self):
        """Test that PatchPanel initializes with correct name."""
        panel = PatchPanel("A")
        assert panel.patch_name == "A"

        panel_b = PatchPanel("B")
        assert panel_b.patch_name == "B"

    @pytest.mark.asyncio
    async def test_compose_creates_widgets(self):
        """Test that PatchPanel creates expected child widgets."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield PatchPanel("A")

        async with TestApp().run_test() as pilot:
            # Check for corpus selection button
            assert pilot.app.query_one("#select-corpus-A")

            # Check for corpus status label
            assert pilot.app.query_one("#corpus-status-A")


class TestCombinerPanel:
    """Tests for CombinerPanel widget (name generation)."""

    @pytest.mark.asyncio
    async def test_compose_creates_widgets(self):
        """Test that CombinerPanel creates expected child widgets."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield CombinerPanel(patch_name="A")

        async with TestApp().run_test() as pilot:
            # Should have combiner labels
            labels = pilot.app.query(Label)
            assert len(labels) > 0

            # Check for "PATCH A NAME COMBINER" header
            labels_text = [str(label.render()) for label in labels]
            assert any("PATCH A NAME COMBINER" in text for text in labels_text)

            # Check for generate button
            assert pilot.app.query_one("#generate-candidates-a")

    @pytest.mark.asyncio
    async def test_compose_creates_patch_b_widgets(self):
        """Test that CombinerPanel creates correct widgets for patch B."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield CombinerPanel(patch_name="B")

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            labels_text = [str(label.render()) for label in labels]
            assert any("PATCH B NAME COMBINER" in text for text in labels_text)
            assert pilot.app.query_one("#generate-candidates-b")

    @pytest.mark.asyncio
    async def test_update_output_with_metadata(self):
        """Test that update_output displays metadata correctly."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield CombinerPanel(patch_name="A", id="test-panel")

        async with TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#test-panel", CombinerPanel)

            # Update with sample metadata
            meta = {
                "arguments": {
                    "syllables": 2,
                    "count": 10000,
                    "seed": 42,
                    "frequency_weight": 1.0,
                },
                "output": {
                    "candidates_generated": 10000,
                    "unique_names": 7500,
                    "unique_percentage": 75.0,
                    "candidates_file": "/path/to/candidates/nltk_candidates_2syl.json",
                },
            }
            panel.update_output(meta)
            await pilot.pause()

            # Check output label was updated
            output_label = pilot.app.query_one("#combiner-output-a", Label)
            text = str(output_label.render())
            assert "Syllables: 2" in text
            assert "Seed: 42" in text

    @pytest.mark.asyncio
    async def test_update_output_with_none_shows_placeholder(self):
        """Test that update_output with None shows placeholder text."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield CombinerPanel(patch_name="A", id="test-panel")

        async with TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#test-panel", CombinerPanel)
            panel.update_output(None)
            await pilot.pause()

            output_label = pilot.app.query_one("#combiner-output-a", Label)
            text = str(output_label.render())
            assert "Generate" in text

    @pytest.mark.asyncio
    async def test_clear_output(self):
        """Test that clear_output resets to placeholder."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield CombinerPanel(patch_name="A", id="test-panel")

        async with TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#test-panel", CombinerPanel)

            # First set some output
            panel.update_output({"arguments": {"syllables": 3}, "output": {}})
            await pilot.pause()

            # Then clear it
            panel.clear_output()
            await pilot.pause()

            output_label = pilot.app.query_one("#combiner-output-a", Label)
            text = str(output_label.render())
            assert "Generate" in text


class TestSelectorPanel:
    """Tests for SelectorPanel widget (name selection)."""

    @pytest.mark.asyncio
    async def test_compose_creates_selector_widgets(self):
        """Test that SelectorPanel creates expected child widgets."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield SelectorPanel(patch_name="A")

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            labels_text = [str(label.render()) for label in labels]
            assert any("PATCH A NAME SELECTOR" in text for text in labels_text)

            # Check for select button
            assert pilot.app.query_one("#select-names-a")

    @pytest.mark.asyncio
    async def test_update_output_with_metadata(self):
        """Test that update_output displays metadata correctly."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield SelectorPanel(patch_name="A", id="test-panel")

        async with TestApp().run_test() as pilot:
            panel = pilot.app.query_one("#test-panel", SelectorPanel)

            meta = {
                "arguments": {
                    "name_class": "first_name",
                    "count": 100,
                    "mode": "hard",
                },
                "statistics": {
                    "total_evaluated": 10000,
                    "admitted": 7500,
                    "admitted_percentage": 75.0,
                    "rejected": 2500,
                },
                "output": {
                    "selections_count": 100,
                    "selections_file": "/path/to/selections/pyphen_first_name_2syl.json",
                },
            }
            panel.update_output(meta)
            await pilot.pause()

            output_label = pilot.app.query_one("#selector-output-a", Label)
            text = str(output_label.render())
            assert "first_name" in text
            assert "Evaluated: 10,000" in text
