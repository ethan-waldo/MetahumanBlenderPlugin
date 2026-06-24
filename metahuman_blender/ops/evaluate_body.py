from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_EvaluateBodyRigLogic(bpy.types.Operator):
        bl_idname = "mhblender.evaluate_body_riglogic"
        bl_label = "Evaluate Body RigLogic"
        bl_description = "Apply body RigLogic corrective joint outputs for the current pose"

        def execute(self, context):
            from ..riglogic.body_evaluator import evaluate_body_for_context
            from ..ui.properties import get_settings

            settings = get_settings(context)
            try:
                result = evaluate_body_for_context(context)
            except Exception as exc:
                settings.body_riglogic_last_error = str(exc)
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}
            settings.body_riglogic_last_error = "" if result.ok else result.message
            self.report({"INFO"} if result.ok else {"ERROR"}, result.message)
            return {"FINISHED"} if result.ok else {"CANCELLED"}

    global classes
    classes = [MHB_OT_EvaluateBodyRigLogic]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
