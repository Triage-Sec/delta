from small.suffix_array import build_suffix_array


def test_suffix_array_basic():
    tokens = ["b", "a", "b", "a"]
    sa = build_suffix_array(tokens)
    assert sorted(sa.suffix_array) == [0, 1, 2, 3]
    assert len(sa.lcp) == max(0, len(tokens) - 1)
