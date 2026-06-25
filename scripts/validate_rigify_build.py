"""Validate Rigify output empty binding pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    import addon_utils
    import bpy

    if "rigify" not in bpy.context.preferences.addons:
        addon_utils.enable("rigify", default_set=True, persistent=True)

    dna_path = Path.home() / "Downloads/OldGuy/NewMetaHumanCharacter/body.dna"
    if not dna_path.exists():
        print("RIGIFY_SKIP: no body.dna")
        return 0

    from metahuman_blender.core.dna_loader import load_dna
    from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender
    from metahuman_blender.core.skeleton_builder import create_metahuman_armature
    from metahuman_blender.rig.rigify_adapter import create_rigify_body_control_rig
    from metahuman_blender.rig.rigify_binding import apply_rigify_empty_bindings, remove_rigify_empty_bindings
    from metahuman_blender.ui.properties import _binding_paths_from_preferences

    asset = load_dna(str(dna_path), _binding_paths_from_preferences(bpy.context))
    skel = create_metahuman_armature(asset)
    expected = compute_joint_armature_matrices_blender(asset.joints)
    max_rest = 0.0
    for joint in asset.joints:
        bone = skel.data.bones.get(joint.name)
        if bone is None:
            continue
        matrix_error = max(
            abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j]))
            for i in range(4)
            for j in range(4)
        )
        max_rest = max(
            max_rest,
            matrix_error,
        )
    result = create_rigify_body_control_rig(skel, asset.character_name)
    created = apply_rigify_empty_bindings(skel, result.control_rig, result.maps, asset.character_name)

    mesh_data = None
    # no mesh in background test

    bpy.context.view_layer.update()
    max_bind = 0.0
    for mapping in result.maps:
        pb = skel.pose.bones.get(mapping.mh_bone)
        empty = bpy.data.objects.get(f"MHBLENDER_bind_{mapping.mh_bone}")
        if pb is None or empty is None:
            continue
        mw = skel.matrix_world @ pb.matrix
        ew = empty.matrix_world
        max_bind = max(max_bind, max(abs(float(mw[i][j]) - float(ew[i][j])) for i in range(4) for j in range(4)))

    hand_ik = result.control_rig.pose.bones.get("hand_ik.L")
    hand_move = 0.0
    if hand_ik is not None:
        rest_mh = skel.matrix_world @ skel.pose.bones["hand_l"].matrix
        hand_ik.location.x += 0.2
        bpy.context.view_layer.update()
        moved_mh = skel.matrix_world @ skel.pose.bones["hand_l"].matrix
        hand_move = max(abs(float(rest_mh[i][j]) - float(moved_mh[i][j])) for i in range(4) for j in range(4))

    remove_rigify_empty_bindings(asset.character_name)
    for obj in (result.control_rig, result.metarig, skel):
        bpy.data.objects.remove(obj, do_unlink=True)

    if max_rest > 0.01:
        print("RIGIFY_FAIL: rest skeleton matrix error")
        return 1
    if max_bind > 0.01:
        print("RIGIFY_FAIL: rest bind error")
        return 1
    if hand_move < 0.05:
        print("RIGIFY_FAIL: Rigify IK control did not move MH hand")
        return 1
    print("RIGIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
