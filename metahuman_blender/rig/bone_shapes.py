from __future__ import annotations

from math import cos, pi, sin


SHAPE_COLLECTION = "MHBlender_Control_Shapes"


def ensure_basic_control_shapes():
    import bpy

    collection = bpy.data.collections.get(SHAPE_COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(SHAPE_COLLECTION)
        bpy.context.scene.collection.children.link(collection)
    collection.hide_viewport = True
    collection.hide_render = True

    shapes = {
        "root": _ensure_shape_object(collection, "MHB_SHAPE_root_circle", _circle_vertices(64, 1.0), _closed_edges(64)),
        "circle": _ensure_shape_object(collection, "MHB_SHAPE_control_circle", _circle_vertices(32, 0.55), _closed_edges(32)),
        "square": _ensure_shape_object(collection, "MHB_SHAPE_control_square", _square_vertices(0.7, 0.45), _square_edges()),
        "box": _ensure_shape_object(collection, "MHB_SHAPE_control_box", _box_vertices(0.55, 0.35, 0.25), _box_edges()),
        "diamond": _ensure_shape_object(collection, "MHB_SHAPE_control_diamond", _diamond_vertices(0.55), _diamond_edges()),
    }

    for obj in shapes.values():
        obj.hide_viewport = True
        obj.hide_render = True
        obj.hide_select = True
        obj.show_name = False
    return shapes


def assign_rigify_style_shapes(control_object, visible_bones: set[str] | None = None) -> None:
    shapes = ensure_basic_control_shapes()
    for pose_bone in control_object.pose.bones:
        if visible_bones is not None and pose_bone.name not in visible_bones:
            pose_bone.custom_shape = None
            continue
        name = pose_bone.name.lower()
        if name == "ctrl_root_global":
            shape = shapes["root"]
            scale = (0.22, 0.22, 0.22)
        elif "pelvis" in name or "spine" in name or "chest" in name:
            shape = shapes["box"]
            scale = (0.18, 0.18, 0.18)
        elif "hand_ik" in name or "foot_ik" in name or "hand" in name or "foot" in name:
            shape = shapes["square"]
            scale = (0.14, 0.14, 0.14)
        elif "pole" in name:
            shape = shapes["diamond"]
            scale = (0.1, 0.1, 0.1)
        elif "head" in name or "neck" in name:
            shape = shapes["diamond"]
            scale = (0.16, 0.16, 0.16)
        else:
            shape = shapes["circle"]
            scale = (0.12, 0.12, 0.12)

        pose_bone.custom_shape = shape
        if hasattr(pose_bone, "use_custom_shape_bone_size"):
            pose_bone.use_custom_shape_bone_size = False
        if hasattr(pose_bone, "custom_shape_scale_xyz"):
            pose_bone.custom_shape_scale_xyz = scale


def _ensure_shape_object(collection, name: str, vertices, edges):
    import bpy

    obj = bpy.data.objects.get(name)
    if obj is not None:
        if obj.name not in collection.objects:
            collection.objects.link(obj)
        return obj

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _circle_vertices(segments: int, radius: float):
    return [(cos((index / segments) * pi * 2.0) * radius, sin((index / segments) * pi * 2.0) * radius, 0.0) for index in range(segments)]


def _closed_edges(count: int):
    return [(index, (index + 1) % count) for index in range(count)]


def _square_vertices(width: float, height: float):
    return [(-width, -height, 0.0), (width, -height, 0.0), (width, height, 0.0), (-width, height, 0.0)]


def _square_edges():
    return [(0, 1), (1, 2), (2, 3), (3, 0)]


def _box_vertices(width: float, depth: float, height: float):
    return [
        (-width, -depth, -height),
        (width, -depth, -height),
        (width, depth, -height),
        (-width, depth, -height),
        (-width, -depth, height),
        (width, -depth, height),
        (width, depth, height),
        (-width, depth, height),
    ]


def _box_edges():
    return [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


def _diamond_vertices(radius: float):
    return [(0.0, radius, 0.0), (radius, 0.0, 0.0), (0.0, -radius, 0.0), (-radius, 0.0, 0.0)]


def _diamond_edges():
    return [(0, 1), (1, 2), (2, 3), (3, 0)]
