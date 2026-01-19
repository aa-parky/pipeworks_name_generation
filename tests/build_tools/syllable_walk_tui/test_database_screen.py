"""
Tests for syllable_walk_tui database screen modal.

Tests for the DatabaseScreen and SyllableDetailModal components.
"""

import sqlite3
from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import DataTable, Label

from build_tools.syllable_walk_tui.modules.database.screen import (
    DatabaseScreen,
    SyllableDetailModal,
)


@pytest.fixture
def sample_db(tmp_path: Path) -> Path:
    """Create a sample corpus database for testing."""
    db_path: Path = tmp_path / "corpus.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create metadata table
    cursor.execute("""
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("INSERT INTO metadata VALUES ('source_tool', 'test_tool')")
    cursor.execute("INSERT INTO metadata VALUES ('generated_at', '2026-01-18T10:00:00')")

    # Create syllables table
    cursor.execute("""
        CREATE TABLE syllables (
            syllable TEXT PRIMARY KEY,
            frequency INTEGER,
            starts_with_vowel INTEGER,
            starts_with_cluster INTEGER,
            starts_with_heavy_cluster INTEGER,
            contains_plosive INTEGER,
            contains_fricative INTEGER,
            contains_liquid INTEGER,
            contains_nasal INTEGER,
            short_vowel INTEGER,
            long_vowel INTEGER,
            ends_with_vowel INTEGER,
            ends_with_nasal INTEGER,
            ends_with_stop INTEGER
        )
    """)

    # Insert test data (100 rows for pagination tests)
    for i in range(100):
        syllable = f"syl{i:03d}"
        cursor.execute(
            """INSERT INTO syllables VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                syllable,
                1000 - i,  # frequency decreasing
                1 if i % 3 == 0 else 0,  # starts_with_vowel
                1 if i % 4 == 0 else 0,  # starts_with_cluster
                1 if i % 10 == 0 else 0,  # starts_with_heavy_cluster
                1 if i % 2 == 0 else 0,  # contains_plosive
                1 if i % 5 == 0 else 0,  # contains_fricative
                1 if i % 6 == 0 else 0,  # contains_liquid
                1 if i % 7 == 0 else 0,  # contains_nasal
                1 if i % 4 == 0 else 0,  # short_vowel
                1 if i % 8 == 0 else 0,  # long_vowel
                1 if i % 3 == 0 else 0,  # ends_with_vowel
                1 if i % 9 == 0 else 0,  # ends_with_nasal
                1 if i % 11 == 0 else 0,  # ends_with_stop
            ),
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_syllable_data():
    """Create sample syllable data for detail modal tests."""
    return {
        "syllable": "test",
        "frequency": 500,
        "starts_with_vowel": False,
        "starts_with_cluster": True,
        "starts_with_heavy_cluster": False,
        "contains_plosive": True,
        "contains_fricative": False,
        "contains_liquid": True,
        "contains_nasal": False,
        "short_vowel": True,
        "long_vowel": False,
        "ends_with_vowel": False,
        "ends_with_nasal": True,
        "ends_with_stop": False,
    }


class TestDatabaseScreen:
    """Tests for DatabaseScreen modal."""

    def test_screen_initialization(self, sample_db):
        """Test that screen initializes with correct defaults."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")

        assert screen.db_path == sample_db
        assert screen.patch_name == "A"
        assert screen.current_page == 1
        assert screen.page_size == 50
        assert screen.sort_direction == "DESC"

    def test_screen_initialization_no_db(self):
        """Test screen initialization without database."""
        screen = DatabaseScreen(db_path=None, patch_name="B")

        assert screen.db_path is None
        assert screen.patch_name == "B"

    @pytest.mark.asyncio
    async def test_compose_creates_widgets(self, sample_db):
        """Test that screen creates expected widgets."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=sample_db, patch_name="A")

        async with TestApp().run_test() as pilot:
            # Check header exists with patch name
            header = pilot.app.query_one(".db-header", Label)
            assert "PATCH A" in str(header.render())

            # Check data table exists
            table = pilot.app.query_one("#db-table", DataTable)
            assert table is not None

            # Check status bar exists
            status = pilot.app.query_one("#db-status", Label)
            assert status is not None

    @pytest.mark.asyncio
    async def test_loads_data_on_mount(self, sample_db):
        """Test that data is loaded when screen is mounted."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=sample_db, patch_name="A")

        async with TestApp().run_test() as pilot:
            table = pilot.app.query_one("#db-table", DataTable)

            # Table should have rows (first page of 50)
            assert table.row_count == 50

    @pytest.mark.asyncio
    async def test_metadata_displayed(self, sample_db):
        """Test that metadata is displayed correctly."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=sample_db, patch_name="A")

        async with TestApp().run_test() as pilot:
            meta = pilot.app.query_one("#db-meta", Label)
            meta_text = str(meta.render())

            assert "test_tool" in meta_text
            assert "2026-01-18" in meta_text
            assert "100" in meta_text  # syllable count

    @pytest.mark.asyncio
    async def test_no_database_message(self, tmp_path):
        """Test that message is shown when no database."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=tmp_path / "nonexistent.db", patch_name="A")

        async with TestApp().run_test() as pilot:
            meta = pilot.app.query_one("#db-meta", Label)
            meta_text = str(meta.render())

            assert "No corpus database found" in meta_text

    @pytest.mark.asyncio
    async def test_pagination_status(self, sample_db):
        """Test that pagination status is shown correctly."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=sample_db, patch_name="A")

        async with TestApp().run_test() as pilot:
            status = pilot.app.query_one("#db-status", Label)
            status_text = str(status.render())

            # Should show page 1/2 (100 rows, 50 per page)
            assert "1/2" in status_text or "Page 1" in status_text

    @pytest.mark.asyncio
    async def test_action_close_screen(self, sample_db):
        """Test that close action works."""

        class TestApp(App):
            def compose(self):
                yield DatabaseScreen(db_path=sample_db, patch_name="A")

        async with TestApp().run_test() as pilot:
            screen = pilot.app.query_one(DatabaseScreen)
            # Just verify the action exists
            assert hasattr(screen, "action_close_screen")

    def test_sortable_columns_defined(self):
        """Test that sortable columns are properly defined."""
        assert len(DatabaseScreen.SORTABLE_COLUMNS) > 0

        # Check essential columns exist
        column_names = [col[0] for col in DatabaseScreen.SORTABLE_COLUMNS]
        assert "syllable" in column_names
        assert "frequency" in column_names

    def test_feature_details_defined(self):
        """Test that feature details mapping is defined."""
        assert len(DatabaseScreen.FEATURE_DETAILS) > 0

        # Check essential features exist
        assert "starts_with_vowel" in DatabaseScreen.FEATURE_DETAILS
        assert "contains_plosive" in DatabaseScreen.FEATURE_DETAILS
        assert "ends_with_vowel" in DatabaseScreen.FEATURE_DETAILS

    def test_bindings_defined(self):
        """Test that key bindings are defined."""
        # Extract binding keys - handles both tuple and Binding objects
        binding_keys = []
        for binding in DatabaseScreen.BINDINGS:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)  # type: ignore[union-attr]
            else:
                binding_keys.append(binding[0])

        assert "escape" in binding_keys
        assert "j" in binding_keys
        assert "k" in binding_keys
        assert "enter" in binding_keys


class TestSyllableDetailModal:
    """Tests for SyllableDetailModal."""

    def test_modal_initialization(self, sample_syllable_data):
        """Test that modal initializes with data."""
        modal = SyllableDetailModal(
            syllable_data=sample_syllable_data,
            feature_details=DatabaseScreen.FEATURE_DETAILS,
        )

        assert modal.syllable_data == sample_syllable_data
        assert modal.feature_details == DatabaseScreen.FEATURE_DETAILS

    @pytest.mark.asyncio
    async def test_compose_shows_syllable(self, sample_syllable_data):
        """Test that modal displays syllable name."""

        class TestApp(App):
            def compose(self):
                yield SyllableDetailModal(
                    syllable_data=sample_syllable_data,
                    feature_details=DatabaseScreen.FEATURE_DETAILS,
                )

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            # Should contain the syllable
            assert any('"test"' in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_compose_shows_frequency(self, sample_syllable_data):
        """Test that modal displays frequency."""

        class TestApp(App):
            def compose(self):
                yield SyllableDetailModal(
                    syllable_data=sample_syllable_data,
                    feature_details=DatabaseScreen.FEATURE_DETAILS,
                )

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            # Should contain frequency
            assert any("500" in text for text in label_texts)

    @pytest.mark.asyncio
    async def test_compose_shows_features(self, sample_syllable_data):
        """Test that modal displays feature values."""

        class TestApp(App):
            def compose(self):
                yield SyllableDetailModal(
                    syllable_data=sample_syllable_data,
                    feature_details=DatabaseScreen.FEATURE_DETAILS,
                )

        async with TestApp().run_test() as pilot:
            labels = pilot.app.query(Label)
            label_texts = [str(lbl.render()) for lbl in labels]

            # Should have Yes/No indicators
            yes_no_found = any("Yes" in text or "No" in text for text in label_texts)
            assert yes_no_found

    def test_bindings_defined(self):
        """Test that escape binding is defined for modal."""
        # Extract binding keys - handles both tuple and Binding objects
        binding_keys = []
        for binding in SyllableDetailModal.BINDINGS:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)  # type: ignore[union-attr]
            else:
                binding_keys.append(binding[0])

        assert "escape" in binding_keys
        assert "enter" in binding_keys


class TestDatabaseScreenActions:
    """Tests for DatabaseScreen action methods."""

    def test_action_next_page_increments(self, sample_db):
        """Test that next page increments current_page."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.total_pages = 5
        screen.current_page = 2

        # Mock _load_data to prevent actual DB calls
        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_next_page()

        assert screen.current_page == 3

    def test_action_next_page_stops_at_max(self, sample_db):
        """Test that next page stops at last page."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.total_pages = 5
        screen.current_page = 5

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_next_page()

        assert screen.current_page == 5  # Should not exceed

    def test_action_prev_page_decrements(self, sample_db):
        """Test that prev page decrements current_page."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.current_page = 3

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_prev_page()

        assert screen.current_page == 2

    def test_action_prev_page_stops_at_one(self, sample_db):
        """Test that prev page stops at page 1."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.current_page = 1

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_prev_page()

        assert screen.current_page == 1  # Should not go below 1

    def test_action_first_page(self, sample_db):
        """Test that first page goes to page 1."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.current_page = 3

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_first_page()

        assert screen.current_page == 1

    def test_action_last_page(self, sample_db):
        """Test that last page goes to final page."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.total_pages = 5
        screen.current_page = 1

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen.action_last_page()

        assert screen.current_page == 5

    def test_action_toggle_sort_asc_to_desc(self, sample_db):
        """Test that toggle sort changes from ASC to DESC."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_direction = "ASC"

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_toggle_sort()

        assert screen.sort_direction == "DESC"

    def test_action_toggle_sort_desc_to_asc(self, sample_db):
        """Test that toggle sort changes from DESC to ASC."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_direction = "DESC"

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_toggle_sort()

        assert screen.sort_direction == "ASC"

    def test_action_toggle_sort_resets_page(self, sample_db):
        """Test that toggle sort resets to page 1."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.current_page = 3

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_toggle_sort()

        assert screen.current_page == 1

    def test_action_next_column_cycles(self, sample_db):
        """Test that next column cycles through sortable columns."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_column_index = 0

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_next_column()

        assert screen.sort_column_index == 1

    def test_action_next_column_wraps(self, sample_db):
        """Test that next column wraps around."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_column_index = len(DatabaseScreen.SORTABLE_COLUMNS) - 1

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_next_column()

        assert screen.sort_column_index == 0

    def test_action_prev_column_cycles(self, sample_db):
        """Test that prev column cycles backwards."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_column_index = 2

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_prev_column()

        assert screen.sort_column_index == 1

    def test_action_prev_column_wraps(self, sample_db):
        """Test that prev column wraps around."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.sort_column_index = 0

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_prev_column()

        assert screen.sort_column_index == len(DatabaseScreen.SORTABLE_COLUMNS) - 1

    def test_action_column_resets_page(self, sample_db):
        """Test that column change resets to page 1."""
        screen = DatabaseScreen(db_path=sample_db, patch_name="A")
        screen.current_page = 3

        screen._load_data = lambda: None  # type: ignore[method-assign]
        screen._setup_columns = lambda: None  # type: ignore[method-assign]
        screen.action_next_column()

        assert screen.current_page == 1
