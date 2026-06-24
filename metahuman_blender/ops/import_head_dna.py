from __future__ import annotations

from pathlib import Path

classes = []


def register():
    import bpy
    from bpy.props import StringProperty
    from bpy_extras.io_utils import ImportHelper

    class MHB_OT_ImportHeadDNA(bpy.types.Operator, ImportHelper):
        bl_idname = "mhblender.import_head_dna"
        bl_label = "Import Head DNA"
        bl_description = "Load head.dna meshes and shape keys onto the existing MetaHuman deform skeleton"
        filename_ext = ".dna"
        filter_glob: StringProperty(default="*.dna", options={"HIDDEN"})

        def execute(self, context):
            from ..core.character_assembly import character_from_empty, find_character_empty, save_character_to_empty
            from ..core.dna_loader import load_dna
            from ..core.mesh_builder import create_head_mesh_objects
            from ..ui.properties import _binding_paths_from_preferences, get_settings
            from .build_body_rig import _find_skeleton

            settings = get_settings(context)
            skeleton = _find_skeleton(context, settings.deform_skeleton_name)
            if skeleton is None:
                self.report({"ERROR"}, "Import body DNA and create a deform skeleton before importing head DNA.")
                return {"CANCELLED"}

            try:
                asset = load_dna(self.filepath, binding_paths=_binding_paths_from_preferences(context))
                character_name = settings.character_name or skeleton.get("mhblender_character") or skeleton.name.removeprefix("MH_").removesuffix("_SKEL")
                collection = skeleton.users_collection[0] if skeleton.users_collection else context.collection
                meshes = create_head_mesh_objects(
                    asset,
                    skeleton,
                    collection=collection,
                    character_name=character_name,
                    binding_paths=_binding_paths_from_preferences(context),
                )

                dna_empty = find_character_empty(character_name)
                if dna_empty is not None:
                    character = character_from_empty(dna_empty)
                    character.head_dna_path = str(Path(self.filepath))
                    character.head_meshes = list(dict.fromkeys(character.head_meshes + [mesh.name for mesh in meshes]))
                    character.deform_skeleton = skeleton.name
                    save_character_to_empty(dna_empty, character)

                skeleton["mhblender_head_dna_path"] = str(Path(self.filepath))
                settings.head_dna_path = str(Path(self.filepath))
                settings.character_name = character_name

                from ..ui.face_sliders import sync_face_gui_controls

                try:
                    sync_face_gui_controls(settings, str(Path(self.filepath)), binding_paths=_binding_paths_from_preferences(context))
                except Exception:
                    pass

                self.report({"INFO"}, f"Imported {len(meshes)} head meshes with {len(asset.blend_shapes)} blend-shape channels.")
                return {"FINISHED"}
            except Exception as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

    global classes
    classes = [MHB_OT_ImportHeadDNA]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
