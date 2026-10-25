"""Read-only source check before a claimed villager Blender export slot.

The receipt describes source availability, not a successful native palette cook.
It is deliberately one-shot so later attempts cannot overwrite this checkpoint.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import ART, CORE, EXPORT, OUT, guard, owned, read, sha, write

CONTRACT = OUT / "qualification/villager-geometry-route/contract-v2.json"
DEST = OUT / "qualification/villager-geometry-route/20261018-resume/preflight.json"
SCRIPT = Path(__file__).with_name("export_villager_three_native_lods.py")
TEXTURE = OUT / "qualification/archer-stock-albedo-atlas.png"
TEXTURE_SHA = "f231747e68cd39bd1c6edcc7ecfc074f79013e4644bf0debb98d46650f0dacdc"


def main() -> dict:
    guard()
    owned(DEST)
    if DEST.exists():
        raise FileExistsError(f"Preserve prior villager preflight: {DEST}")
    contract = read(CONTRACT)
    if (contract["schema"] != "ccp-060-villager-geometry-route/v2"
            or contract["status"] != "source_contract_prepared_native_palette_cook_unproved"
            or set(contract["genders"]) != {"male", "female"}
            or contract["prototype"]["key"] != "english-villager-1"
            or contract["prototype"]["bone_count"] != 73
            or contract["prototype"]["prototype_palette_bones"] != 45
            or sha(CORE) != contract["prototype"]["core_sha256"]
            or sha(Path(contract["prototype"]["manifest"])) != contract["prototype"]["manifest_sha256"]
            or sha(Path(contract["comparison"]["path"])) != contract["comparison"]["sha256"]
            or sha(TEXTURE) != TEXTURE_SHA):
        raise RuntimeError("Pinned common villager input drift")
    rows = {}
    for gender, row in contract["genders"].items():
        expected = {"male": [1188, 434, 148], "female": [1312, 406, 188]}[gender]
        if (row["skeleton_bones"] != 73 or row["chinese_palette_bones"] != 46
                or [lod["triangles"] for lod in row["lods"]] != expected
                or [lod["material_name"] for lod in row["lods"]] != ["lod1", "lod2", "lod3"]):
            raise RuntimeError(f"{gender} source LOD/palette contract drift")
        sources = {
            "pilot_blend": (row["pilot_blend"], row["pilot_blend_sha256"]),
            "authoring_receipt": (row["authoring_receipt"], row["authoring_sha256"]),
            "donor_manifest": (row["donor_manifest"], row["donor_manifest_sha256"]),
            "native_model": (row["model_source"], row["model_sha256"]),
            "native_geometry": (row["geometry_source"], row["geometry_sha256"]),
            "native_material": (row["stock_rrmaterial_source"]["path"],
                                row["stock_rrmaterial_source"]["sha256"]),
        }
        for label, (path, digest) in sources.items():
            if sha(Path(path)) != digest:
                raise RuntimeError(f"{gender} {label} bytes changed")
        candidate_paths = [
            EXPORT / "villager-geometry-route" / gender / "stock-three-lod-control",
            ART / "villager-geometry-route" / gender / "stock-three-lod-control.blend",
            OUT / "qualification/villager-geometry-route" / gender / "export.json",
        ]
        for path in candidate_paths:
            owned(path)
            if path.exists():
                raise FileExistsError(f"Preserve existing export attempt: {path}")
        rows[gender] = {"pilot": row["pilot"], "donor": row["base"],
                        "source_hashes_verified": {label: digest for label, (_, digest) in sources.items()},
                        "native_lod_triangles": expected,
                        "export_destinations_available": [str(path) for path in candidate_paths],
                        "unresolved_palette_gate": "Chinese 46 active versus English 45 active bones"}
    receipt = {
        "schema": "ccp-060-villager-resume-preflight/v1",
        "status": "pinned_sources_verified_export_and_native_cook_not_run",
        "contract": str(CONTRACT), "contract_sha256": sha(CONTRACT),
        "exporter": str(SCRIPT), "exporter_sha256": sha(SCRIPT),
        "prototype_manifest_sha256": contract["prototype"]["manifest_sha256"],
        "installed_core_sha256": sha(CORE), "diagnostic_texture_sha256": sha(TEXTURE),
        "genders": rows,
        "next_gates": ["exclusive Blender handoff", "fresh source export per gender",
                       "normal installed unit validation", "independent native geometry-only cook",
                       "archive readback and donor comparison for all three LODs",
                       "unchanged gender-specific native material/selector pairing"],
        "no_generated_actor_or_animator_authorized": True,
        "no_active_gameplay_or_older_release_edit": True,
    }
    write(DEST, receipt)
    return {"status": receipt["status"], "receipt": str(DEST),
            "genders": sorted(rows), "exporter_sha256": receipt["exporter_sha256"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
