from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MATERIAL_PARTS = ("Body", "Head", "Eyes", "Teeth")
_ANIMATED_CM_PATTERN = re.compile(r"^Head_Basecolor_Animated_CM(\d+)$", re.IGNORECASE)
_ANIMATED_WM_PATTERN = re.compile(r"^Head_Normal_Animated_WM(\d+)$", re.IGNORECASE)
_WRINKLE_MASK_PATTERN = re.compile(r"^head_wm(\d+)_msk_(\d+)$", re.IGNORECASE)
_SKIN_PARTS = {"Body", "Head"}


@dataclass(slots=True)
class MaterialPartTextures:
    basecolor: Path | None = None
    normal: Path | None = None
    srmf: Path | None = None
    animated_basecolors: dict[int, Path] = field(default_factory=dict)
    animated_normals: dict[int, Path] = field(default_factory=dict)

    def has_textures(self) -> bool:
        return (
            self.basecolor is not None
            or self.normal is not None
            or self.srmf is not None
            or bool(self.animated_basecolors)
            or bool(self.animated_normals)
        )


@dataclass(slots=True)
class MaterialSetupResult:
    assigned_mesh_count: int = 0
    material_count: int = 0
    skipped_mesh_count: int = 0
    warnings: list[str] = field(default_factory=list)


def parse_texture_maps(map_files: list[Path | str]) -> dict[str, MaterialPartTextures]:
    parts = {part: MaterialPartTextures() for part in MATERIAL_PARTS}
    for raw_path in map_files:
        path = Path(raw_path)
        stem = path.stem

        cm_match = _ANIMATED_CM_PATTERN.match(stem)
        if cm_match:
            parts["Head"].animated_basecolors[int(cm_match.group(1))] = path
            continue

        wm_match = _ANIMATED_WM_PATTERN.match(stem)
        if wm_match:
            parts["Head"].animated_normals[int(wm_match.group(1))] = path
            continue

        if "_" not in stem:
            continue
        part_name, map_type = stem.split("_", 1)
        if part_name not in parts:
            continue
        map_type_lower = map_type.lower()
        entry = parts[part_name]
        if map_type_lower in {"basecolor", "color"}:
            entry.basecolor = path
        elif map_type_lower == "normal":
            entry.normal = path
        elif map_type_lower == "srmf":
            entry.srmf = path
    return parts


def parse_wrinkle_masks(mask_files: list[Path | str]) -> dict[int, list[Path]]:
    masks_by_level: dict[int, list[Path]] = {}
    for raw_path in mask_files:
        path = Path(raw_path)
        match = _WRINKLE_MASK_PATTERN.match(path.stem)
        if match is None:
            continue
        level = int(match.group(1))
        masks_by_level.setdefault(level, []).append(path)
    for level in masks_by_level:
        masks_by_level[level] = sorted(masks_by_level[level], key=lambda item: item.name)
    return masks_by_level


def material_part_for_mesh(mesh_name: str) -> str | None:
    lower = mesh_name.lower()
    if lower.startswith("body_"):
        return "Body"
    if lower.startswith("head_") or lower.startswith("cartilage_"):
        return "Head"
    if "teeth" in lower or "saliva" in lower:
        return "Teeth"
    if any(token in lower for token in ("eye", "eyelash", "eyeedge", "eyeshell")):
        return "Eyes"
    return None


def dna_mesh_name_from_object(object_name: str, character_name: str, mesh_role: str | None = None) -> str:
    if mesh_role == "head":
        prefix = f"MH_{character_name}_head_"
    else:
        prefix = f"MH_{character_name}_"
    if object_name.startswith(prefix):
        return object_name[len(prefix) :]
    return object_name


def has_assignable_texture_maps(map_files: list[Path | str], mask_files: list[Path | str] | None = None) -> bool:
    if any(part.has_textures() for part in parse_texture_maps(map_files).values()):
        return True
    return bool(parse_wrinkle_masks(mask_files or []))


def setup_materials_from_manifest(
    manifest,
    mesh_objects,
    *,
    viewport_material: bool = True,
) -> MaterialSetupResult:
    if not has_assignable_texture_maps(manifest.map_files, manifest.mask_files):
        return MaterialSetupResult()
    return setup_materials_for_meshes(
        mesh_objects,
        manifest.character_name,
        manifest.map_files,
        mask_files=manifest.mask_files,
        viewport_material=viewport_material,
    )


def setup_materials_for_meshes(
    mesh_objects,
    character_name: str,
    map_files: list[Path | str],
    *,
    mask_files: list[Path | str] | None = None,
    viewport_material: bool = True,
) -> MaterialSetupResult:
    import bpy

    texture_sets = parse_texture_maps(map_files)
    wrinkle_masks = parse_wrinkle_masks(mask_files or [])
    materials_by_part: dict[str, bpy.types.Material] = {}
    result = MaterialSetupResult()

    for obj in mesh_objects:
        if obj.type != "MESH":
            continue
        mesh_name = dna_mesh_name_from_object(
            obj.name,
            character_name,
            mesh_role=obj.get("mhblender_mesh_role"),
        )
        part = material_part_for_mesh(mesh_name)
        if part is None:
            result.skipped_mesh_count += 1
            continue

        textures = texture_sets.get(part)
        if textures is None or not textures.has_textures():
            if part != "Head" or not wrinkle_masks:
                result.skipped_mesh_count += 1
                continue
            textures = MaterialPartTextures()

        material = materials_by_part.get(part)
        if material is None:
            material = _create_metahuman_material(
                character_name,
                part,
                textures,
                wrinkle_masks=wrinkle_masks if part == "Head" else None,
                viewport_material=viewport_material,
            )
            materials_by_part[part] = material

        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
        obj["mhblender_material_part"] = part
        result.assigned_mesh_count += 1

    result.material_count = len(materials_by_part)
    return result


def _create_metahuman_material(
    character_name: str,
    part: str,
    textures: MaterialPartTextures,
    *,
    wrinkle_masks: dict[int, list[Path]] | None = None,
    viewport_material: bool = True,
):
    import bpy

    material_name = f"MH_{character_name}_{part}"
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (900, 0)
    bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_node.location = (600, 0)
    links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

    if part in _SKIN_PARTS:
        _apply_skin_subsurface_settings(bsdf_node)

    x_offset = -900
    if textures.basecolor is not None:
        basecolor_socket = _sample_texture_color(
            nodes,
            links,
            textures.basecolor,
            colorspace="sRGB",
            location=(x_offset, 300),
            label="Base Color",
        )
        if part == "Head" and textures.animated_basecolors:
            basecolor_socket = _stack_wrinkle_color_maps(
                nodes,
                links,
                basecolor_socket,
                textures.animated_basecolors,
                wrinkle_masks or {},
                start_location=(x_offset - 250, 100),
            )
        links.new(basecolor_socket, bsdf_node.inputs["Base Color"])

    if textures.normal is not None:
        normal_socket = _sample_texture_color(
            nodes,
            links,
            textures.normal,
            colorspace="Non-Color",
            location=(x_offset, 0),
            label="Normal",
        )
        if part == "Head" and textures.animated_normals:
            normal_socket = _stack_wrinkle_normal_maps(
                nodes,
                links,
                normal_socket,
                textures.animated_normals,
                wrinkle_masks or {},
                start_location=(x_offset - 250, -200),
            )
        normal_node = nodes.new("ShaderNodeNormalMap")
        normal_node.location = (300, 0)
        links.new(normal_socket, normal_node.inputs["Color"])
        links.new(normal_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    if textures.srmf is not None:
        _wire_srmf_map(
            nodes,
            links,
            bsdf_node,
            textures.srmf,
            location=(x_offset, -350),
            skin=part in _SKIN_PARTS,
        )

    if viewport_material:
        material.diffuse_color = (0.8, 0.8, 0.8, 1.0)

    material["mhblender_material_part"] = part
    material["mhblender_character"] = character_name
    if wrinkle_masks:
        material["mhblender_wrinkle_mask_levels"] = ",".join(str(level) for level in sorted(wrinkle_masks))
    return material


def _sample_texture_color(nodes, links, path: Path, *, colorspace: str, location, label: str):
    image = _load_image(path, colorspace=colorspace)
    texture_node = _create_image_texture_node(nodes, image, location, label=label)
    return texture_node.outputs["Color"]


def _apply_skin_subsurface_settings(bsdf_node) -> None:
    """Tune Principled BSDF for MetaHuman skin (SSS, not glossy coat)."""
    bsdf_node.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf_node.inputs:
        bsdf_node.inputs["Specular IOR Level"].default_value = 0.35
    if "Coat Weight" in bsdf_node.inputs:
        bsdf_node.inputs["Coat Weight"].default_value = 0.0
    bsdf_node.inputs["Subsurface Weight"].default_value = 0.4
    bsdf_node.inputs["Subsurface Radius"].default_value = (1.0, 0.36, 0.14)
    bsdf_node.inputs["Subsurface Scale"].default_value = 0.05


def _wire_srmf_map(nodes, links, bsdf_node, path: Path, *, location, skin: bool = False):
    image = _load_image(path, colorspace="Non-Color", alpha_mode="CHANNEL_PACKED")
    texture_node = _create_image_texture_node(nodes, image, location, label="SRMF")
    separate_node = nodes.new("ShaderNodeSeparateColor")
    separate_node.location = (location[0] + 220, location[1])
    links.new(texture_node.outputs["Color"], separate_node.inputs["Color"])
    # MetaHuman SRMF: R=Specular, G=Roughness, B=Metallic, A=Fuzz
    links.new(separate_node.outputs["Green"], bsdf_node.inputs["Roughness"])
    if skin:
        # Skin uses SSS instead of UE specular/metallic/fuzz channels in Blender.
        return
    links.new(separate_node.outputs["Blue"], bsdf_node.inputs["Metallic"])
    if "Specular IOR Level" in bsdf_node.inputs:
        links.new(separate_node.outputs["Red"], bsdf_node.inputs["Specular IOR Level"])
    if "Coat Weight" in bsdf_node.inputs:
        links.new(texture_node.outputs["Alpha"], bsdf_node.inputs["Coat Weight"])


def _stack_wrinkle_color_maps(
    nodes,
    links,
    base_socket,
    animated_maps: dict[int, Path],
    wrinkle_masks: dict[int, list[Path]],
    *,
    start_location,
):
    current_socket = base_socket
    y = start_location[1]
    for level in sorted(animated_maps):
        animated_socket = _sample_texture_color(
            nodes,
            links,
            animated_maps[level],
            colorspace="sRGB",
            location=(start_location[0], y),
            label=f"CM{level}",
        )
        current_socket = _mix_wrinkle_layer(
            nodes,
            links,
            current_socket,
            animated_socket,
            wrinkle_masks.get(level, []),
            mix_location=(start_location[0] + 260, y),
            strength_label=f"CM{level}_Strength",
        )
        y -= 180
    return current_socket


def _stack_wrinkle_normal_maps(
    nodes,
    links,
    base_socket,
    animated_maps: dict[int, Path],
    wrinkle_masks: dict[int, list[Path]],
    *,
    start_location,
):
    current_socket = base_socket
    y = start_location[1]
    for level in sorted(animated_maps):
        animated_socket = _sample_texture_color(
            nodes,
            links,
            animated_maps[level],
            colorspace="Non-Color",
            location=(start_location[0], y),
            label=f"WM{level}",
        )
        current_socket = _mix_wrinkle_layer(
            nodes,
            links,
            current_socket,
            animated_socket,
            wrinkle_masks.get(level, []),
            mix_location=(start_location[0] + 260, y),
            strength_label=f"WM{level}_Strength",
        )
        y -= 180
    return current_socket


def _mix_wrinkle_layer(
    nodes,
    links,
    base_socket,
    layer_socket,
    mask_paths: list[Path],
    *,
    mix_location,
    strength_label: str,
):
    mix_node = nodes.new("ShaderNodeMixRGB")
    mix_node.location = mix_location
    mix_node.inputs["Fac"].default_value = 0.0
    links.new(base_socket, mix_node.inputs["Color1"])
    links.new(layer_socket, mix_node.inputs["Color2"])

    if mask_paths:
        mask_socket = _combine_wrinkle_masks(
            nodes,
            links,
            mask_paths,
            location=(mix_location[0] - 260, mix_location[1] - 120),
            label_prefix=strength_label,
        )
        strength_node = nodes.new("ShaderNodeValue")
        strength_node.label = strength_label
        strength_node.name = strength_label
        strength_node.outputs[0].default_value = 0.0
        strength_node.location = (mix_location[0] - 120, mix_location[1] - 120)

        multiply_node = nodes.new("ShaderNodeMath")
        multiply_node.operation = "MULTIPLY"
        multiply_node.location = (mix_location[0] - 40, mix_location[1] - 120)
        links.new(mask_socket, multiply_node.inputs[0])
        links.new(strength_node.outputs[0], multiply_node.inputs[1])
        links.new(multiply_node.outputs[0], mix_node.inputs["Fac"])

    return mix_node.outputs["Color"]


def _combine_wrinkle_masks(nodes, links, mask_paths: list[Path], *, location, label_prefix: str):
    x, y = location
    channels: list = []
    for index, path in enumerate(mask_paths):
        image = _load_image(path, colorspace="Non-Color")
        texture_node = _create_image_texture_node(
            nodes,
            image,
            (x, y - index * 160),
            label=f"{label_prefix}_Mask{index + 1}",
        )
        separate_node = nodes.new("ShaderNodeSeparateColor")
        separate_node.location = (x + 220, y - index * 160)
        links.new(texture_node.outputs["Color"], separate_node.inputs["Color"])
        channels.append(separate_node.outputs["Red"])
        channels.append(separate_node.outputs["Green"])
        channels.append(separate_node.outputs["Blue"])

    if not channels:
        value_node = nodes.new("ShaderNodeValue")
        value_node.outputs[0].default_value = 0.0
        return value_node.outputs[0]

    result_socket = channels[0]
    for channel in channels[1:]:
        math_node = nodes.new("ShaderNodeMath")
        math_node.operation = "MAXIMUM"
        math_node.location = (x + 320, y)
        links.new(result_socket, math_node.inputs[0])
        links.new(channel, math_node.inputs[1])
        result_socket = math_node.outputs[0]
    return result_socket


def _create_image_texture_node(nodes, image, location, *, label: str | None = None):
    texture_node = nodes.new("ShaderNodeTexImage")
    texture_node.image = image
    texture_node.location = location
    texture_node.extension = "REPEAT"
    if label:
        texture_node.label = label
    return texture_node


def _load_image(path: Path, *, colorspace: str, alpha_mode: str | None = None):
    import bpy

    resolved = Path(path).expanduser().resolve()
    cache_key = str(resolved)
    image = bpy.data.images.get(cache_key)
    if image is None:
        image = bpy.data.images.load(cache_key, check_existing=True)
        image.name = Path(path).name
    image.colorspace_settings.name = colorspace
    image.source = "FILE"
    if alpha_mode is not None:
        image.alpha_mode = alpha_mode
    return image
