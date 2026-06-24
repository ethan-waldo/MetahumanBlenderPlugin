from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_BakeToMetaHuman(bpy.types.Operator):
        bl_idname = "mhblender.bake_to_metahuman"
        bl_label = "Bake To MetaHuman Skeleton"
        bl_description = "Bake constrained control-rig animation back onto the original MetaHuman skeleton"

        def execute(self, context):
            from ..core.bake import bake_to_metahuman_skeleton
            from ..core.scene_model import BakeSettings
            from ..ui.properties import get_settings
            from .build_body_rig import _find_skeleton

            settings = get_settings(context)
            skeleton = _find_skeleton(context, settings.deform_skeleton_name)
            if skeleton is None:
                self.report({"ERROR"}, "No MetaHuman deform skeleton found.")
                return {"CANCELLED"}
            if settings.frame_end < settings.frame_start:
                self.report({"ERROR"}, "Bake end frame must be greater than or equal to start frame.")
                return {"CANCELLED"}

            bake_to_metahuman_skeleton(
                skeleton,
                BakeSettings(
                    frame_start=settings.frame_start,
                    frame_end=settings.frame_end,
                    clear_constraints_after_bake=settings.clear_constraints_after_bake,
                ),
            )
            self.report({"INFO"}, f"Baked frames {settings.frame_start}-{settings.frame_end} to {skeleton.name}")
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_BakeToMetaHuman]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
