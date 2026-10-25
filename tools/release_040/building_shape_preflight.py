"""Check 0.4.0 building deformation numerically without starting Blender."""
import ast
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/release_040/buildings"
source = (ROOT / "tools/release_040/building_art.py").read_text()
tree = ast.parse(source)
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"smooth", "shape"}]
space = {"np": np}
exec(compile(ast.Module(body=functions, type_ignores=[]), "building_art.shape", "exec"), space)
shape = space["shape"]


def run():
    donors = json.loads((ROOT / "art/recipes/release_040/buildings-donors.json").read_text())["models"]
    rows = []
    for donor in donors:
        data = json.loads(Path(donor["manifest"]).read_text())
        groups = data["geometry"]["groups"]
        points = np.concatenate([np.asarray(g["positions"], dtype=np.float64) for g in groups])
        nextpos = shape(points, donor["family"], donor["age"])
        assert np.isfinite(nextpos).all()
        ground = points[:, 2] <= 0
        assert np.array_equal(nextpos[ground], points[ground])
        sampled = points[::max(1, len(points) // 1500)]
        jac = np.empty((len(sampled), 3, 3), dtype=np.float64)
        eps = 1e-4
        for axis in range(3):
            plus, minus = sampled.copy(), sampled.copy()
            plus[:, axis] += eps
            minus[:, axis] -= eps
            jac[:, :, axis] = (shape(plus, donor["family"], donor["age"]) - shape(minus, donor["family"], donor["age"])) / (2 * eps)
        determinants = np.linalg.det(jac)
        assert np.min(determinants) > 0.1
        moved = np.linalg.norm(nextpos - points, axis=1)
        rows.append({"family": donor["family"], "age": donor["age"], "vertices": len(points),
                     "ground_vertices_fixed": int(np.count_nonzero(ground)),
                     "moved_over_3mm": int(np.count_nonzero(moved > 0.003)),
                     "max_displacement_m": float(np.max(moved)),
                     "min_sampled_jacobian": float(np.min(determinants)),
                     "donor_bounds_m": {"minimum": points.min(axis=0).tolist(), "maximum": points.max(axis=0).tolist()},
                     "remodel_bounds_m": {"minimum": nextpos.min(axis=0).tolist(), "maximum": nextpos.max(axis=0).tolist()}})
        print("SHAPE_PREFLIGHT", donor["family"], donor["age"], rows[-1]["moved_over_3mm"])
    result = {"schema": "ccp.release040.building-shape-preflight/v1", "status": "passed", "models": rows,
              "proof": "Decoded donor numeric shape samples only; Blender export and art critique remain pending"}
    (OUT / "shape-preflight.json").write_text(json.dumps(result, indent=2), encoding="utf8")


if __name__ == "__main__":
    run()
