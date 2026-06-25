"""DNA skeleton matrix validation without an open .blend file."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DNA_CANDIDATES = [
    Path.home() / "Downloads/OldGuy/NewMetaHumanCharacter/body.dna",
    REPO / "testdata/body.dna",
]


def main() -> int:
    import bpy

    dna_path = next((p for p in DNA_CANDIDATES if p.exists()), None)
    if dna_path is None:
        print("VALIDATION_SKIP: no body.dna found")
        return 0

    from metahuman_blender.core.dna_loader import load_dna
    from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender
    from metahuman_blender.core.skeleton_builder import create_metahuman_armature
    from metahuman_blender.riglogic.body_evaluator import _pose_delta_quaternion
    from metahuman_blender.ui.properties import _binding_paths_from_preferences

    asset = load_dna(str(dna_path), _binding_paths_from_preferences(bpy.context))
    skel = create_metahuman_armature(asset)
    expected = compute_joint_armature_matrices_blender(asset.joints)

    max_matrix_error = 0.0
    worst = ""
    checked = 0
    for joint in asset.joints:
        bone = skel.data.bones.get(joint.name)
        if bone is None:
            continue
        diff = max(
            abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j]))
            for i in range(4)
            for j in range(4)
        )
        checked += 1
        if diff > max_matrix_error:
            max_matrix_error = diff
            worst = joint.name

    max_quat = 0.0
    for pb in skel.pose.bones:
        if pb.name.startswith("facial_"):
            continue
        q = _pose_delta_quaternion(skel, pb)
        max_quat = max(max_quat, abs(q.w - 1.0), abs(q.x), abs(q.y), abs(q.z))

    print(f"DNA={dna_path}")
    print(f"BONES={checked}")
    print(f"MATRIX_ERROR max={max_matrix_error:.6f} worst={worst}")
    print(f"QUAT_ERROR max={max_quat:.6f}")

    bpy.data.objects.remove(skel, do_unlink=True)

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
