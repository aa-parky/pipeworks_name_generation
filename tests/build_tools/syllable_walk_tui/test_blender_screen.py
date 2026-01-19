"""
Tests for syllable_walk_tui blender screen modal.

Tests for BlendedWalkScreen component.
"""

import pytest
from textual.app import App
from textual.widgets import Label

from build_tools.syllable_walk_tui.core.state import AppState
from build_tools.syllable_walk_tui.modules.blender.screen import BlendedWalkScreen


@pytest.fixture
def app_with_state():
    """Create an App subclass with a state attribute for testing."""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.state = AppState()

        def compose(self):
            yield BlendedWalkScreen()

    return TestApp()


class TestBlendedWalkScreen:
    """Tests for BlendedWalkScreen modal."""

    def test_bindings_defined(self):
        """Test that escape binding is defined."""
        # Extract binding keys - handles both tuple and Binding objects
        binding_keys = []
        for binding in BlendedWalkScreen.BINDINGS:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)  # type: ignore[union-attr]
            else:
                binding_keys.append(binding[0])
        assert "escape" in binding_keys

    @pytest.mark.asyncio
    async def test_compose_shows_header(self, app_with_state):
        """Test that modal shows header."""
        async with app_with_state.run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("BLENDED WALK RESULTS" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_compose_shows_patch_sections(self, app_with_state):
        """Test that modal shows Patch A and Patch B sections."""
        async with app_with_state.run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("Patch A Walks" in text for text in label_texts)
            assert any("Patch B Walks" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_compose_shows_close_instruction(self, app_with_state):
        """Test that modal shows Esc to close instruction."""
        async with app_with_state.run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("Esc" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_shows_generate_prompt_when_no_outputs(self, app_with_state):
        """Test that modal shows generate prompt when no walks generated."""
        async with app_with_state.run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("Generate to see results" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_shows_patch_a_outputs_when_present(self):
        """Test that modal displays Patch A outputs when available."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.state = AppState()
                # Set some outputs for patch A
                self.state.patch_a.outputs = [
                    "ka-ri-to-na-bi",
                    "su-me-wa-ho-da",
                    "po-li-ne-ra-ku",
                ]

            def compose(self):
                yield BlendedWalkScreen()

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            # Should show first walk output
            assert any("ka-ri-to-na-bi" in text for text in label_texts)
            assert any("su-me-wa-ho-da" in text for text in label_texts)
            assert any("po-li-ne-ra-ku" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_shows_patch_b_outputs_when_present(self):
        """Test that modal displays Patch B outputs when available."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.state = AppState()
                # Set some outputs for patch B
                self.state.patch_b.outputs = [
                    "zo-ba-ri-me-ta",
                    "fu-ke-so-na-di",
                ]

            def compose(self):
                yield BlendedWalkScreen()

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("zo-ba-ri-me-ta" in text for text in label_texts)
            assert any("fu-ke-so-na-di" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_limits_outputs_to_five(self):
        """Test that modal only shows first 5 walks per patch."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.state = AppState()
                # Set 10 outputs for patch A
                self.state.patch_a.outputs = [f"walk-{i}" for i in range(10)]

            def compose(self):
                yield BlendedWalkScreen()

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            # First 5 should be shown
            assert any("walk-0" in text for text in label_texts)
            assert any("walk-4" in text for text in label_texts)

            # 6th and beyond should NOT be shown
            assert not any("walk-5" in text for text in label_texts)
            assert not any("walk-9" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_shows_both_patches_simultaneously(self):
        """Test that modal shows outputs from both patches."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.state = AppState()
                self.state.patch_a.outputs = ["patch-a-walk"]
                self.state.patch_b.outputs = ["patch-b-walk"]

            def compose(self):
                yield BlendedWalkScreen()

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            assert any("patch-a-walk" in text for text in label_texts)
            assert any("patch-b-walk" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_action_close_screen_method_exists(self, app_with_state):
        """Test that action_close_screen method exists."""
        async with app_with_state.run_test() as pilot:
            screen = pilot.app.query_one(BlendedWalkScreen)
            assert hasattr(screen, "action_close_screen")
