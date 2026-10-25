"""Freeze the unsupported generated-source refusal without retrying a cook."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from common import OUT, STAGING, guard, read, sha, write

DEST = OUT / "qualification/material-local-source-probe"
COOK = DEST / "cook.json"
OUTCOME = DEST / "outcome.json"
PROJECT = STAGING / "p/Mods/p60a"
MATERIAL = PROJECT / "project/source/art/scenario/garrison/p60a/units/p60a_m/body/model.material"


def main() -> None:
    guard()
    if OUTCOME.exists():
        raise FileExistsError(OUTCOME)
    receipt = read(COOK)
    log = Path(next(x["log"] for x in receipt["steps"] if x["name"] == "cook"))
    text = log.read_text(encoding="utf-8")
    expected = "p60a_m: generated unit source changed; rebuild from the Action"
    project = read(PROJECT / "mod-project.json")
    if (receipt["status"] != "native_cook_rejected_local_source_preserved"
            or expected not in text or not receipt["material_source_survived_cook"]
            or sha(MATERIAL) != receipt["candidate_material_sha256"]
            or project.get("cooks")):
        raise RuntimeError("Local material refusal evidence changed")
    pixels = {}
    for slot, info in receipt["texture_sources"].items():
        png = Path(info["png"])
        dds = Path(info["decoder_dds"])
        src, dest = Image.open(dds), Image.open(png)
        src.load(); dest.load()
        if (sha(png) != info["png_sha256"] or sha(dds) != info["decoder_dds_sha256"]
                or src.size != dest.size or src.mode != dest.mode or src.tobytes() != dest.tobytes()):
            raise RuntimeError(f"Stock texture PNG conversion drift: {slot}")
        pixels[slot] = {"dimensions": info["dimensions"], "rgba_pixel_sha256": info["rgba_pixel_sha256"],
                        "exact_top_mip": True}
    write(OUTCOME, {"schema": "ccp-060-archer-local-texture-outcome/v1",
                    "status": "normal_cook_refused_generated_unit_source_changes",
                    "cook_receipt": str(COOK), "cook_receipt_sha256": sha(COOK),
                    "normal_cook_log": str(log), "normal_cook_log_sha256": sha(log),
                    "first_error": expected, "five_converted_textures": pixels,
                    "material_source_pre_cook_sha256": receipt["material_source_sha256_before_cook"],
                    "material_source_post_cook_sha256": receipt["material_source_sha256_after_cook"],
                    "material_source_preserved": True,
                    "isolated_project_cook_records": len(project["cooks"]),
                    "archive_or_compiled_readback_available": False,
                    "interpretation": "The supported normal Garrison cook rejected manual changes to generated unit sources before native material burning. The local-PNG source idea remains unqualified; this refusal does not test whether the editor accepts skinTintLUT or whether repacked normal/PBR maps preserve stock semantics.",
                    "route_boundary": "Stop the manual generated-source route. Supported action textures can supply albedo, normal, roughness, metalness and pattern; no installed Build Unit field for skinTintLUT was found. Do not bypass source integrity or patch compiled resources.",
                    "generated_spearman_actor_never_integrated": True})
    print(json.dumps({"status": "normal_cook_refused_generated_unit_source_changes",
                      "outcome": str(OUTCOME)}, indent=2))


if __name__ == "__main__":
    main()
