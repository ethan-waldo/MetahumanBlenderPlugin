from __future__ import annotations

from dataclasses import dataclass

from ..core.constraint_builder import CONSTRAINT_PREFIX
from ..core.scene_model import RigMap

# Optional legacy map for driving directly from FK animator controls.
FK_OUTPUT_MAP: dict[str, str] = {
    "root": "root",
    "pelvis": "spine_fk",
    "spine_01": "spine_fk.001",
    "spine_02": "spine_fk.002",
    "spine_03": "spine_fk.003",
    "spine_04": "tweak_spine.003",
    "spine_05": "tweak_spine.004",
    "neck_01": "tweak_spine.005",
    "neck_02": "neck",
    "clavicle_l": "shoulder.L",
    "clavicle_r": "shoulder.R",
    "upperarm_l": "upper_arm_fk.L",
    "lowerarm_l": "forearm_fk.L",
    "hand_l": "hand_fk.L",
    "upperarm_r": "upper_arm_fk.R",
    "lowerarm_r": "forearm_fk.R",
    "hand_r": "hand_fk.R",
    "thigh_l": "thigh_fk.L",
    "calf_l": "shin_fk.L",
    "foot_l": "foot_fk.L",
    "ball_l": "toe_fk.L",
    "thigh_r": "thigh_fk.R",
    "calf_r": "shin_fk.R",
    "foot_r": "foot_fk.R",
    "ball_r": "toe_fk.R",
}

for _side_mh, _side_rig in (("l", "L"), ("r", "R")):
    _finger_map = {
        "index": "f_index",
        "middle": "f_middle",
        "ring": "f_ring",
        "pinky": "f_pinky",
    }
    for _mh_prefix, _rig_prefix in _finger_map.items():
        FK_OUTPUT_MAP[f"{_mh_prefix}_metacarpal_{_side_mh}"] = f"palm.{_side_rig}"
        FK_OUTPUT_MAP[f"{_mh_prefix}_01_{_side_mh}"] = f"{_rig_prefix}.01_master.{_side_rig}"
        FK_OUTPUT_MAP[f"{_mh_prefix}_02_{_side_mh}"] = f"{_rig_prefix}.02.{_side_rig}"
        FK_OUTPUT_MAP[f"{_mh_prefix}_03_{_side_mh}"] = f"{_rig_prefix}.03.{_side_rig}"
    for _index in (1, 2, 3):
        FK_OUTPUT_MAP[f"thumb_{_index:02d}_{_side_mh}"] = (
            f"thumb.{_index:02d}_master.{_side_rig}" if _index == 1 else f"thumb.{_index:02d}.{_side_rig}"
        )


DEFORM_OUTPUT_MAP: dict[str, str] = {
    "root": "root",
    "pelvis": "DEF-spine",
    "spine_01": "DEF-spine.001",
    "spine_02": "DEF-spine.002",
    "spine_03": "DEF-spine.003",
    "spine_04": "DEF-spine.004",
    "spine_05": "DEF-spine.005",
    "neck_01": "DEF-spine.006",
    "neck_02": "DEF-spine.006",
    "clavicle_l": "DEF-shoulder.L",
    "upperarm_l": "DEF-upper_arm.L",
    "lowerarm_l": "DEF-forearm.L",
    "hand_l": "DEF-hand.L",
    "clavicle_r": "DEF-shoulder.R",
    "upperarm_r": "DEF-upper_arm.R",
    "lowerarm_r": "DEF-forearm.R",
    "hand_r": "DEF-hand.R",
    "thigh_l": "DEF-thigh.L",
    "calf_l": "DEF-shin.L",
    "foot_l": "DEF-foot.L",
    "ball_l": "DEF-toe.L",
    "thigh_r": "DEF-thigh.R",
    "calf_r": "DEF-shin.R",
    "foot_r": "DEF-foot.R",
    "ball_r": "DEF-toe.R",
}

for _side_mh, _side_rig in (("l", "L"), ("r", "R")):
    _finger_map = {
        "index": ("palm.01", "f_index"),
        "middle": ("palm.02", "f_middle"),
        "ring": ("palm.03", "f_ring"),
        "pinky": ("palm.04", "f_pinky"),
    }
    for _mh_prefix, (_palm, _rig_prefix) in _finger_map.items():
        DEFORM_OUTPUT_MAP[f"{_mh_prefix}_metacarpal_{_side_mh}"] = f"DEF-{_palm}.{_side_rig}"
        DEFORM_OUTPUT_MAP[f"{_mh_prefix}_01_{_side_mh}"] = f"DEF-{_rig_prefix}.01.{_side_rig}"
        DEFORM_OUTPUT_MAP[f"{_mh_prefix}_02_{_side_mh}"] = f"DEF-{_rig_prefix}.02.{_side_rig}"
        DEFORM_OUTPUT_MAP[f"{_mh_prefix}_03_{_side_mh}"] = f"DEF-{_rig_prefix}.03.{_side_rig}"
    for _index in (1, 2, 3):
        DEFORM_OUTPUT_MAP[f"thumb_{_index:02d}_{_side_mh}"] = f"DEF-thumb.{_index:02d}.{_side_rig}"


@dataclass(slots=True)
class RigifyBindingResult:
    maps: list[RigMap]
    missing_targets: list[str]
    empty_count: int


def infer_fk_binding_maps(mh_armature, rigify_rig) -> tuple[list[RigMap], list[str]]:
    return _infer_binding_maps(mh_armature, rigify_rig, FK_OUTPUT_MAP)


def infer_deform_binding_maps(mh_armature, rigify_rig) -> tuple[list[RigMap], list[str]]:
    return _infer_binding_maps(mh_armature, rigify_rig, DEFORM_OUTPUT_MAP)


def _infer_binding_maps(mh_armature, rigify_rig, output_map: dict[str, str]) -> tuple[list[RigMap], list[str]]:
    maps: list[RigMap] = []
    missing: list[str] = []
    rig_bones = set(rigify_rig.data.bones.keys())
    mh_bones = set(mh_armature.data.bones.keys())
    for mh_bone, rigify_bone in output_map.items():
        if mh_bone not in mh_bones:
            continue
        if rigify_bone not in rig_bones:
            missing.append(f"{mh_bone}->{rigify_bone}")
            continue
        maps.append(
            RigMap(
                mh_bone=mh_bone,
                control_bone=rigify_bone,
                constraint_type="COPY_TRANSFORMS",
                transform_space="WORLD",
            )
        )
    return maps, missing


def binding_collection_name(character_name: str) -> str:
    return f"MHBLENDER_{character_name}_constraints"


def binding_empty_name(mh_bone: str) -> str:
    return f"{CONSTRAINT_PREFIX}bind_{mh_bone}"


def apply_rigify_empty_bindings(
    mh_armature,
    rigify_rig,
    maps: list[RigMap],
    character_name: str,
    collection=None,
) -> int:
    """Bind MetaHuman bones to Rigify output bones via empty intermediaries."""
    import bpy

    remove_rigify_empty_bindings(character_name)
    constraint_collection = _ensure_binding_collection(character_name, collection)
    created = 0

    for mapping in maps:
        mh_bone = mh_armature.data.bones.get(mapping.mh_bone)
        source_bone = rigify_rig.data.bones.get(mapping.control_bone)
        if mh_bone is None or source_bone is None:
            continue

        empty = bpy.data.objects.new(binding_empty_name(mapping.mh_bone), None)
        empty.empty_display_size = 0.02
        empty.hide_viewport = True
        empty.hide_select = True
        empty.show_in_front = False
        empty["mhblender_role"] = "rigify_binding_empty"
        empty["mhblender_deform_skeleton"] = mh_armature.name
        empty["mhblender_control_rig"] = rigify_rig.name
        empty["mhblender_mh_bone"] = mapping.mh_bone
        empty["mhblender_source_bone"] = mapping.control_bone
        empty["mhblender_fk_bone"] = mapping.control_bone
        constraint_collection.objects.link(empty)

        mh_rest = mh_armature.matrix_world @ mh_bone.matrix_local
        empty.parent = rigify_rig
        empty.parent_type = "BONE"
        empty.parent_bone = mapping.control_bone
        empty.matrix_world = mh_rest

        pose_bone = mh_armature.pose.bones.get(mapping.mh_bone)
        if pose_bone is None:
            continue
        copy = pose_bone.constraints.new("COPY_TRANSFORMS")
        copy.name = f"{CONSTRAINT_PREFIX}{mapping.control_bone}"
        copy.target = empty
        copy.target_space = "WORLD"
        copy.owner_space = "WORLD"
        created += 1

    mh_armature["mhblender_binding_collection"] = constraint_collection.name
    rigify_rig["mhblender_binding_collection"] = constraint_collection.name
    return created


def remove_rigify_empty_bindings(character_name: str) -> int:
    import bpy

    removed = 0
    collection = bpy.data.collections.get(binding_collection_name(character_name))
    if collection is not None:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
        removed += 1

    prefix = f"{CONSTRAINT_PREFIX}bind_"
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY" and obj.name.startswith(prefix) and obj.get("mhblender_role") == "rigify_binding_empty":
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
    return removed


def _ensure_binding_collection(character_name: str, collection=None):
    import bpy

    name = binding_collection_name(character_name)
    constraint_collection = bpy.data.collections.get(name)
    if constraint_collection is None:
        constraint_collection = bpy.data.collections.new(name)
        if collection is not None:
            collection.children.link(constraint_collection)
        else:
            bpy.context.scene.collection.children.link(constraint_collection)
    constraint_collection.hide_viewport = True
    constraint_collection.hide_render = True
    return constraint_collection
