"""Summarize decoded stock building geometry without changing it."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for family in ("barracks", "town_center"):
    for age in range(1, 5):
        path = next((ROOT / f"art/stock_cache/buildings_020/barracks_tc/{family}/age{age:02}").rglob("decoded-static.json"))
        d = json.loads(path.read_text())
        groups = d["geometry"]["groups"]
        allpts = [p for g in groups for p in g["positions"]]
        bounds = [[round(min(p[i] for p in allpts), 3), round(max(p[i] for p in allpts), 3)] for i in range(3)]
        print(f"{family} {age}: groups={len(groups)} vertices={len(allpts)} xyz={bounds}")
        for g in groups:
            pts = g["positions"]
            box = [[round(min(p[i] for p in pts), 2), round(max(p[i] for p in pts), 2)] for i in range(3)]
            print(f"  {g['preview_material']:<18} vertices={len(pts):>6} xyz={box}")
