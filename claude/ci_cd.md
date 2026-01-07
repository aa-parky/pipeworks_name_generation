# CI/CD Pipeline

This document covers the continuous integration and deployment setup for the pipeworks_name_generation project.

## GitHub Actions Workflows

### Main CI Pipeline

**File**: `.github/workflows/ci.yml`

The main CI pipeline runs on every push to `main`/`develop` branches and on all pull requests:

- **Code Quality**: Ruff linting, Black formatting, mypy type checking
- **Test Suite**: Runs on Ubuntu, macOS, Windows with Python 3.12 and 3.13
- **Security Scan**: Bandit for code security, Safety for dependency vulnerabilities
- **Documentation**: Builds Sphinx docs and checks for excessive warnings
- **Package Build**: Builds distribution packages and validates with twine
- **Coverage**: Uploads coverage reports to Codecov

### Dependency Updates

**File**: `.github/workflows/dependency-update.yml`

Automated dependency monitoring:

- Runs weekly on Monday at 9:00 AM UTC
- Checks for outdated dependencies
- Creates GitHub issues with update recommendations

## Pre-commit Hooks

The project uses pre-commit hooks for automated code quality enforcement. These run automatically on `git commit`.

### File Formatting

- Trailing whitespace removal
- End-of-file fixing
- Line ending normalization (LF)

### Code Quality

- YAML/TOML/JSON validation
- Python AST checking
- Import sorting (isort)
- Code formatting (Black)
- Linting (Ruff with auto-fix)
- Type checking (mypy for main package)

### Security

- Bandit security scanning
- Dependency vulnerability checking (Safety)

### Documentation

- Markdown linting (markdownlint)
- Spell checking (codespell)

## Triggers

- **Pre-commit hooks**: Run automatically on `git commit`
- **CI pipeline**: Runs on pushes to `main`/`develop` and on pull requests
- **Manual trigger**: Can be triggered via GitHub Actions UI

## Local Pre-commit Setup

See [Development Guide](development.md#pre-commit-hooks) for installation and usage instructions.
