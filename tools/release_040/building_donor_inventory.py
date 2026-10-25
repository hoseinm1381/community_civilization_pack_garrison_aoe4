"""Pin the exact decoded Chinese building models before 0.4.0 art authoring."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECODE = ROOT / "output/release_040/buildings/donor-decode"
DEST = ROOT / "art/recipes/release_040/buildings-donors.json"
FAMILIES = ("blacksmith", "stable", "archery_range", "market")
AGES = (2, 3, 4)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(groups):
    points = (point for group in groups for point in group["positions"])
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    count = 0
    for point in points:
        count += 1
        for axis in range(3):
            lo[axis] = min(lo[axis], point[axis])
            hi[axis] = max(hi[axis], point[axis])
    return {"minimum": lo, "maximum": hi, "dimensions": [hi[i] - lo[i] for i in range(3)], "vertices": count}


def run():
    files = list(DECODE.glob("*/decoded-static.json"))
    decoded = [(path, json.loads(path.read_text(encoding="utf8"))) for path in files]
    rows = []
    for family in FAMILIES:
        for age in AGES:
            stem = f"art/civilizations/chinese/structures/{family}/chi_{family}_control_age0{age}/chi_{family}_control_age0{age}.rgm"
            matched = []
            for path, data in decoded:
                if data["request"]["logical_path"].replace("\\", "/").lower() == stem:
                    matched.append((path, data))
            assert len(matched) == 1, (stem, len(matched))
            path, data = matched[0]
            geometry = Path(data["geometry"]["source"]["path"])
            assert sha(geometry) == data["geometry"]["source"]["sha256"]
            groups = data["geometry"]["groups"]
            rows.append({
                "family": family, "age": age, "logical_path": stem,
                "manifest": str(path), "manifest_sha256": sha(path),
                "geometry": str(geometry), "geometry_sha256": sha(geometry),
                "resources": {key: {field: value.get(field) for field in ("logical_path", "archive", "archive_path", "sha256", "cache_path")}
                              for key, value in data["resources"].items() if key in ("model", "geometry", "material")},
                "group_count": len(groups), "triangle_count_all_fragments": sum(g["triangle_count"] for g in groups),
                "bounds_all_fragments": box(groups),
                "groups": [{"name": g["name"], "material": g["preview_material"], "vertices": len(g["positions"]),
                            "triangles": g["triangle_count"], "bounds": box([g])} for g in groups],
                "has_collection_contract": data.get("structure_collection_contract") is not None,
            })
    report = {"schema": "ccp.release040.building-donors/v1", "status": "decoded_source_inventory",
              "models": rows, "proof": "Official Garrison decoded static source and hashes; all-fragment counts are not simultaneous drawn triangle counts"}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(report, indent=2), encoding="utf8")
    print("BUILDING_DONORS_PINNED", len(rows), DEST)
    for row in rows:
        print(row["family"], row["age"], row["group_count"], row["bounds_all_fragments"]["vertices"], row["bounds_all_fragments"]["dimensions"])


if __name__ == "__main__":
    run()
