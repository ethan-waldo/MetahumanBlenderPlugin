from __future__ import annotations

from .joint_matrices import compute_joint_armature_matrices_blender, joint_bone_length
from .scene_model import DNAAsset, MetaHumanJoint


def create_metahuman_armature(asset: DNAAsset, collection=None):
    import bpy

    armature_data = bpy.data.armatures.new(f"MH_{asset.character_name}_SKEL_Data")
    armature_object = bpy.data.objects.new(f"MH_{asset.character_name}_SKEL", armature_data)
    (collection or bpy.context.collection).objects.link(armature_object)
    armature_object["mhblender_role"] = "deform_skeleton"
    armature_object["mhblender_dna_path"] = str(asset.path)
    armature_object["mhblender_db_name"] = asset.db_name

    _apply_dna_matrices_to_armature(armature_object, asset.joints)
    armature_object.select_set(False)
    return armature_object


def reorient_metahuman_armature(armature_object, joints: list[MetaHumanJoint]) -> int:
    """Rebuild bone matrices from DNA neutral transforms."""
    import bpy

    existing = {bone.name for bone in armature_object.data.bones}
    if not existing:
        return 0

    previous_hide_viewport = armature_object.hide_viewport
    previous_hide_select = armature_object.hide_select
    armature_object.hide_viewport = False
    armature_object.hide_select = False

    updated = _apply_dna_matrices_to_armature(armature_object, joints, existing_only=existing)

    armature_object.hide_viewport = previous_hide_viewport
    armature_object.hide_select = previous_hide_select
    return updated


def _apply_dna_matrices_to_armature(armature_object, joints: list[MetaHumanJoint], existing_only: set[str] | None = None) -> int:
    import bpy
    from mathutils import Vector

    armature_matrices = compute_joint_armature_matrices_blender(joints)
    children = _joint_children(joints)

    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature_object.data.edit_bones

    if existing_only is None:
        for joint in joints:
            if joint.name not in edit_bones:
                bone = edit_bones.new(joint.name)
                bone.use_deform = True

    for joint in joints:
        if existing_only is not None and joint.name not in existing_only:
            continue
        if joint.parent_index is None:
            continue
        bone = edit_bones.get(joint.name)
        parent_joint = joints[joint.parent_index]
        parent = edit_bones.get(parent_joint.name)
        if bone is None or parent is None:
            continue
        bone.parent = parent
        bone.use_connect = False

    updated = 0
    for joint in joints:
        if existing_only is not None and joint.name not in existing_only:
            continue
        bone = edit_bones.get(joint.name)
        if bone is None:
            continue
        matrix = armature_matrices[joint.index]
        bone.matrix = matrix
        child_index = _pick_tail_child_index(joint, children, joints, armature_matrices)
        length = joint_bone_length(joint, joints, armature_matrices, child_index)
        y_axis = matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))
        if y_axis.length <= 1e-6:
            y_axis = matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
        if y_axis.length <= 1e-6:
            y_axis = Vector((0.0, 0.0, 1.0))
        bone.tail = bone.head + y_axis.normalized() * max(length, 0.001)
        updated += 1

    bpy.ops.object.mode_set(mode="OBJECT")
    armature_object.select_set(False)
    return updated


def apply_joint_world_matrix_to_edit_bone(edit_bone, world_matrix, armature_object, bone_length: float) -> None:
    """Apply a DNA world matrix to an edit bone as a Blender armature-space rest matrix."""
    from mathutils import Vector

    armature_matrix = armature_object.matrix_world.inverted_safe() @ world_matrix
    edit_bone.matrix = armature_matrix
    y_axis = armature_matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))
    if y_axis.length > 1e-6:
        edit_bone.tail = edit_bone.head + y_axis.normalized() * max(bone_length, 0.001)


def apply_dna_orientation_to_edit_bone(edit_bone, head, tail, world_rotation_3x3, default_length: float = 0.05) -> None:
    """Legacy helper; prefer matrix assignment via _apply_dna_matrices_to_armature."""
    from mathutils import Matrix, Vector

    from ..rig.control_orientation import edit_bone_from_armature_matrix

    matrix = Matrix.Translation(Vector(head))
    matrix[0][0:3] = world_rotation_3x3[0]
    matrix[1][0:3] = world_rotation_3x3[1]
    matrix[2][0:3] = world_rotation_3x3[2]
    tail_vector = Vector(tail) - Vector(head)
    length = tail_vector.length if tail_vector.length > 0.001 else default_length
    edit_bone_from_armature_matrix(edit_bone, matrix, length)


def compute_joint_world_positions(joints: list[MetaHumanJoint]) -> dict[int, tuple[float, float, float]]:
    world_matrices = compute_joint_armature_matrices_blender(joints)
    return {index: tuple(matrix.translation) for index, matrix in world_matrices.items()}


def compute_joint_world_rotations(joints: list[MetaHumanJoint]) -> dict[int, object]:
    world_matrices = compute_joint_armature_matrices_blender(joints)
    return {index: matrix.to_3x3() for index, matrix in world_matrices.items()}


def _joint_children(joints: list[MetaHumanJoint]) -> dict[int, list[int]]:
    from collections import defaultdict

    children: dict[int, list[int]] = defaultdict(list)
    for joint in joints:
        if joint.parent_index is not None:
            children[joint.parent_index].append(joint.index)
    return children


def _pick_tail_child_index(joint, children, joints, world_matrices):
    from ..rig.control_orientation import pick_primary_child_index

    world_positions = {index: tuple(matrix.translation) for index, matrix in world_matrices.items()}
    return pick_primary_child_index(joint.name, joint.index, children, joints, world_positions)


def hide_deform_skeleton_display(armature_object) -> None:
    """Keep deformation active but hide the MetaHuman deform armature in the viewport."""
    armature_object.hide_viewport = True
    armature_object.hide_select = True
    armature_object.show_in_front = False

    armature_data = armature_object.data
    armature_data.display_type = "WIRE"
    for bone in armature_data.bones:
        bone.hide = True
        bone.hide_select = True

    if hasattr(armature_data, "collections"):
        for collection in armature_data.collections:
            collection.is_visible = False
