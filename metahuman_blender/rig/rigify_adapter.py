from __future__ import annotations

from dataclasses import dataclass

from ..core.scene_model import RigMap


def rigify_available() -> bool:
    try:
        import rigify  # noqa: F401
    except Exception:
        return False
    return True


def use_internal_control_rig_reason() -> str:
    return (
        "Milestone 1 uses the internal Rigify-style control rig. "
        "This keeps the control-to-MetaHuman mapping stable and avoids Rigify generated-name churn."
    )


@dataclass(slots=True)
class RigifyBuildResult:
    control_rig: object
    metarig: object
    maps: list[RigMap]
    missing_targets: list[str]


META_TO_MH = {
    "spine": ("pelvis", "spine_01"),
    "spine.001": ("spine_01", "spine_02"),
    "spine.002": ("spine_02", "spine_03"),
    "spine.003": ("spine_03", "spine_04"),
    "spine.004": ("spine_04", "spine_05"),
    "spine.005": ("spine_05", "neck_01"),
    "spine.006": ("neck_01", "head"),
    "shoulder.L": ("clavicle_l", "upperarm_l"),
    "upper_arm.L": ("upperarm_l", "lowerarm_l"),
    "forearm.L": ("lowerarm_l", "hand_l"),
    "hand.L": ("hand_l", None),
    "shoulder.R": ("clavicle_r", "upperarm_r"),
    "upper_arm.R": ("upperarm_r", "lowerarm_r"),
    "forearm.R": ("lowerarm_r", "hand_r"),
    "hand.R": ("hand_r", None),
    "pelvis.L": ("pelvis", "thigh_l"),
    "thigh.L": ("thigh_l", "calf_l"),
    "shin.L": ("calf_l", "foot_l"),
    "foot.L": ("foot_l", "ball_l"),
    "toe.L": ("ball_l", None),
    "heel.02.L": ("foot_l", None),
    "pelvis.R": ("pelvis", "thigh_r"),
    "thigh.R": ("thigh_r", "calf_r"),
    "shin.R": ("calf_r", "foot_r"),
    "foot.R": ("foot_r", "ball_r"),
    "toe.R": ("ball_r", None),
    "heel.02.R": ("foot_r", None),
}

for _side_mh, _side_rig in (("l", "L"), ("r", "R")):
    _prefix_map = {
        "index": "f_index",
        "middle": "f_middle",
        "ring": "f_ring",
        "pinky": "f_pinky",
    }
    _palm_map = {
        "index": "palm.01",
        "middle": "palm.02",
        "ring": "palm.03",
        "pinky": "palm.04",
    }
    for _mh_prefix, _rig_prefix in _prefix_map.items():
        META_TO_MH[f"{_palm_map[_mh_prefix]}.{_side_rig}"] = (f"hand_{_side_mh}", f"{_mh_prefix}_01_{_side_mh}")
        META_TO_MH[f"{_rig_prefix}.01.{_side_rig}"] = (f"{_mh_prefix}_01_{_side_mh}", f"{_mh_prefix}_02_{_side_mh}")
        META_TO_MH[f"{_rig_prefix}.02.{_side_rig}"] = (f"{_mh_prefix}_02_{_side_mh}", f"{_mh_prefix}_03_{_side_mh}")
        META_TO_MH[f"{_rig_prefix}.03.{_side_rig}"] = (f"{_mh_prefix}_03_{_side_mh}", None)
    for _index in (1, 2, 3):
        _next = _index + 1 if _index < 3 else None
        META_TO_MH[f"thumb.{_index:02d}.{_side_rig}"] = (
            f"thumb_{_index:02d}_{_side_mh}",
            f"thumb_{_next:02d}_{_side_mh}" if _next else None,
        )

RIGIFY_OUTPUT_MAP = {
    "root": "root",
    "pelvis": "DEF-spine",
    "spine_01": "DEF-spine.001",
    "spine_02": "DEF-spine.002",
    "spine_03": "DEF-spine.003",
    "spine_04": "DEF-spine.004",
    "spine_05": "DEF-spine.005",
    "neck_01": "DEF-spine.006",
    "head": "head",
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
        RIGIFY_OUTPUT_MAP[f"{_mh_prefix}_metacarpal_{_side_mh}"] = f"DEF-{_palm}.{_side_rig}"
        RIGIFY_OUTPUT_MAP[f"{_mh_prefix}_01_{_side_mh}"] = f"DEF-{_rig_prefix}.01.{_side_rig}"
        RIGIFY_OUTPUT_MAP[f"{_mh_prefix}_02_{_side_mh}"] = f"DEF-{_rig_prefix}.02.{_side_rig}"
        RIGIFY_OUTPUT_MAP[f"{_mh_prefix}_03_{_side_mh}"] = f"DEF-{_rig_prefix}.03.{_side_rig}"
    for _index in (1, 2, 3):
        RIGIFY_OUTPUT_MAP[f"thumb_{_index:02d}_{_side_mh}"] = f"DEF-thumb.{_index:02d}.{_side_rig}"

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


def create_rigify_body_control_rig(mh_armature, character_name: str, collection=None) -> RigifyBuildResult:
    import bpy

    _ensure_rigify_enabled()
    collection = collection or bpy.context.collection
    metarig = _add_human_metarig()
    metarig.name = f"META_{character_name}_RIGIFY"
    metarig.data.name = f"META_{character_name}_RIGIFY_Data"
    _move_to_collection(metarig, collection)
    _fit_metarig_to_metahuman(metarig, mh_armature)

    generated = _generate_rigify_rig(metarig)
    generated.name = f"CTRL_{character_name}_RIG"
    generated.data.name = f"CTRL_{character_name}_RIG_Data"
    generated["mhblender_role"] = "control_rig"
    generated["mhblender_control_type"] = "rigify"
    generated["mhblender_deform_skeleton"] = mh_armature.name
    _move_to_collection(generated, collection)
    _mark_generated_rig_non_export_deform(generated)
    _hide_face_controls(generated)

    metarig.hide_viewport = True
    metarig.hide_render = True
    metarig["mhblender_role"] = "rigify_metarig"
    metarig["mhblender_deform_skeleton"] = mh_armature.name
    metarig["mhblender_generated_rig"] = generated.name

    maps, missing = infer_rigify_output_maps(mh_armature, generated)
    return RigifyBuildResult(control_rig=generated, metarig=metarig, maps=maps, missing_targets=missing)


def infer_rigify_output_maps(mh_armature, rigify_rig) -> tuple[list[RigMap], list[str]]:
    maps: list[RigMap] = []
    missing: list[str] = []
    rig_bones = set(rigify_rig.data.bones.keys())
    mh_bones = set(mh_armature.data.bones.keys())
    for mh_bone, rigify_bone in RIGIFY_OUTPUT_MAP.items():
        if mh_bone not in mh_bones:
            continue
        if rigify_bone not in rig_bones:
            missing.append(f"{mh_bone}->{rigify_bone}")
            continue
        if mh_bone == "root":
            maps.append(RigMap(mh_bone=mh_bone, control_bone=rigify_bone, constraint_type="CHILD_OF", transform_space="WORLD"))
        else:
            maps.append(RigMap(mh_bone=mh_bone, control_bone=rigify_bone, constraint_type="COPY_ROTATION", transform_space="LOCAL"))
    return maps, missing


def _ensure_rigify_enabled() -> None:
    import addon_utils
    import bpy

    if "rigify" not in bpy.context.preferences.addons:
        addon_utils.enable("rigify", default_set=True, persistent=True)


def _add_human_metarig():
    import bpy

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    area, region, space = _view3d_context()
    with bpy.context.temp_override(area=area, region=region, space_data=space):
        bpy.ops.object.armature_human_metarig_add()
    return bpy.context.object


def _fit_metarig_to_metahuman(metarig, mh_armature) -> None:
    import bpy
    from mathutils import Vector

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = metarig
    metarig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = metarig.data.edit_bones
    for meta_name, (mh_head, mh_tail) in META_TO_MH.items():
        bone = edit_bones.get(meta_name)
        if bone is None:
            continue
        head = _mh_bone_head_world(mh_armature, mh_head)
        tail = _mh_bone_head_world(mh_armature, mh_tail) if mh_tail else _mh_bone_tail_world(mh_armature, mh_head)
        if head is None:
            continue
        if tail is None or (tail - head).length < 0.01:
            tail = head + Vector((0.0, 0.0, 0.08))
        bone.head = metarig.matrix_world.inverted() @ head
        bone.tail = metarig.matrix_world.inverted() @ tail
        bone.roll = 0.0

    bpy.ops.object.mode_set(mode="OBJECT")


def _generate_rigify_rig(metarig):
    import bpy

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    metarig.select_set(True)
    bpy.context.view_layer.objects.active = metarig
    area, region, space = _view3d_context()
    before = set(bpy.data.objects.keys())
    with bpy.context.temp_override(area=area, region=region, space_data=space):
        bpy.ops.pose.rigify_generate()
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    created = [bpy.data.objects[name] for name in set(bpy.data.objects.keys()) - before]
    rigs = [obj for obj in created if obj.type == "ARMATURE"]
    if not rigs:
        raise RuntimeError("Rigify did not create a generated armature.")
    return rigs[0]


def _mark_generated_rig_non_export_deform(rig_object) -> None:
    for bone in rig_object.data.bones:
        bone.use_deform = False
    rig_object.show_in_front = True


def _hide_face_controls(rig_object) -> None:
    for bone in rig_object.data.bones:
        lowered = bone.name.lower()
        if bone.name in {"head", "neck"}:
            continue
        if any(token in lowered for token in FACE_CONTROL_TOKENS):
            bone.hide = True


def _move_to_collection(obj, collection) -> None:
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for user_collection in list(obj.users_collection):
        if user_collection != collection:
            user_collection.objects.unlink(obj)


def _view3d_context():
    import bpy

    area = next((item for item in bpy.context.window.screen.areas if item.type == "VIEW_3D"), None)
    if area is None:
        raise RuntimeError("Rigify generation requires an open 3D View.")
    region = next((item for item in area.regions if item.type == "WINDOW"), None)
    space = next((item for item in area.spaces if item.type == "VIEW_3D"), None)
    return area, region, space


def _mh_bone_head_world(mh_armature, name: str | None):
    if not name:
        return None
    bone = mh_armature.data.bones.get(name)
    return mh_armature.matrix_world @ bone.head_local if bone else None


def _mh_bone_tail_world(mh_armature, name: str | None):
    if not name:
        return None
    bone = mh_armature.data.bones.get(name)
    return mh_armature.matrix_world @ bone.tail_local if bone else None
