"""
Syllable Walker TUI - Interactive Text User Interface

An interactive terminal UI for exploring phonetic space through the Syllable Walker
system. This is a **build-time tool only** - not used during runtime name generation.

Features:
- Side-by-side patch configuration (dual oscillator comparison)
- Keyboard-first navigation (HJKL + arrow keys)
- Real-time phonetic exploration
- Configurable keybindings

Usage:
    python -m build_tools.syllable_walk_tui

Design Philosophy:
    Based on the eurorack modular synthesizer analogy - we patch conditions,
    not outputs. The focus is on exploring phonetic climates through
    interactive parameter tweaking.
"""

__version__ = "0.1.0"
