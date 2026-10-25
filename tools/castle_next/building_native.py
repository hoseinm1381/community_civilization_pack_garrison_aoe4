"""Remodel five Vietnamese Castle buildings from exact Chinese stock donors.

Run in task-owned factory-startup Blender. Only vertex position, normal and tangent
bytes change in the native RRGeom. Original UVs, indices, collection and masks stay.
"""
import bpy
import copy
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

import numpy as np
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import guarded

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
spec = importlib.util.spec_from_file_location("garrison_shared", str(EXT / "garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
from garrison_shared import relic_chunky as rc
sys.path.insert(0, str(EXT.parent))
import garrison
sys.modules["garrison.garrison_shared"] = shared
garrison.register()
from garrison.decode_projection import _apply_decoded_static

OUT = ROOT / "output/castle_next/buildings"
guarded()
OUT.mkdir(parents=True, exist_ok=True)
DONOR_MANIFEST = OUT.parent / "donors/donor-manifest.json"
JOBS = (("monastery", 3), ("monastery", 4),
        ("siege_workshop", 3), ("siege_workshop", 4), ("keep", 3))
sha = lambda b: hashlib.sha256(b).hexdigest()


def native_path(path):
    """Blender's Python uses the Windows 260-character limit without this prefix."""
    p = str(path)
    return Path("\\\\?\\" + p) if os.name == "nt" and len(p) >= 240 else Path(p)


def smooth(v, a, b):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def shape(points, family, age):
    """Continuous map shared by every construction and damage fragment.

    Keep footing and entry contacts; regionalize the roof silhouette by widening
    the timber eaves and lowering the tall Chinese ridge. The same smooth map is
    applied to all native material and lifecycle fragments, preserving contacts.
    """
    p = np.asarray(points, dtype=np.float64)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    # Parameters are proportions of existing donor mass, not measured percentages
    # of visually changed area. Review paired solids at each age before acceptance.
    profiles = {
        # Roof and high-facade articulation only; foundations, door contact,
        # attack positions and functional markers remain stock-owned.
        "monastery": (0.075, 0.065, 0.115, 0.055, 2.0),
        "siege_workshop": (0.050, 0.035, 0.060, 0.030, 2.1),
        "keep": (0.035, 0.035, 0.035, 0.020, 3.2),
    }
    spread_x, spread_y, lower, eave, side_start = profiles[family]
    age_factor = {3: 1.0, 4: 1.03}[age]
    high = smooth(z, 1.25, 3.25)
    new_x = x * (1 + spread_x * age_factor * high)
    new_y = y * (1 + spread_y * age_factor * high)
    new_z = z - lower * age_factor * np.maximum(z - 1.10, 0)
    new_z -= eave * age_factor * smooth(np.abs(x), side_start, side_start + 1.45) * smooth(z, 1.5, 3.6)
    return np.stack((new_x, new_y, new_z), axis=1)


def bounds(groups):
    pts = np.concatenate([np.asarray(g["positions"], dtype=np.float64) for g in groups])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    return {"minimum": lo.tolist(), "maximum": hi.tolist(), "dimensions": (hi - lo).tolist()}


def unit(v):
    length = np.linalg.norm(v, axis=1)
    return v / np.maximum(length[:, None], 1e-12)


def remodel_group(group, chunk, family, age):
    data = bytearray(chunk.payload)
    n, _, stride, _ = struct.unpack_from("<4I", data)
    assert stride == 24 and n == len(group["positions"])
    rawpos = np.ndarray((n, 4), dtype="<f2", buffer=data, offset=16, strides=(24, 2))
    original = np.stack((-rawpos[:, 0], -rawpos[:, 2], rawpos[:, 1]), axis=1).astype(np.float64)
    assert np.max(np.abs(original - np.asarray(group["positions"]))) < 1e-8
    nextpos = shape(original, family, age)
    moved = np.max(np.abs(nextpos - original), axis=1) > 1e-7
    eps = 1e-4
    jac = np.empty((n, 3, 3), dtype=np.float64)
    for axis in range(3):
        plus, minus = original.copy(), original.copy()
        plus[:, axis] += eps
        minus[:, axis] -= eps
        jac[:, :, axis] = (shape(plus, family, age) - shape(minus, family, age)) / (2 * eps)
    det = np.linalg.det(jac)
    assert float(det.min()) > 0.1
    normal_bytes = np.ndarray((n, 3), dtype=np.int8, buffer=data, offset=24, strides=(24, 1))
    tangent_bytes = np.ndarray((n, 3), dtype=np.int8, buffer=data, offset=28, strides=(24, 1))
    old_normals = unit(np.stack((-normal_bytes[:, 0], -normal_bytes[:, 2], normal_bytes[:, 1]), axis=1).astype(np.float64))
    old_tangents = unit(np.stack((-tangent_bytes[:, 0], -tangent_bytes[:, 2], tangent_bytes[:, 1]), axis=1).astype(np.float64))
    new_normals = unit(np.einsum("nij,nj->ni", np.linalg.inv(jac).transpose(0, 2, 1), old_normals))
    tangent = np.einsum("nij,nj->ni", jac, old_tangents)
    tangent = unit(tangent - new_normals * np.sum(tangent * new_normals, axis=1)[:, None])
    rawpos[:, 0] = -nextpos[:, 0]
    rawpos[:, 1] = nextpos[:, 2]
    rawpos[:, 2] = -nextpos[:, 1]
    normal_bytes[moved] = np.clip(np.rint(np.stack((-new_normals[moved, 0], new_normals[moved, 2], -new_normals[moved, 1]), axis=1) * 127), -127, 127).astype(np.int8)
    tangent_bytes[moved] = np.clip(np.rint(np.stack((-tangent[moved, 0], tangent[moved, 2], -tangent[moved, 1]), axis=1) * 127), -127, 127).astype(np.int8)
    # Even unchanged negative-zero half-floats retain their native sign bits.
    for i in np.flatnonzero(original[:, 2] <= 0):
        off = 16 + int(i) * 24
        data[off:off+24] = chunk.payload[off:off+24]
    quantized = np.stack((-rawpos[:, 0], -rawpos[:, 2], rawpos[:, 1]), axis=1).astype(float)
    group["positions"] = quantized.tolist()
    group["normals"] = unit(np.stack((-normal_bytes[:, 0], -normal_bytes[:, 2], normal_bytes[:, 1]), axis=1).astype(float)).tolist()
    # The fourth half-float, UV/selector bytes and tangent handedness byte stay native.
    assert all(data[16+i*24+6:16+i*24+8] == chunk.payload[16+i*24+6:16+i*24+8] for i in range(n))
    assert all(data[16+i*24+15:16+i*24+24] == chunk.payload[16+i*24+15:16+i*24+24] for i in range(n))
    changed = int(np.count_nonzero(np.max(np.abs(quantized - original), axis=1) > 0.003))
    return bytes(data), {"material": group["preview_material"], "vertices": n, "changed_vertices_over_3mm": changed, "max_half_error_m": float(np.max(np.linalg.norm(quantized - nextpos, axis=1))), "jacobian_min": float(det.min())}


def make_render(scene, name, frame_groups, prefix):
    bb = bounds(frame_groups)
    lo, hi = Vector(bb["minimum"]), Vector(bb["maximum"])
    center = (lo + hi) / 2
    # A diagonal view projects the long TC plan wider than its largest axis.
    # Use the plan diagonal so paired before/after images remain fully framed.
    span = ((hi.x-lo.x)**2 + (hi.y-lo.y)**2 + (hi.z-lo.z)**2)**.5
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 700
    scene.render.resolution_y = 570
    scene.render.resolution_percentage = 100
    views = (("iso", (1, -1, .8)), ("front", (0, -1, .2)),
             ("back", (0, 1, .2)), ("left", (-1, 0, .2)),
             ("right", (1, 0, .2)), ("top", (0, 0, 1)),
             ("bottom", (0, 0, -1)))
    for view, vec in views:
        cam = bpy.data.objects.new("Preview only", bpy.data.cameras.new("Preview only"))
        scene.collection.objects.link(cam)
        cam.location = center + Vector(vec).normalized() * span * 2
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = span * 1.35
        scene.camera = cam
        scene.render.filepath = str(OUT / f"{prefix}-{name}-{view}-solid.png")
        bpy.ops.render.render(write_still=True)
        if view == "iso":
            scene.display.shading.color_type = "TEXTURE"
            scene.render.filepath = str(OUT / f"{prefix}-{name}-iso-textured.png")
            bpy.ops.render.render(write_still=True)
            scene.display.shading.color_type = "MATERIAL"
        bpy.data.objects.remove(cam, do_unlink=True)
    scene.camera = None


assert bpy.app.background and not bpy.data.filepath
donor_index = json.loads(native_path(DONOR_MANIFEST).read_text(encoding="utf8"))
assert donor_index["schema"] == "community-civilization-pack/castle-next-stock-donors/v1"
assert donor_index["status"] == "resolved"
DONORS = donor_index["donors"]
assert set(DONORS) == {f"{family}{age:02}" for family, age in JOBS}
report_path = OUT / "model-validation.json"
report = json.loads(report_path.read_text()) if report_path.exists() else {"schema": "ccp.castle-next.native-source/v1", "status": "running", "models": [], "proof": "Source geometry and offline renders only; no cook/import/native match"}
requested = set(sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else set()
for family, age in JOBS:
    author = ROOT / f"art/authoring/castle_next/buildings/{family}/age{age:02}"
    exports = ROOT / f"art/exports/castle_next/buildings/{family}/age{age:02}"
    author.mkdir(parents=True, exist_ok=True)
    exports.mkdir(parents=True, exist_ok=True)
    if requested and family not in requested and str(age) not in requested and f"{family}:{age}" not in requested:
            continue
    donor = DONORS[f"{family}{age:02}"]
    source = Path(donor["decoded_static_manifest"])
    assert sha(native_path(source).read_bytes()) == donor["decoded_static_manifest_sha256"]
    assert donor["logical_path"].endswith(f"chi_{family}_control_age{age:02}.rgm")
    if donor["resolved"]:
        original = json.loads(source.read_text())
        donor_sha = {k: v["sha256"] for k, v in original["resources"].items() if isinstance(v, dict) and "sha256" in v}
        source_bytes = native_path(original["geometry"]["source"]["path"]).read_bytes()
        assert sha(source_bytes) == donor_sha["geometry"] == original["geometry"]["source"]["sha256"]
        projection = copy.deepcopy(original)
        doc = rc.parse(source_bytes)
        chunks = [c for c in rc.walk(doc.roots) if c.tag == b"GEOB"]
        groups = projection["geometry"]["groups"]
        assert len(chunks) == 2 * len(groups)
        replacements, stats = {}, []
        for gi, (g, c) in enumerate(zip(groups, chunks[::2])):
            payload, stat = remodel_group(g, c, family, age)
            replacements[c.offset] = payload
            stat.update({"group": gi, "index_sha256": sha(chunks[2 * gi + 1].payload)})
            stats.append(stat)
        encoded = rc.rebuild(doc, lambda c: replacements.get(c.offset))
        assert len(encoded) == len(source_bytes) and encoded != source_bytes
        name = f"vn_{family}_age{age:02}"
        target = exports / f"{name}.rrgeom"
        target.write_bytes(encoded)
        projected = author / f"{name}-projection.json"
        projected.write_text(json.dumps(projection), encoding="utf8")
        # Identical donor coordinates are exact shared interfaces across native fragments.
        seen, repeated, gap = {}, 0, 0.0
        for oldg, newg in zip(original["geometry"]["groups"], groups):
            for old, new in zip(oldg["positions"], newg["positions"]):
                key = tuple(old)
                if key in seen:
                    repeated += 1
                    gap = max(gap, float(np.linalg.norm(np.asarray(new) - seen[key])))
                else:
                    seen[key] = np.asarray(new)
        assert gap == 0.0
        bpy.ops.wm.read_factory_settings(use_empty=True)
        proxy = bpy.data.objects.new(f"Chinese {family} age{age:02} donor", None)
        bpy.context.scene.collection.objects.link(proxy)
        proxy["garrison_decode_manifest"] = str(source)
        proxy["garrison_logical_path"] = original["request"]["logical_path"]
        proxy["garrison_display_name"] = f"Chinese {family} age{age:02}"
        root = _apply_decoded_static(proxy, original, create_controls=False)
        scene = bpy.context.scene
        before = author / f"Chinese_{family}_age{age:02}_donor.blend"
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(before))
        make_render(scene, "before", original["geometry"]["groups"], name)
        for obj in [o for o in scene.objects if o.type == "MESH"]:
            gi = obj.get("garrison_mesh_index")
            if gi is None:
                continue
            g = groups[gi]
            assert len(obj.data.vertices) == len(g["positions"])
            for vert, co in zip(obj.data.vertices, g["positions"]):
                vert.co = co
            obj.data.normals_split_custom_set_from_vertices(g["normals"])
            obj.data.update()
            obj["ccp_native_geometry"] = str(target)
        root.name = f"Vietnam_{family}_Age{age:02}"
        after = author / f"Vietnam_{family}_Age{age:02}.blend"
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(after))
        make_render(scene, "after", original["geometry"]["groups"], name)
        row = {"family": family, "age": age, "name": name, "donor_manifest": str(source), "donor_resources_sha256": donor_sha,
               "donor_rrgeom_sha256": sha(source_bytes), "native_geometry": str(target), "native_geometry_sha256": sha(encoded),
               "donor_blend": str(before), "donor_blend_sha256": sha(before.read_bytes()), "editable_blend": str(after),
               "editable_blend_sha256": sha(after.read_bytes()), "projection": str(projected), "groups": stats,
               "before_bounds": bounds(original["geometry"]["groups"]), "after_bounds": bounds(groups),
               "contact_checks": {"repeated_coordinates": repeated, "max_gap_m": gap},
               "preserved": "All native index/UV/selector, fourth position half-float, tangent handedness, material/collection and external stamp bytes",
               "private_model_stem": f"art/scenario/cccastle/{family}_age{age:02}/model",
               "stock_model_stem": donor["logical_path"].removesuffix(".rgm")}
        report["models"] = [r for r in report["models"] if not (r["family"] == family and r["age"] == age)]
        report["models"].append(row)
        report["models"].sort(key=lambda r: (r["family"], r["age"]))
        (OUT / "model-validation.json").write_text(json.dumps(report, indent=2), encoding="utf8")
        print("CCP_MODEL_READY", family, age, flush=True)
report["status"] = "source_ready_for_integration"
(OUT / "model-validation.json").write_text(json.dumps(report, indent=2), encoding="utf8")
