from __future__ import annotations

from dataclasses import dataclass
import logging
from math import radians
from pathlib import Path

from ..core.coordinate_system import dna_location_to_blender
from ..core.dna_loader import _open_reader
from ..rig.face_controls import read_face_gui_values
from ..riglogic.bindings import validate_bindings
from .body_evaluator import _apply_joint_outputs, _build_raw_control_map, _clear_pose_delta, _is_facial_bone

LOGGER = logging.getLogger(__name__)
FACE_EVALUATOR_CACHE: dict[tuple[str, tuple[str, ...]], "FaceRigLogicEvaluator"] = {}
IS_FACE_EVALUATING = False


@dataclass(slots=True)
class EvaluationResult:
    ok: bool
    message: str
    driven_joints: int = 0
    driven_shapes: int = 0


class FaceRigLogicEvaluator:
    def __init__(self, dna_path: str, binding_paths: list[str]):
        import riglogic

        self.dna_path = str(Path(dna_path))
        self.binding_paths = list(binding_paths)
        self.reader = _open_reader(self.dna_path, self.binding_paths)
        self.riglogic = riglogic.RigLogic(self.reader)
        self.instance = riglogic.RigInstance(self.riglogic)
        self.instance.setLOD(0)
        self.gui_names = [self.reader.getGUIControlName(index) for index in range(self.instance.getGUIControlCount())]
        self.gui_map = {name: index for index, name in enumerate(self.gui_names)}
        self.raw_names = [self.reader.getRawControlName(index) for index in range(self.instance.getRawControlCount())]
        self.raw_map = _build_raw_control_map(self.raw_names)
        self.blend_shape_names = [
            self.reader.getBlendShapeChannelName(index) for index in range(self.reader.getBlendShapeChannelCount())
        ]

    @classmethod
    def from_context(cls, context, head_dna_path: str) -> "FaceRigLogicEvaluator":
        from ..ui.properties import _binding_paths_from_preferences

        binding_paths = _binding_paths_from_preferences(context)
        key = (str(head_dna_path), tuple(binding_paths))
        evaluator = FACE_EVALUATOR_CACHE.get(key)
        if evaluator is None:
            evaluator = cls(str(head_dna_path), binding_paths)
            FACE_EVALUATOR_CACHE[key] = evaluator
        return evaluator

    def evaluate(self, context, skeleton, head_meshes: list, gui_values: dict[str, float]) -> EvaluationResult:
        _reset_facial_pose(skeleton)
        _reset_head_shape_keys(head_meshes)

        for gui_name, value in gui_values.items():
            index = self.gui_map.get(gui_name)
            if index is not None:
                self.instance.setGUIControl(index, float(value))

        if hasattr(self.riglogic, "mapGUIToRawControls"):
            self.riglogic.mapGUIToRawControls(self.instance)
        self.riglogic.calculate(self.instance)

        driven_joints = _apply_joint_outputs(
            self.reader,
            list(self.instance.getJointOutputs()),
            skeleton,
            skip_bones=set(),
            facial_only=True,
        )
        driven_shapes = _apply_blend_shape_outputs(
            list(self.instance.getBlendShapeOutputs()),
            head_meshes,
            self.blend_shape_names,
        )
        return EvaluationResult(
            True,
            f"Applied facial RigLogic to {driven_joints} joints and {driven_shapes} shape keys.",
            driven_joints=driven_joints,
            driven_shapes=driven_shapes,
        )


def evaluate_face_for_context(context) -> EvaluationResult:
    from ..ui.face_sliders import face_gui_control_count

    settings = context.scene.metahuman_blender
    status = validate_bindings(_binding_paths_from_preferences(context))
    if not status.available or status.riglogic_module is None:
        return EvaluationResult(False, status.message)

    skeleton = _find_deform_skeleton(context)
    if skeleton is None:
        return EvaluationResult(False, "No MetaHuman deform skeleton found.")

    if face_gui_control_count(settings) == 0:
        return EvaluationResult(False, "Face GUI sliders not loaded. Import ExportManifest.json with head DNA first.")

    from ..core.character_import import resolve_character_paths

    paths = resolve_character_paths(settings, skeleton)
    head_dna_path = paths["head_dna_path"] or _head_dna_from_metadata(settings.character_name)
    if not head_dna_path:
        return EvaluationResult(False, "Head DNA path is not set. Import ExportManifest.json first.")

    head_meshes = _find_head_meshes(settings.character_name)
    evaluator = FaceRigLogicEvaluator.from_context(context, head_dna_path)
    gui_values = read_face_gui_values(settings, evaluator.gui_names)
    return evaluator.evaluate(context, skeleton, head_meshes, gui_values)


def register_handlers() -> None:
    import bpy

    if _face_depsgraph_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_face_depsgraph_handler)
    if _face_frame_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_face_frame_handler)


def unregister_handlers() -> None:
    import bpy

    for handler, handlers in (
        (_face_depsgraph_handler, bpy.app.handlers.depsgraph_update_post),
        (_face_frame_handler, bpy.app.handlers.frame_change_post),
    ):
        if handler in handlers:
            handlers.remove(handler)


def clear_cache() -> None:
    FACE_EVALUATOR_CACHE.clear()


def _face_depsgraph_handler(scene, depsgraph) -> None:
    _evaluate_face_if_enabled(scene)


def _face_frame_handler(scene) -> None:
    _evaluate_face_if_enabled(scene)


def _evaluate_face_if_enabled(scene) -> None:
    global IS_FACE_EVALUATING
    if IS_FACE_EVALUATING:
        return
    settings = getattr(scene, "metahuman_blender", None)
    if settings is None or not getattr(settings, "enable_face_riglogic", False):
        return

    import bpy

    try:
        IS_FACE_EVALUATING = True
        result = evaluate_face_for_context(bpy.context)
        settings.face_riglogic_last_error = "" if result.ok else result.message
    except Exception as exc:
        message = f"Face RigLogic evaluation failed: {exc}"
        LOGGER.warning(message, exc_info=True)
        settings.face_riglogic_last_error = message
    finally:
        IS_FACE_EVALUATING = False


def _apply_blend_shape_outputs(outputs, head_meshes, blend_shape_names: list[str]) -> int:
    driven = 0
    if not outputs:
        return driven
    for index, value in enumerate(outputs):
        if index >= len(blend_shape_names):
            break
        channel_name = blend_shape_names[index]
        float_value = float(value)
        for mesh_object in head_meshes:
            shape_keys = mesh_object.data.shape_keys
            if shape_keys is None:
                continue
            key_block = shape_keys.key_blocks.get(channel_name)
            if key_block is None:
                continue
            key_block.value = float_value if abs(float_value) >= 1.0e-7 else 0.0
            if abs(float_value) >= 1.0e-7:
                driven += 1
    return driven


def _reset_facial_pose(skeleton) -> None:
    for pose_bone in skeleton.pose.bones:
        if _is_facial_bone(pose_bone.name):
            _clear_pose_delta(pose_bone)


def _reset_head_shape_keys(head_meshes) -> None:
    for mesh_object in head_meshes:
        shape_keys = mesh_object.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if key_block.name != "Basis":
                key_block.value = 0.0


def _find_deform_skeleton(context):
    import bpy

    settings = context.scene.metahuman_blender
    skeleton = bpy.data.objects.get(settings.deform_skeleton_name) if settings.deform_skeleton_name else None
    if skeleton and skeleton.type == "ARMATURE":
        return skeleton
    return next((obj for obj in bpy.data.objects if obj.get("mhblender_role") == "deform_skeleton"), None)


def _find_faceboard(context, preferred_name: str):
    import bpy

    from ..core.faceboard_constants import FACEBOARD_OBJECT_NAME

    for name in (preferred_name, FACEBOARD_OBJECT_NAME):
        if name:
            obj = bpy.data.objects.get(name)
            if obj and obj.type == "ARMATURE":
                return obj
    return next((obj for obj in bpy.data.objects if obj.get("mhblender_role") == "faceboard"), None)


def _find_head_meshes(character_name: str):
    import bpy

    meshes = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.get("mhblender_mesh_role") == "head" and obj.get("mhblender_character") == character_name:
            meshes.append(obj)
    return meshes


def _head_dna_from_metadata(character_name: str) -> str:
    from ..core.character_assembly import find_character_empty

    empty = find_character_empty(character_name)
    return str(empty.get("head_dna_path") or "") if empty is not None else ""


def _binding_paths_from_preferences(context) -> list[str]:
    from ..ui.properties import _binding_paths_from_preferences

    return _binding_paths_from_preferences(context)
