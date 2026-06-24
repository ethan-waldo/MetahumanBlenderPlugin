from __future__ import annotations

import re


def infer_lod_index(name: str, fallback: int = 0) -> int:
    match = re.search(r"(?:^|_)lod(\d+)(?:_|$)", name.lower())
    return int(match.group(1)) if match else fallback


def set_lod_visibility(character_name: str, lod_index: int) -> int:
    import bpy

    changed = 0
    for obj in bpy.data.objects:
        if obj.get("mhblender_role") != "metahuman_mesh":
            continue
        if character_name and obj.get("mhblender_character") != character_name:
            continue
        obj_lod = int(obj.get("mhblender_lod", 0))
        hidden = obj_lod != lod_index
        obj.hide_viewport = hidden
        obj.hide_render = hidden
        changed += 1
    return changed
