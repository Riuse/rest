from __future__ import annotations
import json
from .main import app

def main() -> None:
    schema = app.openapi()
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print("Saved openapi.json")

if __name__ == "__main__":
    main()
