from __future__ import annotations

classes = []


def _draw_body_rig_status(layout, settings):
    import bpy

    control = bpy.data.objects.get(settings.control_rig_name) if settings.control_rig_name else None
    skeleton = bpy.data.objects.get(settings.deform_skeleton_name) if settings.deform_skeleton_name else None

    if control is None or control.type != "ARMATURE":
        layout.label(text="No body control rig built yet", icon="INFO")
        layout.label(text="Use Build Body Control Rig above")
        layout.label(text="Requires Rigify add-on enabled", icon="INFO")
        return

    control_type = control.get("mhblender_control_type", "rigify")
    layout.label(text=f"Rigify body rig ({control_type})", icon="ARMATURE_DATA")
    layout.label(text="Animate the normal Rigify controls", icon="POSE_HLT")
    layout.label(text="Face animation uses the Face Controls panel", icon="INFO")
    layout.prop(settings, "control_rig_name", text="Control Rig")
    if skeleton is not None:
        layout.prop(settings, "deform_skeleton_name", text="Deform Skeleton")

    metarig_name = control.get("mhblender_metarig") or skeleton.get("mhblender_metarig") if skeleton else None
    if not metarig_name and skeleton is not None:
        for obj in bpy.data.objects:
            if obj.get("mhblender_role") == "rigify_metarig" and obj.get("mhblender_deform_skeleton") == skeleton.name:
                metarig_name = obj.name
                break
    if metarig_name:
        layout.label(text=f"Metarig: {metarig_name}", icon="OUTLINER_OB_ARMATURE")

    constraint_count = control.get("mhblender_constraint_count")
    if constraint_count is None and skeleton is not None:
        from ..core.rig_mapping import rig_maps_from_json

        constraint_count = len(rig_maps_from_json(skeleton.get("mhblender_rig_map", "")))
    if constraint_count is not None:
        layout.label(text=f"Rigify output bindings: {constraint_count}", icon="CONSTRAINT")

    missing = control.get("mhblender_missing_controls", "")
    if missing:
        missing_items = [item.strip() for item in missing.split(",") if item.strip()]
        box = layout.box()
        box.label(text=f"Missing Rigify output mappings: {len(missing_items)}", icon="ERROR")
        for item in missing_items[:8]:
            box.label(text=item)
        if len(missing_items) > 8:
            box.label(text=f"... and {len(missing_items) - 8} more")


def _draw_body_rig_controls(layout, context):
    import bpy

    from ..rig.body_constants import RIGIFY_MAJOR_CONTROL_GROUPS, RIGIFY_MINOR_CONTROL_GROUPS

    settings = context.scene.metahuman_blender
    control = bpy.data.objects.get(settings.control_rig_name) if settings.control_rig_name else None
    if control is None or control.type != "ARMATURE":
        layout.label(text="No Rigify body rig built yet", icon="INFO")
        return

    row = layout.row(align=True)
    row.operator("mhblender.select_body_rig", icon="ARMATURE_DATA")
    row.prop(control, "show_in_front", text="", icon="XRAY")
    row.prop(settings, "show_body_corrective_bones", text="", icon="BONE_DATA", toggle=True)

    if not hasattr(control.data, "collections"):
        layout.label(text="Rebuild the body rig to enable grouped controls", icon="INFO")
        return

    _draw_rigify_limb_switches(layout, control)
    _draw_rigify_control_groups(layout, control, "Major Controls", RIGIFY_MAJOR_CONTROL_GROUPS)
    _draw_rigify_control_groups(layout, control, "Minor Controls", RIGIFY_MINOR_CONTROL_GROUPS)


def _draw_rigify_control_groups(layout, control, title, groups) -> None:
    box = layout.box()
    box.label(text=title, icon="GROUP_BONE")
    column = box.column(align=True)
    any_found = False
    for label, collection_names in groups:
        collections = getattr(control.data, "collections", None)
        if collections is None:
            continue
        present = [collections.get(name) for name in collection_names if collections.get(name) is not None]
        if not present:
            continue
        any_found = True
        row = column.row(align=True)
        row.label(text=label)
        visible = all(item.is_visible for item in present)
        toggle = row.operator(
            "mhblender.toggle_rigify_control_group",
            text="Hide" if visible else "Show",
            depress=visible,
        )
        toggle.group_label = label
        toggle.visible = not visible
    if not any_found:
        box.label(text="No grouped controls found on this rig", icon="INFO")


def _draw_rigify_limb_switches(layout, control) -> None:
    from ..rig.body_constants import RIGIFY_IK_FK_PAIRS, RIGIFY_LIMB_PARENTS
    from ..rig.rigify_adapter import get_limb_mode

    box = layout.box()
    box.label(text="IK / FK", icon="CON_ARMATURE")
    any_found = False
    for label, _, _ in RIGIFY_IK_FK_PAIRS:
        if label not in RIGIFY_LIMB_PARENTS:
            continue
        any_found = True
        mode = get_limb_mode(control, label)
        row = box.row(align=True)
        row.label(text=label)
        ik = row.operator("mhblender.set_rigify_limb_mode", text="IK", depress=mode == "IK")
        ik.limb_label = label
        ik.mode = "IK"
        fk = row.operator("mhblender.set_rigify_limb_mode", text="FK", depress=mode == "FK")
        fk.limb_label = label
        fk.mode = "FK"
    if not any_found:
        box.label(text="No limb IK/FK controls found", icon="INFO")


def register():
    import bpy

    from .face_sliders import draw_face_controls_panel

    class MHB_OT_SelectBodyRig(bpy.types.Operator):
        bl_idname = "mhblender.select_body_rig"
        bl_label = "Select Body Rig"
        bl_description = "Select the generated Rigify body rig and enter Pose mode"

        def execute(self, context):
            settings = context.scene.metahuman_blender
            control = bpy.data.objects.get(settings.control_rig_name) if settings.control_rig_name else None
            if control is None or control.type != "ARMATURE":
                self.report({"ERROR"}, "No Rigify body rig found.")
                return {"CANCELLED"}
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT")
            for obj in context.view_layer.objects:
                obj.select_set(False)
            control.hide_viewport = False
            control.hide_select = False
            control.select_set(True)
            context.view_layer.objects.active = control
            bpy.ops.object.mode_set(mode="POSE")
            return {"FINISHED"}

    class MHB_OT_SetRigifyLimbMode(bpy.types.Operator):
        bl_idname = "mhblender.set_rigify_limb_mode"
        bl_label = "Set Rigify Limb Mode"
        bl_description = "Switch a limb between Rigify IK and FK control collections"

        limb_label: bpy.props.StringProperty(name="Limb", default="")
        mode: bpy.props.EnumProperty(name="Mode", items=(("IK", "IK", ""), ("FK", "FK", "")))

        def execute(self, context):
            from ..rig.rigify_adapter import set_limb_mode

            settings = context.scene.metahuman_blender
            control = bpy.data.objects.get(settings.control_rig_name) if settings.control_rig_name else None
            if control is None:
                self.report({"ERROR"}, "No Rigify body rig found.")
                return {"CANCELLED"}
            if not set_limb_mode(control, self.limb_label, self.mode):
                self.report({"WARNING"}, f"Could not switch {self.limb_label} to {self.mode}.")
                return {"CANCELLED"}
            return {"FINISHED"}

    class MHB_OT_ToggleRigifyControlGroup(bpy.types.Operator):
        bl_idname = "mhblender.toggle_rigify_control_group"
        bl_label = "Toggle Rigify Control Group"
        bl_description = "Show or hide a grouped set of Rigify animator controls"

        group_label: bpy.props.StringProperty(name="Group", default="")
        visible: bpy.props.BoolProperty(name="Visible", default=True)

        def execute(self, context):
            from ..rig.body_constants import RIGIFY_MAJOR_CONTROL_GROUPS, RIGIFY_MINOR_CONTROL_GROUPS
            from ..rig.rigify_adapter import set_control_group_visibility

            settings = context.scene.metahuman_blender
            control = bpy.data.objects.get(settings.control_rig_name) if settings.control_rig_name else None
            if control is None:
                self.report({"ERROR"}, "No Rigify body rig found.")
                return {"CANCELLED"}

            group_names = None
            for label, names in (*RIGIFY_MAJOR_CONTROL_GROUPS, *RIGIFY_MINOR_CONTROL_GROUPS):
                if label == self.group_label:
                    group_names = names
                    break
            if group_names is None:
                self.report({"ERROR"}, f"Unknown control group: {self.group_label}")
                return {"CANCELLED"}
            set_control_group_visibility(control, group_names, self.visible)
            return {"FINISHED"}

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
            layout.operator("mhblender.validate_body_rig", icon="CHECKMARK")
            layout.operator("mhblender.evaluate_body_riglogic", icon="MODIFIER")
            layout.operator("mhblender.evaluate_face", icon="MODIFIER")
            layout.operator("mhblender.bake_to_metahuman", icon="ACTION")
            layout.separator()
            layout.label(text="Body: Rigify control rig  |  Face: Face Controls panel", icon="INFO")
            layout.prop(settings, "character_name")
            layout.prop(settings, "current_lod")
            layout.prop(settings, "enable_body_riglogic")
            layout.prop(settings, "show_body_corrective_bones", toggle=True)
            if settings.body_riglogic_last_error:
                layout.label(text=settings.body_riglogic_last_error, icon="ERROR")
            layout.prop(settings, "enable_face_riglogic")
            if settings.face_riglogic_last_error:
                layout.label(text=settings.face_riglogic_last_error, icon="ERROR")

    class MHB_PT_BodyRigStatus(bpy.types.Panel):
        bl_idname = "MHB_PT_body_rig_status"
        bl_label = "Body Rig"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):
            _draw_body_rig_status(self.layout, context.scene.metahuman_blender)

    class MHB_PT_BodyRigControls(bpy.types.Panel):
        bl_idname = "MHB_PT_body_rig_controls"
        bl_label = "Body Rig Controls"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "MetaHuman"
        bl_parent_id = "MHB_PT_main_panel"

        def draw(self, context):
            _draw_body_rig_controls(self.layout, context)

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
            layout.separator()
            layout.label(text="3D Faceboard (experimental):")
            layout.operator("mhblender.import_faceboard", icon="OUTLINER_OB_ARMATURE", text="Setup 3D Faceboard")
            layout.prop(settings, "faceboard_rig_name")
            layout.operator("mhblender.import_groom_alembic", icon="CURVES")
            layout.operator("mhblender.export_groom_alembic", icon="EXPORT")

    global classes
    classes = [
        MHB_OT_SelectBodyRig,
        MHB_OT_SetRigifyLimbMode,
        MHB_OT_ToggleRigifyControlGroup,
        MHB_PT_MainPanel,
        MHB_PT_BodyRigStatus,
        MHB_PT_BodyRigControls,
        MHB_PT_FaceSliders,
        MHB_PT_BakePanel,
        MHB_PT_ExperimentalPanel,
    ]
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
