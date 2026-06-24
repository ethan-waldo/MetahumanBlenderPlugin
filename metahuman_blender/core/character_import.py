from __future__ import annotations

import json
from pathlib import Path

from .character_assembly import save_character_to_empty
from .dna_loader import load_dna
from .export_manifest import ExportManifest, load_export_manifest
from .lod import set_lod_visibility
from .material_builder import setup_materials_from_manifest
from .mesh_builder import create_head_mesh_objects, create_mesh_objects
from .scene_model import CharacterInstance
from .skeleton_builder import create_metahuman_armature, hide_deform_skeleton_display


def import_character_from_manifest(context, manifest_path: str | Path, binding_paths: list[str] | None = None):
    manifest = load_export_manifest(manifest_path)
    collection = _ensure_collection(context, f"MH_{manifest.character_name}")

    body_asset = load_dna(manifest.body_dna_path, binding_paths=binding_paths)
    skeleton = create_metahuman_armature(body_asset, collection=collection)
    skeleton["mhblender_role"] = "deform_skeleton"
    skeleton["mhblender_character"] = manifest.character_name
    skeleton["mhblender_dna_path"] = str(manifest.body_dna_path)
    skeleton["mhblender_export_manifest"] = str(manifest.path)

    head_asset = None
    if manifest.head_dna_path is not None:
        head_asset = load_dna(manifest.head_dna_path, binding_paths=binding_paths)
        skeleton["mhblender_head_dna_path"] = str(manifest.head_dna_path)
        from .skeleton_merge import merge_head_joints_into_armature

        merged_bones = merge_head_joints_into_armature(skeleton, head_asset)
        skeleton["mhblender_merged_head_bones"] = merged_bones

    body_meshes = create_mesh_objects(body_asset, skeleton, collection=collection)
    head_meshes = []
    head_import_warning = ""
    if head_asset is not None:
        try:
            head_meshes = create_head_mesh_objects(
                head_asset,
                skeleton,
                collection=collection,
                character_name=manifest.character_name,
                binding_paths=binding_paths,
            )
        except Exception as exc:
            head_import_warning = f"Head import failed: {exc}"

    metadata_empty = _create_metadata_empty(context, manifest, skeleton, body_meshes, head_meshes, collection)
    material_result = setup_materials_from_manifest(
        manifest,
        body_meshes + head_meshes,
    )
    if material_result.material_count:
        metadata_empty["mhblender_material_count"] = material_result.material_count
        metadata_empty["mhblender_materialized_mesh_count"] = material_result.assigned_mesh_count
    hide_deform_skeleton_display(skeleton)
    set_lod_visibility(manifest.character_name, 0)
    if head_import_warning:
        metadata_empty["mhblender_last_warning"] = head_import_warning
    return manifest, skeleton, body_meshes, head_meshes, metadata_empty, head_import_warning, material_result


def import_head_for_skeleton(context, head_dna_path: str | Path, skeleton, character_name: str, binding_paths: list[str] | None = None):
    from .skeleton_merge import merge_head_joints_into_armature

    asset = load_dna(head_dna_path, binding_paths=binding_paths)
    merge_head_joints_into_armature(skeleton, asset)
    collection = skeleton.users_collection[0] if skeleton.users_collection else context.collection
    return create_head_mesh_objects(
        asset,
        skeleton,
        collection=collection,
        character_name=character_name,
        binding_paths=binding_paths,
    )


def character_instance_from_manifest(manifest: ExportManifest, skeleton, body_meshes, head_meshes) -> CharacterInstance:
    return CharacterInstance(
        character_name=manifest.character_name,
        export_manifest_path=str(manifest.path),
        body_dna_path=str(manifest.body_dna_path),
        head_dna_path=str(manifest.head_dna_path) if manifest.head_dna_path else "",
        deform_skeleton=skeleton.name,
        body_meshes=[mesh.name for mesh in body_meshes],
        head_meshes=[mesh.name for mesh in head_meshes],
        texture_maps=[str(path) for path in manifest.map_files],
        texture_masks=[str(path) for path in manifest.mask_files],
        thumbnail_path=str(manifest.thumbnail_path) if manifest.thumbnail_path else "",
    )


def apply_character_settings(settings, manifest: ExportManifest, skeleton) -> None:
    settings.export_manifest_path = str(manifest.path)
    settings.dna_path = str(manifest.body_dna_path)
    settings.head_dna_path = str(manifest.head_dna_path) if manifest.head_dna_path else ""
    settings.character_name = manifest.character_name
    settings.deform_skeleton_name = skeleton.name
    settings.current_lod = 0
    settings.enable_body_riglogic = True
    settings.enable_face_riglogic = True
    settings.body_riglogic_last_error = ""
    settings.face_riglogic_last_error = ""


def resolve_character_paths(settings, skeleton=None) -> dict[str, str]:
    manifest_path = getattr(settings, "export_manifest_path", "") or ""
    if manifest_path:
        try:
            manifest = load_export_manifest(manifest_path)
            return {
                "export_manifest_path": str(manifest.path),
                "body_dna_path": str(manifest.body_dna_path),
                "head_dna_path": str(manifest.head_dna_path) if manifest.head_dna_path else "",
                "character_name": manifest.character_name,
            }
        except Exception:
            pass

    body_dna_path = getattr(settings, "dna_path", "") or ""
    head_dna_path = getattr(settings, "head_dna_path", "") or ""
    if skeleton is not None:
        body_dna_path = skeleton.get("mhblender_dna_path") or body_dna_path
        head_dna_path = skeleton.get("mhblender_head_dna_path") or head_dna_path
    return {
        "export_manifest_path": manifest_path,
        "body_dna_path": body_dna_path,
        "head_dna_path": head_dna_path,
        "character_name": getattr(settings, "character_name", "") or "",
    }


def _ensure_collection(context, name: str):
    import bpy

    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(collection)
    return collection


def _create_metadata_empty(context, manifest: ExportManifest, skeleton, body_meshes, head_meshes, collection):
    import bpy

    empty = bpy.data.objects.new(f"MH_{manifest.character_name}_DNA", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.25
    collection.objects.link(empty)
    empty["mhblender_role"] = "dna_metadata"
    empty["character_name"] = manifest.character_name
    empty["export_manifest_path"] = str(manifest.path)
    empty["dna_path"] = str(manifest.body_dna_path)
    empty["body_dna_path"] = str(manifest.body_dna_path)
    empty["head_dna_path"] = str(manifest.head_dna_path) if manifest.head_dna_path else ""
    empty["deform_skeleton"] = skeleton.name
    empty["meshes_json"] = json.dumps([mesh.name for mesh in body_meshes])
    empty["body_meshes_json"] = json.dumps([mesh.name for mesh in body_meshes])
    empty["head_meshes_json"] = json.dumps([mesh.name for mesh in head_meshes])
    empty["texture_maps_json"] = json.dumps([str(path) for path in manifest.map_files])
    empty["texture_masks_json"] = json.dumps([str(path) for path in manifest.mask_files])
    empty["thumbnail_path"] = str(manifest.thumbnail_path) if manifest.thumbnail_path else ""
    empty["summary_json"] = json.dumps(
        {
            "meta_human_name": manifest.meta_human_name,
            "export_plugin_version": manifest.export_plugin_version,
            "export_engine_version": manifest.export_engine_version,
            "exported_at": manifest.exported_at,
            "body_mesh_count": len(body_meshes),
            "head_mesh_count": len(head_meshes),
            "texture_map_count": len(manifest.map_files),
            "texture_mask_count": len(manifest.mask_files),
        },
        sort_keys=True,
    )

    character = character_instance_from_manifest(manifest, skeleton, body_meshes, head_meshes)
    save_character_to_empty(empty, character)
    return empty
