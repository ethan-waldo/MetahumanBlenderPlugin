classes = []


def register():
    import bpy
    from bpy.props import StringProperty
    from bpy_extras.io_utils import ExportHelper, ImportHelper

    class MHB_OT_ImportGroomAlembic(bpy.types.Operator, ImportHelper):
        bl_idname = "mhblender.import_groom_alembic"
        bl_label = "Import Groom Alembic"
        bl_description = "Import Alembic groom data as Blender curves where supported"
        filename_ext = ".abc"
        filter_glob: StringProperty(default="*.abc", options={"HIDDEN"})

        def execute(self, context):
            from ..groom.alembic_import import import_groom_alembic

            count = import_groom_alembic(self.filepath)
            self.report({"INFO"}, f"Imported {count} groom object(s)")
            return {"FINISHED"}

    class MHB_OT_ExportGroomAlembic(bpy.types.Operator, ExportHelper):
        bl_idname = "mhblender.export_groom_alembic"
        bl_label = "Export Groom Alembic"
        bl_description = "Export selected groom curves to Alembic"
        filename_ext = ".abc"
        filter_glob: StringProperty(default="*.abc", options={"HIDDEN"})

        def execute(self, context):
            from ..groom.curves_export import export_groom_alembic

            export_groom_alembic(self.filepath)
            self.report({"INFO"}, "Exported selected groom curves")
            return {"FINISHED"}

    global classes
    classes = [MHB_OT_ImportGroomAlembic, MHB_OT_ExportGroomAlembic]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
