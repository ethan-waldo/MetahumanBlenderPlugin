from types import SimpleNamespace

from metahuman_blender.core.bake_validation import validate_bake_ready


class FakeSettings:
    control_rig_name = "CTRL_body_RIG"
    frame_start = 1
    frame_end = 10


class FakeConstraint:
    name = "MHBLENDER_CTRL_root"
    mute = False


class FakePoseBone:
    constraints = [FakeConstraint()]


class FakeSkeleton:
    animation_data = None

    def __init__(self):
        self.pose = SimpleNamespace(bones=[FakePoseBone()])
        self.data = {"mhblender_control_rig": "CTRL_body_RIG"}


def test_validate_bake_ready_requires_constraints(monkeypatch):
    skeleton = FakeSkeleton()

    class FakeBpyData:
        objects = {"CTRL_body_RIG": object()}

    monkeypatch.setitem(__import__("sys").modules, "bpy", SimpleNamespace(data=FakeBpyData()))
    result = validate_bake_ready(SimpleNamespace(), skeleton, FakeSettings())
    assert result.ok
    assert result.constraint_count == 1
