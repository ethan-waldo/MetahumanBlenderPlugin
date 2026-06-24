from pathlib import Path

from metahuman_blender.core.coordinate_system import dna_uv_to_blender, udim_tile_number_from_u
from metahuman_blender.core.material_builder import (
    dna_mesh_name_from_object,
    has_assignable_texture_maps,
    material_part_for_mesh,
    parse_texture_maps,
    parse_wrinkle_masks,
)


def test_parse_texture_maps_groups_standard_metahuman_maps(tmp_path):
    maps_dir = tmp_path / "Maps"
    maps_dir.mkdir()
    files = [
        "Body_Basecolor.png",
        "Body_Normal.png",
        "Body_SRMF.png",
        "Head_Basecolor.png",
        "Head_Normal.png",
        "Head_SRMF.png",
        "Head_Basecolor_Animated_CM1.png",
        "Head_Basecolor_Animated_CM2.png",
        "Head_Normal_Animated_WM1.png",
        "Head_Normal_Animated_WM2.png",
        "Eyes_Color.png",
        "Eyes_Normal.png",
        "Teeth_Color.png",
        "Teeth_Normal.png",
    ]
    for name in files:
        (maps_dir / name).write_bytes(b"")

    parts = parse_texture_maps([maps_dir / name for name in files])

    assert parts["Body"].srmf == maps_dir / "Body_SRMF.png"
    assert parts["Head"].basecolor == maps_dir / "Head_Basecolor.png"
    assert parts["Head"].animated_basecolors[1] == maps_dir / "Head_Basecolor_Animated_CM1.png"
    assert parts["Head"].animated_basecolors[2] == maps_dir / "Head_Basecolor_Animated_CM2.png"
    assert parts["Head"].animated_normals[1] == maps_dir / "Head_Normal_Animated_WM1.png"
    assert parts["Head"].animated_normals[2] == maps_dir / "Head_Normal_Animated_WM2.png"
    assert parts["Eyes"].basecolor == maps_dir / "Eyes_Color.png"


def test_parse_wrinkle_masks_groups_by_level(tmp_path):
    masks_dir = tmp_path / "Masks"
    masks_dir.mkdir()
    names = [
        "head_wm3_msk_02.tga",
        "head_wm1_msk_01.tga",
        "head_wm1_msk_04.tga",
        "head_wm13_msk_01.tga",
        "head_wm2_msk_01.tga",
    ]
    for name in names:
        (masks_dir / name).write_bytes(b"")

    masks = parse_wrinkle_masks([masks_dir / name for name in names])

    assert [path.name for path in masks[1]] == ["head_wm1_msk_01.tga", "head_wm1_msk_04.tga"]
    assert [path.name for path in masks[2]] == ["head_wm2_msk_01.tga"]
    assert [path.name for path in masks[3]] == ["head_wm3_msk_02.tga"]
    assert [path.name for path in masks[13]] == ["head_wm13_msk_01.tga"]


def test_material_part_for_mesh_maps_dna_mesh_names():
    assert material_part_for_mesh("body_lod0_mesh") == "Body"
    assert material_part_for_mesh("head_lod0_mesh") == "Head"
    assert material_part_for_mesh("teeth_lod0_mesh") == "Teeth"
    assert material_part_for_mesh("eyeLeft_lod0_mesh") == "Eyes"


def test_dna_mesh_name_from_object_strips_prefixes():
    assert dna_mesh_name_from_object("MH_OldGuy_body_lod0_mesh", "OldGuy", mesh_role="body") == "body_lod0_mesh"
    assert (
        dna_mesh_name_from_object("MH_OldGuy_head_head_lod0_mesh", "OldGuy", mesh_role="head")
        == "head_lod0_mesh"
    )


def test_dna_uv_to_blender_normalizes_to_tile_local_space():
    assert dna_uv_to_blender(1.5, 0.85) == (0.5, 0.85)
    assert dna_uv_to_blender(0.25, 0.75) == (0.25, 0.75)


def test_udim_tile_number_from_u():
    assert udim_tile_number_from_u(1.5) == 1002


def test_has_assignable_texture_maps_with_masks_only(tmp_path):
    masks_dir = tmp_path / "Masks"
    masks_dir.mkdir()
    mask = masks_dir / "head_wm1_msk_01.tga"
    mask.write_bytes(b"")
    assert has_assignable_texture_maps([], [mask]) is True
