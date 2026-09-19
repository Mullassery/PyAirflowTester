# Getting Help

Need help with PyAirflowTester? Here are your options.

## Documentation

Start with the official documentation:

- **README.md** - Quick start guide and feature overview
- **[docs/archive/DEPENDENCY_INTELLIGENCE_DESIGN.md](docs/archive/DEPENDENCY_INTELLIGENCE_DESIGN.md)** - Complete system specification (13 parts, historical)
- **[docs/archive/DEPENDENCY_CACHING_STRATEGY.md](docs/archive/DEPENDENCY_CACHING_STRATEGY.md)** - Production caching guide (historical)
- **[docs/archive/COMPLETE_SYSTEM_SUMMARY.md](docs/archive/COMPLETE_SYSTEM_SUMMARY.md)** - Feature matrix and architecture (historical)
- **examples/** - Working code examples for all phases

## Frequently Asked Questions

### Installation

**Q: Which Python versions are supported?**
A: Python 3.10, 3.11, 3.12 (this is the actual CI test matrix — see
`.github/workflows/ci.yml`). 3.13+ is not in CI and not verified.

**Q: Do I need Rust installed?**
A: No. As of v0.3.0 this ships as a **pure Python** package (`hatchling` build backend, no
compiled extension). The Rust crate in `src/*.rs` is a separate, unwired experiment — the
CLI never imports or calls into it (see README "Architecture"). You do not need a Rust
toolchain to install, run, or develop the supported (Python) parts of this project.

**Q: Can I use this with Airflow 1.x?**
A: No, Airflow 2.0+ is required.

**Q: Does dbt need to be installed?**
A: No, only dbt manifest.json is needed for dbt integration.

### Usage

**Q: How do I get started?**
A: See README.md "Quick Start" section or run `pyairflowtester --help`

**Q: Can I use PyAirflowTester programmatically?**
A: Yes, full Python API available. See examples/dependency_intelligence_usage.py

**Q: How do I analyze my DAGs?**
A: `pyairflowtester dependency build --dags dags/ --dbt-manifest manifest.json`

**Q: What's the difference between impact and blast radius?**
A: Impact shows affected nodes. Blast radius includes deployment safety assessment.

### Performance

**Q: How long does graph construction take? What's the memory usage?**
A: Unknown — not measured by the current maintainers. Earlier drafts of this file quoted
"~4.2 seconds for 1,000+ DAGs" and "<500MB for 100,000 nodes"; these are unverified numbers
from the original v0.1.0 release announcement (see the note in CHANGELOG.md's `[0.1.0]`
entry) and have been removed here rather than repeated as current fact. If you need real
numbers, benchmark against your own DAG/dbt project — there's no included benchmark suite to
point you to yet.

**Q: Can I cache results?**
A: Yes, see docs/archive/DEPENDENCY_CACHING_STRATEGY.md (historical) for multi-layer caching options

### Troubleshooting

**Q: Getting "Module not found" error?**
A: Ensure PyAirflowTester is installed: `pip install pyairflowtester`

**Q: Rust compilation errors?**
A: You should never hit this from a normal install — `pip install pyairflowtester` installs a
pure Python package, no compilation involved. Rust compilation is only possible if you
deliberately `maturin develop` the unwired experimental crate in `src/*.rs` (see README
"Architecture"); it has no effect on the CLI either way.

**Q: CLI commands not recognized?**
A: Try full path: `python -m pyairflowtester.cli` or reinstall with `pip install --force-reinstall pyairflowtester`

**Q: Tests failing?**
A: Check Python version (3.10+), install dev dependencies: `pip install pyairflowtester[dev]`

## Community Support

### GitHub Issues

For bugs and feature requests: https://github.com/Mullassery/PyAirflowTester/issues

When opening an issue, include:
- Clear description
- Steps to reproduce
- Python version
- Airflow/dbt versions (if applicable)
- Full error messages

### GitHub Discussions

For general questions and discussions: https://github.com/Mullassery/PyAirflowTester/discussions

Great for:
- Usage questions
- Best practices
- Architecture discussion
- Community ideas

### Email Support

For security issues: mullassery@gmail.com

For other inquiries: mullassery@gmail.com

## Contributing

Want to help? See CONTRIBUTING.md for:
- Development setup
- Testing procedures
- Code style guidelines
- Pull request process

## Commercial Support

There is no commercial support offering — this is a small, part-time-maintained
open-source project (see README.md "Status"), not a company. If you have a specific need,
email mullassery@gmail.com, but treat any response as best-effort, not an SLA.

## Code Examples

Quick reference for common tasks:

### Build and Analyze Graph
```python
from pyairflowtester.dependency_intelligence import UnifiedGraphBuilder, ImpactAnalysisEngine

graph = UnifiedGraphBuilder.build_unified_graph(
    dag_files=["dags/"],
    dbt_manifest="dbt/manifest.json"
)

impact = ImpactAnalysisEngine(graph).analyze("my_dag")
print(f"Impact: {impact.impact_score:.1%}")
```

### Check Deployment Safety
```python
from pyairflowtester.dependency_intelligence import BlastRadiusEngine

engine = BlastRadiusEngine(graph)
result = engine.analyze(["changed_dag"])
print(f"Safe to deploy: {result.deployable}")
```

### Get System Health
```python
from pyairflowtester.dependency_intelligence import HealthScoreCalculator

calculator = HealthScoreCalculator(graph)
health = calculator.calculate_health_score()
print(f"Health: {health.overall_score:.0f}/100")
```

## Resources

- GitHub: https://github.com/Mullassery/PyAirflowTester
- PyPI: https://pypi.org/project/pyairflowtester/
- Issues: https://github.com/Mullassery/PyAirflowTester/issues
- Discussions: https://github.com/Mullassery/PyAirflowTester/discussions

## Staying Updated

- Watch the repository for releases
- Subscribe to PyPI notifications
- Enable GitHub notifications

## Report a Bug

Found an issue? Open a GitHub issue: https://github.com/Mullassery/PyAirflowTester/issues

Include:
- Bug description
- Reproduction steps
- Environment details
- Error messages

## Suggest a Feature

Have a great idea? Open a discussion: https://github.com/Mullassery/PyAirflowTester/discussions

Include:
- Feature description
- Use case
- Examples
- Benefits

## Next Steps

1. Read the README
2. Explore examples/
3. Try the CLI: `pyairflowtester --help`
4. Check out the documentation
5. Open an issue if you need help

We're here to help!
