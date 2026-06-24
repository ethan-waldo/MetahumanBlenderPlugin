# MetaHuman Blender

Greenfield Blender add-on for importing MetaHuman DNA, preserving the original MetaHuman deform skeleton, building a stable Rigify-style animator control layer, and baking animation back to the MetaHuman skeleton for Unreal export.

## Current milestone

Implemented first-pass body workflow modules:

- OpenRigLogic/DNA binding validation.
- DNA metadata extraction for joints, meshes, controls, blend shape channel names, and mesh-channel mappings when available.
- Original MetaHuman deform armature creation from DNA joint hierarchy.
- Mesh object creation from DNA geometry when topology is exposed by the bindings.
- Internal Rigify-style body control rig with stable `CTRL_*` control names.
- Constraint layer from control bones to original MetaHuman bones.
- Optional body RigLogic evaluation layer that reads Rigify-driven MetaHuman bone rotations and applies OpenRigLogic corrective joint outputs to unconstrained corrective bones.
- Visual bake back to the original MetaHuman skeleton.
- Experimental placeholders for facial RigLogic and groom Alembic import/export.

## Install in Blender

1. Add this folder as an add-on or package it as a Blender extension.
2. Open the add-on preferences.
3. Set `OpenRigLogic Python Path` to the folder containing compiled `dna` and `riglogic` Python modules.
4. Press `Validate Setup`.
5. Use `View3D > Sidebar > MetaHuman`.

## Important constraints

The add-on does not replace the MetaHuman skeleton. `MH_<character>_SKEL` remains the deform/export skeleton. `CTRL_<character>_RIG` is only an animator-facing control layer, and final animation is baked back onto the original skeleton.

Body RigLogic is available from the MetaHuman sidebar. Use `Evaluate Body RigLogic` for a manual current-pose update, or enable `Body RigLogic` for live updates while posing. The current layer applies joint corrective outputs; blend shape and animated-map outputs remain part of the later facial/material pass.

## Local OpenRigLogic build

OpenRigLogic is vendored under `third_party/openriglogic` on the `5.8` branch. To rebuild the Blender-compatible Python bindings:

```bash
scripts/build_openriglogic_for_blender.sh
```

Then set the add-on preference to:

```text
/Users/ethanwaldo/Developer/MetahumanBlenderPlugin/build/openriglogic-blender/python
```

More detail lives in [docs/openriglogic_blender_build.md](docs/openriglogic_blender_build.md).
