from __future__ import annotations

from ..core.faceboard_constants import (
    FACEBOARD_BUILD_VERSION,
    FACEBOARD_COLLECTION_NAME,
    FACEBOARD_LAYOUT_SCALE,
    FACEBOARD_OBJECT_NAME,
    FACEBOARD_ROOT_BONE,
    FACEBOARD_WORLD_LOCATION,
)
from ..core.faceboard_json import FaceboardDefinition, active_axis_for_control, load_faceboard_json
from .bone_shapes import ensure_basic_control_shapes


def build_faceboard_from_json(json_path: str, collection=None) -> tuple[object, FaceboardDefinition]:
    import bpy

    from ..core.faceboard_constants import FACEBOARD_OBJECT_NAME

    existing = bpy.data.objects.get(FACEBOARD_OBJECT_NAME)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    _remove_faceboard_extras()

    definition = load_faceboard_json(json_path)
    armature_object = _create_faceboard_armature(definition, collection)
    return armature_object, definition


def get_or_create_shared_faceboard(json_path: str, collection=None, force_rebuild: bool = False):
    import bpy

    existing = bpy.data.objects.get(FACEBOARD_OBJECT_NAME)
    if (
        not force_rebuild
        and existing is not None
        and existing.type == "ARMATURE"
        and int(existing.get("mhblender_faceboard_build_version") or 0) == FACEBOARD_BUILD_VERSION
    ):
        _ensure_faceboard_collection(existing, collection)
        _apply_faceboard_visibility(existing)
        return existing, load_faceboard_json(existing.get("mhblender_faceboard_json") or json_path)

    return build_faceboard_from_json(json_path, collection=collection)


def _create_faceboard_armature(definition: FaceboardDefinition, collection):
    import bpy

    armature_data = bpy.data.armatures.new(f"{FACEBOARD_OBJECT_NAME}_Data")
    armature_object = bpy.data.objects.new(FACEBOARD_OBJECT_NAME, armature_data)
    armature_object.location = FACEBOARD_WORLD_LOCATION
    armature_object.rotation_euler = (0.0, 0.0, 0.0)

    target_collection = _ensure_faceboard_collection(armature_object, collection)
    if armature_object.name not in target_collection.objects:
        target_collection.objects.link(armature_object)

    positions = _absolute_control_positions(definition)
    _create_background_panel(target_collection, positions)

    bpy.context.view_layer.objects.active = armature_object
    armature_object.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature_data.edit_bones

    root = edit_bones.new(FACEBOARD_ROOT_BONE)
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 0.05)
    root.use_deform = False

    for control in definition.all_controls:
        position = positions.get(control.name)
        if position is None:
            continue
        bone = edit_bones.new(control.name)
        bone.head = position
        bone.tail = (position[0], position[1], position[2] + 0.02)
        bone.parent = root
        bone.use_connect = False
        bone.use_deform = False

    bpy.ops.object.mode_set(mode="OBJECT")
    armature_object.select_set(False)

    armature_object["mhblender_role"] = "faceboard"
    armature_object["mhblender_faceboard_json"] = str(definition.path)
    armature_object["mhblender_faceboard_version"] = definition.version
    armature_object["mhblender_faceboard_build_version"] = FACEBOARD_BUILD_VERSION
    _store_control_axis_metadata(armature_object, definition)
    _apply_faceboard_visibility(armature_object)
    return armature_object


def _absolute_control_positions(definition: FaceboardDefinition) -> dict[str, tuple[float, float, float]]:
    scale = FACEBOARD_LAYOUT_SCALE
    center_x = (definition.extents["min"][0] + definition.extents["max"][0]) / 2.0
    center_y = (definition.extents["min"][1] + definition.extents["max"][1]) / 2.0

    nodes: dict[str, tuple[tuple[float, float], str | None]] = {}
    for group in definition.gui_groups:
        nodes[group.name] = (group.position, group.parent)
    for group in definition.analog_groups:
        nodes[group.name] = (group.position, group.parent)
    for control in definition.all_controls:
        nodes[control.name] = (control.position, control.parent)

    absolute_2d: dict[str, tuple[float, float]] = {}

    def resolve(name: str) -> tuple[float, float]:
        if name in absolute_2d:
            return absolute_2d[name]
        local, parent = nodes.get(name, ((0.0, 0.0), None))
        if parent and parent in nodes:
            px, py = resolve(parent)
            resolved = (px + local[0], py + local[1])
        else:
            resolved = local
        absolute_2d[name] = resolved
        return resolved

    for name in nodes:
        resolve(name)

    positions: dict[str, tuple[float, float, float]] = {}
    for control in definition.all_controls:
        x, y = absolute_2d.get(control.name, control.position)
        positions[control.name] = (
            (x - center_x) * scale,
            0.0,
            (y - center_y) * scale,
        )
    return positions


def _create_background_panel(collection, positions: dict[str, tuple[float, float, float]]) -> None:
    import bpy

    if not positions:
        return

    xs = [pos[0] for pos in positions.values()]
    zs = [pos[2] for pos in positions.values()]
    min_x, max_x = min(xs) - 0.05, max(xs) + 0.05
    min_z, max_z = min(zs) - 0.05, max(zs) + 0.05
    width = max(max_x - min_x, 0.1)
    height = max(max_z - min_z, 0.1)
    center_x = (min_x + max_x) / 2.0
    center_z = (min_z + max_z) / 2.0

    mesh = bpy.data.meshes.new("MHC_FaceBoard_Panel_Mesh")
    mesh.from_pydata(
        [
            (min_x, 0.0, min_z),
            (max_x, 0.0, min_z),
            (max_x, 0.0, max_z),
            (min_x, 0.0, max_z),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()

    panel = bpy.data.objects.get("MHC_FaceBoard_Panel")
    if panel is None:
        panel = bpy.data.objects.new("MHC_FaceBoard_Panel", mesh)
    else:
        panel.data = mesh

    panel.location = (
        FACEBOARD_WORLD_LOCATION[0],
        FACEBOARD_WORLD_LOCATION[1] - 0.01,
        FACEBOARD_WORLD_LOCATION[2],
    )
    panel.display_type = "WIRE"
    panel.show_in_front = True
    panel["mhblender_role"] = "faceboard_panel"

    if panel.name not in collection.objects:
        collection.objects.link(panel)


def _ensure_faceboard_collection(armature_object, preferred_collection=None):
    import bpy

    collection = bpy.data.collections.get(FACEBOARD_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(FACEBOARD_COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
    collection.hide_viewport = False
    collection.hide_select = False

    if armature_object.name not in collection.objects:
        collection.objects.link(armature_object)

    for user_collection in list(armature_object.users_collection):
        if user_collection != collection and user_collection.name.startswith("MH_") and user_collection.name != FACEBOARD_COLLECTION_NAME:
            user_collection.objects.unlink(armature_object)

    panel = bpy.data.objects.get("MHC_FaceBoard_Panel")
    if panel is not None and panel.name not in collection.objects:
        collection.objects.link(panel)

    return collection


def _remove_faceboard_extras() -> None:
    import bpy

    for name in ("MHC_FaceBoard_Panel",):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def _apply_faceboard_visibility(armature_object) -> None:
    armature_object.hide_viewport = False
    armature_object.hide_set(False)
    armature_object.show_in_front = True
    armature_object.display_type = "TEXTURED"
    armature_object.data.display_type = "OCTAHEDRAL"
    _assign_faceboard_shapes(armature_object)


def _assign_faceboard_shapes(armature_object) -> None:
    import bpy

    shapes = ensure_basic_control_shapes()
    circle = shapes["circle"]
    square = shapes["square"]
    diamond = shapes["diamond"]

    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in armature_object.pose.bones:
        if pose_bone.name == FACEBOARD_ROOT_BONE:
            pose_bone.bone.hide = True
            pose_bone.custom_shape = None
            continue
        lowered = pose_bone.name.lower()
        if "eye" in lowered and "aim" in lowered:
            shape = diamond
            scale = (0.12, 0.12, 0.12)
        elif lowered.startswith("ctrl_"):
            shape = square if "gui" in lowered else circle
            scale = (0.1, 0.1, 0.1)
        else:
            shape = circle
            scale = (0.08, 0.08, 0.08)
        pose_bone.custom_shape = shape
        if hasattr(pose_bone, "use_custom_shape_bone_size"):
            pose_bone.use_custom_shape_bone_size = False
        if hasattr(pose_bone, "custom_shape_scale_xyz"):
            pose_bone.custom_shape_scale_xyz = scale
    bpy.ops.object.mode_set(mode="OBJECT")


def _store_control_axis_metadata(armature_object, definition: FaceboardDefinition) -> None:
    import bpy

    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode="POSE")
    for control in definition.all_controls:
        pose_bone = armature_object.pose.bones.get(control.name)
        if pose_bone is None:
            continue
        active_axis = active_axis_for_control(control)
        if active_axis is not None:
            pose_bone["mhblender_gui_axis"] = _map_faceboard_axis(active_axis.axis)
            pose_bone["mhblender_gui_src_min"] = active_axis.src_min
            pose_bone["mhblender_gui_src_max"] = active_axis.src_max
    bpy.ops.object.mode_set(mode="OBJECT")


def _map_faceboard_axis(axis: str) -> str:
    if "." not in axis:
        return axis
    mode, component = axis.split(".", 1)
    if component == "x":
        mapped = "x"
    elif component == "y":
        mapped = "z"
    elif component == "z":
        mapped = "y"
    else:
        mapped = component
    return f"{mode}.{mapped}"
