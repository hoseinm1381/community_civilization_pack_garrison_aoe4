"""Read-only static contract check of the private stock variant RGM/RGO/material.

Builds a task-owned tiny index for the already cooked eight-member variant.
Nothing touches the installed index, Blender, project, or native cooker.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from common import ARCH, CORE, OUT, STAGING, guard, owned, read, sha, write

DEST = OUT / "qualification/archer-pairing-prep"
RECEIPT = DEST / "static-contract.json"
INDEX = DEST / "variant-index.sqlite3"
CONFIG = DEST / "variant-index-config.json"
DECODED = DEST / "variant-decoded"
LOG = DEST / "variant-decode.log"
STOCK = OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json"
VARIANT = OUT / "qualification/archer-variant-readback.json"
PROJECT = STAGING / "v/Mods/v60av/mod-project.json"
ORIGINAL_INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"
ORIGINAL_CONFIG = ORIGINAL_INDEX.with_name("game-assets.local.json")
LOGICAL = "art/scenario/garrison/v60av/v60av_stock/v60av_stock.rgm"


def tiny_index(archive: Path, members: list[dict], archive_id: str) -> None:
    source = sqlite3.connect("file:" + ORIGINAL_INDEX.as_posix() + "?mode=ro", uri=True)
    target = sqlite3.connect(INDEX)
    try:
        for table in ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types"):
            sql = source.execute("select sql from sqlite_master where type=? and name=?",
                                 ("table", table)).fetchone()[0]
            target.execute(sql)
        for key, value in source.execute("select key,value from metadata"):
            if key == "archive_count": value = "1"
            elif key in ("asset_count", "resolved_asset_count"): value = str(len(members))
            target.execute("insert into metadata(key,value) values(?,?)", (key, value))
        stat = archive.stat()
        target.execute("insert into archives values(?,?,?,?,?,?,?,?,?,?,?)",
                       (1, "cardinal", archive.name, str(archive), stat.st_size, stat.st_mtime_ns,
                        archive_id, "11", "0", 1, len(members)))
        for number, item in enumerate(members, 1):
            path = item["path"]
            if not path.startswith("art/"):
                continue
            folder, name = path.rsplit("/", 1)
            extension = Path(name).suffix.lower()
            template = source.execute("select asset_kind,curated_category,civilization,object_class,object_type "
                                      "from resolved_assets where extension=? limit 1", (extension,)).fetchone()
            kind, category, civilization, object_class, object_type = template or (
                "resource", "Other", "Shared / Neutral", "Resource", "Resource")
            raw_name = item["toc"] + ":" + path.replace("/", "\\")
            target.execute("insert into assets(id,archive_id,logical_path,folder,name,extension,asset_kind,curated_category,civilization,object_class,object_type,size,raw_name,verification,storage,encryption,preview_status,preview_path) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (number, 1, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item["size"], raw_name, item["verification"],
                            item["storage"], item["encryption"], "not_generated", None))
            target.execute("insert into resolved_assets(id,logical_path,folder,name,extension,asset_kind,curated_category,civilization,object_class,object_type,size,raw_name,preview_status,preview_path,product,archive,archive_path,provider_archive_id,archive_version,product_version,verified,provider_count) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (number, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item["size"], raw_name, "not_generated", None,
                            "cardinal", archive.name, str(archive), archive_id, "11", "0", 1, 1))
        target.commit()
    finally:
        target.close(); source.close()


def main() -> None:
    guard()
    for path in (RECEIPT, INDEX, CONFIG, DECODED, LOG):
        owned(path)
        if path.exists():
            raise FileExistsError(f"Preserve previous pairing static inspection: {path}")
    variant, stock, project = read(VARIANT), read(STOCK), read(PROJECT)
    archive = Path(variant["archive"])
    if (variant["status"] != "isolated_stock_material_variant_archive_verified_not_runtime_activated"
            or sha(archive) != variant["archive_sha256"]
            or project.get("key") != "v60av"
            or not project.get("mod_id")):
        raise RuntimeError("Pinned private variant evidence changed")
    result = subprocess.run([str(ARCH), "list", "--verify", str(archive)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(f"Variant archive list failed: {result.stderr[-800:]}")
    listing = json.loads(result.stdout)
    members = listing["members"]
    if ({x["path"] for x in members} != set(variant["exact_resource_allowlist"])
            or not listing["archive"]["verification"]["verified"]
            or len(members) != 8):
        raise RuntimeError("Private variant eight-member archive drift")
    DEST.mkdir(parents=True)
    tiny_index(archive, members, project["mod_id"].replace("-", ""))
    config = read(ORIGINAL_CONFIG)
    config["index_path"] = str(INDEX)
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    DECODED.mkdir(parents=True)
    cmd = [str(CORE), "convert", "decode-static", "--logical-path", LOGICAL,
           "--config", str(CONFIG), "--index", str(INDEX), "--output-root", str(DECODED)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    LOG.write_text("COMMAND: " + " ".join(cmd) + "\nEXIT: " + str(proc.returncode)
                   + "\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
                   encoding="utf-8")
    manifests = list(DECODED.glob("*/decoded-static.json"))
    if proc.returncode or len(manifests) != 1:
        write(RECEIPT, {"status": "decode_refused_preserved", "exit_code": proc.returncode,
                        "log": str(LOG), "log_sha256": sha(LOG), "manifest_paths": [str(x) for x in manifests]})
        raise RuntimeError(f"Variant static decode refused; inspect {LOG}")
    decoded = read(manifests[0])
    variant_groups = [(x["name"], x["material"], x["effect"], x["vertex_count"], x["triangle_count"])
                      for x in decoded["geometry"]["groups"]]
    stock_groups = [(x["name"], x["material"], x["effect"], x["vertex_count"], x["triangle_count"])
                    for x in stock["geometry"]["groups"]]
    vg, sg = decoded["skeleton"]["skin_palettes"], stock["skeleton"]["skin_palettes"]
    bind = (decoded["skeleton"]["bones"] == stock["skeleton"]["bones"]
            and len(vg) == len(sg) == 1
            and vg[0]["bones"] == sg[0]["bones"]
            and [x["skin_indices"] for x in vg[0]["lod_palettes"]]
                == [x["skin_indices"] for x in sg[0]["lod_palettes"]])
    stock_materials = {x["name"]: {t["name"]: t["logical_path"]
                              for block in x["blocks"] for t in block["textures"]
                              if t["name"] != "__default"}
                       for x in stock["material"]["materials"]}
    variant_materials = {x["name"]: {t["name"]: t["logical_path"]
                                for block in x["blocks"] for t in block["textures"]
                                if t["name"] != "__default"}
                         for x in decoded["material"]["materials"]}
    exact_geo = variant_groups == stock_groups and (
        variant["extracted"][".rrgeom"]["sha256"] == stock["geometry"]["source"]["sha256"])
    exact_material = variant_materials == stock_materials and (
        variant["extracted"][".rrmaterial"]["sha256"] == stock["material"]["source"]["sha256"])
    status = ("stock_variant_static_contract_exact"
              if decoded["status"] == "decoded" and exact_geo and exact_material and bind
              else "stock_variant_static_contract_mismatch")
    write(RECEIPT, {"schema": "ccp-060-archer-pairing-static-contract/v1", "status": status,
                    "variant_archive": str(archive), "variant_archive_sha256": sha(archive),
                    "variant_rgo_sha256": variant["extracted"][".rgo"]["sha256"],
                    "variant_rgm_sha256": variant["extracted"][".rgm"]["sha256"],
                    "variant_rrmaterial_sha256": variant["extracted"][".rrmaterial"]["sha256"],
                    "decoded_variant_manifest": str(manifests[0]),
                    "decoded_variant_manifest_sha256": sha(manifests[0]),
                    "private_index": str(INDEX), "private_index_sha256": sha(INDEX),
                    "private_config": str(CONFIG), "private_config_sha256": sha(CONFIG),
                    "decode_log": str(LOG), "decode_log_sha256": sha(LOG),
                    "stock_manifest": str(STOCK), "stock_manifest_sha256": sha(STOCK),
                    "variant_geometry_groups": variant_groups, "stock_geometry_groups": stock_groups,
                    "geometry_group_records_and_bytes_exact": exact_geo,
                    "complete_skeleton_bind_and_lod_skin_records_exact": bind,
                    "variant_material_slots": variant_materials,
                    "stock_material_slots": stock_materials,
                    "material_slots_and_bytes_exact": exact_material,
                    "rgo_boundary": "The private RGO is unchanged and the stock variant cook/readback proved it with the original geometry. No standalone RGO selector parser or engine consumer test is claimed; candidate geometry must retain the exact group/material/effect names and full bind records before selective pairing.",
                    "no_new_geometry_or_native_runtime_claim": True})
    print(json.dumps({"status": status, "receipt": str(RECEIPT),
                      "groups_exact": exact_geo, "bind_exact": bind,
                      "materials_exact": exact_material}, indent=2))


if __name__ == "__main__":
    main()
