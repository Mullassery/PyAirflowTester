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
5. Ensure all tests pass and coverage doesn't drop below its current baseline
   (~71-74% overall as of 2026-09-19, verify with `pytest --cov=pyairflowtester
   --cov-report=term-missing` — see README.md "Status" for what's thin: `cli.py` and
   `dependency_intelligence/cli.py` are at 0%)
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request with a clear description

## Development Setup

### Prerequisites
- Python 3.10+ (3.10-3.12 are what CI actually tests)
- Git
- **Rust toolchain: not required.** This ships as a pure Python package; you only need Rust
  if you're deliberately working on the separate, unwired experimental crate in `src/*.rs`
  (see README.md "Architecture").

### Installation

```bash
git clone https://github.com/Mullassery/PyAirflowTester.git
cd PyAirflowTester
pip install -e ".[dev,web]"
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

### Building the actual package (what `pip install pyairflowtester` ships)

The real build backend is `hatchling` (see `pyproject.toml`'s `[build-system]`), not maturin:

```bash
pip install build
python -m build   # produces dist/*.whl and dist/*.tar.gz, pure Python, no Rust involved
```

### Building the separate, unwired Rust experiment (optional, not part of the shipped package)

```bash
pip install maturin
maturin build --release   # or `maturin develop` to import it locally as pyairflowtester._core
```
Nothing in the CLI calls into this even if you build it — see README.md "Architecture".
Note: on at least macOS arm64, `cargo test`/`cargo build --release` on this crate can fail to
link (`ld: symbol(s) not found ... _Py_InitializeEx` etc.) because `pyo3`'s
`extension-module` feature (`Cargo.toml`) deliberately doesn't link against libpython —
reproduced during the 2026-09-19 pass. `cargo clippy` and `cargo check` are unaffected. See
ROADMAP_HONEST.md.

## Project Structure

```
PyAirflowTester/
├── python/
│   ├── pyairflowtester/
│   │   ├── dependency_intelligence/  # Core dependency graph engine
│   │   │   ├── models.py             # Data models
│   │   │   ├── graph.py              # Graph algorithms
│   │   │   ├── parsers.py            # Dependency parsers
│   │   │   ├── analyzers.py          # Ownership/schema/SLA/test-coverage analyzers
│   │   │   ├── analytics.py          # Analytics helpers
│   │   │   ├── intelligence.py       # Failure prediction, health score, recommendations
│   │   │   ├── observability.py      # Metrics/alerts/events/dashboards
│   │   │   └── cli.py                # `dependency ...` subcommands
│   │   ├── rules/                    # Static analysis rules (AFW/DBT/CFG)
│   │   ├── web/                      # `pyairflowtester serve` FastAPI app
│   │   ├── cli.py                    # Main CLI entry point
│   │   ├── scanner.py, scoring.py, report.py, models.py, analyzer.py
│   │   └── __init__.py
│   └── tests/                        # Test suite (sibling of pyairflowtester/, not nested in it)
├── src/                               # Rust crate — separate, unwired, see above
├── examples/                          # Working examples
└── docs/                              # Architecture notes + docs/archive/ (superseded planning docs)
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints on public functions
- Write docstrings for classes and public methods
- Keep line length at 100 characters
- One liner comments maximum, only for non-obvious WHY

## Testing Requirements

- All new features must include tests
- Don't drop the existing coverage baseline (~71-74% overall, uneven — see README.md
  "Status"); there is no enforced 85% target, that number was never accurate
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
