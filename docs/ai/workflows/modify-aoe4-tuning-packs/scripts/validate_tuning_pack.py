#!/usr/bin/env python3
"""Statically validate one or more Age of Empires IV tuning-pack projects."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IGNORED_DIRECTORIES = {".aoe4", ".git", ".hg", ".svn", "__pycache__", "cache"}
GUID_RE = re.compile(r"^[0-9a-f]{32}$")
INTEGER_TAGS = {"int", "locstring", "uniqueid"}
REFERENCE_TAGS = {"instance_reference", "state_tree_node", "template_reference"}


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    file: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate editable sources in AoE4 Attribute Editor tuning packs."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Pack directory, .aoe4mod file, or directory containing multiple packs",
    )
    parser.add_argument("--json", dest="json_path", type=Path, help="Write a JSON report; use - for stdout")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a failure exit code for warnings as well as errors",
    )
    parser.add_argument(
        "--allow-external-loc-guid",
        action="append",
        default=[],
        metavar="GUID",
        help="Allow an intentional foreign custom-loc GUID; may repeat",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_guid(value: str | None) -> str:
    return re.sub(r"[^0-9a-f]", "", (value or "").lower())


def ignored(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    parts = {part.lower() for part in relative.parts[:-1]}
    return bool(parts & IGNORED_DIRECTORIES) or path.suffix.lower() == ".tmp" or "~rf" in path.name.lower()


def discover_packs(path: Path) -> list[tuple[Path, Path]]:
    path = path.resolve()
    if path.is_file():
        return [(path.parent, path)] if path.suffix.lower() == ".aoe4mod" else []
    direct = sorted(path.glob("*.aoe4mod"), key=lambda item: item.name.lower())
    if direct:
        return [(path, manifest) for manifest in direct]
    manifests = [
        item
        for item in path.rglob("*.aoe4mod")
        if item.is_file() and not ignored(item, path)
    ]
    return [(item.parent, item) for item in sorted(manifests, key=lambda item: str(item).lower())]


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


def portable_join(base: Path, value: str) -> Path:
    parts = [part for part in re.split(r"[\\/]", value.strip()) if part and part != "."]
    path = base
    for part in parts:
        path = path.parent if part == ".." else path / part
    return path.resolve()


def read_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16", "utf-8-sig", "utf-8", "cp1252")
    elif data.count(b"\x00") > max(4, len(data) // 10):
        encodings = ("utf-16-le", "utf-16-be", "utf-8-sig", "utf-8", "cp1252")
    else:
        encodings = ("utf-8-sig", "utf-8", "utf-16", "cp1252")
    for encoding in encodings:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1"


def parse_xml(path: Path, diagnostics: list[Diagnostic], label: str) -> ET.Element | None:
    try:
        return ET.fromstring(path.read_bytes())
    except (OSError, ET.ParseError) as exc:
        diagnostics.append(Diagnostic("error", "XML_PARSE", str(path), f"Cannot parse {label}: {exc}"))
        return None


def expected_guid_parts(guid: str) -> list[int]:
    data = uuid.UUID(guid).bytes_le
    return [int.from_bytes(data[offset : offset + 4], "little") for offset in range(0, 16, 4)]


def require_integer(
    value: str,
    path: Path,
    field: str,
    diagnostics: list[Diagnostic],
    *,
    signed32: bool = False,
) -> int | None:
    try:
        number = int(value, 10)
    except ValueError:
        diagnostics.append(Diagnostic("error", "INVALID_INTEGER", str(path), f"{field} must be an integer, got {value!r}."))
        return None
    if signed32 and not -(2**31) <= number < 2**31:
        diagnostics.append(Diagnostic("error", "INTEGER_RANGE", str(path), f"{field}={number} is outside signed 32-bit range."))
    return number


def read_locdb(
    locdb_path: Path,
    diagnostics: list[Diagnostic],
) -> tuple[dict[str, set[str]], set[str]]:
    root = parse_xml(locdb_path, diagnostics, "locdb metadata")
    if root is None:
        return {}, set()
    locales: list[str] = []
    for element in root.iter():
        if local_name(element.tag) != "Locale":
            continue
        name = next(
            ((child.text or "").strip() for child in element if local_name(child.tag) == "Name"),
            "",
        )
        if name:
            locales.append(name)
    if not locales:
        diagnostics.append(Diagnostic("error", "LOCDB_NO_LOCALES", str(locdb_path), "Locdb metadata declares no locales."))

    ids_by_locale: dict[str, set[str]] = {}
    all_ids: set[str] = set()
    for locale in locales:
        csv_path = locdb_path.with_name(f"{locdb_path.stem}_{locale}.csv")
        if not csv_path.is_file():
            diagnostics.append(Diagnostic("error", "MISSING_LOCALE_CSV", str(csv_path), f"Locale {locale!r} has no source CSV."))
            continue
        try:
            text, _ = read_text(csv_path)
            reader = csv.DictReader(io.StringIO(text, newline=""))
            headers = reader.fieldnames or []
            if "ID" not in headers or not ({"Text", "TranslatedText"} & set(headers)):
                diagnostics.append(Diagnostic("error", "LOCDB_CSV_COLUMNS", str(csv_path), "Locale CSV must contain ID plus Text or TranslatedText."))
                continue
            ids: list[str] = []
            text_column = "Text" if "Text" in headers else "TranslatedText"
            for row_number, row in enumerate(reader, start=2):
                identifier = (row.get("ID") or "").strip()
                if not identifier:
                    diagnostics.append(Diagnostic("error", "EMPTY_LOC_ID", str(csv_path), f"Row {row_number} has an empty ID."))
                    continue
                require_integer(identifier, csv_path, f"row {row_number} ID", diagnostics, signed32=True)
                ids.append(identifier)
                localized_text = row.get(text_column) or ""
                if re.search(
                    r"<(?:instance|locstring|group|list|float|int|bool|template_reference|instance_reference)\b",
                    localized_text,
                    flags=re.IGNORECASE,
                ):
                    diagnostics.append(
                        Diagnostic(
                            "warning",
                            "LOC_TEXT_XML_FRAGMENT",
                            str(csv_path),
                            f"Row {row_number} (ID {identifier}) contains an apparent attribute-XML fragment in localization text.",
                        )
                    )
            duplicate_ids = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
            for identifier in duplicate_ids:
                diagnostics.append(Diagnostic("error", "DUPLICATE_LOC_ID", str(csv_path), f"Localization ID {identifier} occurs more than once."))
            ids_by_locale[locale] = set(ids)
            all_ids.update(ids)
        except (OSError, csv.Error) as exc:
            diagnostics.append(Diagnostic("error", "LOCDB_CSV_PARSE", str(csv_path), f"Cannot parse locale CSV: {exc}"))

    if len(ids_by_locale) > 1:
        union = set().union(*ids_by_locale.values())
        for locale, identifiers in sorted(ids_by_locale.items()):
            missing = sorted(union - identifiers, key=lambda item: int(item))
            if missing:
                sample = ", ".join(missing[:8])
                diagnostics.append(Diagnostic("warning", "LOCALE_ID_DRIFT", str(locdb_path), f"Locale {locale!r} is missing {len(missing)} ID(s): {sample}."))
    return ids_by_locale, all_ids


def validate_rdo(
    rdo_path: Path,
    guid: str,
    loc_ids: set[str],
    diagnostics: list[Diagnostic],
) -> None:
    if not rdo_path.is_file():
        diagnostics.append(Diagnostic("error", "MISSING_MOD_RDO", str(rdo_path), "Editable assets/mod.rdo is missing."))
        return
    root = parse_xml(rdo_path, diagnostics, "mod RDO")
    if root is None:
        return
    expected = expected_guid_parts(guid)
    reflect_objects = [
        element
        for element in root.iter()
        if local_name(element.tag) == "DataObject" and element.attrib.get("Type") == "util::ReflectLocString"
    ]
    if not reflect_objects:
        diagnostics.append(Diagnostic("warning", "RDO_NO_LOC_OBJECTS", str(rdo_path), "No util::ReflectLocString objects were found."))
    for reflect in reflect_objects:
        properties = {
            element.attrib.get("Name", ""): element.attrib.get("Value", "")
            for element in reflect
            if local_name(element.tag) == "DataProperty"
        }
        for index, expected_value in enumerate(expected):
            field = f"m_modPart{index}"
            actual = properties.get(field)
            if actual is None:
                diagnostics.append(Diagnostic("error", "RDO_GUID_PART_MISSING", str(rdo_path), f"ReflectLocString object is missing {field}."))
                continue
            value = require_integer(actual, rdo_path, field, diagnostics)
            if value is not None and value != expected_value:
                diagnostics.append(Diagnostic("error", "RDO_GUID_MISMATCH", str(rdo_path), f"{field} is {value}, expected {expected_value} from project GUID."))
        loc_key = properties.get("m_locStringKey")
        if loc_key is None:
            diagnostics.append(Diagnostic("error", "RDO_LOC_KEY_MISSING", str(rdo_path), "ReflectLocString object has no m_locStringKey."))
        elif require_integer(loc_key, rdo_path, "m_locStringKey", diagnostics, signed32=True) is not None and loc_ids and loc_key not in loc_ids:
            diagnostics.append(Diagnostic("error", "RDO_LOC_ID_MISSING", str(rdo_path), f"Localization ID {loc_key} is absent from the locale CSV source."))


def validate_scalar_values(path: Path, root: ET.Element, diagnostics: list[Diagnostic]) -> None:
    for element in root.iter():
        tag = local_name(element.tag)
        if "overrideParent" in element.attrib and element.attrib["overrideParent"] not in {"True", "False"}:
            diagnostics.append(Diagnostic("error", "INVALID_BOOLEAN", str(path), f"overrideParent must be True or False, got {element.attrib['overrideParent']!r}."))
        if "List.ListAction" in element.attrib and element.attrib["List.ListAction"] not in {"Append", "Remove"}:
            diagnostics.append(Diagnostic("warning", "UNKNOWN_LIST_ACTION", str(path), f"Unrecognized List.ListAction {element.attrib['List.ListAction']!r}."))
        for attribute in ("List.ItemID", "List.ParentItemID"):
            if attribute in element.attrib:
                require_integer(element.attrib[attribute], path, attribute, diagnostics, signed32=True)
        value = element.attrib.get("value")
        if value is None or value == "":
            continue
        if tag == "bool" and value not in {"True", "False"}:
            diagnostics.append(Diagnostic("error", "INVALID_BOOLEAN", str(path), f"Boolean {element.attrib.get('name', '')!r} has value {value!r}."))
        elif tag == "colour":
            # Attribute Editor uses * as an inherited/automatic colour sentinel.
            if value != "*":
                require_integer(value, path, f"colour {element.attrib.get('name', '')!r}", diagnostics)
        elif tag in INTEGER_TAGS:
            require_integer(value, path, f"{tag} {element.attrib.get('name', '')!r}", diagnostics, signed32=tag in {"int", "locstring"})
        elif tag == "float":
            try:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError
            except ValueError:
                diagnostics.append(Diagnostic("error", "INVALID_FLOAT", str(path), f"Float {element.attrib.get('name', '')!r} has value {value!r}."))


def validate_lists(path: Path, root: ET.Element, diagnostics: list[Diagnostic]) -> None:
    for list_element in (element for element in root.iter() if local_name(element.tag) == "list"):
        by_id: dict[str, list[ET.Element]] = defaultdict(list)
        for child in list_element:
            item_id = child.attrib.get("List.ItemID")
            if item_id is not None:
                by_id[item_id].append(child)
            parent_id = child.attrib.get("List.ParentItemID")
            action = child.attrib.get("List.ListAction")
            if action == "Append" and item_id is None:
                diagnostics.append(Diagnostic("error", "APPEND_WITHOUT_ITEM_ID", str(path), f"List {list_element.attrib.get('name', '')!r} appends an item without List.ItemID."))
            if action == "Append" and parent_id is not None:
                diagnostics.append(Diagnostic("warning", "APPEND_WITH_PARENT_ID", str(path), f"List {list_element.attrib.get('name', '')!r} combines Append with List.ParentItemID; verify this contradictory identity against the current parent."))
            if parent_id is not None and item_id is None:
                diagnostics.append(Diagnostic("error", "PARENT_ID_WITHOUT_ITEM_ID", str(path), f"List {list_element.attrib.get('name', '')!r} uses List.ParentItemID without List.ItemID."))
        for item_id, elements in sorted(by_id.items()):
            if len(elements) > 1:
                diagnostics.append(Diagnostic("error", "DUPLICATE_LIST_ITEM_ID", str(path), f"List {list_element.attrib.get('name', '')!r} repeats List.ItemID {item_id}."))


def normalize_instance_path(value: str) -> str:
    return re.sub(r"[\\/]+", r"\\", value.strip().lower()).removesuffix(".xml")


def validate_instances(
    instance_root: Path,
    pack_guid: str,
    loc_ids: set[str],
    allowed_external_loc_guids: set[str],
    diagnostics: list[Diagnostic],
) -> tuple[int, int]:
    if not instance_root.is_dir():
        diagnostics.append(Diagnostic("warning", "NO_INSTANCES", str(instance_root), "Pack has no editable attribute instances."))
        return 0, 0
    files = [
        path
        for path in instance_root.rglob("*.xml")
        if path.is_file() and not ignored(path, instance_root)
    ]
    local_instances = {
        normalize_instance_path(str(path.relative_to(instance_root)))
        for path in files
    }
    pbg_files: dict[str, list[tuple[Path, int | None]]] = defaultdict(list)
    unresolved: set[tuple[str, str, str]] = set()
    own_mod_missing: set[tuple[Path, str, str, str]] = set()
    external_mods: set[str] = set()

    for path in sorted(files, key=lambda item: str(item).lower()):
        root = parse_xml(path, diagnostics, "attribute instance")
        if root is None:
            continue
        if local_name(root.tag) != "instance":
            diagnostics.append(Diagnostic("error", "INSTANCE_ROOT", str(path), f"Expected <instance>, found <{local_name(root.tag)}>."))
            continue
        relative = path.relative_to(instance_root)
        category = relative.parts[0] if relative.parts else ""
        template = root.attrib.get("template", "")
        if not template:
            diagnostics.append(Diagnostic("error", "MISSING_TEMPLATE", str(path), "Instance root has no template."))
        elif not (template.lower() == category.lower() or template.lower().startswith(category.lower() + "\\")):
            diagnostics.append(Diagnostic("error", "CATEGORY_TEMPLATE_MISMATCH", str(path), f"Path category {category!r} does not agree with template {template!r}."))
        if root.attrib.get("version") not in {"4", "6"}:
            diagnostics.append(Diagnostic("warning", "UNSEEN_INSTANCE_VERSION", str(path), f"Instance version {root.attrib.get('version')!r} was not observed in the supplied corpus."))

        pbg_elements = direct_named(root, "uniqueid", "pbgid")
        if len(pbg_elements) != 1:
            diagnostics.append(Diagnostic("error", "ROOT_PBG_COUNT", str(path), f"Instance must have exactly one root pbgid; found {len(pbg_elements)}."))
            root_pbg = ""
        else:
            root_pbg = pbg_elements[0].attrib.get("value", "")
            if require_integer(root_pbg, path, "root pbgid", diagnostics) is not None:
                text, _ = read_text(path)
                line_number = next(
                    (
                        number
                        for number, line in enumerate(text.splitlines(), start=1)
                        if "<uniqueid" in line
                        and 'name="pbgid"' in line
                        and f'value="{root_pbg}"' in line
                    ),
                    None,
                )
                pbg_files[root_pbg].append((path, line_number))

        for variant in (child for child in root if local_name(child.tag) == "variant"):
            variant_pbgs = direct_named(variant, "uniqueid", "pbgid")
            if len(variant_pbgs) > 1:
                diagnostics.append(Diagnostic("error", "VARIANT_PBG_COUNT", str(path), f"Variant {variant.attrib.get('name', '')!r} has more than one pbgid."))
            for variant_pbg in variant_pbgs:
                value = variant_pbg.attrib.get("value", "")
                if root_pbg and value != root_pbg:
                    diagnostics.append(Diagnostic("error", "VARIANT_PBG_MISMATCH", str(path), f"Variant {variant.attrib.get('name', '')!r} pbgid {value!r} differs from root {root_pbg!r}."))

        validate_scalar_values(path, root, diagnostics)
        validate_lists(path, root, diagnostics)
        for element in root.iter():
            tag = local_name(element.tag)
            mod = normalize_guid(element.attrib.get("mod"))
            if mod and mod != pack_guid:
                external_mods.add(mod)
            if tag == "locstring" and mod:
                value = element.attrib.get("value", "")
                if mod != pack_guid and mod not in allowed_external_loc_guids:
                    diagnostics.append(Diagnostic("error", "LOCSTRING_GUID_MISMATCH", str(path), f"Custom locstring {value!r} uses mod GUID {mod}, expected {pack_guid}."))
                if mod == pack_guid and value and value != "0" and loc_ids and value not in loc_ids:
                    diagnostics.append(Diagnostic("error", "CUSTOM_LOC_ID_MISSING", str(path), f"Custom localization ID {value} is absent from locale CSV source."))
            if tag in REFERENCE_TAGS:
                value = element.attrib.get("value", "")
                normalized = normalize_instance_path(value)
                if value and "\\" in normalized and normalized not in local_instances:
                    unresolved.add((tag, element.attrib.get("name", ""), value))
                    if mod == pack_guid:
                        own_mod_missing.add((path, tag, element.attrib.get("name", ""), value))

    for pbgid, paths in sorted(pbg_files.items(), key=lambda item: int(item[0])):
        if len(paths) > 1:
            names = ", ".join(
                f"{path.relative_to(instance_root)}{f':{line}' if line else ''}"
                for path, line in paths
            )
            diagnostics.append(Diagnostic("error", "DUPLICATE_PBG_ID", str(instance_root), f"Root pbgid {pbgid} is used by {len(paths)} instances: {names}. Reallocate one instance through the Attribute Editor; do not hand-pick an ID."))

    missing_by_file: dict[Path, list[tuple[str, str, str]]] = defaultdict(list)
    for path, tag, name, value in sorted(own_mod_missing, key=lambda item: tuple(map(str, item))):
        missing_by_file[path].append((tag, name, value))
    for path, references in missing_by_file.items():
        sample = "; ".join(f"{tag}:{name}={value}" for tag, name, value in references[:5])
        diagnostics.append(Diagnostic("error", "OWN_MOD_REFERENCE_MISSING", str(path), f"{len(references)} reference(s) explicitly target this pack GUID but have no local instance: {sample}."))

    if unresolved:
        by_tag = Counter(tag for tag, _, _ in unresolved)
        breakdown = ", ".join(f"{tag}={count}" for tag, count in sorted(by_tag.items()))
        sample = "; ".join(
            f"{tag}:{name}={value}" for tag, name, value in sorted(unresolved)[:5]
        )
        diagnostics.append(Diagnostic("info", "UNRESOLVED_REFERENCE_SUMMARY", str(instance_root), f"{len(unresolved)} reference value(s) are not defined inside this pack ({breakdown}). Sample: {sample}. Treat them as unresolved evidence and verify changed values in the current Attribute Editor or official data."))
    if external_mods:
        diagnostics.append(Diagnostic("warning", "EXTERNAL_MOD_REFERENCES", str(instance_root), f"Pack references {len(external_mods)} external mod GUID(s): {', '.join(sorted(external_mods))}. Verify dependency availability and load order."))
    return len(files), len(unresolved)


def validate_pack(
    pack_root: Path,
    project_path: Path,
    allowed_external_loc_guids: set[str],
) -> dict[str, object]:
    diagnostics: list[Diagnostic] = []
    project = parse_xml(project_path, diagnostics, "project manifest")
    if project is None:
        return {"pack": str(pack_root), "project": str(project_path), "instances": 0, "unresolved_references": 0, "diagnostics": diagnostics}

    guid_text = find_text(project, "ID")
    guid = normalize_guid(guid_text)
    if not GUID_RE.fullmatch(guid):
        diagnostics.append(Diagnostic("error", "INVALID_PROJECT_GUID", str(project_path), f"Project ID {guid_text!r} is not a GUID."))
        return {"pack": str(pack_root), "project": str(project_path), "instances": 0, "unresolved_references": 0, "diagnostics": diagnostics}
    if find_text(project, "Type") != "Extension":
        diagnostics.append(Diagnostic("warning", "PROJECT_TYPE", str(project_path), f"Expected tuning-pack Type 'Extension', found {find_text(project, 'Type')!r}."))

    generic_value = find_text(project, "DataGenericPath") or "assets"
    generic_root = portable_join(pack_root, generic_value)
    if not generic_root.is_dir():
        diagnostics.append(Diagnostic("error", "MISSING_ASSETS", str(project_path), f"DataGenericPath resolves to missing directory {generic_root}."))
    locdb_value = find_text(project, "LocDBPath")
    locdb_path = portable_join(generic_root, locdb_value) if locdb_value else generic_root / "locdb" / f"{project_path.stem}.locdb"
    if not locdb_value:
        diagnostics.append(Diagnostic("error", "MISSING_LOCDB_PATH", str(project_path), "Project manifest has no LocDBPath."))
    if not locdb_path.is_file():
        diagnostics.append(Diagnostic("error", "MISSING_LOCDB", str(locdb_path), "Project LocDBPath does not resolve to a file."))
        loc_ids: set[str] = set()
    else:
        _, loc_ids = read_locdb(locdb_path, diagnostics)

    attrib_dir = generic_root / "attrib"
    attrib_manifests: list[tuple[Path, ET.Element]] = []
    if attrib_dir.is_dir():
        for path in sorted(attrib_dir.glob("*.xml"), key=lambda item: item.name.lower()):
            root = parse_xml(path, diagnostics, "attribute manifest")
            if root is not None and local_name(root.tag) == "mod":
                attrib_manifests.append((path, root))
    if len(attrib_manifests) != 1:
        diagnostics.append(Diagnostic("error", "ATTRIB_MANIFEST_COUNT", str(attrib_dir), f"Expected exactly one direct attribute <mod> manifest; found {len(attrib_manifests)}."))
    for attrib_path, attrib in attrib_manifests:
        attrib_guid = normalize_guid(attrib.attrib.get("guid"))
        if attrib_guid != guid:
            diagnostics.append(Diagnostic("error", "ATTRIB_GUID_MISMATCH", str(attrib_path), f"Attribute GUID {attrib_guid!r} does not match project GUID {guid}."))
        attrib_locdb = portable_join(attrib_path.parent, attrib.attrib.get("locdb_path", ""))
        if attrib_locdb != locdb_path:
            diagnostics.append(Diagnostic("error", "ATTRIB_LOCDB_MISMATCH", str(attrib_path), f"Attribute locdb_path resolves to {attrib_locdb}, expected {locdb_path}."))
        if attrib.attrib.get("override_instances") != "True":
            diagnostics.append(Diagnostic("warning", "OVERRIDE_INSTANCES", str(attrib_path), "Tuning-pack attribute manifest does not set override_instances=\"True\"."))

    validate_rdo(generic_root / "mod.rdo", guid, loc_ids, diagnostics)
    instance_count, unresolved_count = validate_instances(
        attrib_dir / "instances",
        guid,
        loc_ids,
        allowed_external_loc_guids,
        diagnostics,
    )
    return {
        "pack": str(pack_root),
        "project": str(project_path),
        "guid": guid,
        "instances": instance_count,
        "unresolved_references": unresolved_count,
        "diagnostics": diagnostics,
    }


def severity_order(diagnostic: Diagnostic) -> tuple[int, str, str]:
    return ({"error": 0, "warning": 1, "info": 2}[diagnostic.severity], diagnostic.file.lower(), diagnostic.code)


def main() -> int:
    args = parse_args()
    packs: dict[tuple[Path, Path], None] = {}
    for path in args.paths:
        if not path.exists():
            print(f"ERROR INPUT_NOT_FOUND {path}: path does not exist", file=sys.stderr)
            return 2
        for pair in discover_packs(path):
            packs[pair] = None
    if not packs:
        print("ERROR NO_PACKS: no .aoe4mod project manifests found", file=sys.stderr)
        return 2

    allowed_external_loc_guids = {
        normalize_guid(value) for value in args.allow_external_loc_guid
    }
    invalid_allowed_guids = sorted(
        value for value in allowed_external_loc_guids if not GUID_RE.fullmatch(value)
    )
    if invalid_allowed_guids:
        print(
            f"ERROR INVALID_ALLOWED_GUID: {', '.join(invalid_allowed_guids)}",
            file=sys.stderr,
        )
        return 2
    reports = [
        validate_pack(pack_root, project_path, allowed_external_loc_guids)
        for pack_root, project_path in packs
    ]
    all_diagnostics = [diagnostic for report in reports for diagnostic in report["diagnostics"]]
    counts = Counter(diagnostic.severity for diagnostic in all_diagnostics)
    serializable = {
        "summary": {
            "packs": len(reports),
            "instances": sum(int(report["instances"]) for report in reports),
            "errors": counts["error"],
            "warnings": counts["warning"],
            "info": counts["info"],
        },
        "packs": [
            {**report, "diagnostics": [asdict(item) for item in report["diagnostics"]]}
            for report in reports
        ],
    }
    if args.json_path == Path("-"):
        print(json.dumps(serializable, indent=2))
    else:
        for diagnostic in sorted(all_diagnostics, key=severity_order):
            print(f"{diagnostic.severity.upper()} {diagnostic.code} {diagnostic.file}: {diagnostic.message}")
        print(
            f"Validated {len(reports)} pack(s), {sum(int(report['instances']) for report in reports)} instance(s): "
            f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['info']} info."
        )
    if args.json_path and args.json_path != Path("-"):
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return 1 if counts["error"] or (args.strict and counts["warning"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
