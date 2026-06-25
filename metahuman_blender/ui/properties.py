ADDON_ID = "metahuman_blender"

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


def _discover_binding_paths() -> list[str]:
    from pathlib import Path

    addon_root = Path(__file__).resolve().parents[1]
    repo_root = addon_root.parent
    candidates = [
        repo_root / "build" / "openriglogic-blender" / "python",
    ]
    return [str(path) for path in candidates if path.exists()]


def _binding_paths_from_preferences(context) -> list[str]:
    paths: list[str] = []
    prefs = get_addon_preferences(context)
    if prefs and prefs.openriglogic_python_path:
        paths.append(prefs.openriglogic_python_path)
    for path in _discover_binding_paths():
        if path not in paths:
            paths.append(path)
    return paths


def get_addon_preferences(context):
    addon = context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None


def get_settings(context):
    return context.scene.metahuman_blender


def _update_lod_visibility(self, context):
    from ..core.lod import set_lod_visibility

    set_lod_visibility(self.character_name, self.current_lod)


def _update_face_gui_value(self, context):
    from .face_sliders import on_face_gui_value_changed

    on_face_gui_value_changed(self, context)


def _update_body_corrective_visibility(self, context):
    from ..riglogic.body_evaluator import set_body_corrective_bone_visibility

    set_body_corrective_bone_visibility(context, self.show_body_corrective_bones)


class MHB_PG_FaceGuiControl(bpy.types.PropertyGroup):
    control_name: StringProperty(name="Control", default="")
    value: FloatProperty(
        name="Value",
        description="MetaHuman facial GUI control (0 = neutral, 1 = full)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        update=_update_face_gui_value,
    )


class MHB_PG_Settings(bpy.types.PropertyGroup):
    export_manifest_path: StringProperty(
        name="Export Manifest",
        description="Path to ExportManifest.json from the MetaHuman DCC export package",
        subtype="FILE_PATH",
        default="",
    )
    dna_path: StringProperty(
        name="Body DNA",
        description="Resolved from ExportManifest when set",
        subtype="FILE_PATH",
        default="",
    )
    character_name: StringProperty(name="Character", default="")
    deform_skeleton_name: StringProperty(name="Deform Skeleton", default="")
    control_rig_name: StringProperty(name="Control Rig", default="")
    head_dna_path: StringProperty(
        name="Head DNA",
        description="Resolved from ExportManifest when set",
        subtype="FILE_PATH",
        default="",
    )
    faceboard_rig_name: StringProperty(name="Faceboard", default="MHC_FaceBoard")
    faceboard_json_path: StringProperty(
        name="Faceboard JSON",
        description="Bundled faceboard.json used for facial GUI controls",
        subtype="FILE_PATH",
        default="",
    )
    frame_start: IntProperty(name="Start", default=1, min=-1048574, max=1048574)
    frame_end: IntProperty(name="End", default=30, min=-1048574, max=1048574)
    clear_constraints_after_bake: BoolProperty(name="Clear Constraints After Bake", default=False)
    current_lod: IntProperty(name="LOD", default=0, min=0, max=7, update=_update_lod_visibility)
    enable_body_riglogic: BoolProperty(
        name="Body RigLogic",
        description="Evaluate OpenRigLogic body corrective joint outputs while posing",
        default=True,
    )
    show_body_corrective_bones: BoolProperty(
        name="Show Corrective Bones",
        description="Show the hidden MetaHuman body RigLogic corrective bones for debugging",
        default=False,
        update=_update_body_corrective_visibility,
    )
    enable_face_riglogic: BoolProperty(
        name="Face RigLogic",
        description="Evaluate OpenRigLogic facial outputs from the Face Controls sliders",
        default=True,
    )
    face_gui_filter: StringProperty(
        name="Filter Face Controls",
        description="Show only facial GUI sliders whose names contain this text",
        default="",
    )
    face_gui_controls: CollectionProperty(type=MHB_PG_FaceGuiControl)
    body_riglogic_last_error: StringProperty(name="Body RigLogic Error", default="")
    face_riglogic_last_error: StringProperty(name="Face RigLogic Error", default="")
    bake_last_report: StringProperty(name="Bake Report", default="")


class MHB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    openriglogic_python_path: StringProperty(
        name="OpenRigLogic Python Path",
        description="Folder containing the compiled dna and riglogic Python modules",
        subtype="DIR_PATH",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "openriglogic_python_path")
        layout.operator("mhblender.validate_setup")


class MHB_OT_ValidateSetup(bpy.types.Operator):
    bl_idname = "mhblender.validate_setup"
    bl_label = "Validate Setup"
    bl_description = "Check whether OpenRigLogic Python bindings can be imported"

    def execute(self, context):
        from ..core.faceboard_json import bundled_faceboard_json_path
        from ..riglogic.bindings import validate_bindings

        status = validate_bindings(_binding_paths_from_preferences(context))
        messages = [status.message]
        if not status.available:
            self.report({"ERROR"}, messages[0])
            return {"CANCELLED"}

        try:
            messages.append(f"Bundled faceboard: {bundled_faceboard_json_path()}")
        except Exception as exc:
            messages.append(f"Bundled faceboard missing: {exc}")
            self.report({"ERROR"}, " ".join(messages))
            return {"CANCELLED"}

        self.report({"INFO"}, " ".join(messages))
        return {"FINISHED"}


classes = (
    MHB_PG_FaceGuiControl,
    MHB_PG_Settings,
    MHB_AddonPreferences,
    MHB_OT_ValidateSetup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.metahuman_blender = PointerProperty(type=MHB_PG_Settings)


def unregister():
    if hasattr(bpy.types.Scene, "metahuman_blender"):
        del bpy.types.Scene.metahuman_blender
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
