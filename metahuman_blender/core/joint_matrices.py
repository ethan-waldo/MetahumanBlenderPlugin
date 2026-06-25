from __future__ import annotations

from collections import defaultdict
from math import radians

from .coordinate_system import dna_space_matrix_to_blender
from .scene_model import MetaHumanJoint


def _joint_children(joints: list[MetaHumanJoint]) -> dict[int, list[int]]:
    children: dict[int, list[int]] = defaultdict(list)
    for joint in joints:
        if joint.parent_index is not None:
            children[joint.parent_index].append(joint.index)
    return children


def compute_joint_parent_matrices_dna(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """Parent-space neutral transforms: T(neutral_translation) @ R(Euler XYZ degrees)."""
    from mathutils import Euler, Matrix, Vector

    local: dict[int, Matrix] = {}
    for joint in joints:
        translation = Matrix.Translation(Vector(joint.neutral_translation))
        rotation = Euler(tuple(radians(value) for value in joint.neutral_rotation), "XYZ").to_matrix().to_4x4()
        local[joint.index] = translation @ rotation
    return local


def compute_joint_local_matrices_dna(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """Backward-compatible alias for DNA parent-space neutral transforms."""
    return compute_joint_parent_matrices_dna(joints)


def compute_joint_world_matrices_dna(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """World neutral transforms in DNA space."""
    from mathutils import Matrix

    local = compute_joint_parent_matrices_dna(joints)
    world: dict[int, Matrix] = {}
    for joint in joints:
        if joint.parent_index is None or joint.parent_index not in world:
            world[joint.index] = local[joint.index].copy()
        else:
            world[joint.index] = world[joint.parent_index] @ local[joint.index]
    return world


def compute_joint_armature_matrices_blender(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """Blender armature-space rest matrices suitable for Bone.matrix_local."""
    return {
        index: dna_space_matrix_to_blender(matrix)
        for index, matrix in compute_joint_world_matrices_dna(joints).items()
    }


def compute_joint_world_matrices(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """World neutral transforms converted to Blender space."""
    return compute_joint_armature_matrices_blender(joints)


def compute_joint_parent_matrices_blender(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """Parent-space neutral transforms after converting DNA world matrices to Blender space."""
    from mathutils import Matrix

    world = compute_joint_armature_matrices_blender(joints)
    local: dict[int, Matrix] = {}
    for joint in joints:
        if joint.parent_index is None or joint.parent_index not in world:
            local[joint.index] = world[joint.index].copy()
        else:
            parent_world = world[joint.parent_index]
            local[joint.index] = parent_world.inverted_safe() @ world[joint.index]
    return local


def compute_joint_local_matrices_blender(joints: list[MetaHumanJoint]) -> dict[int, object]:
    """Backward-compatible alias for Blender parent-space neutral transforms."""
    return compute_joint_parent_matrices_blender(joints)


def joint_bone_length(
    joint: MetaHumanJoint,
    joints: list[MetaHumanJoint],
    world_matrices: dict[int, object],
    child_index: int | None,
    *,
    default_length: float = 0.05,
) -> float:
    from mathutils import Vector

    if child_index is None:
        return default_length
    head = world_matrices[joint.index].translation
    tail = world_matrices[child_index].translation
    length = (Vector(tail) - Vector(head)).length
    return length if length > 0.001 else default_length
