.PHONY: help install install-dev test test-rust test-python test-integration lint format clean build docs

help:
	@echo "PyAirflowTester - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install              Install package"
	@echo "  make install-dev          Install with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-rust            Run Rust tests"
	@echo "  make test-python          Run Python tests"
	@echo "  make test-integration     Run integration tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run linters (ruff, clippy)"
	@echo "  make format               Format code (black, rustfmt)"
	@echo "  make type-check           Run type checking (mypy)"
	@echo ""
	@echo "Build:"
	@echo "  make build                Build wheels"
	@echo "  make docs                 Build documentation"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Clean build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,otel]"
	pre-commit install

test: test-rust test-python

test-rust:
	@echo "Running Rust tests..."
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
	@echo "Linting Rust code..."
	cargo clippy -- -D warnings

format:
	@echo "Formatting Python code..."
	black python/
	@echo "Formatting Rust code..."
	cargo fmt

type-check:
	@echo "Type checking Python code..."
	mypy python/pyairflowtester --ignore-missing-imports || true

build:
	@echo "Building Python wheels..."
	pip install maturin
	maturin build --release

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
