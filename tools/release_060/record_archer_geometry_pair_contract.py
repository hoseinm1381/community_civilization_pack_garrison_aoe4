"""Pin stock Archer geometry/material IDs and private-selector preservation gates.

Read-only. This is a contract for a future real three-LOD export and native cook;
it does not admit an export, change gameplay, or prove animator runtime behavior.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

STATIC = OUT / "qualification/archer-pairing-prep/static-contract.json"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
TRACE = OUT / "donors/archer-trace.json"
VARIANT = OUT / "qualification/archer-variant-readback.json"
RIG = OUT / "qualification/archer-spearman-rig-comparison.json"
MATERIAL = OUT / "qualification/material-fidelity-assessment.json"
DEST = OUT / "qualification/archer-geometry-pair-contract.json"
STOCK_PATH = "art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02"
PRIVATE_PATH = "art/scenario/garrison/v60av/v60av_stock/v60av_stock"


def main() -> None:
    guard()
    owned(DEST)
    if DEST.exists():
        raise FileExistsError(f"Preserve earlier geometry-pair contract: {DEST}")
    static, donor, trace, variant, rig, material = (read(p) for p in
                                                    (STATIC, STOCK, TRACE, VARIANT, RIG, MATERIAL))
    if (static["status"] != "stock_variant_contract_pinned_new_geometry_unproved"
            or static["stock_manifest_sha256"] != sha(STOCK)
            or static["variant_readback_sha256"] != sha(VARIANT)
            or trace["status"] != "traced"
            or rig["status"] != "exact_bind_records_distinct_animation_owners"
            or variant["archive_sha256"] != sha(variant["archive"])
            or variant["source_model"] != STOCK_PATH
            or material["fidelity_conclusion"]["guide_disallows_treating_those_as_source_maps"] is not True):
        raise RuntimeError("Pinned donor/stock variant/material-fidelity evidence drift")
    body = trace["owners"]["body"]
    if sha(body["rgd"]) != body["rgd_sha256"] or sha(body["xml"]) != body["xml_sha256"]:
        raise RuntimeError("Official body attachment donor source drift")
    xml = ET.parse(body["xml"]).getroot()
    animator_refs = [node.get("Value") for node in xml.iter("RGDNode") if node.get("Key") == "animator0"]
    if len(animator_refs) != 3 or set(animator_refs) != {STOCK_PATH.replace("/", "\\")}:
        raise RuntimeError(f"Official Archer II body attachment refs changed: {animator_refs}")
    anim_source = donor["animation_projection"]["source"]
    if (anim_source["rhka_logical_path"] != "art/civilizations/common/humans/archetypes/base_archer/base_archer.rhka"
            or anim_source["runtime_selection_status"] != "not_decoded"):
        raise RuntimeError("Official linked animation source contract changed")
    compiled_slots = {}
    for item in donor["material"]["materials"]:
        slots = {tex["name"]: tex["logical_path"] for block in item["blocks"]
                 for tex in block["textures"] if tex["name"] != "__default"}
        compiled_slots[item["name"]] = slots
    if set(compiled_slots) != {"lod1", "lod2", "lod3"} or any(
            set(slots) != {"albedoTexture", "normalMap", "metalTex", "patternTex", "skinTintLUT"}
            for slots in compiled_slots.values()):
        raise RuntimeError("Stock three-material/five-slot table changed")
    rows = static["required_geometry_and_palette_lods"]
    expected_materials = [f"lod{i}" for i in (1, 2, 3)]
    if ([row["geometry_group"]["material"] for row in rows] != expected_materials
            or [row["skin_palette_name"] for row in rows]
            != [f"chi_ranged_bow_age02_lod{i}" for i in (1, 2, 3)]):
        raise RuntimeError("Stock RGM geometry/material/palette mapping changed")
    variant_hashes = {suffix: variant["extracted"][suffix]["sha256"]
                      for suffix in (".rgm", ".rgo", ".rrgeom", ".rrmaterial")}
    if (variant_hashes[".rgm"] != static["variant_rgm_sha256"]
            or not variant["extracted"][".rrmaterial"]["byte_identical_to_donor"]
            or not variant["extracted"][".rrgeom"]["byte_identical_to_donor"]):
        raise RuntimeError("Private stock selector/material/geometry freeze drift")
    contract = {
        "schema": "ccp-060-archer-geometry-stock-material-pair-contract/v1",
        "status": "source_and_private_selector_contract_pinned_three_lod_export_unrun",
        "evidence_sha256": {str(p): sha(p) for p in (STATIC, STOCK, TRACE, VARIANT, RIG, MATERIAL)},
        "official_model": STOCK_PATH, "private_stock_variant_model": PRIVATE_PATH,
        "official_body_attachment_member": body["member"],
        "official_body_attachment_rgd_sha256": body["rgd_sha256"],
        "official_body_attachment_animator0_values": animator_refs,
        "official_rhka_logical_path": anim_source["rhka_logical_path"],
        "official_rhka_sha256": anim_source["rhka_sha256"],
        "official_rhka_runtime_selection_decoded": False,
        "stock_geometry_rows": rows,
        "required_export_mesh_objects": [f"chi_ranged_bow_age02_lod{i}" for i in (1, 2, 3)],
        "required_compiled_group_name_per_lod": ["chi_ranged_bow_age02"] * 3,
        "required_material_ids_per_lod": expected_materials,
        "required_effect_per_lod": ["unit"] * 3,
        "required_skin_palette_names": [f"chi_ranged_bow_age02_lod{i}" for i in (1, 2, 3)],
        "stock_compiled_material_slots_by_lod": compiled_slots,
        "private_variant_archive": variant["archive"],
        "private_variant_archive_sha256": variant["archive_sha256"],
        "private_variant_resource_sha256": variant_hashes,
        "allowed_test_pair_change": PRIVATE_PATH + ".rrgeom",
        "required_test_pair_unchanged": [PRIVATE_PATH + suffix for suffix in (".rgm", ".rgo", ".rrmaterial")],
        "generated_prototype_actor_and_animation_resources_prohibited": True,
        "normal_cook_candidate_rrmaterial_is_diagnostic_only": True,
        "no_decoded_packed_map_reauthoring": True,
        "RGM_RGO_animator_preservation_boundary": (
            "In the isolated eight-member pairing, keep private RGM, RGO and byte-identical official RRMaterial unchanged; "
            "replace only RRGeom. No generated English Spearman actor, animator RGM/RGO/RHKA or RGD enters the pair. "
            "Any later private Vietnamese attachment binding may alter only its explicit model path, while the Chinese "
            "actor/inherited animation and weapon references stay frozen. RHKA runtime selection is not yet decoded; "
            "native animation compatibility remains a separate test."
        ),
        "future_vietnamese_texture_route": (
            "Use installed Garrison mod-project variant/variant-set on a fresh private stock model with an authored "
            "source albedo PNG or other intended slot. Cook/read back and require unchanged five-slot material table, "
            "especially patternTex and skinTintLUT, across all three LOD materials. Do not patch compiled RRMaterial. "
            "No texture change is part of the current stock-material geometry pair."
        ),
        "unsupported_claims": ["three-real-LOD export", "native 3-material cook", "RGO selector acceptance of new RRGeom",
                               "Chinese animator runtime behavior", "Vietnamese material appearance", "client import"],
    }
    write(DEST, contract)
    print(json.dumps({"status": contract["status"], "contract": str(DEST),
                      "source_model": STOCK_PATH, "materials": expected_materials}, indent=2))


if __name__ == "__main__":
    main()
