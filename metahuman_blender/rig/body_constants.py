from __future__ import annotations

FACE_CONTROL_TOKENS = (
    "brow",
    "cheek",
    "chin",
    "ear",
    "eye",
    "forehead",
    "jaw",
    "lid",
    "lip",
    "lips",
    "nose",
    "teeth",
    "tongue",
    "temple",
)

# Visible animator controls on the internal body rig.
MAIN_BODY_CONTROLS = {
    "CTRL_root_global",
    "CTRL_pelvis",
    "CTRL_spine_01",
    "CTRL_spine_02",
    "CTRL_spine_03",
    "CTRL_spine_04",
    "CTRL_spine_05",
    "CTRL_neck_01",
    "CTRL_neck_02",
    "CTRL_clavicle_l",
    "CTRL_upperarm_l",
    "CTRL_lowerarm_l",
    "CTRL_hand_l",
    "CTRL_clavicle_r",
    "CTRL_upperarm_r",
    "CTRL_lowerarm_r",
    "CTRL_hand_r",
    "CTRL_thigh_l",
    "CTRL_calf_l",
    "CTRL_foot_l",
    "CTRL_thigh_r",
    "CTRL_calf_r",
    "CTRL_foot_r",
    "CTRL_hand_ik_l",
    "CTRL_hand_ik_r",
    "CTRL_foot_ik_l",
    "CTRL_foot_ik_r",
    "CTRL_arm_pole_l",
    "CTRL_arm_pole_r",
    "CTRL_leg_pole_l",
    "CTRL_leg_pole_r",
}

# Rigify widget prefixes kept visible on the generated body rig.
# Face/head animation is handled by the Face Controls panel instead.
RIGIFY_BODY_CONTROL_PREFIXES = (
    "root",
    "torso",
    "hips",
    "chest",
    "spine_fk",
    "tweak_spine",
    "thigh_ik",
    "thigh_fk",
    "thigh_tweak",
    "thigh_parent",
    "shin_fk",
    "foot_ik",
    "foot_fk",
    "foot_tweak",
    "foot_heel",
    "foot_spin",
    "toe_fk",
    "hand_ik",
    "hand_fk",
    "upper_arm_fk",
    "forearm_fk",
    "upper_arm_ik",
    "forearm_ik",
    "upper_arm_tweak",
    "forearm_tweak",
    "shoulder",
    "VIS_upper_arm_ik_pole",
    "VIS_thigh_ik_pole",
    "palm",
    "f_index",
    "f_middle",
    "f_ring",
    "f_pinky",
    "thumb",
)

RIGIFY_EXCLUDED_CONTROLS = {
    "head",
    "neck",
    "eyes",
    "breast.L",
    "breast.R",
}


def is_rigify_body_animator_bone(bone_name: str) -> bool:
    if bone_name.startswith(("DEF-", "ORG-", "MCH-", "WGT-")):
        return False
    if bone_name in RIGIFY_EXCLUDED_CONTROLS:
        return False
    lowered = bone_name.lower()
    if any(token in lowered for token in FACE_CONTROL_TOKENS):
        return False
    return any(
        bone_name == prefix or bone_name.startswith(f"{prefix}.") or bone_name.startswith(f"{prefix}_")
        for prefix in RIGIFY_BODY_CONTROL_PREFIXES
    )
