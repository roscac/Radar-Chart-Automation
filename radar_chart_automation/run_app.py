"""Launch the GUI using the project's virtual environment interpreter."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _venv_python(project_root: Path) -> Path:
    if os.name == "nt":
        return project_root / ".venv" / "Scripts" / "python.exe"
    return project_root / ".venv" / "bin" / "python"


def _clean_python_env(env: dict[str, str]) -> dict[str, str]:
    clean = dict(env)
    clean.pop("PYTHONHOME", None)
    clean.pop("PYTHONPATH", None)
    return clean


def main() -> int:
    project_root = Path(__file__).resolve().parent
    app_path = project_root / "app.py"
    venv_python = _venv_python(project_root)
    active_python = Path(sys.executable).resolve()

    if not venv_python.exists():
        print("Missing virtual environment at .venv.")
        print("Run the setup once:")
        if os.name == "nt":
            print("  py -m venv .venv")
            print("  .venv\\Scripts\\activate")
        else:
            print("  python3 -m venv .venv")
            print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")
        return 1

    if active_python != venv_python.resolve():
        # Relaunch from .venv to avoid mixing Anaconda/system interpreters with Tk bindings.
        cmd = [str(venv_python), str(app_path)]
        result = subprocess.run(cmd, cwd=str(project_root), env=_clean_python_env(os.environ))
        return result.returncode

    os.chdir(project_root)
    result = subprocess.run([str(active_python), str(app_path)], env=_clean_python_env(os.environ))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
