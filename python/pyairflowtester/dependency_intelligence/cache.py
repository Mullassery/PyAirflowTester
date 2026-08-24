"""Tiered caching for dependency-graph analysis results.

`DEPENDENCY_CACHING_STRATEGY.md` sketched a 4-layer design (L1 in-memory, L2
Redis, L3 SQLite, L4 DuckDB) that was never actually implemented anywhere in
this package. This module implements two of those layers for real:

- L1 `InMemoryCache`: thread-safe LRU with real per-entry TTL.
- L3 `SqliteCache`: persistent, multi-process-safe (WAL journal mode) --
  the layer that lets expensive graph analysis (cycle detection, strongly
  connected components) survive across separate CLI invocations, which
  nothing in this codebase could do before this.
- `TieredCache`: L1-then-L3 lookup, with real event-driven invalidation
  (`register_invalidation_rule` / `emit`) instead of relying on TTL expiry
  alone.

L2 (Redis) and L4 (DuckDB) are NOT implemented here -- they need an external
service/heavier dependency this otherwise dependency-light package
(`click`, `rich` only) doesn't currently take on. `TieredCache` is built so
a `RedisCache`/`DuckDbCache` could plug in as another tier later without
changing this interface, but that's future work, not shipped today.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


class InMemoryCache:
    """Thread-safe LRU cache (L1) with real per-entry TTL.

    Unlike the ad-hoc, TTL-less dicts scattered elsewhere in this codebase
    (e.g. `DependencyGraphEngine._upstream_cache`), entries here actually
    expire and the cache actually evicts least-recently-used entries once
    `max_size` is exceeded.
    """

    def __init__(self, max_size: int = 10_000):
        self.max_size = max_size
        self._data: "OrderedDict[str, tuple[Any, Optional[float]]]" = OrderedDict()
        self._lock = threading.Lock()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.stats.misses += 1
                return None
            value, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._data[key]
                self.stats.misses += 1
                return None
            self._data.move_to_end(key)
            self.stats.hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        with self._lock:
            self._data[key] = (value, expires_at)
            self._data.move_to_end(key)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)
                self.stats.evictions += 1

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            matching = [k for k in self._data if k.startswith(prefix)]
            for k in matching:
                del self._data[k]
            return len(matching)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class SqliteCache:
    """Persistent cache (L3), backed by SQLite in WAL journal mode.

    WAL mode is what makes this safe for concurrent access from multiple
    processes (e.g. two CLI invocations running at once against the same
    cache file) -- readers don't block the writer and vice versa, which the
    default rollback-journal mode doesn't give you.
    """

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL
            )
            """
        )
        self._conn.commit()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                self.stats.misses += 1
                return None
            value_json, expires_at = row
            if expires_at is not None and time.time() > expires_at:
                self._conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                self._conn.commit()
                self.stats.misses += 1
                return None
            self.stats.hits += 1
            return json.loads(value_json)

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        value_json = json.dumps(value)
        with self._lock:
            self._conn.execute(
                "INSERT INTO cache_entries (key, value, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET "
                "value = excluded.value, expires_at = excluded.expires_at",
                (key, value_json, expires_at),
            )
            self._conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            self._conn.commit()

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM cache_entries WHERE key LIKE ? ESCAPE '\\'",
                (prefix.replace("%", r"\%").replace("_", r"\_") + "%",),
            )
            self._conn.commit()
            return cursor.rowcount

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM cache_entries")
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


class TieredCache:
    """L1 (in-memory) -> L3 (SQLite) cache with event-driven invalidation.

    A cache miss on L1 checks L3 before giving up, and a L3 hit repopulates
    L1 (standard tiered-cache read-through behavior). Writes go to both
    tiers so an L1 eviction doesn't lose data L3 still has.

    Event-driven invalidation: register a rule that computes which key
    prefixes to drop for a named event (e.g. "graph_mutated"), then call
    `emit()` whenever that event actually happens. This is what the
    strategy doc asked for instead of relying on TTL expiry alone --
    invalidation happens exactly when the underlying data changes, not up
    to `ttl_seconds` later.
    """

    def __init__(self, l1: Optional[InMemoryCache] = None, l3: Optional[SqliteCache] = None):
        self.l1 = l1 or InMemoryCache()
        self.l3 = l3
        self._invalidation_rules: Dict[str, List[Callable[..., List[str]]]] = {}

    def get(self, key: str) -> Optional[Any]:
        value = self.l1.get(key)
        if value is not None:
            return value
        if self.l3 is not None:
            value = self.l3.get(key)
            if value is not None:
                self.l1.set(key, value)
                return value
        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        self.l1.set(key, value, ttl_seconds)
        if self.l3 is not None:
            self.l3.set(key, value, ttl_seconds)

    def invalidate(self, key: str) -> None:
        self.l1.delete(key)
        if self.l3 is not None:
            self.l3.delete(key)

    def invalidate_prefix(self, prefix: str) -> int:
        count = self.l1.delete_prefix(prefix)
        if self.l3 is not None:
            count += self.l3.delete_prefix(prefix)
        return count

    def register_invalidation_rule(
        self, event: str, key_prefixes_fn: Callable[..., List[str]]
    ) -> None:
        """Register `key_prefixes_fn(**context) -> [prefix, ...]` to run
        whenever `emit(event, **context)` fires -- every prefix it returns
        gets invalidated across both tiers."""
        self._invalidation_rules.setdefault(event, []).append(key_prefixes_fn)

    def emit(self, event: str, **context: Any) -> List[str]:
        """Fire `event`, running every rule registered for it and
        invalidating every prefix they return. Returns the prefixes that
        were invalidated (useful for logging/testing)."""
        invalidated: List[str] = []
        for rule in self._invalidation_rules.get(event, []):
            for prefix in rule(**context):
                self.invalidate_prefix(prefix)
                invalidated.append(prefix)
        return invalidated
