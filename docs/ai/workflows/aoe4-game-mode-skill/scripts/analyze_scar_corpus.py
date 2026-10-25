#!/usr/bin/env python3
"""Build a provenance-aware digest of an AoE4 SCAR reference corpus."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {".api", ".css", ".htm", ".html", ".lua", ".rdo", ".scar", ".txt"}
IGNORED_DIRECTORIES = {".git", ".hg", ".svn", "__pycache__"}
CONTROL_WORDS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}

FUNCTION_DEF_RE = re.compile(r"\b(?:local\s+)?function\s+([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(")
ASSIGNED_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_\.:]*)\s*=\s*function\s*\(")
CALL_RE = re.compile(r"(?<![\w\.])([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(")
IMPORT_RE = re.compile(r"\bimport\s*\(\s*[\"']([^\"']+)[\"']\s*\)")
MODULE_RE = re.compile(r"\bCore_RegisterModule\s*\(\s*[\"']([^\"']+)[\"']")
NETWORK_REGISTER_RE = re.compile(r"\bNetwork_RegisterEvent\s*\(\s*[\"']([^\"']+)[\"']")
NETWORK_CALL_RE = re.compile(r"\bNetwork_CallEvent\s*\(\s*[\"']([^\"']+)[\"']")
RULE_ADD_RE = re.compile(
    r"\b(Rule_Add(?:GlobalEvent|Interval(?:WithDelay)?|OneShot|Event|EntityEvent|SquadEvent|EGroupEvent|SGroupEvent|PlayerEvent)?)\s*\(\s*([A-Za-z_][A-Za-z0-9_\.:]*)"
)
RULE_REMOVE_RE = re.compile(
    r"\b(Rule_Remove(?:GlobalEvent|Event|EntityEvent|SquadEvent|EGroupEvent|SGroupEvent|PlayerEvent)?)\s*\(\s*([A-Za-z_][A-Za-z0-9_\.:]*)"
)
OPTION_RE = re.compile(r"\b((?:option|section|selection)_[A-Za-z0-9_]+)\b")
API_RE = re.compile(
    r"^\s*(?:\d+\(\s+\w+\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s+RETURNS:",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read every file in an AoE4 SCAR corpus and emit a provenance-aware digest."
    )
    parser.add_argument("root", type=Path, help="Corpus root to inspect")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write the full machine-readable report")
    parser.add_argument("--markdown", dest="markdown_path", type=Path, help="Write a compact Markdown digest")
    parser.add_argument("--symbols", dest="symbols_path", type=Path, help="Write a TSV symbol provenance index")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Directory name to exclude; may be repeated",
    )
    parser.add_argument("--top", type=int, default=40, help="Number of top symbols to include")
    parser.add_argument(
        "--default-source",
        choices=("other", "ugc"),
        default="other",
        help="Provenance assigned to files outside Official, unofficial, and scardocs roots.",
    )
    parser.add_argument(
        "--include-extension",
        action="append",
        default=[],
        help="Only include this extension (for example .scar); may be repeated.",
    )
    return parser.parse_args()


def classify_source(relative: Path, default_source: str = "other") -> str:
    parts = [part.lower() for part in relative.parts]
    if parts and parts[0] == "official":
        return "official"
    if parts and parts[0] == "unofficial":
        return "unofficial"
    if parts and parts[0] == "scardocs":
        return "official-docs"
    return default_source


def decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1"


def strip_lua_comments_and_strings(text: str) -> str:
    """Preserve newlines while hiding common Lua comments and quoted strings."""
    result: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        comment_match = re.match(r"--\[(=*)\[", text[index:])
        if comment_match:
            equals = comment_match.group(1)
            closer = "]" + equals + "]"
            start_length = len(comment_match.group(0))
            end = text.find(closer, index + start_length)
            end = length - len(closer) if end == -1 else end
            chunk = text[index : end + len(closer)]
            result.append("\n" * chunk.count("\n"))
            index = end + len(closer)
            continue
        if text.startswith("--", index):
            end = text.find("\n", index + 2)
            if end == -1:
                break
            result.append("\n")
            index = end + 1
            continue
        if text[index] in {'"', "'"}:
            quote = text[index]
            result.append(" ")
            index += 1
            while index < length:
                char = text[index]
                if char == "\\":
                    result.append("  ")
                    index += 2
                    continue
                if char == quote:
                    result.append(" ")
                    index += 1
                    break
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        string_match = re.match(r"\[(=*)\[", text[index:])
        if string_match:
            equals = string_match.group(1)
            closer = "]" + equals + "]"
            start_length = len(string_match.group(0))
            end = text.find(closer, index + start_length)
            end = length - len(closer) if end == -1 else end
            chunk = text[index : end + len(closer)]
            result.append("\n" * chunk.count("\n"))
            index = end + len(closer)
            continue
        result.append(text[index])
        index += 1
    return "".join(result)


def inspect_text(text: str, extension: str) -> dict[str, Any]:
    details: dict[str, Any] = {
        "imports": [],
        "function_definitions": [],
        "calls": [],
        "modules": [],
        "lifecycle_callbacks": [],
        "rule_adds": [],
        "rule_removes": [],
        "network_registers": [],
        "network_calls": [],
        "option_keys": [],
        "api_symbols": [],
    }
    if extension in {".scar", ".lua"}:
        clean = strip_lua_comments_and_strings(text)
        definitions = FUNCTION_DEF_RE.findall(clean) + ASSIGNED_FUNCTION_RE.findall(clean)
        calls = [name for name in CALL_RE.findall(clean) if name not in CONTROL_WORDS]
        details.update(
            imports=sorted(set(IMPORT_RE.findall(text))),
            function_definitions=sorted(set(definitions)),
            calls=calls,
            modules=sorted(set(MODULE_RE.findall(text))),
            lifecycle_callbacks=sorted(
                {
                    name
                    for name in definitions
                    if name.endswith(
                        (
                            "_OnGameSetup",
                            "_PreInit",
                            "_OnInit",
                            "_Start",
                            "_OnGameRestore",
                            "_OnGameOver",
                        )
                    )
                }
            ),
            rule_adds=[{"kind": kind, "callback": callback} for kind, callback in RULE_ADD_RE.findall(clean)],
            rule_removes=[{"kind": kind, "callback": callback} for kind, callback in RULE_REMOVE_RE.findall(clean)],
            network_registers=sorted(set(NETWORK_REGISTER_RE.findall(text))),
            network_calls=sorted(set(NETWORK_CALL_RE.findall(text))),
            option_keys=sorted(set(OPTION_RE.findall(text))),
        )
    elif extension == ".rdo":
        details["option_keys"] = sorted(set(OPTION_RE.findall(text)))
    elif extension == ".api":
        details["api_symbols"] = sorted(set(name for name, _ in API_RE.findall(text)))
    return details


def iter_files(
    root: Path, excluded: set[str], included_extensions: set[str] | None = None
) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in excluded or part in IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            continue
        if included_extensions and path.suffix.lower() not in included_extensions:
            continue
        files.append(path)
    return sorted(files, key=lambda value: value.as_posix().lower())


def counter_rows(counter: collections.Counter[str], limit: int) -> list[dict[str, Any]]:
    return [{"symbol": symbol, "count": count} for symbol, count in counter.most_common(limit)]


def build_report(
    root: Path,
    excluded: set[str],
    top: int,
    default_source: str = "other",
    included_extensions: set[str] | None = None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    extension_counts: collections.Counter[str] = collections.Counter()
    source_counts: collections.Counter[str] = collections.Counter()
    call_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    definition_sets: dict[str, set[str]] = collections.defaultdict(set)
    api_symbols: set[str] = set()

    for path in iter_files(root, excluded, included_extensions):
        relative = path.relative_to(root)
        extension = path.suffix.lower() or "[none]"
        source = classify_source(relative, default_source)
        data = path.read_bytes()
        record: dict[str, Any] = {
            "path": relative.as_posix(),
            "source": source,
            "extension": extension,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "text": extension in TEXT_EXTENSIONS,
        }
        if extension in TEXT_EXTENSIONS:
            text, encoding = decode_text(data)
            record["encoding"] = encoding
            record["lines"] = text.count("\n") + (1 if text else 0)
            details = inspect_text(text, extension)
            record.update(details)
            call_counts[source].update(details["calls"])
            definition_sets[source].update(details["function_definitions"])
            api_symbols.update(details["api_symbols"])
        records.append(record)
        extension_counts[extension] += 1
        source_counts[source] += 1

    official_known = api_symbols | definition_sets["official"]
    secondary_defined = definition_sets["unofficial"] | definition_sets["ugc"]
    secondary_external_calls = (
        call_counts["unofficial"] + call_counts["ugc"]
    ) - collections.Counter(secondary_defined)
    secondary_only = collections.Counter(
        {
            name: count
            for name, count in secondary_external_calls.items()
            if name not in official_known and name not in CONTROL_WORDS
        }
    )

    content_hash_counts = collections.Counter(record["sha256"] for record in records)
    duplicate_groups = [count for count in content_hash_counts.values() if count > 1]
    unique_call_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    seen_hashes: set[str] = set()
    for record in records:
        if record["sha256"] in seen_hashes:
            continue
        seen_hashes.add(record["sha256"])
        unique_call_counts[record["source"]].update(record.get("calls", []))

    return {
        "root": str(root.resolve()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "files": len(records),
            "bytes": sum(record["bytes"] for record in records),
            "text_files": sum(1 for record in records if record["text"]),
            "binary_files": sum(1 for record in records if not record["text"]),
            "lines": sum(record.get("lines", 0) for record in records),
            "extensions": dict(sorted(extension_counts.items())),
            "sources": dict(sorted(source_counts.items())),
            "official_api_symbols": len(api_symbols),
            "official_function_definitions": len(definition_sets["official"]),
            "unofficial_function_definitions": len(definition_sets["unofficial"]),
            "ugc_function_definitions": len(definition_sets["ugc"]),
            "unique_content_hashes": len(content_hash_counts),
            "duplicate_content_groups": len(duplicate_groups),
            "duplicate_file_instances": sum(count - 1 for count in duplicate_groups),
        },
        "top_calls": {
            source: counter_rows(counter, top) for source, counter in sorted(call_counts.items())
        },
        "top_calls_unique_content": {
            source: counter_rows(counter, top)
            for source, counter in sorted(unique_call_counts.items())
        },
        "secondary_unverified_calls": counter_rows(secondary_only, top),
        "files": records,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Corpus manifest",
        "",
        "Generated by `scripts/analyze_scar_corpus.py`. Every file listed below was read and hashed.",
        f"Source root: `{report['root']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        "",
        "## Contents",
        "",
        "1. Coverage",
        "2. Source policy",
        "3. Complete file index",
        "",
        "## Coverage",
        "",
        f"- Files: {summary['files']} ({summary['text_files']} text, {summary['binary_files']} binary)",
        f"- Lines read: {summary['lines']}",
        f"- Bytes read: {summary['bytes']}",
        f"- Official API symbols: {summary['official_api_symbols']}",
        f"- Official SCAR/Lua function definitions: {summary['official_function_definitions']}",
        f"- Unofficial SCAR/Lua function definitions: {summary['unofficial_function_definitions']}",
        f"- UGC SCAR/Lua function definitions: {summary['ugc_function_definitions']}",
        f"- Unique content hashes: {summary['unique_content_hashes']}",
        f"- Duplicate file instances: {summary['duplicate_file_instances']} across {summary['duplicate_content_groups']} content groups",
        "",
        "### Files by provenance",
        "",
        "| Provenance | Files |",
        "| --- | ---: |",
    ]
    for source, count in report["summary"]["sources"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(["", "### Files by extension", "", "| Extension | Files |", "| --- | ---: |"])
    for extension, count in report["summary"]["extensions"].items():
        lines.append(f"| `{extension}` | {count} |")

    lines.extend(
        [
            "",
            "## Source policy",
            "",
            "Treat official API documentation and official source as authoritative. Treat unofficial code as a source of design ideas only until every external call and lifecycle assumption is confirmed against official evidence.",
            "",
            "## Complete file index",
            "",
            "| Source | File | Lines | Bytes | SHA-256 |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for record in report["files"]:
        digest = record["sha256"][:12]
        lines.append(
            f"| {record['source']} | `{record['path']}` | {record.get('lines', '-')} | {record['bytes']} | `{digest}` |"
        )
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def symbol_index(report: dict[str, Any]) -> str:
    symbols: dict[str, dict[str, Any]] = collections.defaultdict(
        lambda: {
            "api": False,
            "definition_sources": set(),
            "definition_types": set(),
            "definition_files": set(),
            "official_calls": 0,
            "unofficial_calls": 0,
            "ugc_calls": 0,
        }
    )
    for record in report["files"]:
        source = record["source"]
        for name in record.get("api_symbols", []):
            symbols[name]["api"] = True
        for name in record.get("function_definitions", []):
            symbols[name]["definition_sources"].add(source)
            symbols[name]["definition_types"].add(f"{source}:{record['extension']}")
            symbols[name]["definition_files"].add(record["path"])
        counts = collections.Counter(record.get("calls", []))
        for name, count in counts.items():
            if source == "official":
                symbols[name]["official_calls"] += count
            elif source == "unofficial":
                symbols[name]["unofficial_calls"] += count
            elif source == "ugc":
                symbols[name]["ugc_calls"] += count

    rows = [
        "symbol\tprovenance\tdefinition_sources\tofficial_calls\tunofficial_calls\tugc_calls\tdefinition_files"
    ]
    for name in sorted(symbols, key=str.lower):
        details = symbols[name]
        sources = details["definition_sources"]
        if details["api"]:
            provenance = "official-api"
        elif "official:.scar" in details["definition_types"]:
            provenance = "official-source"
        elif "official:.lua" in details["definition_types"]:
            provenance = "official-terrain-lua"
        elif "unofficial" in sources:
            provenance = "unofficial-definition"
        elif "ugc" in sources:
            provenance = "ugc-definition"
        else:
            provenance = "usage-only"
        rows.append(
            "\t".join(
                [
                    name,
                    provenance,
                    ",".join(sorted(sources)),
                    str(details["official_calls"]),
                    str(details["unofficial_calls"]),
                    str(details["ugc_calls"]),
                    ";".join(sorted(details["definition_files"])),
                ]
            )
        )
    return "\n".join(rows) + "\n"


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Corpus root is not a directory: {root}")
    included_extensions = {
        value.lower() if value.startswith(".") else f".{value.lower()}"
        for value in args.include_extension
    }
    report = build_report(
        root,
        set(args.exclude),
        args.top,
        args.default_source,
        included_extensions or None,
    )
    if args.json_path:
        write_text(args.json_path, json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    if args.markdown_path:
        write_text(args.markdown_path, markdown_report(report))
    if args.symbols_path:
        write_text(args.symbols_path, symbol_index(report))
    print(json.dumps(report["summary"], indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
