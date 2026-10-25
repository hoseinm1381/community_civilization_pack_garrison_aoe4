"""Create editable buffalo idle and walk Actions on a copy of the 45-bone rig.

This is a source-authoring trial only. It does not export, encode, cook, or
integrate animation into an AoE4 package. Run in background Blender only after
the serialized Blender/cook owner gives the go-ahead:

    blender.exe -b --python tools/release_081/animation_source.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).parent))
from common import ART, OUT, guard, write


SOURCE_REVISION = "r5"
SOURCE = ART / "buffalo" / SOURCE_REVISION / "model.blend"
TRIAL = ART / "animation" / "buffalo-trial.blend"
REPORT = OUT / "art" / "animation" / "buffalo-trial-source.json"
IDLE_FRAMES = (1, 31, 61, 91, 121)
WALK_FRAMES = (1, 7, 13, 19, 25)
ROOT_NAME = "root_m"


def finite_matrix(matrix) -> bool:
    return all(math.isfinite(float(matrix[row][col])) for row in range(4) for col in range(4))


def world_axis_local(bone, world_axis: Vector) -> Vector:
    """Convert an armature-space axis to the bone's rest-local axis."""
    axis = bone.matrix_local.to_3x3().inverted() @ world_axis
    if axis.length < 1e-8:
        raise ValueError(f"Cannot convert rotation axis for bone {bone.name}")
    return axis.normalized()


def set_world_axis_angle(pose_bone, axis: Vector, angle: float) -> None:
    pose_bone.rotation_mode = "QUATERNION"
    pose_bone.rotation_quaternion = Quaternion(world_axis_local(pose_bone.bone, axis), angle)


def clear_pose(rig) -> None:
    rig.animation_data_clear()
    rig.animation_data_create()
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def key_rotations(rig, frame: int, angles: dict[str, tuple[Vector, float]]) -> None:
    for name, (axis, angle) in angles.items():
        pose_bone = rig.pose.bones.get(name)
        if pose_bone is None:
            raise KeyError(f"Required native cattle bone is missing: {name}")
        set_world_axis_angle(pose_bone, axis, angle)
        pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=name)


def smooth_action(action) -> None:
    # Auto-clamped handles keep the duplicated loop endpoint from overshooting.
    try:
        curves = action.fcurves
    except (AttributeError, RuntimeError):
        # Blender's layered Action API can omit the legacy collection; inserted
        # keys already use Blender's default Bezier interpolation in that case.
        return
    for fcurve in curves:
        for key in fcurve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"


def idle_angles(rig, phase: float) -> dict[str, tuple[Vector, float]]:
    pitch = Vector((1.0, 0.0, 0.0))
    ear_axis = Vector((0.0, 1.0, 0.0))
    tail_axis = Vector((0.0, 0.0, 1.0))
    breath = math.sin(phase)
    result = {
        "neck_m": (pitch, 0.035 * breath),
        "neck1_m": (pitch, 0.070 * breath),
        "head_m": (pitch, 0.140 * breath),
        "ear_l": (ear_axis, 0.085 * math.sin(phase + 0.25)),
        "ear1_l": (ear_axis, 0.045 * math.sin(phase + 0.45)),
        "ear_r": (ear_axis, -0.075 * math.sin(phase - 0.20)),
        "ear1_r": (ear_axis, -0.040 * math.sin(phase - 0.35)),
    }
    for index, scale in enumerate((0.055, 0.090, 0.075, 0.050), start=1):
        result[f"tail{index}_m"] = (tail_axis, scale * math.sin(phase - index * 0.24))
    return result


def walk_angles(rig, phase: float) -> dict[str, tuple[Vector, float]]:
    swing_axis = Vector((1.0, 0.0, 0.0))
    sway_axis = Vector((0.0, 0.0, 1.0))
    result: dict[str, tuple[Vector, float]] = {}
    # Four-beat sequence: fore-left, fore-right, hind-left, hind-right.
    # Joint rotations are expressed around armature-space X
    # transformed through each bone's actual rest-local orientation.
    legs = (
        ("front", "l", 0.0, ("frontrump_l", "fronthip_l", "frontknee_l", "frontankle_l", "fronttoes_l")),
        ("front", "r", math.pi / 2.0, ("frontrump_r", "fronthip_r", "frontknee_r", "frontankle_r", "fronttoes_r")),
        ("back", "l", math.pi, ("backhip_l", "backknee_l", "backankle_l", "backtoes3_l")),
        ("back", "r", 3.0 * math.pi / 2.0, ("backhip_r", "backknee_r", "backankle_r", "backtoes3_r")),
    )
    for family, side, offset, names in legs:
        gait = math.sin(phase + offset)
        lift = max(0.0, math.cos(phase + offset))
        sign = 1.0 if family == "front" else -1.0
        values = (0.19 * gait * sign, 0.10 * gait * sign, 0.27 * lift, -0.14 * lift, 0.055 * lift)
        if family == "back":
            values = values[:4]
        for name, angle in zip(names, values):
            result[name] = (swing_axis, angle)

    result.update({
        "spine1_m": (swing_axis, 0.018 * math.sin(phase * 2.0)),
        "chest_m": (swing_axis, 0.025 * math.sin(phase * 2.0 + 0.2)),
        "neck_m": (swing_axis, -0.025 * math.sin(phase * 2.0)),
        "neck1_m": (swing_axis, -0.035 * math.sin(phase * 2.0)),
        "head_m": (swing_axis, -0.045 * math.sin(phase * 2.0)),
        "ear_l": (Vector((0.0, 1.0, 0.0)), 0.035 * math.sin(phase * 2.0)),
        "ear_r": (Vector((0.0, 1.0, 0.0)), -0.035 * math.sin(phase * 2.0)),
        "tail1_m": (sway_axis, 0.045 * math.sin(phase)),
        "tail2_m": (sway_axis, 0.075 * math.sin(phase - 0.15)),
        "tail3_m": (sway_axis, 0.065 * math.sin(phase - 0.30)),
        "tail4_m": (sway_axis, 0.045 * math.sin(phase - 0.45)),
    })
    return result


def set_cycle(action_name: str, rig, frames: tuple[int, ...], angle_function) -> dict:
    clear_pose(rig)
    action = bpy.data.actions.new(action_name)
    rig.animation_data.action = action
    end = frames[-1]
    cycle_length = end - frames[0]
    for frame in frames:
        phase = 2.0 * math.pi * (frame - frames[0]) / cycle_length
        key_rotations(rig, frame, angle_function(rig, phase))
    action.use_fake_user = True
    smooth_action(action)
    return {"action": action, "frames": frames}


def evaluated_mesh_points(rig, scene, frame: int) -> tuple[dict[str, list[Vector]], float]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out: dict[str, list[Vector]] = {}
    for obj in sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name):
        if not any(m.type == "ARMATURE" and m.object == rig for m in obj.modifiers):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points = [v.co.copy() for v in mesh.vertices]
            if points:
                out[obj.name] = points
        finally:
            evaluated.to_mesh_clear()
    pose_delta = 0.0
    for pose_bone in rig.pose.bones:
        if not finite_matrix(pose_bone.matrix):
            raise ValueError(f"Non-finite pose matrix at frame {frame}: {pose_bone.name}")
        rest = pose_bone.bone.matrix_local
        delta = max(abs(pose_bone.matrix[row][col] - rest[row][col]) for row in range(4) for col in range(4))
        pose_delta = max(pose_delta, float(delta))
    return out, pose_delta


def sample_action(rig, scene, action_info: dict) -> dict:
    action = action_info["action"]
    frames = action_info["frames"]
    rig.animation_data.action = action
    # Loop endpoints are the same pose for every bone; root channels remain unset.
    scene.frame_set(frames[0]); bpy.context.view_layer.update()
    first = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    first_meshes, _ = evaluated_mesh_points(rig, scene, frames[0])
    scene.frame_set(frames[-1]); bpy.context.view_layer.update()
    last = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    endpoint_delta = max(
        abs(first[name][row][col] - last[name][row][col])
        for name in first for row in range(4) for col in range(4)
    )
    if endpoint_delta > 1e-5:
        raise AssertionError(f"{action.name} endpoints diverge: {endpoint_delta}")

    root = rig.pose.bones.get(ROOT_NAME)
    if root is None:
        raise KeyError(f"Native cattle root bone missing: {ROOT_NAME}")
    root_errors = []
    mesh_delta = 0.0
    pose_delta = 0.0
    sample_frames = sorted(set(frames + tuple(round(frames[0] + (frames[-1] - frames[0]) * i / 8) for i in range(1, 8))))
    for frame in sample_frames:
        meshes, pdelta = evaluated_mesh_points(rig, scene, frame)
        pose_delta = max(pose_delta, pdelta)
        if set(meshes) != set(first_meshes):
            raise AssertionError(f"Skinned mesh set changed at frame {frame}: {sorted(meshes)}")
        for name, points in meshes.items():
            before = first_meshes[name]
            if len(points) != len(before):
                raise AssertionError(f"Mesh vertex count changed at frame {frame}: {name}")
            for a, b in zip(before, points):
                if not all(math.isfinite(float(x)) for x in b):
                    raise ValueError(f"Non-finite evaluated vertex at frame {frame}: {name}")
                mesh_delta = max(mesh_delta, (b - a).length)
        root_errors.append({
            "frame": frame,
            "location_max_abs": max(abs(float(v)) for v in root.location),
            "scale_max_abs_error_from_one": max(abs(float(v) - 1.0) for v in root.scale),
            "rotation_max_abs_from_identity": max(abs(float(root.rotation_quaternion[i] - (1.0 if i == 0 else 0.0))) for i in range(4)),
        })
    if any(max(row["location_max_abs"], row["scale_max_abs_error_from_one"], row["rotation_max_abs_from_identity"]) > 1e-6 for row in root_errors):
        raise AssertionError(f"{action.name} moved or scaled root_m: {root_errors}")
    if mesh_delta <= 1e-7 or pose_delta <= 1e-7:
        raise AssertionError(f"{action.name} did not produce measurable deformation: mesh={mesh_delta}, pose={pose_delta}")

    return {
        "action": action.name,
        "frame_range": [frames[0], frames[-1]],
        "sample_frames": sample_frames,
        "fps": scene.render.fps,
        "loop_endpoint_max_matrix_basis_delta": endpoint_delta,
        "root_stationary": True,
        "root_scale_one": True,
        "root_samples": root_errors,
        "skinned_meshes": {name: len(points) for name, points in first_meshes.items()},
        "sampled_max_vertex_delta": mesh_delta,
        "sampled_max_pose_matrix_delta_from_rest": pose_delta,
        "sampled_deformation_finite_nonzero": True,
        "qualification": "editable Blender Action only; no Garrison animation encoding/export qualification",
    }


def main() -> None:
    guard()
    if TRIAL.exists():
        raise FileExistsError(f"Preserving existing trial source: {TRIAL}")
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise AssertionError(f"Expected one native buffalo armature, found {len(armatures)}")
    rig = armatures[0]
    if len(rig.data.bones) != 45:
        raise AssertionError(f"Expected retained cattle45 skeleton, found {len(rig.data.bones)} bones")
    rig.data.pose_position = "POSE"
    required = {
        ROOT_NAME, "spine1_m", "chest_m", "neck_m", "neck1_m", "head_m",
        "ear_l", "ear1_l", "ear_r", "ear1_r",
        "tail1_m", "tail2_m", "tail3_m", "tail4_m",
        "frontrump_l", "fronthip_l", "frontknee_l", "frontankle_l", "fronttoes_l",
        "frontrump_r", "fronthip_r", "frontknee_r", "frontankle_r", "fronttoes_r",
        "backhip_l", "backknee_l", "backankle_l", "backtoes3_l",
        "backhip_r", "backknee_r", "backankle_r", "backtoes3_r",
    }
    missing = sorted(required - set(rig.data.bones.keys()))
    if missing:
        raise AssertionError(f"Expected cattle45 controls are missing: {missing}")

    scene = bpy.context.scene
    scene.render.fps = 30
    idle = set_cycle("buffalo_idle_source_trial", rig, IDLE_FRAMES, idle_angles)
    idle_result = sample_action(rig, scene, idle)
    walk = set_cycle("buffalo_walk_source_trial", rig, WALK_FRAMES, walk_angles)
    walk_result = sample_action(rig, scene, walk)
    rig.animation_data.action = idle["action"]
    scene.frame_end = IDLE_FRAMES[-1]
    scene.frame_set(IDLE_FRAMES[0])
    bpy.context.view_layer.update()

    TRIAL.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(TRIAL), copy=True)
    write(REPORT, {
        "status": "source_animation_trial_authored",
        "source": str(SOURCE),
        "source_revision": SOURCE_REVISION,
        "trial_copy": str(TRIAL),
        "actions": [idle_result, walk_result],
        "skeleton": {
            "armature_object": rig.name,
            "bone_count": len(rig.data.bones),
            "bone_names": sorted(b.name for b in rig.data.bones),
            "original_rest_binds_preserved": True,
            "pose_scale_one": True,
        },
        "boundaries": {
            "source_only": True,
            "exported": False,
            "cooked": False,
            "integrated": False,
            "native_game_tested": False,
            "native_animation_qualification": False,
        },
    })
    print(f"081_ANIMATION_SOURCE_TRIAL {TRIAL}")
    print(f"081_ANIMATION_SOURCE_REPORT {REPORT}")


if __name__ == "__main__":
    main()
