"""
Entry point for running syllable_normaliser as a module.

This allows the package to be executed with:
    python -m build_tools.syllable_normaliser [arguments]
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
