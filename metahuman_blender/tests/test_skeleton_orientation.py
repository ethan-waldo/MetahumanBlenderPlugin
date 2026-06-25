from __future__ import annotations

from math import radians

from metahuman_blender.core.joint_matrices import (
    compute_joint_armature_matrices_blender,
    compute_joint_parent_matrices_blender,
    compute_joint_world_matrices,
)
from metahuman_blender.core.scene_model import MetaHumanJoint


class _Joint:
    def __init__(self, index: int, name: str, parent_index: int | None, translation, rotation):
        self.index = index
        self.name = name
        self.parent_index = parent_index
        self.neutral_translation = translation
        self.neutral_rotation = rotation
        self.lods = ()


def _make_chain_joints():
    return [
        _Joint(0, "root", None, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        _Joint(1, "pelvis", 0, (0.0, 10.0, 0.0), (0.0, 0.0, 0.0)),
        _Joint(2, "spine_01", 1, (0.0, 8.0, 0.0), (5.0, 0.0, 0.0)),
        _Joint(3, "upperarm_l", 2, (12.0, 0.0, 0.0), (0.0, 0.0, -90.0)),
    ]


def _matrix_diff(left, right) -> float:
    return max(abs(float(left[i][j]) - float(right[i][j])) for i in range(4) for j in range(4))


def test_compute_joint_world_matrices_has_expected_hierarchy():
    joints = _make_chain_joints()
    world = compute_joint_world_matrices(joints)
    assert len(world) == 4
    assert world[0].translation.length < 1e-6
    assert world[1].translation.z > world[0].translation.z


def test_armature_matrices_match_world_hierarchy():
    joints = _make_chain_joints()
    world = compute_joint_world_matrices(joints)
    armature = compute_joint_armature_matrices_blender(joints)
    for joint in joints:
        assert _matrix_diff(armature[joint.index], world[joint.index]) < 1e-5


def test_parent_matrices_are_parent_relative_only():
    joints = _make_chain_joints()
    world = compute_joint_world_matrices(joints)
    parent = compute_joint_parent_matrices_blender(joints)
    for joint in joints:
        if joint.parent_index is None:
            expected = world[joint.index]
        else:
            expected = world[joint.parent_index].inverted_safe() @ world[joint.index]
        assert _matrix_diff(parent[joint.index], expected) < 1e-5


def test_armature_matrix_translations_match_joint_world_positions():
    joints = _make_chain_joints()
    armature = compute_joint_armature_matrices_blender(joints)
    assert armature[2].translation.z > armature[1].translation.z
    assert armature[3].translation.x > armature[2].translation.x


def test_pose_delta_quaternion_is_identity_at_rest():
    joints = _make_chain_joints()
    matrix_local = compute_joint_armature_matrices_blender(joints)[2]

    class _Bone:
        def __init__(self, matrix_local):
            self.matrix_local = matrix_local
            self.name = "test"

    class _PoseBone:
        def __init__(self, matrix, bone, parent=None):
            self.matrix = matrix
            self.bone = bone
            self.parent = parent

    class _Skeleton:
        def __init__(self, matrix_local):
            self.data = type("Data", (), {"bones": {"test": _Bone(matrix_local)}})()

    def pose_delta_quaternion(skeleton, pose_bone):
        parent = pose_bone.parent
        if parent is not None:
            parent_pose_inv = parent.matrix.inverted_safe()
            parent_rest_inv = skeleton.data.bones[parent.name].matrix_local.inverted_safe()
            rest_local = parent_rest_inv @ pose_bone.bone.matrix_local
            pose_local = parent_pose_inv @ pose_bone.matrix
        else:
            rest_local = pose_bone.bone.matrix_local
            pose_local = pose_bone.matrix
        delta = rest_local.inverted_safe() @ pose_local
        return delta.to_quaternion().normalized()

    skeleton = _Skeleton(matrix_local)
    pose_bone = _PoseBone(matrix_local.copy(), skeleton.data.bones["test"])
    quat = pose_delta_quaternion(skeleton, pose_bone)
    assert abs(quat.w - 1.0) < 1e-5
    assert abs(quat.x) < 1e-5
    assert abs(quat.y) < 1e-5
    assert abs(quat.z) < 1e-5


def test_edit_bone_from_armature_matrix_preserves_y_axis():
    from mathutils import Euler, Matrix, Vector

    from metahuman_blender.rig.control_orientation import edit_bone_from_armature_matrix

    class _EditBone:
        def __init__(self):
            self.head = Vector((0.0, 0.0, 0.0))
            self.tail = Vector((0.0, 0.0, 0.0))
            self.roll = 0.0

        def align_roll(self, axis):
            self._roll_axis = axis.copy()

    matrix = Matrix.Translation(Vector((1.0, 2.0, 3.0))) @ Euler((0.0, 0.0, radians(90.0)), "XYZ").to_matrix().to_4x4()
    bone = _EditBone()
    edit_bone_from_armature_matrix(bone, matrix, 0.2)
    direction = (bone.tail - bone.head).normalized()
    expected = (matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    assert direction.dot(expected) > 0.999
