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

RIGIFY_HIDDEN_COLLECTIONS = frozenset(
    {
        "ORG",
        "MCH",
        "DEF",
        "Face",
        "Face (Primary)",
        "Face (Secondary)",
    }
)

# Primary animator sets shown by default after build.
RIGIFY_MAJOR_CONTROL_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Root", ("Root",)),
    ("Torso", ("Torso", "Torso (Tweak)")),
    ("Arms IK", ("Arm.L (IK)", "Arm.R (IK)")),
    ("Legs IK", ("Leg.L (IK)", "Leg.R (IK)")),
    ("Fingers", ("Fingers",)),
)

# Secondary sets hidden until expanded in the UI.
RIGIFY_MINOR_CONTROL_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Arms FK", ("Arm.L (FK)", "Arm.R (FK)")),
    ("Legs FK", ("Leg.L (FK)", "Leg.R (FK)")),
    ("Arm Tweaks", ("Arm.L (Tweak)", "Arm.R (Tweak)")),
    ("Leg Tweaks", ("Leg.L (Tweak)", "Leg.R (Tweak)")),
    ("Finger Detail", ("Fingers (Detail)",)),
)

RIGIFY_IK_FK_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("Arm L", "Arm.L (IK)", "Arm.L (FK)"),
    ("Arm R", "Arm.R (IK)", "Arm.R (FK)"),
    ("Leg L", "Leg.L (IK)", "Leg.L (FK)"),
    ("Leg R", "Leg.R (IK)", "Leg.R (FK)"),
)

RIGIFY_LIMB_PARENTS: dict[str, str] = {
    "Arm L": "upper_arm_parent.L",
    "Arm R": "upper_arm_parent.R",
    "Leg L": "thigh_parent.L",
    "Leg R": "thigh_parent.R",
}

RIGIFY_LIMB_ORG_BONES: dict[str, tuple[str, ...]] = {
    "Arm L": ("ORG-upper_arm.L", "ORG-forearm.L", "ORG-hand.L"),
    "Arm R": ("ORG-upper_arm.R", "ORG-forearm.R", "ORG-hand.R"),
    "Leg L": ("ORG-thigh.L", "ORG-shin.L", "ORG-foot.L"),
    "Leg R": ("ORG-thigh.R", "ORG-shin.R", "ORG-foot.R"),
}


def iter_rigify_control_group_collections(group: tuple[str, tuple[str, ...]]) -> tuple[str, ...]:
    return group[1]


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
