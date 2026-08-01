# Getting Help

Need help with PyAirflowTester? Here are your options.

## Documentation

Start with the official documentation:

- **README.md** - Quick start guide and feature overview
- **DEPENDENCY_INTELLIGENCE_DESIGN.md** - Complete system specification (13 parts)
- **DEPENDENCY_CACHING_STRATEGY.md** - Production caching guide
- **COMPLETE_SYSTEM_SUMMARY.md** - Feature matrix and architecture
- **examples/** - Working code examples for all phases

## Frequently Asked Questions

### Installation

**Q: Which Python versions are supported?**
A: Python 3.10, 3.11, 3.12, and 3.13+

**Q: Do I need Rust installed?**
A: No, pre-built wheels include Rust extensions. Only needed if building from source.

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

**Q: How long does graph construction take?**
A: ~4.2 seconds for 1,000+ DAGs on modern hardware

**Q: What's the memory usage?**
A: <500MB for 100,000 nodes

**Q: Can I cache results?**
A: Yes, see DEPENDENCY_CACHING_STRATEGY.md for multi-layer caching options

### Troubleshooting

**Q: Getting "Module not found" error?**
A: Ensure PyAirflowTester is installed: `pip install pyairflowtester`

**Q: Rust compilation errors?**
A: Use pre-built wheels instead: `pip install pyairflowtester` (no compilation needed)

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

For enterprise support, custom features, or consulting:
Contact: mullassery@gmail.com

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
