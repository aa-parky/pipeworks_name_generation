"""
Tests for syllable_walk_tui selector functionality.

Tests for selector event handlers, _run_selector method, and select names buttons.
"""

import pytest

from build_tools.syllable_walk_tui.core import SyllableWalkerApp


class TestSelectorEventHandlers:
    """Tests for selector-related event handlers."""

    @pytest.mark.asyncio
    async def test_selector_count_changed_updates_state_a(self):
        """Test that selector count change updates selector_a state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=50, widget_id="selector-count-a")
            app.on_int_spinner_changed(event)

            assert app.state.selector_a.count == 50

    @pytest.mark.asyncio
    async def test_selector_count_changed_updates_state_b(self):
        """Test that selector count change updates selector_b state."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event = IntSpinner.Changed(value=200, widget_id="selector-count-b")
            app.on_int_spinner_changed(event)

            assert app.state.selector_b.count == 200

    @pytest.mark.asyncio
    async def test_selector_mode_hard_updates_state_a(self):
        """Test that selector mode hard updates selector_a state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # First set to soft, then back to hard
            app.state.selector_a.mode = "soft"

            event = RadioOption.Selected(option_name="hard", widget_id="selector-mode-hard-a")
            app.on_profile_selected(event)

            assert app.state.selector_a.mode == "hard"

    @pytest.mark.asyncio
    async def test_selector_mode_soft_updates_state_a(self):
        """Test that selector mode soft updates selector_a state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            event = RadioOption.Selected(option_name="soft", widget_id="selector-mode-soft-a")
            app.on_profile_selected(event)

            assert app.state.selector_a.mode == "soft"

    @pytest.mark.asyncio
    async def test_selector_mode_hard_updates_state_b(self):
        """Test that selector mode hard updates selector_b state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            app.state.selector_b.mode = "soft"

            event = RadioOption.Selected(option_name="hard", widget_id="selector-mode-hard-b")
            app.on_profile_selected(event)

            assert app.state.selector_b.mode == "hard"

    @pytest.mark.asyncio
    async def test_selector_mode_soft_updates_state_b(self):
        """Test that selector mode soft updates selector_b state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            event = RadioOption.Selected(option_name="soft", widget_id="selector-mode-soft-b")
            app.on_profile_selected(event)

            assert app.state.selector_b.mode == "soft"

    @pytest.mark.asyncio
    async def test_selector_states_are_independent(self):
        """Test that selector_a and selector_b states are independent."""
        from build_tools.tui_common.controls import IntSpinner

        app = SyllableWalkerApp()

        async with app.run_test():
            event_a = IntSpinner.Changed(value=50, widget_id="selector-count-a")
            app.on_int_spinner_changed(event_a)

            event_b = IntSpinner.Changed(value=200, widget_id="selector-count-b")
            app.on_int_spinner_changed(event_b)

            assert app.state.selector_a.count == 50
            assert app.state.selector_b.count == 200


class TestSelectorOrderEventHandlers:
    """Tests for selector order-related event handlers."""

    @pytest.mark.asyncio
    async def test_selector_order_random_updates_state_a(self):
        """Test that selector order random updates selector_a state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # Start with alphabetical
            app.state.selector_a.order = "alphabetical"

            event = RadioOption.Selected(option_name="random", widget_id="selector-order-random-a")
            app.on_profile_selected(event)

            assert app.state.selector_a.order == "random"

    @pytest.mark.asyncio
    async def test_selector_order_alphabetical_updates_state_a(self):
        """Test that selector order alphabetical updates selector_a state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # Start with random
            app.state.selector_a.order = "random"

            event = RadioOption.Selected(
                option_name="alphabetical", widget_id="selector-order-alphabetical-a"
            )
            app.on_profile_selected(event)

            assert app.state.selector_a.order == "alphabetical"

    @pytest.mark.asyncio
    async def test_selector_order_random_updates_state_b(self):
        """Test that selector order random updates selector_b state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # Start with alphabetical
            app.state.selector_b.order = "alphabetical"

            event = RadioOption.Selected(option_name="random", widget_id="selector-order-random-b")
            app.on_profile_selected(event)

            assert app.state.selector_b.order == "random"

    @pytest.mark.asyncio
    async def test_selector_order_alphabetical_updates_state_b(self):
        """Test that selector order alphabetical updates selector_b state."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # Start with random
            app.state.selector_b.order = "random"

            event = RadioOption.Selected(
                option_name="alphabetical", widget_id="selector-order-alphabetical-b"
            )
            app.on_profile_selected(event)

            assert app.state.selector_b.order == "alphabetical"

    @pytest.mark.asyncio
    async def test_selector_order_states_are_independent(self):
        """Test that selector_a and selector_b order states are independent."""
        from build_tools.tui_common.controls import RadioOption

        app = SyllableWalkerApp()

        async with app.run_test():
            # Set A to random
            event_a = RadioOption.Selected(
                option_name="random", widget_id="selector-order-random-a"
            )
            app.on_profile_selected(event_a)

            # Set B to alphabetical
            event_b = RadioOption.Selected(
                option_name="alphabetical", widget_id="selector-order-alphabetical-b"
            )
            app.on_profile_selected(event_b)

            # Verify they're independent
            assert app.state.selector_a.order == "random"
            assert app.state.selector_b.order == "alphabetical"


class TestRunSelector:
    """Tests for _run_selector method."""

    @pytest.mark.asyncio
    async def test_run_selector_requires_corpus(self):
        """Test that _run_selector requires corpus to be loaded."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Patch not ready (no corpus loaded)
            assert not app.state.patch_a.is_ready_for_generation()

            # Try to run selector - should show notification
            app._run_selector("A")
            await pilot.pause()

            # Should not crash, selector outputs should be empty
            assert app.state.selector_a.outputs == []

    @pytest.mark.asyncio
    async def test_run_selector_requires_candidates(self, tmp_path):
        """Test that _run_selector requires candidates to exist."""
        app = SyllableWalkerApp()

        # Create a test corpus directory
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()

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
        ]

        async with app.run_test() as pilot:
            # Set up patch state without running combiner first
            app.state.patch_a.corpus_dir = corpus_dir
            app.state.patch_a.corpus_type = "NLTK"
            app.state.patch_a.syllables = ["ka"]
            app.state.patch_a.frequencies = {"ka": 100}
            app.state.patch_a.annotated_data = annotated_data

            # No combiner has run, so no candidates exist
            assert app.state.combiner_a.last_output_path is None

            app._run_selector("A")
            await pilot.pause()

            # Should not crash, selector outputs should be empty
            assert app.state.selector_a.outputs == []

    @pytest.mark.asyncio
    async def test_run_selector_creates_selections(self, tmp_path):
        """Test that _run_selector creates selection files."""
        app = SyllableWalkerApp()

        # Create a test corpus directory
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()

        # Create sample annotated data with features for name selection
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
                "syllable": "ta",
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
                "syllable": "na",
                "frequency": 60,
                "features": {
                    "starts_with_vowel": False,
                    "starts_with_cluster": False,
                    "starts_with_heavy_cluster": False,
                    "contains_plosive": False,
                    "contains_fricative": False,
                    "contains_liquid": False,
                    "contains_nasal": True,
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
            app.state.patch_a.syllables = ["ka", "ta", "na"]
            app.state.patch_a.frequencies = {"ka": 100, "ta": 80, "na": 60}
            app.state.patch_a.annotated_data = annotated_data

            # Set combiner params and run
            app.state.combiner_a.syllables = 2
            app.state.combiner_a.count = 100
            app.state.combiner_a.seed = 42

            app._run_combiner("A")
            await pilot.pause(0.5)

            # Verify combiner created candidates
            assert app.state.combiner_a.last_output_path is not None

            # Now run selector
            app.state.selector_a.name_class = "first_name"
            app.state.selector_a.count = 50
            app.state.selector_a.mode = "hard"

            app._run_selector("A")
            await pilot.pause(0.5)

            # Check that output files were created
            selections_dir = corpus_dir / "selections"
            assert selections_dir.exists()

            # Check that selector state was updated
            assert app.state.selector_a.last_output_path is not None


class TestSelectNamesButtons:
    """Tests for select names button handlers."""

    @pytest.mark.asyncio
    async def test_select_names_a_button_exists(self):
        """Test that select names button A exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#select-names-a")
            assert button is not None

    @pytest.mark.asyncio
    async def test_select_names_b_button_exists(self):
        """Test that select names button B exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#select-names-b")
            assert button is not None


class TestSelectorPanelInApp:
    """Tests for SelectorPanel integration within the app."""

    @pytest.mark.asyncio
    async def test_selector_panel_exists_for_patch_a(self):
        """Test that selector panel A exists in layout."""
        app = SyllableWalkerApp()

        async with app.run_test():
            from build_tools.syllable_walk_tui.modules.generator import SelectorPanel

            selector_a = app.query_one("#selector-panel-a", SelectorPanel)
            assert selector_a.patch_name == "A"

    @pytest.mark.asyncio
    async def test_selector_panel_exists_for_patch_b(self):
        """Test that selector panel B exists in layout."""
        app = SyllableWalkerApp()

        async with app.run_test():
            from build_tools.syllable_walk_tui.modules.generator import SelectorPanel

            selector_b = app.query_one("#selector-panel-b", SelectorPanel)
            assert selector_b.patch_name == "B"
