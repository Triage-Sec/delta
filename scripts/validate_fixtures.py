import json
from pathlib import Path


def validate_jsonl(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON at {path}:{line_no}: {exc}")


def main() -> None:
    base = Path("tests/fixtures")
    for jsonl in base.rglob("*.jsonl"):
        validate_jsonl(jsonl)
    print("fixtures ok")


if __name__ == "__main__":
    main()
