from __future__ import annotations

from mathutils import Vector


LIMB_CHAINS = (
    {
        "side": "l",
        "upper": "upperarm_l",
        "mid": "lowerarm_l",
        "end": "hand_l",
        "ik_target": "CTRL_hand_ik_l",
        "pole": "CTRL_arm_pole_l",
    },
    {
        "side": "r",
        "upper": "upperarm_r",
        "mid": "lowerarm_r",
        "end": "hand_r",
        "ik_target": "CTRL_hand_ik_r",
        "pole": "CTRL_arm_pole_r",
    },
    {
        "side": "l",
        "upper": "thigh_l",
        "mid": "calf_l",
        "end": "foot_l",
        "ik_target": "CTRL_foot_ik_l",
        "pole": "CTRL_leg_pole_l",
    },
    {
        "side": "r",
        "upper": "thigh_r",
        "mid": "calf_r",
        "end": "foot_r",
        "ik_target": "CTRL_foot_ik_r",
        "pole": "CTRL_leg_pole_r",
    },
)


def setup_internal_ik(control_object, mh_armature) -> int:
    import bpy

    bpy.context.view_layer.objects.active = control_object
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = control_object.data.edit_bones
    root = edit_bones.get("CTRL_root_global")
    for chain in LIMB_CHAINS:
        _ensure_pole_bone(edit_bones, mh_armature, control_object, root, chain)
    bpy.ops.object.mode_set(mode="POSE")

    created = 0
    for chain in LIMB_CHAINS:
        created += _add_limb_ik(control_object, chain)
    return created


def _ensure_pole_bone(edit_bones, mh_armature, control_object, root, chain: dict) -> None:
    mid_source = mh_armature.data.bones.get(chain["mid"])
    if mid_source is None or chain["pole"] in edit_bones:
        return
    mid_matrix = mh_armature.matrix_world @ mid_source.matrix_local
    mid_head = mid_matrix.translation
    mid_axes = mid_matrix.to_3x3()
    side_sign = -1.0 if chain["side"] == "l" else 1.0
    pole_dir = mid_axes @ Vector((1.0, 0.0, 0.0))
    if pole_dir.length <= 1e-6:
        pole_dir = mid_axes @ Vector((0.0, 0.0, 1.0))
    if pole_dir.length <= 1e-6:
        pole_dir = Vector((1.0, 0.0, 0.0))
    pole_dir.normalize()
    control_inverse = control_object.matrix_world.inverted()
    pole_head = control_inverse @ (mid_head + pole_dir * 0.25 * side_sign)
    bone = edit_bones.new(chain["pole"])
    bone.head = pole_head
    bone.tail = pole_head + (control_inverse.to_3x3() @ pole_dir) * 0.08
    bone.use_deform = False
    bone.parent = root
    bone.use_connect = False


def _add_limb_ik(control_object, chain: dict) -> int:
    mid_name = f"CTRL_{chain['mid']}"
    target_name = chain["ik_target"]
    pole_name = chain["pole"]
    mid_bone = control_object.pose.bones.get(mid_name)
    if mid_bone is None or control_object.pose.bones.get(target_name) is None:
        return 0

    for constraint in list(mid_bone.constraints):
        if constraint.name.startswith("MHBLENDER_IK_"):
            mid_bone.constraints.remove(constraint)

    ik = mid_bone.constraints.new("IK")
    ik.name = f"MHBLENDER_IK_{chain['mid']}"
    ik.target = control_object
    ik.subtarget = target_name
    ik.chain_count = 2
    ik.use_stretch = False
    pole = control_object.pose.bones.get(pole_name)
    if pole is not None:
        ik.pole_target = control_object
        ik.pole_subtarget = pole_name
        ik.pole_angle = 0.0
    return 1
