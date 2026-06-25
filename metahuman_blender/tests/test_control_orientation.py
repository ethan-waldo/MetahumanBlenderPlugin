from metahuman_blender.rig.control_orientation import is_helper_bone, pick_primary_child_index


class _Joint:
    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name


def test_is_helper_bone_detects_corrective_and_twist_bones():
    assert is_helper_bone("upperarm_correctiveRoot_l")
    assert is_helper_bone("upperarm_twist_01_l")
    assert not is_helper_bone("upperarm_l")


def test_pick_primary_child_index_prefers_anatomical_chain():
    joints = [
        _Joint(0, "upperarm_l"),
        _Joint(1, "upperarm_correctiveRoot_l"),
        _Joint(2, "lowerarm_l"),
    ]
    children = {0: [1, 2]}
    world_positions = {
        0: (0.0, 0.0, 0.0),
        1: (0.0, 0.0, 0.01),
        2: (0.5, 0.0, -0.5),
    }
    assert pick_primary_child_index("upperarm_l", 0, children, joints, world_positions) == 2
