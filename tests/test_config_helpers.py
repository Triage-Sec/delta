from small import CompressionConfig, with_cache_stats_source


def test_with_cache_stats_source():
    cfg = CompressionConfig()
    obj = object()
    new_cfg = with_cache_stats_source(cfg, obj)
    assert new_cfg.cache_stats_source is obj
    assert cfg.cache_stats_source is None
