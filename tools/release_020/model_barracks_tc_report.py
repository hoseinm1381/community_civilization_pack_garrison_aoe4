"""Write concise, evidence-linked barracks/TC source handoff report."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_020/barracks_tc"
h = json.loads((OUT / "source-handoff.json").read_text())
n = json.loads((OUT / "native-byte-audit.json").read_text())
m = json.loads((OUT / "materials-ready.json").read_text())
s = json.loads((OUT / "donor-storage-move.json").read_text())
t = json.loads((OUT / "textured-preview-validation.json").read_text())
assert len(h["models"]) == len(n["models"]) == len(m["models"]) == 8
assert n["status"] == "passed" and m["registered_inputs_verified"] == 24
assert s["status"] == "passed" and s["total_files"] == 1374
assert {(r["family"], r["age"], r["state"]) for r in t} == {
    (family, 1, state) for family in ("barracks", "town_center") for state in ("before", "after")
}

lines = ["# Vietnamese Barracks and Town Center 0.2.0 source handoff", "",
         "The eight actual Chinese combined stamp models were decoded with installed Garrison 0.1.4 and remodeled at their existing scale and ground contacts. Each age keeps its native mesh topology and lifecycle fragments. The continuous map lowers tall roofs, broadens eaves and tempers the Chinese vertical silhouette. These are restrained regional Vietnamese interpretations, not reconstructions of one specific historic barracks or town center.", "",
         "The donor construction, damage, UV, index, material, collection and owner-colour contracts remain available for selective private integration. Other active stamp props, flags, fences and ornaments are owned by the integration graph and were not edited here. The game footprint and gameplay source were not touched.", "",
         "## Eight model inputs", "",
         "| Family | Age | Donor model | Native export | Vertices | Ground vertices fixed | Repeated contacts |", "| --- | ---: | --- | --- | ---: | ---: | ---: |"]
for row in h["models"]:
    lines.append(f"| {row['family']} | {row['age']} | `{row['logical_stock_model']}` | `{row['native_geometry']}` | {row['vertices']:,} | {row['ground_or_buried_vertices_unchanged']:,} | {row['repeated_contact_coordinates']:,} |")
lines += ["", "## Verification", "",
          f"- `tools/release_020/model_barracks_tc_manifest.py`: eight editable donor/remodel blends, eight native exports and their donor hashes; {sum(r['vertices'] for r in h['models']):,} decoded vertices inventoried.",
          "- `tools/release_020/model_barracks_tc_nativecheck.py`: all eight native exports passed installed Garrison Chunky readback. Every non-geometry leaf and every index buffer is byte-identical to its donor. Position, normal and tangent are the only edited native vertex fields; UV, selector and owner-related bytes remain native.",
          "- Every repeated donor interface coordinate remains coincident after quantization (maximum measured gap 0 m). Every vertex at or below ground Z=0 remains unchanged. The Jacobian was checked positive before each native buffer was rebuilt.",
          "- Solid before/after previews and packed editable `.blend` files are retained in `output/release_020/barracks_tc` and `art/authoring/buildings_020`. Preview renders are offline art checks; native culling, construction and owner colours remain untested in a match.",
          f"- The eight immutable decoded donor caches were moved to guarded project F: stock-cache with per-file hash verification. The receipt records {s['total_files']:,} files and {s['total_bytes']:,} bytes; source E: copies were removed only after verification.",
          "- Age-I barracks and Town Center have paired textured game/facade before/after PNGs and `textured-preview-validation.json`. Ages II-IV have paired solid game/facade PNGs; their material carriers are editable sources pending native cook.",
          "", "## Optional roof surfaces", "",
          "Twenty-four Garrison variant carriers are registered in the task-owned 0.2.0 project, two per barracks age and four per town-center age. Each changes one roof shingle or roof timber albedo using the donor texture's detail and alpha. Private PNGs and exact registered project copies have matching hashes in `art/recipes/release_020/barracks-tc-materials.json`. Native normal/metal/damage maps, masks and owner parameters are unchanged. These carriers are uncooked and optional until the integration owner validates the matching native material blocks.",
          "", "## Integration route", "",
          "The geometry exports use the private model path convention `art/scenario/cc020/{family}_age0N/model`. Preserve each original RGM/RGO/collection and the Chinese stamp's secondary parts; point only a private stamp's combined primary model to the corresponding verified private resource. All four Town Center consumers share the same four age attachment lists. Validate fresh native resources, reference closure, culling bounds, construction/damage, owner colours and byte-preserved gameplay before delivery. Garrison's generated game mode and Live Reload stay off.",
          "", "## Commands (from active Garrison root)", "",
          "```powershell", "& $python tools/verify_workspace.py --storage-only",
          "& 'E:/Blender5.2/blender.exe' --factory-startup -b --python tools/release_020/model_barracks_tc.py -- 1 2 3 4",
          "& $python tools/release_020/model_barracks_tc_manifest.py",
          "& 'E:/Blender5.2/5.2/python/bin/python.exe' tools/release_020/model_barracks_tc_nativecheck.py",
          "& $python tools/release_020/model_barracks_tc_projectcheck.py", "```", "",
          "Source checks and previews do not establish a Garrison cook, final package, import, lobby selection or native match. Those are separate release gates.", ""]
(OUT / "ART_HANDOFF.md").write_text("\n".join(lines), encoding="utf8")
print("ART_HANDOFF_REPORT_READY", len(h["models"]))
