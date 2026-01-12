"""
Main Textual application for Syllable Walker TUI.

This module contains the primary App class and layout widgets for the
interactive terminal interface.
"""

from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Label, Static, TabbedContent, TabPane

from build_tools.syllable_walk_tui.config import load_keybindings
from build_tools.syllable_walk_tui.corpus import get_corpus_info, validate_corpus_directory
from build_tools.syllable_walk_tui.state import AppState
from build_tools.syllable_walk_tui.widgets import CorpusBrowserScreen


class PatchPanel(Static):
    """
    Panel displaying patch configuration controls.

    This widget will contain all the module controls (Oscillator, Filter,
    Envelope, LFO, Attenuator) for a single patch.

    Args:
        patch_name: Name of the patch ("A" or "B")
    """

    def __init__(self, patch_name: str, *args, **kwargs):
        """Initialize patch panel with given name."""
        super().__init__(*args, **kwargs)
        self.patch_name = patch_name

    def compose(self) -> ComposeResult:
        """Create child widgets for patch panel."""
        yield Label(f"PATCH {self.patch_name}", classes="patch-header")
        yield Label("", classes="spacer")

        # Corpus selection
        yield Button("Select Corpus Directory", id=f"select-corpus-{self.patch_name}")
        yield Label(
            "No corpus selected", id=f"corpus-status-{self.patch_name}", classes="corpus-status"
        )

        yield Label("", classes="spacer")
        yield Label("Min Len:    [2     ±]")
        yield Label("Max Len:    [5     ±]")
        yield Label("Walk Len:   [5     ±]")
        yield Label("Freq Bias:  [0.5   ─]")
        yield Label("Neighbors:  [10    ±]")
        yield Label("", classes="spacer")
        yield Label("Seed: [42      ] [🎲]")
        yield Label("", classes="spacer")
        yield Label("     [Generate]", classes="button-label")
        yield Label("", classes="spacer")
        yield Label("OUTPUT (10)", classes="section-header")
        yield Label("────────────────────", classes="divider")
        yield Label("(no generations yet)", classes="output-placeholder")


class StatsPanel(Static):
    """
    Panel displaying comparison statistics between patches.

    Shows parameter differences, output metrics, and phonetic analysis.
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for statistics panel."""
        yield Label("COMPARISON STATS", classes="stats-header")
        yield Label("", classes="spacer")
        yield Label("Differences:")
        yield Label("  (generate to compare)")
        yield Label("", classes="spacer")
        yield Label("Outputs:")
        yield Label("  A: 0 generated")
        yield Label("  B: 0 generated")
        yield Label("", classes="spacer")
        yield Label("(More stats as we")
        yield Label(" discover needs)")


class SyllableWalkerApp(App):
    """
    Main Textual application for Syllable Walker TUI.

    Provides interactive interface for exploring phonetic space through
    side-by-side patch configuration and real-time generation.

    Default Keybindings:
        q, Ctrl+Q: Quit application
        ?, F1: Show help
        P: Switch to Patch Config tab
        B: Switch to Blended Walk tab
        A: Switch to Analysis tab

    Note:
        All keybindings are user-configurable via
        ~/.config/pipeworks_tui/keybindings.toml
    """

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        layout: horizontal;
        width: 100%;
        height: 1fr;
    }

    .column {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    .patch-panel {
        width: 35%;
    }

    .stats-panel {
        width: 30%;
    }

    .patch-header {
        text-style: bold;
        color: $accent;
    }

    .stats-header {
        text-style: bold;
        color: $accent;
    }

    .section-header {
        text-style: bold;
        margin-top: 1;
    }

    .divider {
        color: $primary-darken-2;
    }

    .spacer {
        height: 1;
    }

    .button-label {
        text-align: center;
    }

    .output-placeholder {
        color: $text-muted;
        text-style: italic;
    }

    .corpus-status {
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    .corpus-status-valid {
        color: $success;
        text-style: none;
        margin-bottom: 1;
    }
    """

    def __init__(self):
        """Initialize application with default state and keybindings."""
        super().__init__()
        self.state = AppState()
        self.keybindings = load_keybindings()

        # Build dynamic bindings from config
        self._setup_bindings()

    def _setup_bindings(self) -> None:
        """Set up keybindings from configuration."""
        # Global bindings
        for key in self.keybindings.global_bindings["quit"]:
            self.bind(key, "quit", description="Quit", show=True)
        for key in self.keybindings.global_bindings["help"]:
            self.bind(key, "help", description="Help", show=True)

        # Tab switching bindings (show in footer for discoverability)
        patch_key = self.keybindings.get_primary_key("tabs", "patch_config")
        blended_key = self.keybindings.get_primary_key("tabs", "blended_walk")
        analysis_key = self.keybindings.get_primary_key("tabs", "analysis")

        for key in self.keybindings.tab_bindings["patch_config"]:
            self.bind(
                key, "switch_tab('patch-config')", description=f"{patch_key}:Patch", show=True
            )
        for key in self.keybindings.tab_bindings["blended_walk"]:
            self.bind(
                key, "switch_tab('blended-walk')", description=f"{blended_key}:Blended", show=True
            )
        for key in self.keybindings.tab_bindings["analysis"]:
            self.bind(
                key, "switch_tab('analysis')", description=f"{analysis_key}:Analysis", show=True
            )

        # Corpus selection bindings
        self.bind("1", "select_corpus_a", description="1:Corpus A", show=True)
        self.bind("2", "select_corpus_b", description="2:Corpus B", show=True)

    def compose(self) -> ComposeResult:
        """Create application layout."""
        yield Header(show_clock=False)

        # Get display keys for tab labels
        patch_key = self.keybindings.get_display_key("tabs", "patch_config")
        blended_key = self.keybindings.get_display_key("tabs", "blended_walk")
        analysis_key = self.keybindings.get_display_key("tabs", "analysis")

        # Tab bar for multi-screen navigation
        with TabbedContent(initial="patch-config"):
            with TabPane(f"[{patch_key}] Patch Config", id="patch-config"):
                # Three-column layout
                with Horizontal(id="main-container"):
                    with VerticalScroll(classes="column patch-panel"):
                        yield PatchPanel("A", id="patch-a")
                    with VerticalScroll(classes="column stats-panel"):
                        yield StatsPanel(id="stats")
                    with VerticalScroll(classes="column patch-panel"):
                        yield PatchPanel("B", id="patch-b")

            # Placeholder tabs for future screens
            with TabPane(f"[{blended_key}] Blended Walk", id="blended-walk"):
                yield Label("Blended Walk screen (Phase 3+)", classes="placeholder")

            with TabPane(f"[{analysis_key}] Analysis", id="analysis"):
                yield Label("Analysis screen (Phase 4+)", classes="placeholder")

        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """
        Switch to a specific tab.

        Args:
            tab_id: ID of the tab to switch to
        """
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id

    @on(Button.Pressed, "#select-corpus-A")
    def on_button_select_corpus_a(self) -> None:
        """Handle Patch A corpus selection button press."""
        self._select_corpus_for_patch("A")

    @on(Button.Pressed, "#select-corpus-B")
    def on_button_select_corpus_b(self) -> None:
        """Handle Patch B corpus selection button press."""
        self._select_corpus_for_patch("B")

    def action_select_corpus_a(self) -> None:
        """Action: Open corpus selector for Patch A (keybinding: 1)."""
        self._select_corpus_for_patch("A")

    def action_select_corpus_b(self) -> None:
        """Action: Open corpus selector for Patch B (keybinding: 2)."""
        self._select_corpus_for_patch("B")

    def _get_initial_browse_dir(self, patch_name: str) -> Path:
        """
        Get smart initial directory for corpus browser.

        Priority order:
        1. Patch's current corpus_dir (if already set)
        2. Last browsed directory (if set)
        3. _working/output/ (if exists)
        4. Home directory (fallback)

        Args:
            patch_name: "A" or "B"

        Returns:
            Path to start browsing from
        """
        patch = self.state.patch_a if patch_name == "A" else self.state.patch_b

        # 1. Use patch's current corpus_dir if set
        if patch.corpus_dir and patch.corpus_dir.exists():
            return patch.corpus_dir

        # 2. Use last browsed directory if set
        if self.state.last_browse_dir and self.state.last_browse_dir.exists():
            return self.state.last_browse_dir

        # 3. Try _working/output/ if it exists
        project_root = Path(__file__).parent.parent.parent
        working_output = project_root / "_working" / "output"
        if working_output.exists() and working_output.is_dir():
            return working_output

        # 4. Fall back to home directory
        return Path.home()

    @work
    async def _select_corpus_for_patch(self, patch_name: str) -> None:
        """
        Open directory browser and handle corpus selection for a patch.

        Args:
            patch_name: "A" or "B"
        """
        try:
            # Get smart initial directory
            initial_dir = self._get_initial_browse_dir(patch_name)

            # Open browser modal
            result = await self.push_screen_wait(CorpusBrowserScreen(initial_dir))

            if result:
                # Validate and store selection
                is_valid, corpus_type, error = validate_corpus_directory(result)

                if is_valid:
                    # Update patch state
                    patch = self.state.patch_a if patch_name == "A" else self.state.patch_b
                    patch.corpus_dir = result
                    patch.corpus_type = corpus_type

                    # Remember this location for next time
                    self.state.last_browse_dir = result.parent

                    # Update UI
                    try:
                        status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                        corpus_info = get_corpus_info(result)
                        status_label.update(corpus_info)
                        status_label.remove_class("corpus-status")
                        status_label.add_class("corpus-status-valid")
                    except Exception as e:
                        # Log UI update errors but don't fail
                        print(f"Warning: Could not update status label: {e}")

                    self.notify(f"Patch {patch_name}: Selected {corpus_type} corpus", timeout=3)
                else:
                    self.notify(f"Invalid corpus: {error}", severity="error", timeout=5)

            # Ensure focus returns to main screen after modal closes
            # This prevents keybinding issues after corpus selection
            try:
                tabs = self.query_one(TabbedContent)
                tabs.focus()
            except Exception:  # nosec B110
                pass  # Silently fail if we can't set focus

        except Exception as e:
            # Catch any errors to prevent silent failures
            self.notify(f"Error selecting corpus: {e}", severity="error", timeout=5)
            import traceback

            traceback.print_exc()

    def action_help(self) -> None:
        """Show help information."""
        # Placeholder for Phase 2+
        help_text = (
            "Syllable Walker TUI - Keybindings\n\n"
            f"[{self.keybindings.get_display_key('global', 'quit')}] Quit\n"
            f"[{self.keybindings.get_display_key('global', 'help')}] Help\n\n"
            f"Tabs:\n"
            f"[{self.keybindings.get_display_key('tabs', 'patch_config')}] Patch Config\n"
            f"[{self.keybindings.get_display_key('tabs', 'blended_walk')}] Blended Walk\n"
            f"[{self.keybindings.get_display_key('tabs', 'analysis')}] Analysis\n"
        )
        self.notify(help_text, timeout=5)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
