from pathlib import Path

from small.metrics import CompressionMetrics
from small.metrics_writer import write_combined_metrics_jsonl


def test_combined_metrics_writer(tmp_path: Path):
    metrics = CompressionMetrics(
        compression_amount=0.1,
        compression_ratio=0.9,
        effective_savings=3,
        candidates_discovered=2,
        patterns_used=1,
        avg_pattern_length=3.0,
        avg_pattern_frequency=2.0,
        dictionary_overhead_pct=0.2,
        depth_utilization={1: 1},
    )
    path = tmp_path / "combined.jsonl"
    write_combined_metrics_jsonl(path, metrics, {"sets": 1, "hits": 2, "misses": 1, "evictions": 0})
    content = path.read_text(encoding="utf-8")
    assert "compression_ratio" in content
    assert "cache_hit_rate" in content
