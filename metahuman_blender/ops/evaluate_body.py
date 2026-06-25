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

    class MHB_OT_ValidateBodyRig(bpy.types.Operator):
        bl_idname = "mhblender.validate_body_rig"
        bl_label = "Validate Body Rig"
        bl_description = "Check deform skeleton rest pose and RigLogic raw control identity at rest"

        def execute(self, context):
            from ..core.joint_matrices import compute_joint_armature_matrices_blender
            from ..core.character_import import resolve_character_paths
            from ..core.dna_loader import load_dna
            from ..riglogic.body_evaluator import _pose_delta_quaternion
            from ..ui.properties import _binding_paths_from_preferences, get_settings

            settings = get_settings(context)
            skeleton_name = settings.deform_skeleton_name
            skeleton = context.scene.objects.get(skeleton_name) if skeleton_name else None
            if skeleton is None:
                skeleton = next(
                    (obj for obj in bpy.data.objects if obj.get("mhblender_role") == "deform_skeleton"),
                    None,
                )
            if skeleton is None:
                self.report({"ERROR"}, "No MetaHuman deform skeleton found.")
                return {"CANCELLED"}

            paths = resolve_character_paths(settings, skeleton)
            dna_path = paths.get("body_dna_path") or skeleton.get("mhblender_dna_path")
            if not dna_path:
                self.report({"ERROR"}, "No body DNA path found for validation.")
                return {"CANCELLED"}

            asset = load_dna(dna_path, _binding_paths_from_preferences(context))
            expected = compute_joint_armature_matrices_blender(asset.joints)
            max_matrix_error = 0.0
            worst_bone = ""
            checked = 0
            for joint in asset.joints:
                bone = skeleton.data.bones.get(joint.name)
                if bone is None:
                    continue
                diff = max(
                    abs(float(bone.matrix_local[i][j]) - float(expected[joint.index][i][j]))
                    for i in range(4)
                    for j in range(4)
                )
                checked += 1
                if diff > max_matrix_error:
                    max_matrix_error = diff
                    worst_bone = joint.name

            max_quat_error = 0.0
            quat_checked = 0
            for pose_bone in skeleton.pose.bones:
                if pose_bone.name.startswith("facial_"):
                    continue
                quat = _pose_delta_quaternion(skeleton, pose_bone)
                error = max(abs(quat.w - 1.0), abs(quat.x), abs(quat.y), abs(quat.z))
                if error > max_quat_error:
                    max_quat_error = error
                quat_checked += 1

            message = (
                f"Validated {checked} DNA bones (max matrix error {max_matrix_error:.6f} on {worst_bone}); "
                f"{quat_checked} pose deltas (max quat error {max_quat_error:.6f})"
            )
            ok = max_matrix_error < 0.01 and max_quat_error < 0.01
            self.report({"INFO"} if ok else {"WARNING"}, message)
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_EvaluateBodyRigLogic, MHB_OT_ValidateBodyRig]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
