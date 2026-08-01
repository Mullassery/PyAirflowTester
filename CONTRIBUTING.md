# Contributing to PyAirflowTester

Thank you for interest in contributing to PyAirflowTester. We welcome contributions from the community.

## Code of Conduct

Please review our CODE_OF_CONDUCT.md before contributing.

## How to Contribute

### Reporting Bugs

Before creating bug reports, check the issue list to avoid duplicates.

When creating a bug report, include:
- Clear title and description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Your environment (Python version, OS, Airflow version)
- Code samples if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:
- Clear title and description
- Use case and motivation
- Possible implementation approaches
- Any relevant examples

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write tests for new functionality
5. Ensure all tests pass and coverage stays above 85%
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request with a clear description

## Development Setup

### Prerequisites
- Python 3.10+
- Git
- Rust toolchain (for building Rust extensions)

### Installation

```bash
git clone https://github.com/Mullassery/PyAirflowTester.git
cd PyAirflowTester
pip install -e ".[dev,otel]"
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest python/tests/test_dependency_graph.py

# Run with coverage
pytest --cov=python/pyairflowtester --cov-report=html

# Run tests for specific phase
pytest python/tests/test_dependency_*.py -v
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with Black
black python/

# Lint with Ruff
ruff check python/ --fix

# Type checking
mypy python/pyairflowtester

# Pre-commit hooks
pre-commit run --all-files
```

### Building Wheels

```bash
# Install build dependencies
pip install maturin build

# Build wheels
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
maturin build --release -o dist --sdist
```

## Project Structure

```
pyairflowtester/
├── python/pyairflowtester/
│   ├── dependency_intelligence/  # Core dependency graph engine
│   │   ├── models.py            # Data models
│   │   ├── graph.py             # Graph algorithms
│   │   ├── parsers.py           # Dependency parsers
│   │   ├── analyzers.py         # Phase 1 analysis engines
│   │   ├── analytics.py         # Phase 2 analytics
│   │   ├── intelligence.py      # Phase 3 intelligence
│   │   └── observability.py     # Phase 4 observability
│   ├── rules/                    # Static analysis rules
│   ├── cli.py                    # Command-line interface
│   └── tests/                    # Test suite
├── src/                          # Rust bindings
├── examples/                     # Working examples
└── Documentation/                # Guides and specs
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints on public functions
- Write docstrings for classes and public methods
- Keep line length at 100 characters
- One liner comments maximum, only for non-obvious WHY

## Testing Requirements

- All new features must include tests
- Maintain 85%+ code coverage
- Tests should follow naming convention: `test_<feature>_<scenario>`
- Use pytest fixtures for setup/teardown
- Mock external dependencies

Example test structure:

```python
def test_feature_basic_functionality():
    """Test that feature works in basic case."""
    result = feature.execute()
    assert result.success

def test_feature_edge_case():
    """Test that feature handles edge case."""
    result = feature.execute(edge_case=True)
    assert result.handles_gracefully
```

## Documentation

- Update README.md for user-facing changes
- Update relevant .md files in root for architecture/design changes
- Include docstrings in Python code
- Add examples to examples/ directory for new features

## Commit Messages

Use clear, descriptive commit messages:

```
Brief summary (50 chars)

Longer explanation if needed (72 chars per line)

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG or release notes
3. Create git tag: `git tag v<version>`
4. Push tag: `git push origin v<version>`
5. Create GitHub release with release notes
6. Build and publish wheels

## Questions?

- Open an issue with your question
- Check existing documentation in root .md files
- Review examples in examples/ directory

## Thank You

Your contributions make PyAirflowTester better for everyone. Thank you for your time and effort!

---

Happy contributing!
