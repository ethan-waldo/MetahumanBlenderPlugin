from __future__ import annotations

from collections import defaultdict
from math import radians

from .coordinate_system import dna_location_to_blender
from .scene_model import DNAAsset, MetaHumanJoint


def create_metahuman_armature(asset: DNAAsset, collection=None):
    import bpy
    from mathutils import Vector

    armature_data = bpy.data.armatures.new(f"MH_{asset.character_name}_SKEL_Data")
    armature_object = bpy.data.objects.new(f"MH_{asset.character_name}_SKEL", armature_data)
    (collection or bpy.context.collection).objects.link(armature_object)
    armature_object["mhblender_role"] = "deform_skeleton"
    armature_object["mhblender_dna_path"] = str(asset.path)
    armature_object["mhblender_db_name"] = asset.db_name

    world_positions = compute_joint_world_positions(asset.joints)
    children = defaultdict(list)
    for joint in asset.joints:
        if joint.parent_index is not None:
            children[joint.parent_index].append(joint.index)

    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = armature_data.edit_bones
    for joint in asset.joints:
        bone = edit_bones.new(joint.name)
        head = Vector(world_positions[joint.index])
        child_indices = children.get(joint.index, [])
        if child_indices:
            tail = Vector(world_positions[child_indices[0]])
            if (tail - head).length < 0.001:
                tail = head + Vector((0.0, 0.0, 0.05))
        else:
            tail = head + Vector((0.0, 0.0, 0.05))
        bone.head = head
        bone.tail = tail
        bone.roll = 0.0
        bone.use_deform = True

    for joint in asset.joints:
        if joint.parent_index is None:
            continue
        bone = edit_bones.get(joint.name)
        parent = edit_bones.get(asset.joints[joint.parent_index].name)
        if bone and parent:
            bone.parent = parent
            bone.use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    armature_object.select_set(False)
    return armature_object


def compute_joint_world_positions(joints: list[MetaHumanJoint]) -> dict[int, tuple[float, float, float]]:
    from mathutils import Euler, Matrix, Vector

    matrices = {}
    positions: dict[int, tuple[float, float, float]] = {}
    for joint in joints:
        translation = Matrix.Translation(Vector(joint.neutral_translation))
        rotation = Euler(tuple(radians(value) for value in joint.neutral_rotation), "XYZ").to_matrix().to_4x4()
        local_matrix = translation @ rotation
        if joint.parent_index is None or joint.parent_index not in matrices:
            world_matrix = local_matrix
        else:
            world_matrix = matrices[joint.parent_index] @ local_matrix
        matrices[joint.index] = world_matrix
        positions[joint.index] = dna_location_to_blender(tuple(world_matrix.translation))
    return positions
