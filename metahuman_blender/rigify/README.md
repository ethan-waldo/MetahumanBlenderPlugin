# MetaHuman Blender — Rigify feature set

This folder is a [Rigify feature set](https://developer.blender.org/docs/features/animation/rigify/feature_sets/) providing a **body-only** metarig template (no face bones).

## Install

1. Zip the contents of this directory (`__init__.py`, `metarigs/`, `rigs/`) so the archive root contains those folders.
2. In Blender: **Edit → Preferences → Add-ons → Rigify → Install feature set from file**.
3. Choose the ZIP. A **MetaHuman** entry appears under **Add → Armature** metarig templates.

## Use with MetaHuman Blender

The recommended workflow uses **MetaHuman → Build Body Control Rig**, which:

1. Reorients `MH_*_SKEL` from DNA joint matrices.
2. Adds a stock human metarig (or this template), DNA-fits bones to the MetaHuman skeleton.
3. Strips face bones (body-only).
4. Generates the normal Rigify controls and binds Rigify output bones to the MetaHuman skeleton through bone-parented empties with world-space `COPY_TRANSFORMS`.

You do not need to install this feature set for the default build path; it is provided for studios that want a dedicated body-only metarig template in the Rigify menu.
