#!/usr/bin/env python3
"""Conservative static validation for AoE4 SCAR and game-mode RDO files."""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SYMBOL_INDEX = SCRIPT_DIR.parent / "references" / "scar-symbol-provenance.tsv"

LUA_BUILTINS = {
    "assert",
    "collectgarbage",
    "dofile",
    "error",
    "getfenv",
    "getmetatable",
    "ipairs",
    "load",
    "loadfile",
    "loadstring",
    "math.abs",
    "math.acos",
    "math.asin",
    "math.atan",
    "math.ceil",
    "math.cos",
    "math.deg",
    "math.exp",
    "math.floor",
    "math.fmod",
    "math.frexp",
    "math.huge",
    "math.ldexp",
    "math.log",
    "math.max",
    "math.min",
    "math.modf",
    "math.pow",
    "math.rad",
    "math.random",
    "math.randomseed",
    "math.sin",
    "math.sqrt",
    "math.tan",
    "next",
    "pairs",
    "pcall",
    "print",
    "rawequal",
    "rawget",
    "rawset",
    "require",
    "select",
    "setfenv",
    "setmetatable",
    "string.byte",
    "string.char",
    "string.find",
    "string.format",
    "string.gmatch",
    "string.gsub",
    "string.len",
    "string.lower",
    "string.match",
    "string.rep",
    "string.reverse",
    "string.sub",
    "string.upper",
    "table.concat",
    "table.insert",
    "table.remove",
    "table.sort",
    "table.unpack",
    "tonumber",
    "tostring",
    "type",
    "unpack",
    "xpcall",
}

FUNCTION_DEF_RE = re.compile(r"\b(?:local\s+)?function\s+([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(")
ASSIGNED_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_\.:]*)\s*=\s*function\s*\(")
CALL_RE = re.compile(r"(?<![\w\.])([A-Za-z_][A-Za-z0-9_\.:]*)\s*\(")
IMPORT_RE = re.compile(r"\bimport\s*\(\s*[\"']([^\"']+)[\"']\s*\)")
MODULE_RE = re.compile(r"\bCore_RegisterModule\s*\(\s*[\"']([^\"']+)[\"']")
NETWORK_REGISTER_RE = re.compile(r"\bNetwork_RegisterEvent\s*\(\s*[\"']([^\"']+)[\"']")
NETWORK_CALL_RE = re.compile(r"\bNetwork_CallEvent\s*\(\s*[\"']([^\"']+)[\"']")
RULE_ADD_RE = re.compile(
    r"\b(Rule_AddGlobalEvent|Rule_AddInterval(?:WithDelay)?|Rule_AddOneShot|Rule_AddEvent|Rule_AddEntityEvent|Rule_AddSquadEvent|Rule_AddEGroupEvent|Rule_AddSGroupEvent|Rule_AddPlayerEvent)\s*\(\s*([A-Za-z_][A-Za-z0-9_\.:]*)"
)
RULE_REMOVE_RE = re.compile(
    r"\b(Rule_RemoveGlobalEvent|Rule_RemoveEvent|Rule_RemoveEntityEvent|Rule_RemoveSquadEvent|Rule_RemoveEGroupEvent|Rule_RemoveSGroupEvent|Rule_RemovePlayerEvent|Rule_Remove)\s*\(\s*([A-Za-z_][A-Za-z0-9_\.:]*)"
)
PLAYER_SQUADS_ASSIGN_RE = re.compile(
    r"\blocal\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*Player_GetSquads\s*\("
)
RDO_ENTRY_RE = re.compile(r'<DataProperty\s+Name="m_scarWinConditionFile"[^>]*\sValue="([^"]*)"')
RDO_KEY_RE = re.compile(r'<DataProperty\s+Name="m_key"[^>]*\sValue="([^"]*)"')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Statically validate AoE4 .scar, .lua, and game-mode .rdo files.")
    parser.add_argument("files", nargs="+", type=Path, help="Files to validate")
    parser.add_argument("--project-root", type=Path, help="Scan local .scar helpers and network registrations")
    parser.add_argument("--symbol-index", type=Path, default=DEFAULT_SYMBOL_INDEX)
    parser.add_argument("--json", dest="json_path", type=Path, help="Write diagnostics as JSON")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for warnings as well as errors")
    return parser.parse_args()


def decode_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def strip_lua_comments_and_strings(text: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(text):
        comment_match = re.match(r"--\[(=*)\[", text[index:])
        if comment_match:
            closer = "]" + comment_match.group(1) + "]"
            end = text.find(closer, index + len(comment_match.group(0)))
            end = len(text) - len(closer) if end == -1 else end
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
            while index < len(text):
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
            closer = "]" + string_match.group(1) + "]"
            end = text.find(closer, index + len(string_match.group(0)))
            end = len(text) - len(closer) if end == -1 else end
            chunk = text[index : end + len(closer)]
            result.append("\n" * chunk.count("\n"))
            index = end + len(closer)
            continue
        result.append(text[index])
        index += 1
    return "".join(result)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def diagnostic(severity: str, code: str, message: str, line: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if line is not None:
        result["line"] = line
    return result


def load_symbol_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return rows
    headers = lines[0].split("\t")
    for raw in lines[1:]:
        values = raw.split("\t")
        values.extend([""] * (len(headers) - len(values)))
        row = dict(zip(headers, values))
        row["official_calls"] = int(row.get("official_calls") or 0)
        row["unofficial_calls"] = int(row.get("unofficial_calls") or 0)
        rows[row["symbol"]] = row
    return rows


def collect_project_context(root: Path | None) -> tuple[set[str], set[str], str]:
    definitions: set[str] = set()
    network_events: set[str] = set()
    combined: list[str] = []
    if root is None or not root.is_dir():
        return definitions, network_events, ""
    for path in sorted(root.rglob("*.scar")):
        if any(part in {".git", "aoe4-game-mode-skill"} for part in path.parts):
            continue
        text = decode_text(path)
        clean = strip_lua_comments_and_strings(text)
        definitions.update(FUNCTION_DEF_RE.findall(clean))
        definitions.update(ASSIGNED_FUNCTION_RE.findall(clean))
        network_events.update(NETWORK_REGISTER_RE.findall(text))
        combined.append(text)
    return definitions, network_events, "\n".join(combined)


def validate_delimiters(clean: str) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for index, char in enumerate(clean):
        if char in "([{":
            stack.append((char, index))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                diagnostics.append(
                    diagnostic("error", "delimiter-mismatch", f"Unexpected closing delimiter `{char}`.", line_number(clean, index))
                )
            else:
                stack.pop()
    for char, index in stack:
        diagnostics.append(
            diagnostic("error", "delimiter-unclosed", f"Unclosed delimiter `{char}`.", line_number(clean, index))
        )
    return diagnostics


def validate_lua_blocks(clean: str) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    token_re = re.compile(r"\b(function|elseif|if|for|while|do|repeat|end|until)\b")
    for match in token_re.finditer(clean):
        token = match.group(1)
        line = line_number(clean, match.start())
        if token in {"function", "if", "repeat"}:
            stack.append({"kind": token, "line": line, "awaiting_do": False})
        elif token in {"for", "while"}:
            stack.append({"kind": token, "line": line, "awaiting_do": True})
        elif token == "elseif":
            continue
        elif token == "do":
            if stack and stack[-1]["kind"] in {"for", "while"} and stack[-1]["awaiting_do"]:
                stack[-1]["awaiting_do"] = False
            else:
                stack.append({"kind": "do", "line": line, "awaiting_do": False})
        elif token == "until":
            if not stack or stack[-1]["kind"] != "repeat":
                diagnostics.append(diagnostic("error", "lua-block", "`until` has no matching `repeat`.", line))
            else:
                stack.pop()
        elif token == "end":
            if not stack:
                diagnostics.append(diagnostic("error", "lua-block", "`end` has no matching block opener.", line))
            elif stack[-1]["kind"] == "repeat":
                diagnostics.append(
                    diagnostic("error", "lua-block", "A `repeat` block must close with `until`, not `end`.", line)
                )
                stack.pop()
            else:
                stack.pop()
    for item in stack:
        diagnostics.append(
            diagnostic("error", "lua-block", f"Unclosed `{item['kind']}` block.", item["line"])
        )
    return diagnostics


def validate_script(
    path: Path,
    text: str,
    symbol_index: dict[str, dict[str, Any]],
    project_definitions: set[str],
    project_network_events: set[str],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    clean = strip_lua_comments_and_strings(text)
    diagnostics.extend(validate_delimiters(clean))
    diagnostics.extend(validate_lua_blocks(clean))

    definitions = FUNCTION_DEF_RE.findall(clean) + ASSIGNED_FUNCTION_RE.findall(clean)
    definition_counts = collections.Counter(definitions)
    for name, count in sorted(definition_counts.items()):
        if count > 1:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "duplicate-function",
                    f"Function `{name}` is defined {count} times in this file; later definitions overwrite earlier ones unless branches are exclusive.",
                )
            )

    modules = MODULE_RE.findall(text)
    persistent_rules = [match for match in RULE_ADD_RE.finditer(clean) if match.group(1) != "Rule_AddOneShot"]
    for module in modules:
        required = {f"{module}_OnInit", f"{module}_Start"}
        missing = sorted(required - set(definitions))
        if missing:
            diagnostics.append(
                diagnostic("error", "lifecycle-missing", f"Registered module `{module}` lacks callbacks: {', '.join(missing)}.")
            )
        if persistent_rules and f"{module}_OnGameOver" not in definitions:
            diagnostics.append(
                diagnostic(
                    "error",
                    "cleanup-missing",
                    f"Module `{module}` registers persistent rules/events but has no `{module}_OnGameOver` cleanup callback.",
                )
            )

    removed_callbacks = {callback for _, callback in RULE_REMOVE_RE.findall(clean)}
    for match in persistent_rules:
        kind, callback = match.groups()
        if callback not in removed_callbacks and "Rule_RemoveMe" not in text:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "cleanup-unproven",
                    f"`{kind}` registers `{callback}`, but matching removal was not found in this file.",
                    line_number(clean, match.start()),
                )
            )

    for match in PLAYER_SQUADS_ASSIGN_RE.finditer(clean):
        group_name = match.group(1)
        destroy_re = re.compile(rf"\bSGroup_Destroy\s*\(\s*{re.escape(group_name)}\s*\)")
        if not destroy_re.search(clean):
            diagnostics.append(
                diagnostic(
                    "warning",
                    "sgroup-lifetime",
                    f"Temporary squad group `{group_name}` from `Player_GetSquads` is not visibly destroyed.",
                    line_number(clean, match.start()),
                )
            )
        count_re = re.compile(rf"\bSGroup_Count\s*\(\s*{re.escape(group_name)}\s*\)")
        count_match = count_re.search(clean, match.end())
        if count_match:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "sgroup-count-despawned",
                    f"`SGroup_Count({group_name})` includes despawned squads; use `SGroup_CountSpawned` when only active units should count.",
                    line_number(clean, count_match.start()),
                )
            )

    option_tables = sorted(
        set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*\.options)\b", clean))
    )
    if option_tables and "Setup_GetWinConditionOptions" not in clean:
        severity = "error" if modules else "warning"
        code = "options-uninitialized" if modules else "options-external"
        diagnostics.append(
            diagnostic(
                severity,
                code,
                "Option table(s) "
                + ", ".join(f"`{name}`" for name in option_tables)
                + " are used without a visible `Setup_GetWinConditionOptions` call; prove which importing mode initializes them.",
            )
        )

    registered_events = set(NETWORK_REGISTER_RE.findall(text)) | project_network_events
    for match in NETWORK_CALL_RE.finditer(text):
        event = match.group(1)
        if event not in registered_events:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "network-unregistered",
                    f"Network event `{event}` is called but no registration was found in the file or project.",
                    line_number(text, match.start()),
                )
            )

    local_known = set(definitions) | project_definitions | LUA_BUILTINS | {"import"}
    call_occurrences: dict[str, list[int]] = collections.defaultdict(list)
    for match in CALL_RE.finditer(clean):
        name = match.group(1)
        if name in {
            "and",
            "do",
            "else",
            "elseif",
            "end",
            "for",
            "function",
            "if",
            "local",
            "not",
            "or",
            "repeat",
            "return",
            "then",
            "until",
            "while",
        }:
            continue
        call_occurrences[name].append(line_number(clean, match.start()))

    for name, lines in sorted(call_occurrences.items()):
        if name in local_known:
            continue
        provenance = symbol_index.get(name)
        if provenance is None:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "unknown-call",
                    f"Call `{name}` is absent from official API/source evidence and local definitions.",
                    lines[0],
                )
            )
        elif provenance["provenance"] == "unofficial-definition":
            diagnostics.append(
                diagnostic(
                    "warning",
                    "unofficial-call",
                    f"Call `{name}` is supported only by unofficial definitions; inspect and validate its implementation.",
                    lines[0],
                )
            )
        elif provenance["provenance"] == "official-terrain-lua":
            diagnostics.append(
                diagnostic(
                    "warning",
                    "terrain-lua-call",
                    f"Call `{name}` is defined only in official terrain-layout Lua and is not proven available to match-time SCAR.",
                    lines[0],
                )
            )
        elif provenance["provenance"] == "usage-only" and provenance["official_calls"] == 0:
            diagnostics.append(
                diagnostic(
                    "warning",
                    "usage-only-call",
                    f"Call `{name}` has usage evidence but no official API or source definition.",
                    lines[0],
                )
            )

    if re.search(r"\bWorld_GetPlayerAt\s*\(\s*0\s*\)", clean):
        diagnostics.append(
            diagnostic("error", "player-index-zero", "`World_GetPlayerAt(0)` is unsafe; player indices are one-based.")
        )

    imports = IMPORT_RE.findall(text)
    if re.search(r"\bPLAYERS\b", clean) and not any("cardinal.scar" in value.lower() for value in imports):
        diagnostics.append(
            diagnostic(
                "warning",
                "players-contract",
                "`PLAYERS` is used without a visible `cardinal.scar` import; confirm the loader provides it.",
            )
        )
    return diagnostics


def validate_rdo(path: Path, text: str) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        line = exc.position[0] if exc.position else None
        return [diagnostic("error", "rdo-xml", f"Invalid RDO XML: {exc}.", line)]

    entry_match = RDO_ENTRY_RE.search(text)
    if not entry_match or not entry_match.group(1).strip():
        diagnostics.append(
            diagnostic("error", "rdo-entry", "RDO lacks a non-empty `m_scarWinConditionFile` property.")
        )
    keys = RDO_KEY_RE.findall(text)
    duplicates = [key for key, count in collections.Counter(keys).items() if count > 1]
    for key in sorted(duplicates):
        diagnostics.append(
            diagnostic("warning", "rdo-duplicate-key", f"RDO option key `{key}` appears more than once.")
        )
    if not re.search(r'<DataProperty\s+Name="m_name"[^>]*\sValue="[^"]+"', text):
        diagnostics.append(diagnostic("warning", "rdo-name", "RDO lacks a non-empty internal `m_name`."))
    return diagnostics


def validate_file(
    path: Path,
    symbol_index: dict[str, dict[str, Any]],
    project_definitions: set[str],
    project_network_events: set[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {"file": str(path.resolve()), "diagnostics": []}
    if not path.is_file():
        result["diagnostics"].append(diagnostic("error", "missing-file", "File does not exist."))
        return result
    text = decode_text(path)
    extension = path.suffix.lower()
    if extension in {".scar", ".lua"}:
        result["diagnostics"] = validate_script(
            path, text, symbol_index, project_definitions, project_network_events
        )
    elif extension == ".rdo":
        result["diagnostics"] = validate_rdo(path, text)
    else:
        result["diagnostics"].append(
            diagnostic("error", "unsupported-file", f"Unsupported extension `{extension}`.")
        )
    counts = collections.Counter(item["severity"] for item in result["diagnostics"])
    result["summary"] = {"errors": counts["error"], "warnings": counts["warning"]}
    return result


def print_results(results: list[dict[str, Any]]) -> None:
    for result in results:
        print(result["file"])
        diagnostics = result["diagnostics"]
        if not diagnostics:
            print("  OK: no static diagnostics")
            continue
        for item in diagnostics:
            location = f":{item['line']}" if "line" in item else ""
            print(f"  {item['severity'].upper()} {item['code']}{location}: {item['message']}")
        summary = result["summary"]
        print(f"  Summary: {summary['errors']} error(s), {summary['warnings']} warning(s)")


def main() -> int:
    args = parse_args()
    symbol_index = load_symbol_index(args.symbol_index)
    project_definitions, project_network_events, _ = collect_project_context(args.project_root)
    results = [
        validate_file(path, symbol_index, project_definitions, project_network_events)
        for path in args.files
    ]
    print_results(results)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    errors = sum(result["summary"]["errors"] for result in results)
    warnings = sum(result["summary"]["warnings"] for result in results)
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
