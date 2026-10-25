"""Copy/hash-verify task-owned decoded donors onto guarded F: storage.

This is a one-time owned migration. It writes a receipt before deleting the eight
E: donor copies, and never traverses a junction or modifies 0.1.0 inputs.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = json.loads((ROOT / "workspace.json").read_text())
EXT = Path(WORKSPACE["external_root"])
TARGET = EXT / "stock-cache/buildings_020/barracks_tc"
REPORT = ROOT / "output/release_020/barracks_tc/donor-storage-move.json"


def within(path, parent):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    return os.path.commonpath((str(path), str(parent))) == str(parent)


def inventory(folder):
    result = {}
    for parent, dirs, files in os.walk(folder, followlinks=False):
        assert not os.path.islink(parent) and not os.path.isjunction(parent)
        for name in dirs + files:
            assert not os.path.islink(Path(parent) / name) and not os.path.isjunction(Path(parent) / name)
        for name in files:
            path = Path(parent) / name
            rel = path.relative_to(folder).as_posix()
            result[rel] = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


assert EXT.is_dir() and within(TARGET.parent, EXT) if TARGET.parent.exists() else EXT.is_dir()
assert (ROOT / "art/stock_cache").resolve() == (EXT / "stock-cache").resolve()
assert within(ROOT / "art/authoring/buildings_020", ROOT)
TARGET.mkdir(parents=True, exist_ok=True)
assert within(TARGET, EXT)
records = []
for family in ("barracks", "town_center"):
    for age in range(1, 5):
        source = ROOT / f"art/authoring/buildings_020/{family}/donors/age{age:02}"
        dest = TARGET / family / f"age{age:02}"
        assert source.is_dir() and within(source, ROOT / "art/authoring/buildings_020")
        assert not dest.exists(), dest
        prior = inventory(source)
        assert len(prior) > 1
        dest.parent.mkdir(parents=True, exist_ok=True)
        assert within(dest.parent, EXT)
        shutil.copytree(source, dest)
        assert inventory(dest) == prior
        old_manifest = next(source.rglob("decoded-static.json"))
        new_manifest = dest / old_manifest.relative_to(source)
        doc = json.loads(new_manifest.read_text())
        old_base, new_base = str(old_manifest.parent), str(new_manifest.parent)
        raw = new_manifest.read_text()
        assert old_base.replace("\\", "\\\\") in raw
        raw = raw.replace(old_base.replace("\\", "\\\\"), new_base.replace("\\", "\\\\"))
        new_manifest.write_text(raw, encoding="utf8")
        doc = json.loads(new_manifest.read_text())
        assert Path(doc["cache_root"]).resolve() == new_manifest.parent.resolve()
        for resource in doc["resources"].values():
            if isinstance(resource, dict) and resource.get("cache_path"):
                p = Path(resource["cache_path"])
                assert within(p, dest) and p.exists()
                assert hashlib.sha256(p.read_bytes()).hexdigest() == resource["sha256"]
        rec = {"family": family, "age": age, "source": str(source), "destination": str(dest),
               "files": len(prior), "bytes": sum(v["bytes"] for v in prior.values()),
               "copy_verified_sha256": hashlib.sha256(json.dumps(prior, sort_keys=True).encode()).hexdigest(),
               "old_manifest_sha256": prior[old_manifest.relative_to(source).as_posix()]["sha256"],
               "new_manifest_sha256": hashlib.sha256(new_manifest.read_bytes()).hexdigest(),
               "native_resources_identical": True, "source_deleted": False}
        records.append(rec)
        REPORT.write_text(json.dumps({"schema": "ccp.barracks-tc-donor-storage/v1", "status": "copied_verified_pending_delete", "records": records}, indent=2), encoding="utf8")
        # All resolved paths and every copied file were verified above.
        shutil.rmtree(source)
        assert not source.exists()
        rec["source_deleted"] = True
        REPORT.write_text(json.dumps({"schema": "ccp.barracks-tc-donor-storage/v1", "status": "in_progress", "records": records}, indent=2), encoding="utf8")
        print("DONOR_RELOCATED", family, age, rec["files"], rec["bytes"], flush=True)
REPORT.write_text(json.dumps({"schema": "ccp.barracks-tc-donor-storage/v1", "status": "passed", "records": records,
                              "total_files": sum(r["files"] for r in records),
                              "total_bytes": sum(r["bytes"] for r in records),
                              "reclaimed_e_bytes": sum(r["bytes"] for r in records),
                              "note": "Required immutable native donor inputs moved to owned F: stock-cache, not deleted globally."}, indent=2), encoding="utf8")
print("DONOR_STORAGE_PASS", len(records), sum(r["bytes"] for r in records), flush=True)
