from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_EvaluateFace(bpy.types.Operator):
        bl_idname = "mhblender.evaluate_face"
        bl_label = "Evaluate Face Current Frame"
        bl_description = "Experimental single-frame RigLogic evaluation placeholder"

        def execute(self, context):
            from ..riglogic.evaluator import FaceRigLogicEvaluator

            evaluator = FaceRigLogicEvaluator.from_context(context)
            result = evaluator.evaluate_current_frame()
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
