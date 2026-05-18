#!/usr/bin/env python3
# Copyright UT-Battelle, LLC
# SPDX-License-Identifier: Apache-2.0
"""Fix non-ASCII characters in source files.

Replace known Unicode symbols with ASCII equivalents and remove the UTF-8
byte order mark (BOM). Report an error for any remaining non-ASCII character.

Exit with status 1 if any file was modified or if unrecognized non-ASCII
characters were found.

When invoked from pre-commit, file selection is handled by the ``files:``
pattern in the hook configuration.

Usage (standalone)::

    python3 fix-non-ascii.py src/celeritas/Types.hh

Usage (pre-commit)::

    pre-commit run fix-non-ascii
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# UTF-8 encoding of the byte order mark.
_UTF8_BOM = b"\xef\xbb\xbf"

# Mapping of Unicode characters to ASCII replacements.
_REPLACEMENTS: dict[str, str] = {
    "\u00d7": "x",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "--",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u2190": "<-",
    "\u2192": "->",
    "\u21d0": "<=",
    "\u21d2": "=>",
    "\u21d4": "<=>",
    "\u2212": "-",
}

_REPLACEMENTS_TABLE: dict[int, str] = str.maketrans(
    {ord(k): v for k, v in _REPLACEMENTS.items()}
)


def _find_non_ascii_errors(path: Path, text: str) -> list[str]:
    """Return error strings for non-ASCII characters in *text*."""
    errors = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 127:
                errors.append(
                    f"{path}:{lineno}:{col}: "
                    f"non-ASCII character U+{ord(ch):04X} ({ch!r})"
                )
    return errors


def process_file(path: Path) -> tuple[bool, list[str]]:
    """Fix non-ASCII characters in *path* in place."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return False, [f"{path}: {exc}"]

    bom_stripped = raw.startswith(_UTF8_BOM)
    data = raw[3:] if bom_stripped else raw

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return False, [f"{path}: cannot decode as UTF-8: {exc}"]

    text = text.translate(_REPLACEMENTS_TABLE)

    new_raw = text.encode("utf-8")
    modified = bom_stripped or (new_raw != data)

    if text.isascii():
        errors = []
    else:
        errors = _find_non_ascii_errors(path, text)

    if modified:
        path.write_bytes(new_raw)

    return modified, errors


def _build_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        metavar="FILE",
        help="source files to check and fix",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    result = 0
    for filename in args.filenames:
        path = Path(filename)

        modified, errors = process_file(path)

        if modified:
            print(f"Fixed non-ASCII characters in {filename}")
            result = 1

        for error in errors:
            print(error, file=sys.stderr)
        if errors:
            result = 1

    return result


if __name__ == "__main__":
    sys.exit(main())
