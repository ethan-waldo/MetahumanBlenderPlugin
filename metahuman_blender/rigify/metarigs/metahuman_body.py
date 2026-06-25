"""Body-only humanoid metarig (no face). Positions are placeholders; MetaHuman Build Body Control Rig DNA-fits bones."""

from __future__ import annotations

_SPINE_CHAIN = ("spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006")
_ARM_LEFT = ("shoulder.L", "upper_arm.L", "forearm.L", "hand.L")
_ARM_RIGHT = ("shoulder.R", "upper_arm.R", "forearm.R", "hand.R")
_LEG_LEFT = ("pelvis.L", "thigh.L", "shin.L", "foot.L", "toe.L")
_LEG_RIGHT = ("pelvis.R", "thigh.R", "shin.R", "foot.R", "toe.R")


def _add_chain(edit_bones, names, head_start=(0.0, 0.0, 0.0), step=(0.0, 0.0, 0.15)):
    import bpy

    parent = None
    head = list(head_start)
    created = {}
    for name in names:
        bone = edit_bones.new(name)
        bone.head = tuple(head)
        bone.tail = (head[0] + step[0], head[1] + step[1], head[2] + step[2])
        if parent is not None:
            bone.parent = parent
        parent = bone
        created[name] = bone
        head[0] += step[0]
        head[1] += step[1]
        head[2] += step[2]
    return created


def _set_rigify_type(pose_bone, rig_type: str) -> None:
    pose_bone.rigify_type = rig_type


def create_sample(obj):
    import bpy

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = obj.data.edit_bones
    while edit_bones:
        edit_bones.remove(edit_bones[0])

    root = edit_bones.new("root")
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 0.1)

    spine = _add_chain(edit_bones, _SPINE_CHAIN, head_start=(0.0, 0.0, 0.1), step=(0.0, 0.0, 0.12))
    spine["spine"].parent = root

    _add_chain(edit_bones, _ARM_LEFT, head_start=(0.05, 0.0, 1.0), step=(0.12, 0.0, 0.0))
    _add_chain(edit_bones, _ARM_RIGHT, head_start=(-0.05, 0.0, 1.0), step=(-0.12, 0.0, 0.0))
    edit_bones["shoulder.L"].parent = spine["spine.003"]
    edit_bones["shoulder.R"].parent = spine["spine.003"]

    _add_chain(edit_bones, _LEG_LEFT, head_start=(0.08, 0.0, 0.1), step=(0.0, 0.0, -0.18))
    _add_chain(edit_bones, _LEG_RIGHT, head_start=(-0.08, 0.0, 0.1), step=(0.0, 0.0, -0.18))
    edit_bones["pelvis.L"].parent = spine["spine"]
    edit_bones["pelvis.R"].parent = spine["spine"]

    bpy.ops.object.mode_set(mode="OBJECT")
    for name in _SPINE_CHAIN:
        bone = obj.pose.bones.get(name)
        if bone is not None:
            _set_rigify_type(bone, "spines.basic_spine" if name == "spine" else "")
    for side in (".L", ".R"):
        upper = obj.pose.bones.get(f"upper_arm{side}")
        if upper is not None:
            _set_rigify_type(upper, "limbs.arm")
        thigh = obj.pose.bones.get(f"thigh{side}")
        if thigh is not None:
            _set_rigify_type(thigh, "limbs.leg")
