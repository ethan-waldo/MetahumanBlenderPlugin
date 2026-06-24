from __future__ import annotations

from mathutils import Vector

from ..core.rig_mapping import control_name_for_bone, is_body_bone
from .body_constants import MAIN_BODY_CONTROLS
from .bone_shapes import assign_rigify_style_shapes


def create_body_control_rig(mh_armature, character_name: str | None = None, collection=None):
    import bpy

    character = character_name or mh_armature.name.removeprefix("MH_").removesuffix("_SKEL")
    armature_data = bpy.data.armatures.new(f"CTRL_{character}_RIG_Data")
    control_object = bpy.data.objects.new(f"CTRL_{character}_RIG", armature_data)
    (collection or bpy.context.collection).objects.link(control_object)
    control_object.show_in_front = True
    control_object["mhblender_role"] = "control_rig"
    control_object["mhblender_deform_skeleton"] = mh_armature.name

    bpy.context.view_layer.objects.active = control_object
    control_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = armature_data.edit_bones
    root = _create_control_bone(edit_bones, "CTRL_root_global", Vector((0.0, 0.0, 0.0)), size=0.35)
    root.use_deform = False

    control_by_source: dict[str, str] = {}
    for source_bone in mh_armature.data.bones:
        if not is_body_bone(source_bone.name):
            continue
        control_name = control_name_for_bone(source_bone.name)
        bone = _create_control_bone_from_source(edit_bones, control_name, source_bone, mh_armature)
        bone.use_deform = False
        bone.parent = root
        bone.use_connect = False
        control_by_source[source_bone.name] = control_name

    _add_ik_target_pair(edit_bones, mh_armature, root, "hand_l", "CTRL_hand_ik_l")
    _add_ik_target_pair(edit_bones, mh_armature, root, "hand_r", "CTRL_hand_ik_r")
    _add_ik_target_pair(edit_bones, mh_armature, root, "foot_l", "CTRL_foot_ik_l")
    _add_ik_target_pair(edit_bones, mh_armature, root, "foot_r", "CTRL_foot_ik_r")

    bpy.ops.object.mode_set(mode="OBJECT")
    control_object.select_set(False)
    _apply_control_display(control_object)
    assign_rigify_style_shapes(control_object, visible_bones=MAIN_BODY_CONTROLS)
    return control_object


def _create_control_bone_from_source(edit_bones, name: str, source_bone, mh_armature):
    matrix = mh_armature.matrix_world @ source_bone.matrix_local
    head = matrix.translation
    y_axis = matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))
    length = max(source_bone.length, (mh_armature.matrix_world @ source_bone.tail_local - head).length, 0.05)
    if y_axis.length <= 1e-6:
        y_axis = Vector((0.0, 0.0, 1.0))
    else:
        y_axis.normalize()
    tail = head + y_axis * length
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    z_axis = matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
    if z_axis.length > 1e-6:
        bone.align_roll(z_axis)
    return bone


def _create_control_bone(edit_bones, name: str, head: Vector, size: float):
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = head + Vector((0.0, 0.0, max(size * 0.35, 0.04)))
    bone.roll = 0.0
    return bone


def _add_ik_target_pair(edit_bones, mh_armature, parent, source_name: str, control_name: str) -> None:
    source = mh_armature.data.bones.get(source_name)
    if source is None:
        return
    bone = _create_control_bone_from_source(edit_bones, control_name, source, mh_armature)
    bone.use_deform = False
    bone.parent = parent
    bone.use_connect = False


def _apply_control_display(control_object) -> None:
    for bone in control_object.data.bones:
        visible = bone.name in MAIN_BODY_CONTROLS
        bone.hide = not visible
        bone.hide_select = not visible
    for pose_bone in control_object.pose.bones:
        if pose_bone.name in MAIN_BODY_CONTROLS:
            pose_bone.color.palette = "THEME09"
        pose_bone.lock_scale[0] = False
        pose_bone.lock_scale[1] = False
        pose_bone.lock_scale[2] = False
    control_object.data.display_type = "OCTAHEDRAL"
    control_object.display_type = "WIRE"
