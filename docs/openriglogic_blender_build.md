# OpenRigLogic Blender Build Notes

This project uses OpenRigLogic `5.8` for Unreal `5.8` MetaHuman DCC exports.

Blender 5.2 Alpha uses Python `3.13`, but its bundled Python does not include the full development headers CMake needs. The local build therefore uses Homebrew `python@3.13` to compile `.cpython-313` extension modules, while avoiding a hard link to Homebrew's Python framework so the modules import inside Blender.

## Local source patch

The vendored OpenRigLogic CMake files are patched by `scripts/build_openriglogic_for_blender.sh` using:

```text
patches/openriglogic-blender-python-module.patch
```

It updates:

- `python/dna/CMakeLists.txt`
- `python/riglogic/CMakeLists.txt`

Both wrappers prefer `Python3::Module` over `Python3::Python`, which prevents loading a second Python runtime inside Blender.

## Build

```bash
scripts/build_openriglogic_for_blender.sh
```

The Blender add-on preference `OpenRigLogic Python Path` should point to:

```text
/Users/ethanwaldo/Developer/MetahumanBlenderPlugin/build/openriglogic-blender/python
```

## Verified

- Blender imports `dna`.
- Blender imports `riglogic`.
- `/Users/ethanwaldo/Downloads/OldGuy/NewMetaHumanCharacter/body.dna` loads through the add-on DNA loader.
