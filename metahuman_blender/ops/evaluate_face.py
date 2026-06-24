from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_EvaluateFace(bpy.types.Operator):
        bl_idname = "mhblender.evaluate_face"
        bl_label = "Evaluate Face RigLogic"
        bl_description = "Evaluate facial RigLogic from the Face Controls sliders for the current frame"

        def execute(self, context):
            from ..riglogic.evaluator import evaluate_face_for_context

            result = evaluate_face_for_context(context)
            settings = context.scene.metahuman_blender
            settings.face_riglogic_last_error = "" if result.ok else result.message
            level = {"INFO"} if result.ok else {"ERROR"}
            self.report(level, result.message)
            return {"FINISHED"} if result.ok else {"CANCELLED"}

    global classes
    classes = [MHB_OT_EvaluateFace]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
