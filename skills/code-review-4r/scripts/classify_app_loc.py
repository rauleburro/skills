#!/usr/bin/env python3
"""Classify git numstat rows for the production-application LOC budget."""

import json
from pathlib import PurePosixPath
import re
import sys


CODE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".dart", ".ejs", ".go", ".h", ".hbs",
    ".hpp", ".html", ".java", ".js", ".jsx", ".kt", ".kts", ".less", ".m",
    ".mm", ".mjs", ".php", ".pug", ".py", ".rb", ".rs", ".sass", ".scala",
    ".scss", ".svelte", ".swift", ".ts", ".tsx", ".vue",
}

EXCLUDED_DIRS = {
    ".circleci", ".github", ".gitlab", "__mocks__", "__snapshots__", "__tests__",
    "asset", "assets", "build", "ci", "config", "coverage", "dist", "doc", "docs",
    "documentation", "example", "examples", "fixture", "fixtures", "generated",
    "integration_test", "migration", "migrations", "mock", "mocks", "node_modules",
    "public", "sample", "samples", "script", "scripts", "snapshot", "snapshots",
    "static", "test", "tests", "third_party", "tool", "tools", "vendor",
}

TEST_FILE_RE = re.compile(
    r"(^test_|_test$|[._-](test|tests|spec|specs)([._-]|$))",
    re.IGNORECASE,
)

GENERATED_FILE_RE = re.compile(
    r"(\.g\.dart$|\.freezed\.dart$|[._-](generated|gen)\.)",
    re.IGNORECASE,
)

CONFIG_FILE_RE = re.compile(
    r"(^|[._-])(config|configuration)([._-]|$)",
    re.IGNORECASE,
)


def is_app_code(path):
    """Return True only for hand-written production application code."""
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    lowered_parts = {part.lower() for part in parts[:-1]}
    filename = parts[-1] if parts else normalized
    stem = PurePosixPath(filename).stem
    suffix = PurePosixPath(filename).suffix.lower()

    if lowered_parts & EXCLUDED_DIRS:
        return False
    if suffix not in CODE_SUFFIXES:
        return False
    if TEST_FILE_RE.search(stem):
        return False
    if GENERATED_FILE_RE.search(filename):
        return False
    if CONFIG_FILE_RE.search(stem):
        return False
    return True


def summarize_numstat(lines):
    stats = {
        "app_changed_files": 0,
        "app_added_loc": 0,
        "app_removed_loc": 0,
        "excluded_changed_files": 0,
        "excluded_added_loc": 0,
        "excluded_removed_loc": 0,
    }

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if not line:
            continue
        fields = line.split("\t", 2)
        if len(fields) != 3:
            continue
        added, removed, path = fields
        if added == "-" or removed == "-":
            continue

        prefix = "app" if is_app_code(path) else "excluded"
        stats[f"{prefix}_changed_files"] += 1
        stats[f"{prefix}_added_loc"] += int(added)
        stats[f"{prefix}_removed_loc"] += int(removed)

    return stats


if __name__ == "__main__":
    json.dump(summarize_numstat(sys.stdin), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
