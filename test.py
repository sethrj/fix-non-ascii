#!/usr/bin/env python3
"""Locally executable integration test for the fix-non-ascii pre-commit hook."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_INPUT_WITH_NON_ASCII = "int m = 2 × 3;\n"
EXPECTED_OUTPUT_ASCII = "int m = 2 x 3;\n"


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run *cmd* with inherited stdio so hook output is shown live."""
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def run_capture(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run *cmd* and capture stdout/stderr for explicit validation checks."""
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    hook_manifest_path = repo_root / ".pre-commit-hooks.yaml"
    if not hook_manifest_path.is_file():
        print(f"Missing expected hook manifest: {hook_manifest_path}", file=sys.stderr)
        return 1

    hook_manifest = hook_manifest_path.read_text(encoding="utf-8")
    languages = [
        line.split(":", 1)[1].strip()
        for line in hook_manifest.splitlines()
        if line.lstrip().startswith("language:")
    ]
    if languages != ["python"]:
        print(f"Expected hook to use language: python, found: {languages}", file=sys.stderr)
        return 1

    hook_rev = os.environ.get("HOOK_REV")
    if not hook_rev:
        hook_rev_result = run_capture(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=False)
        hook_rev = hook_rev_result.stdout.strip()
        if hook_rev_result.returncode != 0 or not hook_rev:
            print(f"Failed to resolve hook revision from {repo_root}", file=sys.stderr)
            return 1

    for config_key in ("user.name", "user.email"):
        result = run_capture(["git", "config", "--global", "--get", config_key], check=False)
        if result.returncode != 0 or not result.stdout.strip():
            print(f"git config --global {config_key} must be set for local test execution", file=sys.stderr)
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
        sample_file.write_text(TEST_INPUT_WITH_NON_ASCII, encoding="utf-8")
        if sample_file.read_text(encoding="utf-8") != TEST_INPUT_WITH_NON_ASCII:
            print("Failed to create expected U+00D7 test input", file=sys.stderr)
            return 1

        run(["git", "add", "."], cwd=sample_repo)

        # Keep live pre-commit output visible for immediate CI/local debugging context.
        first_run = run(["pre-commit", "run", "--all-files", "--verbose"], cwd=sample_repo, check=False)
        if first_run.returncode == 0:
            print(
                "Expected pre-commit to fail after detecting and fixing non-ASCII multiplication character",
                file=sys.stderr,
            )
            return 1

        if sample_file.read_text(encoding="utf-8") != EXPECTED_OUTPUT_ASCII:
            print("Expected pre-commit to replace U+00D7 with ASCII 'x'", file=sys.stderr)
            return 1

        second_run = run(["pre-commit", "run", "--all-files", "--verbose"], cwd=sample_repo, check=False)
        if second_run.returncode != 0:
            return second_run.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
