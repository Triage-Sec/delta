from small import CompressionConfig
from small.static_dict_builder import StaticDictionaryConfig, build_static_dictionary


def test_static_dictionary_builder_basic():
    corpus = [
        ["a", "b", "c", "d", "a", "b", "c", "d"],
        ["a", "b", "c", "d", "a", "b", "c", "d"],
    ]
    weights = [1.0, 1.0]
    cfg = CompressionConfig(static_dictionary_auto=False, dict_length_enabled=False)
    result = build_static_dictionary(corpus, weights, cfg, StaticDictionaryConfig(max_entries=2), "test")
    assert result.entries
