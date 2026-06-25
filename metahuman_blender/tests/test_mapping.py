from types import SimpleNamespace

from metahuman_blender.core.rig_mapping import (
    control_name_for_bone,
    infer_body_rig_map,
    is_body_bone,
    is_body_control_bone,
    rig_maps_from_json,
    rig_maps_to_json,
)


class FakeArmature:
    def __init__(self, names):
        self.data = SimpleNamespace(bones=[SimpleNamespace(name=name) for name in names])


def test_body_bone_filter_skips_facial_bones():
    assert is_body_bone("spine_01")
    assert is_body_bone("upperarm_l")
    assert not is_body_bone("FACIAL_C_FacialRoot")


def test_body_control_bone_excludes_head_for_face_panel():
    assert is_body_control_bone("spine_01")
    assert not is_body_control_bone("head")


def test_infer_body_rig_map_matches_stable_control_names():
    mh = FakeArmature(["root", "spine_01", "FACIAL_C_FacialRoot"])
    ctrl = FakeArmature([control_name_for_bone("root"), control_name_for_bone("spine_01")])

    report = infer_body_rig_map(mh, ctrl)

    assert report.is_valid
    assert [item.mh_bone for item in report.maps] == ["root", "spine_01"]
    assert report.skipped_bones == ["FACIAL_C_FacialRoot"]


def test_rig_map_json_roundtrip_supports_slotted_dataclasses():
    mh = FakeArmature(["root"])
    ctrl = FakeArmature([control_name_for_bone("root")])
    report = infer_body_rig_map(mh, ctrl)

    restored = rig_maps_from_json(rig_maps_to_json(report.maps))

    assert restored[0].mh_bone == "root"
    assert restored[0].control_bone == "CTRL_root"
