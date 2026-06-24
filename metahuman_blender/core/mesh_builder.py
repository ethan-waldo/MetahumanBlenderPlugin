from __future__ import annotations

from .blend_shape_builder import apply_blend_shape_deltas, reset_shape_key_values
from .coordinate_system import dna_location_to_blender, dna_uv_to_blender
from .dna_loader import _open_reader
from .lod import infer_lod_index
from .scene_model import DNAAsset, MeshSpec


def create_mesh_objects(asset: DNAAsset, armature_object=None, collection=None, populate_blend_shapes: bool = False, binding_paths: list[str] | None = None) -> list:
    import bpy

    created = []
    reader = _open_reader(asset.path, binding_paths) if populate_blend_shapes and binding_paths else None
    for spec in asset.meshes:
        obj = create_mesh_object(asset, spec, collection=collection)
        if obj is None:
            continue
        if armature_object is not None:
            bind_mesh_to_armature(obj, armature_object, asset=asset, spec=spec)
        if reader is not None:
            apply_blend_shape_deltas(reader, obj, spec.index, spec.blend_shape_channels)
        created.append(obj)
    return created


def create_head_mesh_objects(asset: DNAAsset, armature_object, collection=None, character_name: str | None = None, binding_paths: list[str] | None = None) -> list:
    import bpy

    character = character_name or asset.character_name
    created = []
    reader = _open_reader(asset.path, binding_paths) if binding_paths else None
    for spec in asset.meshes:
        obj = create_mesh_object(asset, spec, collection=collection, object_name_prefix=f"MH_{character}_head")
        if obj is None:
            continue
        bind_mesh_to_armature(obj, armature_object, asset=asset, spec=spec)
        obj["mhblender_character"] = character
        obj["mhblender_mesh_role"] = "head"
        if reader is not None:
            apply_blend_shape_deltas(reader, obj, spec.index, spec.blend_shape_channels)
        created.append(obj)
    return created


def create_mesh_object(asset: DNAAsset, spec: MeshSpec, collection=None, object_name_prefix: str | None = None):
    import bpy

    if not spec.vertices:
        return None

    prefix = object_name_prefix or f"MH_{asset.character_name}"
    mesh_data = bpy.data.meshes.new(f"{prefix}_{spec.name}_Mesh")
    vertices = [dna_location_to_blender(vertex) for vertex in spec.vertices]
    faces = spec.faces
    mesh_data.from_pydata(vertices, [], faces)
    _apply_mesh_uvs(mesh_data, spec)
    mesh_data.update()

    obj = bpy.data.objects.new(f"{prefix}_{spec.name}", mesh_data)
    (collection or bpy.context.collection).objects.link(obj)
    obj["mhblender_role"] = "metahuman_mesh"
    obj["mhblender_mesh_role"] = "body"
    obj["mhblender_character"] = asset.character_name
    obj["mhblender_dna_mesh_index"] = spec.index
    obj["mhblender_lod"] = infer_lod_index(spec.name, spec.index)
    if obj["mhblender_lod"] != 0:
        obj.hide_viewport = True
        obj.hide_render = True
    for channel_name in spec.blend_shape_channels:
        obj.shape_key_add(name=channel_name, from_mix=False)
    reset_shape_key_values(obj)
    return obj


def _apply_mesh_uvs(mesh_data, spec: MeshSpec) -> None:
    if not spec.uvs or not spec.face_texture_coordinate_indices:
        return
    if len(spec.face_texture_coordinate_indices) != len(mesh_data.polygons):
        return

    uv_layer = mesh_data.uv_layers.new(name="UVMap")
    for poly_index, poly in enumerate(mesh_data.polygons):
        corner_indices = spec.face_texture_coordinate_indices[poly_index]
        if len(corner_indices) != len(poly.loop_indices):
            continue
        for loop_index, texture_index in zip(poly.loop_indices, corner_indices):
            if texture_index < 0 or texture_index >= len(spec.uvs):
                continue
            u, v = spec.uvs[texture_index]
            uv_layer.data[loop_index].uv = dna_uv_to_blender(u, v)


def bind_mesh_to_armature(mesh_object, armature_object, asset: DNAAsset | None = None, spec: MeshSpec | None = None) -> None:
    modifier = mesh_object.modifiers.new("MetaHuman Deform Skeleton", "ARMATURE")
    modifier.object = armature_object
    mesh_object.parent = armature_object
    if asset is not None and spec is not None:
        apply_skin_weights(mesh_object, asset, spec)


def apply_skin_weights(mesh_object, asset: DNAAsset, spec: MeshSpec) -> int:
    if not spec.skin_weights:
        return 0

    groups_by_joint = {}
    for influences in spec.skin_weights.values():
        for joint_index, _weight in influences:
            if joint_index < 0 or joint_index >= len(asset.joints):
                continue
            if joint_index not in groups_by_joint:
                groups_by_joint[joint_index] = mesh_object.vertex_groups.new(name=asset.joints[joint_index].name)

    assigned = 0
    for vertex_index, influences in spec.skin_weights.items():
        if vertex_index < 0 or vertex_index >= len(mesh_object.data.vertices):
            continue
        for joint_index, weight in influences:
            group = groups_by_joint.get(joint_index)
            if group is None:
                continue
            group.add([vertex_index], weight, "REPLACE")
            assigned += 1
    return assigned


def bind_external_meshes_by_name(asset: DNAAsset, armature_object, objects: list | None = None) -> list:
    import bpy

    candidates = objects or list(bpy.context.selected_objects)
    mesh_names = {spec.name.lower() for spec in asset.meshes}
    bound = []
    for obj in candidates:
        if obj.type != "MESH":
            continue
        if obj.name.lower() in mesh_names or any(name in obj.name.lower() for name in mesh_names):
            bind_mesh_to_armature(obj, armature_object)
            obj["mhblender_role"] = "metahuman_mesh"
            bound.append(obj)
    return bound
