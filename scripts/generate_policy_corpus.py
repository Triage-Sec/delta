import json
import random
from pathlib import Path


def main(out_path: str, count: int, seed: int = 7) -> None:
    rng = random.Random(seed)
    items = []
    for idx in range(count):
        policy = {
            "id": f"sec_{idx:03d}",
            "text": f"All API endpoints must require authentication. Tokens expire after {24 + idx % 10} hours.",
            "domain": "policy",
            "language": "en",
            "source": "synthetic",
        }
        items.append(policy)

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item) + "\n")


if __name__ == "__main__":
    main("tests/fixtures/corpora/policies/security_policies.jsonl", 100)
