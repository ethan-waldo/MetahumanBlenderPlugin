# MetaHuman Blender Workflow

End-to-end checklist for DCC export through Blender animation and back to Unreal.

## Assets required

- A MetaHuman **DCC export folder** containing `ExportManifest.json`
- OpenRigLogic Python bindings built for your Blender version

The MetaHuman Faceboard UI layout is **bundled inside the add-on** at `metahuman_blender/resources/faceboard.json`.

## ExportManifest.json

The manifest is the single entry point for a DCC export package. It references:

- `dna.body` and `dna.head` — rig and mesh DNA files
- `folders.maps` / `files.maps` — color, normal, and SRMF textures
- `folders.masks` / `files.masks` — animated wrinkle map masks
- `thumbnail` — preview image

Example structure:

```json
{
  "metaHumanName": "NewMetaHumanCharacter",
  "dna": { "head": "head.dna", "body": "body.dna" },
  "folders": { "maps": "Maps", "masks": "Masks" },
  "files": { "maps": ["Head_Basecolor.png"], "masks": ["head_wm1_msk_01.tga"] }
}
```

Texture paths are stored on the character metadata empty for future material setup.

## Setup

1. Install the add-on and set **OpenRigLogic Python Path**.
2. Press **Validate Setup**.

## Character import

1. **Import Export Manifest** → select `ExportManifest.json`.
2. Confirm `MH_<character>_SKEL`, body meshes, and head meshes were created.
3. Set **Control Rig Type** to **Internal CTRL_*** (default).
4. **Build Body Control Rig**.

## Head and face

The Faceboard is a **shared scene rig** named `MHC_FaceBoard`, built from the bundled `faceboard.json` shipped with the add-on. The same board is reused for every MetaHuman character.

1. **Import Export Manifest** auto-builds and links the Faceboard when head DNA is present.
2. Use **Setup Faceboard** to rebuild or relink it manually if needed.
3. Enable **Face RigLogic** or press **Evaluate Face RigLogic** while posing Faceboard controls in Pose mode.

## Bake and export

1. Set bake frame range in the **Bake** panel.
2. Press **Bake To MetaHuman Skeleton**.
3. Export `MH_<character>_SKEL` and meshes from Blender for Unreal re-import.

## Legacy import

Per-file **Import Body DNA** and **Import Head DNA** operators remain under the **Experimental** panel for partial packages without a manifest.

## Troubleshooting

- **Body limbs do not move:** rebuild with **Internal CTRL_*** instead of Rigify.
- **Missing head meshes:** confirm `dna.head` exists in ExportManifest.json and the file is present beside the manifest.
- **Face not updating:** import ExportManifest first, then link the Faceboard.
- **Exploded or distorted head mesh:** re-import ExportManifest after updating the add-on. Head DNA joints (~800+ facial bones) are merged into the body skeleton before head meshes bind; older imports that skipped this step leave head weights pointing at missing bones. All corrective shape keys are also reset to 0 after import — if every shape key was at 1.0 the head looked like a jumbled ball of geometry.
- **Pelvic spike or collapsed body:** usually the same skeleton mismatch; re-import from ExportManifest and rebuild the control rig.
- **Control shapes clustered or overlapping:** reload the add-on, then **Build Body Control Rig** again. Only the main FK/IK controls are shown; twist and corrective bones stay hidden but still drive the skeleton.
- **Faceboard not visible:** reload the add-on, then **Setup Faceboard** or re-import ExportManifest. The shared `MHC_FaceBoard` appears beside the character in the `MH_FaceBoard` collection.
