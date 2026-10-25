"""Fresh isolated 0.7.0 Garrison object-PBR cook from a frozen art handoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import msvcrt
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

CFG = configuration(ROOT)
EXT = Path(CFG["external_root"])
LOCK = EXT / "output/release_020/native-build.lock"
NAMES = {"garden", "foundry", "university", "wonder"}
PARTS = [f"garrison_part_{n:04}" for n in range(7)]
STAGES = [0, 20, 0, 80, 20, 20, 20]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fbx_part_model_names(path: Path) -> list[str]:
    """Read binary FBX Model string fields, avoiding Geometry/material names."""
    raw = path.read_bytes()
    if not raw.startswith(b"Kaydara FBX Binary"):
        raise ValueError("Expected Garrison binary FBX export")
    names = []
    needle = b"\x05ModelL"
    at = 0
    while (at := raw.find(needle, at)) >= 0:
        string_at = at + len(needle) + 8  # binary FBX 64-bit model object ID
        if raw[string_at:string_at + 1] != b"S":
            raise ValueError("Unexpected binary FBX Model name field")
        size = int.from_bytes(raw[string_at + 1:string_at + 5], "little")
        name = raw[string_at + 5:string_at + 5 + size].split(b"\0", 1)[0].decode("utf-8")
        if name.startswith("garrison_part_"):
            names.append(name)
        at = string_at + 5 + size
    return names


def fbx_part_polygon_corners(path: Path) -> dict[str, int]:
    raw = path.read_bytes()
    starts = [match.start() for match in re.finditer(b"\x08GeometryL", raw)]
    corners = {}
    if len(starts) != len(PARTS):
        raise ValueError("Expected exactly seven FBX Geometry Mesh nodes")
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(raw)
        name = re.search(rb"garrison_part_[0-9]{4}", raw[start:start + 220])
        vertex_index = raw.find(b"PolygonVertexIndexi", start, end)
        if vertex_index < 0:
            raise ValueError("FBX Geometry node lacks polygon indices")
        key = PARTS[index]
        if name is not None and name.group().decode("ascii") != key:
            raise ValueError("FBX Geometry order differs from assigned parts")
        if key in corners:
            raise ValueError("Duplicate FBX geometry part " + key)
        corners[key] = int.from_bytes(raw[vertex_index + len(b"PolygonVertexIndexi"):
                                          vertex_index + len(b"PolygonVertexIndexi") + 4], "little")
    return corners


def run(out: Path, label: str, args: list[str], timeout=2100) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)
    (out / f"{label}.log").write_text("COMMAND: " + " ".join(args) +
            f"\nEXIT: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{label} failed, see {out / (label + '.log')}")
    return proc.stdout


def main(family: str, source: Path, label: str, work_tag: str | None = None) -> None:
    check_storage(ROOT, CFG)
    if family not in NAMES or not label.replace("-", "").isalnum():
        raise ValueError("Invalid family or cook label")
    source = source.resolve(strict=True)
    exports = (ROOT / "art/exports/buildings_070").resolve(strict=True)
    if not source.is_relative_to(exports):
        raise ValueError("Art source must be inside owned 0.7.0 export root")
    required = {"model.fbx", "building.json", "albedo.png", "normal.png",
                "roughness.png", "metalness.png"}
    files = {p.name: digest(p) for p in source.iterdir() if p.is_file()}
    supplemental_proofs = {}
    if not required.issubset(files):
        raise ValueError(f"Missing required exports: {sorted(required - files.keys())}")
    building = json.loads((source / "building.json").read_text(encoding="utf-8"))
    if (building.get("schema") != "garrison.building-source/v1"
            or building.get("profile") != "english-house"
            or [p["name"] for p in building["parts"]] != PARTS
            or [p["first_stage"] for p in building["parts"]] != STAGES):
        raise ValueError("Seven-part object-PBR lifecycle contract mismatch")
    model_names = fbx_part_model_names(source / "model.fbx")
    if len(model_names) != 7 or sorted(model_names) != PARTS:
        raise ValueError(f"Actual FBX Model names differ from assigned parts: {model_names}")
    if family == "garden":
        receipt_file = source / "source-receipt.json"
        if not receipt_file.is_file():
            raise ValueError("Garden detailed export receipt required")
        art = json.loads(receipt_file.read_text(encoding="utf-8"))
        expected_selectors = {"healthy": [0, 1, 4, 5, 6],
                              "heavy_damage": [0, 3], "ruins": [2]}
        if source.name == "garden":
            expected_collection = "CCP070_Imperial_Garden_Detailed_r2"
        elif source.name == "garden-r3":
            expected_collection = "CCP070_Imperial_Garden_Detailed_r3"
        elif source.name == "garden-r4":
            expected_collection = "CCP070_Imperial_Garden_Detailed_r4"
        elif source.name == "garden-r5":
            expected_collection = "CCP070_Imperial_Garden_Detailed_r4"
        else:
            raise ValueError("Garden export revision directory is not approved")
        if (art.get("input_collection") != expected_collection
                or art.get("selector_parts") != expected_selectors
                or art.get("native_stamp_transform_baked") is not False
                or art.get("files_sha256") != {name: files[name] for name in required}
                or set(art.get("per_part_triangle_count", {})) != {str(i) for i in range(7)}
                or any(v <= 0 for v in art["per_part_triangle_count"].values())
                or art.get("healthy_triangle_count") != sum(
                    art["per_part_triangle_count"][str(i)] for i in (0, 1, 4, 5, 6))
                or art.get("healthy_triangle_count", 0) >= 90000):
            raise ValueError("Garden export semantic/hashes do not match approved lifecycle revision")
        if source.name == "garden-r5" and (
                art.get("revision") != "r5-exact-part-names-from-r4-source"
                or art.get("fbx_model_nodes") != PARTS):
            raise ValueError("Garden r5 exact binary Model-node export receipt mismatch")
        if source.name in ("garden-r4", "garden-r5"):
            proof_root = EXT / "output/release_070/art/detail"
            roof_file = proof_root / "garden-r3-roof-seated.json"
            terrain_file = proof_root / "garden-r4-terrain-base.json"
            roof = json.loads(roof_file.read_text())
            terrain = json.loads(terrain_file.read_text())
            supplemental_proofs = {str(path): digest(path) for path in (roof_file, terrain_file)}
            fit = art["model_local_fit"]
            if (roof.get("revision") != "CCP070_Imperial_Garden_Detailed_r3"
                    or roof.get("unseated") != [] or roof.get("tiles_seated", 0) < 1
                    or terrain.get("revision") != expected_collection
                    or terrain.get("roof_and_uv_geometry_preserved") is not True
                    or terrain.get("world_recess_floor", -1) <= 0
                    or terrain.get("world_base_bottom", 1) >= 0
                    or art.get("roof_seating_proof", {}).get("sha256") != digest(roof_file)
                    or art.get("roof_seating_proof", {}).get("unseated") != 0
                    or art.get("terrain_clearance_proof", {}).get("sha256") != digest(terrain_file)
                    or art.get("terrain_clearance_proof", {}).get("water_world_z", -1) <= 0
                    or abs(fit.get("z_shift", -1) - terrain.get("export_z_shift", -2)) > 1e-8
                    or abs(fit.get("z_shift", -1) - 0.13) > 1e-8):
                raise ValueError("Garden r4 roof/base/grade proof missing or inconsistent")
    else:
        receipt_file = source / "source-receipt.json"
        if not receipt_file.is_file():
            raise ValueError(f"{family} detailed export receipt required")
        art = json.loads(receipt_file.read_text(encoding="utf-8"))
        expected_collection = {"foundry": "CCP070_Trung_Foundries_Detailed_r3",
                               "university": "CCP070_University_Detailed_Overlay_r6",
                               "wonder": "CCP070_Kinh_Thien_Detailed_r4"}[family]
        expected_selectors = {"healthy": [0, 1, 4, 5, 6],
                              "heavy_damage": [0, 3], "ruins": [2]}
        triangles = art.get("per_part_triangles", {})
        roof = art.get("roof_seating_proof")
        if (art.get("kind") != family or art.get("input_collection") != expected_collection
                or art.get("selector_parts") != expected_selectors
                or art.get("native_stamp_transform_baked") is not False
                or art.get("files_sha256") != {name: files[name] for name in required}
                or set(triangles) != {str(i) for i in range(7)}
                or any(v <= 0 for v in triangles.values())
                or art.get("healthy_triangles") != sum(triangles[str(i)] for i in (0,1,4,5,6))
                or art["healthy_triangles"] >= 90000):
            raise ValueError(f"{family} export semantic/contact/hashes invalid")
        if family != "university" and (
                not roof or not roof.get("tiles_seated") or roof.get("unseated") != 0
                or digest(Path(roof["path"])) != roof["sha256"]):
            raise ValueError(f"{family} roof proof mismatch")
        if family == "university":
            shift = art.get("fit", {}).get("shift")
            expected_shift = [-2.338015973567963, 3.7076730728149423, 0.0]
            final_proof = art.get("university_final_proof")
            proof = json.loads(Path(final_proof["path"]).read_text()) if final_proof else {}
            if (art.get("university_stock_body_preserved_outside_export") is not True
                    or not shift or any(abs(a-b) > 1e-8 for a,b in zip(shift, expected_shift))
                    or not final_proof or digest(Path(final_proof["path"])) != final_proof["sha256"]
                    or proof.get("status") != "passed"
                    or proof.get("original_four_stock_groups_vertices_exact") is not True
                    or proof.get("five_nonroof_nonfurniture_parts_geometry_uv_exact") is not True
                    or proof.get("failed_roof_accents") != []
                    or proof.get("supported_roof_accents", 0) < 1):
                raise ValueError("University stock-body/pot-transform contract mismatch")
        if family == "foundry":
            terrain = art.get("terrain_clearance_proof")
            if (not terrain or terrain.get("recess_world_z", -1) <= 0
                    or digest(Path(terrain["path"])) != terrain["sha256"]
                    or abs(art["fit"]["shift"][2] - 0.23) > 1e-8):
                raise ValueError("Foundry pit/platform clearance proof mismatch")
        if family == "wonder":
            repartition = art.get("wonder_repartition_proof")
            proof = json.loads(Path(repartition["path"]).read_text()) if repartition else {}
            actual_corners = fbx_part_polygon_corners(source / "model.fbx")
            expected_corners = {f"garrison_part_{int(part):04}": count for part, count
                                in proof.get("after_per_part_corners", {}).items()}
            if (not repartition or digest(Path(repartition["path"])) != repartition["sha256"]
                    or proof.get("revision") != expected_collection
                    or proof.get("healthy_face_position_uv_multiset_exact") is not True
                    or proof.get("five_other_parts_exact") is not True
                    or proof.get("part4_and_5_first_stage") != 20
                    or proof.get("moved_closed_tile_pans") != 1014
                    or actual_corners != expected_corners
                    or max(actual_corners.values(), default=999999) >= 60000):
                raise ValueError("Wonder FBX healthy repartition proof mismatch")
    out = ROOT / "output/release_070/integration" / f"{family}-{label}"
    if work_tag is not None and (not work_tag.replace("-", "").isalnum() or len(work_tag) > 16):
        raise ValueError("Short work tag must be <=16 alphanumeric/hyphen characters")
    work = (EXT / "staging/r70" / work_tag if work_tag is not None else
            EXT / "staging/release_070/integration" / f"{family}-{label}")
    if out.exists() or work.exists():
        raise FileExistsError("Preserve existing cook attempt")
    out.mkdir(parents=True)
    work.mkdir(parents=True)
    staged = work / "inputs" / family
    shutil.copytree(source, staged)
    if {p.name: digest(p) for p in staged.iterdir() if p.is_file()} != files:
        raise RuntimeError("Staged art differs from source")
    project_name = f"cc070{family}"
    library = work / "library"
    project = library / "Mods" / project_name
    freeze = {"schema": "ccp-070-building-cook-input/v1", "family": family,
              "source": str(source), "staged": str(staged), "work_root": str(work),
              "hashes": files,
              "fbx_model_names": model_names,
              "supplemental_proofs": supplemental_proofs,
              "building": building, "baseline_sga_sha256":
              "9e797ab14faf293ec1570c6dc38f1e7cab2ffda9df7d5078b7a0ecf564233c85"}
    (out / "input-freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    core = str(CFG["garrison_core"])
    with LOCK.open("r+b") as stream:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        try:
            run(out, "create", [core, "mod-project", "create", "--library", str(library),
                                "--name", project_name], timeout=120)
            run(out, "settings", [core, "mod-project", "settings", "--project", str(project),
                                  "--live-reload", "off"], timeout=120)
            run(out, "register", [core, "mod-project", "building", "--project", str(project),
                                  "--source", str(staged), "--name", family,
                                  "--profile", "english-house", "--integration", "script"], timeout=300)
            cfg = json.loads((project / "mod-project.json").read_text())
            if cfg["game_mode"]["enabled"] or cfg["game_mode"]["live_reload"]:
                raise RuntimeError("Garrison game mode or Live Reload unexpectedly enabled")
            result = run(out, "native-cook", [core, "mod-project", "cook", "--project",
                         str(project), "--editor", str(CFG["art_editor"]), "--timeout", "1800"])
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    archive = project / "dist" / (project_name + ".sga")
    if not archive.is_file():
        raise RuntimeError("No fresh cooked archive")
    readback = out / "readback"
    run(out, "readback", [str(CFG["archive_tool"]), "extract", str(archive),
                          str(readback), "--filter", "."], timeout=600)
    model = readback / "art/scenario/garrison" / project_name / "buildings" / family
    media = {p.name: digest(p) for p in model.iterdir() if p.is_file()}
    if not {"model.rgm", "model.rrgeom", "model.rrmaterial"}.issubset(media):
        raise RuntimeError("Native model/geometry/material readback incomplete")
    if {p.name: digest(p) for p in source.iterdir() if p.is_file()} != files:
        raise RuntimeError("Art source changed during cook")
    receipt = {"schema": "ccp-070-building-native-cook/v1",
               "status": "fresh_native_cook_and_readback_complete_runtime_unverified",
               "family": family, "archive": str(archive), "archive_sha256": digest(archive),
               "model_readback": str(model), "media": media,
               "input_freeze_sha256": digest(out / "input-freeze.json"),
               "nonvisual_actor_and_footprint": "unchanged"}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"family": family, "receipt": str(out / "receipt.json"),
                      "archive_sha256": digest(archive)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("family", choices=sorted(NAMES))
    parser.add_argument("source", type=Path)
    parser.add_argument("--label", default="cook-v1")
    parser.add_argument("--work-tag", help="Short immutable owned staging root for native editor path limits")
    args = parser.parse_args()
    main(args.family, args.source, args.label, args.work_tag)
