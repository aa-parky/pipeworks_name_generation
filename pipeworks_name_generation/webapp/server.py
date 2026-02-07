"""Simple web server with Import, Generation, and Database View tabs.

This version stores package imports in SQLite and creates one SQLite data table
for each imported ``*.txt`` selection file. JSON files are intentionally ignored
for now, per current requirements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import sqlite3
import zipfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import parse_qs, urlsplit

from pipeworks_name_generation.webapp.config import (
    ServerSettings,
    apply_runtime_overrides,
    load_server_settings,
)

# Keep pagination intentionally small so database browsing is readable.
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 200

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pipeworks Name Generator</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #121a2d;
      --panel-2: #0f172a;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --border: #334155;
      --accent: #22d3ee;
      --accent-2: #0891b2;
      --ok: #34d399;
      --err: #f87171;
    }
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      background: radial-gradient(circle at top right, #1e293b, var(--bg));
      color: var(--text);
    }
    .wrap {
      max-width: 1280px;
      margin: 1.4rem auto;
      padding: 0 1rem;
    }
    .card {
      border: 1px solid var(--border);
      background: color-mix(in srgb, var(--panel) 92%, black 8%);
      border-radius: 12px;
      padding: 1rem;
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.25);
    }
    h1 {
      margin: 0 0 0.9rem 0;
      font-size: 1.35rem;
    }
    .tabs {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1rem;
      padding-bottom: 0.8rem;
    }
    .tab {
      border: 1px solid var(--border);
      background: var(--panel-2);
      color: var(--text);
      border-radius: 8px;
      padding: 0.45rem 0.7rem;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.9rem;
    }
    .tab.active {
      border-color: color-mix(in srgb, var(--accent) 65%, white 35%);
      background: color-mix(in srgb, var(--accent-2) 22%, var(--panel-2) 78%);
    }
    .panel {
      display: none;
    }
    .panel.active {
      display: block;
    }
    .grid {
      display: grid;
      grid-template-columns: 220px 1fr;
      gap: 0.6rem;
      align-items: center;
      margin-bottom: 0.6rem;
    }
    input, select {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--border);
      background: #0a1324;
      color: var(--text);
      border-radius: 8px;
      padding: 0.5rem 0.6rem;
      font-size: 0.9rem;
    }
    button {
      border: 1px solid color-mix(in srgb, var(--accent) 75%, white 25%);
      background: color-mix(in srgb, var(--accent-2) 35%, #020617 65%);
      color: #ecfeff;
      border-radius: 8px;
      padding: 0.5rem 0.8rem;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.9rem;
    }
    button:hover {
      filter: brightness(1.1);
    }
    button[disabled] {
      opacity: 0.45;
      cursor: default;
      filter: none;
    }
    .row-buttons {
      margin-top: 0.4rem;
      margin-bottom: 0.8rem;
      display: flex;
      gap: 0.45rem;
      align-items: center;
    }
    .muted { color: var(--muted); }
    .ok { color: var(--ok); }
    .err { color: var(--err); }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }
    th, td {
      border-bottom: 1px solid var(--border);
      text-align: left;
      padding: 0.45rem;
      vertical-align: top;
    }
    ul {
      margin-top: 0.5rem;
      padding-left: 1.25rem;
    }
    li {
      line-height: 1.35;
      margin-bottom: 0.35rem;
    }
    code {
      color: #67e8f9;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .split {
      display: grid;
      grid-template-columns: minmax(360px, 440px) minmax(0, 1fr);
      gap: 1.1rem;
      align-items: start;
    }
    .db-sidebar .grid {
      grid-template-columns: 90px 1fr;
    }
    .db-sidebar select {
      min-width: 0;
    }
    #db-table-list {
      margin-top: 0.6rem;
      margin-bottom: 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.65rem 0.8rem;
      max-height: 56vh;
      overflow: auto;
      background: color-mix(in srgb, var(--panel-2) 85%, black 15%);
    }
    #db-row-body td:first-child {
      width: 90px;
      white-space: nowrap;
    }
    .db-main table {
      table-layout: fixed;
    }
    .db-main .row-buttons {
      flex-wrap: wrap;
      gap: 0.55rem;
    }
    #db-page-status {
      margin-left: 0.15rem;
    }
    @media (max-width: 980px) {
      .split { grid-template-columns: 1fr; }
    }
    @media (max-width: 800px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Pipeworks Name Generator</h1>
      <div class="tabs">
        <button type="button" class="tab active" data-tab="import">Import</button>
        <button type="button" class="tab" data-tab="generation">Generation</button>
        <button type="button" class="tab" data-tab="database">Database View</button>
      </div>

      <section class="panel active" id="panel-import">
        <div class="grid">
          <label for="metadata-path">Metadata JSON Path</label>
          <input id="metadata-path" type="text" placeholder="/path/to/package_metadata.json" />
        </div>
        <div class="grid">
          <label for="zip-path">Package ZIP Path</label>
          <input id="zip-path" type="text" placeholder="/path/to/package.zip" />
        </div>
        <div class="row-buttons">
          <button type="button" id="import-btn">Import Pair</button>
        </div>
        <p id="import-status" class="muted">Waiting for input.</p>
      </section>

      <section class="panel" id="panel-generation">
        <div class="grid">
          <label for="name-class">Name Class</label>
          <select id="name-class">
            <option value="first_name">First Name</option>
            <option value="last_name">Last Name</option>
            <option value="object_name">Object Name</option>
            <option value="place_name">Place Name</option>
          </select>
        </div>
        <div class="grid">
          <label for="name-count">Count</label>
          <input id="name-count" type="number" min="1" max="20" value="5" />
        </div>
        <div class="row-buttons">
          <button type="button" id="generate-btn">Generate</button>
        </div>
        <p id="generation-status" class="muted">No names generated yet.</p>
        <ul id="generation-list"></ul>
      </section>

      <section class="panel" id="panel-database">
        <div class="split">
          <div class="db-sidebar">
            <div class="row-buttons">
              <button type="button" id="db-refresh-packages">Refresh Packages</button>
            </div>
            <div class="grid">
              <label for="db-package-select">Package</label>
              <select id="db-package-select"></select>
            </div>
            <div class="grid">
              <label for="db-table-select">Table</label>
              <select id="db-table-select"></select>
            </div>
            <p class="muted" id="db-status">Load packages to begin browsing.</p>
            <ul id="db-table-list"></ul>
          </div>
          <div class="db-main">
            <div class="row-buttons">
              <button type="button" id="db-prev-btn">Previous</button>
              <button type="button" id="db-next-btn">Next</button>
              <span id="db-page-status" class="muted">Rows 0-0</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Line</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody id="db-row-body"></tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </div>

  <script>
    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll(\"'\", '&#39;');
    }

    const tabs = Array.from(document.querySelectorAll('.tab'));
    const panels = {
      import: document.getElementById('panel-import'),
      generation: document.getElementById('panel-generation'),
      database: document.getElementById('panel-database'),
    };

    const dbState = {
      tableId: null,
      offset: 0,
      limit: 20,
      total: 0,
      packageId: null,
    };

    function setActiveTab(tabName) {
      for (const tab of tabs) {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
      }
      for (const [name, panel] of Object.entries(panels)) {
        panel.classList.toggle('active', name === tabName);
      }
    }

    for (const tab of tabs) {
      tab.addEventListener('click', () => setActiveTab(tab.dataset.tab));
    }

    async function importPair() {
      const status = document.getElementById('import-status');
      status.className = 'muted';
      status.textContent = 'Importing...';

      const payload = {
        metadata_json_path: document.getElementById('metadata-path').value.trim(),
        package_zip_path: document.getElementById('zip-path').value.trim(),
      };

      const response = await fetch('/api/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      status.className = response.ok ? 'ok' : 'err';
      status.textContent = data.message || data.error || 'Import failed.';

      if (response.ok) {
        await loadPackages();
      }
    }

    async function generateNames() {
      const status = document.getElementById('generation-status');
      const list = document.getElementById('generation-list');
      status.className = 'muted';
      status.textContent = 'Generating...';
      list.innerHTML = '';

      const payload = {
        name_class: document.getElementById('name-class').value,
        count: Number(document.getElementById('name-count').value || '5'),
      };

      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        status.className = 'err';
        status.textContent = data.error || 'Generation failed.';
        return;
      }

      status.className = 'ok';
      status.textContent = data.message || 'Generated.';
      for (const name of data.names || []) {
        const li = document.createElement('li');
        li.textContent = name;
        list.appendChild(li);
      }
    }

    async function loadPackages() {
      const packageSelect = document.getElementById('db-package-select');
      const status = document.getElementById('db-status');
      status.className = 'muted';
      status.textContent = 'Loading packages...';

      const response = await fetch('/api/database/packages');
      const data = await response.json();
      packageSelect.innerHTML = '';

      if (!response.ok) {
        status.className = 'err';
        status.textContent = data.error || 'Failed to load packages.';
        return;
      }

      const packages = data.packages || [];
      if (!packages.length) {
        status.className = 'muted';
        status.textContent = 'No imported packages available.';
        document.getElementById('db-table-select').innerHTML = '';
        document.getElementById('db-table-list').innerHTML = '';
        document.getElementById('db-row-body').innerHTML = '';
        document.getElementById('db-page-status').textContent = 'Rows 0-0 of 0';
        return;
      }

      for (const pkg of packages) {
        const opt = document.createElement('option');
        opt.value = String(pkg.id);
        opt.textContent = `${pkg.package_name} (id ${pkg.id})`;
        packageSelect.appendChild(opt);
      }

      dbState.packageId = Number(packageSelect.value);
      status.className = 'ok';
      status.textContent = `Loaded ${packages.length} package(s).`;
      await loadPackageTables();
    }

    async function loadPackageTables() {
      const packageSelect = document.getElementById('db-package-select');
      const tableSelect = document.getElementById('db-table-select');
      const tableList = document.getElementById('db-table-list');
      const status = document.getElementById('db-status');
      tableSelect.innerHTML = '';
      tableList.innerHTML = '';

      const packageId = Number(packageSelect.value || '0');
      if (!packageId) {
        status.className = 'muted';
        status.textContent = 'Pick a package.';
        return;
      }

      dbState.packageId = packageId;
      dbState.tableId = null;
      dbState.offset = 0;
      dbState.total = 0;

      const response = await fetch(`/api/database/package-tables?package_id=${encodeURIComponent(packageId)}`);
      const data = await response.json();

      if (!response.ok) {
        status.className = 'err';
        status.textContent = data.error || 'Failed to load tables.';
        return;
      }

      const tables = data.tables || [];
      if (!tables.length) {
        status.className = 'muted';
        status.textContent = 'No txt tables for this package.';
        document.getElementById('db-row-body').innerHTML = '';
        document.getElementById('db-page-status').textContent = 'Rows 0-0 of 0';
        return;
      }

      for (const table of tables) {
        const opt = document.createElement('option');
        opt.value = String(table.id);
        opt.textContent = table.source_txt_name;
        opt.dataset.rowCount = String(table.row_count);
        tableSelect.appendChild(opt);

        const li = document.createElement('li');
        li.innerHTML =
          `<div><strong>${escapeHtml(table.source_txt_name)}</strong> ` +
          `<span class=\"muted\">(${table.row_count} rows)</span></div>` +
          `<code>${escapeHtml(table.table_name)}</code>`;
        tableList.appendChild(li);
      }

      dbState.tableId = Number(tableSelect.value);
      dbState.total = Number(tableSelect.selectedOptions[0]?.dataset.rowCount || '0');
      status.className = 'ok';
      status.textContent = `Loaded ${tables.length} table(s).`;
      await loadTableRows();
    }

    async function loadTableRows() {
      const body = document.getElementById('db-row-body');
      const pageStatus = document.getElementById('db-page-status');
      const prevBtn = document.getElementById('db-prev-btn');
      const nextBtn = document.getElementById('db-next-btn');

      if (!dbState.tableId) {
        body.innerHTML = '';
        pageStatus.textContent = 'Rows 0-0 of 0';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      const response = await fetch(
        `/api/database/table-rows?table_id=${encodeURIComponent(dbState.tableId)}&offset=${encodeURIComponent(dbState.offset)}&limit=${encodeURIComponent(dbState.limit)}`
      );
      const data = await response.json();
      body.innerHTML = '';

      if (!response.ok) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="2">${data.error || 'Failed to load rows.'}</td>`;
        body.appendChild(tr);
        pageStatus.textContent = 'Rows 0-0 of 0';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      const rows = data.rows || [];
      dbState.total = Number(data.total_rows || 0);
      dbState.offset = Number(data.offset || 0);
      dbState.limit = Number(data.limit || dbState.limit);

      for (const row of rows) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${row.line_number}</td><td>${escapeHtml(row.value)}</td>`;
        body.appendChild(tr);
      }

      if (!rows.length) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="2" class="muted">No rows available.</td>';
        body.appendChild(tr);
      }

      const start = dbState.total ? dbState.offset + 1 : 0;
      const end = dbState.offset + rows.length;
      pageStatus.textContent = `Rows ${start}-${end} of ${dbState.total}`;
      prevBtn.disabled = dbState.offset <= 0;
      nextBtn.disabled = (dbState.offset + dbState.limit) >= dbState.total;
    }

    function pagePrev() {
      dbState.offset = Math.max(0, dbState.offset - dbState.limit);
      loadTableRows();
    }

    function pageNext() {
      dbState.offset = dbState.offset + dbState.limit;
      loadTableRows();
    }

    document.getElementById('import-btn').addEventListener('click', importPair);
    document.getElementById('generate-btn').addEventListener('click', generateNames);
    document.getElementById('db-refresh-packages').addEventListener('click', loadPackages);
    document.getElementById('db-package-select').addEventListener('change', loadPackageTables);
    document.getElementById('db-table-select').addEventListener('change', () => {
      const tableSelect = document.getElementById('db-table-select');
      dbState.tableId = Number(tableSelect.value || '0');
      dbState.total = Number(tableSelect.selectedOptions[0]?.dataset.rowCount || '0');
      dbState.offset = 0;
      loadTableRows();
    });
    document.getElementById('db-prev-btn').addEventListener('click', pagePrev);
    document.getElementById('db-next-btn').addEventListener('click', pageNext);

    loadPackages();
  </script>
</body>
</html>
"""

SAMPLE_SYLLABLES = [
    "zor",
    "mok",
    "dra",
    "ven",
    "tal",
    "rik",
    "sul",
    "nor",
    "kai",
    "bel",
    "esh",
    "grim",
]


class WebAppHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the tabbed web UI and JSON API.

    The handler serves one static HTML page and a small set of JSON endpoints:

    - ``GET /``: Web UI shell
    - ``GET /api/health``: Liveness check
    - ``GET /api/database/packages``: Imported package list
    - ``GET /api/database/package-tables``: Table list for one package
    - ``GET /api/database/table-rows``: Paginated rows for one table
    - ``POST /api/import``: Import metadata+zip package pair
    - ``POST /api/generate``: Return placeholder generated names

    Class attributes ``verbose`` and ``db_path`` are injected at startup by
    :func:`create_handler_class`, which allows one handler implementation to be
    reused with per-process runtime settings.
    """

    verbose: bool = True
    db_path: Path = Path("pipeworks_name_generation/data/name_packages.sqlite3")

    def log_message(self, format: str, *args: Any) -> None:
        """Keep request logging optional."""
        if self.verbose:
            super().log_message(format, *args)

    def _send_text(self, content: str, status: int = 200, content_type: str = "text/plain") -> None:
        """Send a UTF-8 text response."""
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """Send a JSON response."""
        self._send_text(json.dumps(payload), status=status, content_type="application/json")

    def _read_json_body(self) -> dict[str, Any]:
        """Read request JSON body and return object payload."""
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header.") from exc

        if content_length <= 0:
            raise ValueError("Request body is required.")

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        """Handle all supported ``GET`` routes.

        Response behavior:

        - Returns ``200`` with HTML for ``/``.
        - Returns ``200`` with JSON for known API routes.
        - Returns ``204`` for ``/favicon.ico`` to avoid browser noise.
        - Returns ``404`` for unknown paths.
        """
        parsed = urlsplit(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/":
            self._send_text(HTML_TEMPLATE, content_type="text/html")
            return

        if route == "/api/health":
            self._send_json({"ok": True})
            return

        if route == "/api/database/packages":
            try:
                with _connect_database(self.db_path) as conn:
                    _initialize_schema(conn)
                    packages = _list_packages(conn)
                self._send_json({"packages": packages, "db_path": str(self.db_path)})
            except Exception as exc:  # nosec B110 - converted into controlled API response
                self._send_json({"error": f"Failed to list packages: {exc}"}, status=500)
            return

        if route == "/api/database/package-tables":
            try:
                package_id = _parse_required_int(query, "package_id", minimum=1)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return

            try:
                with _connect_database(self.db_path) as conn:
                    _initialize_schema(conn)
                    tables = _list_package_tables(conn, package_id)
                self._send_json({"tables": tables})
            except Exception as exc:  # nosec B110 - converted into controlled API response
                self._send_json({"error": f"Failed to list package tables: {exc}"}, status=500)
            return

        if route == "/api/database/table-rows":
            try:
                table_id = _parse_required_int(query, "table_id", minimum=1)
                offset = _parse_optional_int(query, "offset", default=0, minimum=0)
                limit = _parse_optional_int(
                    query,
                    "limit",
                    default=DEFAULT_PAGE_LIMIT,
                    minimum=1,
                    maximum=MAX_PAGE_LIMIT,
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return

            try:
                with _connect_database(self.db_path) as conn:
                    _initialize_schema(conn)
                    table_meta = _get_package_table(conn, table_id)
                    if table_meta is None:
                        self._send_json({"error": "Table id not found."}, status=404)
                        return

                    rows = _fetch_text_rows(
                        conn, table_meta["table_name"], offset=offset, limit=limit
                    )
                    self._send_json(
                        {
                            "table": table_meta,
                            "rows": rows,
                            "offset": offset,
                            "limit": limit,
                            "total_rows": table_meta["row_count"],
                        }
                    )
            except Exception as exc:  # nosec B110 - converted into controlled API response
                self._send_json({"error": f"Failed to load table rows: {exc}"}, status=500)
            return

        if route == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        """Handle all supported ``POST`` routes.

        Delegates to route-specific helpers so payload parsing and validation
        stay isolated from top-level route dispatch.
        """
        if self.path == "/api/import":
            self._handle_import()
            return

        if self.path == "/api/generate":
            self._handle_generation()
            return

        self.send_error(404, "Not Found")

    def _handle_import(self) -> None:
        """Import one metadata+zip pair and create tables for included txt data.

        Expected JSON payload keys:

        - ``metadata_json_path``: Filesystem path to package metadata JSON
        - ``package_zip_path``: Filesystem path to package zip archive

        Returns ``200`` with import summary JSON on success. Returns ``400`` for
        validation/input errors and ``500`` for unexpected runtime failures.
        """
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return

        metadata_raw = str(payload.get("metadata_json_path", "")).strip()
        zip_raw = str(payload.get("package_zip_path", "")).strip()
        if not metadata_raw or not zip_raw:
            self._send_json(
                {"error": "Both 'metadata_json_path' and 'package_zip_path' are required."},
                status=400,
            )
            return

        metadata_path = Path(metadata_raw).expanduser()
        zip_path = Path(zip_raw).expanduser()

        try:
            with _connect_database(self.db_path) as conn:
                _initialize_schema(conn)
                result = _import_package_pair(conn, metadata_path=metadata_path, zip_path=zip_path)
            self._send_json(result)
        except (FileNotFoundError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=400)
        except Exception as exc:  # nosec B110 - converted into controlled API response
            self._send_json({"error": f"Import failed: {exc}"}, status=500)

    def _handle_generation(self) -> None:
        """Generate a deterministic placeholder list for the Generation tab.

        Expected JSON payload keys:

        - ``name_class``: Logical class label (for deterministic variation)
        - ``count``: Requested output size (clamped to ``1..20``)
        """
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return

        name_class = str(payload.get("name_class", "first_name")).strip() or "first_name"
        raw_count = payload.get("count", 5)
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            self._send_json({"error": "Field 'count' must be an integer."}, status=400)
            return

        count = max(1, min(20, count))
        names = _generate_placeholder_names(name_class, count)
        self._send_json(
            {
                "message": f"Generated {len(names)} placeholder name(s) for {name_class}.",
                "names": names,
            }
        )


def _generate_placeholder_names(name_class: str, count: int) -> list[str]:
    """Generate deterministic placeholder names for the Generation tab."""
    names: list[str] = []
    for index in range(count):
        # Use a stable hash per position to keep output deterministic without
        # depending on pseudo-random generators.
        digest = hashlib.sha256(f"{name_class}:{index}".encode("utf-8")).digest()
        pieces = 2 + (digest[0] % 2)
        syllables = [
            SAMPLE_SYLLABLES[digest[offset] % len(SAMPLE_SYLLABLES)]
            for offset in range(1, pieces + 1)
        ]
        names.append("".join(syllables))
    return names


def _connect_database(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite and prepare runtime defaults."""
    resolved = db_path.expanduser()
    if resolved.parent and str(resolved.parent) != ".":
        resolved.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """Create metadata tables used by import and database browsing."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS imported_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            metadata_json_path TEXT NOT NULL,
            package_zip_path TEXT NOT NULL,
            UNIQUE(metadata_json_path, package_zip_path)
        );

        CREATE TABLE IF NOT EXISTS package_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL,
            source_txt_name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            row_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(package_id) REFERENCES imported_packages(id) ON DELETE CASCADE,
            UNIQUE(package_id, source_txt_name)
        );
        """)
    conn.commit()


def _import_package_pair(
    conn: sqlite3.Connection, *, metadata_path: Path, zip_path: Path
) -> dict[str, Any]:
    """Import one metadata+zip pair and create one SQLite table per ``*.txt``.

    The importer currently ignores JSON files inside the archive. It uses the
    metadata ``files_included`` list (when provided) to limit which ``*.txt``
    entries are imported. Each imported txt file becomes its own physical
    SQLite table, with one row per non-empty line.

    Args:
        conn: Open SQLite connection.
        metadata_path: Path to ``*_metadata.json`` file.
        zip_path: Path to package zip file.

    Returns:
        API-style summary payload describing imported package and created tables.

    Raises:
        FileNotFoundError: If metadata or zip path does not exist.
        ValueError: For invalid metadata, duplicate imports, or zip format/data
            issues.
    """
    metadata_resolved = metadata_path.resolve()
    zip_resolved = zip_path.resolve()

    if not metadata_resolved.exists():
        raise FileNotFoundError(f"Metadata JSON does not exist: {metadata_resolved}")
    if not zip_resolved.exists():
        raise FileNotFoundError(f"Package ZIP does not exist: {zip_resolved}")

    payload = _load_metadata_json(metadata_resolved)
    package_name = str(payload.get("common_name", "")).strip() or zip_resolved.stem

    raw_files_included = payload.get("files_included")
    if raw_files_included is None:
        files_included: list[Any] = []
    elif isinstance(raw_files_included, list):
        files_included = raw_files_included
    else:
        raise ValueError("Metadata key 'files_included' must be a list when provided.")

    allowed_txt_names = {
        str(name).strip() for name in files_included if str(name).strip().lower().endswith(".txt")
    }

    try:
        with zipfile.ZipFile(zip_resolved, "r") as archive:
            entries = sorted(
                name
                for name in archive.namelist()
                if not name.endswith("/") and name.lower().endswith(".txt")
            )

            # Restrict to metadata listed txt files when the list is present.
            if allowed_txt_names:
                entries = [entry for entry in entries if Path(entry).name in allowed_txt_names]

            cursor = conn.execute(
                """
                INSERT INTO imported_packages (
                    package_name,
                    imported_at,
                    metadata_json_path,
                    package_zip_path
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    package_name,
                    datetime.now(timezone.utc).isoformat(),
                    str(metadata_resolved),
                    str(zip_resolved),
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a row id for imported package insert.")
            package_id = int(cursor.lastrowid)

            created_tables: list[dict[str, Any]] = []
            for index, entry_name in enumerate(entries, start=1):
                txt_rows = _read_txt_rows(archive, entry_name)
                table_name = _build_package_table_name(
                    package_name, Path(entry_name).stem, package_id, index
                )
                _create_text_table(conn, table_name)
                _insert_text_rows(conn, table_name, txt_rows)

                conn.execute(
                    """
                    INSERT INTO package_tables (package_id, source_txt_name, table_name, row_count)
                    VALUES (?, ?, ?, ?)
                    """,
                    (package_id, Path(entry_name).name, table_name, len(txt_rows)),
                )
                created_tables.append(
                    {
                        "source_txt_name": Path(entry_name).name,
                        "table_name": table_name,
                        "row_count": len(txt_rows),
                    }
                )

            conn.commit()
            return {
                "message": (
                    f"Imported package '{package_name}' with {len(created_tables)} txt table(s)."
                ),
                "package_id": package_id,
                "package_name": package_name,
                "tables": created_tables,
            }
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise ValueError("This metadata/zip pair has already been imported.") from exc
    except zipfile.BadZipFile as exc:
        conn.rollback()
        raise ValueError(f"Invalid ZIP file: {zip_resolved}") from exc
    except Exception:
        conn.rollback()
        raise


def _load_metadata_json(metadata_path: Path) -> dict[str, Any]:
    """Load metadata JSON and enforce object-root structure.

    Args:
        metadata_path: Path to metadata JSON file.

    Returns:
        Parsed JSON object.

    Raises:
        ValueError: If the root JSON value is not an object.
    """
    with open(metadata_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Metadata JSON root must be an object.")
    return payload


def _read_txt_rows(archive: zipfile.ZipFile, entry_name: str) -> list[tuple[int, str]]:
    """Read one txt entry and return ``(line_number, value)`` tuples.

    Empty/whitespace-only lines are skipped during import so DB tables contain
    meaningful values only.
    """
    try:
        payload = archive.read(entry_name)
    except KeyError as exc:
        raise ValueError(f"TXT entry missing from zip: {entry_name}") from exc

    try:
        decoded = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"TXT entry is not valid UTF-8: {entry_name}") from exc

    rows: list[tuple[int, str]] = []
    for line_number, line in enumerate(decoded.splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        rows.append((line_number, text))
    return rows


def _build_package_table_name(package_name: str, txt_stem: str, package_id: int, index: int) -> str:
    """Create a safe SQLite table name that references package and txt source."""
    package_slug = _slugify_identifier(package_name, max_length=24)
    txt_slug = _slugify_identifier(txt_stem, max_length=24)
    return f"pkg_{package_id}_{package_slug}_{txt_slug}_{index}"


def _slugify_identifier(value: str, max_length: int) -> str:
    """Convert free text into an ASCII-safe SQL identifier chunk."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    slug = slug[:max_length].strip("_")
    if not slug:
        slug = "item"
    if slug[0].isdigit():
        slug = f"n_{slug}"
    return slug


def _quote_identifier(identifier: str) -> str:
    """Validate and quote a SQLite identifier."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return f'"{identifier}"'


def _create_text_table(conn: sqlite3.Connection, table_name: str) -> None:
    """Create one physical text table for imported txt rows.

    The table schema is intentionally minimal:

    - ``id``: surrogate primary key
    - ``line_number``: source txt line number
    - ``value``: trimmed non-empty line value
    """
    quoted = _quote_identifier(table_name)
    query = f"""
        CREATE TABLE IF NOT EXISTS {quoted} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_number INTEGER NOT NULL,
            value TEXT NOT NULL
        )
        """
    conn.execute(query)


def _insert_text_rows(
    conn: sqlite3.Connection, table_name: str, rows: list[tuple[int, str]]
) -> None:
    """Insert parsed txt rows into the target physical table."""
    if not rows:
        return

    quoted = _quote_identifier(table_name)
    query = f"""
        INSERT INTO {quoted} (line_number, value)
        VALUES (?, ?)
        """  # nosec B608
    conn.executemany(
        query,
        rows,
    )


def _list_packages(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return imported package list for the Database View tab."""
    rows = conn.execute("""
        SELECT id, package_name, imported_at
        FROM imported_packages
        ORDER BY id DESC
        """).fetchall()
    return [
        {
            "id": int(row["id"]),
            "package_name": str(row["package_name"]),
            "imported_at": str(row["imported_at"]),
        }
        for row in rows
    ]


def _list_package_tables(conn: sqlite3.Connection, package_id: int) -> list[dict[str, Any]]:
    """Return txt tables for one package id."""
    rows = conn.execute(
        """
        SELECT id, source_txt_name, table_name, row_count
        FROM package_tables
        WHERE package_id = ?
        ORDER BY source_txt_name
        """,
        (package_id,),
    ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "source_txt_name": str(row["source_txt_name"]),
            "table_name": str(row["table_name"]),
            "row_count": int(row["row_count"]),
        }
        for row in rows
    ]


def _get_package_table(conn: sqlite3.Connection, table_id: int) -> dict[str, Any] | None:
    """Return one package table metadata row by id."""
    row = conn.execute(
        """
        SELECT id, package_id, source_txt_name, table_name, row_count
        FROM package_tables
        WHERE id = ?
        """,
        (table_id,),
    ).fetchone()
    if row is None:
        return None

    return {
        "id": int(row["id"]),
        "package_id": int(row["package_id"]),
        "source_txt_name": str(row["source_txt_name"]),
        "table_name": str(row["table_name"]),
        "row_count": int(row["row_count"]),
    }


def _fetch_text_rows(
    conn: sqlite3.Connection,
    table_name: str,
    *,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch paginated rows from one physical txt table.

    Args:
        conn: Open SQLite connection.
        table_name: Validated physical table name.
        offset: Zero-based row offset.
        limit: Maximum rows to return.

    Returns:
        List of ``{"line_number": int, "value": str}`` mappings.
    """
    quoted = _quote_identifier(table_name)
    query = f"""
        SELECT line_number, value
        FROM {quoted}
        ORDER BY line_number, id
        LIMIT ? OFFSET ?
        """  # nosec B608
    rows = conn.execute(
        query,
        (limit, offset),
    ).fetchall()
    return [
        {
            "line_number": int(row["line_number"]),
            "value": str(row["value"]),
        }
        for row in rows
    ]


def _parse_required_int(
    query: dict[str, list[str]],
    key: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Parse a required integer query parameter."""
    values = query.get(key, [])
    if not values or not values[0].strip():
        raise ValueError(f"Missing required query parameter: {key}")
    return _coerce_int(values[0], key=key, minimum=minimum, maximum=maximum)


def _parse_optional_int(
    query: dict[str, list[str]],
    key: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Parse an optional integer query parameter."""
    values = query.get(key, [])
    if not values or not values[0].strip():
        return default
    return _coerce_int(values[0], key=key, minimum=minimum, maximum=maximum)


def _coerce_int(
    raw: str,
    *,
    key: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Convert string to bounded integer with useful error messages."""
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Query parameter '{key}' must be an integer.") from exc

    if minimum is not None and value < minimum:
        raise ValueError(f"Query parameter '{key}' must be >= {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"Query parameter '{key}' must be <= {maximum}.")
    return value


def _port_is_available(host: str, port: int) -> bool:
    """Return ``True`` when a host/port can be bound by this process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(host: str = "127.0.0.1", start: int = 8000, end: int = 8999) -> int:
    """Find the first available TCP port in ``start..end``.

    Raises:
        OSError: When no free port is available in the given range.
    """
    for port in range(start, end + 1):
        if _port_is_available(host, port):
            return port
    raise OSError(f"No free ports available in range {start}-{end}.")


def resolve_server_port(host: str, configured_port: int | None) -> int:
    """Resolve runtime port using manual config or auto-discovery.

    Args:
        host: Bind host for availability checks.
        configured_port: Optional explicit port from config/CLI.

    Returns:
        Concrete port to bind.

    Raises:
        OSError: If a configured port is unavailable or no auto port is free.
    """
    if configured_port is not None:
        if not _port_is_available(host, configured_port):
            raise OSError(f"Configured port {configured_port} is already in use.")
        return configured_port
    return find_available_port(host=host, start=8000, end=8999)


def create_handler_class(verbose: bool, db_path: Path) -> type[WebAppHandler]:
    """Create handler class bound to runtime verbosity and DB path."""

    class BoundHandler(WebAppHandler):
        pass

    BoundHandler.verbose = verbose
    BoundHandler.db_path = db_path
    return BoundHandler


def start_http_server(settings: ServerSettings) -> tuple[HTTPServer, int]:
    """Create a configured ``HTTPServer`` instance."""
    port = resolve_server_port(settings.host, settings.port)
    handler_class = create_handler_class(settings.verbose, settings.db_path)
    server = HTTPServer((settings.host, port), handler_class)
    return server, port


def run_server(settings: ServerSettings) -> int:
    """Run the server until interrupted.

    Args:
        settings: Effective runtime settings from config and CLI overrides.

    Returns:
        Process-style exit code (``0`` on normal shutdown).
    """
    server, port = start_http_server(settings)

    if settings.verbose:
        print(f"Serving Pipeworks Name Generator UI at http://{settings.host}:{port}")
        print(f"SQLite DB path: {settings.db_path}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if settings.verbose:
            print("\\nStopping server...")
    finally:
        server.server_close()

    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for this server."""
    parser = argparse.ArgumentParser(
        prog="pipeworks-name-webapp",
        description="Run the simple Pipeworks Name Generator web server.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("server.ini"),
        help="Path to INI config file (default: server.ini)",
    )
    parser.add_argument("--host", type=str, default=None, help="Override server host.")
    parser.add_argument("--port", type=int, default=None, help="Override server port.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose startup/request logs.",
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = create_argument_parser()
    return parser.parse_args(list(argv) if argv is not None else None)


def build_settings_from_args(args: argparse.Namespace) -> ServerSettings:
    """Build effective settings from INI config and CLI overrides."""
    config_path = args.config if isinstance(args.config, Path) else Path(args.config)
    loaded = load_server_settings(config_path)
    verbose_override = False if args.quiet else None
    return apply_runtime_overrides(
        loaded,
        host=args.host,
        port=args.port,
        db_path=None,
        verbose=verbose_override,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for running this server."""
    try:
        args = parse_arguments(argv)
        settings = build_settings_from_args(args)
        return run_server(settings)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
