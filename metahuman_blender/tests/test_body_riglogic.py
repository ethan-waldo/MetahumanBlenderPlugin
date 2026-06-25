from __future__ import annotations

from mathutils import Matrix

from metahuman_blender.riglogic.body_evaluator import (
    _apply_joint_outputs,
    _looks_like_body_corrective_name,
    _set_raw_controls_from_pose,
)


class _Instance:
    def __init__(self):
        self.values = {}

    def setRawControl(self, index, value):
        self.values[index] = value


class _Bone:
    def __init__(self, name, matrix):
        self.name = name
        self.matrix_local = matrix


class _PoseBone:
    def __init__(self, name, matrix=None):
        self.name = name
        self.matrix = matrix or Matrix.Identity(4)
        self.bone = _Bone(name, self.matrix.copy())
        self.parent = None
        self.location = (1.0, 2.0, 3.0)
        self.rotation_mode = "XYZ"
        self.rotation_euler = (0.1, 0.2, 0.3)
        self.scale = (1.5, 1.0, 0.5)


class _Skeleton:
    def __init__(self, pose_bones):
        bones = {bone.name: bone for bone in pose_bones}
        self.pose = type("Pose", (), {"bones": bones})()
        self.data = type("Data", (), {"bones": {name: bone.bone for name, bone in bones.items()}})()


class _Reader:
    def __init__(self, names):
        self.names = names

    def getJointCount(self):
        return len(self.names)

    def getJointName(self, index):
        return self.names[index]


def test_raw_controls_reset_to_identity_before_pose_sampling():
    instance = _Instance()
    raw_map = {
        "upperarm_l": {"x": 0, "y": 1, "z": 2, "w": 3},
        "missing_bone": {"x": 4, "w": 5},
    }
    skeleton = _Skeleton([_PoseBone("upperarm_l")])

    for index in range(6):
        instance.values[index] = 0.75

    _set_raw_controls_from_pose(instance, raw_map, skeleton)

    assert instance.values[0] == 0.0
    assert instance.values[1] == 0.0
    assert instance.values[2] == 0.0
    assert instance.values[3] == 1.0
    assert instance.values[4] == 0.0
    assert instance.values[5] == 1.0


def test_zero_body_joint_output_clears_previous_corrective_pose():
    pose_bone = _PoseBone("calf_correctiveRoot_l")
    skeleton = _Skeleton([pose_bone])
    reader = _Reader(["calf_correctiveRoot_l"])

    driven = _apply_joint_outputs(reader, [0.0] * 9, skeleton, skip_bones=set(), facial_only=False)

    assert driven == 0
    assert tuple(pose_bone.location) == (0.0, 0.0, 0.0)
    assert tuple(pose_bone.rotation_euler) == (0.0, 0.0, 0.0)
    assert tuple(pose_bone.scale) == (1.0, 1.0, 1.0)


def test_body_corrective_name_filter_skips_primary_chain_bones():
    assert _looks_like_body_corrective_name("upperarm_correctiveRoot_l")
    assert _looks_like_body_corrective_name("thigh_out_l")
    assert _looks_like_body_corrective_name("index_02_bulge_l")
    assert not _looks_like_body_corrective_name("spine_03")
    assert not _looks_like_body_corrective_name("upperarm_l")
