"""
Tests for pipeline_tui state module.

Tests state dataclasses, enums, and state management methods.
"""

from datetime import datetime, timedelta
from pathlib import Path

from build_tools.pipeline_tui.core.state import (
    ExtractionConfig,
    ExtractorType,
    JobState,
    JobStatus,
    PipelineState,
)


class TestExtractorType:
    """Tests for ExtractorType enum."""

    def test_pyphen_value(self) -> None:
        """Test PYPHEN enum value exists."""
        assert ExtractorType.PYPHEN is not None

    def test_nltk_value(self) -> None:
        """Test NLTK enum value exists."""
        assert ExtractorType.NLTK is not None

    def test_distinct_values(self) -> None:
        """Test enum values are distinct."""
        assert ExtractorType.PYPHEN != ExtractorType.NLTK


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all expected statuses exist."""
        assert JobStatus.IDLE is not None
        assert JobStatus.CONFIGURING is not None
        assert JobStatus.RUNNING is not None
        assert JobStatus.COMPLETED is not None
        assert JobStatus.FAILED is not None
        assert JobStatus.CANCELLED is not None

    def test_status_count(self) -> None:
        """Test expected number of statuses."""
        assert len(JobStatus) == 6


class TestExtractionConfig:
    """Tests for ExtractionConfig dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = ExtractionConfig()

        assert config.extractor_type == ExtractorType.PYPHEN
        assert config.source_path is None
        assert config.selected_files == []
        assert config.output_dir is None
        assert config.language == "auto"
        assert config.min_syllable_length == 2
        assert config.max_syllable_length == 8
        assert config.file_pattern == "*.txt"

    def test_custom_values(self, tmp_path: Path) -> None:
        """Test custom values."""
        source = tmp_path / "source"
        output = tmp_path / "output"
        files = [tmp_path / "file1.txt", tmp_path / "file2.txt"]

        config = ExtractionConfig(
            extractor_type=ExtractorType.NLTK,
            source_path=source,
            selected_files=files,
            output_dir=output,
            language="de_DE",
            min_syllable_length=3,
            max_syllable_length=10,
            file_pattern="*.md",
        )

        assert config.extractor_type == ExtractorType.NLTK
        assert config.source_path == source
        assert config.selected_files == files
        assert config.output_dir == output
        assert config.language == "de_DE"
        assert config.min_syllable_length == 3
        assert config.max_syllable_length == 10
        assert config.file_pattern == "*.md"

    def test_has_file_selection_empty(self) -> None:
        """Test has_file_selection with no files selected."""
        config = ExtractionConfig()

        assert config.has_file_selection is False

    def test_has_file_selection_with_files(self, tmp_path: Path) -> None:
        """Test has_file_selection with files selected."""
        config = ExtractionConfig(selected_files=[tmp_path / "file.txt"])

        assert config.has_file_selection is True

    def test_is_valid_no_source_or_files(self) -> None:
        """Test validation fails with no source or files."""
        config = ExtractionConfig(output_dir=Path("/tmp/output"))

        is_valid, error = config.is_valid()

        assert is_valid is False
        assert "No source path selected" in error

    def test_is_valid_source_not_exists(self, tmp_path: Path) -> None:
        """Test validation fails when source doesn't exist."""
        config = ExtractionConfig(
            source_path=tmp_path / "nonexistent",
            output_dir=tmp_path / "output",
        )

        is_valid, error = config.is_valid()

        assert is_valid is False
        assert "does not exist" in error

    def test_is_valid_selected_file_not_exists(self, tmp_path: Path) -> None:
        """Test validation fails when selected file doesn't exist."""
        config = ExtractionConfig(
            selected_files=[tmp_path / "nonexistent.txt"],
            output_dir=tmp_path / "output",
        )

        is_valid, error = config.is_valid()

        assert is_valid is False
        assert "does not exist" in error

    def test_is_valid_no_output_dir(self, tmp_path: Path) -> None:
        """Test validation fails with no output directory."""
        source = tmp_path / "source"
        source.mkdir()

        config = ExtractionConfig(source_path=source, output_dir=None)

        is_valid, error = config.is_valid()

        assert is_valid is False
        assert "No output directory selected" in error

    def test_is_valid_min_exceeds_max(self, tmp_path: Path) -> None:
        """Test validation fails when min > max syllable length."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(
            source_path=source,
            output_dir=output,
            min_syllable_length=10,
            max_syllable_length=5,
        )

        is_valid, error = config.is_valid()

        assert is_valid is False
        assert "Min syllable length cannot exceed max" in error

    def test_is_valid_with_source_directory(self, tmp_path: Path) -> None:
        """Test validation passes with valid source directory."""
        source = tmp_path / "source"
        source.mkdir()
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(source_path=source, output_dir=output)

        is_valid, error = config.is_valid()

        assert is_valid is True
        assert error == ""

    def test_is_valid_with_selected_files(self, tmp_path: Path) -> None:
        """Test validation passes with valid selected files."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("test")
        output = tmp_path / "output"
        output.mkdir()

        config = ExtractionConfig(selected_files=[file1], output_dir=output)

        is_valid, error = config.is_valid()

        assert is_valid is True
        assert error == ""


class TestJobState:
    """Tests for JobState dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        state = JobState()

        assert state.status == JobStatus.IDLE
        assert state.config is None
        assert state.start_time is None
        assert state.end_time is None
        assert state.current_stage == ""
        assert state.progress_percent == 0
        assert state.log_messages == []
        assert state.output_path is None
        assert state.error_message == ""

    def test_add_log(self) -> None:
        """Test adding log messages."""
        state = JobState()

        state.add_log("Test message")

        assert len(state.log_messages) == 1
        assert "Test message" in state.log_messages[0]
        # Verify timestamp format [HH:MM:SS]
        assert state.log_messages[0].startswith("[")
        assert "]" in state.log_messages[0]

    def test_add_log_multiple(self) -> None:
        """Test adding multiple log messages."""
        state = JobState()

        state.add_log("First message")
        state.add_log("Second message")
        state.add_log("Third message")

        assert len(state.log_messages) == 3
        assert "First message" in state.log_messages[0]
        assert "Second message" in state.log_messages[1]
        assert "Third message" in state.log_messages[2]

    def test_duration_seconds_not_started(self) -> None:
        """Test duration when job hasn't started."""
        state = JobState()

        assert state.duration_seconds() is None

    def test_duration_seconds_running(self) -> None:
        """Test duration when job is running."""
        state = JobState(start_time=datetime.now() - timedelta(seconds=5))

        duration = state.duration_seconds()

        assert duration is not None
        assert duration >= 5.0
        assert duration < 10.0  # Should be close to 5 seconds

    def test_duration_seconds_completed(self) -> None:
        """Test duration when job is completed."""
        start = datetime.now() - timedelta(seconds=10)
        end = datetime.now() - timedelta(seconds=2)
        state = JobState(start_time=start, end_time=end)

        duration = state.duration_seconds()

        assert duration is not None
        # Duration should be ~8 seconds (10 - 2)
        assert 7.5 <= duration <= 8.5


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        state = PipelineState()

        assert isinstance(state.config, ExtractionConfig)
        assert isinstance(state.job, JobState)
        assert state.last_source_dir == Path.home()
        assert state.last_output_dir == Path.cwd() / "_working" / "output"
        assert state.run_normalize is True
        assert state.run_annotate is True

    def test_reset_job(self) -> None:
        """Test resetting job state."""
        state = PipelineState()
        state.job.status = JobStatus.RUNNING
        state.job.progress_percent = 50
        state.job.add_log("Some log message")

        state.reset_job()

        assert state.job.status == JobStatus.IDLE
        assert state.job.progress_percent == 0
        assert state.job.log_messages == []

    def test_start_job(self) -> None:
        """Test starting a job."""
        state = PipelineState()

        state.start_job()

        assert state.job.status == JobStatus.RUNNING
        assert state.job.config == state.config
        assert state.job.start_time is not None
        assert state.job.current_stage == "extraction"
        assert state.job.progress_percent == 0
        assert len(state.job.log_messages) == 1
        assert "started" in state.job.log_messages[0].lower()

    def test_complete_job(self, tmp_path: Path) -> None:
        """Test completing a job."""
        state = PipelineState()
        state.start_job()
        output_path = tmp_path / "output"

        state.complete_job(output_path)

        assert state.job.status == JobStatus.COMPLETED
        assert state.job.end_time is not None
        assert state.job.output_path == output_path
        assert state.job.progress_percent == 100
        # Should have 2 log messages: started + completed
        assert len(state.job.log_messages) == 2
        assert "completed" in state.job.log_messages[-1].lower()

    def test_fail_job(self) -> None:
        """Test failing a job."""
        state = PipelineState()
        state.start_job()
        error_msg = "Something went wrong"

        state.fail_job(error_msg)

        assert state.job.status == JobStatus.FAILED
        assert state.job.end_time is not None
        assert state.job.error_message == error_msg
        # Should have 2 log messages: started + failed
        assert len(state.job.log_messages) == 2
        assert "failed" in state.job.log_messages[-1].lower()
        assert error_msg in state.job.log_messages[-1]

    def test_reset_preserves_config(self) -> None:
        """Test that reset_job preserves configuration."""
        state = PipelineState()
        state.config.language = "de_DE"
        state.config.min_syllable_length = 5
        state.start_job()

        state.reset_job()

        assert state.config.language == "de_DE"
        assert state.config.min_syllable_length == 5

    def test_start_job_uses_current_config(self) -> None:
        """Test that start_job captures current config."""
        state = PipelineState()
        state.config.extractor_type = ExtractorType.NLTK
        state.config.language = "en_US"

        state.start_job()

        assert state.job.config is not None
        assert state.job.config.extractor_type == ExtractorType.NLTK
        assert state.job.config.language == "en_US"
