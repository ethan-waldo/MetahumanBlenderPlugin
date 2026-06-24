from __future__ import annotations


def create_face_control_placeholders(control_object, gui_controls: list[str]) -> int:
    for name in gui_controls:
        control_object[f"face_{name}"] = 0.0
    return len(gui_controls)
