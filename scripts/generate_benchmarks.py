import json
from pathlib import Path


def main(out_path: str) -> None:
    items = [
        {
            "id": "qa_001",
            "context_id": "sec_001",
            "question": "How long until an authentication token expires due to inactivity?",
            "answer": "24 hours",
            "answer_type": "extractive",
        },
        {
            "id": "qa_002",
            "context_id": "sec_002",
            "question": "What encryption standard is required for PII at rest?",
            "answer": "AES-256 or equivalent",
            "answer_type": "extractive",
        },
    ]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(item) for item in items) + "\n")


if __name__ == "__main__":
    main("tests/fixtures/benchmarks/security_qa.jsonl")
