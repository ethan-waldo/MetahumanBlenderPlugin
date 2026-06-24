import bpy

from bpy.props import StringProperty


class MHB_OT_SetupMaterials(bpy.types.Operator):
    bl_idname = "mhblender.setup_materials"
    bl_label = "Setup Materials"
    bl_description = "Create and assign MetaHuman materials from the export manifest texture maps"
    bl_options = {"REGISTER", "UNDO"}

    character_name: StringProperty(name="Character Name", default="")

    def execute(self, context):
        from ..core.character_import import resolve_character_paths
        from ..core.export_manifest import ExportManifestError, load_export_manifest
        from ..core.material_builder import setup_materials_for_meshes
        from ..ui.properties import get_settings

        settings = get_settings(context)
        paths = resolve_character_paths(settings)
        character_name = self.character_name or paths["character_name"] or settings.character_name
        if not character_name:
            self.report({"ERROR"}, "No character name found. Import an Export Manifest first.")
            return {"CANCELLED"}

        manifest_path = paths["export_manifest_path"]
        if not manifest_path:
            self.report({"ERROR"}, "No export manifest path found. Import an Export Manifest first.")
            return {"CANCELLED"}

        try:
            manifest = load_export_manifest(manifest_path)
        except ExportManifestError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        mesh_objects = [
            obj
            for obj in context.scene.objects
            if obj.type == "MESH" and obj.get("mhblender_character") == character_name
        ]
        if not mesh_objects:
            self.report({"ERROR"}, f"No MetaHuman meshes found for {character_name}")
            return {"CANCELLED"}

        result = setup_materials_for_meshes(
            mesh_objects,
            character_name,
            manifest.map_files,
            mask_files=manifest.mask_files,
        )
        message = (
            f"Assigned {result.material_count} materials to {result.assigned_mesh_count} meshes"
        )
        if result.skipped_mesh_count:
            message += f" ({result.skipped_mesh_count} skipped)"
        self.report({"INFO"}, message)
        return {"FINISHED"}


classes = (MHB_OT_SetupMaterials,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
