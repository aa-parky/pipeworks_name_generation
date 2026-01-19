"""Tests for syllable walker HTTP server module.

This module tests the web server functionality:
- WalkerHTTPHandler class and its methods
- HTTP GET/POST request handling
- API endpoints (/api/stats, /api/walk, /api/datasets, /api/load-dataset)
- run_server initialization and configuration
"""

import io
import json
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from build_tools.syllable_walk.server import WalkerHTTPHandler, run_server
from build_tools.syllable_walk.walker import SyllableWalker

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_syllables_data():
    """Sample syllable data for creating test files."""
    return [
        {
            "syllable": "ka",
            "frequency": 100,
            "features": {
                "starts_with_vowel": False,
                "starts_with_cluster": False,
                "starts_with_heavy_cluster": False,
                "contains_plosive": True,
                "contains_fricative": False,
                "contains_liquid": False,
                "contains_nasal": False,
                "short_vowel": True,
                "long_vowel": False,
                "ends_with_vowel": True,
                "ends_with_nasal": False,
                "ends_with_stop": False,
            },
        },
        {
            "syllable": "ki",
            "frequency": 80,
            "features": {
                "starts_with_vowel": False,
                "starts_with_cluster": False,
                "starts_with_heavy_cluster": False,
                "contains_plosive": True,
                "contains_fricative": False,
                "contains_liquid": False,
                "contains_nasal": False,
                "short_vowel": False,
                "long_vowel": True,
                "ends_with_vowel": True,
                "ends_with_nasal": False,
                "ends_with_stop": False,
            },
        },
        {
            "syllable": "ta",
            "frequency": 90,
            "features": {
                "starts_with_vowel": False,
                "starts_with_cluster": False,
                "starts_with_heavy_cluster": False,
                "contains_plosive": True,
                "contains_fricative": False,
                "contains_liquid": False,
                "contains_nasal": False,
                "short_vowel": True,
                "long_vowel": False,
                "ends_with_vowel": True,
                "ends_with_nasal": False,
                "ends_with_stop": False,
            },
        },
    ]


@pytest.fixture
def sample_data_file(tmp_path, sample_syllables_data):
    """Create a test syllables_annotated.json file."""
    file_path = tmp_path / "test_syllables.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_syllables_data, f)
    return file_path


@pytest.fixture
def initialized_walker(sample_data_file):
    """Pre-initialized walker for tests."""
    return SyllableWalker(sample_data_file, max_neighbor_distance=3, verbose=False)


@pytest.fixture
def mock_handler():
    """Create a mock HTTP handler for testing."""
    handler = MagicMock(spec=WalkerHTTPHandler)

    # Set up default class attributes
    handler.walker_cache = {}
    handler.max_neighbor_distance = 3
    handler.current_dataset_path = None
    handler.verbose = False

    # Set up wfile for response writing
    handler.wfile = io.BytesIO()

    return handler


@pytest.fixture
def handler_with_walker(mock_handler, initialized_walker, sample_data_file):
    """Handler with a pre-loaded walker."""
    path_key = str(sample_data_file)
    WalkerHTTPHandler.walker_cache = {path_key: initialized_walker}
    WalkerHTTPHandler.current_dataset_path = sample_data_file
    WalkerHTTPHandler.verbose = False

    mock_handler.walker_cache = WalkerHTTPHandler.walker_cache
    mock_handler.current_dataset_path = WalkerHTTPHandler.current_dataset_path
    mock_handler.verbose = WalkerHTTPHandler.verbose

    return mock_handler


# ============================================================
# WalkerHTTPHandler Class Attribute Tests
# ============================================================


class TestWalkerHTTPHandlerAttributes:
    """Test WalkerHTTPHandler class attributes."""

    def test_class_has_walker_cache(self):
        """Test handler has walker_cache class attribute."""
        assert hasattr(WalkerHTTPHandler, "walker_cache")
        assert isinstance(WalkerHTTPHandler.walker_cache, dict)

    def test_class_has_max_neighbor_distance(self):
        """Test handler has max_neighbor_distance class attribute."""
        assert hasattr(WalkerHTTPHandler, "max_neighbor_distance")
        assert WalkerHTTPHandler.max_neighbor_distance == 3

    def test_class_has_current_dataset_path(self):
        """Test handler has current_dataset_path class attribute."""
        assert hasattr(WalkerHTTPHandler, "current_dataset_path")

    def test_class_has_verbose(self):
        """Test handler has verbose class attribute."""
        assert hasattr(WalkerHTTPHandler, "verbose")
        assert isinstance(WalkerHTTPHandler.verbose, bool)


# ============================================================
# Handler Method Tests
# ============================================================


class TestHandlerMethods:
    """Test WalkerHTTPHandler methods."""

    def test_log_message_suppresses_output(self, capsys):
        """Test log_message suppresses logging output."""
        # Create minimal mock handler
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.log_message = WalkerHTTPHandler.log_message.__get__(handler, WalkerHTTPHandler)

        # Call log_message
        handler.log_message("%s %s", "GET", "/")

        # Should not produce output
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_get_current_walker_returns_none_when_no_dataset(self):
        """Test _get_current_walker returns None when no dataset loaded."""
        # Reset class state
        WalkerHTTPHandler.current_dataset_path = None
        WalkerHTTPHandler.walker_cache = {}

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.current_dataset_path = None
        handler.walker_cache = {}

        # Bind the method
        handler._get_current_walker = WalkerHTTPHandler._get_current_walker.__get__(
            handler, WalkerHTTPHandler
        )

        result = handler._get_current_walker()
        assert result is None

    def test_get_current_walker_returns_cached_walker(self, initialized_walker, sample_data_file):
        """Test _get_current_walker returns cached walker."""
        path_key = str(sample_data_file)
        WalkerHTTPHandler.walker_cache = {path_key: initialized_walker}
        WalkerHTTPHandler.current_dataset_path = sample_data_file

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.current_dataset_path = sample_data_file
        handler.walker_cache = WalkerHTTPHandler.walker_cache

        handler._get_current_walker = WalkerHTTPHandler._get_current_walker.__get__(
            handler, WalkerHTTPHandler
        )

        result = handler._get_current_walker()
        assert result is initialized_walker


# ============================================================
# Response Method Tests
# ============================================================


class TestResponseMethods:
    """Test response sending methods."""

    def test_send_response_writes_to_wfile(self):
        """Test _send_response writes content to wfile."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.wfile = io.BytesIO()

        # Bind the method
        handler._send_response = WalkerHTTPHandler._send_response.__get__(
            handler, WalkerHTTPHandler
        )

        handler._send_response("test content")

        # Check that send_response, send_header, end_headers were called
        handler.send_response.assert_called_once_with(200)
        assert handler.send_header.call_count >= 2  # Content-Type and Content-Length
        handler.end_headers.assert_called_once()

        # Check content was written
        handler.wfile.seek(0)
        content = handler.wfile.read()
        assert content == b"test content"

    def test_send_response_handles_broken_pipe(self):
        """Test _send_response handles BrokenPipeError gracefully."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.send_response.side_effect = BrokenPipeError()

        handler._send_response = WalkerHTTPHandler._send_response.__get__(
            handler, WalkerHTTPHandler
        )

        # Should not raise
        handler._send_response("test content")

    def test_send_response_handles_connection_reset(self):
        """Test _send_response handles ConnectionResetError gracefully."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.send_response.side_effect = ConnectionResetError()

        handler._send_response = WalkerHTTPHandler._send_response.__get__(
            handler, WalkerHTTPHandler
        )

        # Should not raise
        handler._send_response("test content")

    def test_send_json_response(self):
        """Test _send_json_response serializes and sends JSON."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.wfile = io.BytesIO()

        handler._send_response = MagicMock()
        handler._send_json_response = WalkerHTTPHandler._send_json_response.__get__(
            handler, WalkerHTTPHandler
        )

        test_data = {"key": "value", "count": 42}
        handler._send_json_response(test_data)

        handler._send_response.assert_called_once()
        call_args = handler._send_response.call_args
        assert call_args[0][0] == json.dumps(test_data)
        assert call_args[1]["content_type"] == "application/json"

    def test_send_error_response(self):
        """Test _send_error_response sends error JSON."""
        handler = MagicMock(spec=WalkerHTTPHandler)

        handler._send_json_response = MagicMock()
        handler._send_error_response = WalkerHTTPHandler._send_error_response.__get__(
            handler, WalkerHTTPHandler
        )

        handler._send_error_response("Test error message", status=400)

        handler._send_json_response.assert_called_once_with(
            {"error": "Test error message"}, status=400
        )


# ============================================================
# GET Request Tests
# ============================================================


class TestDoGET:
    """Test do_GET request handling."""

    def test_get_root_returns_html(self):
        """Test GET / returns HTML page."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/"
        handler._send_response = MagicMock()

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
        handler.do_GET()

        handler._send_response.assert_called_once()
        call_args = handler._send_response.call_args
        assert call_args[1]["content_type"] == "text/html"

    def test_get_styles_returns_css(self):
        """Test GET /styles.css returns CSS."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/styles.css"
        handler._send_response = MagicMock()

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
        handler.do_GET()

        handler._send_response.assert_called_once()
        call_args = handler._send_response.call_args
        assert call_args[1]["content_type"] == "text/css"

    def test_get_api_stats_with_no_walker(self):
        """Test GET /api/stats with no walker loaded."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/stats"
        handler._get_current_walker = MagicMock(return_value=None)
        handler._send_error_response = MagicMock()

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
        handler.do_GET()

        handler._send_error_response.assert_called_once()
        assert "No dataset loaded" in str(handler._send_error_response.call_args)

    def test_get_api_stats_with_walker(self, initialized_walker, sample_data_file):
        """Test GET /api/stats with walker loaded."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/stats"
        handler.current_dataset_path = sample_data_file
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_json_response = MagicMock()

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
        handler.do_GET()

        handler._send_json_response.assert_called_once()
        stats = handler._send_json_response.call_args[0][0]
        assert "total_syllables" in stats
        assert "max_neighbor_distance" in stats
        assert stats["total_syllables"] == 3

    def test_get_api_datasets_returns_list(self):
        """Test GET /api/datasets returns dataset list."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/datasets"
        handler.current_dataset_path = None
        handler._send_json_response = MagicMock()

        with patch("build_tools.syllable_walk.server.discover_datasets") as mock_discover:
            mock_discover.return_value = []

            handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
            handler.do_GET()

            handler._send_json_response.assert_called_once()
            response = handler._send_json_response.call_args[0][0]
            assert "datasets" in response
            assert "current" in response

    def test_get_api_datasets_handles_error(self):
        """Test GET /api/datasets handles discover errors."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/datasets"
        handler._send_error_response = MagicMock()

        with patch("build_tools.syllable_walk.server.discover_datasets") as mock_discover:
            mock_discover.side_effect = RuntimeError("Test error")

            handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
            handler.do_GET()

            handler._send_error_response.assert_called_once()
            assert "Error" in str(handler._send_error_response.call_args)

    def test_get_unknown_path_returns_404(self):
        """Test GET unknown path returns 404."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/unknown/path"

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)
        handler.do_GET()

        handler.send_error.assert_called_once_with(404, "Not Found")

    def test_get_404_handles_broken_pipe(self):
        """Test GET 404 handles connection errors gracefully."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/unknown/path"
        handler.send_error.side_effect = BrokenPipeError()

        handler.do_GET = WalkerHTTPHandler.do_GET.__get__(handler, WalkerHTTPHandler)

        # Should not raise
        handler.do_GET()


# ============================================================
# POST Request Tests
# ============================================================


class TestDoPOST:
    """Test do_POST request handling."""

    def test_post_api_walk_with_no_walker(self):
        """Test POST /api/walk with no walker loaded."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler._get_current_walker = MagicMock(return_value=None)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "No dataset loaded" in str(handler._send_error_response.call_args)

    def test_post_api_walk_empty_body(self, initialized_walker):
        """Test POST /api/walk with empty body."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": "0"}
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "Empty request body" in str(handler._send_error_response.call_args)

    def test_post_api_walk_with_profile(self, initialized_walker):
        """Test POST /api/walk with profile."""
        request_body = json.dumps(
            {"start": "ka", "profile": "dialect", "steps": 3, "seed": 42}
        ).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_json_response.assert_called_once()
        response = handler._send_json_response.call_args[0][0]
        assert "walk" in response
        assert "profile" in response
        assert response["profile"] == "dialect"

    def test_post_api_walk_with_custom_params(self, initialized_walker):
        """Test POST /api/walk with custom parameters."""
        request_body = json.dumps(
            {
                "start": "ka",
                "profile": "custom",
                "steps": 3,
                "max_flips": 2,
                "temperature": 1.0,
                "frequency_weight": 0.0,
                "seed": 42,
            }
        ).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_json_response.assert_called_once()
        response = handler._send_json_response.call_args[0][0]
        assert response["profile"] == "custom"

    def test_post_api_walk_random_start(self, initialized_walker):
        """Test POST /api/walk with no start (random)."""
        request_body = json.dumps(
            {"start": None, "profile": "dialect", "steps": 3, "seed": 42}
        ).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_json_response.assert_called_once()

    def test_post_api_walk_invalid_json(self, initialized_walker):
        """Test POST /api/walk with invalid JSON."""
        request_body = b"not valid json{"

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "Invalid JSON" in str(handler._send_error_response.call_args)

    def test_post_api_walk_invalid_syllable(self, initialized_walker):
        """Test POST /api/walk with invalid syllable."""
        request_body = json.dumps(
            {"start": "INVALID_XYZ", "profile": "dialect", "steps": 3}
        ).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/walk"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._get_current_walker = MagicMock(return_value=initialized_walker)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()

    def test_post_api_load_dataset_empty_body(self):
        """Test POST /api/load-dataset with empty body."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": "0"}
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "Empty request body" in str(handler._send_error_response.call_args)

    def test_post_api_load_dataset_missing_path(self):
        """Test POST /api/load-dataset with missing path."""
        request_body = json.dumps({}).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "Missing 'path'" in str(handler._send_error_response.call_args)

    def test_post_api_load_dataset_nonexistent_file(self):
        """Test POST /api/load-dataset with nonexistent file."""
        request_body = json.dumps({"path": "/nonexistent/file.json"}).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "not found" in str(handler._send_error_response.call_args)

    def test_post_api_load_dataset_cached(self, sample_data_file, initialized_walker):
        """Test POST /api/load-dataset with cached dataset."""
        path_key = str(sample_data_file)
        WalkerHTTPHandler.walker_cache = {path_key: initialized_walker}
        WalkerHTTPHandler.verbose = False

        request_body = json.dumps({"path": str(sample_data_file)}).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler.verbose = False
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_json_response.assert_called_once()
        response = handler._send_json_response.call_args[0][0]
        assert response["success"] is True

    def test_post_api_load_dataset_new(self, sample_data_file):
        """Test POST /api/load-dataset with new dataset."""
        WalkerHTTPHandler.walker_cache = {}
        WalkerHTTPHandler.verbose = False
        WalkerHTTPHandler.max_neighbor_distance = 3

        request_body = json.dumps({"path": str(sample_data_file)}).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler.verbose = False
        handler.max_neighbor_distance = 3
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_json_response.assert_called_once()
        response = handler._send_json_response.call_args[0][0]
        assert response["success"] is True
        assert response["total_syllables"] == 3

    def test_post_api_load_dataset_invalid_json(self):
        """Test POST /api/load-dataset with invalid JSON."""
        request_body = b"not valid json"

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler._send_error_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler._send_error_response.assert_called_once()
        assert "Invalid JSON" in str(handler._send_error_response.call_args)

    def test_post_unknown_path_returns_404(self):
        """Test POST unknown path returns 404."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/unknown"

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        handler.send_error.assert_called_once_with(404, "Not Found")

    def test_post_404_handles_broken_pipe(self):
        """Test POST 404 handles connection errors gracefully."""
        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/unknown"
        handler.send_error.side_effect = BrokenPipeError()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)

        # Should not raise
        handler.do_POST()


# ============================================================
# run_server Tests
# ============================================================


class TestRunServer:
    """Test run_server function."""

    def test_run_server_with_explicit_path(self, sample_data_file):
        """Test run_server with explicit data path."""
        with patch.object(HTTPServer, "serve_forever", side_effect=KeyboardInterrupt):
            with patch.object(HTTPServer, "shutdown"):
                # Should not raise
                run_server(
                    data_path=sample_data_file,
                    max_neighbor_distance=2,
                    port=5999,
                    verbose=False,
                )

        # Check handler was configured
        assert WalkerHTTPHandler.max_neighbor_distance == 2
        assert WalkerHTTPHandler.current_dataset_path == sample_data_file

    def test_run_server_auto_discover_no_datasets(self, tmp_path, monkeypatch):
        """Test run_server auto-discover with no datasets raises error."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError, match="No annotated datasets found"):
            run_server(data_path=None, verbose=False)

    def test_run_server_nonexistent_file_raises(self):
        """Test run_server with nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            run_server(data_path="/nonexistent/file.json", verbose=False)

    def test_run_server_auto_discover(self, tmp_path, monkeypatch, sample_syllables_data):
        """Test run_server auto-discovers dataset."""
        monkeypatch.chdir(tmp_path)

        # Create dataset
        output_dir = tmp_path / "_working" / "output"
        nltk_run = output_dir / "20260115_120000_nltk" / "data"
        nltk_run.mkdir(parents=True)
        with open(nltk_run / "nltk_syllables_annotated.json", "w", encoding="utf-8") as f:
            json.dump(sample_syllables_data, f)

        with patch.object(HTTPServer, "serve_forever", side_effect=KeyboardInterrupt):
            with patch.object(HTTPServer, "shutdown"):
                run_server(data_path=None, port=5998, verbose=False)

        # Should have loaded the dataset
        assert WalkerHTTPHandler.current_dataset_path is not None

    def test_run_server_port_in_use_increments(self, sample_data_file):
        """Test run_server increments port when in use."""
        call_count = 0
        original_init = HTTPServer.__init__

        def mock_init(self, server_address, handler_class):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError(48, "Address already in use")
            return original_init(self, server_address, handler_class)

        with patch.object(HTTPServer, "__init__", mock_init):
            with patch.object(HTTPServer, "serve_forever", side_effect=KeyboardInterrupt):
                with patch.object(HTTPServer, "shutdown"):
                    run_server(
                        data_path=sample_data_file,
                        port=5997,
                        verbose=False,
                    )

        assert call_count == 2

    def test_run_server_max_port_attempts_exceeded(self, sample_data_file):
        """Test run_server raises when max port attempts exceeded."""

        def always_fail(*args, **kwargs):
            raise OSError(48, "Address already in use")

        with patch.object(HTTPServer, "__init__", always_fail):
            with pytest.raises(OSError, match="Could not find available port"):
                run_server(
                    data_path=sample_data_file,
                    port=5996,
                    verbose=False,
                )

    def test_run_server_other_os_error_raises(self, sample_data_file):
        """Test run_server re-raises non-port-in-use errors."""

        def other_error(*args, **kwargs):
            raise OSError(99, "Some other error")

        with patch.object(HTTPServer, "__init__", other_error):
            with pytest.raises(OSError, match="Some other error"):
                run_server(
                    data_path=sample_data_file,
                    port=5995,
                    verbose=False,
                )

    def test_run_server_verbose_output(self, sample_data_file, capsys):
        """Test run_server verbose output."""
        with patch.object(HTTPServer, "serve_forever", side_effect=KeyboardInterrupt):
            with patch.object(HTTPServer, "shutdown"):
                run_server(
                    data_path=sample_data_file,
                    port=5994,
                    verbose=True,
                )

        captured = capsys.readouterr()
        assert "Syllable Walker" in captured.out
        assert "initialized" in captured.out.lower() or "ready" in captured.out.lower()

    def test_run_server_string_path(self, sample_data_file):
        """Test run_server accepts string path."""
        with patch.object(HTTPServer, "serve_forever", side_effect=KeyboardInterrupt):
            with patch.object(HTTPServer, "shutdown"):
                run_server(
                    data_path=str(sample_data_file),
                    port=5993,
                    verbose=False,
                )

        assert WalkerHTTPHandler.current_dataset_path == Path(sample_data_file)


# ============================================================
# Integration Tests
# ============================================================


class TestServerIntegration:
    """Integration tests for server behavior."""

    def test_walker_cache_persists_across_requests(self, sample_data_file, initialized_walker):
        """Test walker cache persists across requests."""
        path_key = str(sample_data_file)
        WalkerHTTPHandler.walker_cache = {path_key: initialized_walker}
        WalkerHTTPHandler.current_dataset_path = sample_data_file

        # Verify cache is accessible
        assert path_key in WalkerHTTPHandler.walker_cache
        assert WalkerHTTPHandler.walker_cache[path_key] is initialized_walker

    def test_dataset_switch_updates_current_path(
        self, sample_data_file, tmp_path, sample_syllables_data
    ):
        """Test switching datasets updates current_dataset_path."""
        # Create second dataset
        second_file = tmp_path / "second_data.json"
        with open(second_file, "w", encoding="utf-8") as f:
            json.dump(sample_syllables_data, f)

        WalkerHTTPHandler.walker_cache = {}
        WalkerHTTPHandler.verbose = False
        WalkerHTTPHandler.max_neighbor_distance = 3
        WalkerHTTPHandler.current_dataset_path = sample_data_file

        # Load second dataset
        request_body = json.dumps({"path": str(second_file)}).encode("utf-8")

        handler = MagicMock(spec=WalkerHTTPHandler)
        handler.path = "/api/load-dataset"
        handler.headers = {"Content-Length": str(len(request_body))}
        handler.rfile = io.BytesIO(request_body)
        handler.verbose = False
        handler.max_neighbor_distance = 3
        handler._send_json_response = MagicMock()

        handler.do_POST = WalkerHTTPHandler.do_POST.__get__(handler, WalkerHTTPHandler)
        handler.do_POST()

        # Current path should be updated
        assert WalkerHTTPHandler.current_dataset_path == second_file
