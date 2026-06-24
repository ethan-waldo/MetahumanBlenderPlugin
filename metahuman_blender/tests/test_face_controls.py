from types import SimpleNamespace

from metahuman_blender.rig.face_controls import _bone_to_gui_value


class _FakeBone:
    def __init__(self, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), props=None):
        self.location = SimpleNamespace(x=location[0], y=location[1], z=location[2])
        self.rotation_euler = SimpleNamespace(x=rotation[0], y=rotation[1], z=rotation[2])
        self._props = props or {}

    def get(self, key, default=None):
        return self._props.get(key, default)


def test_bone_to_gui_value_is_zero_at_rest_for_bipolar_axis():
    bone = _FakeBone(props={"mhblender_gui_src_min": -1.0, "mhblender_gui_src_max": 1.0})
    assert _bone_to_gui_value(bone, "translate.x") == 0.0


def test_bone_to_gui_value_maps_positive_bipolar_travel():
    bone = _FakeBone(location=(0.5, 0.0, 0.0), props={"mhblender_gui_src_min": -1.0, "mhblender_gui_src_max": 1.0})
    assert _bone_to_gui_value(bone, "translate.x") == 0.5


def test_bone_to_gui_value_without_channel_uses_pose_offset_not_rest_translation():
    bone = _FakeBone()
    assert _bone_to_gui_value(bone, None) == 0.0
