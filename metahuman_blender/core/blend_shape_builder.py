from __future__ import annotations

from ..core.coordinate_system import dna_location_to_blender


def apply_blend_shape_deltas(reader, mesh_object, mesh_index: int, channel_names: list[str]) -> int:
    if mesh_object.data.shape_keys is None:
        return 0

    target_count = int(_safe_call(reader, "getBlendShapeTargetCount", mesh_index, default=0) or 0)
    applied = 0
    for target_index in range(target_count):
        channel_index = _safe_call(reader, "getBlendShapeChannelIndex", mesh_index, target_index, default=-1)
        if channel_index is None or int(channel_index) < 0:
            continue
        channel_name = _safe_call(reader, "getBlendShapeChannelName", int(channel_index), default=None)
        if channel_name is None or str(channel_name) not in channel_names:
            continue
        key_block = mesh_object.data.shape_keys.key_blocks.get(str(channel_name))
        if key_block is None:
            continue
        if _write_target_deltas(reader, mesh_object, mesh_index, target_index, key_block):
            applied += 1
    reset_shape_key_values(mesh_object)
    return applied


def reset_shape_key_values(mesh_object) -> None:
    shape_keys = mesh_object.data.shape_keys
    if shape_keys is None:
        return
    for key_block in shape_keys.key_blocks:
        if key_block.name != "Basis":
            key_block.value = 0.0
    shape_keys.reference_key.value = 0.0


def _write_target_deltas(reader, mesh_object, mesh_index: int, target_index: int, key_block) -> bool:
    from mathutils import Vector

    delta_count = int(_safe_call(reader, "getBlendShapeTargetDeltaCount", mesh_index, target_index, default=0) or 0)
    if delta_count <= 0:
        return False

    vertex_indices = _safe_call(reader, "getBlendShapeTargetVertexIndices", mesh_index, target_index, default=None)
    xs = _safe_call(reader, "getBlendShapeTargetDeltaXs", mesh_index, target_index, default=None)
    ys = _safe_call(reader, "getBlendShapeTargetDeltaYs", mesh_index, target_index, default=None)
    zs = _safe_call(reader, "getBlendShapeTargetDeltaZs", mesh_index, target_index, default=None)
    if vertex_indices is None or xs is None or ys is None or zs is None:
        return False

    for index in range(min(delta_count, len(vertex_indices), len(xs), len(ys), len(zs))):
        vertex_index = int(vertex_indices[index])
        if vertex_index < 0 or vertex_index >= len(key_block.data):
            continue
        delta = Vector(dna_location_to_blender((float(xs[index]), float(ys[index]), float(zs[index]))))
        key_block.data[vertex_index].co = mesh_object.data.vertices[vertex_index].co.copy() + delta
    return True


def _safe_call(target, method: str, *args, default=None):
    func = getattr(target, method, None)
    if func is None:
        return default
    try:
        return func(*args)
    except Exception:
        return default
