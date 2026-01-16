"""
Walk output panel component.

This module provides the StatsPanel widget for displaying generated walks
from both patches in the center column.
"""

from textual.app import ComposeResult
from textual.widgets import Label, Static


class StatsPanel(Static):
    """
    Panel displaying generated walks from both patches.

    Shows walks with corpus name headers for clear provenance.
    Updated by _generate_walks_for_patch() after generation.
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for walk output panel."""
        # Patch A section
        yield Label("PATCH A", id="walks-header-A", classes="stats-header")
        yield Label("(no corpus selected)", id="walks-corpus-A", classes="corpus-label")
        yield Label("────────────────────", classes="divider")
        yield Label("(generate to see walks)", id="walks-output-A", classes="output-placeholder")

        yield Label("", classes="spacer")
        yield Label("", classes="spacer")

        # Patch B section
        yield Label("PATCH B", id="walks-header-B", classes="stats-header")
        yield Label("(no corpus selected)", id="walks-corpus-B", classes="corpus-label")
        yield Label("────────────────────", classes="divider")
        yield Label("(generate to see walks)", id="walks-output-B", classes="output-placeholder")
