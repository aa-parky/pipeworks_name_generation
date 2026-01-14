"""
Main Textual application for Syllable Walker TUI.

This module contains the primary App class and layout widgets for the
interactive terminal interface.

FOCUS MANAGEMENT PATTERN
========================

This app uses a centralized focus management pattern to prevent parameter
widgets from blocking app-level keybindings (b/a/p for tab switching).

Key Components:
1. App-level BINDINGS use Binding(..., priority=True) for global navigation
2. After modals close, explicitly blur focused widgets (line ~408)
3. Parameter widgets (IntSpinner, FloatSlider, SeedInput) auto-blur after
   value changes (see widgets.py for implementation)

This pattern ensures app-level bindings always fire correctly, even when
parameter widgets have focus. Without this pattern, Textual's focus system
would prevent tab switching after modal closure or parameter adjustment.

See widgets.py module docstring for detailed implementation requirements.
"""

from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Label, Static, TabbedContent, TabPane

from build_tools.syllable_walk_tui.config import load_keybindings
from build_tools.syllable_walk_tui.corpus import (
    get_corpus_info,
    load_annotated_data,
    load_corpus_data,
    validate_corpus_directory,
)
from build_tools.syllable_walk_tui.focus_manager import FocusManager
from build_tools.syllable_walk_tui.state import AppState
from build_tools.syllable_walk_tui.widgets import (
    CorpusBrowserScreen,
    FloatSlider,
    IntSpinner,
    SeedInput,
)


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

        # Parameter controls - matching Dialect profile defaults
        # Filter Module - Syllable Length
        yield IntSpinner(
            "Min Length",
            value=2,
            min_val=1,
            max_val=10,
            id=f"min-length-{self.patch_name}",
        )
        yield IntSpinner(
            "Max Length",
            value=5,
            min_val=1,
            max_val=10,
            id=f"max-length-{self.patch_name}",
        )

        # Envelope Module - Walk Length
        yield IntSpinner(
            "Walk Length",
            value=5,
            min_val=2,
            max_val=20,
            id=f"walk-length-{self.patch_name}",
        )

        # Oscillator Module - Max Feature Flips
        yield IntSpinner(
            "Max Flips",
            value=2,
            min_val=1,
            max_val=3,
            id=f"max-flips-{self.patch_name}",
        )

        # LFO Module - Temperature
        yield FloatSlider(
            "Temperature",
            value=0.7,
            min_val=0.1,
            max_val=5.0,
            step=0.1,
            precision=1,
            id=f"temperature-{self.patch_name}",
        )

        # LFO Module - Frequency Weight
        yield FloatSlider(
            "Freq Weight",
            value=0.0,
            min_val=-2.0,
            max_val=2.0,
            step=0.1,
            precision=1,
            id=f"freq-weight-{self.patch_name}",
        )

        # Attenuator Module - Neighbor Limit
        yield IntSpinner(
            "Neighbors",
            value=10,
            min_val=5,
            max_val=50,
            id=f"neighbors-{self.patch_name}",
        )

        yield Label("", classes="spacer")

        # Global - Seed Input with Random Button
        yield SeedInput(value=None, id=f"seed-{self.patch_name}")

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

    # Class-level bindings with priority=True to work even with focused widgets
    # Using Binding class explicitly to enable priority (allows bindings to fire
    # even when child widgets like IntSpinner/FloatSlider/SeedInput have focus)
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("question_mark", "help", "Help", priority=True),
        Binding("f1", "help", "Help", priority=True),
        Binding("p", "switch_tab('patch-config')", "Patch", priority=True),
        Binding("b", "switch_tab('blended-walk')", "Blended", priority=True),
        Binding("a", "switch_tab('analysis')", "Analysis", priority=True),
        Binding("1", "select_corpus_a", "Corpus A", priority=True),
        Binding("2", "select_corpus_b", "Corpus B", priority=True),
    ]

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
        """Initialize application with default state."""
        super().__init__()
        self.state = AppState()
        self.keybindings = load_keybindings()
        # Note: Keybindings are now defined in BINDINGS class attribute
        # Config-based overrides can be added in future if needed

    def compose(self) -> ComposeResult:
        """Create application layout."""
        yield Header(show_clock=False)

        # Tab bar for multi-screen navigation
        with TabbedContent(initial="patch-config"):
            with TabPane("[p] Patch Config", id="patch-config"):
                # Three-column layout
                with Horizontal(id="main-container"):
                    with VerticalScroll(classes="column patch-panel"):
                        yield PatchPanel("A", id="patch-a")
                    with VerticalScroll(classes="column stats-panel"):
                        yield StatsPanel(id="stats")
                    with VerticalScroll(classes="column patch-panel"):
                        yield PatchPanel("B", id="patch-b")

            # Placeholder tabs for future screens
            with TabPane("[b] Blended Walk", id="blended-walk"):
                yield Label("Blended Walk screen (Phase 3+)", classes="placeholder")

            with TabPane("[a] Analysis", id="analysis"):
                yield Label("Analysis screen (Phase 4+)", classes="placeholder")

        yield Footer()

    def on_mount(self) -> None:
        """
        Handle app mount event.

        Disables focus on VerticalScroll containers to prevent them from
        stealing focus when clicked. This ensures tab switching keybindings
        always work, even after mouse clicks.

        The issue: VerticalScroll.can_focus = True by default. When users
        click anywhere in the scroll area, it captures focus and doesn't
        release it. This breaks tab switching because the App's bindings
        only work when a focusable ancestor has focus.

        Solution: Disable focus on all VerticalScroll containers. They
        still scroll correctly, but they can't capture keyboard focus.
        """
        # Initialize centralized focus manager
        # Set debug=True and use `textual console` for focus debugging
        self.focus_manager = FocusManager(self, debug=False)

        for scroll_container in self.query(VerticalScroll):
            scroll_container.can_focus = False

        # Also disable focus on PatchPanel and StatsPanel containers
        # to prevent them from capturing focus during TAB navigation
        for patch_panel in self.query(PatchPanel):
            patch_panel.can_focus = False
        for stats_panel in self.query(StatsPanel):
            stats_panel.can_focus = False

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

            # CRITICAL FIX: Clear focus after modal closes using FocusManager
            # This prevents Textual from auto-focusing a parameter widget,
            # which would block app-level tab switching bindings (b/a/p)
            self.focus_manager.clear_focus_after_modal()

            if result:
                # Validate and store selection
                is_valid, corpus_type, error = validate_corpus_directory(result)

                if is_valid:
                    # Update patch state
                    patch = self.state.patch_a if patch_name == "A" else self.state.patch_b
                    patch.corpus_dir = result
                    patch.corpus_type = corpus_type

                    # === PHASE 1: Load quick metadata (FAST - synchronous) ===
                    # Load syllables list and frequencies (~50KB, <100ms)
                    # This is fast enough to do immediately without blocking
                    try:
                        syllables, frequencies = load_corpus_data(result)
                        patch.syllables = syllables
                        patch.frequencies = frequencies

                        # Remember this location for next time
                        self.state.last_browse_dir = result.parent

                        # Update UI to show quick metadata loaded
                        try:
                            status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                            corpus_info = get_corpus_info(result)

                            # Build detailed file list showing what was loaded
                            corpus_prefix = corpus_type.lower() if corpus_type else "nltk"
                            files_loaded = (
                                f"{corpus_info}\n"
                                f"─────────────────\n"
                                f"✓ {corpus_prefix}_syllables_unique.txt\n"
                                f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                                f"⏳ {corpus_prefix}_syllables_annotated.json"
                            )
                            status_label.update(files_loaded)
                            status_label.remove_class("corpus-status")
                            status_label.add_class("corpus-status-valid")
                        except Exception as e:
                            # Log UI update errors but don't fail
                            print(f"Warning: Could not update status label: {e}")

                        # Notify user that quick metadata loaded successfully
                        self.notify(
                            f"Patch {patch_name}: Loaded {len(syllables):,} syllables "
                            f"from {corpus_type} corpus",
                            timeout=2,
                        )

                        # === PHASE 2: Kick off background loading (SLOW - async) ===
                        # Load annotated data with phonetic features (~15MB, 1-2 seconds)
                        # This runs in background to avoid freezing the UI
                        # The _load_annotated_data_background method will:
                        # - Set is_loading_annotated = True
                        # - Load data in background thread
                        # - Update UI when complete
                        # - Handle errors gracefully
                        self._load_annotated_data_background(patch_name)

                    except Exception as e:
                        # Failed to load quick metadata - this is a critical error
                        # Don't proceed to annotated data loading
                        self.notify(f"Error loading corpus data: {e}", severity="error", timeout=5)
                        # Reset patch state since loading failed
                        patch.corpus_dir = None
                        patch.corpus_type = None
                        patch.syllables = None
                        patch.frequencies = None
                        patch.annotated_data = None
                        patch.is_loading_annotated = False
                        patch.loading_error = str(e)

                else:
                    self.notify(f"Invalid corpus: {error}", severity="error", timeout=5)

        except Exception as e:
            # Catch any errors to prevent silent failures
            self.notify(f"Error selecting corpus: {e}", severity="error", timeout=5)
            import traceback

            traceback.print_exc()

    @work
    async def _load_annotated_data_background(self, patch_name: str) -> None:
        """
        Load annotated phonetic data in background worker (non-blocking).

        This method runs in a background thread to load the large annotated.json
        file (typically 10-15MB, 400k-600k lines) without freezing the UI.

        The loading process:
        1. Set patch loading state (is_loading_annotated = True)
        2. Update UI to show "Loading..." status
        3. Load annotated data file (1-2 seconds)
        4. Update patch state with loaded data
        5. Update UI to show "Ready" status
        6. Handle any errors and update UI accordingly

        Args:
            patch_name: "A" or "B" to identify which patch to load for

        Note:
            This method uses the @work decorator which automatically runs
            the code in a background worker thread, preventing UI freezing.
            UI updates are scheduled back to the main thread.
        """
        # Get the patch we're loading for
        patch = self.state.patch_a if patch_name == "A" else self.state.patch_b

        # Safety check: ensure corpus directory is set
        if not patch.corpus_dir:
            self.notify(
                f"Patch {patch_name}: Cannot load annotated data - no corpus selected",
                severity="error",
                timeout=5,
            )
            return

        try:
            # === STEP 1: Set loading state ===
            # Mark patch as loading (disables Generate button in UI)
            patch.is_loading_annotated = True
            patch.loading_error = None

            # === STEP 2: Update UI to show loading state ===
            # This tells the user that background loading is happening
            try:
                status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                corpus_info = get_corpus_info(patch.corpus_dir)

                # Show loading progress with file list
                corpus_prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"
                files_loading = (
                    f"{corpus_info}\n"
                    f"─────────────────\n"
                    f"✓ {corpus_prefix}_syllables_unique.txt\n"
                    f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                    f"⏳ {corpus_prefix}_syllables_annotated.json (loading...)"
                )
                status_label.update(files_loading)
                status_label.remove_class("corpus-status")
                status_label.add_class("corpus-status-valid")
            except Exception as e:
                # Log UI update errors but don't fail the loading
                print(f"Warning: Could not update status label (loading): {e}")

            # Notify user that background loading started
            self.notify(
                f"Patch {patch_name}: Loading phonetic features...",
                timeout=2,
                severity="information",
            )

            # === STEP 3: Load annotated data (SLOW - 1-2 seconds) ===
            # This is the expensive operation that happens in the background
            # The @work decorator ensures this doesn't block the UI
            annotated_data, load_metadata = load_annotated_data(patch.corpus_dir)

            # === STEP 4: Update patch state with loaded data ===
            patch.annotated_data = annotated_data
            patch.is_loading_annotated = False

            # === STEP 5: Update UI to show ready state ===
            try:
                status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                corpus_info = get_corpus_info(patch.corpus_dir)
                syllable_count = len(annotated_data)

                # Build source indicator based on what was loaded
                source = load_metadata.get("source", "unknown")
                load_time = load_metadata.get("load_time_ms", "?")

                # Show only files that were actually loaded
                corpus_prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"

                if source == "sqlite":
                    # SQLite path: show corpus.db, JSON not loaded
                    files_ready = (
                        f"{corpus_info}\n"
                        f"─────────────────\n"
                        f"✓ {corpus_prefix}_syllables_unique.txt\n"
                        f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                        f"✓ corpus.db ({load_time}ms, SQLite)\n"
                        f"─────────────────\n"
                        f"Ready: {syllable_count:,} syllables"
                    )
                else:
                    # JSON fallback path: show annotated.json, SQLite not present
                    file_name = load_metadata.get("file_name", "annotated.json")
                    files_ready = (
                        f"{corpus_info}\n"
                        f"─────────────────\n"
                        f"✓ {corpus_prefix}_syllables_unique.txt\n"
                        f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                        f"✓ {file_name} ({load_time}ms, JSON)\n"
                        f"─────────────────\n"
                        f"Ready: {syllable_count:,} syllables"
                    )
                status_label.update(files_ready)
                status_label.remove_class("corpus-status")
                status_label.add_class("corpus-status-valid")
            except Exception as e:
                # Log UI update errors but don't fail the loading
                print(f"Warning: Could not update status label (complete): {e}")

            # Notify user that loading completed successfully
            if source == "sqlite":
                self.notify(
                    f"Patch {patch_name}: Loaded from SQLite ({len(annotated_data):,} syllables, {load_time}ms)",
                    timeout=3,
                    severity="information",
                )
            else:
                self.notify(
                    f"Patch {patch_name}: Loaded from JSON ({len(annotated_data):,} syllables, {load_time}ms)",
                    timeout=3,
                    severity="information",
                )

        except FileNotFoundError as e:
            # === ERROR HANDLING: Annotated file doesn't exist ===
            # This might happen if the corpus hasn't been processed with
            # syllable_feature_annotator yet
            patch.is_loading_annotated = False
            patch.loading_error = "Annotated data file not found"

            # Update UI to show error with file list
            try:
                status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                corpus_prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"
                files_error = (
                    f"{get_corpus_info(patch.corpus_dir)}\n"
                    f"─────────────────\n"
                    f"✓ {corpus_prefix}_syllables_unique.txt\n"
                    f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                    f"✗ {corpus_prefix}_syllables_annotated.json\n"
                    f"─────────────────\n"
                    f"Run syllable_feature_annotator"
                )
                status_label.update(files_error)
                status_label.remove_class("corpus-status-valid")
                status_label.add_class("corpus-status")
            except Exception:  # nosec B110
                pass  # Ignore UI update errors

            self.notify(f"Patch {patch_name}: {str(e)}", severity="error", timeout=5)

        except Exception as e:
            # === ERROR HANDLING: Other errors ===
            patch.is_loading_annotated = False
            patch.loading_error = str(e)

            # Update UI to show error with file list
            try:
                status_label = self.query_one(f"#corpus-status-{patch_name}", Label)
                corpus_prefix = patch.corpus_type.lower() if patch.corpus_type else "nltk"
                files_error = (
                    f"{get_corpus_info(patch.corpus_dir)}\n"
                    f"─────────────────\n"
                    f"✓ {corpus_prefix}_syllables_unique.txt\n"
                    f"✓ {corpus_prefix}_syllables_frequencies.json\n"
                    f"✗ {corpus_prefix}_syllables_annotated.json\n"
                    f"─────────────────\n"
                    f"Error: {str(e)[:30]}..."
                )
                status_label.update(files_error)
                status_label.remove_class("corpus-status-valid")
                status_label.add_class("corpus-status")
            except Exception:  # nosec B110
                pass  # Ignore UI update errors

            self.notify(
                f"Patch {patch_name}: Error loading annotated data: {e}",
                severity="error",
                timeout=5,
            )
            import traceback

            traceback.print_exc()

    def action_help(self) -> None:
        """Show help information."""
        help_text = (
            "Syllable Walker TUI - Keybindings\n\n"
            "[q] Quit\n"
            "[?] Help\n\n"
            "Tabs:\n"
            "[p] Patch Config\n"
            "[b] Blended Walk\n"
            "[a] Analysis\n\n"
            "Corpus:\n"
            "[1] Select Corpus A\n"
            "[2] Select Corpus B\n\n"
            "Parameters:\n"
            "[TAB] Navigate controls\n"
            "[j/k or +/-] Adjust values\n"
        )
        self.notify(help_text, timeout=10)

    def action_quit(self) -> None:  # type: ignore[override]
        """Quit the application."""
        self.exit()

    # =========================================================================
    # Parameter Change Handlers - Wire widgets to PatchState
    # =========================================================================

    @on(IntSpinner.Changed)
    def on_int_spinner_changed(self, event: IntSpinner.Changed) -> None:
        """Handle integer spinner value changes and update patch state."""
        # Use widget_id from the message
        widget_id = event.widget_id
        if not widget_id:
            return

        # Parse widget ID to determine patch and parameter
        # Format: "<param>-<patch>" e.g., "min-length-A"
        parts = widget_id.rsplit("-", 1)
        if len(parts) != 2:
            return

        param_name, patch_name = parts
        patch = self.state.patch_a if patch_name == "A" else self.state.patch_b

        # Update the appropriate parameter in patch state
        if param_name == "min-length":
            patch.min_length = event.value
        elif param_name == "max-length":
            patch.max_length = event.value
        elif param_name == "walk-length":
            patch.walk_length = event.value
        elif param_name == "max-flips":
            patch.max_flips = event.value
        elif param_name == "neighbors":
            patch.neighbor_limit = event.value

        # CRITICAL: Prevent auto-focus after parameter change
        # The widget already called blur(), but ensure nothing else gets focused
        self.focus_manager.prevent_auto_focus()

    @on(FloatSlider.Changed)
    def on_float_slider_changed(self, event: FloatSlider.Changed) -> None:
        """Handle float slider value changes and update patch state."""
        # Use widget_id from the message
        widget_id = event.widget_id
        if not widget_id:
            return

        # Parse widget ID to determine patch and parameter
        parts = widget_id.rsplit("-", 1)
        if len(parts) != 2:
            return

        param_name, patch_name = parts
        patch = self.state.patch_a if patch_name == "A" else self.state.patch_b

        # Update the appropriate parameter in patch state
        if param_name == "temperature":
            patch.temperature = event.value
        elif param_name == "freq-weight":
            patch.frequency_weight = event.value

        # CRITICAL: Prevent auto-focus after parameter change
        self.focus_manager.prevent_auto_focus()

    @on(SeedInput.Changed)
    def on_seed_changed(self, event: SeedInput.Changed) -> None:
        """Handle seed input changes and update patch state."""
        # Use widget_id from the message
        widget_id = event.widget_id
        if not widget_id:
            return

        # Parse widget ID to determine patch
        # Format: "seed-<patch>" e.g., "seed-A"
        parts = widget_id.rsplit("-", 1)
        if len(parts) != 2 or parts[0] != "seed":
            return

        patch_name = parts[1]
        patch = self.state.patch_a if patch_name == "A" else self.state.patch_b

        # Update seed in patch state
        if event.value is None:
            # Blank seed = generate new random seed
            patch.generate_seed()
        else:
            # Explicit seed value
            patch.seed = event.value
            patch.rng = __import__("random").Random(event.value)

        # CRITICAL: Prevent auto-focus after seed change
        self.focus_manager.prevent_auto_focus()
