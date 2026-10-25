#!/usr/bin/env python3
"""Validate an extracted multi-project SCAR corpus without mixing project contexts."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_scar


SUPPORTED_EXTENSIONS = frozenset({".lua", ".rdo", ".scar"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate SCAR projects stored as <subscription>/<archive>/... below "
            "an extracted corpus root."
        )
    )
    parser.add_argument("root", type=Path, help="Extracted corpus root")
    parser.add_argument(
        "--symbol-index",
        type=Path,
        default=validate_scar.DEFAULT_SYMBOL_INDEX,
        help="Official/API symbol provenance TSV.",
    )
    parser.add_argument("--json", dest="json_path", type=Path, help="Write the full report")
    parser.add_argument(
        "--include-extension",
        action="append",
        default=[".scar"],
        help="Extension to validate; may be repeated (default: .scar).",
    )
    return parser.parse_args()


def project_key(root: Path, path: Path) -> tuple[str, ...]:
    parts = path.relative_to(root).parts
    if len(parts) >= 3:
        return parts[:2]
    return parts[:-1]


def build_report(
    root: Path, symbol_index_path: Path, included_extensions: set[str]
) -> dict[str, Any]:
    files = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in included_extensions
        ),
        key=lambda path: path.as_posix().lower(),
    )
    projects: dict[tuple[str, ...], list[Path]] = collections.defaultdict(list)
    for path in files:
        projects[project_key(root, path)].append(path)

    symbol_index = validate_scar.load_symbol_index(symbol_index_path)
    results: list[dict[str, Any]] = []
    for key, project_files in sorted(projects.items()):
        project_root = root.joinpath(*key) if key else root
        definitions, network_events, _ = validate_scar.collect_project_context(project_root)
        for path in project_files:
            result = validate_scar.validate_file(
                path, symbol_index, definitions, network_events
            )
            result["relative_path"] = path.relative_to(root).as_posix()
            result["project"] = "/".join(key)
            results.append(result)

    diagnostics = [item for result in results for item in result["diagnostics"]]
    severities = collections.Counter(item["severity"] for item in diagnostics)
    codes = collections.Counter(item["code"] for item in diagnostics)
    content_hashes = {
        hashlib.sha256(path.read_bytes()).hexdigest() for path in files
    }
    return {
        "source_root": str(root),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "projects": len(projects),
            "files": len(files),
            "unique_content_hashes": len(content_hashes),
            "files_with_errors": sum(
                1 for result in results if result["summary"]["errors"]
            ),
            "files_with_warnings": sum(
                1 for result in results if result["summary"]["warnings"]
            ),
            "errors": severities["error"],
            "warnings": severities["warning"],
            "diagnostics_by_code": dict(sorted(codes.items())),
        },
        "files": results,
    }


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Corpus root is not a directory: {root}")
    included_extensions = {
        value.lower() if value.startswith(".") else f".{value.lower()}"
        for value in args.include_extension
    }
    unsupported = included_extensions - SUPPORTED_EXTENSIONS
    if unsupported:
        raise SystemExit(f"Unsupported extensions: {', '.join(sorted(unsupported))}")
    report = build_report(root, args.symbol_index.resolve(), included_extensions)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(report["summary"], indent=2, ensure_ascii=True))
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
