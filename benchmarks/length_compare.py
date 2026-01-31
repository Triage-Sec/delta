import argparse
import pathlib
import random
import statistics

from delta import CompressionConfig, compress


def generate_tokens(count: int, vocab_size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    return [f"t{rng.randrange(vocab_size)}" for _ in range(count)]


def tokenize_corpus(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return text.split()


def main() -> None:
    parser = argparse.ArgumentParser(description="LTSC max subsequence length comparison")
    parser.add_argument("--tokens", type=int, default=8192)
    parser.add_argument("--vocab", type=int, default=512)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--lengths", type=str, default="2,3,4,5,6")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--corpus", type=str, default="")
    args = parser.parse_args()

    lengths = [int(value.strip()) for value in args.lengths.split(",") if value.strip()]
    if not lengths:
        raise ValueError("No lengths provided.")

    corpus_tokens: list[str] | None = None
    if args.corpus:
        corpus_path = pathlib.Path(args.corpus)
        corpus_tokens = tokenize_corpus(corpus_path)

    print(f"Runs: {args.runs}")
    print(f"Tokens: {len(corpus_tokens) if corpus_tokens is not None else args.tokens}")
    print(f"Vocab: {args.vocab}")
    if args.corpus:
        print(f"Corpus: {args.corpus}")
    print("\nlength,mean_full_ratio,mean_body_ratio")

    for max_len in lengths:
        ratios: list[float] = []
        body_ratios: list[float] = []
        for offset in range(args.runs):
            if corpus_tokens is None:
                seed = args.seed + offset
                tokens = generate_tokens(args.tokens, args.vocab, seed)
            else:
                seed = args.seed
                tokens = corpus_tokens
            cfg = CompressionConfig(max_subsequence_length=max_len, rng_seed=seed)
            result = compress(tokens, cfg)
            ratios.append(result.compressed_length / result.original_length)
            body_ratios.append(len(result.body_tokens) / result.original_length)

        mean_ratio = statistics.mean(ratios)
        mean_body_ratio = statistics.mean(body_ratios)
        print(f"{max_len},{mean_ratio:.4f},{mean_body_ratio:.4f}")


if __name__ == "__main__":
    main()
