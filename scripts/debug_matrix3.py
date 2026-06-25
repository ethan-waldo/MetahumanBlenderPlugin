"""Build skeleton using edit_bone.matrix = DNA armature-space matrices."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def create_armature_from_local_matrices(asset):
    import bpy

    from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender, joint_bone_length
    from metahuman_blender.core.skeleton_builder import _joint_children, _pick_tail_child_index
    from metahuman_blender.core.joint_matrices import compute_joint_world_matrices

    armature = compute_joint_armature_matrices_blender(asset.joints)
    world = compute_joint_world_matrices(asset.joints)
    children = _joint_children(asset.joints)

    arm = bpy.data.armatures.new("TEST_SKEL_Data")
    obj = bpy.data.objects.new("TEST_SKEL", arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit = arm.edit_bones

    for joint in asset.joints:
        bone = edit.new(joint.name)
        bone.use_deform = True

    for joint in asset.joints:
        if joint.parent_index is not None:
            parent = asset.joints[joint.parent_index]
            edit[joint.name].parent = edit[parent.name]
            edit[joint.name].use_connect = False

    for joint in asset.joints:
        bone = edit[joint.name]
        bone.matrix = armature[joint.index]
        child_index = _pick_tail_child_index(joint, children, asset.joints, world)
        length = joint_bone_length(joint, asset.joints, world, child_index)
        # Ensure non-zero bone length for Blender
        direction = (bone.tail - bone.head)
        if direction.length < 0.001:
            y = armature[joint.index].to_3x3() @ __import__("mathutils").Vector((0, 1, 0))
            if y.length > 1e-6:
                bone.tail = bone.head + y.normalized() * length

    bpy.ops.object.mode_set(mode="OBJECT")
    return obj, armature


def main():
    import bpy

    from metahuman_blender.core.dna_loader import load_dna
    from metahuman_blender.ui.properties import _binding_paths_from_preferences

    dna_path = Path.home() / "Downloads/OldGuy/NewMetaHumanCharacter/body.dna"
    asset = load_dna(str(dna_path), _binding_paths_from_preferences(bpy.context))
    obj, expected = create_armature_from_local_matrices(asset)

    max_err = 0.0
    worst = ""
    for joint in asset.joints:
        bone = obj.data.bones.get(joint.name)
        if bone is None:
            continue
        diff = max(
            abs(float(bone.matrix_local[r][c]) - float(expected[joint.index][r][c]))
            for r in range(4)
            for c in range(4)
        )
        if diff > max_err:
            max_err = diff
            worst = joint.name
    print(f"MATRIX_ERROR max={max_err:.6f} worst={worst}")
    bpy.data.objects.remove(obj, do_unlink=True)
    return 0 if max_err < 0.01 else 1


if __name__ == "__main__":
    raise SystemExit(main())
