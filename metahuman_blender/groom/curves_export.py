from __future__ import annotations


def export_groom_alembic(filepath: str) -> None:
    import bpy

    bpy.ops.wm.alembic_export(filepath=filepath, selected=True)
