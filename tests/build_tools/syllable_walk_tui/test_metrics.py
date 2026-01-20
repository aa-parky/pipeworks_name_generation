"""
Tests for corpus shape metrics computation.

Tests the metrics module which computes raw, objective statistics
about corpus shape (inventory, frequency, feature saturation).
"""

import random

import pytest

from build_tools.syllable_walk_tui.services.metrics import (
    FEATURE_NAMES,
    FeatureSaturation,
    FeatureSaturationMetrics,
    FrequencyMetrics,
    InventoryMetrics,
    PoleExemplars,
    compute_corpus_shape_metrics,
    compute_feature_saturation_metrics,
    compute_frequency_metrics,
    compute_inventory_metrics,
    sample_pole_exemplars,
    score_syllable_on_axis,
)
from build_tools.syllable_walk_tui.services.terrain_weights import AxisWeights

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_syllables():
    """Sample syllable list for testing."""
    return ["ka", "ki", "ta", "ti", "na", "ni", "ra", "ri", "sa", "si"]


@pytest.fixture
def sample_frequencies():
    """Sample frequency dict with varied distribution."""
    return {
        "ka": 100,
        "ki": 50,
        "ta": 30,
        "ti": 20,
        "na": 10,
        "ni": 5,
        "ra": 3,
        "ri": 2,
        "sa": 1,
        "si": 1,
    }


@pytest.fixture
def sample_annotated_data():
    """Sample annotated data with phonetic features."""
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
            "syllable": "aa",
            "frequency": 50,
            "features": {
                "starts_with_vowel": True,
                "starts_with_cluster": False,
                "starts_with_heavy_cluster": False,
                "contains_plosive": False,
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
            "syllable": "kran",
            "frequency": 10,
            "features": {
                "starts_with_vowel": False,
                "starts_with_cluster": True,
                "starts_with_heavy_cluster": False,
                "contains_plosive": True,
                "contains_fricative": False,
                "contains_liquid": True,
                "contains_nasal": True,
                "short_vowel": True,
                "long_vowel": False,
                "ends_with_vowel": False,
                "ends_with_nasal": True,
                "ends_with_stop": False,
            },
        },
    ]


# =============================================================================
# InventoryMetrics Tests
# =============================================================================


class TestInventoryMetrics:
    """Tests for inventory metrics computation."""

    def test_basic_computation(self, sample_syllables):
        """Test basic inventory metrics are computed correctly."""
        metrics = compute_inventory_metrics(sample_syllables)

        assert metrics.total_count == 10
        assert metrics.length_min == 2
        assert metrics.length_max == 2
        assert metrics.length_mean == 2.0
        assert metrics.length_median == 2.0

    def test_length_distribution(self, sample_syllables):
        """Test length distribution is computed correctly."""
        metrics = compute_inventory_metrics(sample_syllables)

        # All syllables are length 2
        assert metrics.length_distribution == {2: 10}

    def test_varied_lengths(self):
        """Test with syllables of varied lengths."""
        syllables = ["a", "ka", "kra", "kran", "strax"]
        metrics = compute_inventory_metrics(syllables)

        assert metrics.total_count == 5
        assert metrics.length_min == 1
        assert metrics.length_max == 5
        assert metrics.length_distribution == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}

    def test_empty_list_raises_error(self):
        """Test that empty syllable list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compute_inventory_metrics([])

    def test_single_syllable(self):
        """Test with single syllable (edge case for stdev)."""
        metrics = compute_inventory_metrics(["test"])

        assert metrics.total_count == 1
        assert metrics.length_min == 4
        assert metrics.length_max == 4
        assert metrics.length_std == 0.0  # Single value, no variance

    def test_dataclass_is_frozen(self, sample_syllables):
        """Test that InventoryMetrics is immutable."""
        metrics = compute_inventory_metrics(sample_syllables)

        with pytest.raises(Exception):  # FrozenInstanceError
            metrics.total_count = 999  # type: ignore[misc]


# =============================================================================
# FrequencyMetrics Tests
# =============================================================================


class TestFrequencyMetrics:
    """Tests for frequency distribution metrics computation."""

    def test_basic_computation(self, sample_frequencies):
        """Test basic frequency metrics are computed correctly."""
        metrics = compute_frequency_metrics(sample_frequencies)

        assert metrics.total_occurrences == 222
        assert metrics.freq_min == 1
        assert metrics.freq_max == 100
        assert metrics.unique_freq_count == 9  # 100,50,30,20,10,5,3,2,1

    def test_hapax_count(self, sample_frequencies):
        """Test hapax legomena count (frequency=1)."""
        metrics = compute_frequency_metrics(sample_frequencies)

        # "sa" and "si" both have frequency 1
        assert metrics.hapax_count == 2

    def test_top_10(self, sample_frequencies):
        """Test top 10 syllables by frequency."""
        metrics = compute_frequency_metrics(sample_frequencies)

        # First should be highest frequency
        assert metrics.top_10[0] == ("ka", 100)
        assert metrics.top_10[1] == ("ki", 50)

    def test_bottom_10(self, sample_frequencies):
        """Test bottom 10 syllables by frequency."""
        metrics = compute_frequency_metrics(sample_frequencies)

        # First in bottom should be lowest frequency
        assert metrics.bottom_10[0][1] == 1  # Lowest frequency

    def test_percentiles(self, sample_frequencies):
        """Test that percentiles are computed."""
        metrics = compute_frequency_metrics(sample_frequencies)

        # Just verify they exist and are integers
        assert isinstance(metrics.percentile_10, int)
        assert isinstance(metrics.percentile_25, int)
        assert isinstance(metrics.percentile_50, int)
        assert isinstance(metrics.percentile_75, int)
        assert isinstance(metrics.percentile_90, int)
        assert isinstance(metrics.percentile_99, int)

        # Percentiles should be non-decreasing
        assert metrics.percentile_10 <= metrics.percentile_25
        assert metrics.percentile_25 <= metrics.percentile_50
        assert metrics.percentile_50 <= metrics.percentile_75
        assert metrics.percentile_75 <= metrics.percentile_90
        assert metrics.percentile_90 <= metrics.percentile_99

    def test_empty_dict_raises_error(self):
        """Test that empty frequencies dict raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compute_frequency_metrics({})

    def test_single_entry(self):
        """Test with single entry (edge case for stdev)."""
        metrics = compute_frequency_metrics({"test": 42})

        assert metrics.total_occurrences == 42
        assert metrics.freq_min == 42
        assert metrics.freq_max == 42
        assert metrics.freq_std == 0.0
        assert metrics.hapax_count == 0

    def test_all_hapax(self):
        """Test corpus where all syllables appear exactly once."""
        frequencies = {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}
        metrics = compute_frequency_metrics(frequencies)

        assert metrics.hapax_count == 5
        assert metrics.unique_freq_count == 1

    def test_dataclass_is_frozen(self, sample_frequencies):
        """Test that FrequencyMetrics is immutable."""
        metrics = compute_frequency_metrics(sample_frequencies)

        with pytest.raises(Exception):
            metrics.total_occurrences = 999  # type: ignore[misc]


# =============================================================================
# FeatureSaturationMetrics Tests
# =============================================================================


class TestFeatureSaturationMetrics:
    """Tests for feature saturation metrics computation."""

    def test_basic_computation(self, sample_annotated_data):
        """Test basic feature saturation metrics."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        assert metrics.total_syllables == 3

    def test_all_features_present(self, sample_annotated_data):
        """Test that all 12 features are computed."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        assert len(metrics.features) == 12
        assert len(metrics.by_name) == 12

        for name in FEATURE_NAMES:
            assert name in metrics.by_name

    def test_feature_counts(self, sample_annotated_data):
        """Test specific feature counts from sample data."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        # starts_with_vowel: only "aa" has it
        swv = metrics.by_name["starts_with_vowel"]
        assert swv.true_count == 1
        assert swv.false_count == 2

        # contains_plosive: "ka" and "kran" have it
        cp = metrics.by_name["contains_plosive"]
        assert cp.true_count == 2
        assert cp.false_count == 1

        # ends_with_vowel: "ka" and "aa" have it
        ewv = metrics.by_name["ends_with_vowel"]
        assert ewv.true_count == 2
        assert ewv.false_count == 1

    def test_percentage_calculation(self, sample_annotated_data):
        """Test that percentages are calculated correctly."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        # 1 out of 3 = 33.33...%
        swv = metrics.by_name["starts_with_vowel"]
        assert abs(swv.true_percentage - 33.333) < 0.01

        # 2 out of 3 = 66.66...%
        cp = metrics.by_name["contains_plosive"]
        assert abs(cp.true_percentage - 66.666) < 0.01

    def test_feature_order_matches_canonical(self, sample_annotated_data):
        """Test that features tuple maintains canonical order."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        for i, feat in enumerate(metrics.features):
            assert feat.feature_name == FEATURE_NAMES[i]

    def test_empty_data_raises_error(self):
        """Test that empty annotated data raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compute_feature_saturation_metrics([])

    def test_missing_features_key_raises_error(self):
        """Test that missing features key raises ValueError."""
        bad_data = [{"syllable": "test", "frequency": 1}]

        with pytest.raises(ValueError, match="features"):
            compute_feature_saturation_metrics(bad_data)

    def test_all_true_features(self):
        """Test corpus where all features are True."""
        data = [
            {
                "syllable": "test",
                "frequency": 1,
                "features": {name: True for name in FEATURE_NAMES},
            }
        ]
        metrics = compute_feature_saturation_metrics(data)

        for feat in metrics.features:
            assert feat.true_count == 1
            assert feat.false_count == 0
            assert feat.true_percentage == 100.0

    def test_all_false_features(self):
        """Test corpus where all features are False."""
        data = [
            {
                "syllable": "test",
                "frequency": 1,
                "features": {name: False for name in FEATURE_NAMES},
            }
        ]
        metrics = compute_feature_saturation_metrics(data)

        for feat in metrics.features:
            assert feat.true_count == 0
            assert feat.false_count == 1
            assert feat.true_percentage == 0.0

    def test_dataclass_is_frozen(self, sample_annotated_data):
        """Test that FeatureSaturationMetrics is immutable."""
        metrics = compute_feature_saturation_metrics(sample_annotated_data)

        with pytest.raises(Exception):
            metrics.total_syllables = 999  # type: ignore[misc]


# =============================================================================
# CorpusShapeMetrics Tests (Composite)
# =============================================================================


class TestCorpusShapeMetrics:
    """Tests for composite corpus shape metrics."""

    def test_composite_computation(
        self, sample_syllables, sample_frequencies, sample_annotated_data
    ):
        """Test that composite metrics includes all categories."""
        metrics = compute_corpus_shape_metrics(
            sample_syllables, sample_frequencies, sample_annotated_data
        )

        assert isinstance(metrics.inventory, InventoryMetrics)
        assert isinstance(metrics.frequency, FrequencyMetrics)
        assert isinstance(metrics.feature_saturation, FeatureSaturationMetrics)

    def test_inventory_accessible(
        self, sample_syllables, sample_frequencies, sample_annotated_data
    ):
        """Test that inventory metrics are accessible through composite."""
        metrics = compute_corpus_shape_metrics(
            sample_syllables, sample_frequencies, sample_annotated_data
        )

        assert metrics.inventory.total_count == 10

    def test_frequency_accessible(
        self, sample_syllables, sample_frequencies, sample_annotated_data
    ):
        """Test that frequency metrics are accessible through composite."""
        metrics = compute_corpus_shape_metrics(
            sample_syllables, sample_frequencies, sample_annotated_data
        )

        assert metrics.frequency.total_occurrences == 222

    def test_feature_saturation_accessible(
        self, sample_syllables, sample_frequencies, sample_annotated_data
    ):
        """Test that feature saturation is accessible through composite."""
        metrics = compute_corpus_shape_metrics(
            sample_syllables, sample_frequencies, sample_annotated_data
        )

        assert metrics.feature_saturation.total_syllables == 3

    def test_dataclass_is_frozen(self, sample_syllables, sample_frequencies, sample_annotated_data):
        """Test that CorpusShapeMetrics is immutable."""
        metrics = compute_corpus_shape_metrics(
            sample_syllables, sample_frequencies, sample_annotated_data
        )

        with pytest.raises(Exception):
            metrics.inventory = None  # type: ignore[misc, assignment]


# =============================================================================
# FeatureSaturation Dataclass Tests
# =============================================================================


class TestFeatureSaturationDataclass:
    """Tests for the FeatureSaturation dataclass itself."""

    def test_creation(self):
        """Test FeatureSaturation can be created."""
        fs = FeatureSaturation(
            feature_name="test_feature",
            true_count=75,
            false_count=25,
            true_percentage=75.0,
        )

        assert fs.feature_name == "test_feature"
        assert fs.true_count == 75
        assert fs.false_count == 25
        assert fs.true_percentage == 75.0

    def test_immutability(self):
        """Test FeatureSaturation is frozen."""
        fs = FeatureSaturation(
            feature_name="test", true_count=1, false_count=0, true_percentage=100.0
        )

        with pytest.raises(Exception):
            fs.true_count = 999  # type: ignore[misc]


# =============================================================================
# FEATURE_NAMES Tests
# =============================================================================


class TestFeatureNames:
    """Tests for the FEATURE_NAMES constant."""

    def test_contains_12_features(self):
        """Test FEATURE_NAMES has exactly 12 features."""
        assert len(FEATURE_NAMES) == 12

    def test_is_tuple(self):
        """Test FEATURE_NAMES is immutable tuple."""
        assert isinstance(FEATURE_NAMES, tuple)

    def test_expected_features_present(self):
        """Test that expected feature names are present."""
        expected = {
            "starts_with_vowel",
            "starts_with_cluster",
            "starts_with_heavy_cluster",
            "contains_plosive",
            "contains_fricative",
            "contains_liquid",
            "contains_nasal",
            "short_vowel",
            "long_vowel",
            "ends_with_vowel",
            "ends_with_nasal",
            "ends_with_stop",
        }

        assert set(FEATURE_NAMES) == expected


# =============================================================================
# Syllable Scoring Tests
# =============================================================================


class TestScoreSyllableOnAxis:
    """Tests for score_syllable_on_axis function."""

    def test_score_all_positive_features(self):
        """Syllable with all positive-weight features scores high."""
        features = {"contains_plosive": True, "ends_with_stop": True}
        weights = AxisWeights({"contains_plosive": 0.6, "ends_with_stop": 1.0})
        score = score_syllable_on_axis(features, weights)
        assert score == pytest.approx(1.6)

    def test_score_mixed_features(self):
        """Mixed features produce intermediate score."""
        features = {"contains_liquid": True, "contains_plosive": True}
        weights = AxisWeights({"contains_liquid": -0.8, "contains_plosive": 0.6})
        score = score_syllable_on_axis(features, weights)
        assert score == pytest.approx(-0.2)

    def test_score_no_matching_features(self):
        """No matching features produces zero score."""
        features = {"unknown_feature": True}
        weights = AxisWeights({"contains_plosive": 0.6})
        score = score_syllable_on_axis(features, weights)
        assert score == 0.0

    def test_score_false_features_not_counted(self):
        """Features with False values are not counted."""
        features = {"contains_plosive": False, "ends_with_stop": True}
        weights = AxisWeights({"contains_plosive": 0.6, "ends_with_stop": 1.0})
        score = score_syllable_on_axis(features, weights)
        assert score == pytest.approx(1.0)

    def test_score_empty_features(self):
        """Empty features dict produces zero score."""
        features: dict[str, bool] = {}
        weights = AxisWeights({"contains_plosive": 0.6})
        score = score_syllable_on_axis(features, weights)
        assert score == 0.0

    def test_score_empty_weights(self):
        """Empty weights produces zero score."""
        features = {"contains_plosive": True}
        weights = AxisWeights({})
        score = score_syllable_on_axis(features, weights)
        assert score == 0.0


# =============================================================================
# PoleExemplars Tests
# =============================================================================


class TestPoleExemplars:
    """Tests for PoleExemplars dataclass."""

    def test_creation(self):
        """Test PoleExemplars can be created."""
        exemplars = PoleExemplars(
            axis_name="shape",
            low_pole_exemplars=("mala", "luno"),
            high_pole_exemplars=("krask", "thrix"),
        )
        assert exemplars.axis_name == "shape"
        assert exemplars.low_pole_exemplars == ("mala", "luno")
        assert exemplars.high_pole_exemplars == ("krask", "thrix")

    def test_immutability(self):
        """Test PoleExemplars is frozen."""
        exemplars = PoleExemplars(
            axis_name="shape",
            low_pole_exemplars=("aa",),
            high_pole_exemplars=("kk",),
        )
        with pytest.raises(Exception):
            exemplars.axis_name = "craft"  # type: ignore[misc]

    def test_empty_tuples(self):
        """Test PoleExemplars can have empty tuples."""
        exemplars = PoleExemplars(
            axis_name="test",
            low_pole_exemplars=(),
            high_pole_exemplars=(),
        )
        assert exemplars.low_pole_exemplars == ()
        assert exemplars.high_pole_exemplars == ()


# =============================================================================
# Sample Pole Exemplars Tests
# =============================================================================


class TestSamplePoleExemplars:
    """Tests for sample_pole_exemplars function."""

    @pytest.fixture
    def sample_corpus_data(self):
        """Sample corpus data with varied features for testing exemplars."""
        return [
            # Low pole syllables (negative features)
            {"syllable": "aa", "features": {"ends_with_vowel": True, "contains_liquid": True}},
            {"syllable": "io", "features": {"ends_with_vowel": True, "contains_liquid": True}},
            {"syllable": "mala", "features": {"ends_with_vowel": True, "contains_liquid": True}},
            # Middle syllables
            {"syllable": "mid", "features": {"contains_plosive": True, "contains_liquid": True}},
            {"syllable": "bal", "features": {"contains_plosive": True, "ends_with_vowel": True}},
            # High pole syllables (positive features)
            {"syllable": "krask", "features": {"contains_plosive": True, "ends_with_stop": True}},
            {"syllable": "thrix", "features": {"contains_plosive": True, "ends_with_stop": True}},
            {"syllable": "strunk", "features": {"contains_plosive": True, "ends_with_stop": True}},
        ]

    def test_sample_basic(self, sample_corpus_data):
        """Basic sampling returns correct structure."""
        weights = AxisWeights(
            {
                "ends_with_vowel": -1.0,
                "contains_liquid": -0.5,
                "contains_plosive": 0.6,
                "ends_with_stop": 1.0,
            }
        )
        exemplars = sample_pole_exemplars(sample_corpus_data, weights, "shape", n_exemplars=2)

        assert exemplars.axis_name == "shape"
        assert len(exemplars.low_pole_exemplars) == 2
        assert len(exemplars.high_pole_exemplars) == 2

        # Low pole should have vowel-ending syllables
        for syl in exemplars.low_pole_exemplars:
            assert syl in ("aa", "io", "mala")

        # High pole should have stop-ending syllables
        for syl in exemplars.high_pole_exemplars:
            assert syl in ("krask", "thrix", "strunk")

    def test_deterministic_without_rng(self, sample_corpus_data):
        """Same input produces same output without RNG."""
        weights = AxisWeights({"ends_with_vowel": -1.0, "ends_with_stop": 1.0})

        result1 = sample_pole_exemplars(sample_corpus_data, weights, "test", n_exemplars=2)
        result2 = sample_pole_exemplars(sample_corpus_data, weights, "test", n_exemplars=2)

        assert result1.low_pole_exemplars == result2.low_pole_exemplars
        assert result1.high_pole_exemplars == result2.high_pole_exemplars

    def test_rng_provides_variety(self, sample_corpus_data):
        """RNG shuffles exemplars for variety."""
        weights = AxisWeights({"ends_with_vowel": -1.0, "ends_with_stop": 1.0})

        # With different RNG seeds, should sometimes get different results
        results = set()
        for seed in range(100):
            rng = random.Random(seed)
            result = sample_pole_exemplars(
                sample_corpus_data, weights, "test", n_exemplars=2, rng=rng
            )
            results.add(result.low_pole_exemplars)

        # Should have more than one unique result due to shuffling
        assert len(results) > 1

    def test_empty_data(self):
        """Empty data returns empty exemplars."""
        weights = AxisWeights({"contains_plosive": 1.0})
        exemplars = sample_pole_exemplars([], weights, "test", n_exemplars=3)

        assert exemplars.axis_name == "test"
        assert exemplars.low_pole_exemplars == ()
        assert exemplars.high_pole_exemplars == ()

    def test_thin_corpus_handled(self):
        """Gracefully handles corpora with few syllables."""
        data = [{"syllable": "only", "features": {}}]
        weights = AxisWeights({"contains_plosive": 1.0})
        exemplars = sample_pole_exemplars(data, weights, "test", n_exemplars=3)

        # Should return what's available
        assert len(exemplars.low_pole_exemplars) == 1
        assert len(exemplars.high_pole_exemplars) == 1

    def test_single_exemplar_requested(self, sample_corpus_data):
        """Can request just one exemplar per pole."""
        weights = AxisWeights({"ends_with_vowel": -1.0, "ends_with_stop": 1.0})
        exemplars = sample_pole_exemplars(sample_corpus_data, weights, "test", n_exemplars=1)

        assert len(exemplars.low_pole_exemplars) == 1
        assert len(exemplars.high_pole_exemplars) == 1

    def test_all_features_false(self):
        """Handles data where all features are False."""
        data = [
            {"syllable": "a", "features": {}},
            {"syllable": "b", "features": {}},
            {"syllable": "c", "features": {}},
        ]
        weights = AxisWeights({"contains_plosive": 1.0})
        exemplars = sample_pole_exemplars(data, weights, "test", n_exemplars=2)

        # All should score 0, so order is by original sort stability
        assert len(exemplars.low_pole_exemplars) == 2
        assert len(exemplars.high_pole_exemplars) == 2
