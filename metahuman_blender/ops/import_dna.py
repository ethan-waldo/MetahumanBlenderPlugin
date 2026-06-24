import json
from pathlib import Path

classes = []


def register():
    import bpy
    from bpy.props import StringProperty
    from bpy_extras.io_utils import ImportHelper

    class MHB_OT_ImportDNA(bpy.types.Operator, ImportHelper):
        bl_idname = "mhblender.import_dna"
        bl_label = "Import MetaHuman DNA"
        bl_description = "Load a MetaHuman DNA file and create the original deform skeleton and available meshes"
        filename_ext = ".dna"
        filter_glob: StringProperty(default="*.dna", options={"HIDDEN"})

        def execute(self, context):
            from ..core.dna_loader import load_dna
            from ..core.lod import set_lod_visibility
            from ..core.mesh_builder import create_mesh_objects
            from ..core.skeleton_builder import create_metahuman_armature
            from ..ui.properties import _binding_paths_from_preferences, get_settings

            try:
                asset = load_dna(self.filepath, binding_paths=_binding_paths_from_preferences(context))
                collection = _ensure_collection(context, f"MH_{asset.character_name}")
                skeleton = create_metahuman_armature(asset, collection=collection)
                meshes = create_mesh_objects(asset, skeleton, collection=collection)
                dna_empty = _create_dna_empty(context, asset, skeleton, meshes, collection)

                settings = get_settings(context)
                settings.dna_path = str(Path(self.filepath))
                settings.character_name = asset.character_name
                settings.deform_skeleton_name = skeleton.name
                settings.current_lod = 0
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
    empty["dna_path"] = str(asset.path)
    empty["db_name"] = asset.db_name
    empty["lod_count"] = asset.lod_count
    empty["deform_skeleton"] = skeleton.name
    empty["meshes_json"] = json.dumps([mesh.name for mesh in meshes])
    empty["summary_json"] = json.dumps(asset.metadata, sort_keys=True)
    return empty
