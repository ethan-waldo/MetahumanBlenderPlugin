ADDON_ID = "metahuman_blender"

classes = []


def _binding_paths_from_preferences(context) -> list[str]:
    prefs = get_addon_preferences(context)
    if prefs and prefs.openriglogic_python_path:
        return [prefs.openriglogic_python_path]
    return []


def get_addon_preferences(context):
    addon = context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None


def get_settings(context):
    return context.scene.metahuman_blender


def _update_lod_visibility(self, context):
    from ..core.lod import set_lod_visibility

    set_lod_visibility(self.character_name, self.current_lod)


def register():
    import bpy
    from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty

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

    class MHB_PG_Settings(bpy.types.PropertyGroup):
        dna_path: StringProperty(name="DNA File", subtype="FILE_PATH", default="")
        character_name: StringProperty(name="Character", default="")
        deform_skeleton_name: StringProperty(name="Deform Skeleton", default="")
        control_rig_name: StringProperty(name="Control Rig", default="")
        frame_start: IntProperty(name="Start", default=1, min=-1048574, max=1048574)
        frame_end: IntProperty(name="End", default=30, min=-1048574, max=1048574)
        clear_constraints_after_bake: BoolProperty(name="Clear Constraints After Bake", default=False)
        current_lod: IntProperty(name="LOD", default=0, min=0, max=7, update=_update_lod_visibility)
        enable_body_riglogic: BoolProperty(
            name="Body RigLogic",
            description="Evaluate OpenRigLogic body corrective joint outputs while posing",
            default=False,
        )

    class MHB_OT_ValidateSetup(bpy.types.Operator):
        bl_idname = "mhblender.validate_setup"
        bl_label = "Validate Setup"
        bl_description = "Check whether OpenRigLogic Python bindings can be imported"

        def execute(self, context):
            from ..riglogic.bindings import validate_bindings

            status = validate_bindings(_binding_paths_from_preferences(context))
            level = {"INFO"} if status.available else {"ERROR"}
            self.report(level, status.message)
            return {"FINISHED"} if status.available else {"CANCELLED"}

    global classes
    classes = [MHB_AddonPreferences, MHB_PG_Settings, MHB_OT_ValidateSetup]
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.metahuman_blender = PointerProperty(type=MHB_PG_Settings)


def unregister():
    import bpy

    if hasattr(bpy.types.Scene, "metahuman_blender"):
        del bpy.types.Scene.metahuman_blender
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    from ..riglogic.body_evaluator import unregister_handlers, clear_cache

    unregister_handlers()
    clear_cache()
