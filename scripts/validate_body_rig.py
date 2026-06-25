"""Run inside Blender: blender --background --python scripts/validate_body_rig.py"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    import bpy

    skel = bpy.data.objects.get("MH_NewMetaHumanCharacter_SKEL")
    if skel is None:
        skel = next((o for o in bpy.data.objects if o.get("mhblender_role") == "deform_skeleton"), None)
    if skel is None:
        print("VALIDATION_SKIP: no deform skeleton in open file")
        return 0

    from metahuman_blender.core.character_import import resolve_character_paths
    from metahuman_blender.core.dna_loader import load_dna
    from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender
    from metahuman_blender.core.skeleton_builder import reorient_metahuman_armature
    from metahuman_blender.riglogic.body_evaluator import _pose_delta_quaternion
    from metahuman_blender.ui.properties import _binding_paths_from_preferences

    settings = bpy.context.scene.metahuman_blender
    settings.deform_skeleton_name = skel.name
    paths = resolve_character_paths(settings, skel)
    dna_path = paths.get("body_dna_path") or skel.get("mhblender_dna_path")
    if not dna_path:
        print("VALIDATION_FAIL: no DNA path")
        return 1

    asset = load_dna(dna_path, _binding_paths_from_preferences(bpy.context))
    reorient_metahuman_armature(skel, asset.joints)
    expected = compute_joint_armature_matrices_blender(asset.joints)

    max_matrix_error = 0.0
    worst = ""
    for joint in asset.joints:
        bone = skel.data.bones.get(joint.name)
        if bone is None:
            continue
        diff = max(
            abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j]))
            for i in range(4)
            for j in range(4)
        )
        if diff > max_matrix_error:
            max_matrix_error = diff
            worst = joint.name

    max_quat = 0.0
    for pb in skel.pose.bones:
        if pb.name.startswith("facial_"):
            continue
        q = _pose_delta_quaternion(skel, pb)
        max_quat = max(max_quat, abs(q.w - 1.0), abs(q.x), abs(q.y), abs(q.z))

    print(f"MATRIX_ERROR max={max_matrix_error:.6f} worst={worst}")
    print(f"QUAT_ERROR max={max_quat:.6f}")

    if max_matrix_error >= 0.05:
        print("VALIDATION_FAIL: matrix error too high")
        return 1
    if max_quat >= 0.05:
        print("VALIDATION_FAIL: quat error too high")
        return 1
    print("VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
