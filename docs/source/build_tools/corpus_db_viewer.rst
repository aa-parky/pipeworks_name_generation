Corpus Database Viewer
======================

.. automodule:: build_tools.corpus_db_viewer
   :no-members:

Overview
--------

The Corpus Database Viewer is an interactive terminal user interface (TUI) for inspecting
the corpus database provenance records. It provides a keyboard-driven interface for
browsing extraction run history, viewing schemas, and exporting data.

**Built with:** `Textual <https://textual.textualize.io/>`_ - A modern Python TUI framework

**Replaces:** Flask-based web viewer (archived in ``_working/_archived/pipeworks_db_viewer_flask/``)

Key Features
------------

- **Interactive table browsing** with pagination (50 rows per page)
- **Schema inspection** - View columns, types, indexes, and CREATE TABLE statements
- **Data export** - Export to CSV or JSON formats
- **Keyboard-driven navigation** - Fast, efficient terminal interface
- **Read-only access** - Safe inspection without modification risk

Quick Start
-----------

Launch the viewer with the default database:

.. code-block:: bash

   python -m build_tools.corpus_db_viewer

Specify a custom database:

.. code-block:: bash

   python -m build_tools.corpus_db_viewer --db /path/to/database.db

Command-Line Options
--------------------

.. argparse::
   :module: build_tools.corpus_db_viewer.cli
   :func: create_argument_parser
   :prog: corpus_db_viewer

Keyboard Shortcuts
------------------

Navigation
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key(s)
     - Action
   * - ``↑`` / ``↓``
     - Navigate rows
   * - ``←`` / ``→``
     - Previous/Next page
   * - ``PageUp`` / ``PageDn``
     - Jump 10 pages back/forward
   * - ``Home`` / ``End``
     - Go to first/last page

Actions
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Action
   * - ``t``
     - Switch table (focuses table selector)
   * - ``i``
     - Show schema information
   * - ``e``
     - Export current table
   * - ``r``
     - Refresh data
   * - ``?``
     - Show help screen
   * - ``q``
     - Quit application

Usage Examples
--------------

Browsing Tables
~~~~~~~~~~~~~~~

1. Launch the viewer (it automatically loads the first table)
2. Press ``t`` to focus the table list in the sidebar
3. Use ``↑``/``↓`` arrows to navigate tables
4. Press ``Enter`` to select a table

Or simply click on a table name in the sidebar.

Viewing Schema Information
~~~~~~~~~~~~~~~~~~~~~~~~~~

Press ``i`` to view detailed schema information for the current table:

- Column definitions (name, type, PRIMARY KEY, NOT NULL, DEFAULT values)
- Indexes (name, columns, UNIQUE constraints)
- CREATE TABLE statement (original SQL)

Exporting Data
~~~~~~~~~~~~~~

1. Press ``e`` to open the export modal
2. Edit the filename if desired (without extension)
3. Choose "Export CSV" or "Export JSON"
4. File is saved to the export directory (default: ``_working/exports/``)

**Note:** Export always includes ALL rows, not just the current page.

Python API
----------

Query Functions
~~~~~~~~~~~~~~~

You can use the query functions programmatically:

.. code-block:: python

   from build_tools.corpus_db_viewer import queries
   from pathlib import Path

   db_path = Path("data/raw/syllable_extractor.db")

   # Get list of tables
   tables = queries.get_tables_list(db_path)
   for table in tables:
       print(table['name'])

   # Get schema
   schema = queries.get_table_schema(db_path, "runs")
   print(f"Columns: {len(schema['columns'])}")

   # Get paginated data
   data = queries.get_table_data(
       db_path,
       "runs",
       page=1,
       limit=10,
       sort_by="run_timestamp",
       sort_order="DESC"
   )
   print(f"Total rows: {data['total']}")

Export Functions
~~~~~~~~~~~~~~~~

Export data programmatically:

.. code-block:: python

   from build_tools.corpus_db_viewer import formatters
   from pathlib import Path

   rows = [
       {'id': 1, 'name': 'Alice', 'age': 30},
       {'id': 2, 'name': 'Bob', 'age': 25}
   ]

   # Export to CSV
   formatters.export_to_csv(rows, Path("_working/exports/data.csv"))

   # Export to JSON
   formatters.export_to_json(rows, Path("_working/exports/data.json"))

   # Format helpers
   print(formatters.format_row_count(1234))  # "1,234 rows"
   print(formatters.format_file_size(1048576))  # "1.0 MB"

Database Structure
------------------

The corpus database tracks syllable extraction run provenance:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Table
     - Purpose
   * - ``runs``
     - Extraction run metadata (tool, version, status, timestamps)
   * - ``inputs``
     - Input files used in each run
   * - ``outputs``
     - Output files produced by each run

Troubleshooting
---------------

Database Not Found
~~~~~~~~~~~~~~~~~~

If you see:

.. code-block:: text

   Error: Database not found: data/raw/syllable_extractor.db

**Solution:** Ensure the database file exists, or specify a different path:

.. code-block:: bash

   python -m build_tools.corpus_db_viewer --db /path/to/your/database.db

Textual Not Installed
~~~~~~~~~~~~~~~~~~~~~

If you see:

.. code-block:: text

   Error: Textual library not found. Please install dependencies:
     pip install textual

**Solution:** Install development dependencies:

.. code-block:: bash

   pip install -r requirements-dev.txt

Terminal Too Small
~~~~~~~~~~~~~~~~~~

If the TUI layout looks broken, your terminal window may be too small.
Textual recommends a minimum of 80 columns × 24 rows. Resize your terminal
and the app will automatically reflow.

Design Philosophy
-----------------

Read-Only Access
~~~~~~~~~~~~~~~~

The viewer opens the database in **read-only mode** (``?mode=ro``) to prevent
accidental modifications. This ensures safe inspection of build provenance
without risk of corruption.

Observational Tool
~~~~~~~~~~~~~~~~~~

Like the corpus_db ledger itself, the viewer is **observational only**. It
displays what happened during extraction runs but does not control or modify
any build processes.

Benefits Over Flask Version
----------------------------

The original Flask-based viewer has been replaced by this TUI version.

**Textual TUI advantages:**

- No web server overhead (runs directly in terminal)
- Better integration with build tools ecosystem
- Simpler deployment (no HTML/CSS/JavaScript)
- Reduced dependencies (removed Flask, pandas, Werkzeug)
- Single-language codebase (Python only)
- Native keyboard navigation

**Flask version advantages:**

- SQL query interface (custom SELECT queries)
- Search across all tables
- Browser-based (familiar UI paradigm)

**Decision:** The TUI better matches the "build tool" philosophy and reduces
complexity. The SQL query interface and search features may be added in future
if requested.

Related Documentation
---------------------

- :doc:`corpus_db` - Build provenance ledger
- :doc:`syllable_extractor` - The tool that populates the database
