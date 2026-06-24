from __future__ import annotations

classes = []


def register():
    import bpy

    class MHB_PT_MainPanel(bpy.types.Panel):
        bl_idname = "MHB_PT_main_panel"
        bl_label = "MetaHuman"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"

        def draw(self, context):
            settings = context.scene.metahuman_blender
            layout = self.layout
            layout.operator("mhblender.import_dna", icon="IMPORT")
            layout.operator("mhblender.build_body_rig", icon="ARMATURE_DATA")
            layout.operator("mhblender.evaluate_body_riglogic", icon="MODIFIER")
            layout.operator("mhblender.bake_to_metahuman", icon="ACTION")
            layout.separator()
            layout.prop(settings, "dna_path")
            layout.prop(settings, "character_name")
            layout.prop(settings, "current_lod")
            layout.prop(settings, "deform_skeleton_name")
            layout.prop(settings, "control_rig_name")
            layout.prop(settings, "enable_body_riglogic")

    class MHB_PT_BakePanel(bpy.types.Panel):
        bl_idname = "MHB_PT_bake_panel"
        bl_label = "Bake"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"

        def draw(self, context):
            settings = context.scene.metahuman_blender
            layout = self.layout
            row = layout.row(align=True)
            row.prop(settings, "frame_start")
            row.prop(settings, "frame_end")
            layout.prop(settings, "clear_constraints_after_bake")

    class MHB_PT_ExperimentalPanel(bpy.types.Panel):
        bl_idname = "MHB_PT_experimental_panel"
        bl_label = "Experimental"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):
            layout = self.layout
            layout.operator("mhblender.evaluate_face", icon="MODIFIER")
            layout.operator("mhblender.import_groom_alembic", icon="CURVES")
            layout.operator("mhblender.export_groom_alembic", icon="EXPORT")

    global classes
    classes = [MHB_PT_MainPanel, MHB_PT_BakePanel, MHB_PT_ExperimentalPanel]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
