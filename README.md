# MetaHuman Blender

Greenfield Blender add-on for importing MetaHuman DNA, preserving the original MetaHuman deform skeleton, building a stable internal animator control layer, and baking animation back to the MetaHuman skeleton for Unreal export.

## Current milestone

Production-oriented body and facial workflow modules:

- OpenRigLogic/DNA binding validation.
- **ExportManifest.json** import as the primary DCC package entry point (body DNA, head DNA, texture metadata).
- Original MetaHuman deform armature creation from DNA joint hierarchy.
- Mesh object creation from DNA geometry when topology is exposed by the bindings.
- Internal `CTRL_*` body control rig as the production default.
- Optional experimental Rigify-generated control rig.
- Internal limb IK targets with pole controls.
- Constraint layer from control bones to original MetaHuman bones.
- Body RigLogic evaluation layer for corrective joint outputs.
- Head DNA meshes with blend-shape delta geometry on shape keys (via manifest).
- Faceboard UI bundled at `metahuman_blender/resources/faceboard.json` (shared `MHC_FaceBoard` for all characters).
- Facial RigLogic evaluation from Faceboard GUI controls to joints and shape keys.
- Visual bake back to the original MetaHuman skeleton with pre-bake validation.

## Install in Blender

1. Add this folder as an add-on or package it as a Blender extension.
2. Open the add-on preferences.
3. Set `OpenRigLogic Python Path` to the folder containing compiled `dna` and `riglogic` Python modules.
4. Press `Validate Setup`.
5. Use `View3D > Sidebar > MetaHuman`.

## Workflow: DCC export to Unreal

1. Export a MetaHuman from Unreal with **Export > DCC Export**. The package contains `ExportManifest.json`, `body.dna`, `head.dna`, textures, and masks.
2. **Import Export Manifest** and select `ExportManifest.json`.
3. **Build Body Control Rig** using the default **Internal CTRL_*** control type.
4. Faceboard setup runs automatically during manifest import. Use **Setup Faceboard** to rebuild it if needed.
5. Animate body and face controls. Enable RigLogic toggles for live correctives if desired.
6. Bake and export the baked `MH_<character>_SKEL` for Unreal re-import.

The sidebar **Export Manifest** field is the single source of truth for DNA and texture paths. Individual body/head DNA fields are resolved from the manifest automatically.

## Important constraints

The add-on does not replace the MetaHuman skeleton. `MH_<character>_SKEL` remains the deform/export skeleton. `CTRL_<character>_RIG` is only an animator-facing control layer, and final animation is baked back onto the original skeleton.

Use the **Internal CTRL_*** control rig for production body animation. The Rigify path is experimental and may not evaluate correctly on Blender 5.2.

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
