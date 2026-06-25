from __future__ import annotations

from .scene_model import RigMap

CONSTRAINT_PREFIX = "MHBLENDER_"


def apply_control_constraints(mh_armature, control_armature, maps: list[RigMap], clear_existing: bool = True) -> int:
    import bpy

    if clear_existing:
        clear_metahuman_constraints(mh_armature)

    child_of_constraints = []
    created = 0
    for mapping in maps:
        pose_bone = mh_armature.pose.bones.get(mapping.mh_bone)
        if pose_bone is None:
            continue
        constraint = pose_bone.constraints.new(type=mapping.constraint_type)
        constraint.name = f"{CONSTRAINT_PREFIX}{mapping.control_bone}"
        constraint.target = control_armature
        constraint.subtarget = mapping.control_bone
        if hasattr(constraint, "target_space"):
            constraint.target_space = mapping.transform_space
        if hasattr(constraint, "owner_space"):
            constraint.owner_space = mapping.transform_space
        if hasattr(constraint, "mix_mode") and mapping.constraint_type == "COPY_ROTATION":
            constraint.mix_mode = "REPLACE"
        if hasattr(constraint, "influence"):
            constraint.influence = mapping.weight
        if mapping.constraint_type == "CHILD_OF":
            child_of_constraints.append((pose_bone, constraint))
        created += 1
    for pose_bone, constraint in child_of_constraints:
        set_child_of_inverse(mh_armature, pose_bone, constraint)
    return created


def clear_metahuman_constraints(mh_armature) -> int:
    removed = 0
    for pose_bone in mh_armature.pose.bones:
        for constraint in list(pose_bone.constraints):
            if constraint.name.startswith(CONSTRAINT_PREFIX):
                pose_bone.constraints.remove(constraint)
                removed += 1
    return removed


def mute_metahuman_constraints(mh_armature, mute: bool = True) -> int:
    changed = 0
    for pose_bone in mh_armature.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.name.startswith(CONSTRAINT_PREFIX):
                constraint.mute = mute
                changed += 1
    return changed


def set_child_of_inverse(mh_armature, pose_bone, constraint) -> None:
    if hasattr(constraint, "set_inverse_pending"):
        constraint.set_inverse_pending = True
        return
    _set_child_of_inverse_with_operator(mh_armature, pose_bone, constraint)


def set_child_of_inverse_on_object(empty_object, constraint) -> None:
    if hasattr(constraint, "set_inverse_pending"):
        constraint.set_inverse_pending = True
        return
    _set_child_of_inverse_on_object_with_operator(empty_object, constraint)


def _set_child_of_inverse_with_operator(mh_armature, pose_bone, constraint) -> None:
    import bpy

    previous_active = bpy.context.view_layer.objects.active
    previous_selected = list(bpy.context.selected_objects)
    previous_mode = bpy.context.object.mode if bpy.context.object else "OBJECT"
    previous_hide_viewport = mh_armature.hide_viewport
    previous_hide_select = mh_armature.hide_select

    try:
        mh_armature.hide_viewport = False
        mh_armature.hide_select = False

        if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")

        for obj in previous_selected:
            obj.select_set(False)
        mh_armature.select_set(True)
        bpy.context.view_layer.objects.active = mh_armature

        area = next((item for item in bpy.context.window.screen.areas if item.type == "VIEW_3D"), None)
        if area is None:
            raise RuntimeError("Setting Child Of inverse requires an open 3D View.")

        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        space = next((item for item in area.spaces if item.type == "VIEW_3D"), None)
        override_kwargs = {
            "area": area,
            "region": region,
            "space_data": space,
            "object": mh_armature,
            "active_object": mh_armature,
            "selected_objects": [mh_armature],
        }

        with bpy.context.temp_override(**override_kwargs):
            bpy.ops.object.mode_set(mode="POSE")
            for item in mh_armature.pose.bones:
                if hasattr(item, "select"):
                    item.select = False
            if hasattr(pose_bone, "select"):
                pose_bone.select = True
            mh_armature.data.bones.active = pose_bone.bone
            bpy.ops.constraint.childof_set_inverse(constraint=constraint.name, owner="BONE")
            bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        mh_armature.hide_viewport = previous_hide_viewport
        mh_armature.hide_select = previous_hide_select
        mh_armature.select_set(False)
        for obj in previous_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if previous_active and previous_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = previous_active
            if previous_mode != "OBJECT" and previous_active == bpy.context.view_layer.objects.active:
                try:
                    if bpy.ops.object.mode_set.poll():
                        bpy.ops.object.mode_set(mode=previous_mode)
                except Exception:
                    pass


def _set_child_of_inverse_on_object_with_operator(empty_object, constraint) -> None:
    import bpy

    previous_active = bpy.context.view_layer.objects.active
    previous_selected = list(bpy.context.selected_objects)
    try:
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        empty_object.select_set(True)
        bpy.context.view_layer.objects.active = empty_object

        area = next((item for item in bpy.context.window.screen.areas if item.type == "VIEW_3D"), None)
        if area is None:
            raise RuntimeError("Setting Child Of inverse requires an open 3D View.")
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        space = next((item for item in area.spaces if item.type == "VIEW_3D"), None)
        with bpy.context.temp_override(area=area, region=region, space_data=space, object=empty_object, active_object=empty_object):
            bpy.ops.constraint.childof_set_inverse(constraint=constraint.name, owner="OBJECT")
    finally:
        empty_object.select_set(False)
        for obj in previous_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if previous_active and previous_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = previous_active
