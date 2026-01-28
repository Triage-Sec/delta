from pathlib import Path

from small import CompressionConfig, compress
from small.embedding_cache import SQLiteCacheConfig, SQLiteEmbeddingCache


def test_combined_metrics_with_cache_source(tmp_path: Path):
    cache = SQLiteEmbeddingCache(SQLiteCacheConfig(path=str(tmp_path / "emb.db"), compression="none"))
    # Populate cache stats
    cache.set("k1", [0.1, 0.2], model_id="m")
    path = tmp_path / "combined.jsonl"
    cfg = CompressionConfig(
        combined_metrics_jsonl_path=str(path),
        cache_stats_source=cache,
        static_dictionary_auto=False,
    )
    compress(["a", "b", "a", "b", "a", "b"], cfg)
    content = path.read_text(encoding="utf-8")
    assert "cache_hit_rate" in content
    cache.close()
