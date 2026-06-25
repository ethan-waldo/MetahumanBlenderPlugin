from __future__ import annotations

from .scene_model import DNAAsset
from .skeleton_builder import _apply_dna_matrices_to_armature


def merge_head_joints_into_armature(armature_object, head_asset: DNAAsset) -> int:
    """Add head/facial joints from head.dna that are missing on the body skeleton."""
    import bpy

    existing = {bone.name for bone in armature_object.data.bones}
    joints_to_add = [joint for joint in head_asset.joints if joint.name not in existing]
    if not joints_to_add:
        return 0

    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature_object.data.edit_bones

    for joint in joints_to_add:
        bone = edit_bones.new(joint.name)
        bone.use_deform = True

    for _ in range(16):
        unresolved = 0
        for joint in joints_to_add:
            bone = edit_bones.get(joint.name)
            if bone is None or bone.parent is not None:
                continue
            if joint.parent_index is None:
                continue
            parent_joint = next((item for item in head_asset.joints if item.index == joint.parent_index), None)
            if parent_joint is None:
                unresolved += 1
                continue
            parent_bone = edit_bones.get(parent_joint.name)
            if parent_bone is None:
                unresolved += 1
                continue
            bone.parent = parent_bone
            bone.use_connect = False
        if unresolved == 0:
            break

    bpy.ops.object.mode_set(mode="OBJECT")
    added_names = {joint.name for joint in joints_to_add}
    _apply_dna_matrices_to_armature(armature_object, head_asset.joints, existing_only=added_names)
    return len(joints_to_add)
