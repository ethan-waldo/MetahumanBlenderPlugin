from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_BuildBodyRig(bpy.types.Operator):
        bl_idname = "mhblender.build_body_rig"
        bl_label = "Build Body Control Rig"
        bl_description = "Create an animator control layer and constrain the MetaHuman skeleton to it"

        def execute(self, context):
            from ..core.constraint_builder import apply_control_constraints
            from ..core.rig_mapping import infer_body_rig_map, rig_maps_to_json
            from ..rig.body_controls import create_body_control_rig
            from ..rig.ik_setup import setup_internal_ik
            from ..rig.rigify_adapter import create_rigify_body_control_rig, rigify_available, use_internal_control_rig_reason
            from ..ui.properties import get_settings

            settings = get_settings(context)
            skeleton = _find_skeleton(context, settings.deform_skeleton_name)
            if skeleton is None:
                self.report({"ERROR"}, "Select or import a MetaHuman deform skeleton first.")
                return {"CANCELLED"}

            character_name = settings.character_name or skeleton.name.removeprefix("MH_").removesuffix("_SKEL")
            collection = skeleton.users_collection[0] if skeleton.users_collection else context.collection
            _remove_previous_control_rigs(skeleton)

            use_rigify = settings.control_rig_type == "RIGIFY" and rigify_available()
            if settings.control_rig_type == "RIGIFY" and not rigify_available():
                self.report({"WARNING"}, "Rigify is not available; falling back to internal control rig.")

            if use_rigify:
                build = create_rigify_body_control_rig(skeleton, character_name, collection=collection)
                control_rig = build.control_rig
                maps = build.maps
                missing = build.missing_targets
                control_type = "Rigify (experimental)"
            else:
                control_rig = create_body_control_rig(skeleton, character_name, collection=collection)
                setup_internal_ik(control_rig, skeleton)
                report = infer_body_rig_map(skeleton, control_rig)
                maps = report.maps
                missing = report.missing_controls
                control_type = "internal"
                control_rig["mhblender_control_type"] = "internal"

            created = apply_control_constraints(skeleton, control_rig, maps)

            settings.deform_skeleton_name = skeleton.name
            settings.control_rig_name = control_rig.name
            skeleton["mhblender_rig_map"] = rig_maps_to_json(maps)
            skeleton["mhblender_control_rig"] = control_rig.name
            control_rig["mhblender_deform_skeleton"] = skeleton.name
            control_rig["mhblender_missing_controls"] = ", ".join(missing)

            message = f"Built {control_type} rig {control_rig.name}; added {created} constraints"
            if missing:
                message += f"; {len(missing)} targets were not mapped"
            if not use_rigify:
                message += f". {use_internal_control_rig_reason()}"
            self.report({"INFO"}, message)
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_BuildBodyRig]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def _find_skeleton(context, preferred_name: str):
    import bpy

    if preferred_name:
        obj = bpy.data.objects.get(preferred_name)
        if obj and obj.type == "ARMATURE":
            return obj
    active = context.view_layer.objects.active
    if active and active.type == "ARMATURE" and active.get("mhblender_role") == "deform_skeleton":
        return active
    for obj in context.selected_objects:
        if obj.type == "ARMATURE" and obj.get("mhblender_role") == "deform_skeleton":
            return obj
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE" and obj.get("mhblender_role") == "deform_skeleton":
            return obj
    return None


def _remove_previous_control_rigs(skeleton) -> None:
    import bpy

    names = set()
    stored_name = skeleton.get("mhblender_control_rig")
    if stored_name:
        names.add(stored_name)
    for obj in bpy.data.objects:
        if obj.get("mhblender_role") in {"control_rig", "rigify_metarig"} and obj.get("mhblender_deform_skeleton") == skeleton.name:
            names.add(obj.name)
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
