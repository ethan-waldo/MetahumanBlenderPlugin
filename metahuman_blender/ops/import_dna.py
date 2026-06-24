from __future__ import annotations

import json
from pathlib import Path

classes = []


def register():
    import bpy
    from bpy.props import StringProperty
    from bpy_extras.io_utils import ImportHelper

    class MHB_OT_ImportDNA(bpy.types.Operator, ImportHelper):
        bl_idname = "mhblender.import_dna"
        bl_label = "Import Body DNA (Legacy)"
        bl_description = "Load body.dna directly. Prefer Import Export Manifest for full DCC packages."
        filename_ext = ".dna"
        filter_glob: StringProperty(default="*.dna", options={"HIDDEN"})

        def execute(self, context):
            from ..core.character_assembly import save_character_to_empty
            from ..core.character_import import apply_character_settings
            from ..core.dna_loader import load_dna
            from ..core.export_manifest import find_export_manifest
            from ..core.export_manifest import load_export_manifest
            from ..core.lod import set_lod_visibility
            from ..core.mesh_builder import create_mesh_objects
            from ..core.scene_model import CharacterInstance
            from ..core.skeleton_builder import create_metahuman_armature
            from ..ui.properties import _binding_paths_from_preferences, get_settings

            try:
                dna_path = Path(self.filepath)
                asset = load_dna(dna_path, binding_paths=_binding_paths_from_preferences(context))
                collection = _ensure_collection(context, f"MH_{asset.character_name}")
                skeleton = create_metahuman_armature(asset, collection=collection)
                from ..core.skeleton_builder import hide_deform_skeleton_display

                hide_deform_skeleton_display(skeleton)
                skeleton["mhblender_character"] = asset.character_name
                skeleton["mhblender_dna_path"] = str(dna_path)
                meshes = create_mesh_objects(asset, skeleton, collection=collection)
                dna_empty = _create_dna_empty(context, asset, skeleton, meshes, collection)

                manifest_path = find_export_manifest(dna_path.parent)
                character = CharacterInstance(
                    character_name=asset.character_name,
                    body_dna_path=str(dna_path),
                    deform_skeleton=skeleton.name,
                    body_meshes=[mesh.name for mesh in meshes],
                )
                if manifest_path is not None:
                    manifest = load_export_manifest(manifest_path)
                    character.export_manifest_path = str(manifest.path)
                    character.head_dna_path = str(manifest.head_dna_path) if manifest.head_dna_path else ""
                    character.texture_maps = [str(path) for path in manifest.map_files]
                    character.texture_masks = [str(path) for path in manifest.mask_files]
                    skeleton["mhblender_export_manifest"] = str(manifest.path)
                    if manifest.head_dna_path:
                        skeleton["mhblender_head_dna_path"] = str(manifest.head_dna_path)
                    dna_empty["export_manifest_path"] = str(manifest.path)
                save_character_to_empty(dna_empty, character)

                settings = get_settings(context)
                settings.dna_path = str(dna_path)
                settings.character_name = asset.character_name
                settings.deform_skeleton_name = skeleton.name
                settings.current_lod = 0
                settings.enable_body_riglogic = True
                settings.enable_face_riglogic = True
                if manifest_path is not None:
                    apply_character_settings(settings, manifest, skeleton)

                set_lod_visibility(asset.character_name, 0)

                self.report({"INFO"}, f"Imported {len(asset.joints)} joints, {len(meshes)} meshes. Metadata object: {dna_empty.name}")
                return {"FINISHED"}
            except Exception as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

    global classes
    classes = [MHB_OT_ImportDNA]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def _ensure_collection(context, name: str):
    import bpy

    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(collection)
    return collection


def _create_dna_empty(context, asset, skeleton, meshes, collection):
    import bpy

    empty = bpy.data.objects.new(f"MH_{asset.character_name}_DNA", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.25
    collection.objects.link(empty)
    empty["mhblender_role"] = "dna_metadata"
    empty["character_name"] = asset.character_name
    empty["dna_path"] = str(asset.path)
    empty["body_dna_path"] = str(asset.path)
    empty["db_name"] = asset.db_name
    empty["lod_count"] = asset.lod_count
    empty["deform_skeleton"] = skeleton.name
    empty["meshes_json"] = json.dumps([mesh.name for mesh in meshes])
    empty["body_meshes_json"] = json.dumps([mesh.name for mesh in meshes])
    empty["summary_json"] = json.dumps(asset.metadata, sort_keys=True)
    return empty
