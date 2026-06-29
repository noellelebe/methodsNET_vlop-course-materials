"""Check that the course script environment is ready."""

from __future__ import annotations

import importlib.util
import sys


REQUIRED = ["requests", "bs4", "pandas", "yaml"]
OPTIONAL = ["selenium", "playwright", "pyarrow", "jupyter", "nbconvert"]


def available(module_name: str) -> bool:
    # find_spec() checks whether Python can locate a package without importing
    # and running the package itself.
    return importlib.util.find_spec(module_name) is not None


def main() -> None:
    # sys.version contains the full Python version string; split()[0] keeps only
    # the version number, which is easier to read in setup output.
    print(f"Python: {sys.version.split()[0]}")
    # List comprehension: keep only required packages that are not available.
    missing = [name for name in REQUIRED if not available(name)]
    for name in REQUIRED:
        # This prints one line per required package so students can see exactly
        # which dependency is missing.
        print(f"required {name}: {'ok' if available(name) else 'missing'}")
    for name in OPTIONAL:
        # Optional packages support some workflows but are not needed for the
        # core API/static-scraping scripts.
        print(f"optional {name}: {'ok' if available(name) else 'missing'}")
    if missing:
        # SystemExit stops the script with a readable message instead of
        # continuing into later scripts that would fail less clearly.
        raise SystemExit(
            "Install missing dependencies with: pip install -r requirements.txt"
        )
    print("Environment looks ready for the core scripts.")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Run from the repository root:
#
#     python scripts/runnable_workflows/00_setup_check.py
#
# What each part means:
#
# - python
#   Starts Python from your current environment.
#
# - scripts/runnable_workflows/00_setup_check.py
#   The path to this setup-check script.
#
# This script has no command-line options. It simply checks whether important
# teaching packages can be imported in the Python environment you are using.
