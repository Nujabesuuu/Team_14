"""Run the whole Teamate stack locally with one command: `python dev.py`.

First run: creates apps/api/.venv, installs API and web dependencies, seeds demo data.
Every run: starts the API on :8000 and the web client on :5173; Ctrl+C stops both.
Standard library only, so it works before anything is installed (Windows, macOS, Linux).
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = ROOT / "apps" / "api"
WEB = ROOT / "apps" / "web"
VENV = API / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
INSTALLED_MARK = VENV / ".teamate-installed"
DEMO_DB = API / "teamate.db"


def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def npm() -> str:
    found = shutil.which("npm")
    if not found:
        sys.exit("npm not found. Install Node.js 22+ from https://nodejs.org and run again.")
    return found


def ensure_api_deps() -> None:
    if not VENV_PY.exists():
        step("Creating apps/api/.venv")
        run([sys.executable, "-m", "venv", str(VENV)], cwd=API)
    pyproject = API / "pyproject.toml"
    if not INSTALLED_MARK.exists() or INSTALLED_MARK.stat().st_mtime < pyproject.stat().st_mtime:
        step("Installing API dependencies (pip install -e .[dev])")
        run([str(VENV_PY), "-m", "pip", "install", "-q", "-e", ".[dev]"], cwd=API)
        INSTALLED_MARK.touch()


def ensure_web_deps() -> None:
    if not (WEB / "node_modules").exists():
        step("Installing web dependencies (npm ci)")
        run([npm(), "ci", "--no-audit", "--no-fund"], cwd=WEB)


def wait_for(url: str, timeout: float = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except OSError:
            time.sleep(0.5)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-seed", action="store_true", help="skip demo data (seed is idempotent anyway)")
    parser.add_argument("--fresh", action="store_true", help="move the local demo DB aside and reseed with today's dates")
    args = parser.parse_args()

    if sys.version_info < (3, 12):
        sys.exit(f"Python 3.12+ required, found {sys.version.split()[0]}")

    ensure_api_deps()
    ensure_web_deps()
    # Seed skips a filled DB, so event dates stay where they were on the first run.
    if args.fresh and DEMO_DB.exists():
        backup = DEMO_DB.with_name(f"teamate.backup-{time.strftime('%Y%m%d-%H%M%S')}.db")
        DEMO_DB.rename(backup)
        step(f"Moved the old demo DB to {backup.relative_to(ROOT)}")
    if not args.no_seed:
        step("Seeding demo data (python -m app.seed)")
        run([str(VENV_PY), "-m", "app.seed"], cwd=API)

    step("Starting API on http://localhost:8000 and web on http://localhost:5173")
    procs = [
        subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"], cwd=API),
        subprocess.Popen([npm(), "run", "dev"], cwd=WEB),
    ]
    try:
        if wait_for("http://localhost:8000/api/v1/health/db"):
            print(
                "\n  Teamate is up\n"
                "  UI (skeleton check)  http://localhost:5173/status\n"
                "  UI (app)             http://localhost:5173\n"
                "  API health           http://localhost:8000/api/v1/health\n"
                "  DB health            http://localhost:8000/api/v1/health/db\n"
                "  OpenAPI              http://localhost:8000/docs\n"
                "  Ctrl+C to stop\n",
                flush=True,
            )
        else:
            print("\n  API did not answer /api/v1/health/db within 30 s, see the log above.\n", flush=True)
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
