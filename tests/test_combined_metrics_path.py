from pathlib import Path

from small import CompressionConfig, compress


def test_combined_metrics_jsonl_written(tmp_path: Path):
    path = tmp_path / "combined.jsonl"
    cfg = CompressionConfig(
        metrics_jsonl_path=None,
        combined_metrics_jsonl_path=str(path),
        cache_stats={"sets": 1, "hits": 2, "misses": 1, "evictions": 0},
        static_dictionary_auto=False,
    )
    compress(["a", "b", "a", "b", "a", "b"], cfg)
    content = path.read_text(encoding="utf-8")
    assert "compression_ratio" in content
    assert "cache_hit_rate" in content
