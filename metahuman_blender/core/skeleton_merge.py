from __future__ import annotations

from .scene_model import DNAAsset
from .skeleton_builder import compute_joint_world_positions


def merge_head_joints_into_armature(armature_object, head_asset: DNAAsset) -> int:
    """Add head/facial joints from head.dna that are missing on the body skeleton."""
    import bpy
    from mathutils import Vector

    existing = {bone.name for bone in armature_object.data.bones}
    joints_to_add = [joint for joint in head_asset.joints if joint.name not in existing]
    if not joints_to_add:
        return 0

    world_positions = compute_joint_world_positions(head_asset.joints)
    joint_by_index = {joint.index: joint for joint in head_asset.joints}

    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature_object.data.edit_bones

    for joint in joints_to_add:
        head = Vector(world_positions[joint.index])
        bone = edit_bones.new(joint.name)
        bone.head = head
        bone.tail = head + Vector((0.0, 0.0, 0.05))
        bone.roll = 0.0
        bone.use_deform = True

    for _ in range(16):
        unresolved = 0
        for joint in joints_to_add:
            bone = edit_bones.get(joint.name)
            if bone is None or bone.parent is not None:
                continue
            if joint.parent_index is None:
                continue
            parent_joint = joint_by_index.get(joint.parent_index)
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
    armature_object.select_set(False)
    return len(joints_to_add)
