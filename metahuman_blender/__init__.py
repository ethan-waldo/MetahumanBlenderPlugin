bl_info = {
    "name": "MetaHuman Blender",
    "author": "MetaHuman Blender Contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > MetaHuman",
    "description": "Import MetaHuman DNA, create a control rig, and bake animation to the original skeleton.",
    "category": "Animation",
}

from . import addon


def register():
    addon.register()


def unregister():
    addon.unregister()
