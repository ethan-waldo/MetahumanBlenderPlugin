from __future__ import annotations

from ..core.dna_loader import load_dna
from ..riglogic.control_map import ControlMap


def link_faceboard_to_character(faceboard_object, character_name: str, head_dna_path: str) -> int:
    faceboard_object["mhblender_role"] = "faceboard"
    faceboard_object["mhblender_character"] = character_name
    faceboard_object["mhblender_head_dna_path"] = head_dna_path
    faceboard_object.show_in_front = True

    if not head_dna_path:
        return create_face_control_placeholders(faceboard_object, [])

    try:
        asset = load_dna(head_dna_path)
    except Exception:
        return create_face_control_placeholders(faceboard_object, [])

    control_map = ControlMap.from_names(asset.gui_controls, asset.raw_controls)
    faceboard_object["mhblender_gui_controls_json"] = ",".join(asset.gui_controls)
    mapped = 0
    for gui_name in asset.gui_controls:
        bone = _find_faceboard_bone(faceboard_object, gui_name)
        if bone is None:
            continue
        bone["mhblender_gui_control"] = gui_name
        channel = _parse_gui_channel(gui_name)
        if channel is not None and "mhblender_gui_axis" not in bone:
            bone["mhblender_gui_axis"] = channel
        if control_map.gui_index(gui_name) is not None:
            mapped += 1
    return mapped


def create_face_control_placeholders(control_object, gui_controls: list[str]) -> int:
    for name in gui_controls:
        control_object[f"face_{name}"] = 0.0
    return len(gui_controls)


def read_face_gui_values(settings, gui_names: list[str]) -> dict[str, float]:
    from ..ui.face_sliders import read_face_gui_values as _read_face_gui_values

    return _read_face_gui_values(settings, gui_names)


def read_gui_control_values(faceboard_object, gui_controls: list[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for gui_name in gui_controls:
        bone = _find_faceboard_bone(faceboard_object, gui_name)
        if bone is None:
            values[gui_name] = float(faceboard_object.get(f"face_{gui_name}", 0.0))
            continue
        if "mhblender_gui_value" in bone:
            values[gui_name] = float(bone["mhblender_gui_value"])
            continue
        channel = _parse_gui_channel(gui_name) or bone.get("mhblender_gui_axis")
        values[gui_name] = _bone_to_gui_value(bone, channel)
    return values


def _find_faceboard_bone(faceboard_object, gui_name: str):
    pose_bones = faceboard_object.pose.bones
    base_name, _ = _split_gui_name(gui_name)
    candidates = (
        gui_name,
        base_name,
        gui_name.removeprefix("GUI_"),
        gui_name.removeprefix("gui_"),
        f"GUI_{gui_name}",
        f"GUI_{base_name}",
    )
    for candidate in candidates:
        bone = pose_bones.get(candidate)
        if bone is not None:
            return bone
    lowered = base_name.lower()
    for pose_bone in pose_bones:
        if pose_bone.name.lower() == lowered or pose_bone.get("mhblender_gui_control") == gui_name:
            return pose_bone
    return None


def _split_gui_name(gui_name: str) -> tuple[str, str | None]:
    if "." not in gui_name:
        return gui_name, None
    return gui_name.rsplit(".", 1)


def _parse_gui_channel(gui_name: str) -> str | None:
    base_name, suffix = _split_gui_name(gui_name)
    if suffix is None:
        return None
    channel_map = {
        "tx": "translate.x",
        "ty": "translate.z",
        "tz": "translate.y",
        "rx": "rotate.x",
        "ry": "rotate.z",
        "rz": "rotate.y",
    }
    return channel_map.get(suffix)


def _bone_to_gui_value(pose_bone, channel: str | None = None) -> float:
    if channel is None:
        location = pose_bone.location
        rotation = pose_bone.rotation_euler
        magnitude = max(
            abs(float(location.x)),
            abs(float(location.y)),
            abs(float(location.z)),
            abs(float(rotation.x)),
            abs(float(rotation.y)),
            abs(float(rotation.z)),
        )
        return max(0.0, min(1.0, magnitude))

    mode, axis = channel.split(".", 1)
    if mode == "translate":
        value = float(getattr(pose_bone.location, axis))
    elif mode == "rotate":
        value = float(getattr(pose_bone.rotation_euler, axis))
    else:
        return 0.0

    if abs(value) < 1.0e-6:
        return 0.0

    src_min = float(pose_bone.get("mhblender_gui_src_min", 0.0))
    src_max = float(pose_bone.get("mhblender_gui_src_max", 1.0))

    # MetaHuman DNA GUI channels are unipolar 0-1 with neutral at 0.
    if src_max > src_min > 0:
        return max(0.0, min(1.0, (value - src_min) / (src_max - src_min)))

    if src_min < 0 < src_max:
        if value > 0:
            return max(0.0, min(1.0, value / src_max))
        return max(0.0, min(1.0, (-value) / (-src_min)))

    if src_max > 0:
        return max(0.0, min(1.0, abs(value) / src_max))

    return max(0.0, min(1.0, abs(value)))
