from __future__ import annotations

import logging

classes = []

LOGGER = logging.getLogger(__name__)


def register():
    import bpy

    class MHB_OT_ImportFaceboard(bpy.types.Operator):
        bl_idname = "mhblender.import_faceboard"
        bl_label = "Setup Faceboard"
        bl_description = "Build the bundled MetaHuman Faceboard (MHC_FaceBoard) and link it to the active character"

        def execute(self, context):
            from ..core.character_assembly import character_from_empty, find_character_empty, save_character_to_empty
            from ..core.character_import import resolve_character_paths
            from ..core.faceboard_constants import FACEBOARD_OBJECT_NAME
            from ..core.faceboard_json import FaceboardJsonError, bundled_faceboard_json_path
            from ..rig.face_controls import link_faceboard_to_character
            from ..ui.properties import get_settings

            settings = get_settings(context)
            character_name = settings.character_name
            if not character_name:
                self.report({"ERROR"}, "Import ExportManifest.json first so a character name is set.")
                return {"CANCELLED"}

            paths = resolve_character_paths(settings)
            head_dna_path = paths["head_dna_path"]
            if not head_dna_path:
                self.report({"ERROR"}, "Head DNA path is missing. Import ExportManifest.json first.")
                return {"CANCELLED"}

            try:
                json_path = str(bundled_faceboard_json_path())
                faceboard, mapped = import_faceboard_for_character(
                    context,
                    character_name,
                    head_dna_path,
                )
            except FaceboardJsonError as exc:
                LOGGER.exception("Bundled faceboard missing")
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}
            except Exception as exc:
                LOGGER.exception("Faceboard import failed")
                self.report({"ERROR"}, f"Faceboard import failed: {exc}")
                return {"CANCELLED"}

            settings.faceboard_rig_name = FACEBOARD_OBJECT_NAME
            settings.faceboard_json_path = json_path

            dna_empty = find_character_empty(character_name)
            if dna_empty is not None:
                character = character_from_empty(dna_empty)
                character.faceboard_rig = FACEBOARD_OBJECT_NAME
                save_character_to_empty(dna_empty, character)

            self.report({"INFO"}, f"Setup {faceboard.name}; mapped {mapped} GUI controls from bundled faceboard.json.")
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_ImportFaceboard]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def import_faceboard_for_character(context, character_name: str, head_dna_path: str, collection=None):
    from ..core.character_assembly import character_from_empty, find_character_empty, save_character_to_empty
    from ..core.faceboard_constants import FACEBOARD_OBJECT_NAME
    from ..core.faceboard_json import bundled_faceboard_json_path
    from ..rig.face_controls import link_faceboard_to_character
    from ..ui.properties import get_settings

    json_path = str(bundled_faceboard_json_path())
    faceboard = import_faceboard_from_json(json_path)
    mapped = link_faceboard_to_character(faceboard, character_name, head_dna_path)

    settings = get_settings(context)
    settings.faceboard_rig_name = FACEBOARD_OBJECT_NAME
    settings.faceboard_json_path = json_path

    dna_empty = find_character_empty(character_name)
    if dna_empty is not None:
        character = character_from_empty(dna_empty)
        character.faceboard_rig = FACEBOARD_OBJECT_NAME
        save_character_to_empty(dna_empty, character)

    return faceboard, mapped


def import_faceboard_from_json(json_path: str):
    import importlib

    from ..rig import faceboard_builder

    importlib.reload(faceboard_builder)
    _remove_existing_faceboards()
    faceboard, _definition = faceboard_builder.build_faceboard_from_json(json_path)
    return faceboard


def _remove_existing_faceboards() -> None:
    import bpy

    from ..core.faceboard_constants import FACEBOARD_OBJECT_NAME

    for name in (FACEBOARD_OBJECT_NAME, "MHC_FaceBoard_Panel"):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)

    for obj in list(bpy.data.objects):
        if obj.type != "ARMATURE":
            continue
        if obj.name.startswith("FaceBoard_"):
            bpy.data.objects.remove(obj, do_unlink=True)
