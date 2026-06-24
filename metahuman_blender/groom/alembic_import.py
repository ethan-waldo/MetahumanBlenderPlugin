from __future__ import annotations


def import_groom_alembic(filepath: str) -> int:
    import bpy

    before = set(bpy.data.objects)
    bpy.ops.wm.alembic_import(filepath=filepath)
    imported = [obj for obj in bpy.data.objects if obj not in before]
    for obj in imported:
        obj["mhblender_role"] = "groom"
    return len(imported)
