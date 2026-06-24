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
            from ..core.bake_validation import count_pose_keyframes, validate_bake_ready
            from ..core.scene_model import BakeSettings
            from ..ui.properties import get_settings
            from .build_body_rig import _find_skeleton

            settings = get_settings(context)
            skeleton = _find_skeleton(context, settings.deform_skeleton_name)
            validation = validate_bake_ready(context, skeleton, settings)
            if not validation.ok:
                self.report({"ERROR"}, validation.message)
                return {"CANCELLED"}

            bake_to_metahuman_skeleton(
                skeleton,
                BakeSettings(
                    frame_start=settings.frame_start,
                    frame_end=settings.frame_end,
                    clear_constraints_after_bake=settings.clear_constraints_after_bake,
                ),
            )
            keyframes = count_pose_keyframes(skeleton, settings.frame_start, settings.frame_end)
            report = (
                f"Baked frames {settings.frame_start}-{settings.frame_end} to {skeleton.name}; "
                f"{validation.constraint_count} constraints processed; {keyframes} keyed pose channels."
            )
            settings.bake_last_report = report
            self.report({"INFO"}, report)
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_BakeToMetaHuman]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
