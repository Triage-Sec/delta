import argparse
import time

from small import CompressionConfig, compress


def generate_tokens(count: int) -> list[str]:
    return [f"t{i % 128}" for i in range(count)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Latency scaling benchmark")
    parser.add_argument("--min", type=int, default=100)
    parser.add_argument("--max", type=int, default=100000)
    parser.add_argument("--step", type=int, default=2)
    args = parser.parse_args()

    size = args.min
    while size <= args.max:
        tokens = generate_tokens(size)
        cfg = CompressionConfig(static_dictionary_auto=False, verify=False)
        start = time.perf_counter()
        compress(tokens, cfg)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{size},{elapsed:.2f}")
        size *= args.step


if __name__ == "__main__":
    main()
