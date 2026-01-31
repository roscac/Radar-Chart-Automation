import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "src" / "version.py"
VERSION_PATTERN = r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'


def run(cmd):
    subprocess.check_call(cmd, cwd=ROOT)


def git_clean():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == ""


def bump_version(major: int, minor: int, patch: int, part: str):
    if part == "major":
        return major + 1, 0, 0
    if part == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def main():
    parser = argparse.ArgumentParser(description="Bump version, tag, and push a release.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--major", action="store_true", help="Bump major version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--patch", action="store_true", help="Bump patch version (default)")
    args = parser.parse_args()

    if not git_clean():
        raise SystemExit("Working tree is dirty. Commit or stash changes before releasing.")

    text = VERSION_PATH.read_text()
    match = re.search(VERSION_PATTERN, text)
    if not match:
        raise SystemExit("Version not found in src/version.py")

    major, minor, patch = map(int, match.groups())
    part = "patch"
    if args.major:
        part = "major"
    elif args.minor:
        part = "minor"

    new_major, new_minor, new_patch = bump_version(major, minor, patch, part)
    new_version = f"{new_major}.{new_minor}.{new_patch}"

    updated = re.sub(VERSION_PATTERN, f'__version__ = "{new_version}"', text, count=1)
    VERSION_PATH.write_text(updated)

    tag = f"v{new_version}"

    run(["git", "add", str(VERSION_PATH)])
    run(["git", "commit", "-m", f"Release {tag}"])
    run(["git", "tag", tag])
    run(["git", "push", "origin", "HEAD"])
    run(["git", "push", "origin", tag])

    print(f"Released {tag}. GitHub Actions will build and attach artifacts.")


if __name__ == "__main__":
    main()
