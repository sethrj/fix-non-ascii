#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def run_capture(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    hook_rev = os.environ.get("HOOK_REV")
    if not hook_rev:
        hook_rev = run_capture(["git", "-C", str(repo_root), "rev-parse", "HEAD"]).stdout.strip()

    for config_key in ("user.name", "user.email"):
        result = run_capture(["git", "config", "--global", "--get", config_key], check=False)
        if result.returncode != 0 or not result.stdout.strip():
            print("git user.name and user.email must be configured for local test execution", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        sample_repo = Path(tmpdir)
        run(["git", "init", "-q"], cwd=sample_repo)

        config_text = (
            "repos:\n"
            f"  - repo: {repo_root}\n"
            f"    rev: {hook_rev}\n"
            "    hooks:\n"
            "      - id: fix-non-ascii\n"
        )
        (sample_repo / ".pre-commit-config.yaml").write_text(config_text, encoding="utf-8")

        sample_file = sample_repo / "sample.c"
        sample_file.write_text("int m = 2 × 3;\n", encoding="utf-8")
        if sample_file.read_text(encoding="utf-8") != "int m = 2 × 3;\n":
            print("Failed to create expected U+00D7 test input", file=sys.stderr)
            return 1

        run(["git", "add", "."], cwd=sample_repo)

        first_run = run(["pre-commit", "run", "--all-files", "--verbose"], cwd=sample_repo, check=False)
        if first_run.returncode == 0:
            print(
                "Expected pre-commit to fail after detecting and fixing non-ASCII multiplication character",
                file=sys.stderr,
            )
            return 1

        if sample_file.read_text(encoding="utf-8") != "int m = 2 x 3;\n":
            print("Expected pre-commit to replace U+00D7 with ASCII 'x'", file=sys.stderr)
            return 1

        second_run = run(["pre-commit", "run", "--all-files", "--verbose"], cwd=sample_repo, check=False)
        if second_run.returncode != 0:
            return second_run.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
