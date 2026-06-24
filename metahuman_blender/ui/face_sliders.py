"""Facial GUI controls as sidebar sliders (temporary replacement for the 3D faceboard)."""

import bpy

_SYNCING_FACE_CONTROLS = False


class MHB_OT_ResetFaceSliders(bpy.types.Operator):
    bl_idname = "mhblender.reset_face_sliders"
    bl_label = "Reset Face Sliders"
    bl_description = "Set all facial GUI sliders back to neutral (0)"

    def execute(self, context):
        from .properties import get_settings

        settings = get_settings(context)
        reset_face_gui_values(settings)
        if settings.enable_face_riglogic:
            from ..riglogic.evaluator import evaluate_face_for_context

            result = evaluate_face_for_context(context)
            settings.face_riglogic_last_error = "" if result.ok else result.message
        self.report({"INFO"}, "Face sliders reset to neutral.")
        return {"FINISHED"}


classes = (MHB_OT_ResetFaceSliders,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def face_gui_control_count(settings) -> int:
    collection = getattr(settings, "face_gui_controls", None)
    if collection is None or not hasattr(collection, "__len__"):
        return 0
    return len(collection)


def draw_face_controls_panel(layout, context) -> None:
    from .properties import get_settings

    settings = get_settings(context)
    control_count = face_gui_control_count(settings)

    if control_count == 0:
        layout.label(text="Import ExportManifest with head DNA first.", icon="INFO")
        return

    row = layout.row(align=True)
    row.prop(settings, "face_gui_filter", text="", icon="VIEWZOOM")
    row.operator("mhblender.reset_face_sliders", icon="LOOP_BACK", text="")

    needle = (settings.face_gui_filter or "").strip().lower()
    shown = 0
    for item in settings.face_gui_controls:
        if needle and needle not in item.control_name.lower():
            continue
        row = layout.row(align=True)
        row.prop(item, "value", text=_short_control_label(item.control_name), slider=True)
        shown += 1

    if needle:
        layout.label(text=f"{shown} matching control(s)", icon="INFO")
    elif control_count > 0:
        layout.label(text=f"{control_count} control(s)", icon="INFO")


def sync_face_gui_controls(settings, head_dna_path: str, binding_paths: list[str] | None = None) -> int:
    from ..core.dna_loader import load_dna

    global _SYNCING_FACE_CONTROLS
    _SYNCING_FACE_CONTROLS = True
    try:
        asset = load_dna(head_dna_path, binding_paths=binding_paths)
        settings.face_gui_controls.clear()
        for gui_name in asset.gui_controls:
            item = settings.face_gui_controls.add()
            item.control_name = gui_name
            item.value = 0.0
        return len(asset.gui_controls)
    finally:
        _SYNCING_FACE_CONTROLS = False


def reset_face_gui_values(settings) -> None:
    global _SYNCING_FACE_CONTROLS
    _SYNCING_FACE_CONTROLS = True
    try:
        for item in settings.face_gui_controls:
            item.value = 0.0
    finally:
        _SYNCING_FACE_CONTROLS = False


def read_face_gui_values(settings, gui_names: list[str]) -> dict[str, float]:
    stored = {item.control_name: float(item.value) for item in settings.face_gui_controls}
    return {name: stored.get(name, 0.0) for name in gui_names}


def on_face_gui_value_changed(_self, context) -> None:
    if _SYNCING_FACE_CONTROLS:
        return
    settings = context.scene.metahuman_blender
    if not getattr(settings, "enable_face_riglogic", False):
        return
    from ..riglogic.evaluator import evaluate_face_for_context

    result = evaluate_face_for_context(context)
    settings.face_riglogic_last_error = "" if result.ok else result.message


def _short_control_label(control_name: str) -> str:
    if len(control_name) <= 28:
        return control_name
    return f"...{control_name[-25:]}"
