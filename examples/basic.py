from small import CompressionConfig, compress, decompress


def main():
    tokens = ["def", "foo", "(", ")", ":", "return", "foo", "(", ")"]
    cfg = CompressionConfig(max_subsequence_length=4, rng_seed=123, verify=True)
    result = compress(tokens, cfg)
    restored = decompress(result.compressed_tokens, cfg)

    print("Original length:", result.original_length)
    print("Compressed length:", result.compressed_length)
    print("Compressed tokens:", result.compressed_tokens)
    print("Round-trip ok:", restored == tokens)


if __name__ == "__main__":
    main()
