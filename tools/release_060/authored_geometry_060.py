"""Private 0.6.0 three-LOD authored geometry route; never installs an actor.

Stages: prepare, cook, readback, compare. A Blender exporter must first supply a
binary FBX, an authored decoded-shape snapshot, and an immutable export receipt.
The snapshot has the decoded-static geometry/skeleton layout and records the
authored shape with intended native UVs before the exporter's V preflip, so
intentional remodeling is compared to its own source. Stock supplies only the
rig/LOD format and material identity contract.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import msvcrt
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, ART, CFG, CORE, EXPORT, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write
from compare_archer_three_lod_manual_uvfix import compare_lod
from compare_archer_three_lod_manual_uvfix import normalized_weights
from assemble_archer_geometry_pairing import _scalar_delta

SCHEMA = "ccp-060-authored-native-geometry-spec/v1"
NAMES = ("model.fbx", "model.rig", "model.rgo", "model.rgotemplate",
         "albedo.png", "normal.png", "metalness.png", "roughness.png")
BURNERS = ("RR Material Burner", "RGM", "RRGeometry", "RGO")
SUFFIXES = (".rgm", ".rgo", ".rrgeom", ".rrmaterial")
SLOT_FILES = {"albedoTexture": "albedo.png", "normalMap": "normal.png",
              "metalTex": "metalness.png", "roughnessTex": "roughness.png"}


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def paths(spec_path: Path) -> tuple[dict, Path, Path, Path]:
    guard()
    owned(spec_path)
    spec = read(spec_path)
    if spec.get("schema") != SCHEMA:
        raise ValueError("Unknown authored geometry spec schema")
    slug, key = spec["slug"], spec["project_key"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,55}", slug) or not re.fullmatch(r"[a-z0-9]{4}", key):
        raise ValueError("Slug or four-character private key invalid")
    base = owned(OUT / "authored-geometry" / slug)
    project = owned(STAGING / "ag" / slug / "Mods" / key)
    return spec, base, project, project / "project/source"


def source_inputs(spec: dict) -> tuple[Path, Path, Path, Path, Path, Path]:
    fbx, action, albedo, snapshot, export, stock = (Path(spec[name]) for name in
                                                     ("fbx", "action", "albedo",
                                                      "authored_snapshot", "export_receipt",
                                                      "stock_manifest"))
    for p in (fbx, action, albedo, snapshot, export, stock):
        if not p.is_file(): raise FileNotFoundError(p)
    for p in (fbx, action, albedo):
        if not p.resolve().is_relative_to(EXPORT.resolve()):
            raise ValueError(f"Export input is outside 0.6.0 export root: {p}")
    for p in (snapshot, export, stock): owned(p)
    receipt = read(export)
    expected = {"fbx_sha256": sha(fbx), "action_sha256": sha(action), "albedo_sha256": sha(albedo),
                "authored_snapshot_sha256": sha(snapshot)}
    filenames = {"fbx_sha256": "model.fbx", "action_sha256": "action.json",
                 "albedo_sha256": "albedo.png", "authored_snapshot_sha256": "authored-snapshot.json"}
    actual = {key: receipt.get(key) or receipt.get("files", {}).get(filename, {}).get("sha256")
              for key, filename in filenames.items()}
    actual["authored_snapshot_sha256"] = (actual["authored_snapshot_sha256"]
                                           or receipt.get("authored_snapshot", {}).get("sha256"))
    if any(actual[k] != v for k, v in expected.items()):
        raise RuntimeError("Exporter receipt does not pin actual FBX, albedo, and authored snapshot")
    blend = Path(receipt.get("source_blend") or receipt["blend"])
    if (not blend.resolve().is_relative_to(ART.resolve())
            or (receipt.get("source_blend_sha256") or receipt.get("blend_sha256")) != sha(blend)):
        raise RuntimeError("Exporter source blend drift")
    if spec.get("stock_manifest_sha256") != sha(stock):
        raise RuntimeError("Stock donor hash drift")
    action_data = read(action)
    if (action_data.get("schema") != "garrison.unit-prototype-build/v1"
            or action_data.get("overrides") or action_data.get("attachments")
            or len(action_data.get("bones", [])) != spec["skeleton_bones"]):
        raise RuntimeError("Source action is not a neutral matched prototype document")
    return fbx, action, albedo, snapshot, export, stock


def fbx_skin_counts(fbx: Path) -> tuple[int, int]:
    # Installed Garrison unit exporter produces binary FBX and one Skin and one
    # or more Cluster deformers per LOD. A zero count means the native burner
    # would silently produce an unweighted body; fail before creating a project.
    raw = fbx.read_bytes()
    if not raw.startswith(b"Kaydara FBX Binary"):
        raise RuntimeError("Expected installed binary FBX exporter output")
    skins = raw.count(b"DeformerS\x04\x00\x00\x00Skin")
    clusters = raw.count(b"DeformerS\x07\x00\x00\x00Cluster")
    if skins < 3 or clusters < 3:
        raise RuntimeError(f"FBX requires real skin and cluster deformers for three LODs: {skins=}, {clusters=}")
    return skins, clusters


def rig_file_contract(path: Path, donor: dict) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines.count("[BONES START]") != 1 or "[END]" not in lines:
        raise RuntimeError("Prepared rig bones section missing")
    start = lines.index("[BONES START]") + 1
    end = lines.index("[END]", start)
    names = lines[start:end]
    expected = [bone["name"] for bone in donor["skeleton"]["bones"]]
    if names != expected:
        raise RuntimeError("Prepared rig bones differ from exact donor order")
    return len(names)


def source_contract(spec: dict, snapshot: dict, stock: dict) -> list[tuple[str, str, str]]:
    bones = spec["skeleton_bones"]
    if bones not in (48, 73): raise ValueError("Only qualified 48/46 or 73/46 rig families")
    groups, donor = snapshot["geometry"]["groups"], stock["geometry"]["groups"]
    if snapshot.get("status") != "decoded" or stock.get("status") != "decoded" or len(groups) != len(donor) != 3:
        raise RuntimeError("Expected three authored and stock decoded LOD groups")
    if len(snapshot["skeleton"]["bones"]) != bones or len(stock["skeleton"]["bones"]) != bones:
        raise RuntimeError("Source/stock full skeleton count mismatch")
    source_palette = len(snapshot["skeleton"]["skin_palettes"][0]["bones"])
    stock_palette = len(stock["skeleton"]["skin_palettes"][0]["bones"])
    if source_palette != stock_palette or source_palette not in ((45, 46) if bones == 48 else (46, 56, 58)):
        raise RuntimeError("Authored source does not retain its exact native skin palette")
    required = [(spec["group_name"], f"lod{i}", "unit") for i in (1, 2, 3)]
    if [(g["name"], g["material"], g["effect"]) for g in groups] != required:
        raise RuntimeError("Authored group/material/effect names changed")
    if [g["name"] for g in donor] != [spec["group_name"]] * 3:
        raise RuntimeError("Stock donor group identity changed")
    for number, g in enumerate(groups, 1):
        if (g["triangle_count"] <= 0 or g["vertex_count"] <= 0
                or len(g["triangles"]) != g["triangle_count"]
                or any(len(tri) != 3 or any(index < 0 or index >= g["vertex_count"]
                                                for index in tri) for tri in g["triangles"])
                or len(g["positions"]) != g["vertex_count"]
                or len(g["skin_indices"]) != g["vertex_count"]
                or len(g["skin_weights"]) != g["vertex_count"]
                or set(g["uv_layers"]) != {"UVMap"}
                or ("corner_uvs" not in g
                    and len(g["uv_layers"]["UVMap"]) != g["vertex_count"])):
            raise RuntimeError(f"Authored LOD{number} incomplete")
        corners = g.get("corner_uvs")
        if corners is not None:
            if (g.get("uv_basis") != "native_intended_before_export_preflip"
                    or len(corners) != g["triangle_count"]
                    or any(len(tri) != 3 or any(len(uv) != 2 for uv in tri) for tri in corners)):
                raise RuntimeError(f"Authored LOD{number} corner UV export contract changed")
            normals = g.get("corner_normals")
            if normals is not None and (len(normals) != g["triangle_count"]
                                        or any(len(tri) != 3 or any(len(n) != 3 for n in tri)
                                               for tri in normals)):
                raise RuntimeError(f"Authored LOD{number} corner normal contract changed")
            if normals is not None and any(
                    not all(math.isfinite(value) for value in normal)
                    or abs(math.sqrt(sum(value * value for value in normal)) - 1.0) > .02
                    for tri in normals for normal in tri):
                raise RuntimeError(f"Authored LOD{number} has a non-unit corner normal")
    return required


def expanded_corner_group(group: dict) -> dict:
    """Represent face-corner UV seams as split vertices for decoded comparison."""
    if "corner_uvs" not in group:
        return group
    result = {k: copy for k, copy in group.items()
              if k not in {"positions", "normals", "uv_layers", "skin_indices",
                           "skin_weights", "triangles", "vertex_count", "corner_uvs",
                           "corner_normals", "uv_basis"}}
    result.update(positions=[], normals=[], uv_layers={"UVMap": []},
                  skin_indices=[], skin_weights=[], triangles=[])
    normal_corners = group.get("corner_normals")
    for row, triangle in enumerate(group["triangles"]):
        tri = []
        for corner, index in enumerate(triangle):
            tri.append(len(result["positions"]))
            for key in ("positions", "skin_indices", "skin_weights"):
                result[key].append(group[key][index])
            result["normals"].append(normal_corners[row][corner] if normal_corners is not None
                                     else group["normals"][index])
            result["uv_layers"]["UVMap"].append(group["corner_uvs"][row][corner])
        result["triangles"].append(tri)
    result["vertex_count"] = len(result["positions"])
    return result


def corrected_ranged_normal_count(previous: dict, corrected: dict) -> int:
    """Require a corrected candidate to differ only at invalid LOD2 corners."""
    old, new = copy.deepcopy(previous), copy.deepcopy(corrected)
    counts = []
    for lod, (a, b) in enumerate(zip(old["geometry"]["groups"],
                                 new["geometry"]["groups"]), 1):
        changes = 0
        for row, (a_tri, b_tri) in enumerate(zip(a["corner_normals"], b["corner_normals"])):
            for corner, (a_normal, b_normal) in enumerate(zip(a_tri, b_tri)):
                if a_normal == b_normal:
                    continue
                old_length = math.sqrt(sum(value * value for value in a_normal))
                new_length = math.sqrt(sum(value * value for value in b_normal))
                if (lod != 2 or abs(old_length - 1) <= .02
                        or abs(new_length - 1) > .02
                        or math.dist([value / old_length for value in a_normal], b_normal) > .02):
                    raise RuntimeError("Normal correction changed a valid or unrelated corner")
                a["corner_normals"][row][corner] = b_normal
                changes += 1
        counts.append(changes)
    if old != new or counts != [0, 4, 0]:
        raise RuntimeError("Corrected ranged source changed outside four LOD2 normals")
    return counts[1]


def _adjust_new_panel_native_weight_rounding(source: dict, cooked: dict,
                                             panel_triangles: int) -> tuple[dict, dict]:
    """Reconcile only the appended panel's bounded native 8-bit rounding.

    All pre-existing body corners retain their original authored weights and
    are checked by the ordinary exact corner comparator after this adjustment.
    """
    if panel_triangles != 24 or len(source["triangles"]) <= panel_triangles:
        raise RuntimeError("Only the documented appended 24-triangle panel may round")
    base, panel = source["triangles"][:-panel_triangles], source["triangles"][-panel_triangles:]
    positions = source["positions"]
    base_positions = {tuple(positions[i]) for tri in base for i in tri}
    panel_positions = {tuple(positions[i]) for tri in panel for i in tri}
    if len(panel_positions) != 20 or panel_positions & base_positions:
        raise RuntimeError("Owner panel is not an isolated appended 20-position surface")
    compiled = {}
    for index, position in enumerate(cooked["positions"]):
        key = tuple(position)
        if key not in panel_positions: continue
        value = dict(normalized_weights(cooked, index))
        if key in compiled and compiled[key] != value:
            raise RuntimeError("Native panel position has inconsistent skin weights")
        compiled[key] = value
    if set(compiled) != panel_positions:
        raise RuntimeError("Native owner panel positions differ")
    revised = copy.deepcopy(source)
    changed_corners = 0
    maximum_delta = 0
    dropped_positions = set()
    for tri in panel:
        for index in tri:
            position = tuple(positions[index])
            authored = dict(normalized_weights(source, index))
            native = compiled[position]
            if not set(native) <= set(authored):
                raise RuntimeError("Native owner panel introduced a different bone influence")
            dropped = set(authored) - set(native)
            if sum(authored[bone] for bone in dropped) > 1:
                raise RuntimeError("Native owner panel dropped more than one 8-bit influence count")
            if any(abs(authored[bone] - native[bone]) > 2 for bone in set(native)):
                raise RuntimeError("Native owner panel weight shift exceeds two 8-bit counts")
            if sum(native.values()) != 255 or abs(sum(authored.values()) - 255) > 1:
                raise RuntimeError("Native owner panel weights are not bounded normalized values")
            if dropped and sum(authored[bone] for bone in dropped):
                dropped_positions.add(position)
            delta = max((abs(authored.get(bone, 0) - native.get(bone, 0))
                         for bone in set(authored) | set(native)), default=0)
            maximum_delta = max(maximum_delta, delta)
            if authored != native: changed_corners += 1
            revised["skin_weights"][index] = [native.get(int(bone), 0) / 255
                                               for bone in revised["skin_indices"][index]]
    return revised, {"scope": "appended_owner_panel_only", "panel_triangles": panel_triangles,
                     "panel_positions": len(panel_positions), "changed_corners": changed_corners,
                     "dropped_one_count_influence_positions": len(dropped_positions),
                     "maximum_8bit_weight_scalar_delta": maximum_delta,
                     "native_weight_sum_8bit": 255,
                     "preexisting_body_corners_still_checked_exact": True}


def compare_authored_lod(source: dict, cooked: dict, number: int,
                         panel_triangles: int = 0) -> dict:
    """Match close quantized positions bijectively before the proven corner test.

    Garrison can quantize two nearby authored positions so independent nearest
    neighbor picks collide. A full within-tolerance bipartite assignment keeps
    both distinct positions. The 1.05 mm bound covers the observed Spear IV
    native coordinate-grid diagonal of 1.001082 mm; other corners remain exact.
    """
    left = sorted({tuple(p) for p in source["positions"]})
    right = sorted({tuple(p) for p in cooked["positions"]})
    tolerance = .00105
    native_merge = None
    if len(left) != len(right):
        # Crossbow IV contains two pairs of authored seam positions per LOD
        # separated by ~0.036 mm. The native coordinate grid emits one point
        # for each pair. Permit only this measured quantization collapse; the
        # complete triangle/skin/UV/normal corner signature is checked below.
        if len(left) - len(right) != 2:
            raise RuntimeError(f"LOD{number} unique position count changed")
        merged: dict[tuple, list[tuple]] = {}
        for pos in left:
            nearest = min(right, key=lambda item: math.dist(pos, item))
            if math.dist(pos, nearest) > tolerance:
                raise RuntimeError(f"LOD{number} authored position exceeds native tolerance")
            merged.setdefault(nearest, []).append(pos)
        collisions = [items for items in merged.values() if len(items) > 1]
        maximum_source_separation = max((math.dist(a, b) for a, b in collisions), default=0.0)
        if (len(merged) != len(right) or len(collisions) != 2
                or any(len(items) != 2 for items in collisions)
                or maximum_source_separation > .00005):
            raise RuntimeError(f"LOD{number} native position merge exceeds measured grid collapse")
        matched = {pos: target for target, items in merged.items() for pos in items}
        native_merge = {"merged_pairs": 2, "maximum_authored_pair_separation_m": maximum_source_separation,
                        "limit_m": .00005, "all_native_positions_covered": True,
                        "full_corner_signature_checked_after_projection": True}
    else:
        matched = None
    if matched is None:
        candidates = []
        for pos in left:
            row = sorted(((math.dist(pos, other), index) for index, other in enumerate(right)
                          if math.dist(pos, other) <= tolerance), key=lambda pair: pair[0])
            if not row: raise RuntimeError(f"LOD{number} authored position exceeds native tolerance")
            candidates.append([index for _, index in row])
        owner = [-1] * len(right)

        def assign(left_index: int, seen: set[int]) -> bool:
            for right_index in candidates[left_index]:
                if right_index in seen: continue
                seen.add(right_index)
                previous = owner[right_index]
                if previous < 0 or assign(previous, seen):
                    owner[right_index] = left_index
                    return True
            return False

        for index in sorted(range(len(left)), key=lambda i: len(candidates[i])):
            if not assign(index, set()):
                raise RuntimeError(f"LOD{number} positions have no bijective within-tolerance mapping")
        matched = {left[i]: right[j] for j, i in enumerate(owner)}
    max_distance = max((math.dist(a, matched[a]) for a in left), default=0.0)
    normalized = copy.copy(source)
    normalized["positions"] = [matched[tuple(p)] for p in source["positions"]]
    result = compare_lod(normalized, cooked, number)
    initial_weights_exact = result["weighted_corner_multiset_exact_after_influence_order_normalization"]
    if panel_triangles and not result["passed"]:
        revised, rounding = _adjust_new_panel_native_weight_rounding(normalized, cooked, panel_triangles)
        checked = compare_lod(revised, cooked, number)
        if not checked["passed"]:
            raise RuntimeError("Panel rounding allowance did not preserve exact body/UV/normal comparison")
        result = checked
        result["new_panel_native_weight_rounding"] = rounding
    if native_merge:
        result["source_unique_positions"] = len(left)
        result["native_grid_position_merges"] = native_merge
    result["raw_authored_weighted_corners_exact"] = initial_weights_exact
    result["maximum_position_distance_m"] = max_distance
    result["position_tolerance_m"] = tolerance
    result["authored_position_matching"] = "bijective_within_1.05mm_then_exact_weighted_corner_comparison"
    result["passed"] = result["passed"] and max_distance <= tolerance
    return result


def rig_contract(cooked: dict, stock: dict, bones: int) -> dict:
    a, b = cooked["skeleton"], stock["skeleton"]
    pa, pb = a["skin_palettes"], b["skin_palettes"]
    bk = ("index", "name", "parent_index", "parent_name")
    pk = ("palette_index", "name", "parent_index", "parent_name", "skeleton_index")
    if len(a["bones"]) != bones or len(b["bones"]) != bones or len(pa) != 1 or len(pb) != 1:
        raise RuntimeError("Native skeleton or palette count mismatch")
    ab, bb = pa[0]["bones"], pb[0]["bones"]
    if len(ab) != len(bb) or len(ab) not in ((45, 46) if bones == 48 else (46, 56, 58)):
        raise RuntimeError("Native skin palette count differs from the supported stock donor")
    if any(tuple(x[k] for k in bk) != tuple(y[k] for k in bk) for x, y in zip(a["bones"], b["bones"])):
        raise RuntimeError("Ordered native skeleton hierarchy differs")
    if any(tuple(x[k] for k in pk) != tuple(y[k] for k in pk) for x, y in zip(ab, bb)):
        raise RuntimeError("Ordered native palette identity differs")
    if pa[0]["lod_palettes"] != pb[0]["lod_palettes"] or len(pa[0]["lod_palettes"]) != 3:
        raise RuntimeError("Native three-LOD palette records differ")
    local_rows = [_scalar_delta(x["local_reference_transform"], y["local_reference_transform"])
                  for x, y in zip(a["bones"], b["bones"])]
    global_rows = [_scalar_delta(x["global_reference_transform"], y["global_reference_transform"])
                   for x, y in zip(a["bones"], b["bones"])]
    deltas = {
        "local_reference": max(local_rows),
        "global_reference": max(global_rows),
        "palette_global": max(_scalar_delta(x["global_reference_transform"], y["global_reference_transform"])
                               for x, y in zip(ab, bb)),
        "inverse_bind": max(_scalar_delta(x["inverse_bind_transform"], y["inverse_bind_transform"])
                            for x, y in zip(ab, bb)),
    }
    # The qualified Chinese villager manual route has one measured exception:
    # a pelvis socket leaf outside the stock skin palette. Its 1.353 mm local
    # rest drift cannot deform vertices. No other skeleton bone gets relief.
    exception = None
    offenders = [i for i, (local, glob) in enumerate(zip(local_rows, global_rows))
                 if max(local, glob) > .0002]
    if offenders:
        if len(offenders) != 1 or bones != 73:
            raise RuntimeError(f"Native rest/bind scalar drift: {deltas}")
        index = offenders[0]
        bone = a["bones"][index]
        leaf = not any(child.get("parent_index") == bone["index"] for child in a["bones"])
        unskinned = all(item["skeleton_index"] != bone["index"] for item in ab)
        if (bone["name"] != "metarig_pelvissocket" or not leaf or not unskinned
                or max(local_rows[index], global_rows[index]) > .0014):
            raise RuntimeError(f"Native rest/bind scalar drift outside sole unskinned leaf allowance: {deltas}")
        exception = {"bone": bone["name"], "skeleton_index": bone["index"],
                     "local_scalar_delta": local_rows[index],
                     "global_scalar_delta": global_rows[index],
                     "leaf": leaf, "unskinned": unskinned, "maximum_allowed": .0014}
    if max(deltas["palette_global"], deltas["inverse_bind"]) > .0002:
        raise RuntimeError(f"Active palette/bind scalar drift: {deltas}")
    return {"skeleton_bones": bones, "palette_bones": len(ab),
            "ordered_hierarchy_and_palette_exact": True, "lod_palette_records_exact": True,
            "max_transform_scalar_deltas": deltas, "strict_tolerance": .0002,
            "nondeforming_leaf_exception": exception}


def prepare(spec_path: Path) -> dict:
    spec, base, project, source = paths(spec_path)
    fbx, action, albedo, snapshot_path, export, stock_path = source_inputs(spec)
    snapshot, stock = read(snapshot_path), read(stock_path)
    source_contract(spec, snapshot, stock)
    rig_contract(snapshot, stock, spec["skeleton_bones"])
    skins, clusters = fbx_skin_counts(fbx)
    template_body = Path(spec["template_body"])
    template_project = Path(spec["template_project"])
    for p in (template_body, template_project):
        if not p.resolve().is_relative_to(STAGING.resolve()):
            raise ValueError("Native template must be an owned 0.6.0 staging project")
    if not template_body.is_dir() or not template_project.is_dir():
        raise FileNotFoundError("Generated native source template absent")
    for name in NAMES:
        if not (template_body / name).is_file(): raise FileNotFoundError(template_body / name)
    for name, field in (("model.rig", "template_rig_sha256"),
                        ("model.rgo", "template_rgo_sha256"),
                        ("model.rgotemplate", "template_rgotemplate_sha256")):
        if spec.get(field) != sha(template_body / name):
            raise RuntimeError(f"Pinned generated source template drift: {name}")
    rig_file_contract(template_body / "model.rig", stock)
    target_rel = f"art/scenario/garrison/{spec['project_key']}/body"
    receipt_path = owned(base / "prepare.json")
    if receipt_path.exists():
        raise FileExistsError("Preserve prior authored geometry attempt")
    # Recover only a blank scaffold when an earlier attempt stopped after core
    # create but before source registration. Never replace a populated project.
    existing_project = project.exists()
    if existing_project and (project / "project/source" / target_rel).exists():
        raise FileExistsError("Private geometry source already populated")
    command = [str(CORE), "mod-project", "create", "--library", str(project.parent.parent),
               "--name", spec["project_key"]]
    result = (None if existing_project else
              subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120))
    base.mkdir(parents=True, exist_ok=True)
    create_log = base / "create.log"
    if create_log.exists(): raise FileExistsError("Preserve prior create log")
    if result is None:
        create_log.write_text("RECOVERED: existing blank private scaffold after interrupted prepare\n",
                              encoding="utf-8")
    else:
        create_log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(result.returncode)
                              + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
                              encoding="utf-8")
        if result.returncode: raise RuntimeError(f"Private scaffold create failed: {create_log}")
    config = read(project / "mod-project.json")
    if (config.get("key") != spec["project_key"] or config.get("animated_units")
            or config.get("assets") or config.get("cooks")
            or config.get("game_mode", {}).get("enabled")):
        raise RuntimeError("Private geometry scaffold is not blank")
    before = hashes(project)
    burn = source / "_default.burnproj"
    old_rel = template_body.relative_to(template_project / "project/source").as_posix()
    template_rules = (template_project / "project/source/_default.burnproj").read_text(encoding="utf-8")
    old_native, new_native = old_rel.replace("/", "\\"), target_rel.replace("/", "\\")
    blocks = [b for b in re.findall(r"<BurnRule>.*?</BurnRule>", template_rules, re.DOTALL)
              if old_native in b]
    burners = [re.search(r"<Burner>(.*?)</Burner>", b).group(1) for b in blocks]
    if tuple(burners) != BURNERS:
        raise RuntimeError("Generated four-rule native model burner contract changed")
    original = burn.read_text(encoding="utf-8")
    revised = original.replace("</Rules>", "\n".join(b.replace(old_native, new_native)
                                               for b in blocks) + "\n\t</Rules>", 1)
    if revised == original: raise RuntimeError("Native burn rules were not inserted")
    ET.fromstring(revised)
    template_mat = ET.parse(template_body / "model.material").getroot().find("material")
    slots = {p.get("name"): Path(p.get("value", "")).name for p in template_mat.findall("param")
             if p.get("type") == "tex2D"} if template_mat is not None else {}
    if template_mat is None or template_mat.get("source") != "unit" or slots != SLOT_FILES:
        raise RuntimeError("Generated neutral source material contract changed")
    body = source / target_rel
    body.mkdir(parents=True)
    for name in NAMES:
        src = fbx if name == "model.fbx" else albedo if name == "albedo.png" else template_body / name
        shutil.copy2(src, body / name)
    rig_file_contract(body / "model.rig", stock)
    matset = ET.Element("materialSet")
    for number in (1, 2, 3):
        mat = ET.SubElement(matset, "material", {"name": f"lod{number}", "type": "shader", "source": "unit"})
        for slot, filename in slots.items():
            ET.SubElement(mat, "param", {"name": slot, "type": "tex2D",
                                          "value": target_rel + "/" + filename})
    ET.indent(matset)
    (body / "model.material").write_bytes(ET.tostring(matset, encoding="utf-8", xml_declaration=True))
    burn.write_text(revised, encoding="utf-8")
    after = hashes(project)
    added = set(after) - set(before)
    expected = {"project/source/" + target_rel + "/" + n for n in (*NAMES, "model.material")}
    changed = {n for n in before if before[n] != after.get(n)}
    if added != expected or changed != {"project/source/_default.burnproj"}:
        raise RuntimeError(f"Private source allowlist drift: {added=} {changed=}")
    record = {"schema": "ccp-060-authored-native-prepare/v1", "status": "prepared_not_cooked",
              "spec_sha256": sha(spec_path), "project": str(project), "key": spec["project_key"],
              "body_rel": target_rel, "body": str(body), "source_hashes_after": after,
              "source_fbx_sha256": sha(fbx), "source_action_sha256": sha(action),
              "authored_snapshot_sha256": sha(snapshot_path),
              "export_receipt_sha256": sha(export), "stock_manifest_sha256": sha(stock_path),
              "fbx_skin_nodes": skins, "fbx_cluster_nodes": clusters,
              "template_rgo_diagnostic_only": True, "neutral_material_not_for_final_pair": True,
              "no_actor_or_animation_owner": True, "only_added": sorted(added),
              "only_changed": sorted(changed), "create_log": str(create_log),
              "create_log_sha256": sha(create_log)}
    write(receipt_path, record)
    return {"status": record["status"], "receipt": str(receipt_path)}


def cook(spec_path: Path) -> dict:
    spec, base, project, _ = paths(spec_path)
    prep_path, receipt_path = base / "prepare.json", owned(base / "cook.json")
    run = owned(project / "dist/authored-geometry-cook")
    if run.exists(): raise FileExistsError("Preserve prior native cook")
    prep = read(prep_path)
    if prep["status"] != "prepared_not_cooked" or prep["spec_sha256"] != sha(spec_path):
        raise RuntimeError("Prepared authored source drift")
    before = hashes(project)
    if before != prep["source_hashes_after"]: raise RuntimeError("Native source bytes changed")
    rig_file_contract(Path(prep["body"]) / "model.rig", read(spec["stock_manifest"]))
    if receipt_path.exists():
        prior = read(receipt_path)
        if (prior.get("status") != "lock_busy_no_cook"
                or prior.get("prepare_sha256") != sha(prep_path)
                or prior.get("source_hashes_before") != before):
            raise FileExistsError("Preserve prior native cook receipt")
    editor = Path(CFG["art_editor"])
    if not editor.is_file() or not NATIVE_LOCK.is_file(): raise FileNotFoundError("Native editor or shared byte lock")
    command = [str(editor), "-rtm", "--safe_settings", "--do_not_restore", "--quiet_crash_report",
               "--no_source_control", "--log_path", str(run / "logs"), "--build_mod",
               str(project / f"project/{spec['project_key']}.aoe4mod"), "--no_burn_window",
               "--burn_verbose_log_level", "--burn_cache_type", "Local", "--burn_max_threads", "1",
               "--burn_log_path", str(run / "logs/burn.log"), "--build_path", str(run / "output"),
               "--intermediate_path", str(run / "intermediate")]
    record = {"schema": "ccp-060-authored-native-cook/v1", "status": "pending_lock",
              "prepare_sha256": sha(prep_path), "project": str(project),
              "source_hashes_before": before, "command": command, "run_root": str(run),
              "lock_protocol": "msvcrt first byte LK_NBLCK, never delete", "no_actor_or_animation_owner": True}
    write(receipt_path, record)
    with NATIVE_LOCK.open("r+b") as stream:
        try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            record.update(status="lock_busy_no_cook", error=str(error))
            write(receipt_path, record)
            raise
        try:
            run.mkdir(parents=True)
            stdout, stderr = run / "stdout.log", run / "stderr.log"
            record["status"] = "running_under_shared_lock"; write(receipt_path, record)
            with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
                proc = subprocess.run(command, cwd=editor.parent, stdout=out, stderr=err,
                                      text=True, timeout=1200)
            after = hashes(project)
            archives = sorted((run / "output").rglob("*.sga"))
            record.update(exit_code=proc.returncode, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr),
                          source_bytes_preserved=all(after.get(k) == v for k, v in before.items()),
                          created_project_files=sorted(set(after) - set(before)),
                          archives=[{"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}
                                    for p in archives])
            record["status"] = ("native_cook_failed_preserved" if proc.returncode else
                                "source_changed_refused" if not record["source_bytes_preserved"] else
                                "native_cook_completed_pending_readback" if len(archives) == 1 else
                                "native_archive_count_unexpected")
            write(receipt_path, record)
            return {"status": record["status"], "receipt": str(receipt_path)}
        finally:
            stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def run_json(command: list[str], timeout: int = 120) -> dict:
    proc = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout)
    if proc.returncode: raise RuntimeError(f"Command failed exit {proc.returncode}: {proc.stderr[-1000:]}")
    return json.loads(proc.stdout)


def readback(spec_path: Path) -> dict:
    spec, base, project, _ = paths(spec_path)
    prep, cooked = read(base / "prepare.json"), read(base / "cook.json")
    receipt = owned(base / "readback.json")
    extract, index, config, decoded, log = [owned(base / name) for name in
                                           ("extracted", "private-index.sqlite3", "private-config.json",
                                            "decoded", "decode.log")]
    if any(p.exists() for p in (receipt, extract, index, config, decoded, log)):
        raise FileExistsError("Preserve prior authored native readback")
    if (cooked["status"] != "native_cook_completed_pending_readback"
            or cooked["prepare_sha256"] != sha(base / "prepare.json")
            or not cooked["source_bytes_preserved"] or len(cooked["archives"]) != 1):
        raise RuntimeError("Cook receipt does not qualify readback")
    archive = Path(cooked["archives"][0]["path"])
    if sha(archive) != cooked["archives"][0]["sha256"]:
        raise RuntimeError("Native archive drift")
    listing = run_json([str(ARCH), "list", "--verify", str(archive)])
    if not listing["archive"]["verification"]["verified"]:
        raise RuntimeError("Native archive verification failed")
    members = {m["path"]: m for m in listing["members"]}
    root = prep["body_rel"] + "/model"
    names = [root + suffix for suffix in SUFFIXES]
    if not set(names).issubset(members): raise RuntimeError("Native four-model resource set incomplete")
    allowed_project_descriptor = f"attrib/{spec['project_key']}.rgd"
    if (any((p.startswith("attrib/") and p != allowed_project_descriptor)
            or p.endswith(".rhka") for p in members)
            or allowed_project_descriptor not in members):
        raise RuntimeError("Private art archive contains actor or animation-owner resources")
    extract.mkdir(parents=True)
    resources = {}
    for member in names:
        target = extract / Path(member).name
        run_json([str(ARCH), "extract-member", str(archive), member, str(target)])
        resources[Path(member).suffix] = {"member": member, "path": str(target),
                                          "sha256": sha(target), "bytes": target.stat().st_size}
    # Use the proven private-index schema builder. Redirect only its output path;
    # give the decoder an empty owned game root to avoid stock-owner resolution.
    import decode_archer_three_lod_manual_uvfix as private_index
    private_index.INDEX = index
    private_index.create_index(archive, listing["members"], prep["key"])
    original = read(private_index.ORIGINAL_CONFIG)
    private_root = owned(STAGING / "ag" / spec["slug"])
    (private_root / "cardinal/archives").mkdir(parents=True, exist_ok=True)
    original["index_path"] = str(index)
    original["game_root"] = str(private_root)
    config.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    command = [str(CORE), "convert", "decode-static", "--logical-path", root + ".rgm",
               "--config", str(config), "--index", str(index), "--output-root", str(decoded)]
    proc = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=300)
    log.write_text("COMMAND: " + " ".join(command) + "\nEXIT: " + str(proc.returncode)
                   + "\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
                   encoding="utf-8")
    response = json.loads(proc.stdout) if proc.returncode == 0 else {}
    manifest = Path(response["manifest_path"]) if response.get("manifest_path") else None
    if manifest is not None and (not manifest.is_file() or not manifest.resolve().is_relative_to(decoded.resolve())):
        raise RuntimeError("Private decoder returned unowned or absent manifest")
    record = {"schema": "ccp-060-authored-native-readback/v1",
              "status": "decoded_pending_authored_comparison" if manifest else "decode_failed_preserved",
              "archive": str(archive), "archive_sha256": sha(archive),
              "archive_verified": True, "members": sorted(members), "resources": resources,
              "private_index_sha256": sha(index), "private_config_sha256": sha(config),
              "decode_exit_code": proc.returncode, "decoded_manifest": str(manifest) if manifest else None,
              "decoded_manifest_sha256": sha(manifest) if manifest else None,
              "decode_log_sha256": sha(log), "stock_rgo_and_final_material_not_paired": True,
              "no_generated_actor_or_animation_owner": True}
    write(receipt, record)
    return {"status": record["status"], "receipt": str(receipt)}


def compare(spec_path: Path, report_name: str = "comparison.json") -> dict:
    spec, base, _, _ = paths(spec_path)
    if report_name not in ("comparison.json", "comparison-qualified.json"):
        raise ValueError("Comparison report name outside retained evidence convention")
    report = owned(base / report_name)
    if report.exists(): raise FileExistsError("Preserve prior authored comparison")
    fbx, action, albedo, snapshot_path, export, stock_path = source_inputs(spec)
    prep, rb = read(base / "prepare.json"), read(base / "readback.json")
    if rb["status"] != "decoded_pending_authored_comparison" or prep["spec_sha256"] != sha(spec_path):
        raise RuntimeError("Native source/readback evidence drift")
    if prep["authored_snapshot_sha256"] != sha(snapshot_path) or prep["source_fbx_sha256"] != sha(fbx):
        raise RuntimeError("Authored source changed after native preparation")
    cooked_path = Path(rb["decoded_manifest"])
    if sha(cooked_path) != rb["decoded_manifest_sha256"]:
        raise RuntimeError("Decoded native manifest changed")
    source, cooked, stock = read(snapshot_path), read(cooked_path), read(stock_path)
    required = source_contract(spec, source, stock)
    rig = rig_contract(cooked, stock, spec["skeleton_bones"])
    rig_contract(source, stock, spec["skeleton_bones"])
    groups_a = [expanded_corner_group(g) for g in source["geometry"]["groups"]]
    groups_b = cooked["geometry"]["groups"]
    if cooked.get("status") != "decoded" or len(groups_b) != 3:
        raise RuntimeError("Decoded compiled model lacks three native LODs")
    names = [(g["name"], g["material"], g["effect"]) for g in groups_b]
    panel_count = 0
    prior_panel_source = None
    receipt = read(export)
    if snapshot_path.parent.name == "v5c" and receipt.get("schema") == "ccp-060-archer4-corner-normals-v5c/1":
        corrected_ranged_normal_count(read(snapshot_path.parent.parent / "v5b/authored-snapshot.json"), source)
        prior_panel_source = snapshot_path.parent.parent / "v4/authored-snapshot.json"
        panel_count = 24
    elif snapshot_path.parent.name == "v5b" and receipt.get("schema") == "ccp-060-ranged-tier-export/v1":
        panel = receipt.get("lod_remodel", {}).get("1", {}).get("owner_panel", {})
        prior_panel_source = snapshot_path.parent.parent / "v4/authored-snapshot.json"
        prior = read(prior_panel_source)
        old, new = prior["geometry"]["groups"][0], source["geometry"]["groups"][0]
        if (panel.get("triangles") != 24 or panel.get("vertices") != 20
                or not panel.get("all_vertices_weighted")
                or prior["source_manifest_sha256"] != source["source_manifest_sha256"]
                or old["positions"] != new["positions"][:len(old["positions"])]
                or old["triangles"] != new["triangles"][:len(old["triangles"])]
                or len(new["triangles"]) != len(old["triangles"]) + 24):
            raise RuntimeError("Corrected owner panel is not an append-only 24-triangle addition")
        panel_count = 24
    rows = [compare_authored_lod(a, b, i, panel_count if i == 1 else 0)
            for i, (a, b) in enumerate(zip(groups_a, groups_b), 1)]
    passed = (names == required and all(r["passed"] and
              r["stock_and_compiled_skin_palette_lod_record_exact"] and
              r["stock_and_compiled_vertex_stride_exact"] and
              r["stock_and_compiled_index_stride_exact"] for r in rows))
    record = {"schema": "ccp-060-authored-three-lod-native-comparison/v1",
              "status": "authored_three_lod_geometry_qualified" if passed else "authored_geometry_comparison_failed",
              "source_snapshot": str(snapshot_path), "source_snapshot_sha256": sha(snapshot_path),
              "source_fbx_sha256": sha(fbx), "stock_manifest": str(stock_path),
              "stock_manifest_sha256": sha(stock_path), "compiled_manifest": str(cooked_path),
              "compiled_manifest_sha256": sha(cooked_path), "native_archive_sha256": rb["archive_sha256"],
              "compiled_rrgeom_sha256": rb["resources"][".rrgeom"]["sha256"],
              "rig": rig, "compiled_group_material_effect": names, "lods": rows,
              "appended_panel_prior_snapshot": str(prior_panel_source) if prior_panel_source else None,
              "appended_panel_prior_snapshot_sha256": sha(prior_panel_source) if prior_panel_source else None,
              "comparison_basis": "authored_export_snapshot_not_stock_topology_or_shape",
              "neutral_diagnostic_material_excluded_from_final": True,
              "stock_rgo_and_stock_or_private_albedo_only_rrmaterial_pair_required": True,
              "gameplay_integration_and_native_runtime_unverified": True}
    write(report, record)
    if not passed: raise RuntimeError(f"Authored native geometry mismatch; evidence: {report}")
    return {"status": record["status"], "receipt": str(report)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=("prepare", "cook", "readback", "compare"))
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--report-name", default="comparison.json")
    args = ap.parse_args()
    if args.stage != "compare" and args.report_name != "comparison.json":
        ap.error("--report-name applies only to compare")
    result = compare(args.spec, args.report_name) if args.stage == "compare" else globals()[args.stage](args.spec)
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
