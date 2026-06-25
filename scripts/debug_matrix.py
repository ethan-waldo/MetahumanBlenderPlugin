from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main():
    import bpy
    from mathutils import Matrix, Vector

    from metahuman_blender.core.dna_loader import load_dna
    from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender, compute_joint_world_matrices
    from metahuman_blender.core.skeleton_builder import create_metahuman_armature
    from metahuman_blender.rig.control_orientation import edit_bone_from_armature_matrix
    from metahuman_blender.ui.properties import _binding_paths_from_preferences

    dna_path = Path.home() / "Downloads/OldGuy/NewMetaHumanCharacter/body.dna"
    asset = load_dna(str(dna_path), _binding_paths_from_preferences(bpy.context))
    expected = compute_joint_armature_matrices_blender(asset.joints)
    world = compute_joint_world_matrices(asset.joints)

    def diff(name):
        skel = create_metahuman_armature(asset)
        bone = skel.data.bones[name]
        joint = next(j for j in asset.joints if j.name == name)
        d = max(abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j])) for i in range(4) for j in range(4))
        bpy.data.objects.remove(skel, do_unlink=True)
        return d

    for name in ["pelvis", "spine_01", "upperarm_l", "bigtoe_02_r"]:
        print(name, diff(name))

    # Test direct matrix assignment on pelvis only
    skel = create_metahuman_armature(asset)
    bpy.context.view_layer.objects.active = skel
    bpy.ops.object.mode_set(mode="EDIT")
    eb = skel.data.edit_bones["pelvis"]
    joint = next(j for j in asset.joints if j.name == "pelvis")
    edit_bone_from_armature_matrix(eb, expected[joint.index], 0.1)
    bpy.ops.object.mode_set(mode="OBJECT")
    bone = skel.data.bones["pelvis"]
    d1 = max(abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j])) for i in range(4) for j in range(4))
    print("pelvis after armature matrix decomp", d1)

    # Test edit_bone.matrix assignment
    bpy.ops.object.mode_set(mode="EDIT")
    eb = skel.data.edit_bones["pelvis"]
    eb.matrix = expected[joint.index]
    bpy.ops.object.mode_set(mode="OBJECT")
    bone = skel.data.bones["pelvis"]
    d2 = max(abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j])) for i in range(4) for j in range(4))
    print("pelvis after edit_bone.matrix", d2)

    bpy.data.objects.remove(skel, do_unlink=True)


if __name__ == "__main__":
    main()
