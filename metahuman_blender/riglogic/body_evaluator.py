from __future__ import annotations

from dataclasses import dataclass
import logging
from math import radians
from pathlib import Path
import re

from ..core.coordinate_system import dna_location_to_blender
from ..core.dna_loader import _open_reader
from ..ui.properties import _binding_paths_from_preferences

LOGGER = logging.getLogger(__name__)
EVALUATOR_CACHE: dict[tuple[str, tuple[str, ...]], "BodyRigLogicEvaluator"] = {}
IS_EVALUATING = False


@dataclass(slots=True)
class BodyEvaluationResult:
    ok: bool
    message: str
    driven_bones: int = 0


class BodyRigLogicEvaluator:
    def __init__(self, dna_path: str, binding_paths: list[str]):
        import riglogic

        self.dna_path = str(Path(dna_path))
        self.binding_paths = list(binding_paths)
        self.reader = _open_reader(self.dna_path, self.binding_paths)
        self.riglogic = riglogic.RigLogic(self.reader)
        self.instance = riglogic.RigInstance(self.riglogic)
        self.instance.setLOD(0)
        self.raw_names = [self.reader.getRawControlName(index) for index in range(self.instance.getRawControlCount())]
        self.raw_map = _build_raw_control_map(self.raw_names)
        self.consumed_bones = set(self.raw_map)

    @classmethod
    def from_context(cls, context, skeleton) -> "BodyRigLogicEvaluator":
        from ..core.character_import import resolve_character_paths

        paths = resolve_character_paths(context.scene.metahuman_blender, skeleton)
        dna_path = paths["body_dna_path"] or skeleton.get("mhblender_dna_path")
        binding_paths = _binding_paths_from_preferences(context)
        key = (str(dna_path), tuple(binding_paths))
        evaluator = EVALUATOR_CACHE.get(key)
        if evaluator is None:
            evaluator = cls(str(dna_path), binding_paths)
            EVALUATOR_CACHE[key] = evaluator
        return evaluator

    def evaluate(self, skeleton) -> BodyEvaluationResult:
        _set_raw_controls_from_pose(self.instance, self.raw_map, skeleton)
        self.riglogic.calculate(self.instance)
        driven = _apply_joint_outputs(
            self.reader,
            self.instance.getJointOutputs(),
            skeleton,
            skip_bones=self.consumed_bones,
        )
        return BodyEvaluationResult(True, f"Applied RigLogic body outputs to {driven} corrective bones.", driven)


def evaluate_body_for_context(context) -> BodyEvaluationResult:
    skeleton_name = context.scene.metahuman_blender.deform_skeleton_name
    skeleton = context.scene.objects.get(skeleton_name) if skeleton_name else None
    if skeleton is None:
        import bpy

        skeleton = next((obj for obj in bpy.data.objects if obj.get("mhblender_role") == "deform_skeleton"), None)
    if skeleton is None:
        return BodyEvaluationResult(False, "No MetaHuman deform skeleton found.")
    evaluator = BodyRigLogicEvaluator.from_context(context, skeleton)
    return evaluator.evaluate(skeleton)


def body_corrective_bone_names(context, skeleton) -> set[str]:
    names: set[str] = set()
    try:
        evaluator = BodyRigLogicEvaluator.from_context(context, skeleton)
    except Exception:
        evaluator = None

    if evaluator is not None:
        for joint_index in range(evaluator.reader.getJointCount()):
            bone_name = evaluator.reader.getJointName(joint_index)
            if bone_name in evaluator.consumed_bones or _is_facial_bone(bone_name):
                continue
            if _looks_like_body_corrective_name(bone_name) and skeleton.pose.bones.get(bone_name) is not None:
                names.add(bone_name)

    if names:
        return names

    for pose_bone in skeleton.pose.bones:
        if _looks_like_body_corrective_name(pose_bone.name) and not _is_facial_bone(pose_bone.name):
            names.add(pose_bone.name)
    return names


def set_body_corrective_bone_visibility(context, visible: bool) -> int:
    import bpy

    settings = context.scene.metahuman_blender
    skeleton = bpy.data.objects.get(settings.deform_skeleton_name) if settings.deform_skeleton_name else None
    if skeleton is None:
        skeleton = next((obj for obj in bpy.data.objects if obj.get("mhblender_role") == "deform_skeleton"), None)
    if skeleton is None or skeleton.type != "ARMATURE":
        return 0

    corrective_names = body_corrective_bone_names(context, skeleton)
    if visible:
        skeleton.hide_viewport = False
        skeleton.hide_select = False
        skeleton.show_in_front = True
        skeleton.data.display_type = "WIRE"
        _set_bone_collections_visible(skeleton, True)
        for bone in skeleton.data.bones:
            show_bone = bone.name in corrective_names
            bone.hide = not show_bone
            bone.hide_select = not show_bone
    else:
        for bone in skeleton.data.bones:
            if bone.name in corrective_names:
                bone.hide = True
                bone.hide_select = True
        skeleton.hide_viewport = True
        skeleton.hide_select = True
        skeleton.show_in_front = False
        _set_bone_collections_visible(skeleton, False)
    return len(corrective_names)


def register_handlers() -> None:
    import bpy

    if _depsgraph_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph_handler)
    if _frame_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_frame_handler)


def unregister_handlers() -> None:
    import bpy

    for handler, handlers in (
        (_depsgraph_handler, bpy.app.handlers.depsgraph_update_post),
        (_frame_handler, bpy.app.handlers.frame_change_post),
    ):
        if handler in handlers:
            handlers.remove(handler)


def clear_cache() -> None:
    EVALUATOR_CACHE.clear()


def _depsgraph_handler(scene, depsgraph) -> None:
    _evaluate_scene_if_enabled(scene)


def _frame_handler(scene) -> None:
    _evaluate_scene_if_enabled(scene)


def _evaluate_scene_if_enabled(scene) -> None:
    global IS_EVALUATING
    if IS_EVALUATING:
        return
    settings = getattr(scene, "metahuman_blender", None)
    if settings is None or not getattr(settings, "enable_body_riglogic", False):
        return

    import bpy

    context = bpy.context
    try:
        IS_EVALUATING = True
        result = evaluate_body_for_context(context)
        settings.body_riglogic_last_error = "" if result.ok else result.message
    except Exception as exc:
        message = f"Body RigLogic evaluation failed: {exc}"
        LOGGER.warning(message, exc_info=True)
        settings.body_riglogic_last_error = message
    finally:
        IS_EVALUATING = False


def _build_raw_control_map(raw_names: list[str]) -> dict[str, dict[str, int]]:
    mapping: dict[str, dict[str, int]] = {}
    pattern = re.compile(r"(.+)\.q([xyzw])$")
    for index, name in enumerate(raw_names):
        match = pattern.match(name)
        if not match:
            continue
        bone_name, component = match.groups()
        mapping.setdefault(bone_name, {})[component] = index
    return mapping


def _looks_like_body_corrective_name(name: str) -> bool:
    lowered = name.lower()
    tokens = (
        "corrective",
        "_bck",
        "_fwd",
        "_in_",
        "_in.",
        "_in_l",
        "_in_r",
        "_inn",
        "_out",
        "_inner",
        "_outer",
        "_bulge",
        "_half",
        "_dip",
        "_pip",
        "_mcp",
        "_palm",
        "_palmmid",
        "_slide",
        "kneeback",
        "_knee",
        "ankle_",
    )
    return any(token in lowered for token in tokens)


def _set_bone_collections_visible(skeleton, visible: bool) -> None:
    collections = getattr(skeleton.data, "collections", None)
    if not collections:
        return
    for collection in collections:
        collection.is_visible = visible


def _set_raw_controls_from_pose(instance, raw_map: dict[str, dict[str, int]], skeleton) -> None:
    for components in raw_map.values():
        for component, index in components.items():
            instance.setRawControl(index, 1.0 if component == "w" else 0.0)

    for bone_name, components in raw_map.items():
        pose_bone = skeleton.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        quat = _pose_delta_quaternion(skeleton, pose_bone)
        values = {"x": quat.x, "y": quat.y, "z": quat.z, "w": quat.w}
        for component, index in components.items():
            instance.setRawControl(index, float(values[component]))


def _pose_delta_quaternion(skeleton, pose_bone):
    parent = pose_bone.parent
    if parent is not None:
        parent_pose_inv = parent.matrix.inverted_safe()
        parent_rest_inv = skeleton.data.bones[parent.name].matrix_local.inverted_safe()
        rest_local = parent_rest_inv @ pose_bone.bone.matrix_local
        pose_local = parent_pose_inv @ pose_bone.matrix
    else:
        rest_local = pose_bone.bone.matrix_local
        pose_local = pose_bone.matrix
    delta = rest_local.inverted_safe() @ pose_local
    return delta.to_quaternion().normalized()


def _apply_joint_outputs(reader, outputs, skeleton, skip_bones: set[str], facial_only: bool = False) -> int:
    driven = 0
    for joint_index in range(reader.getJointCount()):
        bone_name = reader.getJointName(joint_index)
        if bone_name in skip_bones:
            continue
        if facial_only and not _is_facial_bone(bone_name):
            continue
        if not facial_only and _is_facial_bone(bone_name):
            continue
        pose_bone = skeleton.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        base = joint_index * 9
        values = outputs[base : base + 9]
        if len(values) < 9 or max(abs(float(value)) for value in values) < 1.0e-7:
            _clear_pose_delta(pose_bone)
            continue
        _apply_output_delta(pose_bone, values)
        driven += 1
    return driven


def _is_facial_bone(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("facial_") or lowered.startswith("teeth") or lowered.startswith("eye")


def _clear_pose_delta(pose_bone) -> None:
    pose_bone.location = (0.0, 0.0, 0.0)
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    pose_bone.scale = (1.0, 1.0, 1.0)


def _apply_output_delta(pose_bone, values) -> None:
    tx, ty, tz, rx, ry, rz, sx, sy, sz = (float(value) for value in values)
    pose_bone.location = dna_location_to_blender((tx, ty, tz))
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = (radians(rx), radians(-rz), radians(ry))
    pose_bone.scale = (1.0 + sx, 1.0 + sz, 1.0 + sy)
