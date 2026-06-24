from __future__ import annotations

from .constraint_builder import clear_metahuman_constraints, mute_metahuman_constraints
from .scene_model import BakeSettings


def bake_to_metahuman_skeleton(mh_armature, settings: BakeSettings) -> None:
    import bpy

    previous_active = bpy.context.view_layer.objects.active
    previous_selection = list(bpy.context.selected_objects)

    bpy.ops.object.mode_set(mode="OBJECT")
    for obj in previous_selection:
        obj.select_set(False)
    mh_armature.select_set(True)
    bpy.context.view_layer.objects.active = mh_armature
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.nla.bake(
        frame_start=settings.frame_start,
        frame_end=settings.frame_end,
        only_selected=False,
        visual_keying=settings.visual_keying,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=True,
        bake_types={"POSE"},
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    if settings.clear_constraints_after_bake:
        clear_metahuman_constraints(mh_armature)
    else:
        mute_metahuman_constraints(mh_armature, True)

    mh_armature.select_set(False)
    for obj in previous_selection:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    if previous_active and previous_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = previous_active
