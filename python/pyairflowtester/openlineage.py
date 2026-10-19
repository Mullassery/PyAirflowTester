"""OpenLineage runtime lineage ingestion.

OpenLineage (Apache-2.0) is emitted by Airflow, dbt, Spark and other tools.
This module parses run events into a small local SQLite store and exposes
job/dataset relationships for runtime-aware analysis.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class RuntimeLineageSummary:
    runs: int
    jobs: int
    datasets: int
    edges: int

    def to_dict(self) -> dict[str, int]:
        return {
            "runs": self.runs,
            "jobs": self.jobs,
            "datasets": self.datasets,
            "edges": self.edges,
        }


def load_events(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        return [data] if isinstance(data, dict) else []
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _dataset_key(dataset: dict[str, Any]) -> str:
    namespace = str(dataset.get("namespace") or "")
    name = str(dataset.get("name") or "")
    return f"{namespace}:{name}" if namespace else name


class LineageStore:
    """SQLite-backed runtime lineage store."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT, job_namespace TEXT, job_name TEXT, event_type TEXT,
                event_time TEXT, producer TEXT,
                PRIMARY KEY (run_id, event_type)
            );
            CREATE TABLE IF NOT EXISTS nodes (
                key TEXT PRIMARY KEY, kind TEXT, namespace TEXT, name TEXT
            );
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT, target TEXT, run_id TEXT,
                PRIMARY KEY (source, target, run_id)
            );
            """)

    def close(self) -> None:
        self._conn.close()

    def ingest(self, events: Iterable[dict[str, Any]]) -> RuntimeLineageSummary:
        for event in events:
            if not isinstance(event, dict):
                continue
            job = event.get("job") or {}
            run = event.get("run") or {}
            job_key = f"{job.get('namespace', '')}:{job.get('name', '')}"
            run_id = str(run.get("runId") or "")
            event_type = str(event.get("eventType") or "")
            self._conn.execute(
                "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    str(job.get("namespace") or ""),
                    str(job.get("name") or ""),
                    event_type,
                    event.get("eventTime"),
                    event.get("producer"),
                ),
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO nodes VALUES (?, 'job', ?, ?)",
                (job_key, str(job.get("namespace") or ""), str(job.get("name") or "")),
            )
            for direction in ("inputs", "outputs"):
                for dataset in event.get(direction) or []:
                    if not isinstance(dataset, dict):
                        continue
                    dataset_key = _dataset_key(dataset)
                    self._conn.execute(
                        "INSERT OR REPLACE INTO nodes VALUES (?, 'dataset', ?, ?)",
                        (
                            dataset_key,
                            str(dataset.get("namespace") or ""),
                            str(dataset.get("name") or ""),
                        ),
                    )
                    source, target = (
                        (dataset_key, job_key) if direction == "inputs" else (job_key, dataset_key)
                    )
                    self._conn.execute(
                        "INSERT OR IGNORE INTO edges VALUES (?, ?, ?)",
                        (source, target, run_id),
                    )
        self._conn.commit()
        return self.summary()

    def summary(self) -> RuntimeLineageSummary:
        def count(table: str) -> int:
            return int(self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

        return RuntimeLineageSummary(
            runs=count("runs"),
            jobs=int(
                self._conn.execute("SELECT COUNT(*) FROM nodes WHERE kind='job'").fetchone()[0]
            ),
            datasets=int(
                self._conn.execute("SELECT COUNT(*) FROM nodes WHERE kind='dataset'").fetchone()[0]
            ),
            edges=count("edges"),
        )

    def jobs(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT namespace, name FROM nodes WHERE kind='job' ORDER BY namespace, name"
        ).fetchall()
        return [{"namespace": n, "name": name} for n, name in rows]

    def datasets(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT namespace, name FROM nodes WHERE kind='dataset' ORDER BY namespace, name"
        ).fetchall()
        return [{"namespace": n, "name": name} for n, name in rows]

    def edges(self) -> list[dict[str, str]]:
        rows = self._conn.execute(
            "SELECT source, target, run_id FROM edges ORDER BY source, target"
        ).fetchall()
        return [{"source": s, "target": t, "run_id": r} for s, t, r in rows]


def ingest_files(paths: Iterable[str | Path], db_path: str | Path) -> RuntimeLineageSummary:
    store = LineageStore(db_path)
    try:
        events: list[dict[str, Any]] = []
        for path in paths:
            events.extend(load_events(path))
        return store.ingest(events)
    finally:
        store.close()


__all__ = ["LineageStore", "RuntimeLineageSummary", "ingest_files", "load_events"]
