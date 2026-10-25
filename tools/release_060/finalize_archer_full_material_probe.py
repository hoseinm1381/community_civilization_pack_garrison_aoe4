"""Record fail-closed outcome of the one native full-material source experiment."""
from __future__ import annotations

import json
from pathlib import Path

from common import OUT, STAGING, guard, read, sha, write

ROOT = OUT / "qualification/material-native-probe"
COOK = ROOT / "cook.json"
OUTCOME = ROOT / "outcome.json"
PROJECT = STAGING / "n/Mods/n60a"
GENERATED = PROJECT / "project/source/art/scenario/garrison/n60a/units/n60a_m/body/model.material"
SOURCE = OUT / "qualification/archer-matched-control-export.json"


def main() -> None:
    guard()
    if OUTCOME.exists():
        raise FileExistsError(OUTCOME)
    cook = read(COOK)
    project = read(PROJECT / "mod-project.json")
    log = Path(next(x["log"] for x in cook["steps"] if x["name"] == "cook"))
    text = log.read_text(encoding="utf-8")
    needle = "Texture path [art/civilizations/chinese/humans/chi_ranged_bow_age02/15644768145151564932_packed.rrtex] not found"
    if (cook["status"] != "native_cook_rejected_full_material_preserved"
            or not cook["material_source_survived_cook"]
            or needle not in text
            or project.get("cooks")
            or sha(GENERATED) != cook["generated_material_sha256_after_edit_before_cook"]):
        raise RuntimeError("Isolated material failure evidence changed")
    source = read(SOURCE)
    source_dir = Path(source["folder"])
    source_ok = all(sha(source_dir / name) == record["sha256"]
                    for name, record in source["files"].items())
    if not source_ok:
        raise RuntimeError("Earlier control source changed")
    write(OUTCOME, {
        "schema": "ccp-060-archer-full-material-outcome/v1",
        "status": "normal_native_cook_rejected_stock_rrtex_source_reference",
        "cook_receipt": str(COOK), "cook_receipt_sha256": sha(COOK),
        "native_cook_log": str(log), "native_cook_log_sha256": sha(log),
        "first_native_fatal": needle,
        "first_failing_slot": "albedoTexture",
        "current_official_stock_ref_sha256": cook["stock_texture_refs"]["albedoTexture"]["sha256"],
        "material_source_pre_cook_sha256": cook["generated_material_sha256_after_edit_before_cook"],
        "material_source_post_cook_sha256": cook["generated_material_sha256_after_cook"],
        "material_source_preserved": True,
        "isolated_project_cook_records": len(project["cooks"]),
        "prior_control_source_hashes_unchanged": source_ok,
        "archive_or_material_readback_available": False,
        "interpretation": "The editor burner did not resolve the game's stock RRtex as a direct .material source texture. The source survived, but compilation stopped at the first slot. PatternTex and skinTintLUT were not reached, so this experiment does not prove whether the burner would accept them if staged as project-local sources.",
        "route_boundary": "Do not use this direct stock-path material source in a release. The supported Build Unit pattern PNG source route passed source validation, but skinTintLUT remains absent from its generated material and unqualified in native cook.",
        "next_action": "Stop this direct-reference route. Any copied-texture or native material-source alternative needs a separate bounded candidate; never patch compiled RRMaterial or the extension, and never integrate the diagnostic Spearman actor.",
    })
    print(json.dumps({"status": "normal_native_cook_rejected_stock_rrtex_source_reference",
                      "outcome": str(OUTCOME)}, indent=2))


if __name__ == "__main__":
    main()
