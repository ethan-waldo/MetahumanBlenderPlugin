from __future__ import annotations

from dataclasses import dataclass

from ..core.scene_model import RigMap
from .body_constants import (
    RIGIFY_HIDDEN_COLLECTIONS,
    RIGIFY_IK_FK_PAIRS,
    RIGIFY_LIMB_ORG_BONES,
    RIGIFY_LIMB_PARENTS,
    RIGIFY_MAJOR_CONTROL_GROUPS,
    RIGIFY_MINOR_CONTROL_GROUPS,
)
from .control_orientation import align_metarig_roll_from_mh, fit_metarig_bone_from_mh, mh_bone_head_world, mh_chain_end_world


def rigify_available() -> bool:
    try:
        import rigify  # noqa: F401
    except Exception:
        return False
    return True


def use_internal_control_rig_reason() -> str:
    return "Using the internal CTRL_* fallback rig because Rigify is unavailable."


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

def create_rigify_body_control_rig(mh_armature, character_name: str, collection=None) -> RigifyBuildResult:
    import bpy

    from .rigify_binding import infer_deform_binding_maps

    _ensure_rigify_enabled()
    collection = collection or bpy.context.collection
    metarig = _add_human_metarig()
    metarig.name = f"META_{character_name}_RIGIFY"
    metarig.data.name = f"META_{character_name}_RIGIFY_Data"
    _move_to_collection(metarig, collection)
    _fit_metarig_to_metahuman(metarig, mh_armature)
    _strip_face_from_metarig(metarig)

    generated = _generate_rigify_rig(metarig)
    _remove_org_copy_influence_drivers(generated)
    for label in RIGIFY_LIMB_PARENTS:
        _sync_limb_org_constraints(generated, label, True)
    generated.name = f"CTRL_{character_name}_RIG"
    generated.data.name = f"CTRL_{character_name}_RIG_Data"
    generated["mhblender_role"] = "control_rig"
    generated["mhblender_control_type"] = "rigify"
    generated["mhblender_deform_skeleton"] = mh_armature.name
    generated["mhblender_metarig"] = metarig.name
    _move_to_collection(generated, collection)
    _mark_generated_rig_non_export_deform(generated)
    configure_rigify_control_collections(generated)
    visible_controls = _preserve_rigify_body_display(generated)
    generated["mhblender_visible_controls"] = len(visible_controls)

    metarig.hide_viewport = True
    metarig.hide_render = True
    metarig["mhblender_role"] = "rigify_metarig"
    metarig["mhblender_deform_skeleton"] = mh_armature.name
    metarig["mhblender_generated_rig"] = generated.name

    maps, missing = infer_deform_binding_maps(mh_armature, generated)
    return RigifyBuildResult(control_rig=generated, metarig=metarig, maps=maps, missing_targets=missing)


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

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = metarig
    metarig.select_set(True)
    metarig.matrix_world = mh_armature.matrix_world.copy()
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = metarig.data.edit_bones
    rigify_roll_refs = {bone.name: bone.z_axis.copy() for bone in edit_bones}
    fitted: list[tuple[object, str, object]] = []
    for meta_name, (mh_head, mh_tail) in META_TO_MH.items():
        bone = edit_bones.get(meta_name)
        if bone is None:
            continue
        source = mh_armature.data.bones.get(mh_head)
        if source is None:
            continue
        head_world = mh_armature.matrix_world @ source.head_local
        if mh_tail:
            tail_source = mh_armature.data.bones.get(mh_tail)
            tail_world = mh_armature.matrix_world @ tail_source.head_local if tail_source else None
        else:
            tail_world = mh_armature.matrix_world @ source.tail_local
        if tail_world is None or (tail_world - head_world).length < 0.01:
            _, tail_world = mh_chain_end_world(mh_armature, mh_head)
        if not fit_metarig_bone_from_mh(bone, mh_armature, mh_head, tail_world, metarig, meta_bone_name=meta_name):
            inverse = metarig.matrix_world.inverted_safe()
            bone.head = inverse @ head_world
            bone.tail = inverse @ tail_world
        if bone.parent is not None and (bone.head - bone.parent.tail).length > 0.001:
            bone.head = bone.parent.tail.copy()
        fitted.append((bone, mh_head, meta_name))

    _apply_limb_bend_hints(edit_bones)
    for bone, mh_head, meta_name in fitted:
        if _preserve_rigify_roll(meta_name):
            roll_ref = rigify_roll_refs.get(meta_name)
            if roll_ref is not None:
                bone.align_roll(roll_ref)
        else:
            align_metarig_roll_from_mh(bone, mh_armature, mh_head, metarig, meta_bone_name=meta_name)
        if bone.parent is not None and (bone.head - bone.parent.tail).length > 0.001:
            bone.head = bone.parent.tail.copy()
    bpy.ops.object.mode_set(mode="OBJECT")


def _preserve_rigify_roll(meta_bone_name: str) -> bool:
    return (
        meta_bone_name.startswith(("hand.", "palm.", "f_index.", "f_middle.", "f_ring.", "f_pinky.", "thumb.", "toe."))
        or meta_bone_name in {"hand.L", "hand.R", "toe.L", "toe.R"}
    )


def _apply_limb_bend_hints(edit_bones) -> None:
    from mathutils import Vector

    # MetaHuman body DNA is often close to a straight A-pose/T-pose limb chain.
    # Rigify needs a clear bend plane for IK, so add a small metarig-only hint.
    for side in ("L", "R"):
        _bend_middle_joint(edit_bones, f"thigh.{side}", f"shin.{side}", f"foot.{side}", Vector((0.0, -1.0, 0.0)), 0.045)
        _bend_middle_joint(edit_bones, f"upper_arm.{side}", f"forearm.{side}", f"hand.{side}", Vector((0.0, 1.0, 0.0)), 0.055)


def _bend_middle_joint(edit_bones, upper_name: str, mid_name: str, end_name: str, bend_direction, minimum_offset: float) -> None:
    upper = edit_bones.get(upper_name)
    mid = edit_bones.get(mid_name)
    end = edit_bones.get(end_name)
    if upper is None or mid is None or end is None:
        return

    start = upper.head.copy()
    original_mid = mid.head.copy()
    finish = end.head.copy()
    chain = finish - start
    if chain.length <= 1e-6:
        return

    plane_dir = bend_direction - chain.normalized() * bend_direction.dot(chain.normalized())
    if plane_dir.length <= 1e-6:
        return
    plane_dir.normalize()

    projected_mid = start + chain * ((original_mid - start).dot(chain) / chain.length_squared)
    current_offset = (original_mid - projected_mid).dot(plane_dir)
    needed_offset = max(float(minimum_offset), current_offset)
    hinted_mid = projected_mid + plane_dir * needed_offset

    upper.tail = hinted_mid
    mid.head = hinted_mid
    mid.tail = finish
    mid.use_connect = True
    if end.parent == mid:
        end.head = finish
        end.use_connect = True


def _strip_face_from_metarig(metarig) -> None:
    import bpy

    if metarig.data.bones.get("face") is None:
        return
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = metarig
    metarig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = metarig.data.edit_bones
    remove_names: list[str] = []
    queue = ["face"]
    while queue:
        name = queue.pop()
        bone = edit_bones.get(name)
        if bone is None:
            continue
        remove_names.append(name)
        queue.extend(child.name for child in bone.children)
    while remove_names:
        for name in list(remove_names):
            bone = edit_bones.get(name)
            if bone is None:
                remove_names.remove(name)
                continue
            if bone.children:
                continue
            edit_bones.remove(bone)
            remove_names.remove(name)
    bpy.ops.object.mode_set(mode="OBJECT")


def _remove_org_copy_influence_drivers(rig_object) -> int:
    """Drop broken Rigify ORG influence drivers so FK/IK switching can work reliably."""
    animation_data = getattr(rig_object, "animation_data", None)
    if animation_data is None or animation_data.drivers is None:
        return 0

    removed = 0
    for driver in list(animation_data.drivers):
        if "ORG-" not in driver.data_path:
            continue
        if "Copy Transforms" not in driver.data_path:
            continue
        if not driver.data_path.endswith(".influence"):
            continue
        animation_data.drivers.remove(driver)
        removed += 1
    if removed:
        rig_object["mhblender_removed_org_drivers"] = removed
    return removed


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


def configure_rigify_control_collections(rig_object) -> int:
    """Hide technical Rigify layers and default to major animator control groups."""
    collections = getattr(rig_object.data, "collections", None)
    if not collections:
        return 0

    configured = 0
    for collection in collections:
        if collection.name in RIGIFY_HIDDEN_COLLECTIONS:
            collection.is_visible = False
            configured += 1

    for _, names in RIGIFY_MAJOR_CONTROL_GROUPS:
        configured += _set_collection_visibility(rig_object, names, True)

    for _, names in RIGIFY_MINOR_CONTROL_GROUPS:
        configured += _set_collection_visibility(rig_object, names, False)

    rig_object["mhblender_limb_mode"] = "IK"
    for label in RIGIFY_LIMB_PARENTS:
        _sync_limb_org_constraints(rig_object, label, True)
    return configured


def get_limb_mode(rig_object, label: str) -> str:
    parent_name = RIGIFY_LIMB_PARENTS.get(label)
    if parent_name:
        parent = rig_object.pose.bones.get(parent_name)
        if parent is not None and "IK_FK" in parent:
            return "IK" if float(parent["IK_FK"]) >= 0.5 else "FK"

    ik_name, fk_name = _ik_fk_collection_names(label)
    if ik_name is None or fk_name is None:
        return "IK"
    ik_visible = _collection_is_visible(rig_object, ik_name)
    fk_visible = _collection_is_visible(rig_object, fk_name)
    if fk_visible and not ik_visible:
        return "FK"
    return "IK"


def set_limb_mode(rig_object, label: str, mode: str) -> bool:
    use_ik = mode == "IK"
    changed = False

    parent_name = RIGIFY_LIMB_PARENTS.get(label)
    if parent_name:
        parent = rig_object.pose.bones.get(parent_name)
        if parent is not None and "IK_FK" in parent:
            target_value = 1.0 if use_ik else 0.0
            if float(parent["IK_FK"]) != target_value:
                parent["IK_FK"] = target_value
                changed = True
            changed |= _sync_limb_org_constraints(rig_object, label, use_ik)

    ik_name, fk_name = _ik_fk_collection_names(label)
    if ik_name is not None and fk_name is not None:
        changed |= _set_collection_visibility(rig_object, (ik_name,), use_ik)
        changed |= _set_collection_visibility(rig_object, (fk_name,), not use_ik)
    return changed


def _sync_limb_org_constraints(rig_object, label: str, use_ik: bool) -> bool:
    """Switch ORG copy constraints between FK and IK targets."""
    changed = 0
    for org_name in RIGIFY_LIMB_ORG_BONES.get(label, ()):
        pose_bone = rig_object.pose.bones.get(org_name)
        if pose_bone is None:
            continue
        for constraint in pose_bone.constraints:
            if constraint.type != "COPY_TRANSFORMS":
                continue
            use_ik_source = constraint.name.endswith(".001")
            target_influence = 1.0 if use_ik_source == use_ik else 0.0
            if constraint.influence != target_influence:
                constraint.influence = target_influence
                changed += 1
    return changed > 0


def set_control_group_visibility(rig_object, group_names: tuple[str, ...], visible: bool) -> int:
    return _set_collection_visibility(rig_object, group_names, visible)


def _preserve_rigify_body_display(rig_object) -> set[str]:
    """Keep Rigify's generated controls, widgets, and bone collections intact."""
    visible: set[str] = set()
    for bone in rig_object.data.bones:
        if bone.hide or bone.hide_select:
            continue
        if bone.name.startswith(("DEF-", "ORG-", "MCH-", "WGT-")):
            continue
        if _bone_has_visible_collection(bone):
            visible.add(bone.name)
    return visible


def _bone_has_visible_collection(bone) -> bool:
    if not hasattr(bone, "collections") or not bone.collections:
        return True
    return any(collection.is_visible for collection in bone.collections)


def _ik_fk_collection_names(label: str) -> tuple[str | None, str | None]:
    for entry_label, ik_name, fk_name in RIGIFY_IK_FK_PAIRS:
        if entry_label == label:
            return ik_name, fk_name
    return None, None


def _collection_is_visible(rig_object, collection_name: str) -> bool:
    collections = getattr(rig_object.data, "collections", None)
    if not collections:
        return False
    collection = collections.get(collection_name)
    return bool(collection and collection.is_visible)


def _set_collection_visibility(rig_object, collection_names: tuple[str, ...], visible: bool) -> int:
    collections = getattr(rig_object.data, "collections", None)
    if not collections:
        return 0
    changed = 0
    for name in collection_names:
        collection = collections.get(name)
        if collection is None or collection.is_visible == visible:
            continue
        collection.is_visible = visible
        changed += 1
    return changed


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
    return mh_bone_head_world(mh_armature, name)


def _mh_bone_tail_world(mh_armature, name: str | None):
    if not name:
        return None
    bone = mh_armature.data.bones.get(name)
    return mh_armature.matrix_world @ bone.tail_local if bone else None
