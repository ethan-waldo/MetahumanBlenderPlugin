from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_OT_BuildBodyRig(bpy.types.Operator):
        bl_idname = "mhblender.build_body_rig"
        bl_label = "Build Body Control Rig"
        bl_description = "Create a Rigify body control rig fitted to the MetaHuman skeleton (face uses Face Controls panel)"

        def execute(self, context):
            from ..core.rig_mapping import rig_maps_to_json
            from ..rig.rigify_adapter import create_rigify_body_control_rig, rigify_available
            from ..rig.rigify_binding import apply_rigify_empty_bindings
            from ..ui.properties import get_settings

            settings = get_settings(context)
            skeleton = _find_skeleton(context, settings.deform_skeleton_name)
            if skeleton is None:
                self.report({"ERROR"}, "Select or import a MetaHuman deform skeleton first.")
                return {"CANCELLED"}

            if not rigify_available():
                self.report(
                    {"ERROR"},
                    "Rigify is required. Enable the Rigify add-on in Preferences > Add-ons.",
                )
                return {"CANCELLED"}

            character_name = settings.character_name or skeleton.name.removeprefix("MH_").removesuffix("_SKEL")
            collection = skeleton.users_collection[0] if skeleton.users_collection else context.collection
            _reorient_skeleton_from_dna(context, skeleton)
            _remove_previous_control_rigs(skeleton, character_name)

            try:
                result = create_rigify_body_control_rig(skeleton, character_name, collection=collection)
            except Exception as exc:
                self.report({"ERROR"}, f"Rigify body rig build failed: {exc}")
                return {"CANCELLED"}

            control_rig = result.control_rig
            maps = result.maps
            missing = result.missing_targets
            created = apply_rigify_empty_bindings(
                skeleton,
                control_rig,
                maps,
                character_name,
                collection=collection,
            )

            settings.deform_skeleton_name = skeleton.name
            settings.control_rig_name = control_rig.name
            skeleton["mhblender_rig_map"] = rig_maps_to_json(maps)
            skeleton["mhblender_control_rig"] = control_rig.name
            control_rig["mhblender_deform_skeleton"] = skeleton.name
            control_rig["mhblender_missing_controls"] = ", ".join(missing)
            control_rig["mhblender_constraint_count"] = created
            control_rig["mhblender_binding_mode"] = "rigify_output_empty"

            _refresh_body_riglogic(context, skeleton)
            _finalize_animation_setup(context, skeleton, control_rig)

            message = f"Built Rigify body rig {control_rig.name}; bound {created} Rigify output bones via empties"
            if missing:
                message += f"; {len(missing)} Rigify output mappings missing"
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


def _reorient_skeleton_from_dna(context, skeleton) -> None:
    from ..core.character_import import resolve_character_paths
    from ..core.dna_loader import load_dna
    from ..core.skeleton_builder import reorient_metahuman_armature
    from ..ui.properties import _binding_paths_from_preferences

    settings = context.scene.metahuman_blender
    paths = resolve_character_paths(settings, skeleton)
    dna_path = paths.get("body_dna_path") or skeleton.get("mhblender_dna_path")
    if not dna_path:
        return

    asset = load_dna(dna_path, _binding_paths_from_preferences(context))
    reorient_metahuman_armature(skeleton, asset.joints)


def _remove_previous_control_rigs(skeleton, character_name: str) -> None:
    import bpy

    from ..core.constraint_builder import clear_metahuman_constraints
    from ..rig.rigify_binding import remove_rigify_empty_bindings

    clear_metahuman_constraints(skeleton)
    remove_rigify_empty_bindings(character_name)

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


def _finalize_animation_setup(context, skeleton, control_rig) -> None:
    import bpy
    from ..rig.rigify_adapter import apply_hand_curl_settings
    from ..riglogic.body_evaluator import set_body_corrective_bone_visibility

    skeleton.hide_viewport = True
    skeleton.hide_select = True
    control_rig.hide_viewport = False
    control_rig.hide_select = False
    control_rig.show_in_front = True
    apply_hand_curl_settings(context)
    if getattr(context.scene.metahuman_blender, "show_body_corrective_bones", False):
        set_body_corrective_bone_visibility(context, True)

    for obj in context.view_layer.objects:
        obj.select_set(False)
    control_rig.select_set(True)
    context.view_layer.objects.active = control_rig
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="POSE")


def _refresh_body_riglogic(context, skeleton) -> None:
    from ..riglogic.body_evaluator import clear_cache, evaluate_body_for_context

    settings = context.scene.metahuman_blender
    clear_cache()
    settings.body_riglogic_last_error = ""
    if not getattr(settings, "enable_body_riglogic", False):
        return
    try:
        result = evaluate_body_for_context(context)
        settings.body_riglogic_last_error = "" if result.ok else result.message
    except Exception as exc:
        settings.body_riglogic_last_error = f"Body RigLogic evaluation failed: {exc}"
