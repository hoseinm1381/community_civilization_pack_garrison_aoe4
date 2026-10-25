"""Import an exact decoded stock idle Action into a separate review-only pilot blend."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, read, sha, write

CLIPS = {"horseman2": 372, "elephant": 55}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", required=True, choices=CLIPS)
    parser.add_argument("--already-open", action="store_true",
                        help="Use the inspected and separately claimed live file without reopening it")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    guard()
    pilot = args.pilot
    author = read(OUT / "pilots" / pilot / "authoring.json")
    base = Path(author["blend"])
    if sha(base) != author["blend_sha256"]:
        raise RuntimeError("Base donor/remix pilot blend changed")
    clip_paths = list((OUT / "pilots" / pilot / "animation").glob(f"*-{CLIPS[pilot]}.json"))
    if len(clip_paths) != 1:
        raise RuntimeError(f"Exact native clip payload missing or ambiguous: {clip_paths}")
    clip_path = clip_paths[0]
    receipt = read(clip_path.with_name(clip_path.stem + "-receipt.json"))
    if receipt["payload_sha256"] != sha(clip_path):
        raise RuntimeError("Native sampled clip payload hash changed")
    clip = read(clip_path)
    if clip.get("status") != "decoded_predictive_preview":
        raise RuntimeError(f"Native stock clip status not previewable: {clip.get('status')}")
    if args.already_open:
        if Path(bpy.data.filepath).resolve() != base.resolve() or bpy.data.is_dirty:
            raise RuntimeError("Live file must be the unmodified pinned pilot input")
    else:
        bpy.ops.wm.open_mainfile(filepath=str(base))
    rigs = {mod.object for item in author["remix"]
            for mod in bpy.data.objects[item["remix"]].modifiers
            if mod.type == "ARMATURE" and mod.object is not None}
    if len(rigs) != 1:
        raise RuntimeError(f"Expected one exact stock deform rig: {rigs}")
    rig = rigs.pop()
    from bl_ext.raw_githubusercontent_com.garrison.unit_animation import import_clip_action
    target, action = import_clip_action(rig, clip, root_motion=False)
    scene = bpy.context.scene
    first, last = action.frame_range
    frame = int(first + (last - first) * .35)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    dest = owned(ART / "pilots" / pilot / (pilot + "_stock_idle_review.blend"))
    if dest.exists() or (OUT / "pilots" / pilot / "pose.json").exists():
        raise FileExistsError("Preserve the existing idle review scene and receipt")
    dest.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    report = {"schema": "ccp-060-native-idle-pose/v1", "pilot": pilot,
              "base_blend": str(base), "base_blend_sha256": sha(base),
              "clip_path": str(clip_path), "clip_sha256": sha(clip_path),
              "clip_source": clip.get("source"), "clip_name": clip["name"],
              "clip_index": clip["clip_index"], "clip_status": clip["status"],
              "preview_target": target.name, "native_rig_bones": len(target.data.bones),
              "action": action.name, "frame": frame,
              "blend": str(dest), "blend_sha256": sha(dest),
              "boundary": "stock RHKA predictive preview, not native match qualification"}
    write(OUT / "pilots" / pilot / "pose.json", report)
    print(json.dumps({"pilot": pilot, "action": action.name, "frame": frame,
                      "blend": str(dest)}))


if __name__ == "__main__":
    main()
