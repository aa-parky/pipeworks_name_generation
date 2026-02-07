"""Tests for the minimal Pipeworks webapp server and API helpers."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from pipeworks_name_generation.webapp.server import (
    WebAppHandler,
    _connect_database,
    _fetch_text_rows,
    _get_package_table,
    _import_package_pair,
    _initialize_schema,
    _list_package_tables,
    _list_packages,
    _quote_identifier,
    _slugify_identifier,
    create_handler_class,
)


def _build_sample_package_pair(tmp_path: Path) -> tuple[Path, Path]:
    """Create a realistic metadata+zip test pair with two ``*.txt`` files."""
    metadata_path = tmp_path / "goblin_flower-latin_selections_metadata.json"
    zip_path = tmp_path / "goblin_flower-latin_selections.zip"

    payload = {
        "common_name": "Goblin Flower Latin",
        "files_included": [
            "nltk_first_name_2syl.txt",
            "nltk_last_name_2syl.txt",
            "nltk_first_name_2syl.json",
        ],
    }
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("selections/nltk_first_name_2syl.txt", "alfa\n\nbeta\ngamma\n")
        archive.writestr("selections/nltk_last_name_2syl.txt", "thorn\nbriar\n")
        archive.writestr("selections/nltk_first_name_2syl.json", '{"ignored": true}')

    return metadata_path, zip_path


class _HandlerHarness:
    """Small in-process harness for route testing without opening sockets."""

    def __init__(self, *, path: str, db_path: Path, body: dict[str, Any] | None = None) -> None:
        payload = b""
        if body is not None:
            payload = json.dumps(body).encode("utf-8")

        self.path = path
        self.db_path = db_path
        self.verbose = False
        self.headers = {"Content-Length": str(len(payload))}
        self.rfile = io.BytesIO(payload)
        self.wfile = io.BytesIO()
        self.response_status = 0
        self.response_headers: dict[str, str] = {}
        self.error_status: int | None = None
        self.error_message: str | None = None

        # Bind handler methods directly so route logic executes unchanged.
        self._send_text = WebAppHandler._send_text.__get__(self, WebAppHandler)
        self._send_json = WebAppHandler._send_json.__get__(self, WebAppHandler)
        self._read_json_body = WebAppHandler._read_json_body.__get__(self, WebAppHandler)
        self._handle_import = WebAppHandler._handle_import.__get__(self, WebAppHandler)
        self._handle_generation = WebAppHandler._handle_generation.__get__(self, WebAppHandler)
        self.do_GET = WebAppHandler.do_GET.__get__(self, WebAppHandler)
        self.do_POST = WebAppHandler.do_POST.__get__(self, WebAppHandler)

    def send_response(self, status: int) -> None:
        """Store HTTP status code sent by handler logic."""
        self.response_status = status

    def send_header(self, name: str, value: str) -> None:
        """Capture response headers for assertions when needed."""
        self.response_headers[name] = value

    def end_headers(self) -> None:
        """Mirror BaseHTTPRequestHandler API; no-op for harness."""

    def send_error(self, code: int, message: str | None = None) -> None:
        """Capture error responses emitted by unknown-route handling."""
        self.error_status = code
        self.error_message = message

    def json_body(self) -> dict[str, Any]:
        """Decode written response body as JSON."""
        self.wfile.seek(0)
        payload = self.wfile.read().decode("utf-8")
        return json.loads(payload) if payload else {}


def test_slugify_identifier_normalizes_input() -> None:
    """Slugify should normalize punctuation, empties, and leading digits."""
    assert _slugify_identifier("Goblin Flower Latin", max_length=24) == "goblin_flower_latin"
    assert _slugify_identifier("%%%###", max_length=24) == "item"
    assert _slugify_identifier("123_name", max_length=24).startswith("n_")


def test_quote_identifier_rejects_unsafe_name() -> None:
    """SQL identifier quoting should reject non-identifier characters."""
    with pytest.raises(ValueError):
        _quote_identifier("drop table x;")


def test_import_package_pair_populates_schema_and_rows(tmp_path: Path) -> None:
    """Importer should create one SQLite table per listed txt file."""
    db_path = tmp_path / "webapp.sqlite3"
    metadata_path, zip_path = _build_sample_package_pair(tmp_path)

    with _connect_database(db_path) as conn:
        _initialize_schema(conn)
        result = _import_package_pair(conn, metadata_path=metadata_path, zip_path=zip_path)

        assert result["package_name"] == "Goblin Flower Latin"
        assert len(result["tables"]) == 2

        packages = _list_packages(conn)
        assert len(packages) == 1
        package_id = packages[0]["id"]

        tables = _list_package_tables(conn, package_id)
        assert len(tables) == 2
        assert {table["source_txt_name"] for table in tables} == {
            "nltk_first_name_2syl.txt",
            "nltk_last_name_2syl.txt",
        }

        first_table = tables[0]
        meta = _get_package_table(conn, int(first_table["id"]))
        assert meta is not None
        rows = _fetch_text_rows(conn, str(meta["table_name"]), offset=0, limit=20)
        assert rows
        assert all("value" in row for row in rows)


def test_import_package_pair_rejects_duplicate_pair(tmp_path: Path) -> None:
    """Importing the same metadata+zip pair twice should fail cleanly."""
    db_path = tmp_path / "webapp.sqlite3"
    metadata_path, zip_path = _build_sample_package_pair(tmp_path)

    with _connect_database(db_path) as conn:
        _initialize_schema(conn)
        _import_package_pair(conn, metadata_path=metadata_path, zip_path=zip_path)

        with pytest.raises(ValueError, match="already been imported"):
            _import_package_pair(conn, metadata_path=metadata_path, zip_path=zip_path)


def test_import_package_pair_rejects_invalid_files_included_type(tmp_path: Path) -> None:
    """Metadata ``files_included`` must be list when provided."""
    db_path = tmp_path / "webapp.sqlite3"
    metadata_path = tmp_path / "bad_metadata.json"
    zip_path = tmp_path / "ok.zip"
    metadata_path.write_text(
        json.dumps({"common_name": "Invalid", "files_included": "nltk_first_name_2syl.txt"}),
        encoding="utf-8",
    )
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("selections/nltk_first_name_2syl.txt", "alfa\n")

    with _connect_database(db_path) as conn:
        _initialize_schema(conn)
        with pytest.raises(ValueError, match="files_included"):
            _import_package_pair(conn, metadata_path=metadata_path, zip_path=zip_path)


def test_api_endpoints_import_and_browse_rows(tmp_path: Path) -> None:
    """End-to-end API flow should import package and expose rows via routes."""
    metadata_path, zip_path = _build_sample_package_pair(tmp_path)
    db_path = tmp_path / "webapi.sqlite3"

    health = _HandlerHarness(path="/api/health", db_path=db_path)
    health.do_GET()
    assert health.response_status == 200
    assert health.json_body()["ok"] is True

    importer = _HandlerHarness(
        path="/api/import",
        db_path=db_path,
        body={
            "metadata_json_path": str(metadata_path),
            "package_zip_path": str(zip_path),
        },
    )
    importer.do_POST()
    import_payload = importer.json_body()
    assert importer.response_status == 200
    assert import_payload["package_name"] == "Goblin Flower Latin"
    assert len(import_payload["tables"]) == 2

    packages = _HandlerHarness(path="/api/database/packages", db_path=db_path)
    packages.do_GET()
    packages_payload = packages.json_body()
    assert packages.response_status == 200
    assert packages_payload["packages"]
    package_id = int(packages_payload["packages"][0]["id"])

    tables = _HandlerHarness(
        path=f"/api/database/package-tables?package_id={package_id}",
        db_path=db_path,
    )
    tables.do_GET()
    tables_payload = tables.json_body()
    assert tables.response_status == 200
    assert tables_payload["tables"]
    table_id = int(tables_payload["tables"][0]["id"])

    rows = _HandlerHarness(
        path=f"/api/database/table-rows?table_id={table_id}&offset=0&limit=20",
        db_path=db_path,
    )
    rows.do_GET()
    rows_payload = rows.json_body()
    assert rows.response_status == 200
    assert rows_payload["rows"]
    assert rows_payload["limit"] == 20

    missing = _HandlerHarness(path="/api/database/table-rows", db_path=db_path)
    missing.do_GET()
    missing_payload = missing.json_body()
    assert missing.response_status == 400
    assert "table_id" in missing_payload["error"]


def test_create_handler_class_binds_runtime_values(tmp_path: Path) -> None:
    """Bound handler class should reflect runtime ``verbose`` and ``db_path``."""
    db_path = tmp_path / "bound.sqlite3"
    bound = create_handler_class(verbose=False, db_path=db_path)
    assert bound.verbose is False
    assert bound.db_path == db_path
