from __future__ import annotations

classes = []


def register():
    import bpy

    from .face_sliders import draw_face_controls_panel

    class MHB_PT_MainPanel(bpy.types.Panel):
        bl_idname = "MHB_PT_main_panel"
        bl_label = "MetaHuman"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"

        def draw(self, context):
            settings = context.scene.metahuman_blender
            layout = self.layout
            layout.operator("mhblender.import_export_manifest", icon="IMPORT")
            layout.operator("mhblender.setup_materials", icon="MATERIAL")
            layout.operator("mhblender.build_body_rig", icon="ARMATURE_DATA")
            layout.operator("mhblender.evaluate_body_riglogic", icon="MODIFIER")
            layout.operator("mhblender.evaluate_face", icon="MODIFIER")
            layout.operator("mhblender.bake_to_metahuman", icon="ACTION")
            layout.separator()
            layout.prop(settings, "control_rig_type")
            if settings.control_rig_type == "RIGIFY":
                layout.label(text="Rigify is experimental on Blender 5.2", icon="ERROR")
            layout.prop(settings, "character_name")
            layout.prop(settings, "current_lod")
            layout.prop(settings, "deform_skeleton_name")
            layout.prop(settings, "control_rig_name")
            layout.prop(settings, "enable_body_riglogic")
            if settings.body_riglogic_last_error:
                layout.label(text=settings.body_riglogic_last_error, icon="ERROR")
            layout.prop(settings, "enable_face_riglogic")
            if settings.face_riglogic_last_error:
                layout.label(text=settings.face_riglogic_last_error, icon="ERROR")

    class MHB_PT_FaceSliders(bpy.types.Panel):
        bl_idname = "MHB_PT_face_sliders"
        bl_label = "Face Controls"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):
            draw_face_controls_panel(self.layout, context)

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
            if settings.bake_last_report:
                layout.label(text=settings.bake_last_report, icon="INFO")

    class MHB_PT_ExperimentalPanel(bpy.types.Panel):
        bl_idname = "MHB_PT_experimental_panel"
        bl_label = "Experimental"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):
            settings = context.scene.metahuman_blender
            layout = self.layout
            layout.label(text="Legacy per-file DNA import:")
            layout.operator("mhblender.import_dna", icon="IMPORT")
            layout.operator("mhblender.import_head_dna", icon="IMPORT")
            layout.separator()
            layout.prop(settings, "dna_path")
            layout.prop(settings, "head_dna_path")
            layout.label(text="Use Internal control rig for production body animation.")
            layout.separator()
            layout.label(text="3D Faceboard (experimental):")
            layout.operator("mhblender.import_faceboard", icon="OUTLINER_OB_ARMATURE", text="Setup 3D Faceboard")
            layout.prop(settings, "faceboard_rig_name")
            layout.operator("mhblender.import_groom_alembic", icon="CURVES")
            layout.operator("mhblender.export_groom_alembic", icon="EXPORT")

    global classes
    classes = [MHB_PT_MainPanel, MHB_PT_FaceSliders, MHB_PT_BakePanel, MHB_PT_ExperimentalPanel]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
