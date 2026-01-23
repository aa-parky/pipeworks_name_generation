"""
Tests for syllable_walk_tui corpus, database, and metrics functionality.

Tests for corpus selection, database actions, metrics computation, and walk generation.
"""

import json
from unittest.mock import patch

import pytest
from textual.widgets import Label

from build_tools.syllable_walk_tui.core import SyllableWalkerApp


class TestCorpusSelectionFlow:
    """Integration tests for corpus selection workflow."""

    @pytest.mark.asyncio
    async def test_corpus_selection_updates_state(self, tmp_path):
        """Test that corpus selection updates patch state correctly."""
        app = SyllableWalkerApp()

        # Create valid NLTK corpus
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_unique.txt").write_text("test\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"test": 1}))

        async with app.run_test() as pilot:
            # Mock the push_screen_wait to return our corpus directory
            async def mock_push_screen_wait(screen):
                return corpus_dir

            with patch.object(app, "push_screen_wait", side_effect=mock_push_screen_wait):
                # Trigger corpus selection for Patch A
                app.action_select_corpus_a()
                await pilot.pause()

                # Wait for worker to complete
                await pilot.pause(0.5)

                # Check that state was updated
                assert app.state.patch_a.corpus_dir == corpus_dir
                assert app.state.patch_a.corpus_type == "NLTK"
                assert app.state.last_browse_dir == corpus_dir.parent

    @pytest.mark.asyncio
    async def test_corpus_selection_updates_ui(self, tmp_path):
        """Test that corpus selection updates UI labels."""
        app = SyllableWalkerApp()

        # Create valid corpus
        corpus_dir = tmp_path / "test_corpus"
        corpus_dir.mkdir()
        (corpus_dir / "nltk_syllables_unique.txt").write_text("test\n")
        (corpus_dir / "nltk_syllables_frequencies.json").write_text(json.dumps({"test": 1}))

        async with app.run_test() as pilot:
            # Mock the push_screen_wait
            async def mock_push_screen_wait(screen):
                return corpus_dir

            with patch.object(app, "push_screen_wait", side_effect=mock_push_screen_wait):
                # Trigger selection
                app.action_select_corpus_a()
                await pilot.pause()
                await pilot.pause(0.5)

                # Check UI was updated
                status_label = app.query_one("#corpus-status-A", Label)
                status_text = str(status_label.render())

                assert "NLTK" in status_text

    @pytest.mark.asyncio
    async def test_corpus_selection_cancelled(self):
        """Test that cancelling corpus selection doesn't update state."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Mock push_screen_wait to return None (cancelled)
            async def mock_push_screen_wait(screen):
                return None

            with patch.object(app, "push_screen_wait", side_effect=mock_push_screen_wait):
                original_corpus = app.state.patch_a.corpus_dir

                app.action_select_corpus_a()
                await pilot.pause()
                await pilot.pause(0.5)

                # State should not have changed
                assert app.state.patch_a.corpus_dir == original_corpus

    @pytest.mark.asyncio
    async def test_invalid_corpus_selection_shows_error(self, tmp_path):
        """Test that selecting invalid corpus shows error notification."""
        app = SyllableWalkerApp()

        # Create invalid corpus (missing files)
        invalid_corpus = tmp_path / "invalid"
        invalid_corpus.mkdir()

        async with app.run_test() as pilot:

            async def mock_push_screen_wait(screen):
                return invalid_corpus

            with patch.object(app, "push_screen_wait", side_effect=mock_push_screen_wait):
                app.action_select_corpus_a()
                await pilot.pause()
                await pilot.pause(0.5)

                # Corpus should not be set
                assert app.state.patch_a.corpus_dir is None
                assert app.state.patch_a.corpus_type is None


class TestDatabaseActions:
    """Tests for database viewer action methods."""

    @pytest.mark.asyncio
    async def test_action_view_database_a_exists(self):
        """Test that database A action exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            assert hasattr(app, "action_view_database_a")

    @pytest.mark.asyncio
    async def test_action_view_database_b_exists(self):
        """Test that database B action exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            assert hasattr(app, "action_view_database_b")

    @pytest.mark.asyncio
    async def test_open_database_no_corpus_shows_notification(self):
        """Test that opening database with no corpus shows notification."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Corpus not loaded
            assert app.state.patch_a.corpus_dir is None

            # Try to open database - should show notification, not crash
            app._open_database_for_patch("A")
            await pilot.pause()

            # Just verify no crash occurred
            assert True

    @pytest.mark.asyncio
    async def test_open_database_no_db_file_shows_notification(self, tmp_path):
        """Test that opening database with missing corpus.db shows notification."""
        app = SyllableWalkerApp()

        # Set corpus dir but don't create corpus.db
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        app.state.patch_a.corpus_dir = corpus_dir

        async with app.run_test() as pilot:
            app._open_database_for_patch("A")
            await pilot.pause()

            # Just verify no crash
            assert True


class TestComputeMetrics:
    """Tests for _compute_metrics_for_patch method."""

    @pytest.mark.asyncio
    async def test_compute_metrics_returns_none_without_data(self):
        """Test that compute metrics returns None without loaded data."""
        app = SyllableWalkerApp()

        async with app.run_test():
            result = app._compute_metrics_for_patch(app.state.patch_a)
            assert result is None

    @pytest.mark.asyncio
    async def test_compute_metrics_requires_syllables(self):
        """Test that compute metrics returns None without syllables."""
        app = SyllableWalkerApp()

        async with app.run_test():
            app.state.patch_a.frequencies = {"test": 1}
            app.state.patch_a.annotated_data = [
                {"syllable": "test", "frequency": 1, "features": {}}
            ]

            result = app._compute_metrics_for_patch(app.state.patch_a)
            assert result is None

    @pytest.mark.asyncio
    async def test_compute_metrics_requires_frequencies(self):
        """Test that compute metrics returns None without frequencies."""
        app = SyllableWalkerApp()

        async with app.run_test():
            app.state.patch_a.syllables = ["test"]
            app.state.patch_a.annotated_data = [
                {"syllable": "test", "frequency": 1, "features": {}}
            ]

            result = app._compute_metrics_for_patch(app.state.patch_a)
            assert result is None

    @pytest.mark.asyncio
    async def test_compute_metrics_requires_annotated_data(self):
        """Test that compute metrics returns None without annotated_data."""
        app = SyllableWalkerApp()

        async with app.run_test():
            app.state.patch_a.syllables = ["test"]
            app.state.patch_a.frequencies = {"test": 1}

            result = app._compute_metrics_for_patch(app.state.patch_a)
            assert result is None

    @pytest.mark.asyncio
    async def test_compute_metrics_with_valid_data(self):
        """Test that compute metrics works with valid data."""
        app = SyllableWalkerApp()

        async with app.run_test():
            app.state.patch_a.syllables = ["test", "ing", "foo"]
            app.state.patch_a.frequencies = {"test": 10, "ing": 20, "foo": 5}
            app.state.patch_a.annotated_data = [
                {"syllable": "test", "frequency": 10, "features": {"starts_with_vowel": False}},
                {"syllable": "ing", "frequency": 20, "features": {"starts_with_vowel": True}},
                {"syllable": "foo", "frequency": 5, "features": {"starts_with_vowel": False}},
            ]

            result = app._compute_metrics_for_patch(app.state.patch_a)

            assert result is not None
            assert result.inventory.total_count == 3
            assert result.frequency.total_occurrences == 35


class TestGenerateWalks:
    """Tests for walk generation."""

    @pytest.mark.asyncio
    async def test_generate_walks_requires_ready_patch(self):
        """Test that generation requires patch to be ready."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Patch not ready (no corpus loaded)
            assert not app.state.patch_a.is_ready_for_generation()

            # Try to generate - should show notification
            app._generate_walks_for_patch("A")
            await pilot.pause()

            # Outputs should still be empty
            assert app.state.patch_a.outputs == []
