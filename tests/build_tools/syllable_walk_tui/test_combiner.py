"""
Tests for syllable_walk_tui combiner functionality.

Tests for combiner event handlers, _run_combiner method, and generate candidates buttons.
"""

from pathlib import Path

import pytest

from build_tools.syllable_walk_tui.core import SyllableWalkerApp


class TestCombinerEventHandlers:
    """Tests for combiner-related event handlers."""

    @pytest.mark.asyncio
    async def test_combiner_syllables_changed_updates_state_a(self):
        """Test that combiner syllables change updates combiner_a state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=3, widget_id="combiner-syllables-a")
            app.on_int_spinner_changed(event)

            assert app.state.combiner_a.syllables == 3

    @pytest.mark.asyncio
    async def test_combiner_syllables_changed_updates_state_b(self):
        """Test that combiner syllables change updates combiner_b state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=4, widget_id="combiner-syllables-b")
            app.on_int_spinner_changed(event)

            assert app.state.combiner_b.syllables == 4

    @pytest.mark.asyncio
    async def test_combiner_count_changed_updates_state_a(self):
        """Test that combiner count change updates combiner_a state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=5000, widget_id="combiner-count-a")
            app.on_int_spinner_changed(event)

            assert app.state.combiner_a.count == 5000

    @pytest.mark.asyncio
    async def test_combiner_count_changed_updates_state_b(self):
        """Test that combiner count change updates combiner_b state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=20000, widget_id="combiner-count-b")
            app.on_int_spinner_changed(event)

            assert app.state.combiner_b.count == 20000

    @pytest.mark.asyncio
    async def test_combiner_freq_weight_changed_updates_state_a(self):
        """Test that combiner freq weight change updates combiner_a state."""
        from build_tools.tui_common.controls import FloatSlider

        app = SyllableWalkerApp()

        async with app.run_test():
            event = FloatSlider.Changed(value=0.5, widget_id="combiner-freq-weight-a")
            app.on_float_slider_changed(event)

            assert app.state.combiner_a.frequency_weight == 0.5

    @pytest.mark.asyncio
    async def test_combiner_freq_weight_changed_updates_state_b(self):
        """Test that combiner freq weight change updates combiner_b state."""
        from build_tools.tui_common.controls import FloatSlider

        app = SyllableWalkerApp()

        async with app.run_test():
            event = FloatSlider.Changed(value=0.8, widget_id="combiner-freq-weight-b")
            app.on_float_slider_changed(event)

            assert app.state.combiner_b.frequency_weight == 0.8

    @pytest.mark.asyncio
    async def test_combiner_seed_changed_updates_state_a(self):
        """Test that combiner seed change updates combiner_a state."""
        from build_tools.tui_common.controls import SeedInput

        app = SyllableWalkerApp()

        async with app.run_test():
            event = SeedInput.Changed(value=12345, widget_id="combiner-seed-a")
            app.on_seed_changed(event)

            assert app.state.combiner_a.seed == 12345

    @pytest.mark.asyncio
    async def test_combiner_seed_changed_updates_state_b(self):
        """Test that combiner seed change updates combiner_b state."""
        from build_tools.tui_common.controls import SeedInput

        app = SyllableWalkerApp()

        async with app.run_test():
            event = SeedInput.Changed(value=99999, widget_id="combiner-seed-b")
            app.on_seed_changed(event)

            assert app.state.combiner_b.seed == 99999

    @pytest.mark.asyncio
    async def test_combiner_states_are_independent(self):
        """Test that combiner_a and combiner_b states are independent."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            # Update combiner_a
            event_a = IntSpinner.Changed(value=3, widget_id="combiner-syllables-a")
            app.on_int_spinner_changed(event_a)

            # Update combiner_b
            event_b = IntSpinner.Changed(value=4, widget_id="combiner-syllables-b")
            app.on_int_spinner_changed(event_b)

            # Verify they're independent
            assert app.state.combiner_a.syllables == 3
            assert app.state.combiner_b.syllables == 4


class TestRunCombiner:
    """Tests for _run_combiner method."""

    @pytest.mark.asyncio
    async def test_run_combiner_requires_corpus(self):
        """Test that _run_combiner requires corpus to be loaded."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Patch not ready (no corpus loaded)
            assert not app.state.patch_a.is_ready_for_generation()

            # Try to run combiner - should show notification
            app._run_combiner("A")
            await pilot.pause()

            # Should not crash, combiner outputs should be empty
            assert app.state.combiner_a.outputs == []

    @pytest.mark.asyncio
    async def test_run_combiner_requires_annotated_data(self):
        """Test that _run_combiner requires annotated_data to be loaded."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set corpus_dir but not annotated_data
            app.state.patch_a.corpus_dir = Path("/tmp/test")
            app.state.patch_a.syllables = ["test"]
            app.state.patch_a.frequencies = {"test": 1}
            # annotated_data is still None

            app._run_combiner("A")
            await pilot.pause()

            # Should not crash
            assert app.state.combiner_a.outputs == []

    @pytest.mark.asyncio
    async def test_run_combiner_creates_candidates(self, tmp_path):
        """Test that _run_combiner creates candidate files."""
        app = SyllableWalkerApp()

        # Create a test corpus directory
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()

        # Create sample annotated data
        annotated_data = [
            {
                "syllable": "ka",
                "frequency": 100,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": True,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": False,
                    "short_vowel": True,
                    "long_vowel": False,
                    "ends_with_vowel": True,
                    "ends_with_nasal": False,
                    "ends_with_stop": False,
                },
            },
            {
                "syllable": "ki",
                "frequency": 80,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": True,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": False,
                    "short_vowel": True,
                    "long_vowel": False,
                    "ends_with_vowel": True,
                    "ends_with_nasal": False,
                    "ends_with_stop": False,
                },
            },
            {
                "syllable": "ta",
                "frequency": 90,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": True,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": False,
                    "short_vowel": True,
                    "long_vowel": False,
                    "ends_with_vowel": True,
                    "ends_with_nasal": False,
                    "ends_with_stop": False,
                },
            },
        ]

        async with app.run_test() as pilot:
            # Set up patch state
            app.state.patch_a.corpus_dir = corpus_dir
            app.state.patch_a.corpus_type = "NLTK"
            app.state.patch_a.syllables = ["ka", "ki", "ta"]
            app.state.patch_a.frequencies = {"ka": 100, "ki": 80, "ta": 90}
            app.state.patch_a.annotated_data = annotated_data

            # Set combiner params
            app.state.combiner_a.syllables = 2
            app.state.combiner_a.count = 100
            app.state.combiner_a.seed = 42

            # Run combiner
            app._run_combiner("A")
            await pilot.pause(0.5)

            # Check that output files were created
            candidates_dir = corpus_dir / "candidates"
            assert candidates_dir.exists()

            candidates_file = candidates_dir / "nltk_candidates_2syl.json"
            assert candidates_file.exists()

            meta_file = candidates_dir / "nltk_combiner_meta.json"
            assert meta_file.exists()

            # Check that combiner state was updated
            assert app.state.combiner_a.last_output_path is not None

    @pytest.mark.asyncio
    async def test_run_combiner_for_patch_b(self, tmp_path):
        """Test that _run_combiner works for patch B."""
        app = SyllableWalkerApp()

        corpus_dir = tmp_path / "test_corpus_b"
        corpus_dir.mkdir()

        annotated_data = [
            {
                "syllable": "ba",
                "frequency": 50,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": True,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": False,
                    "short_vowel": True,
                    "long_vowel": False,
                    "ends_with_vowel": True,
                    "ends_with_nasal": False,
                    "ends_with_stop": False,
                },
            },
            {
                "syllable": "bi",
                "frequency": 60,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": True,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": False,
                    "short_vowel": True,
                    "long_vowel": False,
                    "ends_with_vowel": True,
                    "ends_with_nasal": False,
                    "ends_with_stop": False,
                },
            },
        ]

        async with app.run_test() as pilot:
            app.state.patch_b.corpus_dir = corpus_dir
            app.state.patch_b.corpus_type = "pyphen"
            app.state.patch_b.syllables = ["ba", "bi"]
            app.state.patch_b.frequencies = {"ba": 50, "bi": 60}
            app.state.patch_b.annotated_data = annotated_data

            app.state.combiner_b.syllables = 2
            app.state.combiner_b.count = 50
            app.state.combiner_b.seed = 123

            app._run_combiner("B")
            await pilot.pause(0.5)

            candidates_file = corpus_dir / "candidates" / "pyphen_candidates_2syl.json"
            assert candidates_file.exists()


class TestGenerateCandidatesButtons:
    """Tests for generate candidates button handlers."""

    @pytest.mark.asyncio
    async def test_generate_candidates_a_button_exists(self):
        """Test that generate candidates button A exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#generate-candidates-a")
            assert button is not None

    @pytest.mark.asyncio
    async def test_generate_candidates_b_button_exists(self):
        """Test that generate candidates button B exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#generate-candidates-b")
            assert button is not None
