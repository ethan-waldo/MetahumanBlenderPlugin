from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BakeValidationResult:
    ok: bool
    message: str
    constraint_count: int = 0
    keyframe_count: int = 0


def validate_bake_ready(context, skeleton, settings) -> BakeValidationResult:
    if skeleton is None:
        return BakeValidationResult(False, "No MetaHuman deform skeleton found.")

    constraint_count = sum(
        1
        for pose_bone in skeleton.pose.bones
        for constraint in pose_bone.constraints
        if constraint.name.startswith("MHBLENDER_") and not constraint.mute
    )
    if constraint_count == 0:
        return BakeValidationResult(False, "No active MetaHuman control constraints found. Build the body control rig first.")

    control_name = settings.control_rig_name or skeleton.get("mhblender_control_rig")
    if control_name:
        import bpy

        if control_name not in bpy.data.objects:
            return BakeValidationResult(False, f"Control rig {control_name} is missing from the scene.")

    if settings.frame_end < settings.frame_start:
        return BakeValidationResult(False, "Bake end frame must be greater than or equal to start frame.")

    return BakeValidationResult(True, "Ready to bake.", constraint_count=constraint_count)


def count_pose_keyframes(skeleton, frame_start: int, frame_end: int) -> int:
    if skeleton.animation_data is None or skeleton.animation_data.action is None:
        return 0

    action = skeleton.animation_data.action
    keyframes = set()
    for fcurve in action.fcurves:
        if not fcurve.data_path.startswith("pose.bones"):
            continue
        for keyframe in fcurve.keyframe_points:
            frame = int(round(keyframe.co[0]))
            if frame_start <= frame <= frame_end:
                keyframes.add((fcurve.data_path, frame))
    return len(keyframes)
