"""
Tests for pipeline_tui pipeline execution service.

Tests PipelineExecutor, StageResult, and PipelineResult dataclasses.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from build_tools.pipeline_tui.core.state import ExtractionConfig, ExtractorType
from build_tools.pipeline_tui.services.pipeline import (
    PipelineExecutor,
    PipelineResult,
    StageResult,
)


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        result = StageResult(stage="test", success=True)

        assert result.stage == "test"
        assert result.success is True
        assert result.output_path is None
        assert result.return_code == 0
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.duration_seconds == 0.0
        assert result.error_message == ""

    def test_all_fields(self, tmp_path: Path) -> None:
        """Test all fields populated."""
        result = StageResult(
            stage="extraction",
            success=False,
            output_path=tmp_path / "output",
            return_code=1,
            stdout="some output",
            stderr="error output",
            duration_seconds=5.5,
            error_message="Something failed",
        )

        assert result.stage == "extraction"
        assert result.success is False
        assert result.output_path == tmp_path / "output"
        assert result.return_code == 1
        assert result.stdout == "some output"
        assert result.stderr == "error output"
        assert result.duration_seconds == 5.5
        assert result.error_message == "Something failed"


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        result = PipelineResult(success=True)

        assert result.success is True
        assert result.stages == []
        assert result.run_directory is None
        assert result.cancelled is False
        assert result.total_duration_seconds == 0.0

    def test_with_stages(self, tmp_path: Path) -> None:
        """Test with populated stages."""
        stages = [
            StageResult(stage="extraction", success=True),
            StageResult(stage="normalization", success=True),
        ]

        result = PipelineResult(
            success=True,
            stages=stages,
            run_directory=tmp_path / "run",
            total_duration_seconds=10.0,
        )

        assert len(result.stages) == 2
        assert result.run_directory == tmp_path / "run"
        assert result.total_duration_seconds == 10.0

    def test_cancelled_result(self) -> None:
        """Test cancelled pipeline result."""
        result = PipelineResult(
            success=False,
            cancelled=True,
        )

        assert result.success is False
        assert result.cancelled is True


class TestPipelineExecutorInit:
    """Tests for PipelineExecutor initialization."""

    def test_initialization(self) -> None:
        """Test executor initializes correctly."""
        executor = PipelineExecutor()

        assert executor._current_process is None
        assert executor._cancelled is False


class TestPipelineExecutorValidation:
    """Tests for PipelineExecutor configuration validation."""

    @pytest.mark.asyncio
    async def test_invalid_config_no_source(self, tmp_path: Path) -> None:
        """Test validation fails with no source."""
        config = ExtractionConfig(output_dir=tmp_path)
        executor = PipelineExecutor()

        result = await executor.run_pipeline(config)

        assert result.success is False
        assert len(result.stages) == 1
        assert result.stages[0].stage == "validation"
        assert "No source path selected" in result.stages[0].error_message

    @pytest.mark.asyncio
    async def test_invalid_config_no_output(self, tmp_path: Path) -> None:
        """Test validation fails with no output dir."""
        source = tmp_path / "source"
        source.mkdir()
        config = ExtractionConfig(source_path=source)
        executor = PipelineExecutor()

        result = await executor.run_pipeline(config)

        assert result.success is False
        assert result.stages[0].stage == "validation"


class TestPipelineExecutorExtractionCommand:
    """Tests for extraction command building."""

    @pytest.mark.asyncio
    async def test_pyphen_extraction_command(self, tmp_path: Path) -> None:
        """Test pyphen extraction command building."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
            language="de_DE",
            min_syllable_length=2,
            max_syllable_length=8,
            file_pattern="*.txt",
        )
        executor = PipelineExecutor()

        captured_cmd = []

        async def mock_subprocess(cmd):
            captured_cmd.extend(cmd)
            return ("", "", 1)  # Return failure to stop pipeline

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        # Verify command includes pyphen module
        assert "build_tools.pyphen_syllable_extractor" in captured_cmd
        assert "--source" in captured_cmd
        assert str(source) in captured_cmd
        assert "--lang" in captured_cmd
        assert "de_DE" in captured_cmd
        assert "--min" in captured_cmd
        assert "2" in captured_cmd
        assert "--max" in captured_cmd
        assert "8" in captured_cmd

    @pytest.mark.asyncio
    async def test_nltk_extraction_command(self, tmp_path: Path) -> None:
        """Test NLTK extraction command building."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.NLTK,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        captured_cmd = []

        async def mock_subprocess(cmd):
            captured_cmd.extend(cmd)
            return ("", "", 1)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert "build_tools.nltk_syllable_extractor" in captured_cmd
        # NLTK doesn't have language option
        assert "--lang" not in captured_cmd

    @pytest.mark.asyncio
    async def test_auto_language_detection(self, tmp_path: Path) -> None:
        """Test auto language detection flag."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
            language="auto",
        )
        executor = PipelineExecutor()

        captured_cmd = []

        async def mock_subprocess(cmd):
            captured_cmd.extend(cmd)
            return ("", "", 1)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert "--auto" in captured_cmd
        assert "--lang" not in captured_cmd

    @pytest.mark.asyncio
    async def test_file_selection_command(self, tmp_path: Path) -> None:
        """Test command with specific file selection."""
        source = tmp_path / "source"
        source.mkdir()
        file1 = source / "file1.txt"
        file2 = source / "file2.txt"
        file1.write_text("test1")
        file2.write_text("test2")
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            selected_files=[file1, file2],
            output_dir=output,
        )
        executor = PipelineExecutor()

        captured_cmd = []

        async def mock_subprocess(cmd):
            captured_cmd.extend(cmd)
            return ("", "", 1)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert "--files" in captured_cmd
        assert str(file1) in captured_cmd
        assert str(file2) in captured_cmd
        # Should not have --source when using --files
        assert "--source" not in captured_cmd


class TestPipelineExecutorStages:
    """Tests for pipeline stage execution."""

    @pytest.mark.asyncio
    async def test_extraction_success(self, tmp_path: Path) -> None:
        """Test successful extraction stage."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        # Create a mock run directory
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        async def mock_subprocess(cmd):
            return (f"Run Directory: {run_dir}", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert result.success is True
        assert result.run_directory == run_dir
        assert len(result.stages) == 1
        assert result.stages[0].stage == "extraction"
        assert result.stages[0].success is True

    @pytest.mark.asyncio
    async def test_extraction_failure(self, tmp_path: Path) -> None:
        """Test failed extraction stage."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        async def mock_subprocess(cmd):
            return ("", "Error: Something went wrong", 1)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert result.success is False
        assert result.stages[0].success is False
        assert "Something went wrong" in result.stages[0].error_message

    @pytest.mark.asyncio
    async def test_normalization_stage(self, tmp_path: Path) -> None:
        """Test normalization stage runs after extraction."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        call_count = [0]
        captured_cmds = []

        async def mock_subprocess(cmd):
            captured_cmds.append(cmd.copy())
            call_count[0] += 1
            if call_count[0] == 1:
                return (f"Run Directory: {run_dir}", "", 0)
            return ("", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=True, run_annotate=False)

        assert result.success is True
        assert len(result.stages) == 2
        assert result.stages[0].stage == "extraction"
        assert result.stages[1].stage == "normalization"
        # Verify normalization command
        assert any("pyphen_syllable_normaliser" in str(cmd) for cmd in captured_cmds)

    @pytest.mark.asyncio
    async def test_normalization_skipped_when_disabled(self, tmp_path: Path) -> None:
        """Test normalization skipped when run_normalize=False."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        async def mock_subprocess(cmd):
            return (f"Run Directory: {run_dir}", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=False, run_annotate=False)

        assert result.success is True
        assert len(result.stages) == 1

    @pytest.mark.asyncio
    async def test_annotation_stage(self, tmp_path: Path) -> None:
        """Test annotation stage runs after normalization."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()
        # Create required files for annotation
        (run_dir / "pyphen_syllables_unique.txt").write_text("test\n")
        (run_dir / "pyphen_syllables_frequencies.json").write_text("{}")

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        call_count = [0]

        async def mock_subprocess(cmd):
            call_count[0] += 1
            if call_count[0] == 1:
                return (f"Run Directory: {run_dir}", "", 0)
            return ("", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=True, run_annotate=True)

        assert result.success is True
        # extraction + normalization + annotation + database
        assert len(result.stages) >= 3
        stage_names = [s.stage for s in result.stages]
        assert "annotation" in stage_names

    @pytest.mark.asyncio
    async def test_annotation_fails_missing_files(self, tmp_path: Path) -> None:
        """Test annotation fails when required files missing."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()
        # Don't create required files

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        call_count = [0]

        async def mock_subprocess(cmd):
            call_count[0] += 1
            if call_count[0] <= 2:  # extraction and normalization succeed
                return (f"Run Directory: {run_dir}", "", 0)
            return ("", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=True, run_annotate=True)

        assert result.success is False
        annotation_stage = next(s for s in result.stages if s.stage == "annotation")
        assert annotation_stage.success is False
        assert "not found" in annotation_stage.error_message


class TestPipelineExecutorCallbacks:
    """Tests for progress and log callbacks."""

    @pytest.mark.asyncio
    async def test_progress_callback(self, tmp_path: Path) -> None:
        """Test progress callback is called."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        progress_calls = []

        def on_progress(stage, pct, msg):
            progress_calls.append((stage, pct, msg))

        async def mock_subprocess(cmd):
            return (f"Run Directory: {run_dir}", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(
                config,
                run_normalize=False,
                run_annotate=False,
                on_progress=on_progress,
            )

        assert len(progress_calls) > 0
        assert any(call[0] == "extraction" for call in progress_calls)

    @pytest.mark.asyncio
    async def test_log_callback(self, tmp_path: Path) -> None:
        """Test log callback is called."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        log_messages = []

        def on_log(msg):
            log_messages.append(msg)

        async def mock_subprocess(cmd):
            return (f"Run Directory: {run_dir}", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            await executor.run_pipeline(
                config,
                run_normalize=False,
                run_annotate=False,
                on_log=on_log,
            )

        assert len(log_messages) > 0


class TestPipelineExecutorCancellation:
    """Tests for pipeline cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_sets_flag(self) -> None:
        """Test cancel sets the cancelled flag."""
        executor = PipelineExecutor()

        await executor.cancel()

        assert executor._cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_terminates_process(self) -> None:
        """Test cancel terminates running process."""
        executor = PipelineExecutor()
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock(return_value=0)
        executor._current_process = mock_process

        await executor.cancel()

        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_force_kills_on_timeout(self) -> None:
        """Test cancel force kills if terminate times out."""
        executor = PipelineExecutor()
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()

        async def slow_wait():
            await asyncio.sleep(10)

        mock_process.wait = slow_wait
        executor._current_process = mock_process

        await executor.cancel()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()


class TestPipelineExecutorParseRunDirectory:
    """Tests for run directory parsing from stdout."""

    def test_parse_run_directory_from_stdout(self, tmp_path: Path) -> None:
        """Test parsing run directory from stdout."""
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            output_dir=output,
        )
        executor = PipelineExecutor()

        stdout = f"Processing...\nRun Directory: {run_dir}\nDone."
        result = executor._parse_run_directory(stdout, config)

        assert result == run_dir

    def test_parse_run_directory_appends_suffix(self, tmp_path: Path) -> None:
        """Test run directory parsing appends suffix if needed."""
        output = tmp_path / "output"
        output.mkdir()
        base_dir = output / "20260119_120000"
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            output_dir=output,
        )
        executor = PipelineExecutor()

        # Stdout shows path without suffix
        stdout = f"Run Directory: {base_dir}"
        result = executor._parse_run_directory(stdout, config)

        assert result == run_dir

    def test_parse_run_directory_fallback_to_scan(self, tmp_path: Path) -> None:
        """Test fallback to scanning output directory."""
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            output_dir=output,
        )
        executor = PipelineExecutor()

        # Stdout doesn't contain run directory
        stdout = "Processing complete."
        result = executor._parse_run_directory(stdout, config)

        assert result == run_dir

    def test_parse_run_directory_nltk_suffix(self, tmp_path: Path) -> None:
        """Test NLTK uses _nltk suffix."""
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_nltk"
        run_dir.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.NLTK,
            output_dir=output,
        )
        executor = PipelineExecutor()

        stdout = "Processing complete."
        result = executor._parse_run_directory(stdout, config)

        assert result == run_dir

    def test_parse_run_directory_not_found(self, tmp_path: Path) -> None:
        """Test returns None when run directory not found."""
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            output_dir=output,
        )
        executor = PipelineExecutor()

        stdout = "Processing complete."
        result = executor._parse_run_directory(stdout, config)

        assert result is None


class TestPipelineExecutorNormalization:
    """Tests for normalization stage specifics."""

    @pytest.mark.asyncio
    async def test_normalization_no_run_directory(self, tmp_path: Path) -> None:
        """Test normalization fails without run directory."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        # Mock extraction to succeed but not return a run directory
        async def mock_subprocess(cmd):
            return ("No run directory info", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=True, run_annotate=False)

        # The extraction stage returns no run directory, so normalization fails
        assert result.success is False


class TestPipelineExecutorDatabaseBuild:
    """Tests for database build stage."""

    @pytest.mark.asyncio
    async def test_database_build_stage(self, tmp_path: Path) -> None:
        """Test database build runs after annotation."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()
        run_dir = output / "20260119_120000_pyphen"
        data_dir = run_dir / "data"
        data_dir.mkdir(parents=True)

        # Create required files
        (run_dir / "pyphen_syllables_unique.txt").write_text("test\n")
        (run_dir / "pyphen_syllables_frequencies.json").write_text("{}")

        config = ExtractionConfig(
            extractor_type=ExtractorType.PYPHEN,
            source_path=source,
            output_dir=output,
        )
        executor = PipelineExecutor()

        call_count = [0]
        captured_cmds = []

        async def mock_subprocess(cmd):
            captured_cmds.append(cmd.copy())
            call_count[0] += 1
            if call_count[0] == 1:
                return (f"Run Directory: {run_dir}", "", 0)
            return ("", "", 0)

        with patch.object(executor, "_run_subprocess", mock_subprocess):
            result = await executor.run_pipeline(config, run_normalize=True, run_annotate=True)

        assert result.success is True
        stage_names = [s.stage for s in result.stages]
        assert "database" in stage_names
        # Verify database build command
        assert any("corpus_sqlite_builder" in str(cmd) for cmd in captured_cmds)
