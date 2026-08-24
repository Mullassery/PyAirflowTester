"""Tests for the tiered cache (dependency_intelligence/cache.py)."""

import time

from pyairflowtester.dependency_intelligence.cache import (
    InMemoryCache,
    SqliteCache,
    TieredCache,
)


class TestInMemoryCache:
    def test_set_and_get(self):
        cache = InMemoryCache()
        cache.set("k", {"v": 1})
        assert cache.get("k") == {"v": 1}

    def test_miss_returns_none(self):
        cache = InMemoryCache()
        assert cache.get("missing") is None
        assert cache.stats.misses == 1

    def test_ttl_expiry(self):
        cache = InMemoryCache()
        cache.set("k", "v", ttl_seconds=0.01)
        assert cache.get("k") == "v"
        time.sleep(0.02)
        assert cache.get("k") is None

    def test_lru_eviction(self):
        cache = InMemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts "a" (least recently used)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.stats.evictions == 1

    def test_delete_prefix(self):
        cache = InMemoryCache()
        cache.set("cycles:abc", [1])
        cache.set("cycles:def", [2])
        cache.set("sccs:abc", [3])
        removed = cache.delete_prefix("cycles:")
        assert removed == 2
        assert cache.get("cycles:abc") is None
        assert cache.get("sccs:abc") == [3]

    def test_hit_rate(self):
        cache = InMemoryCache()
        cache.set("k", "v")
        cache.get("k")
        cache.get("missing")
        assert cache.stats.hit_rate == 0.5


class TestSqliteCache:
    def test_set_and_get_persists_across_instances(self, tmp_path):
        db_path = tmp_path / "cache.db"
        cache1 = SqliteCache(db_path)
        cache1.set("k", {"nested": [1, 2, 3]})
        cache1.close()

        cache2 = SqliteCache(db_path)
        assert cache2.get("k") == {"nested": [1, 2, 3]}
        cache2.close()

    def test_ttl_expiry(self, tmp_path):
        cache = SqliteCache(tmp_path / "cache.db")
        cache.set("k", "v", ttl_seconds=0.01)
        assert cache.get("k") == "v"
        time.sleep(0.02)
        assert cache.get("k") is None
        cache.close()

    def test_uses_wal_journal_mode(self, tmp_path):
        cache = SqliteCache(tmp_path / "cache.db")
        mode = cache._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
        cache.close()

    def test_delete_prefix(self, tmp_path):
        cache = SqliteCache(tmp_path / "cache.db")
        cache.set("cycles:abc", [1])
        cache.set("cycles:def", [2])
        cache.set("sccs:abc", [3])
        removed = cache.delete_prefix("cycles:")
        assert removed == 2
        assert cache.get("cycles:abc") is None
        assert cache.get("sccs:abc") == [3]
        cache.close()

    def test_concurrent_processes_can_share_the_same_file(self, tmp_path):
        """WAL mode is what makes this safe -- two independent connections to
        the same file, one write visible to the other after commit."""
        db_path = tmp_path / "shared.db"
        writer = SqliteCache(db_path)
        writer.set("shared_key", "shared_value")

        reader = SqliteCache(db_path)
        assert reader.get("shared_key") == "shared_value"
        writer.close()
        reader.close()


class TestTieredCache:
    def test_read_through_from_l3_populates_l1(self, tmp_path):
        l1 = InMemoryCache()
        l3 = SqliteCache(tmp_path / "cache.db")
        l3.set("k", "from-l3")  # only in L3, not L1

        tiered = TieredCache(l1=l1, l3=l3)
        assert tiered.get("k") == "from-l3"
        # Now L1 should have it too, without touching L3 stats again.
        l3_hits_before = l3.stats.hits
        assert l1.get("k") == "from-l3"
        assert l3.stats.hits == l3_hits_before

    def test_set_writes_both_tiers(self, tmp_path):
        l1 = InMemoryCache()
        l3 = SqliteCache(tmp_path / "cache.db")
        tiered = TieredCache(l1=l1, l3=l3)

        tiered.set("k", "v")

        assert l1.get("k") == "v"
        assert l3.get("k") == "v"

    def test_works_with_only_l1(self):
        tiered = TieredCache()
        tiered.set("k", "v")
        assert tiered.get("k") == "v"

    def test_invalidate_prefix_clears_both_tiers(self, tmp_path):
        l3 = SqliteCache(tmp_path / "cache.db")
        tiered = TieredCache(l3=l3)
        tiered.set("cycles:abc", [1])
        tiered.set("cycles:def", [2])

        count = tiered.invalidate_prefix("cycles:")

        assert count == 4  # 2 from L1 + 2 from L3
        assert tiered.get("cycles:abc") is None
        assert tiered.get("cycles:def") is None

    def test_event_driven_invalidation(self, tmp_path):
        tiered = TieredCache()
        tiered.set("graph:v1:cycles", ["a", "b"])
        tiered.set("graph:v1:sccs", ["c"])
        tiered.set("unrelated:key", "keep-me")

        tiered.register_invalidation_rule(
            "graph_mutated", lambda graph_version: [f"graph:{graph_version}:"]
        )

        invalidated = tiered.emit("graph_mutated", graph_version="v1")

        assert invalidated == ["graph:v1:"]
        assert tiered.get("graph:v1:cycles") is None
        assert tiered.get("graph:v1:sccs") is None
        assert tiered.get("unrelated:key") == "keep-me"

    def test_emit_with_no_registered_rules_is_a_noop(self):
        tiered = TieredCache()
        tiered.set("k", "v")
        assert tiered.emit("nothing_registered") == []
        assert tiered.get("k") == "v"
