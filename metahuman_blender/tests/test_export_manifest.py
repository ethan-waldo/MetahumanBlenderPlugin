import json
from pathlib import Path

from metahuman_blender.core.export_manifest import find_export_manifest, load_export_manifest


def _write_manifest(directory: Path) -> Path:
    maps_dir = directory / "Maps"
    masks_dir = directory / "Masks"
    maps_dir.mkdir(exist_ok=True)
    masks_dir.mkdir(exist_ok=True)
    (maps_dir / "Head_Basecolor.png").write_bytes(b"")
    (masks_dir / "head_wm1_msk_01.tga").write_bytes(b"")
    (directory / "body.dna").write_bytes(b"")
    (directory / "head.dna").write_bytes(b"")
    manifest = directory / "ExportManifest.json"
    manifest.write_text(
        json.dumps(
            {
                "metaHumanName": "NewMetaHumanCharacter",
                "exportPluginVersion": "1.0.0",
                "exportEngineVersion": "5.8.0",
                "exportedAt": "2026.06.24-15.08.00",
                "dna": {"head": "head.dna", "body": "body.dna"},
                "thumbnail": "NewMetaHumanCharacter.png",
                "folders": {"maps": "Maps", "masks": "Masks"},
                "files": {
                    "maps": ["Head_Basecolor.png"],
                    "masks": ["head_wm1_msk_01.tga"],
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest


def test_load_export_manifest_resolves_dna_and_textures(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    manifest = load_export_manifest(manifest_path)

    assert manifest.character_name == "NewMetaHumanCharacter"
    assert manifest.body_dna_path == (tmp_path / "body.dna").resolve()
    assert manifest.head_dna_path == (tmp_path / "head.dna").resolve()
    assert manifest.map_files == [(tmp_path / "Maps" / "Head_Basecolor.png").resolve()]
    assert manifest.mask_files == [(tmp_path / "Masks" / "head_wm1_msk_01.tga").resolve()]


def test_find_export_manifest_in_directory(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    found = find_export_manifest(tmp_path)
    assert found == manifest_path.resolve()


def test_find_export_manifest_from_file_path(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    found = find_export_manifest(manifest_path)
    assert found == manifest_path.resolve()
