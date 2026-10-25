"""Read back native RRGeom with the installed Garrison Chunky parser.

Runs under Blender's bundled Python, without starting Blender or a native cook.
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
spec = importlib.util.spec_from_file_location("garrison_shared", str(EXT / "garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
from garrison_shared import relic_chunky as rc


def native_path(p):
    s = str(p)
    return Path("\\\\?\\" + s) if os.name == "nt" and len(s) >= 240 else Path(s)


sha = lambda b: hashlib.sha256(b).hexdigest()
handoff = json.loads((ROOT / "output/release_040/buildings/model-validation.json").read_text())
result = {"schema": "ccp.buildings-040.native-byte-audit/v1", "status": "running", "models": []}
for row in handoff["models"]:
    donor_manifest = json.loads(native_path(row["donor_manifest"]).read_text())
    donor = native_path(donor_manifest["geometry"]["source"]["path"]).read_bytes()
    final = Path(row["native_geometry"]).read_bytes()
    assert sha(donor) == row["donor_rrgeom_sha256"]
    assert sha(final) == row["native_geometry_sha256"]
    old, new = rc.parse(donor), rc.parse(final)
    original_chunks = list(rc.walk(old.roots))
    final_chunks = list(rc.walk(new.roots))
    assert len(original_chunks) == len(final_chunks)
    geob = 0
    vertices = 0
    changed = 0
    fixed_ground_records = 0
    for a, b in zip(original_chunks, final_chunks):
        assert (a.tag, a.offset, a.decoded_name) == (b.tag, b.offset, b.decoded_name)
        assert len(a.payload) == len(b.payload)
        if a.children:
            # Container payload embeds its child bytes and necessarily changes.
            pass
        elif a.tag != b"GEOB" or geob % 2:
            assert a.payload == b.payload, (row["name"], a.tag, a.decoded_name)
        else:
            n, _, stride, _ = struct.unpack_from("<4I", a.payload)
            assert stride == 24 and a.payload[:16] == b.payload[:16]
            for i in range(n):
                k = 16 + i * 24
                # Native fourth position half-float, UVs, selector bytes and
                # tangent handedness remain byte-identical.
                assert a.payload[k+6:k+8] == b.payload[k+6:k+8]
                assert a.payload[k+11:k+12] == b.payload[k+11:k+12]
                assert a.payload[k+15:k+24] == b.payload[k+15:k+24]
                if struct.unpack_from("<e", a.payload, k + 2)[0] <= 0:
                    assert a.payload[k:k+24] == b.payload[k:k+24], (row["name"], "ground record", i)
                    fixed_ground_records += 1
                changed += a.payload[k:k+15] != b.payload[k:k+15]
            vertices += n
        if a.tag == b"GEOB":
            geob += 1
    assert geob == len(row["groups"]) * 2 and vertices == sum(g["vertices"] for g in row["groups"])
    result["models"].append({"name": row["name"], "chunks": len(original_chunks), "geob_chunks": geob,
                             "vertex_buffers": geob // 2, "vertices": vertices, "changed_vertices": changed,
                             "fixed_ground_records": fixed_ground_records,
                             "non_geob_chunks_byte_identical": True, "index_chunks_byte_identical": True,
                             "uv_selector_owner_bytes_preserved": True})
    print("NATIVE_BYTE_PASS", row["name"], vertices, flush=True)
result["status"] = "passed"
dest = ROOT / "output/release_040/buildings/native-byte-audit.json"
dest.write_text(json.dumps(result, indent=2), encoding="utf8")
print("NATIVE_BYTE_AUDIT_PASSED", len(result["models"]), flush=True)
