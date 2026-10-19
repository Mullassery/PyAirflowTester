.PHONY: help install install-dev test test-rust test-python test-integration lint lint-rust format format-rust clean build docs

help:
	@echo "PyAirflowTester - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install              Install package"
	@echo "  make install-dev          Install with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run the shipped Python test suite"
	@echo "  make test-rust            Run optional Rust crate tests (not shipped)"
	@echo "  make test-python          Run Python tests"
	@echo "  make test-integration     Run integration tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run Python linters"
	@echo "  make lint-rust            Run optional Rust linter (not shipped)"
	@echo "  make format               Format Python code"
	@echo "  make format-rust          Format optional Rust crate"
	@echo "  make type-check           Run type checking (mypy)"
	@echo ""
	@echo "Build:"
	@echo "  make build                Build the pure-Python wheel and sdist"
	@echo "  make docs                 Build documentation"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Clean build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,web]"
	pre-commit install

test: test-python

test-rust:
	@echo "Running optional Rust crate tests (not part of the shipped package)..."
	cargo test --verbose

test-python:
	@echo "Running Python tests..."
	pytest python/tests/ -v --cov=pyairflowtester

test-integration:
	@echo "Running integration tests..."
	pytest python/tests/integration/ -v

lint:
	@echo "Linting Python code..."
	ruff check python/

lint-rust:
	@echo "Linting optional Rust crate (not shipped)..."
	cargo clippy -- -D warnings

format:
	@echo "Formatting Python code..."
	black python/

format-rust:
	@echo "Formatting optional Rust crate..."
	cargo fmt

type-check:
	@echo "Type checking Python code..."
	mypy python/pyairflowtester --ignore-missing-imports

build:
	@echo "Building the pure-Python package (hatchling)..."
	pip install build
	python -m build

docs:
	@echo "Building documentation..."
	pip install sphinx sphinx-rtd-theme
	cd docs && make html

clean:
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf build/ dist/ *.egg-info target/
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .pytest_cache .coverage htmlcov

ci: lint type-check test

pre-commit:
	pre-commit run --all-files
