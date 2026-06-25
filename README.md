# MetaHuman Blender

Blender add-on for importing MetaHuman DNA, preserving the original MetaHuman deform skeleton, building a Rigify animator control layer, and baking animation back to the MetaHuman skeleton for Unreal export.

## Current milestone

Production-oriented body and facial workflow modules:

- OpenRigLogic/DNA binding validation.
- **ExportManifest.json** import as the primary DCC package entry point (body DNA, head DNA, texture metadata).
- DNA matrix-accurate MetaHuman deform armature from joint neutral transforms.
- Mesh object creation from DNA geometry when topology is exposed by the bindings.
- **Rigify** body control rig with Rigify-output→empty→MH binding (Poly Hammer Character Control Rig pattern).
- Optional MetaHuman Rigify feature set template (`metahuman_blender/rigify/`).
- Body RigLogic evaluation layer for corrective joint outputs.
- Head DNA meshes with blend-shape delta geometry on shape keys (via manifest).
- Faceboard UI bundled at `metahuman_blender/resources/faceboard.json` (shared `MHC_FaceBoard` for all characters).
- Facial RigLogic evaluation from Faceboard GUI controls to joints and shape keys.
- Visual bake back to the original MetaHuman skeleton with pre-bake validation.

## Install in Blender

1. Add this folder as an add-on or package it as a Blender extension.
2. **Enable the Rigify add-on** (Preferences → Add-ons → Rigify).
3. Open the MetaHuman add-on preferences.
4. Set `OpenRigLogic Python Path` to the folder containing compiled `dna` and `riglogic` Python modules.
5. Press `Validate Setup`.
6. Use `View3D > Sidebar > MetaHuman`.

## Workflow: DCC export to Unreal

1. Export a MetaHuman from Unreal with **Export > DCC Export**. The package contains `ExportManifest.json`, `body.dna`, `head.dna`, textures, and masks.
2. **Import Export Manifest** and select `ExportManifest.json`.
3. **Build Body Control Rig** — requires Rigify. Creates a DNA-fitted metarig, generates Rigify FK/IK controls, and binds them to the MetaHuman skeleton.
4. Faceboard setup runs automatically during manifest import. Use **Setup Faceboard** to rebuild it if needed.
5. Animate Rigify body controls and Face Controls panel. Enable RigLogic toggles for live correctives if desired.
6. **Bake To MetaHuman Skeleton**, then export the baked `MH_<character>_SKEL` for Unreal re-import.

The sidebar **Export Manifest** field is the single source of truth for DNA and texture paths. Individual body/head DNA fields are resolved from the manifest automatically.

## Important constraints

The add-on does not replace the MetaHuman skeleton. `MH_<character>_SKEL` remains the deform/export skeleton. `CTRL_<character>_RIG` is the normal Rigify-generated animator rig; Rigify output bones drive the MetaHuman skeleton through bone-parented binding empties in `MHBLENDER_<character>_constraints`. Final animation is baked back onto `MH_*_SKEL`.

After skeleton orientation changes, **re-import the Export Manifest** (or rebuild the body rig) so bind pose matches DNA.

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

See also [metahuman_blender/rigify/README.md](metahuman_blender/rigify/README.md) for the optional Rigify feature set template.
