"""MetaHuman body-only Rigify metarig template.

Install this feature set from Rigify preferences (Install feature set from file)
using a ZIP of the ``metahuman_blender/rigify`` package root, or symlink it into
Blender's rigify feature sets path.

After adding the template, DNA-fit bones with MetaHuman > Build Body Control Rig.
"""

from __future__ import annotations

rigify_info = {
    "name": "MetaHuman",
    "description": "Body-only MetaHuman metarig template for Rigify (no face bones).\n"
    "Use MetaHuman Blender Build Body Control Rig to DNA-fit and generate controls.",
    "author": "MetaHuman Blender",
    "warning": "Metarig must be fitted to your MetaHuman skeleton before generating.",
    "link": "https://github.com/ethanwaldo/MetahumanBlenderPlugin",
    "doc_url": "",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "feature_sets": [],
}


def register():
    pass


def unregister():
    pass
