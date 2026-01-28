import json
from pathlib import Path


def main() -> None:
    min_cases = [
        {"id": "edge_min_001", "text": "Xylophone zebra quantum fuchsia.", "domain": "edge_case"},
        {"id": "edge_min_002", "text": "The quick brown fox jumps over the lazy dog.", "domain": "edge_case"},
    ]
    max_cases = [
        {"id": "edge_max_001", "text": "error " * 20, "domain": "edge_case"},
        {"id": "edge_max_002", "text": "if (x > 0) { return true; }\n" * 5, "domain": "edge_case"},
    ]

    base = Path("tests/fixtures/corpora/edge_cases")
    base.mkdir(parents=True, exist_ok=True)
    (base / "minimal_repetition.jsonl").write_text("\n".join(json.dumps(c) for c in min_cases) + "\n")
    (base / "maximum_repetition.jsonl").write_text("\n".join(json.dumps(c) for c in max_cases) + "\n")


if __name__ == "__main__":
    main()
