#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
HOOK_REV=${HOOK_REV:-$(git -C "$REPO_ROOT" rev-parse HEAD)}
SAMPLE_REPO=$(mktemp -d "${TMPDIR:-/tmp}/fix-non-ascii-test.XXXXXX")

cleanup() {
  rm -rf "$SAMPLE_REPO"
}
trap cleanup EXIT

if ! git config --get user.name >/dev/null || ! git config --get user.email >/dev/null; then
  echo "git user.name and user.email must be configured for local test execution" >&2
  exit 1
fi

cd "$SAMPLE_REPO"
git init -q

cat > .pre-commit-config.yaml <<CFG
repos:
  - repo: $REPO_ROOT
    rev: $HOOK_REV
    hooks:
      - id: fix-non-ascii
CFG

printf 'int m = 2 × 3;\n' > sample.c
grep -Fx 'int m = 2 × 3;' sample.c
git add .

if pre-commit run --all-files --verbose; then
  echo "Expected pre-commit to fail after applying fixes" >&2
  exit 1
fi

grep -Fx 'int m = 2 x 3;' sample.c
pre-commit run --all-files --verbose
