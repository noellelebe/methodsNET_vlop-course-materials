"""Check that the course script environment is ready."""

from __future__ import annotations

import importlib.util
import sys


REQUIRED = ["requests", "bs4", "pandas", "yaml"]
OPTIONAL = ["playwright", "pyarrow"]


def available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> None:
    print(f"Python: {sys.version.split()[0]}")
    missing = [name for name in REQUIRED if not available(name)]
    for name in REQUIRED:
        print(f"required {name}: {'ok' if available(name) else 'missing'}")
    for name in OPTIONAL:
        print(f"optional {name}: {'ok' if available(name) else 'missing'}")
    if missing:
        raise SystemExit(
            "Install missing dependencies with: pip install -r requirements.txt"
        )
    print("Environment looks ready for the core scripts.")


if __name__ == "__main__":
    main()
