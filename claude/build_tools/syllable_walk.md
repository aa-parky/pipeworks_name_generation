# Syllable Walker

A phonetic exploration tool that generates sequences of syllables by "walking" through phonetic
feature space using cost-based random selection. Designed for analyzing corpus structure,
understanding phonetic relationships, and exploring potential name generation patterns.

## Overview

The Syllable Walker explores syllable datasets by moving probabilistically from one syllable to
phonetically similar syllables. Each step considers:

- **Phonetic distance**: How many features change (Hamming distance)
- **Frequency bias**: Preference for common vs rare syllables
- **Temperature**: Amount of randomness in selection
- **Inertia**: Tendency to stay at the current syllable

This tool is a **build-time analysis tool** for exploring phonetic space, not a runtime component
of the name generator.

## Quick Start

### Interactive Web Interface (Recommended)

The easiest way to explore syllable walks is through the web interface:

```bash
# Start the web server (default port 5000)
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json --web

# Open http://localhost:5000 in your browser
```

The web interface provides:

- Real-time walk generation
- All four profiles + custom parameters
- Visual walk display with syllable details
- No command-line complexity

### Command-Line Usage

```bash
# Generate a single walk with default profile (dialect)
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json --start ka

# Use a specific profile
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --start bak --profile goblin --steps 10

# Compare all profiles from the same starting point
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --start ka --compare-profiles

# Generate 100 walks for statistical analysis
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --batch 100 --profile ritual --output walks.json

# Search for valid starting syllables
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --search "th"
```

## Walk Profiles

The walker includes four pre-configured profiles representing different exploration strategies:

| Profile | Description | Steps | Max Flips | Temperature | Freq Weight | Use Case |
|---------|-------------|-------|-----------|-------------|-------------|----------|
| **clerical** | Conservative, minimal change | 5 | 1 | 0.3 | 1.0 | Formal names, low variation |
| **dialect** | Balanced exploration | 5 | 2 | 0.7 | 0.0 | General exploration, neutral |
| **goblin** | Chaotic, high variation | 5 | 2 | 1.5 | -0.5 | Exotic names, rare syllables |
| **ritual** | Maximum exploration | 5 | 3 | 2.5 | -1.0 | Extreme variation, discovery |

### Profile Details

#### Clerical

- Favors common syllables (freq weight: 1.0)
- Minimal phonetic changes (max flips: 1)
- Low randomness (temperature: 0.3)
- Good for: Conservative, pronounceable names

#### Dialect

- Neutral frequency bias (freq weight: 0.0)
- Moderate phonetic changes (max flips: 2)
- Balanced randomness (temperature: 0.7)
- Good for: General exploration, typical patterns

#### Goblin

- Favors rare syllables (freq weight: -0.5)
- Moderate phonetic changes (max flips: 2)
- High randomness (temperature: 1.5)
- Good for: Unusual combinations, exotic patterns

#### Ritual

- Strongly favors rare syllables (freq weight: -1.0)
- Maximum phonetic changes (max flips: 3)
- Very high randomness (temperature: 2.5)
- Good for: Extreme exploration, discovering edge cases

## Core Concepts

### Phonetic Distance (Hamming Distance)

Each syllable has 12 binary phonetic features (from `syllable_feature_annotator`). The distance
between two syllables is the number of features that differ:

```text
ka:    [0,0,0,1,0,0,0,1,0,1,0,0]
pai:   [0,0,0,1,0,0,0,0,1,1,0,0]
       ─────────────────↑─────── 1 feature differs
Distance = 1 (very similar)
```

The `max_flips` parameter limits how many features can change in a single step.

### Neighbor Graph

During initialization, the walker pre-computes which syllables are "neighbors" (within the
specified Hamming distance). This enables fast walk generation at the cost of initialization time:

- **Distance 1**: ~30 sec initialization, very conservative walks
- **Distance 2**: ~1 min initialization, moderate walks
- **Distance 3**: ~3 min initialization, maximum flexibility

For 500k+ syllable datasets, distance 3 is recommended for maximum exploration capability.

### Cost Function

Each potential step has a cost based on:

1. **Hamming distance**: How many features change
2. **Feature-specific costs**: Some features cost more to change (configurable)
3. **Frequency weight**: Bias toward common (positive) or rare (negative) syllables
4. **Inertia**: Tendency to stay at the current syllable

The walker uses softmax selection with temperature to probabilistically choose the next syllable.

### Determinism

**Critical**: The same seed always produces the same walk. This is essential for:

- Reproducible experiments
- Testing and validation
- Debugging exploration strategies

```bash
# Same seed = same walk
python -m build_tools.syllable_walk data.json --start ka --seed 42
# Always produces the same sequence
```

## Common Use Cases

### 1. Understanding Corpus Structure

Generate many walks to see how syllables connect:

```bash
python -m build_tools.syllable_walk data.json --batch 100 --output corpus_walks.json
```

Analyze the JSON output to understand:

- Which syllables are central hubs
- Which syllables are isolated
- Common phonetic pathways
- Rare syllable accessibility

### 2. Testing Pattern Viability

Before creating a new name generation pattern, explore if the desired phonetic transitions exist:

```bash
# Can we get from common to rare syllables smoothly?
python -m build_tools.syllable_walk data.json --start the --profile ritual
```

### 3. Finding Interesting Syllable Sequences

Discover unusual but valid phonetic progressions:

```bash
# Explore with goblin profile for exotic combinations
python -m build_tools.syllable_walk data.json --profile goblin --steps 10
```

### 4. Validating Feature Annotations

Ensure the feature annotator correctly captures phonetic relationships:

```bash
# Compare profiles to verify feature distances work as expected
python -m build_tools.syllable_walk data.json --start ka --compare-profiles
```

### 5. Statistical Analysis

Generate large walk datasets for analysis:

```bash
# 1000 walks with different profiles
python -m build_tools.syllable_walk data.json --batch 1000 \
  --profile dialect --output dialect_walks.json
python -m build_tools.syllable_walk data.json --batch 1000 \
  --profile goblin --output goblin_walks.json

# Analyze frequency distributions, transition patterns, etc.
```

## Command-Line Options

For detailed documentation of all CLI options, see the auto-generated
[CLI Reference](../docs/source/cli/syllable_walk.rst).

### Key Options

**Walk Parameters**:

- `--start SYLLABLE` - Starting syllable (default: random)
- `--profile NAME` - Use predefined profile (clerical/dialect/goblin/ritual)
- `--steps N` - Number of steps in walk (default: 5)
- `--seed N` - Random seed for reproducibility

**Custom Parameters** (override profile):

- `--max-flips N` - Maximum feature changes per step (1-3)
- `--temperature T` - Exploration randomness (0.1-5.0)
- `--frequency-weight W` - Common/rare bias (-2.0 to 2.0)

**Operation Modes**:

- `--compare-profiles` - Compare all profiles from same start
- `--batch N` - Generate N walks for analysis
- `--search QUERY` - Find syllables matching query
- `--web` - Start interactive web interface

**Output Control**:

- `--output FILE` - Save results to JSON file
- `--quiet` - Suppress progress messages
- `--verbose` - Show detailed initialization info

**Configuration**:

- `--max-neighbor-distance N` - Neighbor graph distance (1-3)
- `--port PORT` - Web server port (default: 5000)

## Web Interface

The web interface provides an intuitive way to explore syllable walks without command-line
complexity.

### Starting the Server

```bash
# Default port (5000)
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json --web

# Custom port
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --web --port 8000

# Quiet mode (suppress initialization output)
python -m build_tools.syllable_walk data/annotated/syllables_annotated.json \
  --web --quiet
```

### Features

- **Profile Selection**: Choose from four profiles or use custom parameters
- **Starting Syllable**: Specify a starting point or let the system choose randomly
- **Real-time Generation**: Walks generated instantly with visual feedback
- **Walk Display**: See the full walk path and syllable details with frequencies
- **Statistics**: Track total syllables and walks generated
- **Reproducible**: Optionally specify a seed for deterministic walks

### Architecture

The web server uses Python's standard library `http.server` (no Flask dependency), maintaining
the project's zero-runtime-dependency philosophy. All HTML and CSS are embedded in the Python
package.

## Algorithm Details

### Initialization

1. Load syllable data (syllable, frequency, 12-feature vector)
2. Build syllable index and frequency normalization
3. Construct neighbor graph (pre-compute valid transitions)
   - For each syllable, find all syllables within `max_neighbor_distance`
   - Store as sparse adjacency list
   - Memory: ~50MB (dist 1), ~150MB (dist 2), ~300MB (dist 3) for 500k syllables

### Walk Generation

For each step:

1. Get neighbors of current syllable (from pre-computed graph)
2. Filter neighbors by `max_flips` constraint
3. Calculate cost for each valid neighbor:
   - Base cost: Hamming distance × feature costs
   - Frequency adjustment: Apply `frequency_weight` bias
   - Inertia: Add cost to stay at current position
4. Apply softmax with `temperature` to convert costs to probabilities
5. Sample next syllable using seeded RNG (deterministic)
6. Repeat for `steps` iterations

### Cost Function Math

```text
For each neighbor n:
  hamming_cost = sum(feature_costs[i] for i where features differ)
  freq_cost = frequency_weight × log(frequency[n])
  total_cost = hamming_cost + freq_cost + inertia_cost

Probability of selecting n:
  P(n) = exp(-cost(n) / temperature) / sum(exp(-cost(k) / temperature))
```

Higher temperature = more random selection (flattens probability distribution).
Lower temperature = more deterministic (strongly favors lowest cost).

## Performance Characteristics

### Initialization Time (500k syllables)

| Max Neighbor Distance | Time | Memory | Max Flips Supported |
|----------------------|------|--------|---------------------|
| 1 | ~30 seconds | ~50 MB | 1 |
| 2 | ~1 minute | ~150 MB | 1-2 |
| 3 | ~3 minutes | ~300 MB | 1-3 |

Recommendation: Use distance 3 for maximum flexibility unless initialization time is critical.

### Walk Generation Performance

- **After initialization**: <10ms per walk (instant)
- **Deterministic**: Same seed always produces same walk
- **Scalable**: Walk generation speed independent of corpus size

### Memory Usage

Memory scales with corpus size and neighbor graph density:

- Small corpus (10k syllables): <10 MB
- Medium corpus (100k syllables): ~50 MB
- Large corpus (500k syllables): ~300 MB (dist 3)

## Output Format

### Single Walk Output

```json
{
  "walk": [
    {
      "syllable": "ka",
      "frequency": 20,
      "features": [0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0]
    },
    {
      "syllable": "pai",
      "frequency": 9,
      "features": [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0]
    }
  ],
  "profile": "dialect",
  "start": "ka",
  "seed": 42
}
```

### Batch Output

```json
{
  "walks": [
    {
      "walk": [...],
      "start": "ka",
      "seed": 42
    },
    {
      "walk": [...],
      "start": "bak",
      "seed": 43
    }
  ],
  "profile": "dialect",
  "parameters": {
    "steps": 5,
    "max_flips": 2,
    "temperature": 0.7,
    "frequency_weight": 0.0
  }
}
```

## Integration with Main Package (Future)

The Syllable Walker is currently a **build-time analysis tool**. Potential future integrations:

### 1. Walk-Based Name Generation

Use walks as a pattern generation strategy:

- Start from a seed syllable
- Walk N steps to generate a name
- Different profiles = different name styles

### 2. Pattern Discovery

Analyze walk data to discover common phonetic patterns:

- Extract frequent transition sequences
- Identify stable vs volatile syllable clusters
- Inform pattern development for `data/patterns/`

### 3. Corpus Quality Metrics

Use walks to measure corpus properties:

- **Connectivity**: Can we reach most syllables?
- **Diversity**: How many unique paths exist?
- **Clustering**: Are there isolated syllable groups?

### 4. Interactive Name Refinement

For applications with UI:

- User starts with a name
- Walk from each syllable to find variations
- User steers walk direction interactively

## Troubleshooting

### Initialization Takes Forever

- Reduce `--max-neighbor-distance` (default 3 → try 2)
- Use smaller corpus for testing
- Initialization is one-time cost, walk generation is instant

### Getting Stuck at One Syllable

- Increase `--max-flips` (allow bigger phonetic jumps)
- Increase `--temperature` (more randomness)
- Check if starting syllable is isolated (use `--search` to find alternatives)

### Walks Too Random / Not Interesting

- Decrease `--temperature` (less randomness)
- Adjust `--frequency-weight` (try -0.5 to favor rare syllables)
- Try different profiles (clerical for conservative, goblin for exotic)

### Port Already in Use (Web Mode)

```bash
# Try a different port
python -m build_tools.syllable_walk data.json --web --port 8000
```

## Technical Notes

### Dependencies

- **NumPy**: Required for efficient feature matrix operations (build-time only)
- **Standard Library**: All other functionality uses Python stdlib

### Determinism Implementation

Uses `random.Random(seed)` to create isolated RNG instances, avoiding global state contamination.
This ensures reproducibility even when multiple walks are generated concurrently.

### Feature Space

The 12-dimensional binary feature space comes from `syllable_feature_annotator`:

- 3 onset features
- 4 internal features
- 2 nucleus features
- 3 coda features

See `feature_annotator.md` for details on how features are detected.

## Related Tools

- **syllable_feature_annotator**: Generates the input data with phonetic features
- **syllable_normaliser**: Prepares syllable corpus before annotation
- **syllable_extractor**: Extracts raw syllables from dictionary

## Examples

### Example 1: Find Clerical Names

```bash
# Conservative walks favoring common syllables
python -m build_tools.syllable_walk data.json --profile clerical --steps 3

Output: the → then → den
        (common, minimal change)
```

### Example 2: Find Exotic Combinations

```bash
# Chaotic walks favoring rare syllables
python -m build_tools.syllable_walk data.json --profile goblin --steps 5

Output: ka → gjal → kveld → fyrklo → skrypt
        (rare, high variation)
```

### Example 3: Statistical Corpus Analysis

```bash
# Generate 1000 walks and analyze
python -m build_tools.syllable_walk data.json --batch 1000 \
  --profile dialect --output walks.json

# Then analyze walks.json with Python:
import json
walks = json.load(open('walks.json'))
# Count syllable appearances, measure transition frequencies, etc.
```

### Example 4: Interactive Exploration

```bash
# Start web interface and explore visually
python -m build_tools.syllable_walk data.json --web

# Navigate to http://localhost:5000
# Try different profiles, observe walk patterns
# Use custom parameters to fine-tune behavior
```

## References

For implementation details, see:

- `build_tools/syllable_walk/walker.py` - Core algorithm
- `build_tools/syllable_walk/profiles.py` - Profile definitions
- `build_tools/syllable_walk/server.py` - Web interface
- `tests/test_syllable_walk.py` - Comprehensive test suite
