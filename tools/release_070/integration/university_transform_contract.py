"""Verify exact University stock-body to private pot-visual model coordinates."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from workspace_support import check_storage, configuration

check_storage(ROOT, configuration(ROOT))
BASE = ROOT / "output/release_070/integration"
CONTRACT = BASE / "native-contract/contract.json"
MEASURE = BASE / "native-measure/university.json"
OUT = BASE / "university-transform"


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def blender_to_engine(b):
    # Exact projection used by the installed Garrison static decoder.
    return (-b[0], b[2], -b[1])


def engine_to_blender(e):
    return (-e[0], -e[2], e[1])


def q_conjugate(q):
    return (-q[0], -q[1], -q[2], q[3])


def q_rotate(q, p):
    # Non-unit input is normalized before applying the ordinary quaternion rotation.
    x, y, z, w = q
    norm = math.sqrt(x*x + y*y + z*z + w*w)
    x, y, z, w = (v/norm for v in (x, y, z, w))
    ux, uy, uz = x, y, z
    dot = ux*p[0] + uy*p[1] + uz*p[2]
    cross = (uy*p[2]-uz*p[1], uz*p[0]-ux*p[2], ux*p[1]-uy*p[0])
    uu = ux*ux + uy*uy + uz*uz
    return tuple(2*dot*u + (w*w-uu)*v + 2*w*c
                 for u, v, c in zip((ux,uy,uz), p, cross))


def world_from_model(b, transform):
    q = transform[:4]
    t = transform[4:7]
    scale = transform[7:10]
    e = blender_to_engine(b)
    scaled = tuple(e[i]*scale[i] for i in range(3))
    return add(q_rotate(q, scaled), t)


def pot_local_from_stock_local(stock_b, main, pot):
    world = world_from_model(stock_b, main)
    relative = sub(world, pot[4:7])
    local_e = q_rotate(q_conjugate(pot[:4]), relative)
    scale = pot[7:10]
    return engine_to_blender(tuple(local_e[i]/scale[i] for i in range(3)))


def bounds(points):
    return {"min": [min(p[i] for p in points) for i in range(3)],
            "max": [max(p[i] for p in points) for i in range(3)]}


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    actor = next(x for x in contract["actors"] if x["family"] == "university")
    stamps = [s for r in actor["references"] for s in r["stamps"]
              if s["member"] == "art/stamps/civ_chinese/chi_university.bin"]
    assert stamps and all(s["visuals"] == stamps[0]["visuals"] for s in stamps)
    visuals = stamps[0]["visuals"]
    main_visual = next(v for v in visuals if v["id"] == "1024830896721280423")
    pot_visual = next(v for v in visuals if v["id"] == "16329432728099511667")
    assert main_visual["model"].endswith("chi_university_control_age04")
    assert pot_visual["model"].endswith("small_water_pot")
    main_t, pot_t = main_visual["transform"], pot_visual["transform"]
    assert main_t[:4] == pot_t[:4] and main_t[7:] == pot_t[7:] == [1.0]*3
    measure = json.loads(MEASURE.read_text())
    minimum = measure["model_local_bounds_min"]
    maximum = measure["model_local_bounds_max"]
    corners = list(itertools.product(*zip(minimum, maximum)))
    # Include asymmetric interior probes so sign and axis swaps cannot pass by bounds alone.
    probes = [*corners, (-1.25, 2.75, 3.125), (4.2, -3.1, 7.7), (0,0,0)]
    shifted = [pot_local_from_stock_local(p, main_t, pot_t) for p in probes]
    main_world = [world_from_model(p, main_t) for p in probes]
    pot_world = [world_from_model(p, pot_t) for p in shifted]
    errors = [math.dist(a, b) for a, b in zip(main_world, pot_world)]
    offset = pot_local_from_stock_local((0,0,0), main_t, pot_t)
    linear_error = max(math.dist(sub(p, o), offset) for p, o in zip(shifted, probes))
    assert max(errors) < 1e-5 and linear_error < 1e-5
    result = {"schema": "ccp-070-university-pot-visual-transform/v1",
              "source_contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
              "source_measure_sha256": hashlib.sha256(MEASURE.read_bytes()).hexdigest(),
              "coordinate_projection": "blender=(-engine.x,-engine.z,engine.y)",
              "main_visual_id": main_visual["id"], "main_model": main_visual["model"],
              "main_transform": main_t, "pot_visual_id": pot_visual["id"],
              "pot_model": pot_visual["model"], "pot_transform": pot_t,
              "mapping": "addon_model_local_B = stock_main_model_local_B + offset_B",
              "offset_B": offset, "stock_healthy_bounds_B": bounds(corners),
              "addon_local_bounds_B": bounds(shifted[:8]),
              "main_world_bounds_engine": bounds(main_world[:8]),
              "addon_world_bounds_engine": bounds(pot_world[:8]),
              "probe_count": len(probes), "max_world_coordinate_error": max(errors),
              "max_local_translation_error": linear_error,
              "stamp_transform_baked_into_mesh": False,
              "native_lifecycle": "requires separate addon RGM/RGO selector qualification and match test"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "contract.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"offset_B": offset, "max_error": max(errors),
                      "receipt": str(OUT / "contract.json")}))


if __name__ == "__main__":
    main()
