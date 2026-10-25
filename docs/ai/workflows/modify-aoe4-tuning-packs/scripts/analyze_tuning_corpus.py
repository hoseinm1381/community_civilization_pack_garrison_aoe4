#!/usr/bin/env python3
"""Read and index an AoE4 tuning-pack corpus without modifying it."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


XML_EXTENSIONS = {".aoe4mod", ".burnproj", ".locdb", ".rdo", ".xml"}
TEXT_EXTENSIONS = XML_EXTENSIONS | {".csv", ".md", ".txt", ".ucs"}
IGNORED_DIRECTORIES = {".aoe4", ".git", ".hg", ".svn", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hash every file and build XML/locdb indexes for an AoE4 tuning-pack corpus."
    )
    parser.add_argument("root", type=Path, help="Directory containing official and handmade tuning packs")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write the full report as JSON")
    parser.add_argument("--markdown", dest="markdown_path", type=Path, help="Write an auditable corpus manifest")
    parser.add_argument("--instances", dest="instances_path", type=Path, help="Write the instance index as TSV")
    parser.add_argument("--properties", dest="properties_path", type=Path, help="Write the property-path index as TSV")
    parser.add_argument("--exclude", action="append", default=[], help="Directory name to exclude; may repeat")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_guid(value: str | None) -> str:
    return re.sub(r"[^0-9a-f]", "", (value or "").lower())


def stream_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def decode_bytes(data: bytes, extension: str) -> tuple[str, str]:
    encodings = ("utf-16", "utf-8-sig", "utf-8", "cp1252") if extension == ".ucs" else (
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "cp1252",
    )
    for encoding in encodings:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1"


def iter_files(root: Path, excluded: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".tmp" or "~rf" in path.name.lower():
            continue
        relative = path.relative_to(root)
        if any(part in excluded or part in IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix().lower())


def find_text(root: ET.Element, name: str) -> str:
    for element in root.iter():
        if local_name(element.tag) == name:
            return (element.text or "").strip()
    return ""


def direct_named(root: ET.Element, tag: str, name: str) -> list[ET.Element]:
    return [
        child
        for child in root
        if local_name(child.tag) == tag and child.attrib.get("name") == name
    ]


def property_rows(
    element: ET.Element,
    prefix: tuple[str, ...] = (),
) -> Iterable[tuple[str, str]]:
    tag = local_name(element.tag)
    name = element.attrib.get("name") or element.attrib.get("value") if tag == "variant" else element.attrib.get("name")
    component = f"{tag}:{name}" if name else tag
    current = prefix + (component,)
    if "value" in element.attrib and tag not in {"instance", "variant"}:
        yield "/".join(current), element.attrib["value"]
    for child in element:
        yield from property_rows(child, current)


def inspect_instance(
    root: ET.Element,
    relative: Path,
    pack: str,
    sha256: str,
) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    parts = [part.lower() for part in relative.parts]
    instance_index = parts.index("instances")
    category = relative.parts[instance_index + 1]
    instance_relative = Path(*relative.parts[instance_index + 1 :]).with_suffix("").as_posix().replace("/", "\\")
    pbg_elements = direct_named(root, "uniqueid", "pbgid")
    parent_elements = direct_named(root, "instance_reference", "parent_pbg")
    variants = [child.attrib.get("name", "") for child in root if local_name(child.tag) == "variant"]
    references: set[tuple[str, str, str]] = set()
    custom_loc: set[tuple[str, str, str]] = set()
    list_actions: collections.Counter[str] = collections.Counter()
    override_count = 0
    for element in root.iter():
        tag = local_name(element.tag)
        if tag in {"instance_reference", "template_reference", "state_tree_node"}:
            value = element.attrib.get("value", "")
            if value:
                references.add((tag, element.attrib.get("name", ""), value))
        if tag == "locstring" and element.attrib.get("mod"):
            custom_loc.add(
                (
                    element.attrib.get("name", ""),
                    element.attrib.get("value", ""),
                    normalize_guid(element.attrib.get("mod")),
                )
            )
        if "overrideParent" in element.attrib:
            override_count += 1
        if "List.ListAction" in element.attrib:
            list_actions[element.attrib["List.ListAction"]] += 1

    properties = list(property_rows(root))
    record = {
        "pack": pack,
        "file": relative.as_posix(),
        "category": category,
        "instance_path": instance_relative,
        "template": root.attrib.get("template", ""),
        "version": root.attrib.get("version", ""),
        "description": root.attrib.get("description", ""),
        "pbgid": pbg_elements[0].attrib.get("value", "") if pbg_elements else "",
        "pbgid_count": len(pbg_elements),
        "parent_pbg": parent_elements[0].attrib.get("value", "") if parent_elements else "",
        "parent_pbg_count": len(parent_elements),
        "variants": variants,
        "reference_count": len(references),
        "reference_sample": [
            {"tag": tag, "name": name, "value": value}
            for tag, name, value in sorted(references)[:40]
        ],
        "custom_loc_count": len(custom_loc),
        "custom_loc_ids": sorted({value for _, value, _ in custom_loc})[:100],
        "custom_loc_mods": sorted({mod for _, _, mod in custom_loc}),
        "override_count": override_count,
        "list_actions": dict(sorted(list_actions.items())),
        "property_count": len(properties),
        "sha256": sha256,
    }
    return record, properties


def inspect_sga(data: bytes) -> dict[str, Any]:
    if not data.startswith(b"_ARCHIVE") or len(data) < 12:
        return {"valid_header": False}
    version = int.from_bytes(data[8:12], "little")
    name_bytes = data[12:140]
    try:
        archive_name = name_bytes.decode("utf-16-le", errors="ignore").split("\x00", 1)[0]
    except UnicodeError:
        archive_name = ""
    return {"valid_header": True, "version": version, "archive_name": archive_name}


def read_csv(text: str) -> tuple[list[str], list[dict[str, str]], str | None]:
    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        return headers, list(reader), None
    except csv.Error as exc:
        return [], [], str(exc)


def build_report(root: Path, excluded: set[str]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    instances: list[dict[str, Any]] = []
    extension_counts: collections.Counter[str] = collections.Counter()
    pack_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    category_counts: collections.Counter[str] = collections.Counter()
    template_counts: collections.Counter[str] = collections.Counter()
    property_index: dict[tuple[str, str], dict[str, Any]] = {}
    xml_errors: list[dict[str, Any]] = []
    csv_errors: list[dict[str, Any]] = []

    for path in iter_files(root, excluded):
        relative = path.relative_to(root)
        pack = relative.parts[0] if relative.parts else "[root]"
        source = "official-archive" if pack.lower() == "official" else "handmade"
        extension = path.suffix.lower() or "[none]"
        sha256 = stream_hash(path)
        record: dict[str, Any] = {
            "path": relative.as_posix(),
            "pack": pack,
            "source": source,
            "extension": extension,
            "bytes": path.stat().st_size,
            "sha256": sha256,
        }
        extension_counts[extension] += 1
        pack_counts[pack]["files"] += 1
        pack_counts[pack]["bytes"] += record["bytes"]
        pack_counts[pack][extension] += 1

        data: bytes | None = None
        if extension in TEXT_EXTENSIONS or extension == ".sga":
            data = path.read_bytes()
        if extension in TEXT_EXTENSIONS and data is not None:
            text, encoding = decode_bytes(data, extension)
            record["encoding"] = encoding
            record["lines"] = text.count("\n") + (1 if text else 0)
        else:
            text = ""

        if extension in XML_EXTENSIONS and data is not None:
            try:
                xml_root = ET.fromstring(data)
                record["xml_root"] = local_name(xml_root.tag)
                record["xml_elements"] = sum(1 for _ in xml_root.iter())
                if local_name(xml_root.tag) == "instance" and "instances" in [p.lower() for p in relative.parts]:
                    instance, properties = inspect_instance(xml_root, relative, pack, sha256)
                    instances.append(instance)
                    category_counts[instance["category"]] += 1
                    template_counts[instance["template"]] += 1
                    for property_path, value in properties:
                        key = (instance["category"], property_path)
                        details = property_index.setdefault(
                            key,
                            {
                                "category": instance["category"],
                                "property_path": property_path,
                                "count": 0,
                                "packs": set(),
                                "example_file": instance["file"],
                                "sample_values": [],
                            },
                        )
                        details["count"] += 1
                        details["packs"].add(pack)
                        if value not in details["sample_values"] and len(details["sample_values"]) < 5:
                            details["sample_values"].append(value)
                elif extension == ".aoe4mod":
                    record["mod_id"] = find_text(xml_root, "ID")
                    record["mod_type"] = find_text(xml_root, "Type")
                    record["locdb_path"] = find_text(xml_root, "LocDBPath")
                elif local_name(xml_root.tag) == "mod":
                    record["attrib_guid"] = xml_root.attrib.get("guid", "")
                    record["attrib_locdb_path"] = xml_root.attrib.get("locdb_path", "")
                    record["override_instances"] = xml_root.attrib.get("override_instances", "")
            except ET.ParseError as exc:
                error = {"file": relative.as_posix(), "error": str(exc)}
                xml_errors.append(error)
                record["xml_error"] = str(exc)
        elif extension == ".csv":
            headers, rows, error = read_csv(text)
            record["csv_headers"] = headers
            record["csv_rows"] = len(rows)
            if error:
                csv_errors.append({"file": relative.as_posix(), "error": error})
                record["csv_error"] = error
        elif extension == ".ucs":
            entries = [line for line in text.splitlines() if "\t" in line]
            record["ucs_entries"] = len(entries)
        elif extension == ".sga" and data is not None:
            record["sga"] = inspect_sga(data[:256])
        files.append(record)

    property_rows = []
    for details in property_index.values():
        property_rows.append(
            {
                **details,
                "packs": sorted(details["packs"]),
            }
        )
    property_rows.sort(key=lambda row: (row["category"].lower(), row["property_path"].lower()))

    pack_rows = []
    for pack, counts in sorted(pack_counts.items(), key=lambda item: item[0].lower()):
        pack_rows.append({"pack": pack, **dict(sorted(counts.items()))})

    return {
        "root": str(root.resolve()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "files": len(files),
            "bytes": sum(record["bytes"] for record in files),
            "lines": sum(record.get("lines", 0) for record in files),
            "instances": len(instances),
            "xml_errors": len(xml_errors),
            "csv_errors": len(csv_errors),
            "extensions": dict(sorted(extension_counts.items())),
            "categories": dict(sorted(category_counts.items())),
            "templates": dict(sorted(template_counts.items())),
        },
        "packs": pack_rows,
        "xml_errors": xml_errors,
        "csv_errors": csv_errors,
        "instances": instances,
        "properties": property_rows,
        "files": files,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Tuning-pack corpus manifest",
        "",
        "Generated by `scripts/analyze_tuning_corpus.py`. Every file listed below was read and hashed.",
        f"Source root: `{report['root']}`",
        f"Generated UTC: `{report['generated_at_utc']}`",
        "",
        "## Contents",
        "",
        "1. Coverage",
        "2. Pack inventory",
        "3. Attribute categories",
        "4. Source policy",
        "5. Complete file index",
        "",
        "## Coverage",
        "",
        f"- Files: {summary['files']}",
        f"- Bytes: {summary['bytes']}",
        f"- Text lines: {summary['lines']}",
        f"- Attribute instances: {summary['instances']}",
        f"- XML parse errors: {summary['xml_errors']}",
        f"- CSV parse errors: {summary['csv_errors']}",
        "",
        "## Pack inventory",
        "",
        "| Pack | Files | Bytes | XML | UCS | SGA |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pack in report["packs"]:
        lines.append(
            f"| {pack['pack']} | {pack.get('files', 0)} | {pack.get('bytes', 0)} | {pack.get('.xml', 0)} | {pack.get('.ucs', 0)} | {pack.get('.sga', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Attribute categories",
            "",
            "| Category | Instances |",
            "| --- | ---: |",
        ]
    )
    for category, count in summary["categories"].items():
        lines.append(f"| `{category}` | {count} |")
    lines.extend(
        [
            "",
            "## Source policy",
            "",
            "Treat `official/Attrib.sga` and current Attribute Editor/base-data evidence as authoritative. Treat extracted handmade XML as secondary implementation examples. Generated cache, UCS, RRTEX, BIN, and SGA files are build outputs, not edit targets.",
            "",
            "## Complete file index",
            "",
            "| Source | Pack | File | Lines | Bytes | SHA-256 |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for record in report["files"]:
        lines.append(
            f"| {record['source']} | {record['pack']} | `{record['path']}` | {record.get('lines', '-')} | {record['bytes']} | `{record['sha256'][:12]}` |"
        )
    return "\n".join(lines) + "\n"


def instance_tsv(report: dict[str, Any]) -> str:
    headers = [
        "pack",
        "file",
        "category",
        "instance_path",
        "template",
        "version",
        "pbgid",
        "parent_pbg",
        "variants",
        "references",
        "custom_loc_refs",
        "properties",
        "sha256",
    ]
    rows = ["\t".join(headers)]
    for item in report["instances"]:
        rows.append(
            "\t".join(
                [
                    item["pack"],
                    item["file"],
                    item["category"],
                    item["instance_path"],
                    item["template"],
                    item["version"],
                    item["pbgid"],
                    item["parent_pbg"],
                    ",".join(item["variants"]),
                    str(item["reference_count"]),
                    str(item["custom_loc_count"]),
                    str(item["property_count"]),
                    item["sha256"],
                ]
            )
        )
    return "\n".join(rows) + "\n"


def property_tsv(report: dict[str, Any]) -> str:
    rows = ["category\tproperty_path\tcount\tpack_count\tpacks\texample_file\tsample_values"]
    for item in report["properties"]:
        rows.append(
            "\t".join(
                [
                    item["category"],
                    item["property_path"],
                    str(item["count"]),
                    str(len(item["packs"])),
                    ",".join(item["packs"]),
                    item["example_file"],
                    " | ".join(value.replace("\t", " ").replace("\n", " ") for value in item["sample_values"]),
                ]
            )
        )
    return "\n".join(rows) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Corpus root is not a directory: {root}")
    report = build_report(root, set(args.exclude))
    if args.json_path:
        write_text(args.json_path, json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    if args.markdown_path:
        write_text(args.markdown_path, markdown_report(report))
    if args.instances_path:
        write_text(args.instances_path, instance_tsv(report))
    if args.properties_path:
        write_text(args.properties_path, property_tsv(report))
    print(json.dumps(report["summary"], indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
