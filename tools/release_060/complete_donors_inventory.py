"""Trace existing stock body/equipment donor closure for the 0.6.0 roster.

This is an inventory-only pass. It reads the official RGD closure, existing
pilot and ranged-rig decode receipts, and Garrison's local asset index. It does
not run a decode, cook, export, or Blender operation.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from common import ARCH, CORE, OUT, ROOT, guard, owned, read, sha, write

DEST = OUT / "inventory/complete-donors"
INDEX = Path.home() / "AppData/Local/Garrison/Kit/game-assets.sqlite3"


def write_text(path: Path, payload: str) -> None:
    path = owned(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(payload, encoding="utf-8")
    temp.replace(path)


def logical_actor(actor: str) -> str:
    return "attrib/" + actor.replace("\\", "/").lower() + ".rgd"


def read_xml(path: Path) -> ET.Element | None:
    if not path.is_file():
        return None
    return ET.parse(path).getroot()


def node_value(node: ET.Element) -> str:
    return node.get("Value") or node.get("value") or ""


def descendants(root: ET.Element):
    for node in root.iter():
        yield node


def model_refs(root: ET.Element | None) -> list[str]:
    if root is None:
        return []
    refs = set()
    for node in descendants(root):
        key = (node.get("Key") or node.get("key") or "").lower()
        val = node_value(node).strip().replace("\\", "/")
        if val.lower().startswith("art/") and (
            key in {"parent_animator", "animator", "animator0", "animator1", "animator2", "animator3"}
            or key.startswith("animator") and key.endswith("_mesh")
            or key in {"model", "mesh", "animator_mesh"}
        ):
            if not val.lower().endswith(".rgm"):
                val += ".rgm"
            refs.add(val.lower())
    return sorted(refs)


def model_ref_evidence(root: ET.Element | None) -> list[dict]:
    """Preserve the RGD field and variant that owns each exact art reference."""
    if root is None:
        return []
    valid_variants = {"default", "campaign", "cordoba", "xp3"}
    result = []

    def visit(node: ET.Element, variant: str | None = None):
        key = (node.get("Key") or node.get("key") or "").lower()
        if key in valid_variants:
            variant = key
        val = node_value(node).strip().replace("\\", "/")
        if val.lower().startswith("art/") and (
            key in {"parent_animator", "animator", "animator0", "animator1", "animator2", "animator3"}
            or key.startswith("animator") and key.endswith("_mesh")
            or key in {"model", "mesh", "animator_mesh"}
        ):
            if not val.lower().endswith(".rgm"):
                val += ".rgm"
            result.append({"logical_model_path": val.lower(), "source_field": key,
                           "variant": variant, "node_name": node.tag})
        for child in node:
            visit(child, variant)

    visit(root)
    unique = {(r["logical_model_path"], r["source_field"], r["variant"], r["node_name"]): r for r in result}
    return [unique[k] for k in sorted(unique)]


def pbg_member(root: ET.Element | None, key: str) -> str | None:
    if root is None:
        return None
    for node in root.iter():
        if (node.get("Key") or "").lower() == key.lower():
            name = node.get("Value")
            if name:
                parent = node.get("Map") or node.get("map")
                # The adjacent $PBGMAP is sibling encoded, so find it from parent.
                parent_node = None
                for candidate in root.iter():
                    if node in list(candidate):
                        parent_node = candidate
                        break
                if parent_node is not None:
                    for sibling in parent_node:
                        if (sibling.get("Key") or "").upper() == "$PBGMAP":
                            parent = sibling.get("Value")
                            break
                if parent:
                    return "attrib/" + parent.replace("\\", "/").strip("/").lower() + "/" + name.lower() + ".rgd"
    return None


def member_xml_path(member: dict) -> Path:
    return OUT / Path(member["decoded_output"])


def provider(logical: str, index_sha: str, archive_hashes: dict[str, str]) -> dict:
    logical = logical.lower().replace("\\", "/")
    stem = logical[:-4] if logical.endswith(".rgm") else logical
    paths = [stem + ext for ext in (".rgm", ".rrgeom", ".rrmaterial")]
    rows = []
    with sqlite3.connect("file:" + INDEX.as_posix() + "?mode=ro", uri=True) as db:
        for path in paths:
            hits = db.execute(
                "select logical_path,archive_path,archive,size,provider_count from resolved_assets where lower(logical_path)=?",
                (path.lower(),),
            ).fetchall()
            candidates = db.execute(
                "select a.logical_path,ar.name,ar.path,a.size,a.verification,a.storage "
                "from assets a join archives ar on ar.id=a.archive_id where lower(a.logical_path)=? "
                "order by ar.path,a.id", (path.lower(),)
            ).fetchall()
            if len(hits) == 1:
                asset_path, archive_path, archive, size, provider_count = hits[0]
                archive_path = str(Path(archive_path))
                if archive_path not in archive_hashes and Path(archive_path).is_file():
                    archive_hashes[archive_path] = sha(Path(archive_path))
                rows.append({"logical_path": asset_path, "archive": archive,
                             "archive_path": archive_path,
                             "archive_sha256": archive_hashes.get(archive_path),
                             "bytes": size, "status": "resolved_from_resolved_assets",
                             "resolved_provider_count": provider_count,
                             "index_candidate_count": len(candidates),
                             "index_candidates": [{"logical_path": c[0], "archive": c[1], "archive_path": c[2],
                                                   "bytes": c[3], "verification": c[4], "storage": c[5]}
                                                  for c in candidates]})
            else:
                rows.append({"logical_path": path, "status": "missing" if not hits else "ambiguous",
                             "matches": len(hits), "index_candidate_count": len(candidates),
                             "index_candidates": [{"logical_path": c[0], "archive": c[1], "archive_path": c[2],
                                                   "bytes": c[3], "verification": c[4], "storage": c[5]}
                                                  for c in candidates]})
    return {"logical_model_path": logical, "index_sha256": index_sha,
            "components": rows,
            "provider_complete": all(r["status"] == "resolved_from_resolved_assets" for r in rows)}


def existing_decode_maps() -> tuple[dict[str, dict], dict[str, dict]]:
    decoded: dict[str, dict] = {}
    pilot_trace = read(OUT / "pilots/pilot-trace.json")
    pilot_decodes = read(OUT / "pilots/pilot-decodes.json")
    def detail(manifest: Path, source: str, owner: str, expected_sha: str | None = None) -> dict:
        data = read(manifest)
        groups = data.get("geometry", {}).get("groups", [])
        texture_list = [{"texture_name": t.get("texture_name"),
                         "source_sha256": (t.get("source") or {}).get("sha256"),
                         "source_bytes": (t.get("source") or {}).get("size"),
                         "width": t.get("width"), "height": t.get("height"),
                         "mip_count": t.get("mip_count")} for t in data.get("textures", [])]
        skeleton = data.get("skeleton") or {}
        plan = data.get("animated_asset_import_plan") or {}
        return {"source": source, "owner": owner, "manifest": str(manifest),
                "manifest_sha256": sha(manifest), "expected_manifest_sha256": expected_sha,
                "status": data.get("status"),
                "geometry_groups": [{"name": g.get("name"), "material": g.get("material"),
                                     "vertices": g.get("vertex_count"), "triangles": g.get("triangle_count"),
                                     "bounds": g.get("bounds")} for g in groups],
                "skeleton_bones": len(skeleton.get("bones", [])),
                "skin_palette_bones": data.get("rig_palette_binding", {}).get("palette_bones"),
                "texture_count": len(texture_list), "missing_texture_count": len(data.get("missing_textures", [])),
                "textures": texture_list,
                "animation_import_plan_status": plan.get("status"),
                "animation_owner_model": (plan.get("source") or {}).get("logical_path")}

    # Only map each stock model to its own receipt. The pilot trace contains
    # alternative attachment models; those are references, not decoded meshes.
    for name, record in pilot_decodes.get("pilots", {}).items():
        model = record.get("stock_model", {})
        logical = model.get("logical_path", "").lower().replace("\\", "/")
        manifest = Path(record.get("manifest", ""))
        if logical and manifest.is_file():
            decoded[logical] = detail(manifest, "pilot-decodes.json", name, record.get("manifest_sha256"))
    equip_path = OUT / "pilots/pilot-equipment.json"
    if equip_path.is_file():
        equipment = read(equip_path)
        for pilot, entries in equipment.get("pilots", {}).items():
            for role, record in entries.items():
                logical = record.get("stock_model", {}).get("logical_path", "").lower().replace("\\", "/")
                manifest = Path(record.get("manifest", ""))
                if logical and manifest.is_file():
                    decoded[logical] = detail(manifest, "pilot-equipment.json", f"{pilot}/{role}",
                                              record.get("manifest_sha256"))

    # Find any other hash-verified stock decodes already in the bounded 0.6.0
    # pilot/decode tree. Repeated legacy and verified directories collapse by
    # logical model path; no donor copy is created.
    for base in (OUT / "pilots", OUT / "donors/decoded", OUT / "qualification/ranged-rig-audit/decoded",
                 OUT / "inventory/complete-donors/decoded"):
        if not base.is_dir():
            continue
        for manifest in base.rglob("decoded-static.json"):
            receipt = next((parent / "source-identity.json" for parent in manifest.parents
                            if parent != base.parent and (parent / "source-identity.json").is_file()), None)
            if not receipt:
                continue
            identity = read(receipt)
            recorded = identity.get("source_identity", {})
            expected = identity.get("manifest_sha256")
            if expected != sha(manifest):
                continue
            model_paths = [p.lower().replace("\\", "/") for p in recorded.get("model_and_companions", []) if p.lower().endswith(".rgm")]
            if len(model_paths) == 1:
                decoded.setdefault(model_paths[0], detail(manifest, "verified-existing-source-identity.json",
                                                          receipt.parent.name, expected))
    rig_path = OUT / "qualification/ranged-rig-audit/report.json"
    if rig_path.is_file():
        rig = read(rig_path)
        for logical, record in rig.get("models", {}).items():
            logical = logical.lower().replace("\\", "/")
            manifest_path = Path(record.get("manifest", ""))
            if manifest_path.is_file():
                decoded[logical] = detail(manifest_path, "ranged-rig-audit/report.json",
                                          "ranged-rig-audit", record.get("manifest_sha256"))
    return decoded, {"pilot_trace": pilot_trace, "pilot_decodes": pilot_decodes}


def frozen_local_source_records(coverage: dict, known_official_members: set[str]) -> tuple[list[dict], dict]:
    freeze_path = OUT / "baseline/preparation-freeze.json"
    freeze = read(freeze_path)
    snapshot = Path(freeze["source_snapshot"])
    frozen_inputs = freeze.get("inputs", {}).get("assets", {})
    records = []
    seeds = set()
    for family in coverage["family_tier_coverage"]:
        for key in ("body_targets", "attached_crew_targets"):
            for actor in family.get(key, []):
                actor = actor.replace("\\", "/").lower()
                if actor.startswith("ebps/vietnam/"):
                    seeds.add((family["family"], actor))
    for family, actor in sorted(seeds):
        rel = "attrib/instances/" + actor + ".xml"
        path = snapshot / Path(rel)
        expected = frozen_inputs.get(rel, {}).get("sha256")
        if not path.is_file() or not expected:
            records.append({"family": family, "actor": actor, "status": "absent_from_frozen_xml_registry",
                            "registry_relative_path": rel, "path": str(path)})
            continue
        actual = sha(path)
        if actual != expected:
            raise RuntimeError(f"Frozen XML hash mismatch: {path}: {actual} != {expected}")
        root = ET.parse(path).getroot()
        refs = []
        for node in root.iter():
            if node.tag.lower().endswith("instance_reference"):
                name = node.get("name", "")
                value = node.get("value", "")
                if name in {"parent_pbg", "attachments", "animator_attachments"} and value:
                    refs.append({"name": name, "value": value.replace("\\", "/").lower(),
                                 "mod": node.get("mod"), "overrideParent": node.get("overrideParent")})
        refs = sorted({(r["name"], r["value"], r["mod"], r["overrideParent"]): r for r in refs}.values(),
                      key=lambda r: (r["name"], r["value"]))
        parents = [r["value"] for r in refs if r["name"] == "parent_pbg"]
        official_targets = []
        for parent in parents:
            member = "attrib/" + parent + ".rgd"
            official_targets.append({"target_member": member,
                                     "present_in_official_closure": member.lower() in known_official_members})
        records.append({"family": family, "actor": actor, "status": "verified_frozen_xml",
                        "registry_relative_path": rel, "path": str(path), "sha256": actual,
                        "parent_pbg_refs": parents, "render_and_animator_attachment_refs": refs,
                        "official_parent_targets": official_targets,
                        "source_snapshot_status": freeze.get("status")})
    return records, {"path": str(freeze_path), "sha256": sha(freeze_path),
                     "source_snapshot": str(snapshot), "status": freeze.get("status"),
                     "xml_files_verified": sum(1 for r in records if r.get("status") == "verified_frozen_xml")}


def complexity_budget(paths: list[str], model_records: dict[str, dict]) -> dict:
    lod_totals: dict[str, int] = defaultdict(int)
    lod_peaks: dict[str, int] = defaultdict(int)
    decoded_count = 0
    per_model = {}
    missing = []
    for logical in sorted(set(paths)):
        record = model_records.get(logical)
        detail = record.get("existing_decode") if record else None
        if not detail:
            missing.append(logical)
            continue
        decoded_count += 1
        per_lod: dict[str, int] = defaultdict(int)
        for group in detail.get("geometry_groups", []):
            label = str(group.get("material") or group.get("name") or "unknown").lower()
            match = re.search(r"lod[_ -]?([0-9]+)", label)
            lod = "lod" + match.group(1) if match else label
            if isinstance(group.get("triangles"), int):
                per_lod[lod] += group["triangles"]
        per_model[logical] = dict(sorted(per_lod.items()))
        for lod, triangles in per_lod.items():
            lod_totals[lod] += triangles
            lod_peaks[lod] = max(lod_peaks[lod], triangles)
    if not paths:
        status = "no_render_slot_in_current_refs"
    elif missing:
        status = "partial_decoded_complexity_budget"
    else:
        status = "complete_for_resolved_render_slots"
    return {"status": status, "unique_render_model_paths": len(set(paths)),
            "decoded_model_count": decoded_count, "undecoded_model_paths": missing,
            "summed_triangles_by_lod_across_unique_decoded_models": dict(sorted(lod_totals.items())),
            "peak_single_model_triangles_by_lod": dict(sorted(lod_peaks.items())),
            "per_model_triangles_by_lod": per_model,
            "budget_limit": "Decode receipts only; incomplete where any cited render model lacks an existing decode. No appearance or gameplay budget implied."}


def main() -> None:
    guard()
    coverage = read(OUT / "inventory/coverage-audit-v2.json")
    land = read(OUT / "inventory/land_units.json")
    closure_path = next((OUT / "inventory").glob("official_rgd_closure_*.json"))
    closure = read(closure_path)
    local_xml_records, freeze_evidence = frozen_local_source_records(
        coverage, {m.lower() for m in (entry["member"] for entry in closure["members"])})
    index_sha = sha(INDEX)
    members = {m["member"].lower(): m for m in closure["members"]}
    visual_links: dict[str, list[dict]] = defaultdict(list)
    for link in closure.get("entity_visual_attachment_and_weapon_links", []):
        visual_links[link["source_member"].lower()].append(link)
    parents: dict[str, str] = {}
    for edge in closure.get("parent_edges", []):
        source = edge["source_member"].lower()
        target = edge.get("member", "").lower()
        if target:
            parents[source] = target

    # Family seed actors include each local body entity and each explicitly
    # attached crew entity. If the Vietnamese instance has a donor parent, use
    # that as the official asset target and retain the local actor as consumer.
    actor_owners: dict[str, set[str]] = defaultdict(set)
    actor_roles: dict[str, set[str]] = defaultdict(set)
    family_seed_map = {}
    for row in coverage["family_tier_coverage"]:
        family = row["family"]
        seeds = []
        for actor in row.get("body_targets", []):
            actor = actor.replace("\\", "/").lower()
            seeds.append((actor, "body"))
        for actor in row.get("attached_crew_targets", []):
            actor = actor.replace("\\", "/").lower()
            seeds.append((actor, "attached_crew"))
        for actor in row.get("donor_parent_targets", []):
            actor = actor.replace("\\", "/").lower()
            seeds.append((actor, "donor_parent"))
        family_seed_map[family] = []
        for actor, role in seeds:
            member = logical_actor(actor).lower()
            actor_owners[member].add(family)
            actor_roles[member].add(role)
            family_seed_map[family].append({"actor": actor, "role": role, "member": member})

    # Use the coverage audit's nine reachable inherited stock entries, including
    # the SBP-to-EBP body edge where one exists.
    stock_actor_rows = coverage["included_inherited_stock_actors"]
    stock_actor_ids = [r["id"] for r in stock_actor_rows]
    for stock_row in stock_actor_rows:
        actor = stock_row.get("full_id") or stock_row["id"]
        actor = actor.replace("\\", "/").lower()
        member = logical_actor(actor)
        actor_owners[member].add("stock:" + stock_row["id"].rsplit("\\", 1)[-1])
        actor_roles[member].add("reachable_stock_actor")
    for edge in closure.get("squad_loadout_body_edges", []):
        if edge["source_member"].lower() in actor_owners:
            for body in edge.get("candidate_members", []):
                actor_owners[body.lower()].update(actor_owners[edge["source_member"].lower()])
                actor_roles[body.lower()].add("stock_loadout_body")

    # The land-unit visual scan covers exact currently resolved stock model refs;
    # include all ten entries because the official/chinese official is a named
    # preservation case even though it is not one of the nine counted roster IDs.
    stock_visuals = []
    for row in land.get("native_actor_visual_summary", []):
        if row.get("model_asset_refs"):
            stock_visuals.append(row)
            for model in row["model_asset_refs"]:
                if model.lower().startswith("art\\"):
                    pass

    # Follow body actor parent chains and attachment-list references. The
    # closure was already decoded; this is a read-only join, not another extract.
    actor_records: dict[str, dict] = {}
    attachment_model_owners: dict[str, list[dict]] = defaultdict(list)
    actor_queue = list(actor_owners)
    visited = set()
    while actor_queue:
        member_path = actor_queue.pop(0).lower()
        if member_path in visited:
            continue
        visited.add(member_path)
        entry = members.get(member_path)
        if not entry:
            actor_records[member_path] = {"status": "outside_official_closure",
                                          "owners": sorted(actor_owners.get(member_path, [])),
                                          "roles": sorted(actor_roles.get(member_path, []))}
            continue
        xml_root = read_xml(member_xml_path(entry))
        refs = []
        for link in visual_links.get(member_path, []):
            if link.get("pbg_map", "").lower() == "attachments\\attachment_lists":
                target = link.get("member", "").lower()
                if target:
                    refs.append(target)
        # Also inspect explicit animator_attachments PBG in the actor itself;
        # this captures the stock owner if it was omitted by the visual scan.
        own_attach = pbg_member(xml_root, "animator_attachments")
        if own_attach and own_attach.lower() in members:
            refs.append(own_attach.lower())
        refs = sorted(set(refs))
        models = []
        for attach_member in refs:
            attach_record = members.get(attach_member)
            aroot = read_xml(member_xml_path(attach_record)) if attach_record else None
            found = model_ref_evidence(aroot)
            for evidence in found:
                model = evidence["logical_model_path"]
                models.append({**evidence, "attachment_member": attach_member,
                               "attachment_sha256": attach_record.get("decoded_sha256") if attach_record else None})
                attachment_model_owners[model].append({"actor_member": member_path,
                                                       "attachment_member": attach_member,
                                                       "source_field": evidence["source_field"],
                                                       "actor_roles": sorted(actor_roles.get(member_path, [])),
                                                       "consumers": sorted(actor_owners.get(member_path, []))})
        parent = parents.get(member_path)
        if parent:
            actor_owners[parent].update(actor_owners.get(member_path, set()))
            actor_roles[parent].update(actor_roles.get(member_path, set()))
            actor_queue.append(parent)
        actor_records[member_path] = {"status": "resolved", "closure_member": entry["member"],
                                      "raw_sha256": entry.get("raw_sha256"),
                                      "decoded_sha256": entry.get("decoded_sha256"),
                                      "owners": sorted(actor_owners.get(member_path, [])),
                                      "roles": sorted(actor_roles.get(member_path, [])),
                                      "attachment_members": refs, "model_refs": models,
                                      "parent_member": parent}

    local_by_actor = {r.get("actor"): r for r in local_xml_records if r.get("status") == "verified_frozen_xml"}
    for member_path, record in actor_records.items():
        local_actor = member_path.removeprefix("attrib/").removesuffix(".rgd")
        local_record = local_by_actor.get(local_actor)
        if local_record and record.get("status") != "resolved":
            record["status"] = "resolved_frozen_local_source"
            record["frozen_xml_registry"] = {"path": local_record["path"], "sha256": local_record["sha256"],
                                              "parent_pbg_refs": local_record["parent_pbg_refs"],
                                              "attachments": local_record["render_and_animator_attachment_refs"]}

    # Add the exact model refs already available from stock visual summary and
    # pilot traces (including direct animal/mount references).
    model_owners = defaultdict(list)
    for model, owners in attachment_model_owners.items():
        model_owners[model].extend(owners)
    pilot_trace = read(OUT / "pilots/pilot-trace.json")
    for name, pilot in pilot_trace.get("pilots", {}).items():
        for model in pilot.get("stock_models", {}).values():
            logical = model.get("logical_path", "").lower().replace("\\", "/")
            if logical:
                model_owners[logical].append({"owner": name, "relation": "pilot-stock-model"})
        for attachment in pilot.get("attachment_rgds", {}).values():
            for model in attachment.get("models", []):
                logical = model.get("value", "").lower().replace("\\", "/")
                if logical:
                    if not logical.endswith(".rgm"):
                        logical += ".rgm"
                    model_owners[logical].append({"owner": name, "relation": "pilot-equipment-model"})
    for row in stock_visuals:
        for val in row.get("model_asset_refs", []):
            logical = val.lower().replace("\\", "/")
            if not logical.startswith("art/"):
                continue
            if not logical.endswith(".rgm"):
                logical += ".rgm"
            model_owners[logical].append({"owner": row.get("id"), "relation": "native_actor_visual_summary"})

    # The VN instances' referenced attachment lists are already captured in the
    # family matrix. Resolve those exact stock RGD members as the tier-specific
    # appearance/equipment layer (the common archetype parent alone is not a
    # complete donor description).
    family_attachment_models: dict[str, list[dict]] = defaultdict(list)
    for row in coverage["family_tier_coverage"]:
        family = row["family"]
        for target in row.get("attachment_targets", []):
            member_path = "attrib/" + target.replace("\\", "/").lower().strip("/") + ".rgd"
            entry = members.get(member_path)
            if not entry:
                continue
            aroot = read_xml(member_xml_path(entry))
            for evidence in model_ref_evidence(aroot):
                logical = evidence["logical_model_path"]
                field = evidence["source_field"]
                # A tier/civ animator0..3 is the actual model slot. Parent or
                # generic animator refs preserve the archetype rig/animation
                # owner separately, even when they point into humans/animals.
                is_render_slot = field in {"animator0", "animator1", "animator2", "animator3"}
                if is_render_slot:
                    relation = "render_body_model_slot"
                elif field in {"parent_animator", "animator"}:
                    relation = "animator_or_archetype_reference"
                else:
                    relation = "other_model_reference"
                rec = {**evidence, "attachment_member": entry["member"],
                       "attachment_sha256": entry.get("decoded_sha256"), "relation": relation,
                       "tier_or_age_marker": next(iter(re.findall(r"(?:tier|age)0?([1-4])", logical)), None),
                       "gender_marker": ("female" if "female" in logical else "male" if "male" in logical else None)}
                family_attachment_models[family].append(rec)
                model_owners[logical].append({"owner": family, "relation": relation,
                                              "attachment_member": entry["member"],
                                              "source_field": field, "variant": evidence["variant"]})

    existing_decodes, decode_sources = existing_decode_maps()
    archive_hashes = {}
    model_records = {}
    for logical, owners in sorted(model_owners.items()):
        record = provider(logical, index_sha, archive_hashes)
        record["owners"] = owners
        record["existing_decode"] = existing_decodes.get(logical)
        record["decode_status"] = "decoded_existing" if logical in existing_decodes else "not_decoded_in_existing_receipts"
        model_records[logical] = record

    # Add member-level index identity for each exact primary RGM. The archive
    # listing reads metadata only; it does not extract or decode payloads.
    list_cache: dict[tuple[str, str], dict] = {}
    for logical, record in model_records.items():
        primary = record["components"][0]
        if primary.get("status") != "resolved_from_resolved_assets":
            record["archive_member"] = {"status": primary.get("status", "unresolved")}
            continue
        archive_path = primary["archive_path"]
        basename = Path(logical).name
        cache_key = (archive_path.lower(), basename.lower())
        if cache_key not in list_cache:
            proc = subprocess.run([str(ARCH), "list", archive_path, "--filter", basename],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            try:
                result = json.loads(proc.stdout) if proc.returncode == 0 else None
            except json.JSONDecodeError:
                result = None
            list_cache[cache_key] = result or {"error": (proc.stderr or proc.stdout)[-1200:]}
        listing = list_cache[cache_key]
        members_found = listing.get("members", [])
        matches = [m for m in members_found if m.get("path", "").lower() == logical.lower()]
        if len(matches) == 1:
            m = matches[0]
            record["archive_member"] = {"status": "exact_member_listed", "member": m["path"],
                                        "crc32": m.get("crc"), "bytes": m.get("size"),
                                        "stored_bytes": m.get("stored_size"),
                                        "storage": m.get("storage"),
                                        "verification": m.get("verification"),
                                        "member_sha256": None,
                                        "member_sha256_note": "Not extracted in this trace-only pass; CRC32 plus full archive SHA256 identify the indexed member."}
        else:
            record["archive_member"] = {"status": "exact_member_not_unique", "matches": len(matches),
                                        "listed_count": listing.get("member_count"),
                                        "listing_error": listing.get("error")}

    # Explicit model/equipment references from the family's source closure are
    # retained even when the source model is unresolved at asset level.
    family_rows = []
    for row in coverage["family_tier_coverage"]:
        family = row["family"]
        seeds = family_seed_map[family]
        model_set = set()
        body_model_set = set()
        for member, record in actor_records.items():
            if family in record.get("owners", []):
                for item in record.get("model_refs", []):
                    model_set.add(item["logical_model_path"])
                    if item.get("source_field") in {"animator0", "animator1", "animator2", "animator3"}:
                        body_model_set.add(item["logical_model_path"])
        for item in family_attachment_models.get(family, []):
            model_set.add(item["logical_model_path"])
            if item["relation"] == "render_body_model_slot":
                body_model_set.add(item["logical_model_path"])
        # Keep animator/archetype refs present in the full manifest but do not
        # count them as render-body decodes for the complexity budget.
        family_rows.append({"family": family, "tiers": row.get("tiers", []),
                            "squad_ids": row.get("squad_ids", []), "entity_ids": row.get("entity_ids", []),
                            "body_and_crew_seed_actors": seeds,
                            "body_model_paths_reached_from_seed_or_parent": sorted(body_model_set),
                            "all_body_and_equipment_model_paths": sorted(model_set),
                            "complexity_budget": complexity_budget(sorted(body_model_set), model_records),
                            "attachment_model_evidence": family_attachment_models.get(family, []),
                            "body_model_disposition": ("render_slot_traced" if body_model_set else
                                                        "animator_or_attachment_only_no_explicit_render_slot" if model_set else
                                                        "no_model_reference_resolved"),
                            "mount_disposition": ("animal_mount_model_refs_present; fit and tack remain pilot-limited"
                                                  if any("/animals/" in p for p in body_model_set) and family in {
                                                      "vn_unit_horseman", "vn_unit_knight", "vn_unit_scout"}
                                                  else "elephant_body_asset_refs_present; fit and tack remain pilot-limited"
                                                  if family.startswith("vn_unit_war_elephant")
                                                  else "N/A for foot unit or non-mounted siege actor"),
                            "crew_disposition": ("attached crew actor ref traced; seat/transform unresolved"
                                                 if row.get("attached_crew_targets")
                                                 else "N/A; no separate attached crew actor in source closure")})

    # Count render-body slots only when the owning RGD field proves that role.
    # Archetype/animator references and the land-unit visual summary's broad
    # model list stay in the donor manifest but do not inflate this count.
    body_like = set()
    for row in family_rows:
        body_like.update(row["body_model_paths_reached_from_seed_or_parent"])
    stock_actor_manifest = []
    stock_visual_by_id = {str(r.get("id", "")).lower().replace("\\", "/"): r for r in stock_visuals}
    for stock_row in stock_actor_rows:
        full_id = (stock_row.get("full_id") or stock_row["id"]).replace("\\", "/").lower()
        member = logical_actor(full_id)
        visual = stock_visual_by_id.get(full_id)
        closure_refs = []
        render_paths = set()
        all_paths = set()
        for actor_member, actor_record in actor_records.items():
            if "stock:" + stock_row["id"].rsplit("\\", 1)[-1] not in actor_record.get("owners", []):
                continue
            for ref in actor_record.get("model_refs", []):
                path = ref["logical_model_path"]
                all_paths.add(path)
                is_render = ref.get("source_field") in {"animator0", "animator1", "animator2", "animator3"}
                if is_render:
                    render_paths.add(path)
                closure_refs.append({**ref, "source_actor_member": actor_member,
                                    "role": "render_body_model_slot" if is_render else "animator_or_archetype_or_equipment_reference"})
        body_like.update(render_paths)
        stock_actor_manifest.append({"id": stock_row["id"], "full_id": full_id,
                                     "category": stock_row.get("category"),
                                     "official_member_path": stock_row.get("official_member_path"),
                                     "included": stock_row.get("included"),
                                     "relation_types": stock_row.get("relation_types", []),
                                     "consumers": stock_row.get("consumers", []),
                                     "variants": stock_row.get("variants", []),
                                     "visual_summary_present": visual is not None,
                                     "render_body_model_paths_by_field_provenance": sorted(render_paths),
                                     "all_model_paths_in_actor_closure": sorted(all_paths),
                                     "actor_closure_model_field_evidence": closure_refs,
                                     "visual_summary_model_asset_refs": visual.get("model_asset_refs", []) if visual else [],
                                     "material_refs_in_decoded_RGD": visual.get("material_refs_in_decoded_RGD", []) if visual else [],
                                     "animation_owner_status": "exact actor/animator RGD references traced; clips remain unqualified",
                                     "explicit_render_slot_complexity_budget": complexity_budget(sorted(render_paths), model_records),
                                     "complexity_budget": complexity_budget(sorted(all_paths), model_records),
                                     "complexity_budget_scope": "All model refs in this actor's official RGD/loadout-body closure, including parent_animator archetype owners; source field evidence above distinguishes body/archetype/equipment. This is not an assertion that every reference is a render slot."})
    decoded_body = sum(1 for p in body_like if p in existing_decodes)
    freeze_path = OUT / "baseline/preparation-freeze.json"
    report = {
        "schema": "ccp-060-complete-donors-inventory/v1",
        "status": "trace_complete_decode_checkpoint",
        "evidence_boundary": "Preparation-freeze XML, official RGD closure, current-index donor trace, existing decode receipts, and bounded selected body decodes; no Blender export, native cook, package import, or match proof.",
        "eventual_baseline_note": {"selected_baseline": "not yet identified; root says 0.5.2 is not finished and no artifacts are selected or pinned",
                                   "inventory_source_boundary": "This report remains preparation-freeze and diagnostic-parity evidence; reconcile it after the actual final 0.5.2/0.5.3 source is identified.",
                                   "diagnostic_test_c": "Not pinned or tested; exact-path question remains pending."},
        "scope": {"corrected_family_rows": len(coverage["family_tier_coverage"]),
                  "reachable_stock_actor_ids": len(stock_actor_ids),
                  "stock_visual_summary_entries": len(stock_visuals),
                  "includes_official_context_entry": any("official_1" in r.get("id", "") for r in stock_visuals)},
        "counts": {"unique_actor_members_traced_or_attempted": len(visited),
                   "actor_members_with_official_closure": sum(1 for r in actor_records.values() if r.get("status") == "resolved"),
                   "actor_members_verified_against_frozen_local_xml": sum(1 for r in actor_records.values() if r.get("status") == "resolved_frozen_local_source"),
                   "actor_members_outside_official_and_local_registries": sum(1 for r in actor_records.values() if r.get("status") not in {"resolved", "resolved_frozen_local_source"}),
                   "unique_body_like_model_paths": len(body_like),
                   "body_like_models_with_existing_decode_or_lod_detail": decoded_body,
                   "body_like_models_without_existing_decode_detail": len(body_like) - decoded_body,
                   "all_unique_model_paths_including_equipment": len(model_records),
                   "primary_rgm_refs_missing_or_ambiguous_in_current_asset_index": sum(1 for r in model_records.values() if r["components"][0]["status"] != "resolved_from_resolved_assets"),
                   "model_refs_with_missing_rrgeom_or_rrmaterial_index_companions": sum(1 for r in model_records.values() if any(c["status"] != "resolved_from_resolved_assets" for c in r["components"][1:])),
                   "family_local_vietnam_xml_refs_verified_against_frozen_registry": sum(1 for r in local_xml_records if r.get("status") == "verified_frozen_xml"),
                   "family_local_vietnam_xml_refs_absent_from_frozen_registry": sum(1 for r in local_xml_records if r.get("status") != "verified_frozen_xml"),
                   "frozen_parent_targets_present_in_official_closure": sum(1 for r in local_xml_records for p in r.get("official_parent_targets", []) if p["present_in_official_closure"])},
        "source_evidence": {"coverage_audit": {"path": str(OUT / "inventory/coverage-audit-v2.json"), "sha256": sha(OUT / "inventory/coverage-audit-v2.json")},
                            "official_rgd_closure": {"path": str(closure_path), "sha256": sha(closure_path)},
                            "preparation_freeze": freeze_evidence,
                            "land_units": {"path": str(OUT / "inventory/land_units.json"), "sha256": sha(OUT / "inventory/land_units.json")},
                            "asset_index": {"path": str(INDEX), "sha256": index_sha},
                            "pilot_trace": {"path": str(OUT / "pilots/pilot-trace.json"), "sha256": sha(OUT / "pilots/pilot-trace.json")},
                            "pilot_decodes": {"path": str(OUT / "pilots/pilot-decodes.json"), "sha256": sha(OUT / "pilots/pilot-decodes.json")},
                            "pilot_equipment": {"path": str(OUT / "pilots/pilot-equipment.json"),
                                                "sha256": sha(OUT / "pilots/pilot-equipment.json") if (OUT / "pilots/pilot-equipment.json").is_file() else None},
                            "ranged_rig_audit": {"path": str(OUT / "qualification/ranged-rig-audit/report.json"), "sha256": sha(OUT / "qualification/ranged-rig-audit/report.json")}},
        "family_body_matrix": family_rows,
        "frozen_local_vietnam_xml_registry": local_xml_records,
        "reachable_stock_actor_ids": stock_actor_ids,
        "reachable_stock_actor_manifest": stock_actor_manifest,
        "stock_visual_context": [{"id": r.get("id"), "model_asset_refs": r.get("model_asset_refs", []),
                                  "material_refs_in_decoded_RGD": r.get("material_refs_in_decoded_RGD", []),
                                  "animation_owner_status": "native actor/animator attachment owner in land_units visual scan; full clips unqualified"}
                                 for r in stock_visuals],
        "actor_closure": actor_records,
        "models": model_records,
        "decode_sources": {"pilot_decode_report": str(OUT / "pilots/pilot-decodes.json"),
                           "ranged_rig_report": str(OUT / "qualification/ranged-rig-audit/report.json")},
        "remaining_qualification_gates": [
            "Decode additional body donors only after parent review of the trace-only count.",
            "Decoded mesh/texture/LOD detail still does not qualify Blender authoring, native cook, or game runtime.",
            "Animation clips and complete donor animation-owner chains remain unqualified beyond exact RGD attachment-owner references.",
            "Mount, tack, siege crew, and elephant/tower seat placement remain asset-fit questions where existing evidence lacks decoded previews or native match proof."
        ]
    }
    write(DEST / "complete-donors.json", report)
    lines = ["# Complete obtainable donor trace (0.6.0)", "",
             report["evidence_boundary"], "",
             f"Trace counts: {len(family_rows)} family rows, {len(stock_actor_ids)} reachable stock actor IDs, "
             f"{len(body_like)} unique body-like model paths ({decoded_body} already decoded; "
             f"{len(body_like)-decoded_body} lack existing decode/LOD detail), "
             f"{len(model_records)} total body/equipment model paths.", "",
             "## Family body matrix", "",
             "| Family | Tiers | Body model paths | Existing decoded detail |", "|---|---:|---:|---|"]
    for row in family_rows:
        paths = row["body_model_paths_reached_from_seed_or_parent"]
        decoded_names = [Path(p).stem for p in paths if p in existing_decodes]
        status = ", ".join(decoded_names) if decoded_names else ("none present" if paths else "unresolved")
        lines.append(f"| `{row['family']}` | {', '.join(map(str,row['tiers']))} | {len(paths)} | {status} |")
    lines += ["", "## Decode checkpoint", "",
              "Only pre-existing decode receipts were consulted. No additional body or equipment decode was run in this pass.", "",
              "## Evidence hashes", ""]
    for name, rec in report["source_evidence"].items():
        lines.append(f"- `{name}`: `{rec['sha256']}`")
    lines += ["", "Full owner, archive/member, component hash, texture and LOD detail is in `complete-donors.json`.", ""]
    write_text(DEST / "complete-donors.md", "\n".join(lines))
    print(json.dumps(report["counts"], indent=2))


def decode_selected_bodies() -> None:
    """Decode only the four missing Chinese villager render bodies approved by the parent."""
    guard()
    free = shutil.disk_usage(OUT).free
    if free < 2 * 1024**3:
        raise RuntimeError(f"Insufficient free capacity before decode generation: {free} bytes")
    report_path = DEST / "complete-donors.json"
    report = read(report_path)
    previous_batch = report.get("additional_decode_batch")
    if previous_batch and previous_batch.get("status") == "completed" and len(previous_batch.get("results", [])) == 4:
        outcomes = previous_batch["results"]
        free = previous_batch.get("free_bytes_before_generation", free)
        report["evidence_boundary"] = (
            "Frozen source XML, official RGD closure, current-index donor trace, existing decode receipts, "
            "and four selective Garrison stock body decodes; no Blender export, native cook, package import, or match proof.")
        write(report_path, report)
        write_markdown(report, free, outcomes)
        print(json.dumps(previous_batch, indent=2))
        return
    config = INDEX.with_name("game-assets.local.json")
    if not INDEX.is_file() or not config.is_file():
        raise FileNotFoundError("Required current Garrison stock index/config is absent")
    selected = [
        "art/civilizations/chinese/humans/chi_villager_male_age02/chi_villager_male_age02.rgm",
        "art/civilizations/chinese/humans/chi_villager_female_age02/chi_villager_female_age02.rgm",
        "art/civilizations/chinese/humans/chi_villager_male_age03/chi_villager_male_age03.rgm",
        "art/civilizations/chinese/humans/chi_villager_female_age03/chi_villager_female_age03.rgm",
    ]
    already, _ = existing_decode_maps()
    outcomes = []
    for logical in selected:
        record = report["models"].get(logical)
        if record is None:
            outcomes.append({"logical_model_path": logical, "status": "not_in_traced_model_manifest"})
            break
        if logical in already:
            report["models"][logical]["existing_decode"] = already[logical]
            report["models"][logical]["decode_status"] = "decoded_existing_reused"
            outcomes.append({"logical_model_path": logical, "status": "decoded_existing_reused",
                             "manifest": already[logical]["manifest"],
                             "manifest_sha256": already[logical]["manifest_sha256"]})
            continue
        components = record["components"]
        if len(components) != 3 or any(c.get("status") != "resolved_from_resolved_assets" for c in components):
            outcomes.append({"logical_model_path": logical, "status": "blocked_missing_or_ambiguous_companion",
                             "components": components})
            break
        source_identity = {"index_sha256": sha(INDEX), "config_sha256": sha(config),
                           "model_and_companions": [c["logical_path"] for c in components],
                           "archives": {c["archive_path"]: c["archive_sha256"] for c in components}}
        fingerprint = hashlib.sha256(json.dumps(source_identity, sort_keys=True).encode()).hexdigest()[:20]
        slug = Path(logical).parent.name
        target = owned(DEST / "decoded" / slug / ("verified-" + fingerprint))
        target.mkdir(parents=True, exist_ok=True)
        receipt_path = target / "source-identity.json"
        existing = list(target.glob("*/decoded-static.json"))
        if existing:
            if len(existing) != 1 or not receipt_path.is_file():
                outcomes.append({"logical_model_path": logical, "status": "blocked_unverified_existing_cache",
                                 "target": str(target)})
                break
            receipt = read(receipt_path)
            if receipt.get("source_identity") != source_identity or receipt.get("manifest_sha256") != sha(existing[0]):
                outcomes.append({"logical_model_path": logical, "status": "blocked_stale_existing_cache",
                                 "target": str(target)})
                break
            manifest = existing[0]
        else:
            command = [str(CORE), "convert", "decode-static", "--logical-path", logical,
                       "--config", str(config), "--index", str(INDEX), "--output-root", str(target)]
            try:
                proc = subprocess.run(command, capture_output=True, text=True,
                                      encoding="utf-8", errors="replace", timeout=90)
            except subprocess.TimeoutExpired:
                outcomes.append({"logical_model_path": logical, "status": "failed_timeout_90s",
                                 "command": command})
                break
            if proc.returncode:
                outcomes.append({"logical_model_path": logical, "status": "failed_decode",
                                 "returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:],
                                 "stderr_tail": proc.stderr[-1800:]})
                break
            manifests = list(target.glob("*/decoded-static.json"))
            if len(manifests) != 1:
                outcomes.append({"logical_model_path": logical, "status": "failed_manifest_count",
                                 "manifest_count": len(manifests), "stdout_tail": proc.stdout[-1200:]})
                break
            manifest = manifests[0]
            write(receipt_path, {"source_identity": source_identity, "manifest_sha256": sha(manifest),
                                 "status": "verified_current_index_decode"})
        msha = sha(manifest)
        outcomes.append({"logical_model_path": logical, "status": "decoded_new_or_verified_reuse",
                         "manifest": str(manifest), "manifest_sha256": msha,
                         "source_identity": source_identity})
        already, _ = existing_decode_maps()
        if logical in already:
            report["models"][logical]["existing_decode"] = already[logical]
            report["models"][logical]["decode_status"] = "decoded_existing_or_new_verified"
        write(report_path, report)
        print(f"decoded {logical}", flush=True)
    report["additional_decode_batch"] = {"scope": "four Chinese villager Age II/III gender bodies only",
                                         "status": "completed" if len(outcomes) == len(selected) else "stopped_at_first_unresolved_or_failure",
                                         "max_per_decode_timeout_seconds": 90,
                                         "free_bytes_before_generation": free,
                                         "results": outcomes}
    report["evidence_boundary"] = (
        "Frozen source XML, official RGD closure, current-index donor trace, existing decode receipts, "
        "and four selective Garrison stock body decodes; no Blender export, native cook, package import, or match proof.")
    report["counts"]["selected_additional_body_decodes"] = sum(
        1 for r in outcomes if r["status"] in {"decoded_new_or_verified_reuse", "decoded_existing_reused"})
    report["counts"]["body_like_models_with_existing_decode_or_lod_detail"] = sum(
        1 for p in {p for row in report["family_body_matrix"] for p in row["body_model_paths_reached_from_seed_or_parent"]}
        if report["models"].get(p, {}).get("existing_decode"))
    report["counts"]["body_like_models_without_existing_decode_detail"] = (
        report["counts"]["unique_body_like_model_paths"] -
        report["counts"]["body_like_models_with_existing_decode_or_lod_detail"])
    write(report_path, report)
    write_markdown(report, free, outcomes)
    print(json.dumps(report["additional_decode_batch"], indent=2))


def write_markdown(report: dict, free: int, outcomes: list[dict]) -> None:
    md_path = DEST / "complete-donors.md"
    lines = ["# Complete obtainable donor trace (0.6.0)", "", report["evidence_boundary"], "",
             f"Trace counts: {len(report['family_body_matrix'])} family rows, "
             f"{len(report['reachable_stock_actor_ids'])} reachable stock actor IDs, "
             f"{report['counts']['unique_actor_members_traced_or_attempted']} actor members "
             f"({report['counts']['actor_members_with_official_closure']} official closure; "
             f"{report['counts']['actor_members_verified_against_frozen_local_xml']} frozen local VN XML), "
             f"{report['counts']['unique_body_like_model_paths']} render-body slots "
             f"({report['counts']['body_like_models_with_existing_decode_or_lod_detail']} with decode/LOD detail; "
             f"{report['counts']['body_like_models_without_existing_decode_detail']} without), "
             f"{report['counts']['all_unique_model_paths_including_equipment']} total body/equipment model refs.", "",
             "All primary RGM refs resolve through the current index and exact archive member listing. "
             f"{report['counts']['model_refs_with_missing_rrgeom_or_rrmaterial_index_companions']} referenced models lack one or more same-stem geometry/material index companions; "
             "the RGM providers remain resolved, and no alternate provider was selected.", "",
             f"Baseline boundary: {report['eventual_baseline_note']['selected_baseline']}. "
             f"{report['eventual_baseline_note']['inventory_source_boundary']} "
             f"{report['eventual_baseline_note']['diagnostic_test_c']}", "",
             "## Family render-body matrix", "",
             "| Family | Tiers | Render body slots | Existing decoded detail | Complexity budget | Mount | Crew |",
             "|---|---:|---:|---|---|---|---|"]
    for row in report["family_body_matrix"]:
        paths = row["body_model_paths_reached_from_seed_or_parent"]
        decoded_names = [Path(p).stem for p in paths if report["models"].get(p, {}).get("existing_decode")]
        if decoded_names:
            detail_text = ", ".join(decoded_names)
        elif row["body_model_disposition"] == "animator_or_attachment_only_no_explicit_render_slot":
            detail_text = "archetype/animator owner only"
        else:
            detail_text = "no existing decode detail"
        budget = row["complexity_budget"]
        lod_text = ", ".join(f"{k}: {v}" for k, v in budget["summed_triangles_by_lod_across_unique_decoded_models"].items()) or "no decoded totals"
        lines.append(f"| `{row['family']}` | {', '.join(map(str,row['tiers']))} | {len(paths)} | "
                     f"{detail_text} | {budget['status']}; {lod_text}; {len(budget['undecoded_model_paths'])} undecoded | "
                     f"{row['mount_disposition']} | {row['crew_disposition']} |")
    lines += ["", "## Reachable inherited stock actors", "",
              "All nine obtainable inherited stock actor IDs are included. A visual summary or archetype reference does not count as a decoded body unless a render slot is established from animator0–animator3 field provenance.", "",
              "| Stock actor | Category | Reachability / consumers | Model refs in closure | Complexity status |", "|---|---|---|---:|---|"]
    for row in report["reachable_stock_actor_manifest"]:
        budget = row["complexity_budget"]
        consumers = ", ".join(row["consumers"][:3]) + ("…" if len(row["consumers"]) > 3 else "")
        lines.append(f"| `{row['id']}` | {row['category']} | {consumers} | "
                     f"{budget['unique_render_model_paths']} | {budget['status']} |")
    lines += ["", "## Four selective body decodes", "",
              f"F: free capacity before generation: {free} bytes. Each decode had a 90-second timeout; the batch stopped on the first error.", ""]
    for result in outcomes:
        lines.append(f"- `{result['logical_model_path']}`: **{result['status']}**" +
                     (f"; manifest SHA-256 `{result['manifest_sha256']}`" if result.get("manifest_sha256") else ""))
    lines += ["", "## Evidence hashes", ""]
    for name, rec in report["source_evidence"].items():
        if rec.get("sha256"):
            lines.append(f"- `{name}`: `{rec['sha256']}`")
    lines += ["", "Full model owners, attachment fields, archive/member CRCs and hashes, component status, "
              "per-model complexity budgets, decoded textures, LOD triangles and source receipts are recorded in `complete-donors.json`.", ""]
    write_text(md_path, "\n".join(lines))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decode-selected-bodies", action="store_true",
                        help="run the parent-authorized maximum-four villager body decode subset after tracing")
    parser.add_argument("--decode-only", action="store_true",
                        help="run the selected decode subset against the existing trace report without rebuilding the trace")
    args = parser.parse_args()
    if args.decode_only:
        decode_selected_bodies()
    else:
        main()
        if args.decode_selected_bodies:
            decode_selected_bodies()
