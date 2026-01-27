import argparse
import random
import statistics
import time

from small import CompressionConfig, compress


def generate_tokens(count: int, vocab_size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    return [f"t{rng.randrange(vocab_size)}" for _ in range(count)]


def main() -> None:
    parser = argparse.ArgumentParser(description="LTSC compression latency benchmark")
    parser.add_argument("--tokens", type=int, default=8192)
    parser.add_argument("--vocab", type=int, default=512)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--max-len", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    tokens = generate_tokens(args.tokens, args.vocab, args.seed)
    cfg = CompressionConfig(max_subsequence_length=args.max_len, rng_seed=args.seed)

    timings_ms: list[float] = []
    for _ in range(args.runs):
        start = time.perf_counter()
        compress(tokens, cfg)
        end = time.perf_counter()
        timings_ms.append((end - start) * 1000)

    avg = statistics.mean(timings_ms)
    p95 = statistics.quantiles(timings_ms, n=20)[-1]
    print(f"Runs: {args.runs}")
    print(f"Tokens: {args.tokens}")
    print(f"Max subsequence length: {args.max_len}")
    print(f"Mean latency (ms): {avg:.2f}")
    print(f"P95 latency (ms): {p95:.2f}")


if __name__ == "__main__":
    main()
