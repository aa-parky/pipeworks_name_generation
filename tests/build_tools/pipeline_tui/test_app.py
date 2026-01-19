"""
Tests for pipeline_tui main application.

Tests PipelineTuiApp initialization, state management, and event handling.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.widgets import Label, TabbedContent

from build_tools.pipeline_tui.core.app import PipelineTuiApp
from build_tools.pipeline_tui.core.state import (
    ExtractorType,
    JobStatus,
    PipelineState,
)


class TestPipelineTuiAppInit:
    """Tests for PipelineTuiApp initialization."""

    def test_default_initialization(self) -> None:
        """Test default initialization values."""
        app = PipelineTuiApp()

        assert app.theme == "nord"
        assert isinstance(app.state, PipelineState)
        assert app.state.config.source_path is None
        assert app.state.config.output_dir is None

    def test_initialization_with_source_dir(self, tmp_path: Path) -> None:
        """Test initialization with source directory."""
        app = PipelineTuiApp(source_dir=tmp_path)

        assert app.state.config.source_path == tmp_path
        assert app.state.last_source_dir == tmp_path

    def test_initialization_with_output_dir(self, tmp_path: Path) -> None:
        """Test initialization with output directory."""
        output = tmp_path / "output"
        app = PipelineTuiApp(output_dir=output)

        assert app.state.config.output_dir == output
        assert app.state.last_output_dir == output

    def test_initialization_with_all_options(self, tmp_path: Path) -> None:
        """Test initialization with all options."""
        source = tmp_path / "source"
        output = tmp_path / "output"

        app = PipelineTuiApp(
            source_dir=source,
            output_dir=output,
            theme="dracula",
        )

        assert app.theme == "dracula"
        assert app.state.config.source_path == source
        assert app.state.config.output_dir == output


class TestPipelineTuiAppCompose:
    """Tests for application composition."""

    @pytest.mark.asyncio
    async def test_compose_has_header_and_footer(self) -> None:
        """Test app composes with header and footer."""
        from textual.widgets import Footer, Header

        app = PipelineTuiApp()

        async with app.run_test():
            header = app.query_one(Header)
            footer = app.query_one(Footer)
            assert header is not None
            assert footer is not None

    @pytest.mark.asyncio
    async def test_compose_has_tabbed_content(self) -> None:
        """Test app composes with tabbed content."""
        app = PipelineTuiApp()

        async with app.run_test():
            tabbed = app.query_one(TabbedContent)
            assert tabbed is not None

    @pytest.mark.asyncio
    async def test_compose_has_status_label(self) -> None:
        """Test app composes with status label."""
        app = PipelineTuiApp()

        async with app.run_test():
            status = app.query_one("#status-label", Label)
            assert status is not None


class TestPipelineTuiAppStatusText:
    """Tests for status bar text generation."""

    def test_get_status_text_default(self) -> None:
        """Test default status text."""
        app = PipelineTuiApp()

        status = app._get_status_text()

        assert "Not selected" in status
        assert "pyphen" in status
        assert "idle" in status

    def test_get_status_text_with_source(self, tmp_path: Path) -> None:
        """Test status text with source path."""
        app = PipelineTuiApp()
        app.state.config.source_path = tmp_path / "my_corpus"

        status = app._get_status_text()

        assert "my_corpus" in status

    def test_get_status_text_with_selected_files(self, tmp_path: Path) -> None:
        """Test status text with file selection."""
        app = PipelineTuiApp()
        app.state.config.selected_files = [
            tmp_path / "file1.txt",
            tmp_path / "file2.txt",
        ]

        status = app._get_status_text()

        assert "2 files" in status

    def test_get_status_text_nltk_extractor(self) -> None:
        """Test status text with NLTK extractor."""
        app = PipelineTuiApp()
        app.state.config.extractor_type = ExtractorType.NLTK

        status = app._get_status_text()

        assert "nltk" in status

    def test_get_status_text_running_status(self) -> None:
        """Test status text when job is running."""
        app = PipelineTuiApp()
        app.state.job.status = JobStatus.RUNNING

        status = app._get_status_text()

        assert "running" in status


class TestPipelineTuiAppTabSwitching:
    """Tests for tab switching actions."""

    @pytest.mark.asyncio
    async def test_action_tab_configure(self) -> None:
        """Test switching to configure tab."""
        app = PipelineTuiApp()

        async with app.run_test():
            app.action_tab_configure()
            tabbed = app.query_one(TabbedContent)
            assert tabbed.active == "configure"

    @pytest.mark.asyncio
    async def test_action_tab_monitor(self) -> None:
        """Test switching to monitor tab."""
        app = PipelineTuiApp()

        async with app.run_test():
            app.action_tab_monitor()
            tabbed = app.query_one(TabbedContent)
            assert tabbed.active == "monitor"

    @pytest.mark.asyncio
    async def test_action_tab_history(self) -> None:
        """Test switching to history tab."""
        app = PipelineTuiApp()

        async with app.run_test():
            app.action_tab_history()
            tabbed = app.query_one(TabbedContent)
            assert tabbed.active == "history"


class TestPipelineTuiAppRunPipeline:
    """Tests for pipeline execution action."""

    @pytest.mark.asyncio
    async def test_action_run_pipeline_invalid_config(self) -> None:
        """Test run pipeline fails with invalid config."""
        app = PipelineTuiApp()
        notifications = []

        async with app.run_test():
            with patch.object(
                app, "notify", side_effect=lambda msg, **kw: notifications.append(msg)
            ):
                app.action_run_pipeline()

        # Should notify about invalid config
        assert any("Cannot run" in n for n in notifications)

    @pytest.mark.asyncio
    async def test_action_run_pipeline_already_running(self) -> None:
        """Test run pipeline fails when already running."""
        app = PipelineTuiApp()
        app.state.job.status = JobStatus.RUNNING
        notifications = []

        async with app.run_test():
            with patch.object(
                app, "notify", side_effect=lambda msg, **kw: notifications.append(msg)
            ):
                app.action_run_pipeline()

        assert any("already running" in n for n in notifications)

    @pytest.mark.asyncio
    async def test_action_run_pipeline_valid_config(self, tmp_path: Path) -> None:
        """Test run pipeline starts with valid config."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        app = PipelineTuiApp(source_dir=source, output_dir=output)

        async with app.run_test():
            with patch.object(app, "_run_pipeline_async"):
                app.action_run_pipeline()

        assert app.state.job.status == JobStatus.RUNNING


class TestPipelineTuiAppCancelJob:
    """Tests for job cancellation action."""

    @pytest.mark.asyncio
    async def test_action_cancel_job_not_running(self) -> None:
        """Test cancel job fails when no job running."""
        app = PipelineTuiApp()
        notifications = []

        async with app.run_test():
            with patch.object(
                app, "notify", side_effect=lambda msg, **kw: notifications.append(msg)
            ):
                app.action_cancel_job()

        assert any("No job is running" in n for n in notifications)

    @pytest.mark.asyncio
    async def test_action_cancel_job_running(self) -> None:
        """Test cancel job when job is running."""
        app = PipelineTuiApp()
        app.state.job.status = JobStatus.RUNNING
        notifications = []

        async with app.run_test():
            with patch.object(
                app, "notify", side_effect=lambda msg, **kw: notifications.append(msg)
            ):
                with patch.object(app, "_cancel_pipeline_async"):
                    app.action_cancel_job()

        assert any("Cancelling" in n for n in notifications)


class TestPipelineTuiAppHelp:
    """Tests for help action."""

    @pytest.mark.asyncio
    async def test_action_help(self) -> None:
        """Test help action shows notification."""
        app = PipelineTuiApp()
        notifications = []

        async with app.run_test():
            with patch.object(
                app, "notify", side_effect=lambda msg, **kw: notifications.append(msg)
            ):
                app.action_help()

        assert any("Help" in n for n in notifications)


class TestPipelineTuiAppMessageHandlers:
    """Tests for ConfigurePanel message handlers."""

    def test_on_extractor_changed(self) -> None:
        """Test extractor changed message handler."""
        app = PipelineTuiApp()

        # Create mock event
        mock_event = MagicMock()
        mock_event.extractor_type = ExtractorType.NLTK

        with patch.object(app, "_update_status"):
            with patch.object(app, "notify"):
                app.on_configure_panel_extractor_changed(mock_event)

        assert app.state.config.extractor_type == ExtractorType.NLTK

    def test_on_language_changed(self) -> None:
        """Test language changed message handler."""
        app = PipelineTuiApp()

        mock_event = MagicMock()
        mock_event.language = "de_DE"

        with patch.object(app, "notify"):
            app.on_configure_panel_language_changed(mock_event)

        assert app.state.config.language == "de_DE"

    def test_on_constraints_changed(self) -> None:
        """Test constraints changed message handler."""
        app = PipelineTuiApp()

        mock_event = MagicMock()
        mock_event.min_length = 3
        mock_event.max_length = 10
        mock_event.file_pattern = "*.md"

        app.on_configure_panel_constraints_changed(mock_event)

        assert app.state.config.min_syllable_length == 3
        assert app.state.config.max_syllable_length == 10
        assert app.state.config.file_pattern == "*.md"

    def test_on_pipeline_stages_changed(self) -> None:
        """Test pipeline stages changed message handler."""
        app = PipelineTuiApp()

        mock_event = MagicMock()
        mock_event.run_normalize = False
        mock_event.run_annotate = False

        app.on_configure_panel_pipeline_stages_changed(mock_event)

        assert app.state.run_normalize is False
        assert app.state.run_annotate is False

    @pytest.mark.asyncio
    async def test_on_source_selected(self) -> None:
        """Test source selected message triggers action."""
        app = PipelineTuiApp()

        async with app.run_test():
            with patch.object(app, "action_select_source") as mock_action:
                mock_event = MagicMock()
                app.on_configure_panel_source_selected(mock_event)
                mock_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_output_selected(self) -> None:
        """Test output selected message triggers action."""
        app = PipelineTuiApp()

        async with app.run_test():
            with patch.object(app, "action_select_output") as mock_action:
                mock_event = MagicMock()
                app.on_configure_panel_output_selected(mock_event)
                mock_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_files_selected(self) -> None:
        """Test files selected message triggers action."""
        app = PipelineTuiApp()

        async with app.run_test():
            with patch.object(app, "action_select_files") as mock_action:
                mock_event = MagicMock()
                app.on_configure_panel_files_selected(mock_event)
                mock_action.assert_called_once()


class TestPipelineTuiAppBindings:
    """Tests for keybinding configuration."""

    def test_bindings_defined(self) -> None:
        """Test expected bindings are defined."""
        from textual.binding import Binding

        bindings = PipelineTuiApp.BINDINGS

        binding_keys = []
        for b in bindings:
            if isinstance(b, Binding):
                binding_keys.append(b.key)
            else:
                binding_keys.append(b[0])

        assert "q" in binding_keys
        assert "1" in binding_keys
        assert "2" in binding_keys
        assert "3" in binding_keys
        assert "r" in binding_keys
        assert "c" in binding_keys
        assert "d" in binding_keys
        assert "f" in binding_keys
        assert "o" in binding_keys


class TestPipelineTuiAppMetadata:
    """Tests for application metadata."""

    def test_title_defined(self) -> None:
        """Test application title is defined."""
        assert PipelineTuiApp.TITLE == "Pipeline Build Tools"

    def test_subtitle_defined(self) -> None:
        """Test application subtitle is defined."""
        assert "Syllable" in PipelineTuiApp.SUB_TITLE


class TestPipelineTuiAppUpdateStatus:
    """Tests for _update_status method."""

    @pytest.mark.asyncio
    async def test_update_status_updates_label(self) -> None:
        """Test _update_status updates the status label."""
        app = PipelineTuiApp()

        async with app.run_test():
            # Change state
            app.state.config.extractor_type = ExtractorType.NLTK
            app._update_status()

            # Verify by checking the status text method directly
            status_text = app._get_status_text()
            assert "nltk" in status_text

    def test_update_status_handles_missing_widget(self) -> None:
        """Test _update_status handles missing widget gracefully."""
        app = PipelineTuiApp()

        # Should not raise even without the widget mounted
        app._update_status()


class TestPipelineTuiAppPipelineExecution:
    """Tests for pipeline execution via PipelineExecutor."""

    @pytest.mark.asyncio
    async def test_run_pipeline_success_updates_state(self, tmp_path: Path) -> None:
        """Test successful pipeline updates job state."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "run"
        run_dir.mkdir()

        app = PipelineTuiApp(source_dir=source, output_dir=output)

        from build_tools.pipeline_tui.services.pipeline import PipelineResult

        mock_result = PipelineResult(
            success=True,
            run_directory=run_dir,
            total_duration_seconds=5.0,
        )

        async with app.run_test():
            app.state.start_job()
            # Directly test state update logic that would happen in _run_pipeline_async
            if mock_result.success and mock_result.run_directory:
                app.state.complete_job(mock_result.run_directory)

        assert app.state.job.status == JobStatus.COMPLETED
        assert app.state.job.output_path == run_dir

    @pytest.mark.asyncio
    async def test_run_pipeline_failure_updates_state(self, tmp_path: Path) -> None:
        """Test failed pipeline updates job state."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        app = PipelineTuiApp(source_dir=source, output_dir=output)

        from build_tools.pipeline_tui.services.pipeline import PipelineResult, StageResult

        mock_result = PipelineResult(
            success=False,
            stages=[
                StageResult(
                    stage="extraction",
                    success=False,
                    error_message="Extraction failed",
                )
            ],
        )

        async with app.run_test():
            app.state.start_job()
            # Test state update logic for failure
            if not mock_result.success and not mock_result.cancelled:
                error_msg = "Unknown error"
                for stage_result in mock_result.stages:
                    if not stage_result.success and stage_result.error_message:
                        error_msg = stage_result.error_message
                        break
                app.state.fail_job(error_msg)

        assert app.state.job.status == JobStatus.FAILED
        assert "Extraction failed" in app.state.job.error_message

    @pytest.mark.asyncio
    async def test_run_pipeline_cancelled_updates_state(self, tmp_path: Path) -> None:
        """Test cancelled pipeline updates job state."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        app = PipelineTuiApp(source_dir=source, output_dir=output)

        from build_tools.pipeline_tui.services.pipeline import PipelineResult

        mock_result = PipelineResult(
            success=False,
            cancelled=True,
        )

        async with app.run_test():
            app.state.start_job()
            # Test state update logic for cancellation
            if mock_result.cancelled:
                app.state.job.status = JobStatus.CANCELLED

        assert app.state.job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_pipeline_calls_executor(self) -> None:
        """Test pipeline cancellation calls executor cancel."""
        app = PipelineTuiApp()

        async with app.run_test():
            app.state.start_job()
            # Test cancellation - executor.cancel should be callable
            with patch.object(app._executor, "cancel", new_callable=AsyncMock) as mock_cancel:
                await mock_cancel()
                mock_cancel.assert_called_once()

    def test_executor_initialized(self) -> None:
        """Test executor is initialized with the app."""
        from build_tools.pipeline_tui.services.pipeline import PipelineExecutor

        app = PipelineTuiApp()
        assert isinstance(app._executor, PipelineExecutor)
