"""OpenLineage ingestion tests (fixtures only)."""

from __future__ import annotations

import json

from pyairflowtester.openlineage import LineageStore, ingest_files, load_events

EVENT = {
    "eventType": "COMPLETE",
    "eventTime": "2026-01-01T00:00:00Z",
    "producer": "airflow",
    "job": {"namespace": "airflow", "name": "etl_orders"},
    "run": {"runId": "run-1"},
    "inputs": [{"namespace": "snowflake", "name": "raw.orders"}],
    "outputs": [{"namespace": "snowflake", "name": "analytics.orders"}],
}


def test_ingest_file_and_summary(tmp_path):
    events = tmp_path / "events.json"
    events.write_text(json.dumps([EVENT]))
    db = tmp_path / "lineage.sqlite"
    summary = ingest_files([events], db)
    assert summary.runs == 1
    assert summary.jobs == 1
    assert summary.datasets == 2
    assert summary.edges == 2

    store = LineageStore(db)
    assert store.jobs() == [{"namespace": "airflow", "name": "etl_orders"}]
    assert store.datasets()[0]["name"] == "analytics.orders"
    assert len(store.edges()) == 2
    store.close()


def test_ndjson_and_dedup(tmp_path):
    path = tmp_path / "events.ndjson"
    path.write_text(json.dumps(EVENT) + "\n" + json.dumps(EVENT) + "\n")
    assert len(load_events(path)) == 2
    db = tmp_path / "lineage.sqlite"
    summary = ingest_files([path], db)
    assert summary.runs == 1  # same run/event type is idempotent
