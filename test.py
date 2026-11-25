"""Run every automated check of Teamate with one command: `python test.py`.

API: ruff check, ruff format --check, pytest. Web: tsc, oxlint, vitest. The same steps as CI.
Installs dependencies on the first run (like dev.py) and never touches the demo DB: tests use in-memory SQLite.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from dev import API, VENV_PY, WEB, ensure_api_deps, ensure_web_deps, npm

API_STEPS = [
    ("ruff check", [str(VENV_PY), "-m", "ruff", "check", "app", "tests"]),
    ("ruff format --check", [str(VENV_PY), "-m", "ruff", "format", "--check", "app", "tests"]),
    ("pytest", [str(VENV_PY), "-m", "pytest", "-q"]),
]
WEB_STEPS = [
    ("typecheck", ["run", "typecheck"]),
    ("lint", ["run", "lint"]),
    ("vitest", ["test"]),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    only = parser.add_mutually_exclusive_group()
    only.add_argument("--api", action="store_true", help="only the API checks")
    only.add_argument("--web", action="store_true", help="only the web checks")
    args = parser.parse_args()

    steps: list[tuple[str, list[str], Path]] = []
    if not args.web:
        ensure_api_deps()
        steps += [(f"api · {name}", cmd, API) for name, cmd in API_STEPS]
    if not args.api:
        ensure_web_deps()
        steps += [(f"web · {name}", [npm(), *cmd], WEB) for name, cmd in WEB_STEPS]

    results = []
    for name, cmd, cwd in steps:
        print(f"\n==> {name}", flush=True)
        started = time.monotonic()
        code = subprocess.run(cmd, cwd=cwd).returncode
        results.append((name, code, time.monotonic() - started))

    print("\n  Summary")
    for name, code, seconds in results:
        print(f"  {'PASS' if code == 0 else 'FAIL'}  {name:<28} {seconds:5.1f}s")
    failed = [name for name, code, _ in results if code]
    print(f"\n  {'All checks passed' if not failed else f'{len(failed)} failed: ' + ', '.join(failed)}\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
