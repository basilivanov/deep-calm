#!/usr/bin/env python3
"""Export OpenAPI schema for DeepCalm backend."""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app  # noqa

OUTPUT = ROOT_DIR / "cortex" / "APIs" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI exported to {OUTPUT}")


if __name__ == "__main__":
    main()
