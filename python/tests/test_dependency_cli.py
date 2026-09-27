"""Regression tests for `pyairflowtester dependency ...` CLI wiring.

`dependency_intelligence/cli.py` has 0% coverage overall (see
ROADMAP_HONEST.md) -- this file is not an attempt to fix that broadly, only
to pin down one specific bug found and fixed during a bug-hunt pass: the
`build` command's `--datasets` option was accepted but silently discarded.
"""

from click.testing import CliRunner
from pyairflowtester.dependency_intelligence.cli import build


class TestBuildDatasetsOption:
    def test_datasets_option_is_not_silently_discarded(self, tmp_path):
        """Regression test: `build`'s `--datasets` option used to be parsed
        by click and then thrown away -- the function body always called
        `UnifiedGraphBuilder.build_unified_graph(..., dataset_files=[])`
        regardless of what `--datasets` pointed at, so dataset nodes never
        appeared in the built graph no matter what was passed."""
        dataset_dir = tmp_path / "datasets"
        dataset_dir.mkdir()
        (dataset_dir / "dataset_dag.py").write_text(
            "from airflow.datasets import Dataset\n" 'Dataset("s3://bucket/data.csv")\n'
        )

        runner = CliRunner()
        result = runner.invoke(build, ["--datasets", str(dataset_dir)])

        assert result.exit_code == 0
        assert '"node_count": 1' in result.output
        assert "s3://bucket/data.csv" in result.output
