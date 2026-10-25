"""Bounded exact-native rattan attachment compatibility gate; no actor cook."""
from __future__ import annotations

import json
from pathlib import Path

from common import ART, OUT, guard, owned, read, sha, write
from rattan_attachment_route import list_attachment_evidence

BASE = OUT / "rattan-probe/native-gate-v1"
ROUTE = OUT / "rattan-probe/attachment-route.json"
MATRIX = OUT / "rattan-probe/compatibility-matrix.json"
RGO = OUT / "qualification/native-rgo-controls/proof-first49.json"
STOCK = OUT / ("qualification/archer-pairing-prep/animation-owners/"
               "animation-owners-2m2rxfvb/attrib/attachments/attachment_lists")
SAMPLES = (
    "races/core/units/unit_swordshield",
    "civilizations/french/units/campaign/tier1_shield_villager_cmp_fre",
    "civilizations/french/units/campaign/french_champion_no_shield_cmp_fre",
)
RANGED_MODELS = (
    "chi_ranged_bow_age02", "chi_ranged_bow_age03", "chi_ranged_bow_age04",
    "chi_ranged_crossbow_age03", "chi_ranged_crossbow_age04",
    "chi_ranged_cannoneer_age04",
)
PRESERVED = (
    "assets/scar/vietnam/rattan_armor.scar",
    "assets/attrib/instances/upgrade/vietnam/vn_ratten_shield_vit.xml",
)


def main() -> None:
    guard()
    target = owned(BASE / "qualification.json")
    if target.exists():
        raise FileExistsError("Preserve prior rattan compatibility gate")
    route, matrix, rgo = read(ROUTE), read(MATRIX), read(RGO)
    rows = route["six_official_chinese_tier_attachment_records"]
    if (len(rows) != 6 or not route["finding"]["six_records_have_only_single_static_body_mesh_entry"]
            or not route["finding"]["six_records_have_no_explicit_requirement_or_visibility_fields"]):
        raise RuntimeError("Pinned Chinese tier attachment evidence changed")
    if matrix["status"] != "static_source_and_source_parity_compiled_reconciliation_complete_runtime_unqualified":
        raise RuntimeError("Pinned tier compatibility status changed")
    if rgo["status"] != "all_exact_installed_stock_rgos_preserved":
        raise RuntimeError("Native RGO preservation proof changed")

    samples = []
    for name in SAMPLES:
        raw = STOCK / (name + ".rgd")
        decoded = owned(BASE / (Path(name).name + ".xml"))
        if not raw.is_file() or not decoded.is_file():
            raise FileNotFoundError(name)
        record = list_attachment_evidence(decoded, {"member": name + ".rgd",
                                                   "raw_sha256": sha(raw),
                                                   "decoded_sha256": sha(decoded)})
        samples.append(record)
    rgo_rows = {}
    for model in RANGED_MODELS:
        found = [row for row in rgo["rows"]
                 if row["stock_member"].endswith(f"/{model}/{model}.rgo")]
        if not found or not all(row["native_rgo_byte_identical"] for row in found):
            raise RuntimeError(f"Stock RGO identity unproved: {model}")
        rgo_rows[model] = [{"stock_member": row["stock_member"],
                            "private_rgo_sha256": row["private_rgo"]["sha256"],
                            "byte_identical_to_installed_stock": True} for row in found]
    preserved = []
    for relative in PRESERVED:
        active = Path(relative)
        frozen = OUT / "baseline/final053/source" / relative
        if not active.is_file() or not frozen.is_file():
            raise FileNotFoundError(relative)
        preserved.append({"path": relative, "active_sha256": sha(active),
                          "frozen_053_sha256": sha(frozen),
                          "byte_identical": sha(active) == sha(frozen)})
    if not all(item["byte_identical"] for item in preserved):
        raise RuntimeError("Existing rattan armor owner or upgrade changed")

    blend_dir = ART / "authoring/release_060/archer"
    art = sorted(p for p in blend_dir.glob("*rattan*.blend") if p.is_file())
    exports = sorted(p for p in (ART / "exports/release_060").rglob("*")
                     if p.is_file() and "rattan" in p.as_posix().lower())
    report = {
        "schema": "ccp-060-rattan-native-attachment-gate/v1",
        "status": "deferred_no_schema_proven_isolated_attachment",
        "prior_route": str(ROUTE), "prior_route_sha256": sha(ROUTE),
        "prior_matrix": str(MATRIX), "prior_matrix_sha256": sha(MATRIX),
        "official_stock_attachment_samples": samples,
        "six_chinese_tier_lists": [{"member": row["member"],
                                    "single_static_body_mesh_per_variant": True,
                                    "explicit_condition_fields": False} for row in rows],
        "ranged_stock_rgo_identity": rgo_rows,
        "rgo_proof_sha256": sha(RGO),
        "preserved_existing_armor_and_upgrade": preserved,
        "editable_rattan_art": [{"path": str(p), "sha256": sha(p)} for p in art],
        "exported_modular_rattan_media": [str(p) for p in exports],
        "schema_proven_upgrade_conditioned_overlay": False,
        "cook_attempted": False,
        "reason_no_cook": ("Six official Chinese tier lists each select one static body mesh; "
                           "the bounded shield examples expose no research condition; "
                           "the Japanese pavise upgrade points to an unresolved action tree; "
                           "no modular rattan overlay FBX/LOD export exists. A private cook "
                           "could only prove static replacement or an invented condition, "
                           "which would not qualify retained actor/orders/actions."),
        "activation_allowed": False,
        "native_match_behavior_unproved": True,
    }
    write(target, report)
    print(json.dumps({"status": report["status"], "report": str(target),
                      "stock_samples": len(samples), "native_rgos": len(rgo_rows),
                      "source_owners_preserved": len(preserved),
                      "exported_overlay_media": len(exports)}, indent=2))


if __name__ == "__main__":
    main()
