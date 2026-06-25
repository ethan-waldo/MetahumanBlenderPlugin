from __future__ import annotations

from mathutils import Matrix, Vector

# Preferred child joint for orienting a MetaHuman body bone along its anatomical chain.
MH_PRIMARY_CHILD: dict[str, str] = {
    "pelvis": "spine_01",
    "spine_01": "spine_02",
    "spine_02": "spine_03",
    "spine_03": "spine_04",
    "spine_04": "spine_05",
    "spine_05": "neck_01",
    "neck_01": "neck_02",
    "neck_02": "head",
    "clavicle_l": "upperarm_l",
    "upperarm_l": "lowerarm_l",
    "lowerarm_l": "hand_l",
    "clavicle_r": "upperarm_r",
    "upperarm_r": "lowerarm_r",
    "lowerarm_r": "hand_r",
    "thigh_l": "calf_l",
    "calf_l": "foot_l",
    "foot_l": "ball_l",
    "thigh_r": "calf_r",
    "calf_r": "foot_r",
    "foot_r": "ball_r",
}

_HELPER_BONE_TOKENS = (
    "corrective",
    "twist",
    "scap",
    "out_",
    "_drv",
    "driver",
    "helper",
    "socket",
    "offset",
)


def is_helper_bone(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in _HELPER_BONE_TOKENS)


def mh_orientation_reference_bone(mh_armature, mh_bone_name: str) -> str:
    """Return the MetaHuman bone whose rest orientation should drive Rigify fitting."""
    if mh_armature is None or not mh_bone_name:
        return mh_bone_name

    if "_" in mh_bone_name:
        prefix, side = mh_bone_name.rsplit("_", 1)
        if side in {"l", "r"}:
            corrective_name = f"{prefix}_correctiveRoot_{side}"
            if mh_armature.data.bones.get(corrective_name) is not None:
                return corrective_name

    return mh_bone_name


def align_metarig_roll_from_mh(
    edit_bone,
    mh_armature,
    mh_bone_name: str,
    metarig,
    *,
    meta_bone_name: str,
) -> bool:
    """Match metarig roll to the DNA skeleton bone's rest Z axis."""
    del meta_bone_name
    source = mh_armature.data.bones.get(mh_bone_name)
    if source is None:
        return False

    chain = edit_bone.tail - edit_bone.head
    if chain.length <= 1e-6:
        return False

    mh_matrix = mh_armature.matrix_world @ source.matrix_local
    roll_world = mh_matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
    y_axis = chain.normalized()
    roll_world -= y_axis * y_axis.dot(roll_world)
    if roll_world.length <= 1e-6:
        return False

    roll_axis = metarig.matrix_world.inverted_safe().to_3x3() @ roll_world
    edit_bone.align_roll(roll_axis)
    return True


def fit_metarig_bone_from_mh(
    edit_bone,
    mh_armature,
    mh_bone_name: str,
    tail_world,
    metarig,
    *,
    meta_bone_name: str,
) -> bool:
    """Position a metarig edit bone on the MetaHuman joint chain."""
    source = mh_armature.data.bones.get(mh_bone_name)
    if source is None:
        return False

    head_world = mh_armature.matrix_world @ source.head_local
    if tail_world is None:
        tail_world = mh_armature.matrix_world @ source.tail_local
    if (tail_world - head_world).length <= 1e-6:
        return False

    inverse = metarig.matrix_world.inverted_safe()
    edit_bone.head = inverse @ head_world
    edit_bone.tail = inverse @ tail_world
    return align_metarig_roll_from_mh(
        edit_bone,
        mh_armature,
        mh_bone_name,
        metarig,
        meta_bone_name=meta_bone_name,
    )


def mh_bone_head_world(mh_armature, bone_name: str | None) -> Vector | None:
    if not bone_name:
        return None
    bone = mh_armature.data.bones.get(bone_name)
    if bone is None:
        return None
    return mh_armature.matrix_world @ bone.head_local


def mh_chain_end_world(mh_armature, bone_name: str, *, fallback_length: float = 0.08) -> tuple[Vector, Vector]:
    """Return world-space head/tail for a control bone aligned to the anatomical chain."""
    head = mh_bone_head_world(mh_armature, bone_name)
    if head is None:
        return Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, fallback_length))

    child_name = MH_PRIMARY_CHILD.get(bone_name)
    tail = mh_bone_head_world(mh_armature, child_name) if child_name else None
    if tail is None:
        source = mh_armature.data.bones.get(bone_name)
        if source is not None:
            tail = mh_armature.matrix_world @ source.tail_local
    if tail is None or (tail - head).length < 0.01:
        tail = head + Vector((0.0, 0.0, fallback_length))
    return head, tail


def world_points_to_edit_bone(edit_bone, armature_object, head_world: Vector, tail_world: Vector) -> None:
    inverse = armature_object.matrix_world.inverted()
    edit_bone.head = inverse @ head_world
    edit_bone.tail = inverse @ tail_world
    align_control_bone_roll(edit_bone)


def edit_bone_from_armature_matrix(edit_bone, armature_local_matrix, bone_length: float) -> None:
    """Set edit bone head/tail/roll from an armature-local 4x4 matrix."""
    head = armature_local_matrix.translation
    y_axis = armature_local_matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))
    if y_axis.length <= 1e-6:
        y_axis = armature_local_matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
    if y_axis.length <= 1e-6:
        y_axis = Vector((0.0, 0.0, 1.0))
    y_axis.normalize()
    length = max(float(bone_length), 0.001)
    edit_bone.head = head
    edit_bone.tail = head + y_axis * length
    z_axis = armature_local_matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
    if z_axis.length > 1e-6:
        edit_bone.align_roll(z_axis)


def copy_mh_bone_to_edit_bone(edit_bone, mh_armature, source_bone_name: str, control_armature) -> bool:
    """Match a control/metarig bone rest pose to a MetaHuman deform bone."""
    source = mh_armature.data.bones.get(source_bone_name)
    if source is None:
        return False
    rest_world = mh_armature.matrix_world @ source.matrix_local
    armature_space = control_armature.matrix_world.inverted_safe() @ rest_world
    if edit_bone.parent is not None:
        edit_bone.matrix = edit_bone.parent.matrix.inverted_safe() @ armature_space
    else:
        edit_bone.matrix = armature_space
    length = (source.tail_local - source.head_local).length
    if (edit_bone.tail - edit_bone.head).length < 0.001 and length > 1e-6:
        direction = edit_bone.matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))
        if direction.length > 1e-6:
            edit_bone.tail = edit_bone.head + direction.normalized() * length
    return True


def align_control_bone_roll(edit_bone) -> None:
    """Give controls a stable roll independent of vertical MetaHuman deform bones."""
    direction = edit_bone.tail - edit_bone.head
    if direction.length <= 1e-6:
        edit_bone.roll = 0.0
        return
    y_axis = direction.normalized()
    reference = Vector((0.0, 1.0, 0.0))
    if abs(y_axis.dot(reference)) > 0.95:
        reference = Vector((1.0, 0.0, 0.0))
    edit_bone.align_roll(reference)


def pick_primary_child_index(joint_name: str, joint_index: int, children, joints, world_positions) -> int | None:
    child_indices = children.get(joint_index, [])
    if not child_indices:
        return None

    preferred_name = MH_PRIMARY_CHILD.get(joint_name)
    if preferred_name:
        for child_index in child_indices:
            if joints[child_index].name == preferred_name:
                return child_index

    best_index = None
    best_distance = 0.0
    head = Vector(world_positions[joint_index])
    for child_index in child_indices:
        child_name = joints[child_index].name
        if is_helper_bone(child_name):
            continue
        distance = (Vector(world_positions[child_index]) - head).length
        if distance > best_distance:
            best_distance = distance
            best_index = child_index

    if best_index is not None:
        return best_index

    for child_index in child_indices:
        distance = (Vector(world_positions[child_index]) - head).length
        if distance > best_distance:
            best_distance = distance
            best_index = child_index
    return best_index
