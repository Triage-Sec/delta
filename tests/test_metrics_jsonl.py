from pathlib import Path

from small import CompressionConfig, compress


def test_metrics_jsonl_written(tmp_path: Path):
    path = tmp_path / "metrics.jsonl"
    cfg = CompressionConfig(metrics_jsonl_path=str(path), static_dictionary_auto=False)
    result = compress(["a", "b", "a", "b", "a", "b"], cfg)
    content = path.read_text(encoding="utf-8")
    assert "compression_ratio" in content
