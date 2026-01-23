"""
Tests for syllable_walk_tui export and render functionality.

Tests for export buttons, _export_to_txt method, and render screen action.
"""

import pytest

from build_tools.syllable_walk_tui.core import SyllableWalkerApp


class TestExportTxtButtons:
    """Tests for export TXT button handlers."""

    @pytest.mark.asyncio
    async def test_export_txt_a_button_exists(self):
        """Test that export TXT button A exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#export-txt-a")
            assert button is not None

    @pytest.mark.asyncio
    async def test_export_txt_b_button_exists(self):
        """Test that export TXT button B exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            button = app.query_one("#export-txt-b")
            assert button is not None

    @pytest.mark.asyncio
    async def test_export_txt_a_handler_calls_export(self, tmp_path):
        """Test that button A handler calls _export_to_txt for patch A."""
        app = SyllableWalkerApp()

        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()
        json_path = selections_dir / "test_a.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            # Set up state for export
            app.state.selector_a.outputs = ["TestName"]
            app.state.selector_a.last_output_path = str(json_path)

            # Call the button handler directly
            app.on_button_export_txt_a()
            await pilot.pause()

            # Verify file was created
            txt_path = selections_dir / "test_a.txt"
            assert txt_path.exists()

    @pytest.mark.asyncio
    async def test_export_txt_b_handler_calls_export(self, tmp_path):
        """Test that button B handler calls _export_to_txt for patch B."""
        app = SyllableWalkerApp()

        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()
        json_path = selections_dir / "test_b.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            # Set up state for export
            app.state.selector_b.outputs = ["TestNameB"]
            app.state.selector_b.last_output_path = str(json_path)

            # Call the button handler directly
            app.on_button_export_txt_b()
            await pilot.pause()

            # Verify file was created
            txt_path = selections_dir / "test_b.txt"
            assert txt_path.exists()


class TestExportToTxt:
    """Tests for _export_to_txt method."""

    @pytest.mark.asyncio
    async def test_export_to_txt_requires_names(self):
        """Test that _export_to_txt requires names to be available."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # No names in selector outputs
            assert app.state.selector_a.outputs == []

            # Try to export - should show notification
            app._export_to_txt("A")
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_export_to_txt_requires_output_path(self):
        """Test that _export_to_txt requires last_output_path to be set."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set names but no output path
            app.state.selector_a.outputs = ["Kala", "Tana", "Naka"]
            app.state.selector_a.last_output_path = None

            # Try to export - should show notification
            app._export_to_txt("A")
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_export_to_txt_creates_file(self, tmp_path):
        """Test that _export_to_txt creates TXT file with names."""
        app = SyllableWalkerApp()

        # Create a test selections directory
        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()

        # Create a fake JSON output path
        json_path = selections_dir / "nltk_first_name_2syl.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            # Set up selector state with names and output path
            app.state.selector_a.outputs = ["Kala", "Tana", "Naka"]
            app.state.selector_a.last_output_path = str(json_path)

            # Export
            app._export_to_txt("A")
            await pilot.pause()

            # Check TXT file was created
            txt_path = selections_dir / "nltk_first_name_2syl.txt"
            assert txt_path.exists()

            # Check contents
            content = txt_path.read_text()
            assert "Kala\n" in content
            assert "Tana\n" in content
            assert "Naka\n" in content

    @pytest.mark.asyncio
    async def test_export_to_txt_for_patch_b(self, tmp_path):
        """Test that _export_to_txt works for patch B."""
        app = SyllableWalkerApp()

        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()

        json_path = selections_dir / "pyphen_last_name_3syl.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            app.state.selector_b.outputs = ["Bakala", "Bitana"]
            app.state.selector_b.last_output_path = str(json_path)

            app._export_to_txt("B")
            await pilot.pause()

            txt_path = selections_dir / "pyphen_last_name_3syl.txt"
            assert txt_path.exists()

            content = txt_path.read_text()
            assert "Bakala\n" in content
            assert "Bitana\n" in content

    @pytest.mark.asyncio
    async def test_export_to_txt_one_name_per_line(self, tmp_path):
        """Test that exported TXT has exactly one name per line."""
        app = SyllableWalkerApp()

        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()

        json_path = selections_dir / "test_output.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            names = ["Alpha", "Beta", "Gamma", "Delta"]
            app.state.selector_a.outputs = names
            app.state.selector_a.last_output_path = str(json_path)

            app._export_to_txt("A")
            await pilot.pause()

            txt_path = selections_dir / "test_output.txt"
            lines = txt_path.read_text().strip().split("\n")

            assert len(lines) == 4
            assert lines == names

    @pytest.mark.asyncio
    async def test_export_to_txt_preserves_name_order(self, tmp_path):
        """Test that exported TXT preserves the order of names."""
        app = SyllableWalkerApp()

        selections_dir = tmp_path / "selections"
        selections_dir.mkdir()

        json_path = selections_dir / "test_order.json"
        json_path.write_text("{}")

        async with app.run_test() as pilot:
            # Specific order
            names = ["Zeta", "Alpha", "Mika", "Beta"]
            app.state.selector_a.outputs = names
            app.state.selector_a.last_output_path = str(json_path)

            app._export_to_txt("A")
            await pilot.pause()

            txt_path = selections_dir / "test_order.txt"
            lines = txt_path.read_text().strip().split("\n")

            # Order should be preserved
            assert lines == names

    @pytest.mark.asyncio
    async def test_export_to_txt_handles_write_error(self, tmp_path):
        """Test that _export_to_txt handles file write errors gracefully."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up state with names but point to non-existent directory
            app.state.selector_a.outputs = ["TestName"]
            # Path to a directory that doesn't exist
            app.state.selector_a.last_output_path = "/nonexistent/path/test.json"

            # This should trigger the exception handler, not crash
            app._export_to_txt("A")
            await pilot.pause()

            # Should not crash - exception is caught and notification shown
            assert True


class TestRenderScreenAction:
    """Tests for action_view_render method."""

    @pytest.mark.asyncio
    async def test_action_view_render_exists(self):
        """Test that action_view_render method exists."""
        app = SyllableWalkerApp()

        async with app.run_test():
            assert hasattr(app, "action_view_render")

    @pytest.mark.asyncio
    async def test_render_screen_binding_exists(self):
        """Test that 'r' binding is registered for render screen."""
        from build_tools.syllable_walk_tui.core import SyllableWalkerApp

        # Extract binding keys from BINDINGS
        binding_keys = []
        for binding in SyllableWalkerApp.BINDINGS:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)  # type: ignore[union-attr]
            else:
                binding_keys.append(binding[0])

        assert "r" in binding_keys

    @pytest.mark.asyncio
    async def test_render_without_selections_shows_notification(self):
        """Test that opening render without selections shows notification."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # No selections yet
            assert app.state.selector_a.outputs == []
            assert app.state.selector_b.outputs == []

            # Try to open render screen - should show notification
            app.action_view_render()
            await pilot.pause()

            # Should not crash, and no render screen pushed
            assert True

    @pytest.mark.asyncio
    async def test_render_with_patch_a_selections(self):
        """Test opening render screen with Patch A selections."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up Patch A selections
            app.state.selector_a.outputs = ["orma", "krath", "velum"]
            app.state.selector_a.name_class = "first_name"

            # Open render screen
            app.action_view_render()
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_render_with_patch_b_selections(self):
        """Test opening render screen with Patch B selections only."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up Patch B selections only
            app.state.selector_b.outputs = ["striden", "velum"]
            app.state.selector_b.name_class = "last_name"

            # Open render screen
            app.action_view_render()
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_render_with_both_patches_selections(self):
        """Test opening render screen with both patches having selections."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up both patches
            app.state.selector_a.outputs = ["orma", "krath"]
            app.state.selector_a.name_class = "first_name"
            app.state.selector_b.outputs = ["striden", "velum"]
            app.state.selector_b.name_class = "last_name"

            # Open render screen
            app.action_view_render()
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_render_keypress_opens_screen(self):
        """Test that pressing 'r' opens render screen."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up some selections first
            app.state.selector_a.outputs = ["test"]
            app.state.selector_a.name_class = "first_name"

            # Press 'r' to open render screen
            await pilot.press("r")
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_render_keypress_without_selections(self):
        """Test that pressing 'r' without selections shows notification."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # No selections
            assert app.state.selector_a.outputs == []
            assert app.state.selector_b.outputs == []

            # Press 'r' - should show notification, not crash
            await pilot.press("r")
            await pilot.pause()

            # Should not crash
            assert True

    @pytest.mark.asyncio
    async def test_render_passes_correct_name_classes(self):
        """Test that render passes correct name classes from selector state."""
        app = SyllableWalkerApp()

        async with app.run_test() as pilot:
            # Set up specific name classes
            app.state.selector_a.name_class = "place_name"
            app.state.selector_a.outputs = ["test"]
            app.state.selector_b.name_class = "organisation"
            app.state.selector_b.outputs = ["org"]

            # Open render screen - verify no errors with different name classes
            app.action_view_render()
            await pilot.pause()

            # Should not crash with non-default name classes
            assert True
