import logging

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

LOGGER = logging.getLogger(__name__)


class MHB_OT_ImportExportManifest(bpy.types.Operator, ImportHelper):
    bl_idname = "mhblender.import_export_manifest"
    bl_label = "Import Export Manifest"
    bl_description = "Import a MetaHuman DCC export package from ExportManifest.json (body, head, textures metadata)"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob = StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        from ..core.character_import import apply_character_settings, import_character_from_manifest
        from ..core.export_manifest import ExportManifestError, load_export_manifest
        from ..ui.properties import _binding_paths_from_preferences, get_settings

        if not self.filepath:
            self.report({"ERROR"}, "Select ExportManifest.json")
            return {"CANCELLED"}

        filepath = bpy.path.abspath(self.filepath)

        try:
            manifest = load_export_manifest(filepath)
            imported_manifest, skeleton, body_meshes, head_meshes, metadata_empty, head_warning, material_result = import_character_from_manifest(
                context,
                manifest.path,
                binding_paths=_binding_paths_from_preferences(context),
            )
            settings = get_settings(context)
            apply_character_settings(settings, imported_manifest, skeleton)

            message = (
                f"Imported {manifest.character_name} from ExportManifest: "
                f"{len(body_meshes)} body meshes"
            )
            if head_meshes:
                message += f", {len(head_meshes)} head meshes"
            elif head_warning:
                message += f" (head import warning: {head_warning})"
            if manifest.map_files:
                message += f", {len(manifest.map_files)} texture maps"
            if material_result.material_count:
                message += f", materials applied ({material_result.material_count} parts, {material_result.assigned_mesh_count} meshes)"
            elif manifest.map_files:
                message += ", texture maps found but no materials could be assigned"
            message += f". Metadata: {metadata_empty.name}"

            face_message = _setup_face_gui_sliders(context, imported_manifest, settings)
            if face_message:
                message += f"; {face_message}"

            _evaluate_riglogic(context, settings)

            self.report({"INFO"}, message)
            return {"FINISHED"}
        except ExportManifestError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            from ..riglogic.bindings import validate_bindings

            LOGGER.exception("ExportManifest import failed")
            message = str(exc)
            if "OpenRigLogic" in message or "dna" in message.lower():
                status = validate_bindings(_binding_paths_from_preferences(context))
                message = (
                    f"{message}. Set OpenRigLogic Python Path in add-on preferences "
                    f"or build bindings with scripts/build_openriglogic_for_blender.sh. "
                    f"Searched: {', '.join(status.search_paths) or 'no paths'}"
                )
            self.report({"ERROR"}, message)
            return {"CANCELLED"}


classes = (MHB_OT_ImportExportManifest,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def _evaluate_riglogic(context, settings) -> None:
    if not settings.enable_body_riglogic and not settings.enable_face_riglogic:
        return

    try:
        if settings.enable_body_riglogic:
            from ..riglogic.body_evaluator import evaluate_body_for_context

            result = evaluate_body_for_context(context)
            settings.body_riglogic_last_error = "" if result.ok else result.message
        if settings.enable_face_riglogic:
            from ..riglogic.evaluator import evaluate_face_for_context

            result = evaluate_face_for_context(context)
            settings.face_riglogic_last_error = "" if result.ok else result.message
    except Exception as exc:
        LOGGER.warning("Initial RigLogic evaluation failed", exc_info=True)
        message = str(exc)
        if settings.enable_body_riglogic:
            settings.body_riglogic_last_error = message
        if settings.enable_face_riglogic:
            settings.face_riglogic_last_error = message


def _setup_face_gui_sliders(context, manifest, settings) -> str:
    from ..core.character_import import resolve_character_paths
    from ..ui.face_sliders import sync_face_gui_controls
    from ..ui.properties import _binding_paths_from_preferences

    paths = resolve_character_paths(settings)
    head_dna_path = paths["head_dna_path"]
    if not head_dna_path:
        return ""

    try:
        count = sync_face_gui_controls(settings, head_dna_path, binding_paths=_binding_paths_from_preferences(context))
        return f"{count} face GUI sliders loaded (see Face Controls panel)"
    except Exception as exc:
        LOGGER.exception("Face GUI slider setup failed")
        return f"Face slider setup failed: {exc}"
