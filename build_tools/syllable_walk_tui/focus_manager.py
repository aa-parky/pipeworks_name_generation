"""
Focus Management for Syllable Walker TUI.

This module provides centralized focus management to prevent parameter widgets
from blocking app-level keybindings (b/a/p for tab switching).

PROBLEM STATEMENT
=================

Textual's focus system has a precedence issue where even with priority=True,
app-level bindings don't reliably fire when child widgets have focus. This
causes tab switching (b/a/p) to fail after:
1. Corpus browser modal closes
2. User adjusts a parameter with j/k keys

SOLUTION
========

This module provides a centralized FocusManager class that:
1. Explicitly clears focus after modals close
2. Prevents auto-focusing of widgets after parameter changes
3. Provides debug logging to track focus state changes
4. Ensures app-level bindings always work

SOLUTION ARCHITECTURE
=====================

This module implements a two-layer focus management strategy:

Layer 1: Widget-Level Auto-Blur (widgets.py)
---------------------------------------------
Parameter widgets (IntSpinner, FloatSlider, SeedInput) automatically call
self.blur() after value changes. This releases focus immediately after
adjustment, but Textual may still auto-focus another widget.

Layer 2: App-Level Focus Prevention (app.py via FocusManager)
--------------------------------------------------------------
After parameter change handlers complete, app.py calls
focus_manager.prevent_auto_focus() to ensure no widget has captured focus.
This catches cases where Textual auto-focused a widget after the first blur.

Result: App-level bindings (b/a/p) always work because no widget holds focus
long enough to block them.

USAGE
=====

In app.py:
    from build_tools.syllable_walk_tui.focus_manager import FocusManager

    class SyllableWalkerApp(App):
        def on_mount(self):
            # Initialize with debug=False for production, debug=True for troubleshooting
            self.focus_manager = FocusManager(self, debug=False)

        async def _select_corpus_for_patch(self, patch_name):
            result = await self.push_screen_wait(CorpusBrowserScreen(...))
            # Layer 2: Prevent auto-focus after modal closes
            self.focus_manager.clear_focus_after_modal()
            ...

        @on(IntSpinner.Changed)
        def on_int_spinner_changed(self, event):
            # ... update state ...
            # Layer 2: Prevent auto-focus after parameter change
            self.focus_manager.prevent_auto_focus()

In widgets.py:
    class IntSpinner(Static):
        def action_increment(self):
            self.value += 1
            self.post_message(self.Changed(self.value, self.id))
            # Layer 1: Auto-blur immediately after value change
            self.blur()

DEBUGGING
=========

To debug focus issues:
1. Set debug=True when initializing FocusManager in app.py
2. Run `textual console` in one terminal
3. Run the TUI in another terminal
4. Check console logs for focus state changes

The logs will show exactly what widget has focus at each critical point,
making it easy to identify where focus is being captured incorrectly
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App
    from textual.widget import Widget


class FocusManager:
    """
    Centralized focus management for Syllable Walker TUI.

    Prevents parameter widgets from blocking app-level keybindings by:
    - Clearing focus after modals close
    - Preventing auto-focus after parameter changes
    - Tracking focus state for debugging
    """

    def __init__(self, app: "App", debug: bool = False):
        """
        Initialize focus manager.

        Args:
            app: The Textual App instance to manage focus for
            debug: Enable debug logging to console (use with `textual console`)
        """
        self.app = app
        self.debug = debug
        self._last_focused_widget: "Widget | None" = None

    def log(self, message: str) -> None:
        """Log a debug message if debug mode is enabled."""
        if self.debug:
            self.app.log(f"[FocusManager] {message}")

    def clear_focus_after_modal(self) -> None:
        """
        Clear focus after a modal closes.

        This prevents Textual from auto-focusing a parameter widget,
        which would block app-level tab switching bindings (b/a/p).

        Call this immediately after push_screen_wait() returns.
        """
        focused = self.app.focused
        self.log(f"clear_focus_after_modal: focused widget = {focused}")

        if focused:
            self._last_focused_widget = focused
            focused.blur()
            self.log(f"Blurred widget: {focused}")

        # Verify focus was cleared
        after_blur = self.app.focused
        self.log(f"After blur: focused widget = {after_blur}")

    def clear_focus_after_parameter_change(self, widget: "Widget") -> None:
        """
        Clear focus after a parameter widget changes its value.

        This ensures app-level bindings work immediately after adjusting
        parameters with j/k keys.

        Args:
            widget: The parameter widget that changed (IntSpinner, FloatSlider, etc.)
        """
        self.log(f"clear_focus_after_parameter_change: widget = {widget}")

        if widget.has_focus:
            widget.blur()
            self.log(f"Blurred parameter widget: {widget}")

        # Verify no widget got auto-focused
        after_blur = self.app.focused
        if after_blur and after_blur != self._last_focused_widget:
            self.log(f"WARNING: Unexpected focus after blur: {after_blur}")
            # Force clear the unexpected focus
            after_blur.blur()
            self.log(f"Force-cleared unexpected focus: {after_blur}")

        self.log(f"After parameter change blur: focused widget = {self.app.focused}")

    def prevent_auto_focus(self) -> None:
        """
        Prevent any widget from auto-focusing.

        Call this when you want to ensure no widget has focus,
        allowing app-level bindings to work freely.
        """
        focused = self.app.focused
        self.log(f"prevent_auto_focus: currently focused = {focused}")

        if focused:
            focused.blur()
            self.log(f"Cleared focus from: {focused}")

        # Double-check nothing got re-focused
        final_focus = self.app.focused
        if final_focus:
            self.log(f"WARNING: Widget re-focused after prevent_auto_focus: {final_focus}")
            final_focus.blur()
            self.log(f"Force-cleared re-focused widget: {final_focus}")

    def get_focus_state(self) -> dict[str, str]:
        """
        Get current focus state for debugging.

        Returns:
            Dictionary with focus state information
        """
        focused = self.app.focused
        return {
            "focused_widget": str(focused) if focused else "None",
            "focused_widget_type": type(focused).__name__ if focused else "None",
            "focused_widget_id": getattr(focused, "id", "no-id") if focused else "None",
            "last_focused_widget": (
                str(self._last_focused_widget) if self._last_focused_widget else "None"
            ),
        }

    def log_focus_state(self, context: str = "") -> None:
        """
        Log current focus state for debugging.

        Args:
            context: Optional context string to identify where this was called from
        """
        state = self.get_focus_state()
        prefix = f"[{context}] " if context else ""
        self.log(
            f"{prefix}Focus state: "
            f"widget={state['focused_widget_type']} "
            f"id={state['focused_widget_id']}"
        )
