from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..riglogic.bindings import validate_bindings
from .scene_model import DNAAsset, MeshSpec, MetaHumanJoint, Vector3

ReaderFactory = Callable[[Path], Any]


class DNALoadError(RuntimeError):
    pass


def load_dna(path: str | Path, binding_paths: list[str] | None = None, reader_factory: ReaderFactory | None = None) -> DNAAsset:
    dna_path = Path(path).expanduser()
    if not dna_path.exists() and reader_factory is None:
        raise DNALoadError(f"DNA file does not exist: {dna_path}")

    reader = reader_factory(dna_path) if reader_factory else _open_reader(dna_path, binding_paths)
    return asset_from_reader(reader, dna_path)


def asset_from_reader(reader: Any, path: str | Path) -> DNAAsset:
    dna_path = Path(path)
    lod_count = int(_call_first(reader, ("getLODCount",), default=1) or 1)
    db_name = str(_call_first(reader, ("getDBName", "getName", "getArchetype"), default=dna_path.stem))
    joints = _read_joints(reader, lod_count)
    meshes = _read_meshes(reader)
    blend_shapes = _read_named_items(reader, "getBlendShapeChannelCount", "getBlendShapeChannelName")
    _assign_blend_shapes_to_meshes(reader, meshes, blend_shapes)

    return DNAAsset(
        path=dna_path,
        db_name=db_name,
        lod_count=lod_count,
        meshes=meshes,
        joints=joints,
        blend_shapes=blend_shapes,
        raw_controls=_read_named_items(reader, "getRawControlCount", "getRawControlName"),
        gui_controls=_read_named_items(reader, "getGUIControlCount", "getGUIControlName"),
        metadata={
            "joint_count": len(joints),
            "mesh_count": len(meshes),
            "blend_shape_count": len(blend_shapes),
        },
    )


def _open_reader(path: Path, binding_paths: list[str] | None) -> Any:
    status = validate_bindings(binding_paths)
    if not status.available or status.dna_module is None:
        raise DNALoadError(status.message)

    dna = status.dna_module
    try:
        if hasattr(dna, "FileStream") and hasattr(dna, "BinaryStreamReader"):
            stream = dna.FileStream(str(path), dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
            data_layer = getattr(dna, "DataLayer_All", None) or getattr(dna, "DataLayer_Geometry", None)
            reader = dna.BinaryStreamReader(stream, data_layer) if data_layer is not None else dna.BinaryStreamReader(stream)
            if hasattr(reader, "read"):
                reader.read()
            status_type = getattr(dna, "Status", None)
            if status_type is not None and hasattr(status_type, "isOk") and not status_type.isOk():
                status_value = status_type.get()
                raise DNALoadError(f"Error loading DNA: {getattr(status_value, 'message', status_value)}")
            return reader
    except Exception as exc:
        raise DNALoadError(f"Failed to load DNA with Python bindings: {exc}") from exc

    raise DNALoadError("The installed DNA module does not expose FileStream/BinaryStreamReader.")


def _read_joints(reader: Any, lod_count: int) -> list[MetaHumanJoint]:
    count = int(_call_first(reader, ("getJointCount",), default=0) or 0)
    lod_membership = _joint_lod_membership(reader, lod_count)
    joints: list[MetaHumanJoint] = []
    for index in range(count):
        parent_index = _safe_call(reader, "getJointParentIndex", index, default=None)
        if parent_index is None or int(parent_index) == index or int(parent_index) >= count:
            parent: int | None = None
        else:
            parent = int(parent_index)
        joints.append(
            MetaHumanJoint(
                index=index,
                name=str(_safe_call(reader, "getJointName", index, default=f"joint_{index:03d}")),
                parent_index=parent,
                neutral_translation=_vector3(_safe_call(reader, "getNeutralJointTranslation", index, default=(0.0, 0.0, 0.0))),
                neutral_rotation=_vector3(_safe_call(reader, "getNeutralJointRotation", index, default=(0.0, 0.0, 0.0))),
                lods=tuple(lod for lod, indices in lod_membership.items() if index in indices),
            )
        )
    return joints


def _read_meshes(reader: Any) -> list[MeshSpec]:
    count = int(_call_first(reader, ("getMeshCount",), default=0) or 0)
    meshes: list[MeshSpec] = []
    for mesh_index in range(count):
        mesh = MeshSpec(
            index=mesh_index,
            name=str(_safe_call(reader, "getMeshName", mesh_index, default=f"mesh_{mesh_index:03d}")),
            vertices=_read_vertices(reader, mesh_index),
            faces=_read_faces(reader, mesh_index),
            uvs=_read_texture_coordinates(reader, mesh_index),
            face_texture_coordinate_indices=_read_face_texture_coordinate_indices(reader, mesh_index),
            skin_weights=_read_skin_weights(reader, mesh_index),
        )
        meshes.append(mesh)
    return meshes


def _read_vertices(reader: Any, mesh_index: int) -> list[Vector3]:
    count = int(_safe_call(reader, "getVertexPositionCount", mesh_index, default=0) or 0)
    if count <= 0:
        return []

    xs = _safe_call(reader, "getVertexPositionXs", mesh_index, default=None)
    ys = _safe_call(reader, "getVertexPositionYs", mesh_index, default=None)
    zs = _safe_call(reader, "getVertexPositionZs", mesh_index, default=None)
    if xs is not None and ys is not None and zs is not None:
        return [(float(xs[i]), float(ys[i]), float(zs[i])) for i in range(count)]

    vertices: list[Vector3] = []
    for vertex_index in range(count):
        vertices.append(_vector3(_safe_call(reader, "getVertexPosition", mesh_index, vertex_index, default=(0.0, 0.0, 0.0))))
    return vertices


def _read_texture_coordinates(reader: Any, mesh_index: int) -> list[tuple[float, float]]:
    count = int(_safe_call(reader, "getVertexTextureCoordinateCount", mesh_index, default=0) or 0)
    if count <= 0:
        return []

    us = _safe_call(reader, "getVertexTextureCoordinateUs", mesh_index, default=None)
    vs = _safe_call(reader, "getVertexTextureCoordinateVs", mesh_index, default=None)
    if us is not None and vs is not None:
        return [(float(us[i]), float(vs[i])) for i in range(count)]

    coordinates: list[tuple[float, float]] = []
    for texture_index in range(count):
        value = _safe_call(reader, "getVertexTextureCoordinate", mesh_index, texture_index, default=(0.0, 0.0))
        if hasattr(value, "u") and hasattr(value, "v"):
            coordinates.append((float(value.u), float(value.v)))
        elif isinstance(value, (list, tuple)) and len(value) >= 2:
            coordinates.append((float(value[0]), float(value[1])))
        else:
            coordinates.append((0.0, 0.0))
    return coordinates


def _read_face_texture_coordinate_indices(reader: Any, mesh_index: int) -> list[tuple[int, ...]]:
    face_count = int(_safe_call(reader, "getFaceCount", mesh_index, default=0) or 0)
    if face_count <= 0:
        return []

    faces: list[tuple[int, ...]] = []
    for face_index in range(face_count):
        layout_indices = _safe_call(reader, "getFaceVertexLayoutIndices", mesh_index, face_index, default=None)
        if layout_indices is None:
            continue
        corner_indices: list[int] = []
        for layout_index in layout_indices:
            layout = _safe_call(reader, "getVertexLayout", mesh_index, int(layout_index), default=None)
            texture_index = _texture_coordinate_index_from_layout(layout)
            if texture_index is None:
                continue
            corner_indices.append(texture_index)
        if len(corner_indices) >= 3:
            faces.append(tuple(corner_indices))
    return faces


def _texture_coordinate_index_from_layout(layout: Any) -> int | None:
    if layout is None:
        return None
    if isinstance(layout, (list, tuple)) and len(layout) >= 2:
        return int(layout[1])
    if hasattr(layout, "textureCoordinate"):
        return int(layout.textureCoordinate)
    return None


def _read_faces(reader: Any, mesh_index: int) -> list[tuple[int, ...]]:
    face_count = int(_safe_call(reader, "getFaceCount", mesh_index, default=0) or 0)
    if face_count <= 0:
        return []

    layout_positions = _safe_call(reader, "getVertexLayoutPositionIndices", mesh_index, default=None)
    faces: list[tuple[int, ...]] = []
    for face_index in range(face_count):
        layout_indices = _safe_call(reader, "getFaceVertexLayoutIndices", mesh_index, face_index, default=None)
        if layout_indices is None:
            continue
        face: list[int] = []
        for layout_index in layout_indices:
            if hasattr(reader, "getVertexLayoutPositionIndex"):
                face.append(int(reader.getVertexLayoutPositionIndex(mesh_index, int(layout_index))))
            elif layout_positions is not None:
                face.append(int(layout_positions[int(layout_index)]))
            else:
                face.append(int(layout_index))
        if len(face) >= 3:
            faces.append(tuple(face))
    return faces


def _assign_blend_shapes_to_meshes(reader: Any, meshes: list[MeshSpec], blend_shapes: list[str]) -> None:
    count = int(_safe_call(reader, "getMeshBlendShapeChannelMappingCount", default=0) or 0)
    for mapping_index in range(count):
        mapping = _safe_call(reader, "getMeshBlendShapeChannelMapping", mapping_index, default=None)
        if mapping is None:
            continue
        if isinstance(mapping, (list, tuple)) and len(mapping) >= 2:
            mesh_index = int(mapping[0])
            channel_index = int(mapping[1])
        else:
            mesh_index = int(getattr(mapping, "meshIndex", -1))
            channel_index = int(getattr(mapping, "blendShapeChannelIndex", -1))
        if 0 <= mesh_index < len(meshes) and 0 <= channel_index < len(blend_shapes):
            meshes[mesh_index].blend_shape_channels.append(blend_shapes[channel_index])


def _read_skin_weights(reader: Any, mesh_index: int) -> dict[int, list[tuple[int, float]]]:
    count = int(_safe_call(reader, "getSkinWeightsCount", mesh_index, default=0) or 0)
    weights: dict[int, list[tuple[int, float]]] = {}
    for vertex_index in range(count):
        joint_indices = _safe_call(reader, "getSkinWeightsJointIndices", mesh_index, vertex_index, default=None)
        values = _safe_call(reader, "getSkinWeightsValues", mesh_index, vertex_index, default=None)
        if joint_indices is None or values is None:
            continue
        influences = [
            (int(joint_index), float(weight))
            for joint_index, weight in zip(joint_indices, values)
            if float(weight) > 0.0
        ]
        if influences:
            weights[vertex_index] = influences
    return weights


def _read_named_items(reader: Any, count_method: str, name_method: str) -> list[str]:
    count = int(_safe_call(reader, count_method, default=0) or 0)
    return [str(_safe_call(reader, name_method, index, default=f"{name_method}_{index}")) for index in range(count)]


def _joint_lod_membership(reader: Any, lod_count: int) -> dict[int, set[int]]:
    membership: dict[int, set[int]] = {}
    for lod in range(lod_count):
        indices = _safe_call(reader, "getJointIndicesForLOD", lod, default=None)
        membership[lod] = {int(index) for index in indices} if indices is not None else set()
    return membership


def _vector3(value: Any) -> Vector3:
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return (float(value.x), float(value.y), float(value.z))
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    return (0.0, 0.0, 0.0)


def _call_first(target: Any, names: tuple[str, ...], default: Any = None) -> Any:
    for name in names:
        value = _safe_call(target, name, default=None)
        if value is not None:
            return value
    return default


def _safe_call(target: Any, method: str, *args: Any, default: Any = None) -> Any:
    func = getattr(target, method, None)
    if func is None:
        return default
    try:
        return func(*args)
    except TypeError:
        if args:
            return default
        try:
            return func()
        except Exception:
            return default
    except Exception:
        return default
