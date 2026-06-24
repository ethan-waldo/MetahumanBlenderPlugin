from __future__ import annotations

import json
from dataclasses import asdict

from .export_manifest import load_export_manifest
from .scene_model import CharacterInstance


def character_from_empty(empty) -> CharacterInstance:
    head_meshes = _load_json_list(empty.get("head_meshes_json"))
    body_meshes = _load_json_list(empty.get("body_meshes_json") or empty.get("meshes_json"))
    return CharacterInstance(
        character_name=str(empty.get("character_name") or ""),
        export_manifest_path=str(empty.get("export_manifest_path") or ""),
        body_dna_path=str(empty.get("body_dna_path") or empty.get("dna_path") or ""),
        head_dna_path=str(empty.get("head_dna_path") or ""),
        deform_skeleton=str(empty.get("deform_skeleton") or ""),
        body_control_rig=str(empty.get("body_control_rig") or ""),
        faceboard_rig=str(empty.get("faceboard_rig") or ""),
        head_meshes=head_meshes,
        body_meshes=body_meshes,
        texture_maps=_load_json_list(empty.get("texture_maps_json")),
        texture_masks=_load_json_list(empty.get("texture_masks_json")),
        thumbnail_path=str(empty.get("thumbnail_path") or ""),
    )


def save_character_to_empty(empty, character: CharacterInstance) -> None:
    empty["character_name"] = character.character_name
    empty["export_manifest_path"] = character.export_manifest_path
    empty["body_dna_path"] = character.body_dna_path
    empty["head_dna_path"] = character.head_dna_path
    empty["deform_skeleton"] = character.deform_skeleton
    empty["body_control_rig"] = character.body_control_rig
    empty["faceboard_rig"] = character.faceboard_rig
    empty["head_meshes_json"] = json.dumps(character.head_meshes)
    empty["body_meshes_json"] = json.dumps(character.body_meshes)
    empty["texture_maps_json"] = json.dumps(character.texture_maps)
    empty["texture_masks_json"] = json.dumps(character.texture_masks)
    empty["thumbnail_path"] = character.thumbnail_path


def resolve_paths_from_character(character: CharacterInstance) -> CharacterInstance:
    if not character.export_manifest_path:
        return character
    try:
        manifest = load_export_manifest(character.export_manifest_path)
    except Exception:
        return character
    character.body_dna_path = str(manifest.body_dna_path)
    character.head_dna_path = str(manifest.head_dna_path) if manifest.head_dna_path else ""
    character.texture_maps = [str(path) for path in manifest.map_files]
    character.texture_masks = [str(path) for path in manifest.mask_files]
    character.thumbnail_path = str(manifest.thumbnail_path) if manifest.thumbnail_path else ""
    if not character.character_name:
        character.character_name = manifest.character_name
    return character


def find_character_empty(character_name: str):
    import bpy

    for obj in bpy.data.objects:
        if obj.get("mhblender_role") != "dna_metadata":
            continue
        if obj.get("character_name") == character_name or obj.name == f"MH_{character_name}_DNA":
            return obj
    return None


def find_deform_skeleton(character_name: str):
    import bpy

    expected = f"MH_{character_name}_SKEL"
    obj = bpy.data.objects.get(expected)
    if obj and obj.type == "ARMATURE":
        return obj
    for candidate in bpy.data.objects:
        if candidate.type == "ARMATURE" and candidate.get("mhblender_role") == "deform_skeleton":
            if candidate.get("mhblender_character") == character_name:
                return candidate
    return None


def _load_json_list(value) -> list[str]:
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def character_to_json(character: CharacterInstance) -> str:
    return json.dumps(asdict(character), indent=2, sort_keys=True)
